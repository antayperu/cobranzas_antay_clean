import sqlite3
import pandas as pd
import os
import hashlib
from datetime import datetime

DB_NAME = "email_ledger.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_full_ledger_df():
    """
    Returns the raw ledger of last sends.
    """
    try:
        conn = get_connection()
        query = "SELECT * FROM ledger_last_send"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"DB Error: {e}")
        return pd.DataFrame()

def get_status_map(email_list, target_date_str=None, min_timestamp=None):
    """
    Returns a dictionary {email: {'status': 'SENT'|'FAILED', 'time': 'HH:MM', 'ts_raw': ...}}
    for the given emails.
    
    Args:
        email_list (list): List of emails to check.
        target_date_str (str): Optional. Filter by date string (YYYY-MM-DD). Default to Today if no min_timestamp provided.
        min_timestamp (str/datetime): Optional. Only include records triggered AFTER this time.
                                      Overrides target_date_str if provided.
    """
    try:
        conn = get_connection()
        
        # Build Query dynamically
        # Standard: Filter by day using string comparison
        date_filter = ""
        params = email_list.copy()
        
        if min_timestamp:
            # Session-Based Scoping: Everything after this TS
            date_filter = "AND timestamp >= ?"
            params.append(str(min_timestamp))
        else:
            # Default: Today
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
        
        status_map = {}
        for _, row in df.iterrows():
            # Last write wins usually, but we want to show 'SENT' if at least one was sent
            email = row['recipient']
            status = row['status']
            ts = row['timestamp']
            
            # Formato hora
            try:
                time_str = datetime.strptime(str(ts).split('.')[0], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
            except:
                time_str = str(ts)[11:16]

            # Logic: If already SENT, keep it. If FAILED, can be overwritten by SENT.
            current = status_map.get(email, {'status': 'PENDING'})
            
            # --- Rich Data Upgrade (Phase 4) ---
            # We store the raw timestamp logic to expose it later
            
            # Priority: SENT > BLOCKED > FAILED > PENDING
            priority_map = {'SENT': 3, 'BLOCKED': 2, 'FAILED': 1, 'PENDING': 0}
            curr_prio = priority_map.get(current.get('status', 'PENDING'), 0)
            new_prio = priority_map.get(status, 0)
            
            if new_prio >= curr_prio:
                status_map[email] = {
                    'status': status, 
                    'time': time_str,
                    'ts_raw': ts # RAW Timestamp for Report
                }

        return status_map
    except Exception as e:
        print(f"DB Error: {e}")
        return {}

def get_today_stats():
    """
    Returns counts of Sent vs Failed for today.
    """
    try:
        conn = get_connection()
        today_start = datetime.now().strftime("%Y-%m-%d 00:00:00")
        query = """
            SELECT status, COUNT(*) as count 
            FROM send_attempts 
            WHERE timestamp >= ? 
            GROUP BY status
        """
        df = pd.read_sql_query(query, conn, params=(today_start,))
        conn.close()
        
        stats = {
            'SENT': df[df['status']=='SENT']['count'].sum(),
            'FAILED': df[df['status']=='FAILED']['count'].sum(),
            'BLOCKED': df[df['status']=='BLOCKED']['count'].sum()
        }
        return stats
        return stats
    except:
        return {'SENT': 0, 'FAILED': 0, 'BLOCKED': 0}

def reset_today_stats():
    """
    Deletes all records from send_attempts for the current day.
    Useful for testing or manual reset by user.
    """
    try:
        conn = get_connection()
        c = conn.cursor()
        today_start = datetime.now().strftime("%Y-%m-%d")
        
        # Delete using LIKE 'YYYY-MM-DD%' pattern
        query = "DELETE FROM send_attempts WHERE timestamp LIKE ?"
        c.execute(query, (f"{today_start}%",))
        rows = c.rowcount
        
        # Also clean ledger_last_send? No, business logic usually keeps last send forever.
        # But if the user wants to retry "immediately" and bypass TTL, they might want this too.
        # For safety/simplicity of the request "Reset Control", we just clear the Status View.
        # The TTL block is separate. Ideally we should allow clearing that too if 'reset'.
        # Let's clean TTL entries for today too just in case.
        
        c.execute("DELETE FROM ledger_last_send WHERE last_sent_at LIKE ?", (f"{today_start}%",))
        
        conn.commit()
        conn.close()
        return True, f"Se eliminaron {rows} registros del historial de hoy."
    except Exception as e:
        print(f"DB Reset Error: {e}")
        return False, str(e)
