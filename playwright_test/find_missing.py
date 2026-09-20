import pandas as pd, psycopg2, psycopg2.extras, os
from dotenv import load_dotenv
load_dotenv()

def _fmt_codcli(v):
    try:
        return str(int(float(str(v).strip()))).zfill(6)
    except (ValueError, TypeError):
        return None

df = pd.read_excel('playwright_test/upload_temp/ctasxcob19092026.xlsx')
cxc_codes = set(filter(None, df['codcli'].apply(_fmt_codcli)))

conn = psycopg2.connect(os.getenv('DATABASE_URL'), connect_timeout=10)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute('SELECT cliente_id, nombre FROM public.clientes')
neon_rows = {str(r['cliente_id']).strip(): r['nombre'] for r in cur.fetchall()}
conn.close()

neon_ids = set(neon_rows.keys())
missing = cxc_codes - neon_ids
print(f"Clientes faltantes en Neon: {len(missing)}")
for cod in sorted(missing):
    match = df[df['codcli'].apply(lambda x: _fmt_codcli(x) == cod if pd.notna(x) else False)]
    nombre_cxc = match['nomcli'].iloc[0] if not match.empty and 'nomcli' in match.columns else '(sin nombre en CxC)'
    print(f"  Codigo: {cod} | Nombre en CxC: {nombre_cxc}")
