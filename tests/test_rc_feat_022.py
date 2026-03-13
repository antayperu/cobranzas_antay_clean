"""
RC-FEAT-022: Bandeja de Pendientes
Tests unitarios para get_cuotas_pendientes_hoy y get_clientes_sin_gestion_ciclo.
"""
import types, sys, pytest
from unittest.mock import MagicMock, patch
from datetime import date


def _import_dbm():
    for mod in ("supabase", "postgrest", "gotrue", "httpx"):
        sys.modules.setdefault(mod, types.ModuleType(mod))
    import utils.db_manager as dbm
    return dbm


# ──────────────────────────────────────────────
# Tests get_cuotas_pendientes_hoy
# ──────────────────────────────────────────────
class TestGetCuotasPendientesHoy:

    def test_sin_supabase_retorna_lista_vacia(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=None):
            result = dbm.get_cuotas_pendientes_hoy()
        assert result == []

    def test_retorna_lista(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                mock_exec.return_value = MagicMock(data=[
                    {"id": "c-1", "estado": "PENDIENTE", "fecha_vencimiento": "2025-06-01",
                     "monto_cuota": 500, "numero_cuota": 1, "acuerdos_pago": {"cliente_id": "C001"}},
                ])
                result = dbm.get_cuotas_pendientes_hoy()
        assert isinstance(result, list)

    def test_resultado_tiene_cuotas_pendientes(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                mock_exec.return_value = MagicMock(data=[
                    {"id": "c-1", "estado": "PENDIENTE", "fecha_vencimiento": "2025-01-01",
                     "monto_cuota": 300, "numero_cuota": 2},
                    {"id": "c-2", "estado": "PENDIENTE", "fecha_vencimiento": "2025-02-15",
                     "monto_cuota": 300, "numero_cuota": 3},
                ])
                result = dbm.get_cuotas_pendientes_hoy(limit=100)
        assert len(result) == 2

    def test_retorna_vacio_si_no_hay_cuotas(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                mock_exec.return_value = MagicMock(data=[])
                result = dbm.get_cuotas_pendientes_hoy()
        assert result == []

    def test_funcion_exists_en_dbm(self):
        dbm = _import_dbm()
        assert hasattr(dbm, "get_cuotas_pendientes_hoy")
        assert callable(dbm.get_cuotas_pendientes_hoy)


# ──────────────────────────────────────────────
# Tests get_clientes_sin_gestion_ciclo
# ──────────────────────────────────────────────
class TestGetClientesSinGestionCiclo:

    def test_sin_supabase_retorna_lista_vacia(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=None):
            result = dbm.get_clientes_sin_gestion_ciclo("CICLO-001")
        assert result == []

    def test_sin_cycle_id_vacio_retorna_vacio_o_lista(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=None):
            result = dbm.get_clientes_sin_gestion_ciclo("")
        assert isinstance(result, list)

    def test_detecta_clientes_sin_gestion(self):
        """Clientes en ciclo pero sin gestión deben aparecer en el resultado."""
        dbm = _import_dbm()
        docs_data = [
            {"cliente_id": "C001"},
            {"cliente_id": "C002"},
            {"cliente_id": "C003"},
        ]
        gestiones_data = [
            {"cliente_id": "C002"},  # Solo C002 tiene gestión
        ]
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                resp_docs = MagicMock(data=docs_data)
                resp_gest = MagicMock(data=gestiones_data)
                mock_exec.side_effect = [resp_docs, resp_gest]
                result = dbm.get_clientes_sin_gestion_ciclo("CICLO-001")
        # C001 y C003 no tienen gestión
        assert "C001" in result
        assert "C003" in result
        assert "C002" not in result

    def test_todos_con_gestion_retorna_vacio(self):
        dbm = _import_dbm()
        docs_data = [{"cliente_id": "C001"}, {"cliente_id": "C002"}]
        gestiones_data = [{"cliente_id": "C001"}, {"cliente_id": "C002"}]
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                mock_exec.side_effect = [
                    MagicMock(data=docs_data),
                    MagicMock(data=gestiones_data),
                ]
                result = dbm.get_clientes_sin_gestion_ciclo("CICLO-001")
        assert result == []

    def test_retorna_lista_ordenada(self):
        dbm = _import_dbm()
        docs_data = [{"cliente_id": "C003"}, {"cliente_id": "C001"}, {"cliente_id": "C002"}]
        gestiones_data = []
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                mock_exec.side_effect = [
                    MagicMock(data=docs_data),
                    MagicMock(data=gestiones_data),
                ]
                result = dbm.get_clientes_sin_gestion_ciclo("CICLO-001")
        assert result == sorted(result), "La lista debe estar ordenada"

    def test_funcion_exists_en_dbm(self):
        dbm = _import_dbm()
        assert hasattr(dbm, "get_clientes_sin_gestion_ciclo")
        assert callable(dbm.get_clientes_sin_gestion_ciclo)

    def test_respeta_limit(self):
        dbm = _import_dbm()
        docs_data = [{"cliente_id": f"C{i:03d}"} for i in range(50)]
        gestiones_data = []
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                mock_exec.side_effect = [
                    MagicMock(data=docs_data),
                    MagicMock(data=gestiones_data),
                ]
                result = dbm.get_clientes_sin_gestion_ciclo("CICLO-001", limit=10)
        assert len(result) <= 10
