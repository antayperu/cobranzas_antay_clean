
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_excel_files(num_clients=57):
    # 1. Cartera (Master Data)
    clients = []
    for i in range(1, num_clients + 1):
        code = f"{i:06d}"
        clients.append({
            'codigo_cliente': code,
            'codcli': code,
            'nomcli': f'Cliente Prueba {i}',
            'CORREO': f'test_client_{i}@example.com',
            'telefono': f'999000{i:03d}',
            'NOTA': ''
        })
    df_cartera = pd.DataFrame(clients)
    df_cartera.to_excel("Cartera_Test.xlsx", index=False)
    print(f"Generated Cartera_Test.xlsx with {len(df_cartera)} clients")

    # 2. CtasxCobrar (Documents)
    docs = []
    today = datetime.now()
    for i in range(1, num_clients + 1):
        code = f"{i:06d}"
        # Each client has 2 docs
        for d in range(1, 3):
            docs.append({
                'codcli': code,
                'coddoc': '01',
                'sersun': 'F001',
                'numsun': f"{i*100 + d}", # Ensure unique numbers
                'fecdoc': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
                'fecvct': (today - timedelta(days=5)).strftime('%Y-%m-%d'), # Overdue
                'mondoc': 100.0 * d,
                'sldacl': 100.0 * d, # Saldo = Monto (No payments)
                'codmnd': 'SOL',
                'tipcam': 3.80,
                'mododo': 100.0 * d,
                # Extra cols to satisfy generic load
                'tipped': 'VENTA'
            })
    df_ctas = pd.DataFrame(docs)
    df_ctas.to_excel("Ctas_Test.xlsx", index=False)
    print(f"Generated Ctas_Test.xlsx with {len(df_ctas)} documents")

    # 3. Cobranza (Payments/Detractions - Empty for this test to keep it simple)
    # Or add one detraction for testing logic if needed, but for persistence test, simple balance is enough.
    df_cob = pd.DataFrame(columns=['coddoc', 'numsun', 'forpag', 'monpag', 'fecpro', 'nombco', 'codbco', 'nudopa'])
    df_cob.to_excel("Cobranza_Test.xlsx", index=False)
    print("Generated Cobranza_Test.xlsx (Empty)")

if __name__ == "__main__":
    generate_excel_files()
