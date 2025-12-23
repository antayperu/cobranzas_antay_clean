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
