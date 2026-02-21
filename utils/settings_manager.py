import copy
import json
import os
from typing import Any, Dict, Optional

from utils.supabase_client import SupabaseClient

CONFIG_FILE = "config.json"  # Legacy bootstrap source only.
CONFIG_TABLE = os.getenv("SUPABASE_CONFIG_TABLE", "app_config")
CONFIG_KEY = os.getenv("SUPABASE_CONFIG_KEY", "global")

DEFAULT_SETTINGS = {
    "company_name": "DACTA SOCIEDAD ANONIMA CERRADA - DACTA S.A.C.",
    "company_ruc": "20375779448",
    "phone_contact": "+51 998 080 797",
    "primary_color": "#2E86AB",
    "secondary_color": "#A23B72",
    "email_template": {
        "intro_text": (
            "Le informamos que a la fecha presenta documentos pendientes de pago.\n"
            "Agradeceremos gestionar la cancelacion para mantener su servicio activo y evitar inconvenientes."
        ),
        "footer_text": (
            "En caso de haber realizado el pago recientemente, por favor hacer caso omiso a este mensaje.\n\n"
            "Atentamente,\nArea de Cobranzas y Facturacion"
        ),
        "alert_text": (
            "Si el documento esta afecto a Detraccion, debe abonarlo en nuestra cuenta del Banco de la Nacion Nro 00-058-420913."
        ),
    },
    "smtp_config": {
        "server": "smtp.gmail.com",
        "port": "587",
        "user": "",
        "password": "",
        "resend_api_key": "",
        "sendgrid_api_key": "",
        "force_smtp": False,
    },
    "supervisor_config": {
        "email": "acamacho@integrens.com",
        "enabled": True,
        "mode": "BCC",
    },
    "whatsapp_template": (
        "Estimados *{EMPRESA}*,\n\n"
        "Adjuntamos el Estado de Cuenta actualizado. A la fecha, presentan documentos pendientes por un *Total de: {TOTAL_SALDO_REAL}*.\n\n"
        "**Detalle de Documentos:**\n"
        "{DETALLE_DOCS}\n\n"
        "Agradeceremos gestionar el pago a la brevedad.\n\n"
        "_DACTA S.A.C. | RUC: 20375779448 Este es un mensaje automatico de notificacion de deuda. Consultas: +51 998 080 797_"
    ),
    "text_color": "#262730",
    "features": {
        "show_analysis": False,
        "show_sales": False,
    },
    "report_views": {
        "ejecutiva": [
            "COD CLIENTE",
            "EMPRESA",
            "COMPROBANTE",
            "FECHA EMISIÓN",
            "MONEDA",
            "MONT EMIT",
            "TIPO CAMBIO",
            "SALDO",
            "DETRACCIÓN",
            "ESTADO DETRACCION",
            "AMORTIZACIONES",
            "SALDO REAL",
            "ESTADO_EMAIL",
            "FECHA_ULTIMO_ENVIO",
            "NOTA",
            "ENVIAR EMAIL",
        ],
        "completa": [
            "COD CLIENTE",
            "EMPRESA",
            "COMPROBANTE",
            "FECHA EMISIÓN",
            "MONEDA",
            "MONT EMIT",
            "TIPO CAMBIO",
            "SALDO",
            "DETRACCIÓN",
            "ESTADO DETRACCION",
            "AMORTIZACIONES",
            "SALDO REAL",
            "ESTADO_EMAIL",
            "FECHA_ULTIMO_ENVIO",
            "NOTA",
            "ENVIAR EMAIL",
        ],
    },
}


def _defaults_copy() -> Dict[str, Any]:
    return copy.deepcopy(DEFAULT_SETTINGS)


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _read_legacy_config_file() -> Optional[Dict[str, Any]]:
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception as e:
        print(f"Legacy config read error: {e}")
    return None


def _get_supabase():
    wrapper = SupabaseClient.get_instance()
    if not wrapper.is_available():
        return None
    return wrapper.get_client()


def _load_remote_payload(client) -> Optional[Dict[str, Any]]:
    try:
        response = (
            client.table(CONFIG_TABLE)
            .select("payload")
            .eq("config_key", CONFIG_KEY)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        payload = rows[0].get("payload")
        return payload if isinstance(payload, dict) else None
    except Exception as e:
        print(f"Remote config load error: {e}")
        return None


def _save_remote_payload(client, payload: Dict[str, Any]) -> bool:
    try:
        client.table(CONFIG_TABLE).upsert(
            {"config_key": CONFIG_KEY, "payload": payload},
            on_conflict="config_key",
        ).execute()
        return True
    except Exception as e:
        print(f"Remote config save error: {e}")
        return False


def _apply_env_overrides(settings: Dict[str, Any]) -> Dict[str, Any]:
    env_map = {
        "SMTP_SERVER": ("smtp_config", "server"),
        "SMTP_PORT": ("smtp_config", "port"),
        "SMTP_USER": ("smtp_config", "user"),
        "SMTP_PASSWORD": ("smtp_config", "password"),
        "RESEND_API_KEY": ("smtp_config", "resend_api_key"),
        "SENDGRID_API_KEY": ("smtp_config", "sendgrid_api_key"),
        "SUPABASE_URL": ("supabase_config", "url"),
        "SUPABASE_KEY": ("supabase_config", "key"),
    }
    allow_override_if = {"", "587", "smtp.gmail.com"}

    for env_name, (section, key) in env_map.items():
        env_val = os.getenv(env_name)
        if not env_val:
            continue
        if section not in settings or not isinstance(settings.get(section), dict):
            settings[section] = {}
        current_val = settings[section].get(key, "")
        if not current_val or str(current_val) in allow_override_if:
            settings[section][key] = env_val
    return settings


def load_settings() -> Dict[str, Any]:
    """
    Cloud-first settings load:
    1) Supabase app_config.
    2) One-time bootstrap from legacy config.json when remote row does not exist.
    3) Defaults.
    """
    settings = _defaults_copy()
    client = _get_supabase()

    if client:
        remote_payload = _load_remote_payload(client)
        if remote_payload:
            settings = _deep_merge(settings, remote_payload)
        else:
            legacy_payload = _read_legacy_config_file()
            if legacy_payload:
                settings = _deep_merge(settings, legacy_payload)
                _save_remote_payload(client, settings)
            else:
                _save_remote_payload(client, settings)
    else:
        # Dev/test fallback when Supabase is unavailable.
        legacy_payload = _read_legacy_config_file()
        if legacy_payload:
            settings = _deep_merge(settings, legacy_payload)

    return _apply_env_overrides(settings)


def save_settings(settings: Dict[str, Any]) -> bool:
    """Persist settings in Supabase app_config (cloud-only target)."""
    client = _get_supabase()
    if not client:
        print("Error saving config: Supabase no disponible.")
        return False

    payload = _deep_merge(_defaults_copy(), settings or {})
    return _save_remote_payload(client, payload)
