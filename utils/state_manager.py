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
    """Save processing cycle snapshot to Supabase for session restoration."""
    client = _get_supabase()
    if not client:
        return False, "Supabase no disponible para guardar sesion."

    try:
        # Serialize DataFrame — convert problematic types first
        df_clean = df.copy()
        for col in df_clean.columns:
            if df_clean[col].dtype == "datetime64[ns]" or "datetime" in str(df_clean[col].dtype):
                df_clean[col] = df_clean[col].astype(str)
            elif df_clean[col].dtype == "object":
                df_clean[col] = df_clean[col].fillna("").astype(str)

        records = df_clean.to_dict(orient="records")

        payload = {
            "cycle_id": cycle_id,
            "df_final_json": records,
            "metadata": metadata or {},
            "row_count": len(records),
            "created_at": datetime.datetime.now().isoformat(),
            "expires_at": (
                datetime.datetime.now() + datetime.timedelta(days=30)
            ).isoformat(),
        }

        from utils.db_manager import _safe_execute
        _safe_execute(
            client.table("ciclos_procesamiento")
            .upsert(payload, on_conflict="cycle_id")
        )
        return True, f"Sesion guardada en cloud ({len(records)} filas)."
    except Exception as e:
        print(f"save_session_cloud Error: {e}")
        return False, f"Error guardando sesion cloud: {e}"


def load_session_cloud() -> Tuple[Optional[pd.DataFrame], Optional[Dict], Optional[datetime.datetime]]:
    """Load the most recent processing cycle from Supabase."""
    client = _get_supabase()
    if not client:
        return None, None, None

    try:
        from utils.db_manager import _safe_execute
        res = _safe_execute(
            client.table("ciclos_procesamiento")
            .select("cycle_id, df_final_json, metadata, row_count, created_at")
            .order("created_at", desc=True)
            .limit(1)
        )
        rows = res.data or []
        if not rows:
            return None, None, None

        row = rows[0]
        records = row.get("df_final_json", [])
        if not records:
            return None, None, None

        df = pd.DataFrame(records)
        metadata = row.get("metadata", {})
        created_str = row.get("created_at", "")

        try:
            created_at = datetime.datetime.fromisoformat(
                created_str.replace("Z", "+00:00")
            )
        except Exception:
            created_at = datetime.datetime.now()

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
                "cycle_id": row.get("cycle_id", ""),
                "created_at": created_at,
                "row_count": row.get("row_count", 0),
                "file_ctas": meta.get("file_ctas") or "—",
                "file_cobranza": meta.get("file_cobranza") or "—",
                "fecha_corte": meta.get("fecha_corte") or "—",
            })
        return sessions
    except Exception as e:
        print(f"list_sessions_cloud Error: {e}")
        return []


def load_session_by_id(cycle_id: str) -> Tuple[Optional["pd.DataFrame"], Optional[Dict], Optional[datetime.datetime]]:
    """Carga un ciclo especifico por su cycle_id."""
    client = _get_supabase()
    if not client:
        return None, None, None
    try:
        from utils.db_manager import _safe_execute
        res = _safe_execute(
            client.table("ciclos_procesamiento")
            .select("cycle_id, df_final_json, metadata, row_count, created_at")
            .eq("cycle_id", str(cycle_id).strip())
            .limit(1)
        )
        rows = res.data or []
        if not rows:
            return None, None, None

        row = rows[0]
        records = row.get("df_final_json", [])
        if not records:
            return None, None, None

        df = pd.DataFrame(records)
        metadata = row.get("metadata", {})
        created_str = row.get("created_at", "")
        try:
            created_at = datetime.datetime.fromisoformat(
                created_str.replace("Z", "+00:00")
            )
        except Exception:
            created_at = datetime.datetime.now()

        return df, metadata, created_at
    except Exception as e:
        print(f"load_session_by_id Error: {e}")
        return None, None, None


def clear_session_cloud() -> bool:
    """
    Elimina TODOS los ciclos de Supabase.
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
