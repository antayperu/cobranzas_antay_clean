import json
import os

CONFIG_FILE = "config.json"

DEFAULT_SETTINGS = {
    "company_name": "DACTA SOCIEDAD ANONIMA CERRADA - DACTA S.A.C.",
    "company_ruc": "20375779448",
    "phone_contact": "+51 998 080 797",
    "primary_color": "#2E86AB",
    "secondary_color": "#A23B72",
    "email_template": {
        "intro_text": "Le informamos que a la fecha presenta documentos pendientes de pago.\nAgradeceremos gestionar la cancelación para mantener su servicio activo y evitar inconvenientes.",
        "footer_text": "En caso de haber realizado el pago recientemente, por favor hacer caso omiso a este mensaje.\n\nAtentamente,\nÁrea de Cobranzas y Facturación",
        "alert_text": "Si el documento está afecto a Detracción, debe abonarlo en nuestra cuenta del Banco de la Nación N° 00-058-420913."
    },
    "smtp_config": {
        "server": "smtp.gmail.com",
        "port": "587",
        "user": "",
        "password": ""
    },
    "supervisor_config": {
        "email": "acamacho@integrens.com",
        "enabled": True,
        "mode": "BCC"
    },
    "whatsapp_template": (
        "Estimados *{EMPRESA}*,\n\n"
        "Adjuntamos el Estado de Cuenta actualizado. A la fecha, presentan documentos pendientes por un *Total de: {TOTAL_SALDO_REAL}*.\n\n"
        "**Detalle de Documentos:**\n"
        "{DETALLE_DOCS}\n\n"
        "Agradeceremos gestionar el pago a la brevedad.\n\n"
        "_DACTA S.A.C. | RUC: 20375779448 Este es un mensaje automático de notificación de deuda. Consultas: +51 998 080 797_"
    ),
    "text_color": "#262730",
    "features": {
        "show_analysis": False,
        "show_sales": False
    },
    "report_views": {
        "ejecutiva": [
            "COD CLIENTE", "EMPRESA", "COMPROBANTE", "FECHA EMISIÓN", "MONEDA", 
            "MONT EMIT", "TIPO CAMBIO", "SALDO", "DETRACCIÓN", "ESTADO DETRACCION", 
            "AMORTIZACIONES", "SALDO REAL", "ESTADO_EMAIL", "FECHA_ULTIMO_ENVIO", 
            "NOTA", "ENVIAR EMAIL"
        ],
        "completa": [
             "COD CLIENTE", "EMPRESA", "COMPROBANTE", "FECHA EMISIÓN", "MONEDA", 
            "MONT EMIT", "TIPO CAMBIO", "SALDO", "DETRACCIÓN", "ESTADO DETRACCION", 
            "AMORTIZACIONES", "SALDO REAL", "ESTADO_EMAIL", "FECHA_ULTIMO_ENVIO", 
            "NOTA", "ENVIAR EMAIL"
        ]
    }
}

def load_settings():
    """Carga configuración desde JSON o devuelve defaults."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            # Merge con defaults por si faltan claves nuevas
            settings = DEFAULT_SETTINGS.copy()
            
            # Update recursivo simple
            for k, v in saved.items():
                if isinstance(v, dict) and k in settings and isinstance(settings[k], dict):
                    settings[k].update(v)
                else:
                    settings[k] = v
            
            # --- RC-FEAT-CLOUD: Safe Multi-Source Settings ---
            # 1. Start with Defaults
            # 2. Merge JSON (User UI changes) -> This is already done in for-loop above
            
            # 3. Apply Environment Variables ONLY IF the value is still the default or empty
            # (Allows Railway dashboard to provide initial setup, but UI can override them)
            
            env_map = {
                "SMTP_SERVER": ('smtp_config', 'server'),
                "SMTP_PORT": ('smtp_config', 'port'),
                "SMTP_USER": ('smtp_config', 'user'),
                "SMTP_PASSWORD": ('smtp_config', 'password'),
                "SUPABASE_URL": ('supabase_config', 'url'),
                "SUPABASE_KEY": ('supabase_config', 'key')
            }
            
            for env_name, (section, key) in env_map.items():
                env_val = os.getenv(env_name)
                if env_val:
                    # Specific Logic: Don't override if user has already set a non-default value in JSON
                    # (Simple check: if JSON has anything other than "" or "587" in some cases)
                    if section in settings:
                         current_val = settings[section].get(key, "")
                         # If current_val is empty or the absolute hardcoded default, use Env Var
                         if not current_val or current_val in ["", "587", "smtp.gmail.com"]:
                             settings[section][key] = env_val
                    else:
                         # For sections that don't exist yet (like supabase_config)
                         if section not in settings: settings[section] = {}
                         settings[section][key] = env_val
                
            return settings
    except:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Guarda la configuración en JSON."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
