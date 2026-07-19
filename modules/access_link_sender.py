import json
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.settings_manager import load_settings

_SECRETS_FILE = os.path.join(PROJECT_ROOT, "email_secrets.json")


def _load_secrets_file():
    """Fallback: lee credenciales desde email_secrets.json en la raiz del proyecto."""
    if not os.path.exists(_SECRETS_FILE):
        return {}
    try:
        with open(_SECRETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[WARN] No se pudo leer {_SECRETS_FILE}: {e}")
        return {}


def _load_runtime_email_config():
    settings = load_settings() or {}
    smtp_cfg       = settings.get("smtp_config", {})       if isinstance(settings, dict) else {}
    supervisor_cfg = settings.get("supervisor_config", {}) if isinstance(settings, dict) else {}
    server_notif   = settings.get("server_notification", {}) if isinstance(settings, dict) else {}

    sender_email    = str(smtp_cfg.get("user")     or os.getenv("SMTP_USER", "")).strip()
    sender_password = str(smtp_cfg.get("password") or os.getenv("SMTP_PASSWORD", "")).strip()

    # Prioridad del destinatario: config UI > env var > supervisor_config > sender (fallback)
    recipient_email = (
        str(server_notif.get("recipient_email", "")).strip()
        or os.getenv("ACCESS_LINK_RECIPIENT", "").strip()
        or str(supervisor_cfg.get("email", "")).strip()
        or sender_email
    )

    # Fallback final: si Supabase no tiene credenciales SMTP, leer desde email_secrets.json
    if not sender_email or not sender_password:
        secrets = _load_secrets_file()
        if secrets.get("sender_email") and secrets.get("sender_password"):
            print("[INFO] Usando credenciales SMTP desde email_secrets.json")
            sender_email    = secrets["sender_email"]
            sender_password = secrets["sender_password"]
            recipient_email = (
                str(server_notif.get("recipient_email", "")).strip()
                or os.getenv("ACCESS_LINK_RECIPIENT", "").strip()
                or secrets.get("recipient_email", sender_email)
            )

    return {
        "sender_email":         sender_email,
        "sender_password":      sender_password,
        "recipient_email":      recipient_email,
        "smtp_server":          str(smtp_cfg.get("server") or os.getenv("SMTP_SERVER", "")).strip(),
        "smtp_port":            str(smtp_cfg.get("port")   or os.getenv("SMTP_PORT", "")).strip(),
        "send_enabled":         server_notif.get("send_enabled", True),
        "retry_attempts":       int(server_notif.get("retry_attempts", 3)),
        "retry_delay_seconds":  int(server_notif.get("retry_delay_seconds", 15)),
    }


def _resolve_smtp_target(sender_email, config):
    smtp_server = str(config.get("smtp_server", "")).strip()
    smtp_port   = str(config.get("smtp_port",   "")).strip()

    if smtp_server:
        try:
            return smtp_server, int(smtp_port or "587")
        except ValueError:
            return smtp_server, 587

    if "gmail" in sender_email:
        return "smtp.gmail.com", 587
    if "outlook" in sender_email or "hotmail" in sender_email:
        return "smtp.office365.com", 587
    return "smtp.gmail.com", 587


def _build_html_email(url: str, ambiente: str = "QA") -> str:
    """
    Template HTML correo de inicio — paleta Antay completa con inline CSS.
    Compatible con Gmail, Outlook y Apple Mail.
    """
    timestamp   = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    fecha_larga = datetime.now().strftime("%d de %B de %Y")

    # Paleta Antay (igual que COLORS en utils/ui/styles.py — inline obligatorio en email)
    C_PRIMARY    = "#0D3B66"
    C_ACCENT     = "#0B7285"
    C_BG         = "#F1F5FB"
    C_SURFACE    = "#FFFFFF"
    C_TEXT_MAIN  = "#102A43"
    C_TEXT_MUTED = "#486581"
    C_BORDER     = "#D9E2EC"

    ambiente_upper = ambiente.upper()
    ambiente_label = "Servidor QA" if ambiente_upper == "QA" else "Servidor Producción"
    ambiente_color = C_ACCENT

    return f"""<!DOCTYPE html>
<html lang="es" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>ReporteCobranzas &middot; Acceso Remoto</title>
  <!--[if !mso]><!-->
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
  <!--<![endif]-->
</head>
<body style="margin:0;padding:0;background-color:{C_BG};font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

  <!-- Preheader invisible (vista previa en bandeja de entrada) -->
  <div style="display:none;max-height:0;overflow:hidden;color:{C_BG};">
    El {ambiente_label} est&aacute; activo. Accede ahora con tu enlace personal.&nbsp;&zwnj;&nbsp;
  </div>

  <!-- WRAPPER -->
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
         style="background-color:{C_BG};width:100%;">
    <tr>
      <td align="center" style="padding:40px 16px 48px;">

        <!-- CARD 560px -->
        <table role="presentation" width="560" cellspacing="0" cellpadding="0" border="0"
               style="max-width:560px;width:100%;background:{C_SURFACE};
                      border-radius:4px;
                      box-shadow:0 1px 3px rgba(0,0,0,0.08),0 8px 32px rgba(13,59,102,0.10);">

          <!-- HEADER -->
          <tr>
            <td align="center"
                style="background:{C_PRIMARY};padding:32px 48px 28px;border-radius:4px 4px 0 0;">
              <div style="font-family:Manrope,'Helvetica Neue',Arial,sans-serif;
                          font-size:11px;font-weight:700;letter-spacing:3px;
                          text-transform:uppercase;color:rgba(255,255,255,0.55);margin-bottom:10px;">
                ANTAY F&Aacute;BRICA DE SOFTWARE
              </div>
              <div style="font-family:Manrope,'Helvetica Neue',Arial,sans-serif;
                          font-size:22px;font-weight:800;color:#FFFFFF;
                          letter-spacing:0.5px;line-height:1.2;margin-bottom:12px;">
                ReporteCobranzas
              </div>
              <div style="width:32px;height:2px;background:rgba(255,255,255,0.25);margin:0 auto 14px;"></div>
              <div style="font-family:'Helvetica Neue',Arial,sans-serif;
                          font-size:13px;color:rgba(255,255,255,0.70);font-weight:400;">
                Sistema listo &middot; {fecha_larga}
              </div>
            </td>
          </tr>

          <!-- CUERPO -->
          <tr>
            <td style="padding:36px 48px 0;">
              <p style="margin:0 0 8px;font-family:'Helvetica Neue',Arial,sans-serif;
                         font-size:14px;color:{C_TEXT_MUTED};">Hola,</p>
              <p style="margin:0 0 28px;font-family:'Helvetica Neue',Arial,sans-serif;
                         font-size:16px;color:{C_TEXT_MAIN};line-height:1.6;">
                El <strong style="color:{C_PRIMARY};">{ambiente_label}</strong>
                se ha iniciado correctamente y est&aacute; listo para recibir conexiones.
              </p>

              <!-- INFO CARD -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                     style="border:1px solid {C_BORDER};border-left:4px solid {C_ACCENT};
                            border-radius:3px;margin-bottom:28px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <div style="font-family:'Helvetica Neue',Arial,sans-serif;
                                font-size:10px;font-weight:700;letter-spacing:1.5px;
                                text-transform:uppercase;color:{C_TEXT_MUTED};margin-bottom:14px;">
                      Detalles de acceso
                    </div>

                    <!-- Fila: Ambiente -->
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                           style="margin-bottom:10px;">
                      <tr>
                        <td style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px;
                                   color:{C_TEXT_MUTED};width:110px;vertical-align:top;padding-top:3px;">
                          Ambiente
                        </td>
                        <td>
                          <span style="display:inline-block;background:{ambiente_color};color:#fff;
                                       font-size:10px;font-weight:700;letter-spacing:1px;
                                       text-transform:uppercase;padding:3px 8px;border-radius:2px;">
                            {ambiente_upper}
                          </span>
                        </td>
                      </tr>
                    </table>

                    <!-- Fila: Hora -->
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                           style="margin-bottom:10px;">
                      <tr>
                        <td style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px;
                                   color:{C_TEXT_MUTED};width:110px;">
                          Hora de inicio
                        </td>
                        <td style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:13px;
                                   color:{C_TEXT_MAIN};font-weight:600;">
                          {timestamp}
                        </td>
                      </tr>
                    </table>

                    <!-- Fila: URL -->
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                      <tr>
                        <td style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px;
                                   color:{C_TEXT_MUTED};width:110px;vertical-align:top;padding-top:3px;">
                          URL
                        </td>
                        <td style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:12px;
                                   color:{C_ACCENT};word-break:break-all;">
                          <a href="{url}" style="color:{C_ACCENT};text-decoration:none;">{url}</a>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- BOTÓN CTA -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                     style="margin-bottom:32px;">
                <tr>
                  <td align="center">
                    <a href="{url}"
                       style="display:inline-block;background:{C_ACCENT};color:#FFFFFF;
                              font-family:'Helvetica Neue',Arial,sans-serif;
                              font-size:15px;font-weight:700;letter-spacing:0.3px;
                              text-decoration:none;padding:14px 40px;border-radius:3px;
                              min-width:200px;text-align:center;line-height:1;">
                      Abrir ReporteCobranzas
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- NOTA -->
          <tr>
            <td style="padding:0 48px 32px;">
              <p style="margin:0;font-family:'Helvetica Neue',Arial,sans-serif;
                         font-size:12px;color:{C_TEXT_MUTED};background:{C_BG};
                         padding:12px 16px;border-radius:3px;line-height:1.5;">
                Este enlace es temporal y cambia cada vez que el servidor se reinicia.
                Si no funciona, pide al equipo que reinicie el t&uacute;nel.
              </p>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="border-top:1px solid {C_BORDER};padding:20px 48px;border-radius:0 0 4px 4px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:11px;color:{C_TEXT_MUTED};">
                    ReporteCobranzas v2.2.0 &nbsp;&middot;&nbsp; Antay F&aacute;brica de Software
                  </td>
                  <td align="right" style="font-family:'Helvetica Neue',Arial,sans-serif;
                                           font-size:11px;color:{C_TEXT_MUTED};">
                    Generado autom&aacute;ticamente
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
        <!-- / CARD -->

      </td>
    </tr>
  </table>

</body>
</html>"""


def send_access_link(url: str, ambiente: str = "QA") -> bool:
    config = _load_runtime_email_config()

    if not config.get("send_enabled", True):
        print("[INFO] Notificacion de servidor desactivada en configuracion.")
        return True  # No es error — es intencional

    sender_email    = config.get("sender_email", "")
    sender_password = config.get("sender_password", "")
    recipient_email = config.get("recipient_email", sender_email)

    if not sender_email or not sender_password:
        print("[ERROR] Credenciales SMTP incompletas para notificar link de acceso.")
        return False

    max_attempts = config.get("retry_attempts", 3)
    retry_delay  = config.get("retry_delay_seconds", 15)

    subject   = f"ReporteCobranzas {ambiente} · Servidor activo — {datetime.now().strftime('%d/%m %H:%M')}"
    html_body = _build_html_email(url, ambiente)

    for attempt in range(1, max_attempts + 1):
        try:
            msg = MIMEMultipart("alternative")
            msg["From"]    = f"Antay ReporteCobranzas <{sender_email}>"
            msg["To"]      = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            smtp_server, smtp_port = _resolve_smtp_target(sender_email, config)
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()

            print(f"[OK] Notificacion enviada a {recipient_email} (intento {attempt}/{max_attempts})")
            return True

        except Exception as e:
            print(f"[WARN] Intento {attempt}/{max_attempts} fallido: {e}")
            if attempt < max_attempts:
                print(f"[INFO] Reintentando en {retry_delay}s...")
                time.sleep(retry_delay)

    print("[ERROR] Todos los intentos fallaron. No se pudo notificar.")
    return False
