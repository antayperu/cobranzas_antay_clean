"""
migrate_historical.py
=====================
Migra datos históricos desde archivos Excel de ciclos previos hacia Supabase.

Tablas que se poblan:
  - clientes              (upsert por cliente_id)
  - ciclos_procesamiento  (upsert por cycle_id)
  - gestiones             (insert — un registro por cliente enviado)
  - notificaciones        (insert — un registro por cliente enviado)

Uso:
  py migrate_historical.py              # Ejecuta la migración real
  py migrate_historical.py --dry-run    # Simula sin tocar Supabase
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

HISTORICAL_DIR = os.path.join(os.path.dirname(__file__), "data", "historical_cycles")


# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------
def get_client():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise EnvironmentError(
            "Faltan variables de entorno: SUPABASE_URL y/o SUPABASE_SERVICE_ROLE_KEY"
        )
    return create_client(url, key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_filename(filename: str):
    """
    Extrae cycle_id y fecha ISO desde el nombre de archivo.
    Ej: DACTA_S.A.C._ReporteCobranzas_20251230_1453.xlsx
    Retorna: ('HIST_20251230_1453', '2025-12-30T14:53:00')
    """
    base = os.path.splitext(filename)[0]
    parts = base.split("_")
    hhmm     = parts[-1]       # '1453'
    yyyymmdd = parts[-2]       # '20251230'
    cycle_id = f"HIST_{yyyymmdd}_{hhmm}"
    fecha_iso = (
        f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
        f"T{hhmm[:2]}:{hhmm[2:]}:00"
    )
    return cycle_id, fecha_iso


def find_col(df: pd.DataFrame, *candidates) -> str | None:
    """Retorna el primer nombre de columna que exista en el DataFrame."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def safe(val) -> str:
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    return str(val).strip()


# ---------------------------------------------------------------------------
# PASO 1: Upsert clientes
# ---------------------------------------------------------------------------
def upsert_clientes(client, df: pd.DataFrame, dry_run: bool) -> int:
    # Columna teléfono puede tener encoding roto en el nombre
    tel_col = find_col(df, 'TELÉFONO', 'TELEFONO', 'TEL\ufffdFONO')

    seen = {}
    for _, row in df.iterrows():
        cod = safe(row.get('COD CLIENTE'))
        if not cod or cod in seen:
            continue
        email_raw = safe(row.get('CORREO', ''))
        email_first = email_raw.split(',')[0].strip() if email_raw else None
        telefono = safe(row.get(tel_col, '')) if tel_col else None
        seen[cod] = {
            "cliente_id": cod,
            "nombre": safe(row.get('EMPRESA', cod)) or cod,
            "email": email_first or None,
            "telefono": telefono or None,
            "estado": "ACTIVO",
        }

    if not seen:
        return 0

    batch = list(seen.values())
    if dry_run:
        print(f"    [DRY] clientes upsert: {len(batch)}")
        return len(batch)

    CHUNK = 100
    for i in range(0, len(batch), CHUNK):
        client.table("clientes").upsert(batch[i:i+CHUNK], on_conflict="cliente_id").execute()
    return len(batch)


# ---------------------------------------------------------------------------
# PASO 2: Insert ciclo_procesamiento
# ---------------------------------------------------------------------------
def insert_ciclo(client, cycle_id: str, fecha_iso: str, df: pd.DataFrame, dry_run: bool):
    df_clean = df.copy()
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].astype(str).replace("nan", "")
    records = df_clean.to_dict(orient="records")

    payload = {
        "cycle_id": cycle_id,
        "df_final_json": records,
        "row_count": len(records),
        "metadata": {"source": "migration_historica", "archivo_origen": cycle_id},
        "created_at": fecha_iso,
        "expires_at": None,
    }

    if dry_run:
        print(f"    [DRY] ciclo upsert: {cycle_id} ({len(records)} filas)")
        return

    client.table("ciclos_procesamiento").upsert(payload, on_conflict="cycle_id").execute()


# ---------------------------------------------------------------------------
# PASO 3: Gestiones + Notificaciones (un registro por cliente enviado)
# ---------------------------------------------------------------------------
def insert_gestiones_notificaciones(
    client, cycle_id: str, fecha_iso: str, df: pd.DataFrame, dry_run: bool
):
    estado_col = find_col(df, 'ESTADO_EMAIL', 'ESTADO_ENVIO')
    fecha_col  = find_col(df, 'FECHA_ULTIMO_ENVIO')
    tel_col    = find_col(df, 'TELÉFONO', 'TELEFONO', 'TEL\ufffdFONO')

    if not estado_col:
        print("    ADVERTENCIA: columna de estado no encontrada — saltando gestiones.")
        return 0, 0

    df_sent = df[df[estado_col].astype(str).str.strip().str.upper() == 'ENVIADO'].copy()
    if df_sent.empty:
        print("    Sin registros ENVIADO en este archivo.")
        return 0, 0

    # Agregar saldo y datos por cliente (múltiples docs → un envío por cliente)
    agg_cols = {'EMPRESA': 'first', 'CORREO': 'first', 'SALDO REAL': 'sum'}
    if tel_col:
        agg_cols[tel_col] = 'first'
    if fecha_col:
        agg_cols[fecha_col] = 'first'

    clientes_env = (
        df_sent.groupby('COD CLIENTE')
        .agg(agg_cols)
        .reset_index()
    )

    gest_rows  = []
    notif_rows = []

    for _, row in clientes_env.iterrows():
        cod = safe(row['COD CLIENTE'])
        if not cod:
            continue

        # Fecha de envío: desde el Excel si existe, sino la del nombre de archivo
        if fecha_col and safe(row.get(fecha_col)):
            fecha_env = safe(row.get(fecha_col))
        else:
            fecha_env = fecha_iso

        saldo  = float(row.get('SALDO REAL', 0) or 0)
        correo = safe(row.get('CORREO', ''))
        destino = correo.split(',')[0].strip() if correo else cod

        gest_rows.append({
            "cliente_id":  cod,
            "tipo_gestion": "EMAIL",
            "canal":        "EMAIL",
            "resultado":    "EXITOSO",
            "notas":        f"Migrado desde {cycle_id} | Saldo: S/ {saldo:,.2f}",
            "fecha":        fecha_env,
            "metadata":     {"cycle_id": cycle_id, "migrated": True},
        })

        notif_rows.append({
            "tipo_notificacion": "INFO",
            "prioridad":         "NORMAL",
            "cliente_id":        cod,
            "destinatario":      destino.lower(),
            "asunto":            f"Estado de Cuenta — ciclo {cycle_id}",
            "mensaje":           f"Saldo total notificado: S/ {saldo:,.2f}",
            "estado":            "ENVIADO",
            "fecha_envio":       fecha_env,
            "metadata":          {"cycle_id": cycle_id, "migrated": True, "channel": "EMAIL"},
            "cycle_id":          cycle_id,
        })

    if dry_run:
        print(f"    [DRY] gestiones: {len(gest_rows)} | notificaciones: {len(notif_rows)}")
        return len(gest_rows), len(notif_rows)

    CHUNK = 100
    g_ok = n_ok = 0
    for i in range(0, len(gest_rows), CHUNK):
        client.table("gestiones").insert(gest_rows[i:i+CHUNK]).execute()
        g_ok += len(gest_rows[i:i+CHUNK])
    for i in range(0, len(notif_rows), CHUNK):
        client.table("notificaciones").insert(notif_rows[i:i+CHUNK]).execute()
        n_ok += len(notif_rows[i:i+CHUNK])

    return g_ok, n_ok


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Migra ciclos históricos Excel → Supabase"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simula la migración sin insertar nada en Supabase"
    )
    args = parser.parse_args()
    dry_run = args.dry_run

    if dry_run:
        print("=" * 60)
        print("MODO DRY-RUN - no se escribira nada en Supabase")
        print("=" * 60)

    files = sorted([f for f in os.listdir(HISTORICAL_DIR) if f.endswith('.xlsx')])
    if not files:
        print(f"No se encontraron archivos .xlsx en:\n  {HISTORICAL_DIR}")
        sys.exit(1)

    client = None if dry_run else get_client()

    total_g = total_n = 0
    print(f"\n{len(files)} archivos a procesar:\n")

    for fname in files:
        path = os.path.join(HISTORICAL_DIR, fname)
        cycle_id, fecha_iso = parse_filename(fname)

        print("-" * 60)
        print(f"Archivo  : {fname}")
        print(f"cycle_id : {cycle_id}   fecha: {fecha_iso}")

        try:
            df = pd.read_excel(path)
            print(f"Filas    : {len(df)}")

            # 1. Clientes — reactivado: CLEAN script los borró con CASCADE
            n_cli = upsert_clientes(client, df, dry_run)
            print(f"  Clientes upserted   : {n_cli}")

            # 2. Ciclo
            insert_ciclo(client, cycle_id, fecha_iso, df, dry_run)
            print(f"  Ciclo registrado    : OK")

            # 3. Gestiones + Notificaciones
            g, n = insert_gestiones_notificaciones(client, cycle_id, fecha_iso, df, dry_run)
            print(f"  Gestiones           : {g}")
            print(f"  Notificaciones      : {n}")
            total_g += g
            total_n += n

        except Exception as e:
            print(f"  ERROR procesando {fname}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n" + "=" * 60)
    print(f"RESUMEN {'(DRY-RUN) ' if dry_run else ''}| {len(files)} archivos procesados")
    print(f"  Gestiones insertadas: {total_g}")
    print(f"  Notificaciones      : {total_n}")
    print("DONE.")


if __name__ == "__main__":
    main()
