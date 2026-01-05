
import os
import pandas as pd
from utils import email_sender

# Mock Data - Scenario A (With Detraccion)
mock_df_A = pd.DataFrame([
    {
        'COMPROBANTE': 'F001-0001234', 'FECH EMIS': '2025-01-10', 'FECH VENC': '2025-01-25',
        'MONEDA': 'Soles', 'MONT EMIT': 1500.00, 'SALDO REAL': 1500.00, 'DETRACCIÓN': 0.0, 'ESTADO DETRACCION': 'NO APLICA'
    },
    {
        'COMPROBANTE': 'F001-0001236', 'FECH EMIS': '2025-01-12', 'FECH VENC': '2025-01-27',
        'MONEDA': 'Soles', 'MONT EMIT': 2000.00, 'SALDO REAL': 0.00, 'DETRACCIÓN': 240.0, 'ESTADO DETRACCION': 'PENDIENTE'
    }
])

# Mock Data - Scenario B (No Detraccion)
mock_df_B = pd.DataFrame([
    {
        'COMPROBANTE': 'F001-0001234', 'FECH EMIS': '2025-01-10', 'FECH VENC': '2025-01-25',
        'MONEDA': 'Soles', 'MONT EMIT': 1500.00, 'SALDO REAL': 1500.00, 'DETRACCIÓN': 0.0, 'ESTADO DETRACCION': 'NO APLICA'
    }
])

# SCENARIO A: Corporate Logo + Intro + Footer + Detraccion
config_a = {
    'company_name': 'DACTA S.A.C.',
    'company_ruc': '20601995817',
    'primary_color': '#2E86AB',
    'secondary_color': '#A23B72',
    'logo_path': 'fake_logo.png', # Simulates Having a Logo
    'email_template': {
        'intro_text': "Hola Cliente A,\nEsta es una prueba de INTRO con saltos de línea.\n<script>alert(\"no injection\")</script>",
        'footer_text': "Footer Personalizado\nLínea 2 de Footer.",
        'alert_text': "⚠️ IMPORTANTE: Ud. tiene detracciones pendientes.\nFavor regularizar."
    }
}

# SCENARIO B: NO LOGO + No Detraccion + Default Footer
config_b = {
    'company_name': 'EMPRESA SIN LOGO',
    'company_ruc': '12345678900',
    'primary_color': '#FF0000',
    'secondary_color': '#000000',
    'logo_path': '', # Simulates NO LOGO
    'email_template': {
        'intro_text': "Intro en una sola línea.",
        'footer_text': "", # Empty -> Default Signature
        'alert_text': ""
    }
}

# Scenario A
html_A = email_sender.generate_premium_email_body_cid("Cliente A", mock_df_A, "S/ 1,500.00", "US$ 0.00", config_a)
with open("preview_scenario_A.html", "w", encoding="utf-8") as f:
    f.write(html_A)

# Scenario B
html_B = email_sender.generate_premium_email_body_cid("Cliente B", mock_df_B, "S/ 1,500.00", "US$ 0.00", config_b)
with open("preview_scenario_B.html", "w", encoding="utf-8") as f:
    f.write(html_B)

print("Generated: preview_scenario_A.html (With Detraccion)")
print("Generated: preview_scenario_B.html (No Detraccion)")

