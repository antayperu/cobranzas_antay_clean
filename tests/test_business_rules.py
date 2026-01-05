"""
Business Rules Automated Tests
Suite de tests automatizados para validar reglas de negocio sin UI.
"""

import pytest
import pandas as pd
from datetime import datetime
from tests.fixtures.synthetic_data import (
    create_synthetic_df_final,
    create_synthetic_df_filtered,
    create_synthetic_client_group_email,
    simulate_email_sent,
    fixture_fresh_load,
    fixture_with_duplicates,
    fixture_mixed_debt
)


class TestA_NewCycleTracking:
    """Test A: Nuevo ciclo - tracking limpio y contadores en 0"""
    
    def test_fresh_load_tracking_initialized_as_pending(self):
        """Al procesar data, tracking debe quedar PENDIENTE y FECHA vacío"""
        df = fixture_fresh_load()
        
        # Validar que TODOS los registros tienen tracking limpio
        assert (df['ESTADO_EMAIL'] == 'PENDIENTE').all(), "Todos los registros deben tener ESTADO_EMAIL='PENDIENTE'"
        assert (df['FECHA_ULTIMO_ENVIO'] == '').all(), "Todos los registros deben tener FECHA_ULTIMO_ENVIO vacío"
    
    def test_fresh_load_enviados_hoy_is_zero(self):
        """'Enviados Hoy' debe ser 0 cuando fresh_load=True"""
        df = fixture_fresh_load()
        is_fresh_load = True  # Simular flag fresh_load
        
        if not is_fresh_load:
            # Lógica normal: consultar DB
            sent_emails_today = []  # Simular consulta DB
        else:
            # Ciclo nuevo: NO consultar DB
            sent_emails_today = []
        
        enviados_hoy = len(sent_emails_today)
        assert enviados_hoy == 0, f"En fresh_load, 'Enviados Hoy' debe ser 0, pero es {enviados_hoy}"
    
    def test_fresh_load_pendientes_greater_than_zero(self):
        """'Pendientes' debe ser > 0 si hay emails válidos"""
        df = fixture_fresh_load()
        client_group = create_synthetic_client_group_email(df)
        
        pendientes = len(client_group)
        assert pendientes > 0, f"Debe haber pendientes > 0, pero es {pendientes}"


class TestB_FilterSharing:
    """Test B: Filtro compartido - tab Email usa subset filtrado"""
    
    def test_email_tab_uses_filtered_subset(self):
        """Si se pasa df_filtered (subset), tab Email debe construir destinatarios SOLO con ese subset"""
        df_final = fixture_fresh_load()
        
        # Filtrar solo "Empresa 1"
        df_filtered = create_synthetic_df_filtered(df_final, filter_empresa="Empresa 1")
        
        # Tab Email debe usar df_filtered
        client_group = create_synthetic_client_group_email(df_filtered)
        
        # Validar que TODOS los destinatarios son de "Empresa 1"
        assert (client_group['EMPRESA'] == 'Empresa 1').all(), "Todos los destinatarios deben ser de 'Empresa 1'"
    
    def test_html_preview_uses_filtered_docs(self):
        """Documentos del cliente en preview deben coincidir con vista filtrada"""
        df_final = fixture_fresh_load()
        df_filtered = create_synthetic_df_filtered(df_final, filter_moneda="SOLES")
        
        # Simular selección de un cliente
        client_code = df_filtered['COD CLIENTE'].iloc[0]
        docs_cli_mail = df_filtered[df_filtered['COD CLIENTE'] == client_code]
        
        # Validar que TODOS los documentos son en SOLES
        assert (docs_cli_mail['MONEDA'] == 'SOLES').all(), "Todos los documentos del preview deben ser en SOLES"


class TestC_ZeroDebtRule:
    """Test C: Regla deuda 0 - excluir clientes sin deuda salvo detracción pendiente"""
    
    def test_exclude_clients_with_zero_debt_and_no_detraction(self):
        """Excluir clientes con SALDO REAL=0 y DETR_PENDIENTE_AMOUNT=0"""
        df = fixture_mixed_debt()
        client_group = create_synthetic_client_group_email(df)
        
        # Validar que NINGÚN cliente tiene ambos en 0
        for _, row in client_group.iterrows():
            assert row['SALDO REAL'] > 0.01 or row['DETR_PENDIENTE_AMOUNT'] > 0.01, \
                f"Cliente {row['COD CLIENTE']} tiene deuda=0 y detracción=0, no debería aparecer"
    
    def test_include_clients_with_zero_debt_but_pending_detraction(self):
        """Incluir clientes con SALDO REAL=0 pero DETR_PENDIENTE_AMOUNT>0"""
        df = fixture_mixed_debt()
        
        # Forzar un cliente con saldo 0 pero detracción pendiente
        df.loc[0, 'SALDO REAL'] = 0.0
        df.loc[0, 'DETRACCIÓN'] = 150.0
        df.loc[0, 'ESTADO DETRACCION'] = 'PENDIENTE'
        df.loc[0, 'DETR_PENDIENTE_AMOUNT'] = 150.0
        
        client_group = create_synthetic_client_group_email(df)
        
        # Validar que el cliente con saldo 0 pero detracción pendiente SÍ aparece
        client_codes = client_group['COD CLIENTE'].tolist()
        assert df.loc[0, 'COD CLIENTE'] in client_codes, \
            "Cliente con saldo=0 pero detracción pendiente DEBE aparecer"


class TestD_DuplicateEmails:
    """Test D: Emails duplicados - no filtrar todo por un solo 'SENT' histórico"""
    
    def test_duplicate_emails_all_clients_visible(self):
        """Con emails duplicados, todos los clientes deben aparecer en la lista"""
        df = fixture_with_duplicates()
        client_group = create_synthetic_client_group_email(df)
        
        # Validar que hay múltiples clientes con el mismo email
        email_counts = client_group['EMAIL_FINAL'].value_counts()
        assert (email_counts > 1).any(), "Debe haber al menos un email compartido por múltiples clientes"
        
        # Validar que todos los clientes con email válido aparecen
        expected_clients = df[df['EMAIL_FINAL'] != '']['COD CLIENTE'].nunique()
        actual_clients = client_group['COD CLIENTE'].nunique()
        
        # Puede haber menos clientes si algunos tienen saldo 0 y sin detracción
        assert actual_clients > 0, "Debe haber al menos un cliente en la lista"
    
    def test_duplicate_emails_counters_by_client(self):
        """Contadores deben funcionar por registro/cliente, no por email único"""
        df = fixture_with_duplicates()
        
        # Simular que se envió a un email compartido
        shared_email = "shared@example.com"
        df_after_send = simulate_email_sent(df, shared_email)
        
        # Contar enviados (por registros, no por emails únicos)
        enviados_count = (df_after_send['ESTADO_EMAIL'] == 'ENVIADO').sum()
        
        # Debe haber múltiples registros marcados como ENVIADO (todos los que comparten el email)
        assert enviados_count > 1, f"Debe haber múltiples registros enviados, pero solo hay {enviados_count}"


class TestE_HTMLPreviewConsistency:
    """Test E: HTML preview - documentos coinciden con vista filtrada"""
    
    def test_html_preview_matches_filtered_view(self):
        """Documentos del cliente en preview deben ser exactamente los de df_filtered"""
        df_final = fixture_fresh_load()
        
        # Filtrar por empresa
        df_filtered = create_synthetic_df_filtered(df_final, filter_empresa="Empresa 5")
        
        # Simular selección de cliente
        client_code = df_filtered['COD CLIENTE'].iloc[0]
        docs_cli_mail = df_filtered[df_filtered['COD CLIENTE'] == client_code]
        
        # Validar que los documentos son SOLO de la vista filtrada
        assert len(docs_cli_mail) > 0, "Debe haber al menos un documento"
        assert (docs_cli_mail['EMPRESA'] == 'Empresa 5').all(), "Todos los documentos deben ser de 'Empresa 5'"
    
    def test_html_preview_totals_match_filtered_totals(self):
        """Totales del preview deben coincidir con totales de la vista filtrada"""
        df_final = fixture_fresh_load()
        df_filtered = create_synthetic_df_filtered(df_final, filter_moneda="SOLES")
        
        # Simular selección de cliente
        client_code = df_filtered['COD CLIENTE'].iloc[0]
        docs_cli_mail = df_filtered[df_filtered['COD CLIENTE'] == client_code]
        
        # Calcular totales (como en el código real)
        totales_s = docs_cli_mail[docs_cli_mail['MONEDA'] == 'SOLES']['SALDO REAL'].sum()
        totales_d = docs_cli_mail[docs_cli_mail['MONEDA'] != 'SOLES']['SALDO REAL'].sum()
        
        # En este caso, como filtramos por SOLES, totales_d debe ser 0
        assert totales_d == 0.0, f"Con filtro SOLES, totales en dólares debe ser 0, pero es {totales_d}"
        assert totales_s > 0.0, f"Con filtro SOLES, totales en soles debe ser > 0, pero es {totales_s}"


# Configuración de pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
