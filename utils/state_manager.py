import os
import pandas as pd
import datetime
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Local cache (legacy) -------------------------------------------------------
# ---------------------------------------------------------------------------
CACHE_DIR = ".cache"
SESSION_FILE = os.path.join(CACHE_DIR, "current_session.parquet")
META_FILE = os.path.join(CACHE_DIR, "session_meta.txt")


def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def save_session(df, metadata_str=""):
    try:
        ensure_cache_dir()
        df.to_parquet(SESSION_FILE, index=False)
        with open(META_FILE, "w", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()}|{metadata_str}")
        return True, "Sesion guardada exitosamente."
    except Exception as e:
        return False, f"Error guardando sesion: {e}"


def load_session():
    if not os.path.exists(SESSION_FILE) or not os.path.exists(META_FILE):
        return None, None, None
    try:
        df = pd.read_parquet(SESSION_FILE)
        with open(META_FILE, "r", encoding="utf-8") as f:
            content = f.read().split("|")
            timestamp_str = content[0]
            meta = content[1] if len(content) > 1 else ""
        load_time = datetime.datetime.fromisoformat(timestamp_str)
        return df, meta, load_time
    except Exception as e:
        print(f"Cache load error: {e}")
        return None, None, None


def clear_session():
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        if os.path.exists(META_FILE):
            os.remove(META_FILE)
        return True
    except Exception:
        return False


def has_valid_session():
    if os.path.exists(SESSION_FILE) and os.path.exists(META_FILE):
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                content = f.read().split("|")
                timestamp_str = content[0]
                meta = content[1] if len(content) > 1 else ""
            dt = datetime.datetime.fromisoformat(timestamp_str)
            return True, dt, meta
        except Exception:
            pass
    return False, None, None


# ---------------------------------------------------------------------------
# Mapeo de columnas: df_final <-> documentos_ciclo
# ---------------------------------------------------------------------------
# Clave: nombre exacto en df_final  →  Valor: nombre de columna en Supabase
_DF_TO_DB: Dict[str, str] = {
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

_DB_TO_DF: Dict[str, str] = {v: k for k, v in _DF_TO_DB.items()}

# Columnas numéricas en documentos_ciclo (se guardan como float, no como str)
_NUMERIC_DB_COLS = {"tipo_cambio", "mont_emit", "saldo_real", "saldo", "detraccion"}


def _df_row_to_doc(dfrow: Any, cycle_id: str, df_columns: list) -> dict:
    """Convierte una fila de df_final a un dict listo para insertar en documentos_ciclo."""
    doc: Dict[str, Any] = {"cycle_id": cycle_id}
    for df_col, db_col in _DF_TO_DB.items():
        val = dfrow[df_col] if df_col in df_columns else None
        if db_col in _NUMERIC_DB_COLS:
            if val is None or (isinstance(val, float) and pd.isna(val)):
                doc[db_col] = None
            else:
                try:
                    doc[db_col] = float(val)
                except (ValueError, TypeError):
                    doc[db_col] = None
        else:
            if val is None or (isinstance(val, float) and pd.isna(val)):
                doc[db_col] = ""
            else:
                doc[db_col] = str(val)
    return doc


def _docs_to_df(rows: list) -> pd.DataFrame:
    """Convierte filas de documentos_ciclo de vuelta a df_final con nombres de columna originales."""
    if not rows:
        return pd.DataFrame()
    df_rows = []
    for doc in rows:
        row: Dict[str, Any] = {}
        for db_col, df_col in _DB_TO_DF.items():
            row[df_col] = doc.get(db_col)
        df_rows.append(row)
    df = pd.DataFrame(df_rows)
    # Garantizar que existan todas las columnas esperadas
    for df_col in _DF_TO_DB.keys():
        if df_col not in df.columns:
            df[df_col] = ""
    # Rellenar valores nulos en columnas de tracking con defaults seguros.
    # Esto ocurre cuando la fila en documentos_ciclo tiene NULL (ciclos históricos
    # o cuando update_estado_whatsapp_in_cycle falló silenciosamente).
    _tracking_defaults = {
        "ESTADO_EMAIL":       "PENDIENTE",
        "ESTADO_WHATSAPP":    "PENDIENTE",
        "ESTADO_ENVIO_TEXTO": "",
        "FECHA_ULTIMO_ENVIO": "",
        "FECHA_ULTIMO_WA":    "",
    }
    for _col, _default in _tracking_defaults.items():
        if _col in df.columns:
            df[_col] = df[_col].fillna(_default)
    return df


# ---------------------------------------------------------------------------
# Cloud (Supabase) session persistence  --------------------------------------
# ---------------------------------------------------------------------------

def _get_supabase():
    """Get Supabase client via db_manager (avoids circular import at module level)."""
    import utils.db_manager as dbm
    return dbm.get_supabase_client()


def save_session_cloud(
    df: pd.DataFrame,
    cycle_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Guarda un ciclo en Supabase usando modelo cabecera/detalle:
    - UPSERT en ciclos_procesamiento (solo metadatos)
    - DELETE + INSERT en documentos_ciclo (una fila por documento del Excel)
    """
    client = _get_supabase()
    if not client:
        return False, "Supabase no disponible para guardar sesion."

    try:
        from utils.db_manager import _safe_execute

        # 1. Upsert cabecera (sin df_final_json)
        header = {
            "cycle_id":   cycle_id,
            "row_count":  len(df),
            "metadata":   metadata or {},
            "created_at": datetime.datetime.now().isoformat(),
            "expires_at": (
                datetime.datetime.now() + datetime.timedelta(days=30)
            ).isoformat(),
        }
        _safe_execute(
            client.table("ciclos_procesamiento")
            .upsert(header, on_conflict="cycle_id")
        )

        # 2. Borrar documentos previos del ciclo (permite re-guardar limpio)
        _safe_execute(
            client.table("documentos_ciclo")
            .delete()
            .eq("cycle_id", cycle_id)
        )

        # 3. Insertar documentos en lotes
        df_cols = list(df.columns)
        rows = [_df_row_to_doc(df.iloc[i], cycle_id, df_cols) for i in range(len(df))]

        CHUNK = 100
        for i in range(0, len(rows), CHUNK):
            _safe_execute(
                client.table("documentos_ciclo")
                .insert(rows[i:i + CHUNK])
            )

        return True, f"Sesion guardada en cloud ({len(rows)} filas)."
    except Exception as e:
        print(f"save_session_cloud Error: {e}")
        return False, f"Error guardando sesion cloud: {e}"


def load_session_cloud() -> Tuple[Optional[pd.DataFrame], Optional[Dict], Optional[datetime.datetime]]:
    """Carga el ciclo más reciente desde Supabase usando documentos_ciclo."""
    client = _get_supabase()
    if not client:
        return None, None, None

    try:
        from utils.db_manager import _safe_execute

        # Obtener el cycle_id más reciente
        res = _safe_execute(
            client.table("ciclos_procesamiento")
            .select("cycle_id, metadata, row_count, created_at")
            .order("created_at", desc=True)
            .limit(1)
        )
        rows = res.data or []
        if not rows:
            return None, None, None

        header = rows[0]
        cycle_id = header.get("cycle_id", "")
        metadata = header.get("metadata", {})
        created_str = header.get("created_at", "")

        try:
            created_at = datetime.datetime.fromisoformat(
                created_str.replace("Z", "+00:00")
            )
        except Exception:
            created_at = datetime.datetime.now()

        # Cargar documentos del ciclo
        doc_res = _safe_execute(
            client.table("documentos_ciclo")
            .select("*")
            .eq("cycle_id", cycle_id)
            .order("created_at", desc=False)
        )
        doc_rows = doc_res.data or []
        if not doc_rows:
            return None, None, None

        df = _docs_to_df(doc_rows)
        return df, metadata, created_at
    except Exception as e:
        print(f"load_session_cloud Error: {e}")
        return None, None, None


def has_valid_session_cloud() -> Tuple[bool, Optional[datetime.datetime], Optional[Dict]]:
    """Lightweight check: returns True if at least one cloud session exists."""
    client = _get_supabase()
    if not client:
        return False, None, None

    try:
        from utils.db_manager import _safe_execute
        res = _safe_execute(
            client.table("ciclos_procesamiento")
            .select("cycle_id, metadata, row_count, created_at")
            .order("created_at", desc=True)
            .limit(1)
        )
        rows = res.data or []
        if not rows:
            return False, None, None

        row = rows[0]
        created_str = row.get("created_at", "")
        try:
            created_at = datetime.datetime.fromisoformat(
                created_str.replace("Z", "+00:00")
            )
        except Exception:
            created_at = None

        metadata = row.get("metadata", {})
        metadata["row_count"] = row.get("row_count", 0)
        metadata["cycle_id"] = row.get("cycle_id", "")
        return True, created_at, metadata
    except Exception as e:
        print(f"has_valid_session_cloud Error: {e}")
        return False, None, None


def list_sessions_cloud(limit: int = 20) -> list:
    """
    Lista todos los ciclos disponibles en Supabase ordenados del mas reciente al mas antiguo.
    Retorna lista de dicts con: cycle_id, created_at, row_count, file_ctas, file_cobranza, fecha_corte.
    """
    client = _get_supabase()
    if not client:
        return []
    try:
        from utils.db_manager import _safe_execute
        res = _safe_execute(
            client.table("ciclos_procesamiento")
            .select("cycle_id, metadata, row_count, created_at")
            .order("created_at", desc=True)
            .limit(limit)
        )
        rows = res.data or []
        sessions = []
        for row in rows:
            meta = row.get("metadata") or {}
            created_str = row.get("created_at", "")
            try:
                created_at = datetime.datetime.fromisoformat(
                    created_str.replace("Z", "+00:00")
                )
            except Exception:
                created_at = None
            sessions.append({
                "cycle_id":      row.get("cycle_id", ""),
                "created_at":    created_at,
                "row_count":     row.get("row_count", 0),
                "file_ctas":     meta.get("file_ctas") or "—",
                "file_cobranza": meta.get("file_cobranza") or "—",
                "fecha_corte":   meta.get("fecha_corte") or "—",
            })
        return sessions
    except Exception as e:
        print(f"list_sessions_cloud Error: {e}")
        return []


def load_session_by_id(cycle_id: str) -> Tuple[Optional["pd.DataFrame"], Optional[Dict], Optional[datetime.datetime]]:
    """Carga un ciclo especifico por su cycle_id usando documentos_ciclo."""
    client = _get_supabase()
    if not client:
        return None, None, None
    try:
        from utils.db_manager import _safe_execute

        # Obtener metadatos de la cabecera
        hdr_res = _safe_execute(
            client.table("ciclos_procesamiento")
            .select("cycle_id, metadata, row_count, created_at")
            .eq("cycle_id", str(cycle_id).strip())
            .limit(1)
        )
        hdr_rows = hdr_res.data or []
        if not hdr_rows:
            return None, None, None

        header = hdr_rows[0]
        metadata = header.get("metadata", {})
        created_str = header.get("created_at", "")
        try:
            created_at = datetime.datetime.fromisoformat(
                created_str.replace("Z", "+00:00")
            )
        except Exception:
            created_at = datetime.datetime.now()

        # Obtener documentos del ciclo
        doc_res = _safe_execute(
            client.table("documentos_ciclo")
            .select("*")
            .eq("cycle_id", str(cycle_id).strip())
            .order("created_at", desc=False)
        )
        doc_rows = doc_res.data or []
        if not doc_rows:
            return None, None, None

        df = _docs_to_df(doc_rows)
        return df, metadata, created_at
    except Exception as e:
        print(f"load_session_by_id Error: {e}")
        return None, None, None


def clear_session_cloud() -> bool:
    """
    Elimina TODOS los ciclos de Supabase.
    documentos_ciclo se limpia automaticamente via CASCADE FK.
    ATENCION: Solo usar en reset total de datos. No llamar en flujo normal de nuevo ciclo.
    """
    client = _get_supabase()
    if not client:
        return False
    try:
        from utils.db_manager import _safe_execute
        _safe_execute(
            client.table("ciclos_procesamiento")
            .delete()
            .neq("cycle_id", "__placeholder__")
        )
        return True
    except Exception as e:
        print(f"clear_session_cloud Error: {e}")
        return False
