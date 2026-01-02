import pandas as pd
import numpy as np

# Mock data based on User Report
data = {
    'COD CLIENTE': ['000150', '000150', '000150', '000150'],
    'EMPRESA': ['DIPASPAN PERU S.A.C.', 'DIPASPAN PERU S.A.C.', 'DIPASPAN PERU S.A.C.', 'DIPASPAN PERU S.A.C.'],
    'MONEDA': ['S/.', 'S/.', 'US$', 'US$'],
    'SALDO REAL': [70.80, 70.80, 129.80, 129.80], # Trying as floats first (expected)
    'DETRACCIÓN': [0.0, 0.0, 0.0, 0.0],
    'ESTADO DETRACCION': ['No Aplica', 'No Aplica', 'No Aplica', 'No Aplica']
}
df_float = pd.DataFrame(data)

# Mock data as Strings (Possible Malfunction)
data_str = {
    'COD CLIENTE': ['000150', '000150', '000150', '000150'],
    'EMPRESA': ['DIPASPAN PERU S.A.C.', 'DIPASPAN PERU S.A.C.', 'DIPASPAN PERU S.A.C.', 'DIPASPAN PERU S.A.C.'],
    'MONEDA': ['S/.', 'S/.', 'US$', 'US$'],
    'SALDO REAL': ['S/ 70.80', 'S/ 70.80', '$ 129.80', '$ 129.80'], # Strings
    'DETRACCIÓN': [0.0, 0.0, 0.0, 0.0],
    'ESTADO DETRACCION': ['No Aplica', 'No Aplica', 'No Aplica', 'No Aplica']
}
df_str = pd.DataFrame(data_str)

def test_logic(df, label):
    print(f"--- Testing {label} ---")
    print("Types in SALDO REAL:", df['SALDO REAL'].apply(type).unique())
    
    try:
        mask_soles = df['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
        df_sol = df[mask_soles]
        df_dol = df[~mask_soles]
        
        sum_s = df_sol['SALDO REAL'].sum()
        sum_d = df_dol['SALDO REAL'].sum()
        
        print(f"Sum Soles: {sum_s} (Type: {type(sum_s)})")
        print(f"Sum USD: {sum_d} (Type: {type(sum_d)})")
        
        count_s = len(df_sol)
        # Attempt Format
        kpi_dacta_s = f"S/ {sum_s:,.2f} ({count_s:02d} documentos)"
        print("KPI S: Success ->", kpi_dacta_s)
        
    except Exception as e:
        print(f"CRASH: {e}")

test_logic(df_float, "FLOAT DATA")
test_logic(df_str, "STRING DATA")
