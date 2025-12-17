import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pandas as pd

# Colores Branding
COLOR_PRIMARY = "#2E86AB"
COLOR_SECONDARY = "#A23B72"
COLOR_BG = "#f4f4f4"
COLOR_TEXT = "#333333"


def generate_premium_email_body_cid(client_name, docs_df, total_s, total_d, branding_config):
    """
    Genera cuerpo HTML asumiendo que el logo se adjunta con Content-ID: <logo_dacta>
    branding_config: {company_name, primary_color, secondary_color, email_template}
    """
    
    # 1. Extraer Branding
    COLOR_PRIMARY = branding_config.get('primary_color', '#2E86AB')
    COLOR_SECONDARY = branding_config.get('secondary_color', '#A23B72')
    BG_COLOR = "#f4f4f4"
    TEXT_COLOR = "#333333"
    
    COMPANY_NAME = branding_config.get('company_name', 'DACTA S.A.C.')
    TEMPLATE = branding_config.get('email_template', {})
    
    INTRO_TEXT = TEMPLATE.get('intro_text', '').replace('{cliente}', client_name).replace('\n', '<br>')
    FOOTER_TEXT = TEMPLATE.get('footer_text', '').replace('\n', '<br>')
    ALERT_TEXT = TEMPLATE.get('alert_text', '')
    table_rows = ""
    for _, row in docs_df.iterrows():
        # Formatear valores para la vista tabla
        # Asumimos que vienen ya formateados o los formateamos aqui
        moneda = row.get('MONEDA', '')
        simbolo = "S/" if str(moneda).upper().startswith('S') else "$"
        
        monto_total = row.get('MONT EMIT', 0)
        saldo = row.get('SALDO REAL', 0)
        detraccion = row.get('DETRACCIÓN', 0)
        
        # Formato numérico visual
        try:
             # Si ya es string (del display), usarlo, sino formatear
             if isinstance(monto_total, str) and ("S/" in monto_total or "$" in monto_total):
                 m_total = monto_total
             else:
                 m_total = f"{simbolo} {float(monto_total):,.2f}"

             if isinstance(saldo, str) and ("S/" in saldo or "$" in saldo):
                 m_saldo = saldo
             else:
                 m_saldo = f"{simbolo} {float(saldo):,.2f}"
                 
             if detraccion > 0:
                 m_detr = f"S/ {float(detraccion):,.2f}"
             else:
                 m_detr = "-"
        except:
            m_total = str(monto_total)
            m_saldo = str(saldo)
            m_detr = "-"

        # Fechas
        try:
            f_emis = pd.to_datetime(row.get('FECH EMIS')).strftime('%d/%m/%Y')
            f_venc = pd.to_datetime(row.get('FECH VENC')).strftime('%d/%m/%Y')
        except:
            f_emis = str(row.get('FECH EMIS'))
            f_venc = str(row.get('FECH VENC'))

        # Estilo Detraccion (Alerta si hay)
        style_det = "color: #d9534f; font-weight: bold;" if detraccion > 0 else "color: #ccc;"

        table_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{row.get('COMPROBANTE', '')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{f_emis}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">{f_venc}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{moneda}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{m_total}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; color: {COLOR_PRIMARY}; font-weight: bold;">{m_saldo}</td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; {style_det} font-size: 0.9em;">{m_detr}</td>
        </tr>
        """

    # 2. HTML Completo
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; background-color: {BG_COLOR}; margin: 0; padding: 0; color: {TEXT_COLOR}; }}
        .container {{ max_width: 700px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .header {{ background: white; padding: 20px; text-align: center; border-bottom: 4px solid {COLOR_PRIMARY}; }}
        .header img {{ max-width: 250px; height: auto; }}
        .content {{ padding: 30px; }}
        .greeting {{ font-size: 18px; margin-bottom: 20px; color: {COLOR_PRIMARY}; }}
        .message {{ line-height: 1.6; margin-bottom: 25px; font-size: 15px; }}
        .alert-box {{ background-color: #fdf2f2; border-left: 4px solid #d9534f; padding: 15px; margin-bottom: 20px; font-size: 14px; color: #a94442; }}
        .table-container {{ overflow-x: auto; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background-color: #f8f9fa; color: #555; font-weight: bold; padding: 12px; text-align: left; border-bottom: 2px solid {COLOR_PRIMARY}; }}
        .totals-box {{ background-color: #eef7fb; padding: 15px; border-radius: 5px; text-align: right; margin-bottom: 20px; }}
        .totals-box strong {{ color: {COLOR_SECONDARY}; font-size: 16px; margin-left: 15px; }}
        .footer {{ background-color: #333; color: #ccc; padding: 20px; text-align: center; font-size: 12px; line-height: 1.5; }}
        .btn {{ display: inline-block; background-color: {COLOR_SECONDARY}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 10px; }}
        .header-msg {{ text-align:center; font-weight:bold; color:{COLOR_PRIMARY}; margin-bottom:20px; }}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                 <img src="cid:logo_dacta" alt="{COMPANY_NAME}">
            </div>
            
            <div class="content">
                <div class="greeting">Estimados <strong>{client_name}</strong>,</div>
                
                <div class="header-msg">
                    Notificación de {COMPANY_NAME}
                </div>

                <div class="message">
                    {INTRO_TEXT}
                </div>

                <div class="alert-box">
                    <strong>Importante:</strong> {ALERT_TEXT}
                </div>
                
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Documento</th>
                                <th>Emisión</th>
                                <th>Vencimiento</th>
                                <th>Mon</th>
                                <th style="text-align: right;">Importe</th>
                                <th style="text-align: right;">Saldo</th>
                                <th style="text-align: right;">Detracción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>

                <div class="totals-box">
                    Total Pendiente: 
                    <strong>{total_s}</strong>
                    <strong>{total_d}</strong>
                </div>

                <div class="message" style="font-size: 13px; color: #666;">
                    {FOOTER_TEXT}
                </div>
            </div>
            
            <div class="footer">
                {COMPANY_NAME} | RUC: {branding_config.get('company_ruc', '')}<br>
                Este es un mensaje automático de notificación de deuda.<br>
                Consultas: {branding_config.get('phone_contact', '')}
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

from email.mime.image import MIMEImage

def send_email_batch(smtp_config, messages, progress_callback=None, logo_path=None):
    """
    Envía lote de correos usando SMTP.
    
    Args:
        smtp_config (dict): {server, port, user, password}
        messages (list): List of dicts {email, subject, html_body, client_name}
        logo_path (str): Ruta local del archivo de imagen para el logo
    """
    stats = {'success': 0, 'failed': 0, 'log': []}
    
    try:
        server = smtplib.SMTP(smtp_config['server'], int(smtp_config['port']))
        server.starttls()
        server.login(smtp_config['user'], smtp_config['password'])
        
        stats['log'].append(f"✅ Conectado a {smtp_config['server']}")

        total = len(messages)
        for i, msg_data in enumerate(messages):
            try:
                # Crear Mensaje
                msg = MIMEMultipart('related') # Cambiado a related para adjuntos inline
                msg['From'] = smtp_config['user']
                msg['To'] = msg_data['email']
                msg['Subject'] = msg_data['subject']
                
                # Cuerpo HTML
                msg_alternative = MIMEMultipart('alternative')
                msg.attach(msg_alternative)
                msg_alternative.attach(MIMEText(msg_data['html_body'], 'html'))
                
                # Adjuntar Logo Inline (si existe)
                if logo_path:
                    try:
                        with open(logo_path, 'rb') as f:
                            logo_data = f.read()
                        image = MIMEImage(logo_data)
                        image.add_header('Content-ID', '<logo_dacta>')
                        image.add_header('Content-Disposition', 'inline', filename='logo.png')
                        msg.attach(image)
                    except Exception as e_img:
                         stats['log'].append(f"⚠️ No se pudo adjuntar logo: {str(e_img)}")

                # Enviar
                server.send_message(msg)
                
                stats['success'] += 1
                stats['log'].append(f"[{i+1}/{total}] Enviado a {msg_data['client_name']} ({msg_data['email']})")
                
                if progress_callback:
                    progress_callback(i+1, total, f"Enviando a {msg_data['client_name']}...")
                
            except Exception as e:
                stats['failed'] += 1
                stats['log'].append(f"[{i+1}/{total}] ❌ Error para {msg_data['client_name']}: {str(e)}")

        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        err_msg = "❌ Error de Autenticación (535). \nSi usas Gmail, NECESITAS activar 'Verificación en 2 pasos' y generar una 'Contraseña de Aplicación'. Tu contraseña normal de Google NO funcionará."
        stats['log'].append(err_msg)
        stats['failed'] = len(messages)
    except Exception as e:
        stats['log'].append(f"❌ Error de Conexión SMTP: {str(e)}")
        stats['failed'] = len(messages)
        
    return stats
