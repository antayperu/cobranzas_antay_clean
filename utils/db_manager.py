import sqlite3
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configuración de Motores ---
DB_NAME = "email_ledger.db"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

_client = None

def get_supabase_client():
    """Inicializa el cliente de Supabase solo si es necesario."""
    global _client
    if _client is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Supabase Init Error: {e}")
    return _client

def is_cloud_mode():
    """Detecta si la app debe operar en modo Cloud."""
    return SUPABASE_URL is not None and SUPABASE_KEY is not None

def initialize_db():
    """Asegura que las tablas existan en local (SQLite). 
    En Cloud se asume que se ejecutó el script SQL inicial."""
    if not is_cloud_mode():
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS ledger_last_send
                         (ledger_key TEXT PRIMARY KEY, last_sent_at TIMESTAMP, last_msg_id TEXT, send_count INTEGER)''')
            c.execute('''CREATE TABLE IF NOT EXISTS send_attempts
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, ledger_key TEXT, recipient TEXT, status TEXT, reason TEXT, timestamp TIMESTAMP, run_id TEXT)''')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Init Error: {e}")
            return False
    return True # En Cloud retornamos True (asumido setup manual)

# --- Funciones de Interfaz Única (SSOT) ---

def log_attempt(recipient, status, run_id, ledger_key, reason=""):
    """Registra un intento de envío en el motor activo."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                # 1. Insert search_attempts
                client.table("send_attempts").insert({
                    "recipient": recipient,
                    "status": status,
                    "run_id": run_id,
                    "ledger_key": ledger_key,
                    "reason": reason,
                    "timestamp": ts
                }).execute()
                
                # 2. Update/Upsert ledger_last_send
                # Upsert en Supabase requiere que ledger_key sea PK
                client.table("ledger_last_send").upsert({
                    "ledger_key": ledger_key,
                    "last_sent_at": ts,
                    "send_count": 1 # Podríamos incrementar, pero para tracking basta el timestamp
                }).execute()
                return True
            except Exception as e:
                print(f"Supabase Logging Error: {e}")

    # Fallback/Local: SQLite
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # History
        c.execute("INSERT INTO send_attempts (id, ledger_key, recipient, status, reason, timestamp, run_id) VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                  (ledger_key, recipient, status, reason, ts, run_id))
        # Last Send Info
        c.execute("INSERT OR REPLACE INTO ledger_last_send (ledger_key, last_sent_at, send_count) VALUES (?, ?, COALESCE((SELECT send_count FROM ledger_last_send WHERE ledger_key = ?), 0) + 1)",
                  (ledger_key, ts, ledger_key))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"SQLite Logging Error: {e}")
        return False

def get_status_map(email_list, target_date_str=None, min_timestamp=None):
    """Obtiene el mapa de estados desde el motor activo."""
    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                query = client.table("send_attempts").select("recipient, status, timestamp").in_("recipient", email_list)
                
                if min_timestamp:
                    query = query.gte("timestamp", str(min_timestamp))
                else:
                    if not target_date_str:
                        target_date_str = datetime.now().strftime("%Y-%m-%d")
                    query = query.like("timestamp", f"{target_date_str}%")
                
                res = query.order("timestamp", desc=False).execute()
                return _process_rows_into_map(res.data)
            except Exception as e:
                print(f"Supabase Query Error: {e}")

    # Local: SQLite
    try:
        conn = sqlite3.connect(DB_NAME)
        params = email_list.copy()
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
            WHERE recipient IN ({','.join(['?']*len(email_list))})
            {date_filter}
            ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return _process_rows_into_map(df.to_dict('records'))
    except Exception as e:
        print(f"SQLite Query Error: {e}")
        return {}

def _process_rows_into_map(rows):
    """Lógica común para procesar filas de DB en el mapa visual."""
    status_map = {}
    priority_map = {'SENT': 3, 'BLOCKED': 2, 'FAILED': 1, 'PENDING': 0}
    
    for row in rows:
        email = row['recipient']
        status = row['status']
        ts = row['timestamp']
        
        try:
            time_str = datetime.strptime(str(ts).split('.')[0].replace('T', ' '), "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        except:
            time_str = str(ts)[11:16]

        current = status_map.get(email, {'status': 'PENDING'})
        curr_prio = priority_map.get(current.get('status', 'PENDING'), 0)
        new_prio = priority_map.get(status, 0)
        
        if new_prio >= curr_prio:
            status_map[email] = {
                'status': status, 
                'time': time_str,
                'ts_raw': ts
            }
    return status_map

def get_today_stats():
    """Obtiene estadísticas del día."""
    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                today_start = datetime.now().strftime("%Y-%m-%d 00:00:00")
                res = client.table("send_attempts").select("status").gte("timestamp", today_start).execute()
                df = pd.DataFrame(res.data)
                if df.empty: return {'SENT': 0, 'FAILED': 0, 'BLOCKED': 0}
                counts = df['status'].value_counts().to_dict()
                return {s: counts.get(s, 0) for s in ['SENT', 'FAILED', 'BLOCKED']}
            except: pass

    # SQLite
    try:
        conn = sqlite3.connect(DB_NAME)
        today_start = datetime.now().strftime("%Y-%m-%d 00:00:00")
        df = pd.read_sql_query("SELECT status, COUNT(*) as count FROM send_attempts WHERE timestamp >= ? GROUP BY status", 
                               conn, params=(today_start,))
        conn.close()
        stats = {s: df[df['status']==s]['count'].sum() for s in ['SENT', 'FAILED', 'BLOCKED']}
        return stats
    except:
        return {'SENT': 0, 'FAILED': 0, 'BLOCKED': 0}

def get_last_sent_info(ledger_key):
    """Consulta la tabla ledger_last_send para TTL."""
    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                res = client.table("ledger_last_send").select("*").eq("ledger_key", ledger_key).execute()
                return res.data[0] if res.data else None
            except: pass

    # SQLite
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM ledger_last_send WHERE ledger_key = ?", (ledger_key,))
        row = c.fetchone()
        conn.close()
        if row:
            return {'ledger_key': row[0], 'last_sent_at': row[1], 'last_msg_id': row[2], 'send_count': row[3]}
    except: pass
    return None

def reset_today_stats():
    """Limpia el historial de hoy."""
    today_pattern = f"{datetime.now().strftime('%Y-%m-%d')}%"
    if is_cloud_mode():
        client = get_supabase_client()
        if client:
            try:
                client.table("send_attempts").delete().like("timestamp", today_pattern).execute()
                client.table("ledger_last_send").delete().like("last_sent_at", today_pattern).execute()
                return True, "Historial de hoy limpiado en Cloud."
            except Exception as e: return False, str(e)

    # SQLite
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM send_attempts WHERE timestamp LIKE ?", (today_pattern,))
        c.execute("DELETE FROM ledger_last_send WHERE last_sent_at LIKE ?", (today_pattern,))
        conn.commit()
        conn.close()
        return True, "Historial de hoy limpiado en Local."
    except Exception as e: return False, str(e)
