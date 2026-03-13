"""
RC-FEAT-023: Trazabilidad Completa — reconcile_ciclo_recovery
Tests unitarios para los 3 niveles de trazabilidad.
"""
import types, sys, pytest
from unittest.mock import MagicMock, patch


def _import_dbm():
    for mod in ("supabase", "postgrest", "gotrue", "httpx"):
        sys.modules.setdefault(mod, types.ModuleType(mod))
    import utils.db_manager as dbm
    return dbm


# ──────────────────────────────────────────────
# Tests reconcile_ciclo_recovery
# ──────────────────────────────────────────────
class TestReconcileCicloRecovery:

    def test_sin_cycle_ids_retorna_false(self):
        dbm = _import_dbm()
        result = dbm.reconcile_ciclo_recovery("", "CICLO-002")
        assert result["ok"] is False
        assert "requeridos" in result["mensaje"].lower() or "cycle_id" in result["mensaje"].lower()

    def test_sin_cycle_id_nuevo_retorna_false(self):
        dbm = _import_dbm()
        result = dbm.reconcile_ciclo_recovery("CICLO-001", "")
        assert result["ok"] is False

    def test_sin_supabase_retorna_false(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=None):
            result = dbm.reconcile_ciclo_recovery("CICLO-001", "CICLO-002")
        assert result["ok"] is False
        assert "Supabase" in result["mensaje"]

    def test_resultado_tiene_claves_ok_mensaje_stats(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_get_docs_simple_by_cycle", return_value=[]):
                with patch.object(dbm, "get_gestiones_list", return_value=[]):
                    with patch.object(dbm, "_safe_execute", return_value=MagicMock(data=[], count=0)):
                        result = dbm.reconcile_ciclo_recovery("CICLO-001", "CICLO-002")
        assert "ok" in result
        assert "mensaje" in result
        assert "stats" in result

    def test_tasa_recuperacion_cero_si_sin_docs_anterior(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            # anterior: vacío, nuevo: vacío → tasa 0
            with patch.object(dbm, "_get_docs_simple_by_cycle", return_value=[]):
                with patch.object(dbm, "get_gestiones_list", return_value=[]):
                    with patch.object(dbm, "_safe_execute", return_value=MagicMock(data=[], count=0)):
                        result = dbm.reconcile_ciclo_recovery("CICLO-001", "CICLO-002")
        if result["ok"]:
            assert result["stats"].get("tasa_recuperacion", 0) == 0.0

    def test_detecta_docs_recuperados(self):
        """Docs en anterior pero no en nuevo → recuperados."""
        dbm = _import_dbm()
        docs_anterior = [
            {"match_key": "MK-001", "cliente_id": "C001", "saldo_real": 1000, "saldo_original": 1200},
            {"match_key": "MK-002", "cliente_id": "C001", "saldo_real": 500, "saldo_original": 600},
            {"match_key": "MK-003", "cliente_id": "C002", "saldo_real": 800, "saldo_original": 900},
        ]
        # MK-001 y MK-002 pagados (no están en nuevo), MK-003 sigue pendiente
        docs_nuevo = [
            {"match_key": "MK-003", "cliente_id": "C002", "saldo_real": 800, "saldo_original": 900},
        ]

        call_count = [0]
        def _mock_get_docs(cycle_id):
            call_count[0] += 1
            return docs_anterior if "001" in cycle_id else docs_nuevo

        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_get_docs_simple_by_cycle", side_effect=_mock_get_docs):
                with patch.object(dbm, "get_gestiones_list", return_value=[]):
                    with patch.object(dbm, "_safe_execute", return_value=MagicMock(data=[], count=0)):
                        result = dbm.reconcile_ciclo_recovery("CICLO-001", "CICLO-002")

        assert result["ok"] is True
        stats = result["stats"]
        assert stats["docs_recuperados"] == 2   # MK-001 y MK-002
        assert stats["monto_recuperado"] == 1500.0   # 1000 + 500
        assert stats["clientes_total"] >= 1   # Al menos C002 sigue en nuevo

    def test_tasa_recuperacion_calculada(self):
        """Con 2 de 3 docs recuperados → tasa = 66.67%."""
        dbm = _import_dbm()
        docs_anterior = [
            {"match_key": f"MK-{i:03d}", "cliente_id": "C001", "saldo_real": 100, "saldo_original": 100}
            for i in range(3)
        ]
        docs_nuevo = [
            {"match_key": "MK-002", "cliente_id": "C001", "saldo_real": 100, "saldo_original": 100}
        ]

        def _mock_get(cycle_id):
            return docs_anterior if "ANT" in cycle_id else docs_nuevo

        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_get_docs_simple_by_cycle", side_effect=_mock_get):
                with patch.object(dbm, "get_gestiones_list", return_value=[]):
                    with patch.object(dbm, "_safe_execute", return_value=MagicMock(data=[], count=0)):
                        result = dbm.reconcile_ciclo_recovery("CICLO-ANT", "CICLO-NUE")

        assert result["ok"] is True
        tasa = result["stats"]["tasa_recuperacion"]
        assert abs(tasa - 66.67) < 0.1

    def test_sql_tiene_tabla_resumen_cliente_ciclo(self):
        """El archivo SQL contiene CREATE TABLE resumen_cliente_ciclo."""
        import pathlib
        sql_file = pathlib.Path("sql/12_create_resumen_tablas.sql")
        assert sql_file.exists(), "sql/12_create_resumen_tablas.sql no existe"
        content = sql_file.read_text(encoding="utf-8")
        assert "resumen_cliente_ciclo" in content
        assert "resumen_ciclo" in content

    def test_sql_tiene_unique_constraint_por_cliente_ciclo(self):
        """La tabla resumen_cliente_ciclo debe tener UNIQUE (cliente_id, cycle_id)."""
        import pathlib
        content = pathlib.Path("sql/12_create_resumen_tablas.sql").read_text(encoding="utf-8")
        assert "UNIQUE (cliente_id, cycle_id)" in content

    def test_funcion_retorna_dict_completo_en_exito(self):
        dbm = _import_dbm()
        docs = [{"match_key": "MK-001", "cliente_id": "C001", "saldo_real": 500, "saldo_original": 500}]
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_get_docs_simple_by_cycle", return_value=docs):
                with patch.object(dbm, "get_gestiones_list", return_value=[]):
                    with patch.object(dbm, "_safe_execute", return_value=MagicMock(data=[], count=0)):
                        result = dbm.reconcile_ciclo_recovery("CICLO-001", "CICLO-002")
        assert isinstance(result, dict)
        assert set(result.keys()) >= {"ok", "mensaje", "stats"}

    def test_function_exists_in_dbm(self):
        dbm = _import_dbm()
        assert hasattr(dbm, "reconcile_ciclo_recovery"), "reconcile_ciclo_recovery no existe en db_manager"
        assert callable(dbm.reconcile_ciclo_recovery)
