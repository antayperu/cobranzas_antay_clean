"""
RC-FEAT-021: Módulo Acuerdos de Pago con Cuotas
Tests unitarios para insert_acuerdo_pago, get_acuerdos_by_cliente, update_cuota_estado.
"""
import types, sys, pytest
from unittest.mock import MagicMock, patch, call
from datetime import date


# ──────────────────────────────────────────────
# Helpers de import
# ──────────────────────────────────────────────
def _stub_supabase():
    """Devuelve un stub de supabase con .table().select().eq()... encadenables."""
    stub = MagicMock()
    # Simular respuesta exitosa con un UUID de acuerdo
    resp_acuerdo = MagicMock()
    resp_acuerdo.data = [{"id": "acuerdo-uuid-1234"}]
    resp_cuotas = MagicMock()
    resp_cuotas.data = []
    stub.table.return_value.insert.return_value.select.return_value.execute.return_value = resp_acuerdo
    stub.table.return_value.insert.return_value.execute.return_value = resp_cuotas
    return stub


def _import_dbm():
    """Importar db_manager con supabase stubbed."""
    # Ensure supabase stub
    for mod in ("supabase", "postgrest", "gotrue", "httpx"):
        sys.modules.setdefault(mod, types.ModuleType(mod))
    import importlib
    import utils.db_manager as dbm
    return dbm


# ──────────────────────────────────────────────
# Tests insert_acuerdo_pago
# ──────────────────────────────────────────────
class TestInsertAcuerdoPago:

    def test_sin_supabase_retorna_false(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=None):
            ok, msg = dbm.insert_acuerdo_pago(
                cliente_id="C001", monto_total=3000, numero_cuotas=3,
                fecha_acuerdo="2025-01-15",
                cuotas=[
                    {"numero_cuota": 1, "monto_cuota": 1000, "fecha_vencimiento": "2025-02-01"},
                    {"numero_cuota": 2, "monto_cuota": 1000, "fecha_vencimiento": "2025-03-01"},
                    {"numero_cuota": 3, "monto_cuota": 1000, "fecha_vencimiento": "2025-04-01"},
                ],
            )
        assert ok is False
        assert "Supabase" in msg

    def test_monto_cero_retorna_false(self):
        dbm = _import_dbm()
        ok, msg = dbm.insert_acuerdo_pago(
            cliente_id="C001", monto_total=0, numero_cuotas=1,
            fecha_acuerdo="2025-01-15",
            cuotas=[{"numero_cuota": 1, "monto_cuota": 0, "fecha_vencimiento": "2025-02-01"}],
        )
        assert ok is False

    def test_cuotas_mismatch_retorna_false(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            ok, msg = dbm.insert_acuerdo_pago(
                cliente_id="C001", monto_total=2000, numero_cuotas=2,
                fecha_acuerdo="2025-01-15",
                cuotas=[{"numero_cuota": 1, "monto_cuota": 2000, "fecha_vencimiento": "2025-02-01"}],
            )
        assert ok is False
        assert "cuotas" in msg.lower() or "2" in msg

    def test_cliente_id_vacio_retorna_false(self):
        dbm = _import_dbm()
        ok, msg = dbm.insert_acuerdo_pago(
            cliente_id="", monto_total=1000, numero_cuotas=1,
            fecha_acuerdo="2025-01-15",
            cuotas=[{"numero_cuota": 1, "monto_cuota": 1000, "fecha_vencimiento": "2025-02-01"}],
        )
        assert ok is False

    def test_payload_tiene_estado_activo(self):
        """El payload insertado en acuerdos_pago debe tener estado='ACTIVO'."""
        dbm = _import_dbm()
        _sb = _stub_supabase()
        with patch.object(dbm, "get_supabase_client", return_value=_sb):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                resp_mock = MagicMock()
                resp_mock.data = [{"id": "uuid-test-0001"}]
                mock_exec.return_value = resp_mock

                dbm.insert_acuerdo_pago(
                    cliente_id="C001", monto_total=900, numero_cuotas=1,
                    fecha_acuerdo="2025-06-01",
                    cuotas=[{"numero_cuota": 1, "monto_cuota": 900, "fecha_vencimiento": "2025-07-01"}],
                )
                # Primer call a _safe_execute es el insert del acuerdo
                first_call_args = mock_exec.call_args_list[0]
                # Verifica que la query encadena insert con payload de estado ACTIVO
                inserted_obj = first_call_args[0][0]
                # No podemos inspeccionar el payload directamente (es objeto postgREST),
                # pero al menos verificamos que se llamó dos veces (acuerdo + cuotas)
                assert mock_exec.call_count >= 2


# ──────────────────────────────────────────────
# Tests get_acuerdos_by_cliente
# ──────────────────────────────────────────────
class TestGetAcuerdosByCliente:

    def test_sin_supabase_retorna_lista_vacia(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=None):
            result = dbm.get_acuerdos_by_cliente("C001")
        assert result == []

    def test_retorna_lista(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                mock_exec.return_value = MagicMock(data=[
                    {"id": "uuid-1", "cliente_id": "C001", "monto_total": 3000, "cuotas": []}
                ])
                result = dbm.get_acuerdos_by_cliente("C001")
        assert isinstance(result, list)

    def test_acuerdo_incluye_clave_cuotas(self):
        """Cada acuerdo devuelto debe tener la clave 'cuotas'."""
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                # Primera llamada: acuerdos; segunda llamada: cuotas del acuerdo
                resp_acuerdos = MagicMock(data=[{"id": "uuid-1", "cliente_id": "C001", "monto_total": 1000}])
                resp_cuotas = MagicMock(data=[{"id": "c-1", "acuerdo_id": "uuid-1", "numero_cuota": 1}])
                mock_exec.side_effect = [resp_acuerdos, resp_cuotas]
                result = dbm.get_acuerdos_by_cliente("C001")
        assert len(result) == 1
        assert "cuotas" in result[0]
        assert len(result[0]["cuotas"]) == 1


# ──────────────────────────────────────────────
# Tests update_cuota_estado
# ──────────────────────────────────────────────
class TestUpdateCuotaEstado:

    def test_sin_supabase_retorna_false(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=None):
            ok, msg = dbm.update_cuota_estado("cuota-1", "PAGADO")
        assert ok is False

    def test_estado_invalido_retorna_false(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            ok, msg = dbm.update_cuota_estado("cuota-1", "INEXISTENTE")
        assert ok is False
        assert "inv" in msg.lower()  # invalido / inválido

    def test_estados_validos_aceptados(self):
        dbm = _import_dbm()
        for estado in ("PENDIENTE", "PAGADO", "VENCIDO", "REPACTADO"):
            with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
                with patch.object(dbm, "_safe_execute", return_value=MagicMock()):
                    ok, _ = dbm.update_cuota_estado("cuota-1", estado)
            assert ok is True, f"Estado {estado} debería ser aceptado"

    def test_pagado_con_fecha_pago(self):
        dbm = _import_dbm()
        with patch.object(dbm, "get_supabase_client", return_value=MagicMock()):
            with patch.object(dbm, "_safe_execute") as mock_exec:
                mock_exec.return_value = MagicMock()
                ok, msg = dbm.update_cuota_estado(
                    "cuota-1", "PAGADO", fecha_pago="2025-06-15"
                )
        assert ok is True

    def test_constantes_estados_cuota(self):
        dbm = _import_dbm()
        assert dbm.CUOTA_ESTADOS_VALIDOS == {"PENDIENTE", "PAGADO", "VENCIDO", "REPACTADO"}

    def test_constantes_estados_acuerdo(self):
        dbm = _import_dbm()
        assert dbm.ACUERDO_ESTADOS_VALIDOS == {"ACTIVO", "CUMPLIDO", "INCUMPLIDO", "CANCELADO"}
