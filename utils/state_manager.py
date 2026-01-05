import os
import pandas as pd
import datetime
import shutil

# Define cache directory
CACHE_DIR = ".cache"
SESSION_FILE = os.path.join(CACHE_DIR, "current_session.parquet")
META_FILE = os.path.join(CACHE_DIR, "session_meta.txt")

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def save_session(df, metadata_str=""):
    """
    Saves the main DataFrame and metadata to a local cache.
    """
    try:
        ensure_cache_dir()
        # Use parquet for speed and efficient type preservation
        df.to_parquet(SESSION_FILE, index=False)
        
        with open(META_FILE, 'w', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now().isoformat()}|{metadata_str}")
            
        return True, "Sesión guardada exitosamente."
    except Exception as e:
        return False, f"Error guardando sesión: {str(e)}"

def load_session():
    """
    Loads the DataFrame and metadata from cache.
    Returns: (df, metadata_str, load_time) or (None, None, None)
    """
    if not os.path.exists(SESSION_FILE) or not os.path.exists(META_FILE):
        return None, None, None
        
    try:
        df = pd.read_parquet(SESSION_FILE)
        
        with open(META_FILE, 'r', encoding='utf-8') as f:
            content = f.read().split('|')
            timestamp_str = content[0]
            meta = content[1] if len(content) > 1 else ""
            
        load_time = datetime.datetime.fromisoformat(timestamp_str)
        return df, meta, load_time
    except Exception as e:
        print(f"Cache load error: {e}")
        return None, None, None

def clear_session():
    """
    Clears the cache files.
    """
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        if os.path.exists(META_FILE):
            os.remove(META_FILE)
        return True
    except:
        return False

def has_valid_session():
    """
    Checks if a valid session exists without loading the full data.
    """
    if os.path.exists(SESSION_FILE) and os.path.exists(META_FILE):
        try:
            with open(META_FILE, 'r', encoding='utf-8') as f:
                content = f.read().split('|')
                timestamp_str = content[0]
                meta = content[1] if len(content) > 1 else ""
            
            dt = datetime.datetime.fromisoformat(timestamp_str)
            return True, dt, meta
        except:
            pass
    return False, None, None
