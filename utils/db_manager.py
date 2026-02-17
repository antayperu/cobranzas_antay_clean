import os
import sqlite3
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
    if status_code == "SENT":
        return "INFO", "ENVIADO", _now_str(), "NORMAL"
    if status_code == "BLOCKED":
        return "ALERTA", "PENDIENTE", None, "NORMAL"
    if status_code in {"FAILED", "ERROR", "BOUNCE", "BOUNCED"}:
        return "GESTION_FALLIDA", "PENDIENTE", None, "ALTA"
    return "INFO", "PENDIENTE", None, "NORMAL"


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
    }

    try:
        _safe_execute(client.table("notificaciones").insert(payload))
        return True
    except Exception as e:
        print(f"persist_notification_event Error: {e}")
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
CLIENTES_SELECT_FIELDS = "cliente_id, nombre, email, telefono, ruc, direccion, estado, notas, updated_at"


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


def _normalize_cliente_record(row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    cliente_id = _normalize_cliente_id(row.get("cliente_id"))
    if not cliente_id:
        return None, "cliente_id es obligatorio"

    nombre = _clean_optional_text(row.get("nombre")) or f"Cliente {cliente_id}"
    payload = {
        "cliente_id": cliente_id,
        "nombre": nombre,
        "email": _clean_optional_text(row.get("email"), lower=True),
        "telefono": _clean_optional_text(row.get("telefono")),
        "ruc": _clean_optional_text(row.get("ruc")),
        "direccion": _clean_optional_text(row.get("direccion")),
        "estado": _normalize_cliente_estado(row.get("estado")),
        "notas": _clean_optional_text(row.get("notas")),
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
            haystack = " ".join(
                [
                    str(row.get("cliente_id", "")),
                    str(row.get("nombre", "")),
                    str(row.get("email", "")),
                    str(row.get("telefono", "")),
                    str(row.get("ruc", "")),
                    str(row.get("direccion", "")),
                    str(row.get("notas", "")),
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
        res = _safe_execute(
            client.table("clientes")
            .select(CLIENTES_SELECT_FIELDS)
            .order("nombre")
            .limit(limit)
        )
        rows = list(res.data or [])
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
        res = _safe_execute(
            client.table("clientes")
            .select("cliente_id, nombre, email, telefono, ruc, direccion, estado, notas")
            .order("cliente_id")
            .limit(limit)
        )
        return list(res.data or [])
    except Exception as e:
        print(f"get_clientes_master Error: {e}")
        return []


def update_cliente_fields(
    *,
    cliente_id: str,
    nombre: Optional[str] = None,
    email: Optional[str] = None,
    telefono: Optional[str] = None,
    ruc: Optional[str] = None,
    direccion: Optional[str] = None,
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
    if ruc is not None:
        payload["ruc"] = _clean_optional_text(ruc)
    if direccion is not None:
        payload["direccion"] = _clean_optional_text(direccion)
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
            _safe_execute(client.table("clientes").upsert(batch, on_conflict="cliente_id"))
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
