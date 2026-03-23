import os
import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


DB_NAME = "email_ledger.db"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

_client = None
_last_error: Optional[str] = None


def _set_last_error(message: Optional[str]) -> None:
    global _last_error
    _last_error = message


def get_last_error() -> Optional[str]:
    return _last_error


def get_supabase_client():
    """Initialize Supabase client lazily."""
    global _client
    if _client is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client

            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
            _set_last_error(None)
        except Exception as e:
            _set_last_error(f"Supabase Init Error: {e}")
            print(f"Supabase Init Error: {e}")
    return _client


def is_cloud_mode() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def initialize_db() -> bool:
    """
    Cloud mode: require Supabase connectivity.
    Local/testing mode: ensure SQLite tables exist.
    """
    if is_cloud_mode():
        client = get_supabase_client()
        if client is None:
            if not get_last_error():
                _set_last_error("No se pudo inicializar cliente Supabase.")
            return False
        _set_last_error(None)
        return True

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_last_send (
                ledger_key TEXT PRIMARY KEY,
                last_sent_at TIMESTAMP,
                last_msg_id TEXT,
                send_count INTEGER
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS send_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ledger_key TEXT,
                recipient TEXT,
                status TEXT,
                reason TEXT,
                timestamp TIMESTAMP,
                run_id TEXT
            )
            """
        )
        conn.commit()
        conn.close()
        _set_last_error(None)
        return True
    except Exception as e:
        _set_last_error(f"DB Init Error: {e}")
        print(f"DB Init Error: {e}")
        return False


def _safe_execute(table_op):
    try:
        result = table_op.execute()
        _set_last_error(None)
        return result
    except Exception as e:
        _set_last_error(str(e))
        raise


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_attempt(recipient, status, run_id, ledger_key, reason=""):
    """Log send attempt to active engine."""
    ts = _now_str()

    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                _safe_execute(
                    client.table("send_attempts").insert(
                        {
                            "recipient": recipient,
                            "status": status,
                            "run_id": run_id,
                            "ledger_key": ledger_key,
                            "reason": reason,
                            "timestamp": ts,
                        }
                    )
                )
                _safe_execute(
                    client.table("ledger_last_send").upsert(
                        {
                            "ledger_key": ledger_key,
                            "last_sent_at": ts,
                            "send_count": 1,
                        }
                    )
                )
                return True
            except Exception as e:
                print(f"Supabase Logging Error: {e}")
                return False

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO send_attempts (id, ledger_key, recipient, status, reason, timestamp, run_id) VALUES (NULL, ?, ?, ?, ?, ?, ?)",
            (ledger_key, recipient, status, reason, ts, run_id),
        )
        c.execute(
            "INSERT OR REPLACE INTO ledger_last_send (ledger_key, last_sent_at, send_count) VALUES (?, ?, COALESCE((SELECT send_count FROM ledger_last_send WHERE ledger_key = ?), 0) + 1)",
            (ledger_key, ts, ledger_key),
        )
        conn.commit()
        conn.close()
        _set_last_error(None)
        return True
    except Exception as e:
        _set_last_error(str(e))
        print(f"SQLite Logging Error: {e}")
        return False


def get_status_map(email_list, target_date_str=None, min_timestamp=None):
    """Get status map for recipient list."""
    if not email_list:
        return {}

    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                query = client.table("send_attempts").select("recipient, status, timestamp").in_(
                    "recipient", email_list
                )

                if min_timestamp:
                    query = query.gte("timestamp", str(min_timestamp))
                else:
                    if not target_date_str:
                        target_date_str = datetime.now().strftime("%Y-%m-%d")
                    day_start = datetime.strptime(str(target_date_str), "%Y-%m-%d")
                    day_end = day_start.replace(hour=23, minute=59, second=59)
                    query = query.gte("timestamp", day_start.strftime("%Y-%m-%d %H:%M:%S"))
                    query = query.lte("timestamp", day_end.strftime("%Y-%m-%d %H:%M:%S"))

                res = _safe_execute(query.order("timestamp", desc=False))
                cloud_rows = res.data or []
                if cloud_rows or DB_NAME == "email_ledger.db":
                    return _process_rows_into_map(cloud_rows)
                # In tests with custom DB file, fallback to local if cloud is empty.
            except Exception as e:
                print(f"Supabase Query Error: {e}")
                if DB_NAME == "email_ledger.db":
                    return {}

    try:
        conn = sqlite3.connect(DB_NAME)
        params = list(email_list)
        date_filter = ""
        if min_timestamp:
            date_filter = "AND timestamp >= ?"
            params.append(str(min_timestamp))
        else:
            if not target_date_str:
                target_date_str = datetime.now().strftime("%Y-%m-%d")
            date_filter = "AND timestamp LIKE ?"
            params.append(f"{target_date_str}%")

        query = f"""
            SELECT recipient, status, timestamp
            FROM send_attempts
            WHERE recipient IN ({",".join(["?"] * len(email_list))})
            {date_filter}
            ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        _set_last_error(None)
        return _process_rows_into_map(df.to_dict("records"))
    except Exception as e:
        _set_last_error(str(e))
        print(f"SQLite Query Error: {e}")
        return {}


def _process_rows_into_map(rows):
    status_map = {}
    priority_map = {"SENT": 3, "BLOCKED": 2, "FAILED": 1, "PENDING": 0}

    for row in rows:
        email = row["recipient"]
        status = row["status"]
        ts = row["timestamp"]

        try:
            time_str = datetime.strptime(
                str(ts).split(".")[0].replace("T", " "), "%Y-%m-%d %H:%M:%S"
            ).strftime("%H:%M")
        except Exception:
            time_str = str(ts)[11:16]

        current = status_map.get(email, {"status": "PENDING"})
        curr_prio = priority_map.get(current.get("status", "PENDING"), 0)
        new_prio = priority_map.get(status, 0)

        if new_prio >= curr_prio:
            status_map[email] = {"status": status, "time": time_str, "ts_raw": ts}
    return status_map


def get_today_stats():
    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                today_start = datetime.now().strftime("%Y-%m-%d 00:00:00")
                res = _safe_execute(
                    client.table("send_attempts").select("status").gte("timestamp", today_start)
                )
                df = pd.DataFrame(res.data or [])
                if df.empty:
                    return {"SENT": 0, "FAILED": 0, "BLOCKED": 0}
                counts = df["status"].value_counts().to_dict()
                return {s: counts.get(s, 0) for s in ["SENT", "FAILED", "BLOCKED"]}
            except Exception:
                return {"SENT": 0, "FAILED": 0, "BLOCKED": 0}

    try:
        conn = sqlite3.connect(DB_NAME)
        today_start = datetime.now().strftime("%Y-%m-%d 00:00:00")
        df = pd.read_sql_query(
            "SELECT status, COUNT(*) as count FROM send_attempts WHERE timestamp >= ? GROUP BY status",
            conn,
            params=(today_start,),
        )
        conn.close()
        _set_last_error(None)
        stats = {s: df[df["status"] == s]["count"].sum() for s in ["SENT", "FAILED", "BLOCKED"]}
        return stats
    except Exception:
        return {"SENT": 0, "FAILED": 0, "BLOCKED": 0}


def get_last_sent_info(ledger_key):
    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                res = _safe_execute(
                    client.table("ledger_last_send").select("*").eq("ledger_key", ledger_key)
                )
                return res.data[0] if res.data else None
            except Exception:
                return None

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM ledger_last_send WHERE ledger_key = ?", (ledger_key,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "ledger_key": row[0],
                "last_sent_at": row[1],
                "last_msg_id": row[2],
                "send_count": row[3],
            }
    except Exception:
        return None
    return None


def reset_today_stats():
    now = datetime.now()
    today_pattern = f"{now.strftime('%Y-%m-%d')}%"
    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                _safe_execute(
                    client.table("ledger_last_send")
                    .delete()
                    .gte("last_sent_at", day_start.strftime("%Y-%m-%d %H:%M:%S"))
                    .lte("last_sent_at", day_end.strftime("%Y-%m-%d %H:%M:%S"))
                )
                return True, "Rate-limit reiniciado en Cloud. Historial preservado."
            except Exception as e:
                return False, str(e)

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM ledger_last_send WHERE last_sent_at LIKE ?", (today_pattern,))
        conn.commit()
        conn.close()
        _set_last_error(None)
        return True, "Rate-limit reiniciado en Local. Historial preservado."
    except Exception as e:
        _set_last_error(str(e))
        return False, str(e)


def clear_all_ledger():
    success, _msg = reset_today_stats()
    return success


def _normalize_status_code(status_code: Optional[str]) -> str:
    return str(status_code or "").strip().upper()


def _map_status_to_notification(status_code: str) -> Tuple[str, str, Optional[str], str]:
    # tipo_notificacion = CANAL (EMAIL / WHATSAPP) — no el tipo de alerta.
    # La prioridad/urgencia queda en los campos `estado` y `prioridad`.
    if status_code == "SENT":
        return "EMAIL", "ENVIADO", _now_str(), "NORMAL"
    if status_code == "BLOCKED":
        return "EMAIL", "PENDIENTE", None, "NORMAL"
    if status_code in {"FAILED", "ERROR", "BOUNCE", "BOUNCED"}:
        return "EMAIL", "PENDIENTE", None, "ALTA"
    return "EMAIL", "PENDIENTE", None, "NORMAL"


def persist_notification_event(
    *,
    cliente_id: Optional[str],
    destinatario: str,
    asunto: str,
    mensaje: str,
    status_code: Optional[str],
    run_id: Optional[str] = None,
    notification_key: Optional[str] = None,
    match_keys: Optional[Iterable[str]] = None,
    documento_id: Optional[str] = None,
    metadata_extra: Optional[Dict[str, Any]] = None,
    cycle_id: Optional[str] = None,
) -> bool:
    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para persistir notificaciones.")
        return False

    code = _normalize_status_code(status_code)
    tipo_notif, estado, fecha_envio, prioridad = _map_status_to_notification(code)

    metadata: Dict[str, Any] = {"channel": "EMAIL", "status_code": code}
    if run_id:
        metadata["run_id"] = run_id
    if notification_key:
        metadata["notification_key"] = notification_key
    if match_keys is not None:
        metadata["match_keys"] = list(match_keys)
    if metadata_extra:
        metadata.update(metadata_extra)

    payload = {
        "tipo_notificacion": tipo_notif,
        "prioridad": prioridad,
        "destinatario": str(destinatario or "").strip().lower(),
        "asunto": str(asunto or "").strip(),
        "mensaje": str(mensaje or "").strip(),
        "estado": estado,
        "fecha_envio": fecha_envio,
        "cliente_id": str(cliente_id).strip() if cliente_id else None,
        "documento_id": str(documento_id).strip() if documento_id else None,
        "metadata": metadata,
        "cycle_id": str(cycle_id).strip() if cycle_id else None,
    }

    try:
        _safe_execute(client.table("notificaciones").insert(payload))
        return True
    except Exception as e:
        print(f"persist_notification_event Error: {e}")
        return False


def get_notifications_by_cycle(cycle_id: str) -> List[Dict[str, Any]]:
    """Devuelve todas las notificaciones de un ciclo para reconciliar tracking."""
    if not cycle_id:
        return []
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = _safe_execute(
            client.table("notificaciones")
            .select("cliente_id, estado, fecha_envio, created_at, metadata")
            .eq("cycle_id", str(cycle_id).strip())
            .order("created_at", desc=False)
        )
        return res.data or []
    except Exception as e:
        print(f"get_notifications_by_cycle Error: {e}")
        return []


def get_wa_gestiones_by_cycle(cycle_id: str) -> List[Dict[str, Any]]:
    """Devuelve gestiones WHATSAPP de un ciclo para reconciliar tracking WA."""
    if not cycle_id:
        return []
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = _safe_execute(
            client.table("gestiones")
            .select("cliente_id, resultado, notas, fecha, created_at, metadata, tipo_registro")
            .eq("tipo_gestion", "WHATSAPP")
            .eq("cycle_id", str(cycle_id).strip())
            .order("created_at", desc=False)
        )
        return res.data or []
    except Exception as e:
        print(f"get_wa_gestiones_by_cycle Error: {e}")
        return []


def reconcile_tracking_from_notifications(
    df: "pd.DataFrame",
    cycle_id: str,
) -> "pd.DataFrame":
    """
    Reconstruye ESTADO_EMAIL / FECHA_ULTIMO_ENVIO desde notificaciones (email)
    y ESTADO_WHATSAPP / FECHA_ULTIMO_WA desde gestiones (whatsapp).
    """
    df = df.copy()

    # --- EMAIL: desde tabla notificaciones (por cycle_id) ---
    notifs = get_notifications_by_cycle(cycle_id)
    for notif in notifs:
        estado = str(notif.get("estado", "")).strip().upper()
        if estado != "ENVIADO":
            continue

        cliente_id = str(notif.get("cliente_id") or "").strip()
        fecha = str(notif.get("fecha_envio") or notif.get("created_at", ""))[:19]
        meta = notif.get("metadata") or {}
        channel = str(meta.get("channel", "EMAIL")).strip().upper()
        match_keys = meta.get("match_keys") or []

        if channel == "EMAIL":
            if match_keys:
                mask = df["MATCH_KEY"].astype(str).isin([str(mk) for mk in match_keys])
            else:
                mask = df["COD CLIENTE"].astype(str).str.strip() == cliente_id
            if mask.any():
                if "ESTADO_EMAIL" in df.columns:
                    df.loc[mask, "ESTADO_EMAIL"] = "ENVIADO"
                if "FECHA_ULTIMO_ENVIO" in df.columns:
                    df.loc[mask, "FECHA_ULTIMO_ENVIO"] = fecha
                if "ESTADO_ENVIO_TEXTO" in df.columns:
                    hora = fecha[11:16] if len(fecha) >= 16 else ""
                    df.loc[mask, "ESTADO_ENVIO_TEXTO"] = f"ENVIADO ({hora})" if hora else "ENVIADO"

    # --- WHATSAPP: desde tabla gestiones (metadata.cycle_id) ---
    wa_gestiones = get_wa_gestiones_by_cycle(cycle_id)
    for gestion in wa_gestiones:
        resultado = str(gestion.get("resultado", "")).strip().upper()
        if resultado != "EXITOSO":
            continue

        cliente_id = str(gestion.get("cliente_id") or "").strip()
        fecha = str(gestion.get("fecha") or gestion.get("created_at", ""))[:19]
        mask = df["COD CLIENTE"].astype(str).str.strip() == cliente_id
        if mask.any():
            if "ESTADO_WHATSAPP" in df.columns:
                df.loc[mask, "ESTADO_WHATSAPP"] = "ENVIADO"
            if "FECHA_ULTIMO_WA" in df.columns:
                df.loc[mask, "FECHA_ULTIMO_WA"] = fecha

    return df


def update_estados_email_in_cycle(cycle_id: str, match_keys: list, fecha: str) -> bool:
    """UPDATE documentos_ciclo.estado_email = ENVIADO para los match_keys del ciclo."""
    if not cycle_id or not match_keys:
        return False
    client = get_supabase_client()
    if not client:
        return False
    try:
        _safe_execute(
            client.table("documentos_ciclo")
            .update({"estado_email": "ENVIADO", "fecha_ultimo_envio": fecha})
            .eq("cycle_id", str(cycle_id))
            .in_("match_key", [str(mk) for mk in match_keys])
        )
        return True
    except Exception as e:
        print(f"update_estados_email_in_cycle Error: {e}")
        return False


def update_estado_whatsapp_in_cycle(cycle_id: str, cliente_ids: list, fecha: str) -> bool:
    """UPDATE documentos_ciclo.estado_whatsapp = ENVIADO para los cliente_ids del ciclo."""
    if not cycle_id or not cliente_ids:
        return False
    client = get_supabase_client()
    if not client:
        return False
    try:
        _safe_execute(
            client.table("documentos_ciclo")
            .update({"estado_whatsapp": "ENVIADO", "fecha_ultimo_wa": fecha})
            .eq("cycle_id", str(cycle_id))
            .in_("cliente_id", [str(c) for c in cliente_ids])
        )
        return True
    except Exception as e:
        print(f"update_estado_whatsapp_in_cycle Error: {e}")
        return False


def get_documento_id_by_numero(cliente_id: str, numero_documento: str) -> Optional[str]:
    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para consultar documentos.")
        return None
    try:
        res = _safe_execute(
            client.table("documentos")
            .select("documento_id")
            .eq("cliente_id", str(cliente_id))
            .eq("numero_documento", str(numero_documento))
            .limit(1)
        )
        rows = res.data or []
        if not rows:
            return None
        return rows[0].get("documento_id")
    except Exception as e:
        print(f"get_documento_id_by_numero Error: {e}")
        return None


def get_notifications_history(cliente_ids: List[str], limit: int = 200) -> List[Dict[str, Any]]:
    if not cliente_ids:
        return []
    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para consultar historial.")
        return []
    try:
        res = _safe_execute(
            client.table("notificaciones")
            .select(
                "cliente_id, destinatario, tipo_notificacion, prioridad, estado, fecha_envio, asunto, created_at, metadata"
            )
            .in_("cliente_id", cliente_ids)
            .order("created_at", desc=True)
            .limit(limit)
        )
        return res.data or []
    except Exception as e:
        print(f"get_notifications_history Error: {e}")
        return []


def _extract_row_date(row: Dict[str, Any]) -> Optional[str]:
    raw = row.get("fecha_envio") or row.get("created_at")
    if raw is None:
        return None
    return str(raw)[:10]


def get_notifications_report(
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    estado: Optional[str] = None,
    canal: Optional[str] = None,
    limit: int = 3000,
) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para reporte de notificaciones.")
        return []

    try:
        res = _safe_execute(
            client.table("notificaciones")
            .select(
                "cliente_id, destinatario, estado, fecha_envio, created_at, tipo_notificacion, metadata, asunto, prioridad"
            )
            .order("created_at", desc=True)
            .limit(limit)
        )
        rows = list(res.data or [])
    except Exception as e:
        print(f"get_notifications_report Error: {e}")
        return []

    estado_norm = str(estado or "").strip().upper()
    canal_norm = str(canal or "").strip().upper()

    filtered: List[Dict[str, Any]] = []
    for row in rows:
        row_date = _extract_row_date(row)
        if date_from and row_date and row_date < str(date_from):
            continue
        if date_to and row_date and row_date > str(date_to):
            continue

        if estado_norm and str(row.get("estado", "")).strip().upper() != estado_norm:
            continue

        metadata = row.get("metadata") or {}
        channel_value = str(metadata.get("channel", "")).strip().upper()
        if canal_norm and channel_value != canal_norm:
            continue

        filtered.append(row)

    return filtered[:limit]


CLIENTE_ESTADOS_VALIDOS = {"ACTIVO", "INACTIVO", "MOROSO"}
CLIENTE_ENVIAR_EMAIL_VALIDOS = {"SI", "NO", "SIN CONFIGURAR"}
LEGACY_EXTRA_PREFIX = "[EXTRA_FIELDS]"
CLIENTES_SELECT_FIELDS = (
    "cliente_id, nombre, email, telefono, dni, ruc, direccion, "
    "estado, enviar_email, notas, extra_fields, updated_at"
)


def _clean_optional_text(value: Any, *, lower: bool = False) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat"}:
        return None
    return text.lower() if lower else text


def _normalize_cliente_id(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(float(text))).zfill(6)
    except Exception:
        if text.isdigit():
            return text.zfill(6)
        return text


def _normalize_cliente_estado(value: Any) -> str:
    estado = str(value or "").strip().upper()
    if estado in {"A", "AC"}:
        return "ACTIVO"
    if estado in {"I", "IN"}:
        return "INACTIVO"
    if estado in {"M", "MO"}:
        return "MOROSO"
    if estado in CLIENTE_ESTADOS_VALIDOS:
        return estado
    return "ACTIVO"


def _normalize_cliente_enviar_email(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if raw in {"SI", "SÍ", "YES", "Y", "1", "TRUE", "ENVIAR"}:
        return "SI"
    if raw in {"NO", "N", "0", "FALSE", "NO ENVIAR"}:
        return "NO"
    if raw in {"", "NAN", "NONE", "NAT", "NULL", "SIN CONFIGURAR", "SINCONFIGURAR"}:
        return "SIN CONFIGURAR"
    return raw if raw in CLIENTE_ENVIAR_EMAIL_VALIDOS else "SIN CONFIGURAR"


def _extract_legacy_extra_from_notas(value: Any) -> Tuple[Optional[str], Dict[str, Any]]:
    text = str(value or "").strip()
    if not text or LEGACY_EXTRA_PREFIX not in text:
        return _clean_optional_text(text), {}

    idx = text.rfind(LEGACY_EXTRA_PREFIX)
    base_note = text[:idx].strip()
    payload = text[idx + len(LEGACY_EXTRA_PREFIX) :].strip()

    extras: Dict[str, Any] = {}
    if payload:
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                extras = {str(k): v for k, v in parsed.items()}
        except Exception:
            extras = {}

    return _clean_optional_text(base_note), extras


def _merge_legacy_extra_into_notas(row: Dict[str, Any], extra_payload: Dict[str, Any]) -> None:
    if not isinstance(extra_payload, dict) or not extra_payload:
        return

    note_clean, note_extra = _extract_legacy_extra_from_notas(row.get("notas"))
    merged = dict(note_extra)
    for k, v in extra_payload.items():
        key = str(k).strip()
        value = _clean_optional_text(v)
        if key and value is not None:
            merged[key] = value

    if not merged:
        if note_clean is not None:
            row["notas"] = note_clean
        return

    packed = f"{LEGACY_EXTRA_PREFIX}{json.dumps(merged, ensure_ascii=False)}"
    row["notas"] = f"{note_clean}\n{packed}".strip() if note_clean else packed


def _normalize_cliente_record(row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    cliente_id = _normalize_cliente_id(row.get("cliente_id"))
    if not cliente_id:
        return None, "cliente_id es obligatorio"

    nombre = _clean_optional_text(row.get("nombre")) or f"Cliente {cliente_id}"
    extra_fields = row.get("extra_fields")
    if isinstance(extra_fields, dict):
        clean_extra = {
            str(k): str(v).strip()
            for k, v in extra_fields.items()
            if str(k).strip() and str(v).strip()
        }
    else:
        clean_extra = {}
    payload = {
        "cliente_id": cliente_id,
        "nombre": nombre,
        "email": _clean_optional_text(row.get("email"), lower=True),
        "telefono": _clean_optional_text(row.get("telefono")),
        "dni": _clean_optional_text(row.get("dni")),
        "ruc": _clean_optional_text(row.get("ruc")),
        "direccion": _clean_optional_text(row.get("direccion")),
        "enviar_email": _normalize_cliente_enviar_email(row.get("enviar_email")),
        "estado": _normalize_cliente_estado(row.get("estado")),
        "notas": _clean_optional_text(row.get("notas")),
        "extra_fields": clean_extra,
        "updated_at": _now_str(),
    }
    return payload, None


def _chunk_list(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _filter_client_rows(rows: List[Dict[str, Any]], *, search: str = "", estado: str = "") -> List[Dict[str, Any]]:
    search_norm = str(search or "").strip().lower()
    estado_norm = str(estado or "").strip().upper()

    filtered: List[Dict[str, Any]] = []
    for row in rows:
        if estado_norm and estado_norm != "TODOS":
            if str(row.get("estado", "")).strip().upper() != estado_norm:
                continue

        if search_norm:
            extra_blob = row.get("extra_fields")
            if isinstance(extra_blob, dict):
                extra_text = " ".join(
                    [f"{k} {v}" for k, v in extra_blob.items() if str(v).strip()]
                )
            else:
                extra_text = str(extra_blob or "")
            haystack = " ".join(
                [
                    str(row.get("cliente_id", "")),
                    str(row.get("nombre", "")),
                    str(row.get("email", "")),
                    str(row.get("telefono", "")),
                    str(row.get("dni", "")),
                    str(row.get("ruc", "")),
                    str(row.get("direccion", "")),
                    str(row.get("enviar_email", "")),
                    str(row.get("notas", "")),
                    extra_text,
                ]
            ).lower()
            if search_norm not in haystack:
                continue
        filtered.append(row)
    return filtered


def list_clientes_for_admin(search: str = "", limit: int = 200) -> List[Dict[str, Any]]:
    # Backward-compatible alias for existing UI/tests.
    return list_clientes_full(search=search, estado="", limit=limit)


def list_clientes_full(search: str = "", estado: str = "", limit: int = 1000) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para listar clientes.")
        return []

    try:
        try:
            res = _safe_execute(
                client.table("clientes")
                .select(CLIENTES_SELECT_FIELDS)
                .order("nombre")
                .limit(limit)
            )
        except Exception:
            # Compatibilidad con esquemas legacy que aun no tengan campos nuevos.
            legacy_fields = "cliente_id, nombre, email, telefono, ruc, direccion, estado, notas, updated_at"
            res = _safe_execute(
                client.table("clientes")
                .select(legacy_fields)
                .order("nombre")
                .limit(limit)
            )
        rows = list(res.data or [])
        for row in rows:
            raw_note = row.get("notas")
            note_clean, note_extra = _extract_legacy_extra_from_notas(raw_note)
            if isinstance(raw_note, str) and LEGACY_EXTRA_PREFIX in raw_note:
                row["notas"] = note_clean or ""
            elif note_clean is not None:
                row["notas"] = note_clean
            row.setdefault("dni", None)
            row.setdefault("enviar_email", None)
            row.setdefault("extra_fields", {})
            if not isinstance(row.get("extra_fields"), dict):
                row["extra_fields"] = {}
            if note_extra:
                row["extra_fields"].update(note_extra)
            if not row.get("dni"):
                row["dni"] = _clean_optional_text(row["extra_fields"].get("dni"))
            enviar_source = _clean_optional_text(row.get("enviar_email"))
            if not enviar_source:
                enviar_source = row["extra_fields"].get("enviar_email")
            row["enviar_email"] = _normalize_cliente_enviar_email(enviar_source)
        return _filter_client_rows(rows, search=search, estado=estado)
    except Exception as e:
        print(f"list_clientes_full Error: {e}")
        return []


def get_clientes_master(limit: int = 50000) -> List[Dict[str, Any]]:
    """
    Retorna cartera maestra de clientes desde Supabase para ciclos sin Excel de clientes.
    """
    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para obtener cartera maestra.")
        return []
    try:
        try:
            res = _safe_execute(
                client.table("clientes")
                .select(
                    "cliente_id, nombre, email, telefono, dni, ruc, direccion, estado, enviar_email, notas, extra_fields"
                )
                .order("cliente_id")
                .limit(limit)
            )
        except Exception:
            res = _safe_execute(
                client.table("clientes")
                .select("cliente_id, nombre, email, telefono, ruc, direccion, estado, notas")
                .order("cliente_id")
                .limit(limit)
            )
        rows = list(res.data or [])
        for row in rows:
            raw_note = row.get("notas")
            note_clean, note_extra = _extract_legacy_extra_from_notas(raw_note)
            if isinstance(raw_note, str) and LEGACY_EXTRA_PREFIX in raw_note:
                row["notas"] = note_clean or ""
            elif note_clean is not None:
                row["notas"] = note_clean
            row.setdefault("dni", None)
            row.setdefault("enviar_email", None)
            row.setdefault("extra_fields", {})
            if not isinstance(row.get("extra_fields"), dict):
                row["extra_fields"] = {}
            if note_extra:
                row["extra_fields"].update(note_extra)
            if not row.get("dni"):
                row["dni"] = _clean_optional_text(row["extra_fields"].get("dni"))
            enviar_source = _clean_optional_text(row.get("enviar_email"))
            if not enviar_source:
                enviar_source = row["extra_fields"].get("enviar_email")
            row["enviar_email"] = _normalize_cliente_enviar_email(enviar_source)
        return rows
    except Exception as e:
        print(f"get_clientes_master Error: {e}")
        return []


def update_cliente_fields(
    *,
    cliente_id: str,
    nombre: Optional[str] = None,
    email: Optional[str] = None,
    telefono: Optional[str] = None,
    dni: Optional[str] = None,
    ruc: Optional[str] = None,
    direccion: Optional[str] = None,
    enviar_email: Optional[str] = None,
    estado: Optional[str] = None,
    notas: Optional[str] = None,
) -> Tuple[bool, str]:
    cliente_id_norm = _normalize_cliente_id(cliente_id)
    if not cliente_id_norm:
        return False, "cliente_id es obligatorio"

    payload: Dict[str, Any] = {}
    if nombre is not None:
        payload["nombre"] = (_clean_optional_text(nombre) or f"Cliente {cliente_id_norm}")
    if email is not None:
        payload["email"] = _clean_optional_text(email, lower=True)
    if telefono is not None:
        payload["telefono"] = _clean_optional_text(telefono)
    if dni is not None:
        payload["dni"] = _clean_optional_text(dni)
    if ruc is not None:
        payload["ruc"] = _clean_optional_text(ruc)
    if direccion is not None:
        payload["direccion"] = _clean_optional_text(direccion)
    if enviar_email is not None:
        payload["enviar_email"] = _normalize_cliente_enviar_email(enviar_email)
    if estado is not None:
        estado_raw = str(estado or "").strip().upper()
        alias = {
            "A": "ACTIVO",
            "AC": "ACTIVO",
            "I": "INACTIVO",
            "IN": "INACTIVO",
            "M": "MOROSO",
            "MO": "MOROSO",
        }
        estado_norm = alias.get(estado_raw, estado_raw)
        if estado_norm not in CLIENTE_ESTADOS_VALIDOS:
            return False, "estado invalido: use ACTIVO, INACTIVO o MOROSO"
        payload["estado"] = estado_norm
    if notas is not None:
        payload["notas"] = _clean_optional_text(notas)

    if not payload:
        return False, "sin cambios para actualizar"

    payload["updated_at"] = _now_str()

    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para actualizar cliente.")
        return False, _last_error or "Supabase no disponible"

    try:
        _safe_execute(client.table("clientes").update(payload).eq("cliente_id", cliente_id_norm))
        return True, "Cliente actualizado correctamente."
    except Exception as e:
        print(f"update_cliente_fields Error: {e}")
        return False, f"No se pudo actualizar cliente: {e}"


def upsert_clientes_rows(rows: List[Dict[str, Any]], batch_size: int = 200) -> Tuple[bool, str]:
    if not rows:
        return False, "No hay registros para guardar."

    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para guardar clientes.")
        return False, _last_error or "Supabase no disponible"

    normalized_rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    for idx, row in enumerate(rows, start=1):
        payload, err = _normalize_cliente_record(row)
        if err:
            errors.append(f"fila {idx}: {err}")
            continue
        normalized_rows.append(payload)  # type: ignore[arg-type]

    if not normalized_rows:
        msg = "Ningun registro valido para guardar."
        if errors:
            msg += f" Errores: {errors[:3]}"
        return False, msg

    safe_batch_size = max(int(batch_size or 200), 1)
    try:
        for batch in _chunk_list(normalized_rows, safe_batch_size):
            fallback_batch = [dict(row) for row in batch]
            while True:
                try:
                    _safe_execute(client.table("clientes").upsert(fallback_batch, on_conflict="cliente_id"))
                    break
                except Exception as e_upsert:
                    # Compatibilidad con esquemas legacy sin columnas nuevas.
                    msg = str(e_upsert).lower()
                    changed = False

                    def _drop_optional(field: str) -> bool:
                        removed_any = False
                        for row in fallback_batch:
                            if field not in row:
                                continue
                            value = row.get(field)
                            if value not in (None, "", {}):
                                if "extra_fields" in row:
                                    if not isinstance(row.get("extra_fields"), dict):
                                        row["extra_fields"] = {}
                                    row["extra_fields"][field] = value
                                else:
                                    _merge_legacy_extra_into_notas(row, {field: value})
                            row.pop(field, None)
                            removed_any = True
                        return removed_any

                    if "dni" in msg:
                        changed = _drop_optional("dni") or changed
                    if "enviar_email" in msg:
                        changed = _drop_optional("enviar_email") or changed
                    if "extra_fields" in msg:
                        removed_extra = False
                        for row in fallback_batch:
                            if "extra_fields" not in row:
                                continue
                            extra_payload = row.pop("extra_fields", None)
                            if isinstance(extra_payload, dict) and extra_payload:
                                _merge_legacy_extra_into_notas(row, extra_payload)
                            removed_extra = True
                        changed = removed_extra or changed

                    if not changed:
                        raise
        message = f"Clientes guardados: {len(normalized_rows)}"
        if errors:
            message += f" | filas ignoradas: {len(errors)}"
        return True, message
    except Exception as e:
        print(f"upsert_clientes_rows Error: {e}")
        return False, f"No se pudo guardar clientes: {e}"


def delete_clientes_by_ids(cliente_ids: Iterable[str]) -> Tuple[bool, str]:
    ids_norm = sorted({_normalize_cliente_id(cid) for cid in (cliente_ids or []) if _normalize_cliente_id(cid)})
    if not ids_norm:
        return False, "No hay cliente_id validos para eliminar."

    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para eliminar clientes.")
        return False, _last_error or "Supabase no disponible"

    try:
        _safe_execute(client.table("clientes").delete().in_("cliente_id", ids_norm))
        return True, f"Clientes eliminados: {len(ids_norm)}"
    except Exception as e:
        print(f"delete_clientes_by_ids Error: {e}")
        return False, f"No se pudo eliminar clientes: {e}"


def migrate_clientes_from_cartera_df(df_cartera: pd.DataFrame, batch_size: int = 200) -> Dict[str, Any]:
    if df_cartera is None or df_cartera.empty:
        return {
            "ok": False,
            "message": "La cartera esta vacia.",
            "counts": {"rows": 0, "errors": 0},
            "error_samples": [],
        }

    try:
        from scripts.migrate_excel_to_supabase import build_clientes

        df_ctas_seed = pd.DataFrame(columns=["codcli", "nomcli"])
        rows, errors = build_clientes(df_ctas_seed, df_cartera)
    except Exception as e:
        return {
            "ok": False,
            "message": f"No se pudo preparar migracion de cartera: {e}",
            "counts": {"rows": 0, "errors": 1},
            "error_samples": [str(e)],
        }

    ok, msg = upsert_clientes_rows(rows, batch_size=batch_size)
    return {
        "ok": ok,
        "message": msg,
        "counts": {"rows": len(rows), "errors": len(errors)},
        "error_samples": errors[:10],
    }


# ---------------------------------------------------------------------------
# CRM: Gestiones (interactions tracking)
# ---------------------------------------------------------------------------

GESTION_TIPOS_VALIDOS = {"EMAIL", "WHATSAPP", "LLAMADA", "VISITA", "NOTA", "OTRO"}

# Fallback estático — solo se usa si Supabase no está disponible o la tabla
# catalogo_resultados aún no existe. La fuente de verdad es la BD.
_RESULTADOS_FALLBACK = [
    {"codigo": "EXITOSO",        "etiqueta": "Acordó pagar",            "icono": "✅", "color_scheme": "success", "es_legado": False, "orden": 1},
    {"codigo": "PROMESA_PAGO",   "etiqueta": "Prometió pagar",          "icono": "🤝", "color_scheme": "info",    "es_legado": True,  "orden": 93},
    {"codigo": "SOLICITO_PLAZO", "etiqueta": "Solicitó más plazo", "icono": "⏳", "color_scheme": "warning", "es_legado": False, "orden": 3},
    {"codigo": "EN_NEGOCIACION", "etiqueta": "En negociación",     "icono": "💬", "color_scheme": "info",    "es_legado": False, "orden": 4},
    {"codigo": "SIN_RESPUESTA",  "etiqueta": "Sin respuesta",      "icono": "📵", "color_scheme": "neutral", "es_legado": False, "orden": 5},
    {"codigo": "ESCALAR_LEGAL",  "etiqueta": "Derivar a Legal",    "icono": "⚖️", "color_scheme": "danger",  "es_legado": False, "orden": 6},
    {"codigo": "DISPUTA",        "etiqueta": "Disputó la deuda",   "icono": "❓", "color_scheme": "warning", "es_legado": False, "orden": 7},
    {"codigo": "FALLIDO",        "etiqueta": "Falló",              "icono": "❌", "color_scheme": "danger",  "es_legado": True,  "orden": 90},
    {"codigo": "PENDIENTE",      "etiqueta": "Prometió pagar",     "icono": "🤝", "color_scheme": "warning", "es_legado": True,  "orden": 91},
    {"codigo": "REPROGRAMADO",   "etiqueta": "Derivar a Legal",    "icono": "⚖️", "color_scheme": "neutral", "es_legado": True,  "orden": 92},
]

# Caché en memoria: se invalida cada 5 minutos para reflejar cambios en BD sin reiniciar.
_catalogo_cache: Optional[List[Dict[str, Any]]] = None
_catalogo_cache_ts: float = 0.0
_CATALOGO_TTL_SECONDS = 300  # 5 minutos


def get_catalogo_resultados(*, include_legado: bool = True) -> List[Dict[str, Any]]:
    """Devuelve el catálogo de resultados desde Supabase con caché de 5 minutos.

    Cada elemento tiene: codigo, etiqueta, icono, color_scheme, es_legado, orden.
    Si la tabla no existe o Supabase no está disponible, usa el fallback estático.

    Args:
        include_legado: Si False, excluye valores legado (para nuevas gestiones).
    """
    import time
    global _catalogo_cache, _catalogo_cache_ts

    now = time.monotonic()
    if _catalogo_cache is None or (now - _catalogo_cache_ts) > _CATALOGO_TTL_SECONDS:
        client = get_supabase_client()
        if client:
            try:
                resp = _safe_execute(
                    client.table("catalogo_resultados")
                    .select("codigo,etiqueta,icono,color_scheme,es_legado,orden")
                    .eq("activo", True)
                    .order("orden")
                )
                if resp and isinstance(resp.data, list) and resp.data:
                    _catalogo_cache = resp.data
                    _catalogo_cache_ts = now
            except Exception:
                pass  # mantiene caché anterior o usa fallback

    rows = _catalogo_cache if _catalogo_cache else _RESULTADOS_FALLBACK
    if not include_legado:
        rows = [r for r in rows if not r.get("es_legado", False)]
    return rows


def get_resultado_label(codigo: str) -> str:
    """Convierte un código interno al label con ícono para mostrar en UI."""
    for r in get_catalogo_resultados(include_legado=True):
        if r["codigo"] == codigo:
            return f"{r['icono']} {r['etiqueta']}"
    return codigo


def _get_resultados_validos_set() -> set:
    """Set de códigos válidos para validación en insert_gestion."""
    return {r["codigo"] for r in get_catalogo_resultados(include_legado=True)}




def insert_gestion(
    *,
    cliente_id: str,
    tipo_gestion: str,
    resultado: str = "PENDIENTE",
    notas: Optional[str] = None,
    usuario: Optional[str] = None,
    duracion_minutos: Optional[int] = None,
    fecha: Optional[str] = None,
    cycle_id: Optional[str] = None,
    metadata_extra: Optional[Dict[str, Any]] = None,
    tipo_registro: str = "GESTION",
) -> Tuple[bool, str]:
    """Insert a gestion/interaction record.

    tipo_registro:
      'ENVIO'   — Registro automático del sistema (WA masivo enviado).
                  El Dashboard lo cuenta en "WA enviados", no en "Gestiones".
      'GESTION' — Acción manual del gestor (seguimiento, notas, resultado).
                  El Dashboard lo cuenta en "Gestiones totales" y KPIs de éxito.
    """
    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para registrar gestion.")
        return False, _last_error or "Supabase no disponible"

    tipo_norm = str(tipo_gestion or "").strip().upper()
    if tipo_norm not in GESTION_TIPOS_VALIDOS:
        return False, f"Tipo de gestion invalido: {tipo_gestion}"

    resultado_norm = str(resultado or "PENDIENTE").strip().upper()
    if resultado_norm not in _get_resultados_validos_set():
        resultado_norm = "PENDIENTE"

    tipo_reg_norm = "ENVIO" if str(tipo_registro or "").strip().upper() == "ENVIO" else "GESTION"

    payload: Dict[str, Any] = {
        "cliente_id": str(cliente_id).strip(),
        "tipo_gestion": tipo_norm,
        "canal": tipo_norm,
        "resultado": resultado_norm,
        "notas": str(notas or "").strip() or None,
        "usuario": str(usuario or "").strip() or None,
        "duracion_minutos": duracion_minutos if duracion_minutos and duracion_minutos > 0 else None,
        "metadata": metadata_extra or {},
        "cycle_id": str(cycle_id).strip() if cycle_id else None,
        "tipo_registro": tipo_reg_norm,
    }
    if fecha:
        payload["fecha"] = fecha

    try:
        _safe_execute(client.table("gestiones").insert(payload))
        return True, "Gestion registrada correctamente."
    except Exception as e:
        print(f"insert_gestion Error: {e}")
        return False, f"No se pudo registrar gestion: {e}"


def get_gestiones_list(
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tipo: Optional[str] = None,
    cliente_id: Optional[str] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """Fetch gestiones with optional filters."""
    client = get_supabase_client()
    if not client:
        _set_last_error("Supabase no disponible para consultar gestiones.")
        return []

    try:
        query = (
            client.table("gestiones")
            .select("id, cliente_id, tipo_gestion, canal, fecha, resultado, notas, usuario, duracion_minutos, metadata, created_at")
            .order("fecha", desc=True)
            .limit(limit)
        )
        if cliente_id:
            query = query.eq("cliente_id", str(cliente_id).strip())
        if tipo and tipo.upper() != "TODOS":
            query = query.eq("tipo_gestion", tipo.upper())

        res = _safe_execute(query)
        rows = list(res.data or [])

        # Client-side date filtering
        if date_from or date_to:
            filtered = []
            for row in rows:
                row_date = str(row.get("fecha", "") or row.get("created_at", ""))[:10]
                if date_from and row_date < str(date_from):
                    continue
                if date_to and row_date > str(date_to):
                    continue
                filtered.append(row)
            rows = filtered

        return rows
    except Exception as e:
        print(f"get_gestiones_list Error: {e}")
        return []


def get_gestiones_by_client(cliente_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch all gestiones for a specific client."""
    return get_gestiones_list(cliente_id=cliente_id, limit=limit)


def get_clientes_nombres_map() -> Dict[str, str]:
    """Retorna {cliente_id: nombre} desde la tabla maestra clientes. Ligero, sin JOINs."""
    client = get_supabase_client()
    if not client:
        return {}
    try:
        res = _safe_execute(
            client.table("clientes")
            .select("cliente_id, nombre")
            .order("cliente_id")
            .limit(50000)
        )
        return {
            str(r["cliente_id"]).strip(): str(r["nombre"]).strip()
            for r in (res.data or [])
            if r.get("cliente_id") and r.get("nombre")
        }
    except Exception:
        return {}


def get_gestiones_stats() -> Dict[str, Any]:
    """Aggregate stats for gestiones: counts by tipo and resultado."""
    client = get_supabase_client()
    if not client:
        return {}

    try:
        res = _safe_execute(
            client.table("gestiones")
            .select("tipo_gestion, resultado, fecha")
            .order("fecha", desc=True)
            .limit(5000)
        )
        rows = res.data or []

        by_tipo: Dict[str, int] = {}
        by_resultado: Dict[str, int] = {}
        today_str = _now_str()[:10]
        today_count = 0

        for row in rows:
            tipo = row.get("tipo_gestion", "OTRO")
            by_tipo[tipo] = by_tipo.get(tipo, 0) + 1
            resultado = row.get("resultado", "PENDIENTE")
            by_resultado[resultado] = by_resultado.get(resultado, 0) + 1
            if str(row.get("fecha", ""))[:10] == today_str:
                today_count += 1

        return {
            "total": len(rows),
            "today": today_count,
            "by_tipo": by_tipo,
            "by_resultado": by_resultado,
        }
    except Exception as e:
        print(f"get_gestiones_stats Error: {e}")
        return {}


def get_crm_dashboard_stats() -> Dict[str, Any]:
    """Combined stats from notificaciones + gestiones for CRM dashboard KPIs."""
    client = get_supabase_client()
    if not client:
        return {}

    stats: Dict[str, Any] = {
        "last_mass_notification": None,
        "total_notifications": 0,
        "notifications_today": 0,
        "notifications_week": 0,
        "notifications_last_active_date": None,
        "notifications_last_active_count": 0,
        "success_rate": 0.0,
        "total_gestiones": 0,
        "gestiones_today": 0,
    }

    try:
        # Latest notification
        res = _safe_execute(
            client.table("notificaciones")
            .select("fecha_envio, estado, created_at")
            .order("created_at", desc=True)
            .limit(3000)
        )
        notifs = res.data or []
        stats["total_notifications"] = len(notifs)

        if notifs:
            stats["last_mass_notification"] = notifs[0].get("fecha_envio") or notifs[0].get("created_at")

        today_str = _now_str()[:10]
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        sent_count = 0
        for n in notifs:
            n_date = str(n.get("fecha_envio", "") or n.get("created_at", ""))[:10]
            if n_date == today_str:
                stats["notifications_today"] += 1
            if n_date >= week_ago:
                stats["notifications_week"] += 1
            if str(n.get("estado", "")).upper() == "ENVIADO":
                sent_count += 1

        if notifs:
            stats["success_rate"] = round(sent_count / len(notifs) * 100, 1)
            # Último día con actividad (distinto de hoy puede ser ayer u otro día)
            last_active = str(notifs[0].get("fecha_envio") or notifs[0].get("created_at", ""))[:10]
            stats["notifications_last_active_date"] = last_active
            stats["notifications_last_active_count"] = sum(
                1 for n in notifs
                if str(n.get("fecha_envio", "") or n.get("created_at", ""))[:10] == last_active
            )

        # Gestiones stats
        gestiones_stats = get_gestiones_stats()
        stats["total_gestiones"] = gestiones_stats.get("total", 0)
        stats["gestiones_today"] = gestiones_stats.get("today", 0)
        stats["gestiones_by_tipo"] = gestiones_stats.get("by_tipo", {})

    except Exception as e:
        print(f"get_crm_dashboard_stats Error: {e}")

    return stats


# ---------------------------------------------------------------------------
# RC-FEAT-021: Acuerdos de Pago con Cuotas
# ---------------------------------------------------------------------------

ACUERDO_ESTADOS_VALIDOS = {"ACTIVO", "CUMPLIDO", "INCUMPLIDO", "CANCELADO"}
CUOTA_ESTADOS_VALIDOS = {"PENDIENTE", "PAGADO", "VENCIDO", "REPACTADO"}


def insert_acuerdo_pago(
    *,
    cliente_id: str,
    monto_total: float,
    numero_cuotas: int,
    fecha_acuerdo: str,
    cuotas: List[Dict[str, Any]],
    gestor: Optional[str] = None,
    ciclo_id: Optional[str] = None,
    notas: Optional[str] = None,
) -> Tuple[bool, str]:
    """Insert an acuerdo_pago with its cuotas.

    Args:
        cuotas: list of dicts with keys:
            numero_cuota (int), monto_cuota (float), fecha_vencimiento (str 'YYYY-MM-DD')
    """
    client = get_supabase_client()
    if not client:
        return False, "Supabase no disponible."

    if not cliente_id or monto_total <= 0 or numero_cuotas < 1:
        return False, "Parámetros inválidos: cliente_id, monto_total o numero_cuotas."
    if len(cuotas) != numero_cuotas:
        return False, f"Se esperaban {numero_cuotas} cuotas, se recibieron {len(cuotas)}."

    try:
        acuerdo_payload: Dict[str, Any] = {
            "cliente_id": str(cliente_id).strip(),
            "monto_total": float(monto_total),
            "numero_cuotas": int(numero_cuotas),
            "fecha_acuerdo": str(fecha_acuerdo),
            "gestor": str(gestor).strip() if gestor else None,
            "ciclo_id": str(ciclo_id).strip() if ciclo_id else None,
            "notas": str(notas).strip() if notas else None,
            "estado": "ACTIVO",
        }
        # insert() sin .select() para compatibilidad con supabase-py < 2.x
        _safe_execute(client.table("acuerdos_pago").insert(acuerdo_payload))
        # Recuperar el id recién insertado por cliente_id + fecha_acuerdo
        fetch_resp = _safe_execute(
            client.table("acuerdos_pago")
            .select("id")
            .eq("cliente_id", acuerdo_payload["cliente_id"])
            .eq("fecha_acuerdo", acuerdo_payload["fecha_acuerdo"])
            .order("created_at", desc=True)
            .limit(1)
        )
        acuerdo_id = fetch_resp.data[0]["id"] if fetch_resp and fetch_resp.data else None
        if not acuerdo_id:
            return False, "No se pudo obtener el ID del acuerdo creado."

        cuotas_payload = [
            {
                "acuerdo_id": acuerdo_id,
                "numero_cuota": int(c["numero_cuota"]),
                "monto_cuota": float(c["monto_cuota"]),
                "fecha_vencimiento": str(c["fecha_vencimiento"]),
                "estado": "PENDIENTE",
            }
            for c in cuotas
        ]
        _safe_execute(client.table("cuotas_acuerdo").insert(cuotas_payload))
        return True, acuerdo_id
    except Exception as e:
        print(f"insert_acuerdo_pago Error: {e}")
        return False, f"Error al crear acuerdo: {e}"


def get_acuerdos_by_cliente(cliente_id: str) -> List[Dict[str, Any]]:
    """Return acuerdos_pago for a client, each with a 'cuotas' list."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        acuerdos_resp = _safe_execute(
            client.table("acuerdos_pago")
            .select("*")
            .eq("cliente_id", str(cliente_id).strip())
            .order("fecha_acuerdo", desc=True)
        )
        acuerdos = acuerdos_resp.data if acuerdos_resp and acuerdos_resp.data else []

        for acuerdo in acuerdos:
            cuotas_resp = _safe_execute(
                client.table("cuotas_acuerdo")
                .select("*")
                .eq("acuerdo_id", acuerdo["id"])
                .order("numero_cuota")
            )
            acuerdo["cuotas"] = cuotas_resp.data if cuotas_resp and cuotas_resp.data else []
        return acuerdos
    except Exception as e:
        print(f"get_acuerdos_by_cliente Error: {e}")
        return []


def update_cuota_estado(
    cuota_id: str,
    nuevo_estado: str,
    *,
    fecha_pago: Optional[str] = None,
    notas: Optional[str] = None,
) -> Tuple[bool, str]:
    """Update the estado of a cuota_acuerdo row."""
    client = get_supabase_client()
    if not client:
        return False, "Supabase no disponible."

    estado_norm = str(nuevo_estado).strip().upper()
    if estado_norm not in CUOTA_ESTADOS_VALIDOS:
        return False, f"Estado inválido: {nuevo_estado}"

    try:
        payload: Dict[str, Any] = {
            "estado": estado_norm,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if fecha_pago:
            payload["fecha_pago"] = str(fecha_pago)
        if notas:
            payload["notas"] = str(notas).strip()

        _safe_execute(
            client.table("cuotas_acuerdo").update(payload).eq("id", str(cuota_id))
        )
        return True, "Cuota actualizada correctamente."
    except Exception as e:
        print(f"update_cuota_estado Error: {e}")
        return False, f"No se pudo actualizar cuota: {e}"


# ---------------------------------------------------------------------------
# RC-FEAT-023: Trazabilidad Completa — reconcile_ciclo_recovery
# ---------------------------------------------------------------------------

def _get_docs_simple_by_cycle(cycle_id: str) -> List[Dict[str, Any]]:
    """Fetch match_key, cliente_id, saldo from documentos_ciclo for a cycle."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        resp = _safe_execute(
            client.table("documentos_ciclo")
            .select("match_key,cliente_id,saldo_real,saldo_original")
            .eq("cycle_id", str(cycle_id))
            .limit(5000)
        )
        return resp.data if resp and resp.data else []
    except Exception as e:
        print(f"_get_docs_simple_by_cycle Error: {e}")
        return []


def reconcile_ciclo_recovery(
    cycle_id_anterior: str,
    cycle_id_nuevo: str,
) -> Dict[str, Any]:
    """Detect recovered documents between two cycles and persist summary tables.

    A document is considered "recovered" (client paid) when its match_key
    was present in cycle_id_anterior but is absent in cycle_id_nuevo.

    Persists:
       - resumen_cliente_ciclo: one row per client in cycle_id_nuevo
       - resumen_ciclo:         one aggregate row for cycle_id_nuevo

    Returns a dict with keys: ok (bool), mensaje (str), stats (dict).
    """
    if not cycle_id_anterior or not cycle_id_nuevo:
        return {"ok": False, "mensaje": "cycle_id_anterior y cycle_id_nuevo son requeridos.", "stats": {}}

    client = get_supabase_client()
    if not client:
        return {"ok": False, "mensaje": "Supabase no disponible.", "stats": {}}

    try:
        docs_ant = _get_docs_simple_by_cycle(cycle_id_anterior)
        docs_nue = _get_docs_simple_by_cycle(cycle_id_nuevo)

        keys_ant: Dict[str, Dict] = {str(d.get("match_key", "")): d for d in docs_ant if d.get("match_key")}
        keys_nue: Dict[str, Dict] = {str(d.get("match_key", "")): d for d in docs_nue if d.get("match_key")}

        # Docs in anterior but NOT in nuevo → recovered
        keys_recuperados = set(keys_ant.keys()) - set(keys_nue.keys())

        # Build per-client stats for cycle_id_nuevo
        cliente_nuevo: Dict[str, Dict[str, Any]] = {}
        for doc in docs_nue:
            cid = str(doc.get("cliente_id", "")).strip()
            if not cid:
                continue
            if cid not in cliente_nuevo:
                cliente_nuevo[cid] = {"docs_total": 0, "monto_total": 0.0,
                                       "docs_recuperados": 0, "monto_recuperado": 0.0}
            cliente_nuevo[cid]["docs_total"] += 1
            cliente_nuevo[cid]["monto_total"] += float(doc.get("saldo_real") or 0)

        # Build per-client recovered stats
        for mk in keys_recuperados:
            doc = keys_ant[mk]
            cid = str(doc.get("cliente_id", "")).strip()
            if not cid:
                continue
            if cid not in cliente_nuevo:
                cliente_nuevo[cid] = {"docs_total": 0, "monto_total": 0.0,
                                       "docs_recuperados": 0, "monto_recuperado": 0.0}
            cliente_nuevo[cid]["docs_recuperados"] += 1
            cliente_nuevo[cid]["monto_recuperado"] += float(doc.get("saldo_real") or 0)

        # Gestiones por cliente en el ciclo nuevo
        gestiones_nuevas = get_gestiones_list(limit=5000)  # All recent
        gestiones_por_cliente: Dict[str, int] = {}
        for g in gestiones_nuevas:
            cid = str(g.get("cliente_id", "")).strip()
            if cid:
                gestiones_por_cliente[cid] = gestiones_por_cliente.get(cid, 0) + 1

        # Acuerdos activos por cliente
        acuerdos_resp = _safe_execute(
            client.table("acuerdos_pago").select("cliente_id").eq("estado", "ACTIVO")
        )
        clientes_con_acuerdo: set = set()
        if acuerdos_resp and acuerdos_resp.data:
            clientes_con_acuerdo = {str(r["cliente_id"]).strip() for r in acuerdos_resp.data}

        # Persist resumen_cliente_ciclo
        ahora = datetime.utcnow().isoformat()
        resumen_rows = []
        for cid, stats in cliente_nuevo.items():
            n_gestiones = gestiones_por_cliente.get(cid, 0)
            tiene_acuerdo = cid in clientes_con_acuerdo
            if stats["docs_total"] == 0 and stats["docs_recuperados"] > 0:
                estado_cli = "RECUPERADO"
            elif stats["docs_recuperados"] > 0:
                estado_cli = "PARCIAL"
            elif n_gestiones == 0:
                estado_cli = "SIN_ACTIVIDAD"
            else:
                estado_cli = "PENDIENTE"

            resumen_rows.append({
                "cliente_id": cid,
                "cycle_id": cycle_id_nuevo,
                "docs_total": stats["docs_total"],
                "monto_total": round(stats["monto_total"], 2),
                "docs_recuperados": stats["docs_recuperados"],
                "monto_recuperado": round(stats["monto_recuperado"], 2),
                "gestiones_count": n_gestiones,
                "tiene_acuerdo_pago": tiene_acuerdo,
                "estado": estado_cli,
                "updated_at": ahora,
            })

        if resumen_rows:
            _safe_execute(
                client.table("resumen_cliente_ciclo")
                .upsert(resumen_rows, on_conflict="cliente_id,cycle_id")
            )

        # Persist resumen_ciclo
        total_docs_rec = sum(v["docs_recuperados"] for v in cliente_nuevo.values())
        total_monto_rec = sum(v["monto_recuperado"] for v in cliente_nuevo.values())
        total_docs_ant = len(keys_ant)
        tasa = round(total_docs_rec / total_docs_ant * 100, 2) if total_docs_ant > 0 else 0.0

        total_gestiones = len(gestiones_nuevas)
        total_acuerdos_resp = _safe_execute(
            client.table("acuerdos_pago").select("id", count="exact").eq("estado", "ACTIVO")
        )
        total_acuerdos = total_acuerdos_resp.count if total_acuerdos_resp else 0

        resumen_ciclo_row = {
            "cycle_id": cycle_id_nuevo,
            "cycle_id_anterior": cycle_id_anterior,
            "clientes_total": len(cliente_nuevo),
            "docs_total": len(keys_nue),
            "monto_total": round(sum(v["monto_total"] for v in cliente_nuevo.values()), 2),
            "clientes_recuperados": sum(1 for v in cliente_nuevo.values() if v["docs_recuperados"] > 0),
            "docs_recuperados": total_docs_rec,
            "monto_recuperado": round(total_monto_rec, 2),
            "tasa_recuperacion": tasa,
            "gestiones_total": total_gestiones,
            "acuerdos_total": total_acuerdos or 0,
            "updated_at": ahora,
        }
        _safe_execute(
            client.table("resumen_ciclo")
            .upsert([resumen_ciclo_row], on_conflict="cycle_id")
        )

        stats_out = {
            "clientes_total": len(cliente_nuevo),
            "docs_recuperados": total_docs_rec,
            "monto_recuperado": round(total_monto_rec, 2),
            "tasa_recuperacion": tasa,
        }
        return {
            "ok": True,
            "mensaje": (
                f"Trazabilidad calculada: {total_docs_rec} docs recuperados "
                f"({tasa}%) sobre {total_docs_ant} del ciclo anterior."
            ),
            "stats": stats_out,
        }
    except Exception as e:
        print(f"reconcile_ciclo_recovery Error: {e}")
        return {"ok": False, "mensaje": f"Error en reconciliación: {e}", "stats": {}}


# ---------------------------------------------------------------------------
# RC-FEAT-022: Bandeja de Pendientes
# ---------------------------------------------------------------------------

def get_cuotas_pendientes_hoy(limit: int = 200) -> List[Dict[str, Any]]:
    """Return cuotas_acuerdo with estado=PENDIENTE and fecha_vencimiento <= today."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        resp = _safe_execute(
            client.table("cuotas_acuerdo")
            .select("id,acuerdo_id,numero_cuota,monto_cuota,fecha_vencimiento,estado,notas,"
                    "acuerdos_pago(cliente_id,gestor,ciclo_id)")
            .eq("estado", "PENDIENTE")
            .lte("fecha_vencimiento", today_str)
            .order("fecha_vencimiento")
            .limit(limit)
        )
        return resp.data if resp and resp.data else []
    except Exception as e:
        print(f"get_cuotas_pendientes_hoy Error: {e}")
        return []


def get_clientes_sin_gestion_ciclo(cycle_id: str, limit: int = 200) -> List[str]:
    """Return cliente_ids in cycle_id that have zero gestiones registered."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        # Get all clients in cycle
        docs_resp = _safe_execute(
            client.table("documentos_ciclo")
            .select("cliente_id")
            .eq("cycle_id", str(cycle_id))
            .limit(2000)
        )
        all_clients = {str(d["cliente_id"]).strip() for d in (docs_resp.data or []) if d.get("cliente_id")}

        # Get clients with gestiones in cycle
        gestiones_resp = _safe_execute(
            client.table("gestiones")
            .select("cliente_id")
            .eq("cycle_id", str(cycle_id))
            .limit(2000)
        )
        clients_with_gestiones = {str(d["cliente_id"]).strip() for d in (gestiones_resp.data or []) if d.get("cliente_id")}

        sin_gestion = sorted(all_clients - clients_with_gestiones)
        return sin_gestion[:limit]
    except Exception as e:
        print(f"get_clientes_sin_gestion_ciclo Error: {e}")
        return []


# ---------------------------------------------------------------------------
# RC-FEAT-038: Dashboard de Efectividad — Funciones de consulta
# ---------------------------------------------------------------------------

def get_funnel_cobranza(cycle_id: Optional[str] = None) -> Dict[str, int]:
    """Funnel de cobranza: cartera → notificados → respondieron → acuerdo → recuperado.

    Returns dict with keys: cartera, notificados_wa, notificados_email,
    con_respuesta, con_acuerdo, recuperados.
    """
    client = get_supabase_client()
    if not client:
        return {}
    try:
        # Cartera = clientes ÚNICOS en el ciclo.
        # REGLA: los registros DSP y PAV se excluyen del cálculo de SALDOS y de la cartera
        # financiera (un cliente con SOLO registros DSP/PAV no tiene deuda real en cobranza).
        # Pero el flag enviar_email es una propiedad del CLIENTE, no del registro:
        # si un cliente tiene facturas FAC + notas DSP, el DSP solo reduce su saldo,
        # no lo saca de cartera. Por eso set_notificable usa TODOS los documentos
        # para respetar la voluntad de notificar al cliente, independiente del tipo de documento.
        # Nota: documentos_ciclo usa cod_cliente (no cliente_id) como clave de cliente.
        q_docs = client.table("documentos_ciclo").select("cod_cliente, tipo_pedido, enviar_email")
        if cycle_id:
            q_docs = q_docs.eq("cycle_id", str(cycle_id))
        resp_docs = _safe_execute(q_docs.limit(5000))
        _TIPOS_EXCL = {"DSP", "PAV"}
        _todos_docs = [r for r in (resp_docs.data or []) if r.get("cod_cliente")]
        # _filas_validas: registros de deuda real (excluye DSP/PAV) — base de la cartera financiera
        _filas_validas = [
            r for r in _todos_docs
            if str(r.get("tipo_pedido", "") or "").strip().upper() not in _TIPOS_EXCL
        ]
        # cartera_total: clientes con al menos UN registro de deuda real
        cartera_total = len({str(r["cod_cliente"]).strip() for r in _filas_validas})
        # cartera notificable: de la cartera financiera, los que tienen enviar_email='SI'
        cartera = len({
            str(r["cod_cliente"]).strip()
            for r in _filas_validas
            if str(r.get("enviar_email", "SI") or "SI").strip().upper() == "SI"
        })  # base de los KPIs operativos

        # Notificados WA = clientes únicos que recibieron envío masivo en el ciclo.
        # Solo tipo_registro='ENVIO' — no los seguimientos manuales del gestor.
        q_wa = (client.table("gestiones").select("cliente_id")
                .eq("tipo_gestion", "WHATSAPP").eq("tipo_registro", "ENVIO"))
        if cycle_id:
            q_wa = q_wa.eq("cycle_id", str(cycle_id))
        resp_wa = _safe_execute(q_wa.limit(5000))
        set_wa = {str(r["cliente_id"]).strip() for r in (resp_wa.data or []) if r.get("cliente_id")}
        notificados_wa = len(set_wa)

        # Notificados Email = clientes únicos con notificación EMAIL ENVIADA en el ciclo
        q_email = client.table("notificaciones").select("cliente_id").eq("tipo_notificacion", "EMAIL").eq("estado", "ENVIADO")
        if cycle_id:
            q_email = q_email.eq("cycle_id", str(cycle_id))
        resp_email = _safe_execute(q_email.limit(5000))
        set_email = {str(r["cliente_id"]).strip() for r in (resp_email.data or []) if r.get("cliente_id")}
        notificados_email = len(set_email)

        # Con gestión registrada = clientes únicos a los que el gestor registró CUALQUIER resultado.
        # Filtra tipo_registro='GESTION' (acciones manuales del gestor).
        # NO filtra por resultado — SIN_RESPUESTA también es una gestión registrada.
        # Selecciona tipo_gestion también — se reutiliza para calcular set_directo sin query extra.
        # set_notificable: clientes que (1) tienen deuda real en cartera Y (2) tienen enviar_email='SI'.
        # La condición (1) usa _filas_validas (excluye DSP/PAV — sin deuda real, fuera de cobranza).
        # La condición (2) usa _todos_docs: el flag enviar_email es del CLIENTE, no del registro.
        # Razón: un cliente puede tener FAC + DSP; el DSP no debe anular su flag de notificación.
        # Un cliente con SOLO registros DSP/PAV no tiene deuda real → queda fuera del funnel.
        _set_en_cartera = {str(r["cod_cliente"]).strip() for r in _filas_validas}
        _set_con_flag   = {
            str(r["cod_cliente"]).strip()
            for r in _todos_docs
            if str(r.get("enviar_email", "SI") or "SI").strip().upper() == "SI"
        }
        set_notificable = _set_en_cartera & _set_con_flag  # intersección exacta

        _TIPOS_DIRECTOS = {"LLAMADA", "VISITA", "NOTA", "OTRO"}
        q_resp = (client.table("gestiones").select("cliente_id, tipo_gestion")
                  .eq("tipo_registro", "GESTION"))
        if cycle_id:
            q_resp = q_resp.eq("cycle_id", str(cycle_id))
        resp_resp = _safe_execute(q_resp.limit(5000))
        # Intersectar con set_notificable: especiales NO cuentan en el funnel operativo
        set_resp = {
            str(r["cliente_id"]).strip()
            for r in (resp_resp.data or [])
            if r.get("cliente_id") and str(r["cliente_id"]).strip() in set_notificable
        }
        con_respuesta = len(set_resp)

        # Gestión directa = LLAMADA/VISITA/NOTA/OTRO — derivado de resp_resp (sin query extra).
        # Representa el trabajo proactivo del gestor: llamadas, visitas, notas directas.
        # Solo cuenta clientes notificables (mismo filtro que el resto del funnel).
        _filas_directas = [
            r for r in (resp_resp.data or [])
            if r.get("cliente_id")
            and str(r["cliente_id"]).strip() in set_notificable
            and str(r.get("tipo_gestion", "") or "").upper() in _TIPOS_DIRECTOS
        ]
        set_directo = {str(r["cliente_id"]).strip() for r in _filas_directas}
        contacto_directo = len(set_directo)

        # Desglose de gestión directa por canal — clientes únicos por tipo.
        # Permite mostrar "Con gestión directa: 2 (1 llamada · 1 visita)" en el funnel.
        def _cuentadir(tipo: str) -> int:
            return len({str(r["cliente_id"]).strip() for r in _filas_directas
                        if str(r.get("tipo_gestion", "") or "").upper() == tipo})
        llamadas_dir = _cuentadir("LLAMADA")
        visitas_dir  = _cuentadir("VISITA")
        notas_dir    = _cuentadir("NOTA")
        otros_dir    = _cuentadir("OTRO")

        # Métricas de cobertura derivadas con set operations (sin doble conteo)
        set_notif   = set_wa | set_email                 # notificados por sistema
        set_alcanz  = set_notif | set_directo            # alcanzados por cualquier vía
        alcanzados     = len(set_alcanz)
        sin_contactar  = max(cartera - alcanzados, 0)
        pendientes_seg = max(alcanzados - con_respuesta, 0)  # alcanzados sin resultado aún

        # Acuerdos activos = registros únicos (1 acuerdo por cliente por ciclo)
        q_acuerdo = client.table("acuerdos_pago").select("id", count="exact").eq("estado", "ACTIVO")
        if cycle_id:
            q_acuerdo = q_acuerdo.eq("ciclo_id", str(cycle_id))
        resp_acuerdo = _safe_execute(q_acuerdo.limit(1))
        con_acuerdo = resp_acuerdo.count if resp_acuerdo else 0

        # Recuperados = clientes únicos con resultado EXITOSO confirmado manualmente por el gestor.
        # Solo tipo_registro='GESTION' — los envíos automáticos (tipo_registro='ENVIO') no cuentan.
        # Alineado con PASO 2 ⑨ de sql/99_dashboard_data_reconciliation.sql
        q_rec = (client.table("gestiones").select("cliente_id")
                 .eq("resultado", "EXITOSO").eq("tipo_registro", "GESTION"))
        if cycle_id:
            q_rec = q_rec.eq("cycle_id", str(cycle_id))
        resp_rec = _safe_execute(q_rec.limit(5000))
        recuperados = len({str(r["cliente_id"]).strip() for r in (resp_rec.data or []) if r.get("cliente_id")})

        return {
            "cartera":           cartera,          # cartera notificable — base de KPIs operativos
            "cartera_total":     cartera_total,    # exposición financiera total (incluye especiales)
            "notificados_wa":    notificados_wa,
            "notificados_email": notificados_email,
            "contacto_directo":  contacto_directo, # LLAMADA/VISITA/NOTA — proactivo del gestor
            "llamadas_dir":      llamadas_dir,     # clientes únicos contactados por LLAMADA
            "visitas_dir":       visitas_dir,      # clientes únicos contactados por VISITA
            "notas_dir":         notas_dir,        # clientes únicos con NOTA registrada
            "otros_dir":         otros_dir,        # clientes únicos con OTRO canal directo
            "alcanzados":        alcanzados,        # unión exacta notificados ∪ contacto directo
            "sin_contactar":     sin_contactar,     # cartera − alcanzados (métrica de alarma)
            "con_respuesta":     con_respuesta,     # con resultado GESTION registrado
            "pendientes_seg":    pendientes_seg,    # alcanzados − con_respuesta
            "con_acuerdo":       con_acuerdo,
            "recuperados":       recuperados,
        }
    except Exception as e:
        print(f"get_funnel_cobranza Error: {e}")
        return {}


def get_efectividad_por_plantilla(cycle_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns effectivity grouped by WA template used.

    Each row: {plantilla, total_enviados, exitosos, tasa_pct}
    Derived from notificaciones.metadata (campo 'template') + gestiones.resultado.
    """
    client = get_supabase_client()
    if not client:
        return []
    try:
        # Los WA masivos se graban en gestiones (tipo_gestion='WHATSAPP', tipo_registro='ENVIO').
        # La plantilla usada queda en metadata->>'template_label'.
        # Alineado con PASO 4 de sql/99_dashboard_data_reconciliation.sql
        import json as _json
        q = (client.table("gestiones")
             .select("cliente_id, metadata, resultado")
             .eq("tipo_gestion", "WHATSAPP")
             .eq("tipo_registro", "ENVIO"))
        if cycle_id:
            q = q.eq("cycle_id", str(cycle_id))
        resp = _safe_execute(q.limit(5000))
        notifs = resp.data or []

        # Agrupar por plantilla
        plantilla_totales: Dict[str, int] = {}
        plantilla_clientes: Dict[str, set] = {}
        for n in notifs:
            meta = n.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = _json.loads(meta)
                except Exception:
                    meta = {}
            plantilla = str(meta.get("template_label", meta.get("template", meta.get("plantilla", "Desconocida"))))
            plantilla_totales[plantilla] = plantilla_totales.get(plantilla, 0) + 1
            if plantilla not in plantilla_clientes:
                plantilla_clientes[plantilla] = set()
            cli = str(n.get("cliente_id", "")).strip()
            if cli:
                plantilla_clientes[plantilla].add(cli)

        if not plantilla_totales:
            return []

        # Exitosos = gestiones manuales (tipo_registro='GESTION') con resultado EXITOSO en el ciclo.
        # Se cruzan por cliente para determinar cuántos de los enviados con cada plantilla respondieron.
        q_g = (client.table("gestiones").select("cliente_id, resultado")
               .eq("resultado", "EXITOSO").eq("tipo_registro", "GESTION"))
        if cycle_id:
            q_g = q_g.eq("cycle_id", str(cycle_id))
        resp_g = _safe_execute(q_g.limit(5000))
        exitosos_set = {str(r["cliente_id"]).strip() for r in (resp_g.data or []) if r.get("cliente_id")}

        result = []
        for plantilla, total in sorted(plantilla_totales.items(), key=lambda x: -x[1]):
            clientes_p = plantilla_clientes.get(plantilla, set())
            exitosos = len(clientes_p & exitosos_set)
            tasa = round(exitosos / total * 100, 1) if total > 0 else 0.0
            result.append({
                "plantilla": plantilla,
                "total_enviados": total,
                "exitosos": exitosos,
                "tasa_pct": tasa,
            })
        return result
    except Exception as e:
        print(f"get_efectividad_por_plantilla Error: {e}")
        return []


def get_top_clientes_criticos(n: int = 10, cycle_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Top N clientes ordenados por saldo pendiente desc.

    Returns list of dicts: {cliente_id, nombre, saldo_total, docs_count,
    dias_mora_max, gestiones_count, ultimo_resultado}
    """
    client = get_supabase_client()
    if not client:
        return []
    # Tipos de pedido que son datos basura — excluidos del análisis
    _TIPOS_EXCLUIDOS = {"DSP", "PAV"}

    try:
        q = client.table("documentos_ciclo").select(
            "cliente_id, empresa, saldo_real, dias_mora, fech_venc, moneda, tipo_pedido, enviar_email"
        )
        if cycle_id:
            q = q.eq("cycle_id", str(cycle_id))
        resp = _safe_execute(q.limit(2000))
        docs = resp.data or []

        # Agregar por cliente (excluyendo tipos de pedido basura)
        cliente_data: Dict[str, Dict[str, Any]] = {}
        for d in docs:
            # Filtrar datos basura
            tipo_ped = str(d.get("tipo_pedido", "") or "").strip().upper()
            if tipo_ped in _TIPOS_EXCLUIDOS:
                continue

            cid = str(d.get("cliente_id", "")).strip()
            if not cid:
                continue

            moneda = str(d.get("moneda", "") or "").strip().upper()
            es_sol = moneda.startswith("S")
            saldo  = float(d.get("saldo_real") or 0)

            if cid not in cliente_data:
                _env = str(d.get("enviar_email", "SI") or "SI").strip().upper()
                cliente_data[cid] = {
                    "cliente_id":  cid,
                    "nombre":      str(d.get("empresa", cid)),
                    "saldo_sol":   0.0,
                    "saldo_usd":   0.0,
                    "docs_sol":    0,
                    "docs_usd":    0,
                    "dias_mora_max": 0,
                    "es_especial": _env != "SI",  # True = cliente especial, excluido del funnel KPI
                }
            if es_sol:
                cliente_data[cid]["saldo_sol"] += saldo
                cliente_data[cid]["docs_sol"]  += 1
            else:
                cliente_data[cid]["saldo_usd"] += saldo
                cliente_data[cid]["docs_usd"]  += 1

            try:
                mora = int(d.get("dias_mora") or 0)
            except (ValueError, TypeError):
                mora = 0
            if mora > cliente_data[cid]["dias_mora_max"]:
                cliente_data[cid]["dias_mora_max"] = mora

        for data in cliente_data.values():
            data["saldo_total"] = data["saldo_sol"] + data["saldo_usd"]
            data["docs_count"]  = data["docs_sol"] + data["docs_usd"]

        if not cliente_data:
            return []

        # Solo gestiones MANUALES del gestor (tipo_registro='GESTION').
        # Los envíos automáticos (tipo_registro='ENVIO') no cuentan como gestión.
        # Alineado con PASO 5 ⑬ de sql/99_dashboard_data_reconciliation.sql
        q_g = (client.table("gestiones")
               .select("cliente_id, resultado, fecha")
               .eq("tipo_registro", "GESTION")
               .order("fecha", desc=True))
        if cycle_id:
            q_g = q_g.eq("cycle_id", str(cycle_id))
        resp_g = _safe_execute(q_g.limit(5000))
        gestiones_rows = resp_g.data or []

        gestiones_count: Dict[str, int] = {}
        ultimo_resultado: Dict[str, str] = {}
        fecha_ultimo_gestion: Dict[str, str] = {}
        for g in gestiones_rows:
            cid = str(g.get("cliente_id", "")).strip()
            gestiones_count[cid] = gestiones_count.get(cid, 0) + 1
            if cid not in ultimo_resultado:
                ultimo_resultado[cid] = str(g.get("resultado", ""))
                fecha_ultimo_gestion[cid] = str(g.get("fecha", "") or "")

        for cid, data in cliente_data.items():
            data["gestiones_count"] = gestiones_count.get(cid, 0)
            data["ultimo_resultado"] = ultimo_resultado.get(cid, "SIN_GESTION")
            data["fecha_ultimo_gestion"] = fecha_ultimo_gestion.get(cid, "")

        # Ordenar por saldo_sol DESC (referencia principal), igual que PASO 5 ⑫ del SQL.
        # Clientes con saldo solo en USD quedan al final (saldo_sol = 0).
        sorted_clientes = sorted(cliente_data.values(), key=lambda x: -x["saldo_sol"])
        return sorted_clientes[:n]
    except Exception as e:
        print(f"get_top_clientes_criticos Error: {e}")
        return []


def get_kpis_periodo(date_from: str, date_to: str) -> Dict[str, Any]:
    """KPIs agregados para un rango de fechas (YYYY-MM-DD).

    Returns: {gestiones_total, exitosos, promesas, sin_respuesta,
    tasa_exito_pct, notificaciones_wa, notificaciones_email,
    tasa_notif_exitosa_pct, acuerdos_activos}
    """
    client = get_supabase_client()
    if not client:
        return {}
    try:
        # Gestiones del período — solo gestiones manuales del gestor (tipo_registro='GESTION').
        # Los envíos automáticos del sistema (tipo_registro='ENVIO') se cuentan
        # en el bloque de WA enviados, no aquí.
        # Sufijo -05:00 = hora Lima (UTC-5).
        resp_g = _safe_execute(
            client.table("gestiones")
            .select("resultado, fecha")
            .eq("tipo_registro", "GESTION")
            .gte("fecha", f"{date_from}T00:00:00-05:00")
            .lte("fecha", f"{date_to}T23:59:59-05:00")
            .limit(10000)
        )
        gestiones = resp_g.data or []

        by_resultado: Dict[str, int] = {}
        for g in gestiones:
            r = str(g.get("resultado", "PENDIENTE"))
            by_resultado[r] = by_resultado.get(r, 0) + 1

        total_g = len(gestiones)
        exitosos = by_resultado.get("EXITOSO", 0)
        promesas = by_resultado.get("PROMESA_PAGO", 0)
        sin_resp = by_resultado.get("SIN_RESPUESTA", 0)
        tasa_exito = round(exitosos / total_g * 100, 1) if total_g > 0 else 0.0

        # Notificaciones EMAIL en el período (emails se guardan en notificaciones)
        resp_n = _safe_execute(
            client.table("notificaciones")
            .select("tipo_notificacion, estado, fecha_envio")
            .gte("fecha_envio", f"{date_from}T00:00:00-05:00")
            .lte("fecha_envio", f"{date_to}T23:59:59-05:00")
            .limit(10000)
        )
        notifs = resp_n.data or []
        notif_email = sum(1 for n in notifs if str(n.get("tipo_notificacion", "")).upper() == "EMAIL")
        notif_enviadas = sum(1 for n in notifs if str(n.get("estado", "")).upper() == "ENVIADO")
        tasa_notif = round(notif_enviadas / len(notifs) * 100, 1) if notifs else 0.0

        # Mensajes WA enviados en el período — solo envíos automáticos del sistema
        # (tipo_registro='ENVIO'). Los seguimientos manuales son tipo_registro='GESTION'
        # y se cuentan en gestiones_total, no aquí.
        resp_wa_g = _safe_execute(
            client.table("gestiones")
            .select("tipo_gestion")
            .eq("tipo_gestion", "WHATSAPP")
            .eq("tipo_registro", "ENVIO")
            .gte("fecha", f"{date_from}T00:00:00-05:00")
            .lte("fecha", f"{date_to}T23:59:59-05:00")
            .limit(10000)
        )
        notif_wa = len(resp_wa_g.data or [])

        # Acuerdos activos (no filtrados por fecha — estado actual)
        resp_a = _safe_execute(
            client.table("acuerdos_pago").select("id", count="exact").eq("estado", "ACTIVO").limit(1)
        )
        acuerdos_activos = resp_a.count if resp_a else 0

        return {
            "gestiones_total": total_g,
            "exitosos": exitosos,
            "promesas": promesas,
            "sin_respuesta": sin_resp,
            "by_resultado": by_resultado,
            "tasa_exito_pct": tasa_exito,
            "notificaciones_wa": notif_wa,
            "notificaciones_email": notif_email,
            "tasa_notif_exitosa_pct": tasa_notif,
            "acuerdos_activos": acuerdos_activos,
        }
    except Exception as e:
        print(f"get_kpis_periodo Error: {e}")
        return {}
