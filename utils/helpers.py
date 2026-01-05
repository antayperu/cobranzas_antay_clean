import re
from datetime import datetime

def sanitize_filename(name: str, fallback: str = "Empresa_No_Definida") -> str:
    """
    Limpia un string para que sea seguro como nombre de archivo.
    Reemplaza caracteres inválidos por '_'.
    Si el nombre queda vacío, retorna el fallback.
    """
    if not name or not isinstance(name, str):
        return fallback.strip()
    
    # Reemplazar caracteres no permitidos en Windows
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Reemplazar espacios múltiples y saltos
    cleaned = re.sub(r'\s+', '_', cleaned)
    # Trim
    cleaned = cleaned.strip('_')
    
    if not cleaned:
        return fallback.strip()
        
    return cleaned

def get_export_filename(company_name: str) -> str:
    """
    Genera nombres de archivo estandarizados:
    <EMPRESA>_ReporteCobranzas_<YYYYMMDD>_<HHMM>.xlsx
    """
    safe_name = sanitize_filename(company_name)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M")
    
    return f"{safe_name}_ReporteCobranzas_{timestamp}.xlsx"

def normalize_emails(value):
    """
    Normaliza una entrada de emails (str, list, tuple) a una lista plana de strings limpios.
    Maneja:
    - None -> []
    - str -> split por ',' o ';' o newline
    - list/tuple -> flatten, convert to str, strip
    - Deduplicación preservando orden
    """
    if not value:
        return []
    
    # 1. Unify to list
    if isinstance(value, str):
        # Replace common separators
        normalized = value.replace(';', ',').replace('\n', ',')
        items = normalized.split(',')
    elif isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = [str(value)]
        
    # 2. Clean & Filter
    cleaned = []
    seen = set()
    for item in items:
        s = str(item).strip()
        if s and s.lower() not in seen:
            cleaned.append(s)
            seen.add(s.lower())
            
            
    return cleaned

def safe_clean_decimal(val):
    """
    Convierte valores numéricos o strings con formato (moneda, comas) a float puro.
    Ej: "S/ 1,200.50" -> 1200.50
    """
    import pandas as pd
    try:
        if pd.isna(val) or val == "": return 0.0
        if isinstance(val, (int, float)): return float(val)
        # Cleanup: remove spaces, currency symbols, commas
        # Include common symbols: S/, $, US$, S/.
        s = str(val).replace(",", "").replace("$", "").replace("S/", "").replace("S/.", "").replace("US", "").strip()
        return float(s)
    except:
        return 0.0
