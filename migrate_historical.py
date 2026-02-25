"""
migrate_historical.py
=====================
Migra datos históricos desde archivos Excel de ciclos previos hacia Supabase.

Tablas que se poblan:
  - ciclos_procesamiento  (upsert por cycle_id — solo metadatos, SIN df_final_json)
  - documentos_ciclo      (insert — una fila por documento del Excel)
  - notificaciones        (insert — un registro por cliente con email ENVIADO)

Tablas que NO se tocan:
  - clientes              (ya tienen data correcta en Supabase — NO se upsertea)
  - gestiones             (emails históricos NO van a gestiones — regla de routing)

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
# Mapeo de columnas Excel → documentos_ciclo (igual que state_manager)
# ---------------------------------------------------------------------------
_DF_TO_DB = {
    "COD CLIENTE":        "cod_cliente",
    "EMPRESA":            "empresa",
    "Enviar Email":       "enviar_email",
    "NOTA":               "nota",
    "CORREO":             "correo",
    "TELÉFONO":           "telefono",
    "TIPO PEDIDO":        "tipo_pedido",
    "COMPROBANTE":        "comprobante",
    "FECH EMIS":          "fech_emis",
    "FECH VENC":          "fech_venc",
    "DÍAS MORA":          "dias_mora",
    "ESTADO DEUDA":       "estado_deuda",
    "MONEDA":             "moneda",
    "TIPO CAMBIO":        "tipo_cambio",
    "MONT EMIT":          "mont_emit",
    "MONT EMIT_DISPLAY":  "mont_emit_display",
    "SALDO REAL":         "saldo_real",
    "SALDO REAL_DISPLAY": "saldo_real_display",
    "SALDO":              "saldo",
    "SALDO_DISPLAY":      "saldo_display",
    "DETRACCIÓN":         "detraccion",
    "DETRACCIÓN_DISPLAY": "detraccion_display",
    "ESTADO DETRACCION":  "estado_detraccion",
    "AMORTIZACIONES":     "amortizaciones",
    "MATCH_KEY":          "match_key",
    "EMAIL_FINAL":        "email_final",
    "ESTADO_EMAIL":       "estado_email",
    "FECHA_ULTIMO_ENVIO": "fecha_ultimo_envio",
    "ESTADO_WHATSAPP":    "estado_whatsapp",
    "FECHA_ULTIMO_WA":    "fecha_ultimo_wa",
}

_NUMERIC_DB_COLS = {"tipo_cambio", "mont_emit", "saldo_real", "saldo", "detraccion"}


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


# Renombres para normalizar columnas de Excel histórico al formato de df_final
_EXCEL_RENAMES = {
    "ENVIAR EMAIL": "Enviar Email",  # históricos usan mayúsculas; df_final usa title case
}


def normalize_excel_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra columnas del Excel histórico al formato esperado por _DF_TO_DB."""
    return df.rename(columns=_EXCEL_RENAMES)


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


def safe_num(val):
    """Convierte a float o retorna None si es NaN/None."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# PASO 0: Insert clientes faltantes (solo los que no existen — no sobrescribe)
# ---------------------------------------------------------------------------
def insert_clientes_missing(client, df: pd.DataFrame, dry_run: bool) -> int:
    """
    Inserta clientes que no existen en la tabla clientes.
    Usa upsert con ignoreDuplicates=True para NO sobrescribir data actual.
    """
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
        print(f"    [DRY] clientes insert-if-missing: {len(batch)}")
        return len(batch)

    CHUNK = 100
    for i in range(0, len(batch), CHUNK):
        # ignore_duplicates=True → INSERT ... ON CONFLICT DO NOTHING (no sobrescribe)
        client.table("clientes").upsert(
            batch[i:i + CHUNK],
            on_conflict="cliente_id",
            ignore_duplicates=True,
        ).execute()
    return len(batch)


# ---------------------------------------------------------------------------
# PASO 1: Insert ciclo_procesamiento (cabecera) + documentos_ciclo (detalle)
# ---------------------------------------------------------------------------
def insert_ciclo_con_documentos(
    client, cycle_id: str, fecha_iso: str, df: pd.DataFrame, dry_run: bool
) -> int:
    """
    Inserta cabecera en ciclos_procesamiento y una fila por documento en documentos_ciclo.
    Retorna la cantidad de documentos insertados.
    """
    if dry_run:
        print(f"    [DRY] ciclo upsert: {cycle_id} ({len(df)} filas)")
        return len(df)

    # Cabecera (sin df_final_json)
    header = {
        "cycle_id":   cycle_id,
        "row_count":  len(df),
        "metadata":   {"source": "migration_historica", "archivo_origen": cycle_id},
        "created_at": fecha_iso,
        "expires_at": None,
    }
    client.table("ciclos_procesamiento").upsert(header, on_conflict="cycle_id").execute()

    # Borrar documentos previos del ciclo (idempotente)
    client.table("documentos_ciclo").delete().eq("cycle_id", cycle_id).execute()

    # Construir filas para documentos_ciclo
    df_cols = list(df.columns)
    rows = []
    for i in range(len(df)):
        dfrow = df.iloc[i]
        doc = {"cycle_id": cycle_id}
        for df_col, db_col in _DF_TO_DB.items():
            val = dfrow[df_col] if df_col in df_cols else None
            if db_col in _NUMERIC_DB_COLS:
                doc[db_col] = safe_num(val)
            else:
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    doc[db_col] = ""
                else:
                    doc[db_col] = str(val)
        rows.append(doc)

    CHUNK = 100
    for i in range(0, len(rows), CHUNK):
        client.table("documentos_ciclo").insert(rows[i:i + CHUNK]).execute()

    return len(rows)


# ---------------------------------------------------------------------------
# PASO 2: Notificaciones (solo emails ENVIADO — regla de routing)
# ---------------------------------------------------------------------------
def insert_notificaciones(
    client, cycle_id: str, fecha_iso: str, df: pd.DataFrame, dry_run: bool
) -> int:
    """
    Inserta en notificaciones un registro por cliente con ESTADO_EMAIL = ENVIADO.
    NO escribe en gestiones (regla maestra: email → notificaciones solamente).
    """
    estado_col = find_col(df, 'ESTADO_EMAIL', 'ESTADO_ENVIO')
    fecha_col  = find_col(df, 'FECHA_ULTIMO_ENVIO')

    if not estado_col:
        print("    ADVERTENCIA: columna de estado no encontrada — saltando notificaciones.")
        return 0

    # Borrar notificaciones previas del ciclo (idempotente)
    if not dry_run:
        client.table("notificaciones").delete().eq("cycle_id", cycle_id).execute()

    df_sent = df[df[estado_col].astype(str).str.strip().str.upper() == 'ENVIADO'].copy()
    if df_sent.empty:
        print("    Sin registros ENVIADO en este archivo.")
        return 0

    # Agregar por cliente (múltiples documentos → un registro de envío por cliente)
    agg_cols = {'EMPRESA': 'first', 'CORREO': 'first', 'SALDO REAL': 'sum'}
    if fecha_col:
        agg_cols[fecha_col] = 'first'

    clientes_env = (
        df_sent.groupby('COD CLIENTE')
        .agg(agg_cols)
        .reset_index()
    )

    notif_rows = []
    for _, row in clientes_env.iterrows():
        cod = safe(row['COD CLIENTE'])
        if not cod:
            continue

        fecha_env = safe(row.get(fecha_col)) if fecha_col and safe(row.get(fecha_col)) else fecha_iso
        saldo     = float(row.get('SALDO REAL', 0) or 0)
        correo    = safe(row.get('CORREO', ''))
        destino   = correo.split(',')[0].strip() if correo else cod

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
        print(f"    [DRY] notificaciones: {len(notif_rows)}")
        return len(notif_rows)

    CHUNK = 100
    n_ok = 0
    for i in range(0, len(notif_rows), CHUNK):
        client.table("notificaciones").insert(notif_rows[i:i + CHUNK]).execute()
        n_ok += len(notif_rows[i:i + CHUNK])

    return n_ok


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

    total_docs = total_n = 0
    print(f"\n{len(files)} archivos a procesar:\n")

    for fname in files:
        path = os.path.join(HISTORICAL_DIR, fname)
        cycle_id, fecha_iso = parse_filename(fname)

        print("-" * 60)
        print(f"Archivo  : {fname}")
        print(f"cycle_id : {cycle_id}   fecha: {fecha_iso}")

        try:
            df = normalize_excel_columns(pd.read_excel(path, dtype={"COD CLIENTE": str}))
            print(f"Filas    : {len(df)}")

            # 0. Clientes faltantes (insert-if-missing, no sobrescribe)
            n_cli = insert_clientes_missing(client, df, dry_run)
            print(f"  Clientes (nuevos)    : {n_cli}")

            # 1. Ciclo (cabecera) + documentos_ciclo (detalle)
            n_docs = insert_ciclo_con_documentos(client, cycle_id, fecha_iso, df, dry_run)
            print(f"  Documentos insertados: {n_docs}")
            total_docs += n_docs

            # 2. Notificaciones (solo emails ENVIADO — NO gestiones)
            n = insert_notificaciones(client, cycle_id, fecha_iso, df, dry_run)
            print(f"  Notificaciones       : {n}")
            total_n += n

        except Exception as e:
            print(f"  ERROR procesando {fname}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n" + "=" * 60)
    print(f"RESUMEN {'(DRY-RUN) ' if dry_run else ''}| {len(files)} archivos procesados")
    print(f"  Documentos insertados: {total_docs}")
    print(f"  Notificaciones       : {total_n}")
    print("DONE.")


if __name__ == "__main__":
    main()
