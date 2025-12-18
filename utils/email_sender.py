import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from email.utils import make_msgid, formatdate
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
    html_rows = ""
    for _, row in docs_df.iterrows():
        # Formatear valores
        moneda = row.get('MONEDA', '')
        simbolo = "S/" if str(moneda).upper().startswith('S') else "$"
        
        monto_total = row.get('MONT EMIT', 0)
        saldo = row.get('SALDO REAL', 0)
        detraccion = row.get('DETRACCIÓN', 0)
        
        # Lógica Estado Detracción
        estado_dt_raw = str(row.get('ESTADO DETRACCION', ''))
        if estado_dt_raw.upper() == "NO APLICA":
            estado_dt_val = "No aplica"
        elif estado_dt_raw.upper() == "PENDIENTE":
            estado_dt_val = "Pendiente"
        else:
            estado_dt_val = "Cobrado"
        
        # Formato numérico visual
        try:
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

        # Estilo Detraccion
        style_det = "color: #d9534f; font-weight: bold;" if detraccion > 0 else "color: #ccc;"
        if estado_dt_val == "Cobrado":
             style_det = "color: #28a745; font-weight: bold;" # Verde si está cobrado

        html_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <span class="mobile-label">Documento:</span>
                {row.get('COMPROBANTE', '')}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <span class="mobile-label">Emisión:</span>
                {f_emis}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <span class="mobile-label">Vencimiento:</span>
                {f_venc}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">
                <span class="mobile-label">Importe:</span>
                {m_total}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; color: {COLOR_PRIMARY}; font-weight: bold;">
                <span class="mobile-label">Saldo:</span>
                {m_saldo}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">
                 <span class="mobile-label">Detracción:</span>
                 {m_detr}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center; {style_det} font-size: 0.9em;">
                <span class="mobile-label">Estado:</span>
                {estado_dt_val}
            </td>
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
        
        /* Default: Hide mobile labels on desktop */
        .mobile-label {{ display: none; }}

        /* Mobile Responsiveness: Stacked Cards */
        @media only screen and (max-width: 600px) {{
            /* Block layout for structural elements */
            table, thead, tbody, th, td, tr {{ 
                display: block; 
                width: 100% !important; /* Force full width */
                box-sizing: border-box;
            }}
            
            /* Hide Desktop Headers - Aggressive approach for email clients */
            thead, thead tr, th {{ 
                display: none !important;
                width: 0 !important;
                height: 0 !important;
                opacity: 0 !important;
                overflow: hidden !important;
                visibility: hidden !important;
                mso-hide: all !important; /* Outlook specific */
            }}
            
            /* Card Style for Rows */
            tr {{ 
                border: 1px solid #e0e0e0; 
                margin-bottom: 15px; 
                border-radius: 8px; 
                background-color: #ffffff;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                overflow: hidden;
            }}
            
            /* Stacked Cells */
            td {{ 
                border: none;
                border-bottom: 1px solid #f0f0f0; 
                position: relative;
                padding: 12px 15px !important; 
                text-align: right !important; /* Values align right */
                white-space: normal;
                display: block; /* Ensure clean block model */
                min-height: 25px; /* Visual height stability */
            }}
            
            td:last-child {{
                border-bottom: none;
            }}
            
            /* Reveal Mobile Labels */
            .mobile-label {{ 
                display: inline-block;
                float: left;
                width: 40%;
                font-weight: bold;
                text-align: left;
                color: {COLOR_SECONDARY};
                white-space: nowrap;
            }}
        }}
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
                    Estado de Cuenta
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
                            <tr class="header-row">
                                <th>Documento</th>
                                <th>Emisión</th>
                                <th>Vencimiento</th>
                                <th style="text-align: right;">Importe</th>
                                <th style="text-align: right;">Saldo</th>
                                <th style="text-align: right;">Detracción</th>
                                <th style="text-align: center;">Estado Detr.</th>
                            </tr>
                        </thead>
                        <tbody>
                            {html_rows}
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

def generate_plain_text_body(client_name, docs_df, total_s, total_d, branding_config):
    """
    Genera versión texto plano para reducir puntaje de spam.
    """
    company_name = branding_config.get('company_name', 'DACTA S.A.C.')
    intro = branding_config.get('email_template', {}).get('intro_text', '').replace('{cliente}', client_name)
    footer = branding_config.get('email_template', {}).get('footer_text', '')
    
    text = f"Estimados {client_name},\n\n"
    text += f"Notificación de {company_name}\n\n"
    text += f"{intro}\n\n"
    text += f"{'DOC':<15} | {'VENC':<10} | {'IMPORTE':>13} | {'SALDO':>13} | {'DETRAC.':>10} | {'ESTADO':<10}\n"
    text += "-" * 95 + "\n"
    
    for _, row in docs_df.iterrows():
        doc = row.get('COMPROBANTE', '')
        venc = str(row.get('FECH VENC', ''))
        # Limpieza de fecha: 00:00:00
        if " " in venc:
            venc = venc.split(" ")[0]
            
        mon = row.get('MONEDA', '')
        sim = "S/" if str(mon).upper().startswith('S') else "$"
        
        # Lógica Estado Detracción
        estado_dt_raw = str(row.get('ESTADO DETRACCION', ''))
        if estado_dt_raw.upper() == "NO APLICA":
            estado_dt_val = "No aplica"
        elif estado_dt_raw.upper() == "PENDIENTE":
            estado_dt_val = "Pendiente"
        else:
            estado_dt_val = "Cobrado"
        
        try:
            imp = float(row.get('MONT EMIT', 0))
            sal = float(row.get('SALDO REAL', 0))
            det = float(row.get('DETRACCIÓN', 0))
            
            str_det = f"S/ {det:,.2f}" if det > 0 else "-"
            
            line = f"{doc:<15} | {venc:<10} | {sim} {imp:>9,.2f} | {sim} {sal:>9,.2f} | {str_det:>10} | {estado_dt_val:<10}"
        except:
             line = f"{doc:<15} | {venc:<10} | {row.get('MONT EMIT', ''):>13} | {row.get('SALDO REAL', ''):>13} | {'-':>10} | {estado_dt_val:<10}"
            
        text += line + "\n"
        
    text += "-" * 95 + "\n"
    text += f"TOTAL PENDIENTE: {total_s}   {total_d}\n\n"
    text += f"{footer}\n\n"
    text += "Nota: Este correo contiene elementos gráficos. Si no los ve, habilite el contenido HTML.\n"
    
    return text

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
                msg = MIMEMultipart('related') 
                msg['From'] = smtp_config['user']
                msg['To'] = msg_data['email']
                msg['Subject'] = msg_data['subject']
                msg['Reply-To'] = smtp_config['user']
                msg['Date'] = formatdate(localtime=True)
                msg['Message-ID'] = make_msgid(domain=smtp_config['user'].split('@')[-1])
                
                # Estructura MIME:
                # related
                #   |-- alternative
                #        |-- plain text
                #        |-- html
                #   |-- logo image (inline)

                msg_alternative = MIMEMultipart('alternative')
                msg.attach(msg_alternative)
                
                # 1. Plain Text (Primero, para clientes viejos/filtros)
                # Si no se pasó texto plano, generar uno básico genérico, pero idealmente debe pasarse
                plain_text = msg_data.get('plain_body', 'Por favor habilite HTML para ver este mensaje.')
                msg_alternative.attach(MIMEText(plain_text, 'plain'))
                
                # 2. HTML (Segundo, preferido)
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
