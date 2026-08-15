"""
Prueba de performance — Generación de ciclo nuevo.
Simula el flujo completo de app.py sin la UI de Streamlit.
Ejecutar con: python test_perf_ciclo.py
"""
import time
import os
import sys
from pathlib import Path
from datetime import datetime

# Cargar credenciales ANTES de importar cualquier módulo del proyecto
from dotenv import load_dotenv
load_dotenv(".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
if not SUPABASE_URL:
    print("❌ SUPABASE_URL no encontrado en .env")
    sys.exit(1)

import pandas as pd
import utils.db_manager as dbm
import utils.supabase_cycle_service as scs
from utils.processing import process_data
import utils.state_manager as state_mgr

PATH_CTAS = Path("test_data/cta_cobrar_150826.xlsx")
PATH_COB  = Path("test_data/det_cobranza_150826.xlsx")

SEP = "=" * 62

def hdr(n, texto):
    print(f"\n[{n}] {texto}...")

def ok(seg, extra=""):
    tag = f"  [OK]  {seg:.2f}s"
    print(tag + (f"  -- {extra}" if extra else ""))

def err(msg):
    print(f"  [ERROR]  {msg}")

print("\n" + SEP)
print("   PRUEBA DE PERFORMANCE - GENERACION DE CICLO NUEVO")
print(f"   Supabase: {SUPABASE_URL[:50]}...")
print(SEP)

timings = {}
t_total = time.perf_counter()

# ── 1. Conexión ─────────────────────────────────────────────────────────────
hdr(1, "Inicializando conexión Supabase")
t = time.perf_counter()
if not dbm.initialize_db():
    err(dbm.get_last_error())
    sys.exit(1)
timings["1_conexion"] = time.perf_counter() - t
ok(timings["1_conexion"])

# ── 2. Lectura Excel ────────────────────────────────────────────────────────
hdr(2, "Leyendo archivos Excel")
t = time.perf_counter()
df_ctas_raw     = pd.read_excel(PATH_CTAS)
df_cobranza_raw = pd.read_excel(PATH_COB)
timings["2_excel"] = time.perf_counter() - t
ok(timings["2_excel"], f"CxC={len(df_ctas_raw)} filas | Cobranza={len(df_cobranza_raw)} filas")

# ── 3. Cartera maestra desde Supabase ───────────────────────────────────────
hdr(3, "Descargando cartera maestra desde Supabase")
t = time.perf_counter()
cartera_rows = dbm.get_clientes_master(limit=50000)
timings["3_cartera"] = time.perf_counter() - t
if not cartera_rows:
    err(f"Sin cartera maestra: {dbm.get_last_error()}")
    sys.exit(1)
df_cartera_raw = pd.DataFrame(cartera_rows).rename(columns={
    "cliente_id":  "codigo_cliente",
    "nombre":      "nombre_cliente",
    "email":       "correo",
    "enviar_email":"Enviar Email",
    "estado":      "estado_cliente",
    "notas":       "nota",
})
ok(timings["3_cartera"], f"{len(df_cartera_raw)} clientes")

# ── 4. process_data ─────────────────────────────────────────────────────────
hdr(4, "Cruzando datos (process_data)")
t = time.perf_counter()
df_final = process_data(df_ctas_raw, df_cartera_raw, df_cobranza_raw)
timings["4_process"] = time.perf_counter() - t
ok(timings["4_process"], f"df_final={len(df_final)} filas")

# ── Generar cycle_id ────────────────────────────────────────────────────────
cycle_id = datetime.now().strftime("CIC-%Y%m%d-%H%M")
print(f"\n   Cycle ID: {cycle_id}")

# ── 5. Limpiar ledger TTL ───────────────────────────────────────────────────
hdr(5, "Limpiando ledger TTL (clear_all_ledger)")
t = time.perf_counter()
ok_ledger = dbm.clear_all_ledger()
timings["5_ledger"] = time.perf_counter() - t
ok(timings["5_ledger"]) if ok_ledger else err("Fallo clear_all_ledger")  # noqa

# ── 6. persist_cycle_to_supabase ────────────────────────────────────────────
hdr(6, "Persistiendo ciclo (clientes + documentos + cobranzas)")
t = time.perf_counter()
result = scs.persist_cycle_to_supabase(
    df_ctas=df_ctas_raw,
    df_cartera=df_cartera_raw,
    df_cobranza=df_cobranza_raw,
)
timings["6_persist"] = time.perf_counter() - t
if result.get("ok"):
    c = result["counts"]
    ok(timings["6_persist"],
       f"clientes={c.get('clientes',0)} | docs={c.get('documentos',0)} | cob={c.get('cobranzas',0)}")
    errs = result.get("errors", {})
    if any(v > 0 for v in errs.values()):
        print(f"  ⚠️   Filas con error: {errs}")
        samples = result.get("error_samples", {})
        for tabla, sample in samples.items():
            if sample:
                print(f"       {tabla}: {sample[0]}")
else:
    err(result.get("message", "Error desconocido"))
    sys.exit(1)

# ── 7. save_session_cloud ───────────────────────────────────────────────────
hdr(7, "Guardando sesión en la nube (documentos_ciclo)")
t = time.perf_counter()
ok_cloud, msg_cloud = state_mgr.save_session_cloud(
    df=df_final,
    cycle_id=cycle_id,
    metadata={"cycle_id": cycle_id, "row_count": len(df_final)},
)
timings["7_session"] = time.perf_counter() - t
ok(timings["7_session"], msg_cloud) if ok_cloud else err(msg_cloud)  # noqa

# Resumen
total = time.perf_counter() - t_total

print("\n" + SEP)
print("   RESUMEN DE TIEMPOS")
print(SEP)


labels = [
    ("1_conexion", "Conexión Supabase"),
    ("2_excel",    "Lectura Excel (2 archivos)"),
    ("3_cartera",  "Cartera maestra (Supabase)"),
    ("4_process",  "process_data — cruce y cálculo"),
    ("5_ledger",   "Limpiar ledger TTL"),
    ("6_persist",  "persist_cycle (clientes+docs+cob)"),
    ("7_session",  "save_session_cloud (docs_ciclo)"),
]

for key, label in labels:
    val = timings.get(key, 0)
    bar = "█" * max(1, int(val * 4))
    print(f"  {label:<38} {val:5.2f}s  {bar}")

print(f"\n  {'TOTAL':<38} {total:5.2f}s")
print(SEP)
print(f"\n  [OK] Ciclo generado: {cycle_id}\n")
