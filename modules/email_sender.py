import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
try:
    from .email_config import load_email_config
except ImportError:
    from email_config import load_email_config

def send_access_link(url):
    config = load_email_config()
    if not config:
        print("[WARN] Sin config de email. Ejecuta 8_CONFIGURAR_EMAIL.bat")
        return False

    sender_email = config.get("sender_email")
    sender_password = config.get("sender_password")
    recipient_email = config.get("recipient_email", sender_email)

    if not sender_email or not sender_password:
        print("[ERROR] Credenciales de email incompletas.")
        return False

    subject = f"Acceso Cobranzas Antay - {datetime.now().strftime('%d/%m %H:%M')}"

    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
      <div style="background:#f8f9fa;padding:20px;border-radius:10px;border:1px solid #ddd;">
        <h2 style="color:#0d6efd;">Reporte Cobranzas Antay - Acceso Remoto</h2>
        <p>El sistema se ha iniciado correctamente en el servidor QA.</p>
        <div style="background:#fff;padding:15px;border-left:5px solid #198754;margin:20px 0;">
          <p style="margin:0;font-size:14px;color:#666;">Tu Link de Acceso:</p>
          <p style="margin:5px 0 0 0;font-size:18px;font-weight:bold;">
            <a href="{url}" style="color:#198754;text-decoration:none;">{url}</a>
          </p>
        </div>
        <p style="font-size:12px;color:#999;">
          Enlace temporal — cambia si el servidor se reinicia.<br>
          Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
      </div>
    </body></html>
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Antay Bot <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))

        if "gmail" in sender_email:
            smtp_server, smtp_port = "smtp.gmail.com", 587
        elif "outlook" in sender_email or "hotmail" in sender_email:
            smtp_server, smtp_port = "smtp.office365.com", 587
        else:
            smtp_server, smtp_port = "smtp.gmail.com", 587

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"[OK] Correo enviado a {recipient_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Enviando correo: {e}")
        return False
