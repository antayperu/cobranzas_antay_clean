
import pandas as pd
import utils.email_sender as es
import utils.helpers as helpers

# Mock Config
CONFIG = {
    'company_name': 'Test Corp',
    'primary_color': '#000000',
    'secondary_color': '#ffffff',
    'email_template': {'intro_text': 'Hola', 'footer_text': 'Chau'},
    'company_ruc': '20000000001'
}

# Mock Data (Based on user screenshot)
# Columns found in app.py view_cols
df_data = {
    'COD CLIENTE': ['000150']*4,
    'EMPRESA': ['DIPASPAN PERU S.A.C.']*4,
    'MONEDA': ['S/.', 'S/.', 'US$', 'US$'],
    'SALDO REAL': ['S/ 70.80', 'S/ 70.80', '$ 129.80', '$ 129.80'],
    'DETRACCIÓN': ['S/ 0.00', 'S/ 0.00', 'S/ 0.00', 'S/ 0.00'],
    'ESTADO DETRACCION': ['No Aplica', 'No Aplica', 'No Aplica', 'No Aplica'],
    'COMPROBANTE': ['F001-1', 'F001-2', 'F001-3', 'F001-4'],
    'FECH EMIS': ['2025-01-01']*4,
    'FECH VENC': ['2025-01-15']*4,
    'MONT EMIT': ['100', '100', '100', '100']
}

df = pd.DataFrame(df_data)

print("--- STARTING SIMULATION ---")
try:
    # Call the function
    html_body = es.generate_premium_email_body_cid("DIPASPAN", df, "S/ 100", "$ 100", CONFIG)
    print("--- SUCCESS ---")
    if "Error calculando totales" in html_body:
        print("RESULT: ERROR FOUND IN HTML")
        print(html_body)
    else:
        print("RESULT: HTML Generated OK")
except Exception as e:
    print(f"--- CRITICAL FAILURE: {e}")
    import traceback
    traceback.print_exc()
