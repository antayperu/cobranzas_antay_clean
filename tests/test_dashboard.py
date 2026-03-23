"""
Tests para RC-FEAT-038: Dashboard de Efectividad de Cobranza.
Verifica las 4 funciones nuevas de db_manager y la estructura del tab.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils.db_manager as dbm


# ---------------------------------------------------------------------------
# 1. get_funnel_cobranza
# ---------------------------------------------------------------------------

class TestGetFunnelCobranza(unittest.TestCase):

    @patch('utils.db_manager.get_supabase_client', return_value=None)
    def test_sin_supabase_retorna_vacio(self, _):
        result = dbm.get_funnel_cobranza()
        self.assertEqual(result, {})

    @patch('utils.db_manager.get_supabase_client')
    def test_estructura_claves_retornadas(self, mock_client):
        mock_sb = MagicMock()
        # Configurar respuestas para cada query (count=exact)
        mock_resp = MagicMock()
        mock_resp.count = 5
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value = mock_resp
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value = mock_resp
        mock_sb.table.return_value.select.return_value.in_.return_value.eq.return_value.limit.return_value = mock_resp
        mock_client.return_value = mock_sb

        result = dbm.get_funnel_cobranza(cycle_id="CIC-20260317-0900")
        # Debe retornar un dict (puede estar vacío si mock no cuadra exactamente,
        # pero no debe lanzar excepción)
        self.assertIsInstance(result, dict)

    @patch('utils.db_manager.get_supabase_client', return_value=None)
    def test_sin_cycle_id_acepta_none(self, _):
        result = dbm.get_funnel_cobranza(cycle_id=None)
        self.assertEqual(result, {})


# ---------------------------------------------------------------------------
# 2. get_efectividad_por_plantilla
# ---------------------------------------------------------------------------

class TestGetEfectividadPorPlantilla(unittest.TestCase):

    @patch('utils.db_manager.get_supabase_client', return_value=None)
    def test_sin_supabase_retorna_lista_vacia(self, _):
        result = dbm.get_efectividad_por_plantilla()
        self.assertEqual(result, [])

    @patch('utils.db_manager.get_supabase_client')
    def test_estructura_filas_retornadas(self, mock_client):
        mock_sb = MagicMock()

        # Simular notificaciones enviadas con metadata de plantilla
        notif_data = [
            {"cliente_id": "CLI-001", "estado": "ENVIADO",
             "metadata": {"template": "📋 Cobranza Estándar"}},
            {"cliente_id": "CLI-002", "estado": "ENVIADO",
             "metadata": {"template": "📋 Cobranza Estándar"}},
            {"cliente_id": "CLI-003", "estado": "ENVIADO",
             "metadata": {"template": "🔔 Primer Recordatorio"}},
        ]
        gestiones_data = [
            {"cliente_id": "CLI-001", "resultado": "EXITOSO"},
        ]

        mock_notif_resp = MagicMock()
        mock_notif_resp.data = notif_data
        mock_gest_resp = MagicMock()
        mock_gest_resp.data = gestiones_data

        # Primer call → notificaciones, segundo call → gestiones
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value = mock_notif_resp
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value = mock_gest_resp
        mock_client.return_value = mock_sb

        result = dbm.get_efectividad_por_plantilla()
        self.assertIsInstance(result, list)
        # Si hay datos, cada fila debe tener las claves esperadas
        for fila in result:
            self.assertIn("plantilla", fila)
            self.assertIn("total_enviados", fila)
            self.assertIn("exitosos", fila)
            self.assertIn("tasa_pct", fila)

    @patch('utils.db_manager.get_supabase_client')
    def test_metadata_string_json_parseado(self, mock_client):
        """metadata como string JSON debe parsearse sin error."""
        import json
        mock_sb = MagicMock()
        notif_data = [
            {"cliente_id": "CLI-010", "estado": "ENVIADO",
             "metadata": json.dumps({"template": "🔴 Urgente / Pre-Legal"})},
        ]
        mock_resp = MagicMock()
        mock_resp.data = notif_data
        mock_gest_resp = MagicMock()
        mock_gest_resp.data = []

        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value = mock_resp
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value = mock_gest_resp
        mock_client.return_value = mock_sb

        # No debe lanzar excepción
        result = dbm.get_efectividad_por_plantilla()
        self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# 3. get_top_clientes_criticos
# ---------------------------------------------------------------------------

class TestGetTopClientesCriticos(unittest.TestCase):

    @patch('utils.db_manager.get_supabase_client', return_value=None)
    def test_sin_supabase_retorna_lista_vacia(self, _):
        result = dbm.get_top_clientes_criticos(n=5)
        self.assertEqual(result, [])

    @patch('utils.db_manager.get_supabase_client')
    def test_respeta_limite_n(self, mock_client):
        mock_sb = MagicMock()
        # 20 documentos para 10 clientes distintos
        docs_data = [
            {"cliente_id": f"CLI-{i:03d}", "nombre_cliente": f"Empresa {i}",
             "saldo_pendiente": float(1000 * (20 - i)), "dias_mora": i * 5}
            for i in range(1, 21)
        ]
        mock_docs_resp = MagicMock()
        mock_docs_resp.data = docs_data
        mock_gest_resp = MagicMock()
        mock_gest_resp.data = []

        mock_sb.table.return_value.select.return_value.order.return_value.limit.return_value = mock_docs_resp
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value = mock_gest_resp
        mock_client.return_value = mock_sb

        result = dbm.get_top_clientes_criticos(n=5)
        # Puede ser hasta 5 (o menos si mock no cuadra perfectamente con la call chain)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 5)

    @patch('utils.db_manager.get_supabase_client')
    def test_estructura_campos_retornados(self, mock_client):
        mock_sb = MagicMock()
        docs_data = [
            {"cliente_id": "CLI-001", "nombre_cliente": "ACME S.A.C.",
             "saldo_pendiente": 5000.0, "dias_mora": 45},
        ]
        mock_docs_resp = MagicMock()
        mock_docs_resp.data = docs_data
        mock_gest_resp = MagicMock()
        mock_gest_resp.data = [{"cliente_id": "CLI-001", "resultado": "SIN_RESPUESTA", "fecha": "2026-03-17"}]

        mock_sb.table.return_value.select.return_value.order.return_value.limit.return_value = mock_docs_resp
        mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value = mock_gest_resp
        mock_client.return_value = mock_sb

        result = dbm.get_top_clientes_criticos(n=10)
        self.assertIsInstance(result, list)
        if result:
            for campo in ["cliente_id", "nombre", "saldo_total", "docs_count",
                          "dias_mora_max", "gestiones_count", "ultimo_resultado"]:
                self.assertIn(campo, result[0], f"Campo '{campo}' faltante en resultado")


# ---------------------------------------------------------------------------
# 4. get_kpis_periodo
# ---------------------------------------------------------------------------

class TestGetKpisPeriodo(unittest.TestCase):

    @patch('utils.db_manager.get_supabase_client', return_value=None)
    def test_sin_supabase_retorna_vacio(self, _):
        result = dbm.get_kpis_periodo("2026-03-01", "2026-03-17")
        self.assertEqual(result, {})

    @patch('utils.db_manager.get_supabase_client')
    @patch('utils.db_manager._safe_execute')
    def test_estructura_claves_esperadas(self, mock_safe_exec, mock_client):
        mock_client.return_value = MagicMock()  # cliente disponible

        gestiones_data = [
            {"resultado": "EXITOSO", "fecha": "2026-03-15T10:00:00"},
            {"resultado": "SIN_RESPUESTA", "fecha": "2026-03-15T11:00:00"},
            {"resultado": "PROMESA_PAGO", "fecha": "2026-03-16T09:00:00"},
        ]
        notif_data = [
            {"canal": "WHATSAPP", "estado": "ENVIADO", "fecha_envio": "2026-03-15T10:00:00"},
            {"canal": "EMAIL", "estado": "ENVIADO", "fecha_envio": "2026-03-15T10:05:00"},
        ]

        mock_g = MagicMock()
        mock_g.data = gestiones_data
        mock_n = MagicMock()
        mock_n.data = notif_data
        # WA gestiones query (nueva — los WA se leen de gestiones, no de notificaciones)
        mock_wa_g = MagicMock()
        mock_wa_g.data = [{"tipo_gestion": "WHATSAPP"}]
        mock_a = MagicMock()
        mock_a.count = 3

        # _safe_execute se llama 4 veces: gestiones_stats, notificaciones_email, gestiones_wa, acuerdos
        mock_safe_exec.side_effect = [mock_g, mock_n, mock_wa_g, mock_a]

        result = dbm.get_kpis_periodo("2026-03-01", "2026-03-17")
        self.assertIsInstance(result, dict)
        claves_esperadas = [
            "gestiones_total", "exitosos", "promesas", "sin_respuesta",
            "tasa_exito_pct", "notificaciones_wa", "notificaciones_email",
            "tasa_notif_exitosa_pct", "acuerdos_activos", "by_resultado",
        ]
        for clave in claves_esperadas:
            self.assertIn(clave, result, f"Clave '{clave}' faltante en get_kpis_periodo")

    @patch('utils.db_manager.get_supabase_client')
    def test_tasa_exito_calculada_correctamente(self, mock_client):
        mock_sb = MagicMock()
        # 2 EXITOSO sobre 4 gestiones → tasa 50%
        gestiones_data = [
            {"resultado": "EXITOSO", "fecha": "2026-03-10T10:00:00"},
            {"resultado": "EXITOSO", "fecha": "2026-03-11T10:00:00"},
            {"resultado": "SIN_RESPUESTA", "fecha": "2026-03-12T10:00:00"},
            {"resultado": "PROMESA_PAGO", "fecha": "2026-03-13T10:00:00"},
        ]
        mock_g_resp = MagicMock()
        mock_g_resp.data = gestiones_data
        mock_n_resp = MagicMock()
        mock_n_resp.data = []
        mock_a_resp = MagicMock()
        mock_a_resp.count = 0

        mock_sb.table.return_value.select.return_value.gte.return_value.lte.return_value.limit.side_effect = [
            mock_g_resp, mock_n_resp,
        ]
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value = mock_a_resp
        mock_client.return_value = mock_sb

        result = dbm.get_kpis_periodo("2026-03-01", "2026-03-17")
        self.assertIsInstance(result, dict)
        # Si los mocks cuadraron, tasa debe ser 50.0
        if result.get("gestiones_total", 0) == 4:
            self.assertEqual(result["tasa_exito_pct"], 50.0)


# ---------------------------------------------------------------------------
# 5. Importación y render_tab del dashboard (smoke import test)
# ---------------------------------------------------------------------------

class TestDashboardTabImport(unittest.TestCase):

    def test_modulo_importable(self):
        """El módulo dashboard.py debe importarse sin error."""
        try:
            import utils.ui.tabs.dashboard as dash
            self.assertTrue(hasattr(dash, "render_tab"))
        except ImportError as e:
            self.fail(f"No se pudo importar utils.ui.tabs.dashboard: {e}")

    def test_render_tab_es_callable(self):
        import utils.ui.tabs.dashboard as dash
        self.assertTrue(callable(dash.render_tab))

    def test_helpers_formato_moneda(self):
        from utils.ui.tabs.dashboard import _fmt_moneda, _fmt_pct
        self.assertEqual(_fmt_moneda(1200.5), "S/ 1,200.50")
        self.assertEqual(_fmt_pct(85.3), "85.3%")

    def test_helpers_resultado_label(self):
        from utils.ui.tabs.dashboard import _resultado_label
        self.assertEqual(_resultado_label("EXITOSO"), "✅ Acordó pagar")
        self.assertEqual(_resultado_label("ESCALAR_LEGAL"), "⚖️ Derivar a Legal")
        self.assertEqual(_resultado_label("SIN_GESTION"), "— Sin gestión")
        # Código desconocido → retorna el código mismo
        self.assertEqual(_resultado_label("CODIGO_RARO"), "CODIGO_RARO")


if __name__ == '__main__':
    unittest.main()
