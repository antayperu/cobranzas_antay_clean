import json
import os

CONFIG_FILE = "email_secrets.json"

def load_email_config():
    """Carga la configuración de email desde el archivo JSON local."""
    if not os.path.exists(CONFIG_FILE):
        return None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando configuración de email: {e}")
        return None

def save_email_config(email, password, recipient=None):
    """Guarda la configuración de email."""
    if not recipient:
        recipient = email # Default to sending to self
        
    config = {
        "sender_email": email,
        "sender_password": password,
        "recipient_email": recipient
    }
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"✅ Configuración guardada en {CONFIG_FILE} (NO COMITEAR ESTE ARCHIVO)")
        return True
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        return False
