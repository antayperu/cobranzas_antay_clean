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
    "text_color": "#262730",
    "features": {
        "show_analysis": False,
        "show_sales": False
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
