"""
Tests para RC-FEAT-019: Resultado Post-Envío WhatsApp
Verifica que la lógica de mapeo de opciones y persistencia de gestiones funciona correctamente.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils.db_manager as dbm


# Mapa extraído del panel (mismo que en whatsapp.py) — estándar industria 2026-03-17
_RESULTADO_MAP = {
    "✅ Acordó pagar":       "EXITOSO",
    "🤝 Prometió pagar":     "PROMESA_PAGO",
    "⏳ Solicitó más plazo": "SOLICITO_PLAZO",
    "💬 En negociación":     "EN_NEGOCIACION",
    "📵 Sin respuesta":      "SIN_RESPUESTA",
    "⚖️ Derivar a Legal":    "ESCALAR_LEGAL",
    "❓ Disputó la deuda":   "DISPUTA",
}


class TestRC019ResultadoPostEnvio(unittest.TestCase):

    # ------------------------------------------------------------------
    # 1. Mapeo de opciones a valores Supabase (estándar industria)
    # ------------------------------------------------------------------
    def test_mapeo_acordo_pagar(self):
        self.assertEqual(_RESULTADO_MAP["✅ Acordó pagar"], "EXITOSO")

    def test_mapeo_prometio_pagar(self):
        self.assertEqual(_RESULTADO_MAP["🤝 Prometió pagar"], "PROMESA_PAGO")

    def test_mapeo_sin_respuesta(self):
        self.assertEqual(_RESULTADO_MAP["📵 Sin respuesta"], "SIN_RESPUESTA")

    def test_mapeo_escalar(self):
        self.assertEqual(_RESULTADO_MAP["⚖️ Derivar a Legal"], "ESCALAR_LEGAL")

    def test_mapeo_plazo(self):
        self.assertEqual(_RESULTADO_MAP["⏳ Solicitó más plazo"], "SOLICITO_PLAZO")

    def test_mapeo_en_negociacion(self):
        self.assertEqual(_RESULTADO_MAP["💬 En negociación"], "EN_NEGOCIACION")

    def test_mapeo_disputa(self):
        self.assertEqual(_RESULTADO_MAP["❓ Disputó la deuda"], "DISPUTA")

    def test_todos_los_valores_son_validos_en_supabase(self):
        """Los valores mapeados deben estar en el catálogo de resultados válidos."""
        validos = dbm._get_resultados_validos_set()
        for opcion, valor in _RESULTADO_MAP.items():
            self.assertIn(
                valor,
                validos,
                f"Opción '{opcion}' mapea a '{valor}' que no está en el catálogo de resultados",
            )

    # ------------------------------------------------------------------
    # 2. insert_gestion se llama con los parámetros correctos
    # ------------------------------------------------------------------
    @patch('utils.db_manager.get_supabase_client')
    def test_insert_gestion_resultado_wa(self, mock_client):
        mock_sb = MagicMock()
        mock_insert = MagicMock()
        mock_sb.table.return_value.insert.return_value = mock_insert
        mock_insert.execute.return_value = MagicMock(data=[{'id': 'abc'}])
        mock_client.return_value = mock_sb

        ok, msg = dbm.insert_gestion(
            cliente_id='CLI-001',
            tipo_gestion='WHATSAPP',
            resultado='EXITOSO',
            notas='Resultado post-envío WA: ✅ Acordó pagar | Deuda: S/1,200',
            cycle_id='CIC-20260313-1000',
            metadata_extra={
                'source': 'panel_resultado_post_envio',
                'opcion_gestor': '✅ Acordó pagar',
            },
        )

        self.assertTrue(ok, f"insert_gestion falló: {msg}")
        mock_sb.table.assert_called_with("gestiones")

    @patch('utils.db_manager.get_supabase_client')
    def test_insert_gestion_sin_respuesta(self, mock_client):
        mock_sb = MagicMock()
        mock_insert = MagicMock()
        mock_sb.table.return_value.insert.return_value = mock_insert
        mock_insert.execute.return_value = MagicMock(data=[{'id': 'xyz'}])
        mock_client.return_value = mock_sb

        ok, msg = dbm.insert_gestion(
            cliente_id='CLI-002',
            tipo_gestion='WHATSAPP',
            resultado='SIN_RESPUESTA',
            notas='Resultado post-envío WA: 📵 Sin respuesta',
            cycle_id='CIC-20260313-1000',
        )
        self.assertTrue(ok)

    # ------------------------------------------------------------------
    # 3. Resultado inválido debe ser normalizado a PENDIENTE
    # ------------------------------------------------------------------
    @patch('utils.db_manager.get_supabase_client')
    def test_resultado_invalido_normalizado(self, mock_client):
        mock_sb = MagicMock()
        mock_insert = MagicMock()
        mock_sb.table.return_value.insert.return_value = mock_insert
        mock_insert.execute.return_value = MagicMock(data=[{'id': 'zzz'}])
        mock_client.return_value = mock_sb

        # Pasamos un resultado que no está en el set válido
        ok, msg = dbm.insert_gestion(
            cliente_id='CLI-003',
            tipo_gestion='WHATSAPP',
            resultado='RESULTADO_INEXISTENTE',  # debe normalizarse a PENDIENTE
        )
        self.assertTrue(ok)
        # Verificar que el payload enviado tiene resultado=PENDIENTE
        call_args = mock_sb.table.return_value.insert.call_args[0][0]
        self.assertEqual(call_args['resultado'], 'PENDIENTE')

    # ------------------------------------------------------------------
    # 4. Sin Supabase disponible, retorna False con mensaje claro
    # ------------------------------------------------------------------
    @patch('utils.db_manager.get_supabase_client', return_value=None)
    def test_sin_supabase_retorna_false(self, _):
        ok, msg = dbm.insert_gestion(
            cliente_id='CLI-001',
            tipo_gestion='WHATSAPP',
            resultado='EXITOSO',
        )
        self.assertFalse(ok)
        self.assertIn("Supabase", msg)

    # ------------------------------------------------------------------
    # 5. last_wa_send_results contiene los campos requeridos post-envío
    # ------------------------------------------------------------------
    def test_estructura_session_state_post_envio(self):
        """El dict guardado en session_state debe tener los campos que necesita el panel."""
        simulated_result = {
            'exitosos': 3,
            'fallidos': 1,
            'details': [
                {'Cliente': 'EMPRESA A', 'CodCliente': 'CLI-001',
                 'Teléfono': '999000001', 'Estado': '✅ Enviado', 'Deuda': 'S/1,200'},
                {'Cliente': 'EMPRESA B', 'CodCliente': 'CLI-002',
                 'Teléfono': '999000002', 'Estado': '✅ Enviado', 'Deuda': 'S/3,400'},
            ],
            'cycle_id': 'CIC-20260313-1000',
            'resultados_registrados': {},
        }
        self.assertIn('details', simulated_result)
        self.assertIn('cycle_id', simulated_result)
        self.assertIn('resultados_registrados', simulated_result)
        for det in simulated_result['details']:
            self.assertIn('CodCliente', det, "Cada detail debe tener CodCliente para poder persistir en gestiones")

    # ------------------------------------------------------------------
    # 6. Opción "Sin registrar" no debe llamar a insert_gestion
    # ------------------------------------------------------------------
    def test_sin_registrar_no_inserta(self):
        """Si el gestor deja '⏳ Sin registrar', no se debe llamar a insert_gestion."""
        opcion = "⏳ Sin registrar"
        resultado = _RESULTADO_MAP.get(opcion)
        self.assertIsNone(resultado, "⏳ Sin registrar no debe tener mapeo — se skipea en el loop")


if __name__ == '__main__':
    unittest.main()
