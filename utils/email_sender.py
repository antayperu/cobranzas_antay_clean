import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from email.utils import make_msgid, formatdate
import pandas as pd
import uuid
import utils.helpers as helpers
import hashlib
import time
import threading
import os
import sqlite3
import traceback

# Colores Branding
COLOR_PRIMARY = "#2E86AB"
COLOR_SECONDARY = "#A23B72"
COLOR_BG = "#f4f4f4"
COLOR_TEXT = "#333333"


def generate_premium_email_body_cid(client_name, docs_df, total_s, total_d, branding_config):
    """
    Genera cuerpo HTML asumiendo que el logo se adjunta con Content-ID: <logo_dacta>
    branding_config: {company_name, primary_color, secondary_color, email_template, ...}
    Refinado v3 (RC-UX-003): "Corporate Sheet" Look (700px, Shadow, Formal Header).
    """
    
    # 1. Branding y Config
    COLOR_PRIMARY = branding_config.get('primary_color', '#2E86AB')
    COLOR_SECONDARY = branding_config.get('secondary_color', '#A23B72')
    BG_COLOR = "#F5F7FB" # RC-UX-003: Fondo gris azulado corporativo
    TEXT_COLOR = "#333333"
    COMPANY_NAME = branding_config.get('company_name', 'DACTA S.A.C.')
    TEMPLATE = branding_config.get('email_template', {})
    
    # --- PROCESAMIENTO DE TOTALES Y KPIs ---
    sum_detr = 0.0 # Define base scope
    try:
        mask_soles = docs_df['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
        
        # Dataframes por moneda
        df_sol = docs_df[mask_soles]
        df_dol = docs_df[~mask_soles]
        
        # 1. Deuda DACTA Soles
        sum_s = df_sol['SALDO REAL'].sum()
        count_s = len(df_sol)
        kpi_dacta_s = f"S/ {sum_s:,.2f} ({count_s:02d} documentos)" if (sum_s > 0 or count_s > 0) else "S/ 0.00 (00 documentos)"

        # 2. Deuda DACTA Dolares
        sum_d = df_dol['SALDO REAL'].sum()
        count_d = len(df_dol)
        kpi_dacta_d = f"US$ {sum_d:,.2f} ({count_d:02d} documentos)" if (sum_d > 0 or count_d > 0) else "US$ 0.00 (00 documentos)"
        
        # 3. Detracción SUNAT (Solo documentos afectos)
        df_detr = docs_df[docs_df['DETRACCIÓN'] > 0]
        
        # Normalizar estado
        def is_pending(val):
            v = str(val).upper().strip()
            return v == "PENDIENTE"
            
        mask_pending_detr = df_detr['ESTADO DETRACCION'].apply(is_pending)
        df_detr_pending = df_detr[mask_pending_detr]
        
        sum_detr = df_detr_pending['DETRACCIÓN'].sum()
        count_detr = len(df_detr_pending)
        
        # RC-UX-003: Always display Sunat line, even if 0, for consistency in "Corporate Summary"
        kpi_sunat = f"S/ {sum_detr:,.2f} ({count_detr:02d} documentos afectos)" 

        # Construir HTML de Totales (Tabla Resumen Formal)
        # RC-UX-003: Require 3 explicit lines/rows in a summary box, not just bullets.
        summary_rows_html = f"""
            <tr>
                <td style="padding: 6px 0; color: #555;">Deuda Total <strong>Soles</strong>:</td>
                <td style="padding: 6px 0; text-align: right; font-weight: bold; color: {COLOR_PRIMARY};">{kpi_dacta_s}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #555;">Deuda Total <strong>Dólares</strong>:</td>
                <td style="padding: 6px 0; text-align: right; font-weight: bold; color: {COLOR_PRIMARY};">{kpi_dacta_d}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #555;">Detracciones SUNAT Pendientes:</td>
                <td style="padding: 6px 0; text-align: right; font-weight: bold; color: #333;">{kpi_sunat}</td>
            </tr>
        """

    except Exception as e:
        summary_rows_html = "<tr><td colspan='2'>Error calculando totales.</td></tr>"

    # --- 1. CONFIGURABLE TEXTS & SAFETY (RC-UX-004) ---
    email_config = branding_config.get('email_template', {})
    
    # Helper for safe HTML rendering
    def nl2br_safe(text_input):
        if not text_input:
            return ""
        # Escape HTML special characters first to prevent injection
        safe_text = html.escape(str(text_input))
        # Convert newlines to <br> for email rendering
        return safe_text.replace('\n', '<br>')

    # A. Intro Text
    raw_intro = email_config.get('intro_text', '').strip()
    if not raw_intro:
        # Default with {cliente} placeholder support
        raw_intro = "Estimado cliente {cliente},\nAdjuntamos el detalle actualizado de sus documentos pendientes de pago. Agradeceremos verificar la siguiente información:"
    
    # Process Intro: Safe render + Client Name injection
    safe_cliente = html.escape(str(client_name))
    intro_html = nl2br_safe(raw_intro).replace("{cliente}", safe_cliente)

    # B. Footer Text (RC-BUG-018: Exclusive Logic)
    # If custom text is present, we use IT ALONE (replacing the default signature).
    # If custom text is empty, we use the DEFAULT SIGNATURE.
    
    raw_footer = email_config.get('footer_text', '').strip()
    
    if raw_footer:
        # User defined footer -> Use it exclusively
        # We wrap it in a div for spacing if needed, but the content is just the text
        footer_block_html = nl2br_safe(raw_footer)
    else:
        # Default Signature
        ruc = branding_config.get('company_ruc', '20601995817')
        footer_block_html = f"<strong>{COMPANY_NAME}</strong> &bull; RUC: {ruc}<br>Área de Cobranzas y Facturación"

    # C. Detraccion Block (Conditional)
    detraccion_block_html = ""
    if sum_detr > 0:
        raw_alert = email_config.get('alert_text', '').strip()
        if raw_alert:
            alert_content_html = nl2br_safe(raw_alert)
            # Styling matches the existing warning style but wrapped clean
            detraccion_block_html = f"""
            <div style="background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 15px; margin: 20px 0; border-radius: 4px; font-size: 14px;">
                {alert_content_html}
            </div>
            """

    # Header Compacto
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    # RC-UX-007: Dynamic Logo Logic
    # Check if logo exists in config (path or bytes)
    has_logo = bool(branding_config.get('logo_path') or branding_config.get('logo_bytes'))
    
    if has_logo:
        # Render Corporate Logo Block (Enterprise Standard: 360px width)
        # RC-BUG-LOGO: Use specific inline CSS for Gmail compatibility
        logo_block_html = f"""
        <tr>
            <td align="center" style="padding: 25px 40px 10px 40px; border-bottom: 0px;">
                <img src="cid:logo_dacta" width="360" alt="{COMPANY_NAME}" 
                     style="display:block; margin: 0 auto 10px auto; width:360px; max-width:360px; height:auto; max-height:110px; border:0; outline:none; text-decoration:none;">
            </td>
        </tr>
        """
        # Reduced top padding for title since logo takes space
        title_padding_top = "0px"
    else:
        # No Logo -> Empty Block
        logo_block_html = ""
        # Increase top padding to center title nicely in the white box
        title_padding_top = "30px"

    # --- GENERACIÓN DE FILAS (PC y MÓVIL) ---
    table_rows = ""
    mobile_cards = ""
    
    for idx, row in docs_df.iterrows(): # idx needed for zebra stripe simulation if not using css nth-child
        # Datos
        doc = row.get('COMPROBANTE', '')
        
        try:
            f_emis = pd.to_datetime(row.get('FECH EMIS')).strftime('%d/%m/%Y')
            f_venc = pd.to_datetime(row.get('FECH VENC')).strftime('%d/%m/%Y')
        except:
            f_emis, f_venc = str(row.get('FECH EMIS')), str(row.get('FECH VENC'))

        moneda = row.get('MONEDA', '')
        sim = "S/" if str(moneda).upper().startswith('S') else "US$"
        
        try:
            imp_val = float(row.get('MONT EMIT', 0))
            sal_val = float(row.get('SALDO REAL', 0)) # Saldo a DACTA
            det_val = float(row.get('DETRACCIÓN', 0)) # Detracción SUNAT
        except:
            imp_val, sal_val, det_val = 0.0, 0.0, 0.0

        # Formatos Visuales
        m_imp = f"{sim} {imp_val:,.2f}"
        m_sal = f"{sim} {sal_val:,.2f}"
        
        # Regla: Detracciones SIEMPRE S/
        if det_val > 0:
            m_det = f"S/ {det_val:,.2f}"
            style_det_cell = "" # Standard text
        else:
            m_det = "-"
            style_det_cell = "color: #ccc;"

        # Badge Logic for Status
        estado_dt = str(row.get('ESTADO DETRACCION', '')).strip().upper()
        if estado_dt == "PENDIENTE":
            # Badge Amber
            badge_html = f'<span style="background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">Pendiente</span>'
            mobile_st_text = "Pendiente"
            mobile_style_st = "color: #d9534f; font-weight: bold;"
        elif estado_dt == "NO APLICA":
            # Badge Gray
            badge_html = f'<span style="background-color: #e2e3e5; color: #383d41; padding: 4px 8px; border-radius: 4px; font-size: 11px;">No aplica</span>'
            mobile_st_text = "No aplica"
            mobile_style_st = "color: #999;"
        else:
            # Badge Green
            badge_html = f'<span style="background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">Cobrado</span>'
            mobile_st_text = "Cobrado"
            mobile_style_st = "color: #28a745;"
             
        # Regla visual: Si Saldo Dacta es 0 pero Detraccion Pendiente -> Alerta visual explícita
        # Zebra Striping Logic for Row BG
        # Use simple toggle based on idx if needed, or CSS. CSS nth-child is better but inline support varies.
        # We will use explicit background color for even rows for better email support.
        # But for "Sheet" look, we want white bg mostly. We'll rely on TR border.
        # user requested Zebra: row_bg = #f8f9fa if even.
        if idx % 2 == 0:
            row_bg_pc = "#ffffff"
        else:
            row_bg_pc = "#f9fafb"

        m_sal_display = m_sal
        
        # "Saldo a DACTA: 0.00 — Solo falta detracción SUNAT" logic
        if sal_val <= 0.1 and det_val > 0 and estado_dt == "PENDIENTE":
            m_sal_display = "<span style='color:#999;'>0.00</span><br><span style='font-size:10px; color:#d9534f'>(Solo Detracción)</span>"
            # Highlight this row specially? 
            row_bg_pc = "#fff8f8" 

        # --- A) HTML TABLE ROW (PC) ---
        table_rows += f"""
        <tr style="background-color: {row_bg_pc};">
            <td style="padding: 12px 15px; border-bottom: 1px solid #eee; font-size: 13px;">{doc}</td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #eee; font-size: 13px;">{f_emis}</td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #eee; font-size: 13px;">{f_venc}</td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #eee; text-align: right; font-size: 13px;">{m_imp}</td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold; color: {COLOR_PRIMARY}; font-size: 13px;">{m_sal_display}</td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #eee; text-align: right; font-size: 13px; {style_det_cell}">{m_det}</td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #eee; text-align: center;">{badge_html}</td>
        </tr>
        """
        
        # --- B) HTML CARD (MOBILE) ---
        # Card Layout unchanged as per Requirement
        mobile_cards += f"""
        <div class="mobile-card" style="display:none; background:#fff; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 12px; padding: 15px;">
            <div style="border-bottom: 1px solid #f0f0f0; padding-bottom: 8px; margin-bottom: 8px; font-weight: bold; color: #333;">
                <span style="color:{COLOR_PRIMARY}">{doc}</span> 
                <span style="float:right; font-weight:normal; font-size:12px; color:#666;">Vence: {f_venc}</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 13px;">
                <span style="color:#666;">Importe:</span> <span>{m_imp}</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-weight: bold; color: {COLOR_PRIMARY};">
                <span>Saldo a DACTA:</span> <span>{m_sal_display}</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #eee; font-size: 13px;">
                 <span style="color:#666;">Detracción SUNAT (S/):</span> 
                 <span style="{mobile_style_st}">{m_det} <small>({mobile_st_text})</small></span>
            </div>
        </div>
        """


    # 2. CUERPO HTML FINAL REFINADO
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Base Reset */
        body {{ font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: {BG_COLOR}; margin: 0; padding: 20px 0; color: {TEXT_COLOR}; -webkit-font-smoothing: antialiased; }}
        
        /* Helpers */
        .desktop-only {{ display: table; }}
        .mobile-only {{ display: none; }}
        
        /* Body Content */
        .content-box {{ padding: 35px 40px; }}
        
        /* Summary Box */
        .summary-box {{ background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 20px; margin: 25px 0; }}
        
        /* Data Table */
        table.data-table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 10px; }}
        table.data-table th {{ 
            background-color: #f1f5f9; 
            color: #475569; 
            font-weight: 600; 
            text-transform: uppercase; 
            font-size: 11px; 
            letter-spacing: 0.05em; 
            padding: 12px 15px; 
            text-align: left; 
            border-bottom: 2px solid #cbd5e1;
        }}
        
        /* Accounts Section */
        .accounts-grid {{ display: table; width: 100%; margin-top: 35px; border-top: 2px solid #f1f5f9; padding-top: 20px; }}
        .account-col {{ display: table-cell; vertical-align: top; width: 48%; padding-right: 2%; }}
        .account-title {{ font-size: 12px; font-weight: 700; color: {COLOR_PRIMARY}; text-transform: uppercase; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; }}
        .account-item {{ font-size: 12px; color: #4b5563; margin-bottom: 6px; line-height: 1.5; }}
        .bank-label {{ font-weight: 600; color: #111827; }}
        
        /* Footer */
        .footer {{ text-align: center; color: #9ca3af; font-size: 11px; padding: 20px; border-top: 1px solid #f3f4f6; background-color: #fafafa; }}

        /* MEDIA QUERIES (MOBILE) */
        @media only screen and (max-width: 600px) {{
            /* Reset body padding for mobile */
            body {{ padding: 0; background-color: #f4f4f4; }}
            
            /* Fluid Container logic handled by table width 100% on small screens naturally or max-width override */
            .main-table-wrapper {{ width: 100% !important; }}
            
            /* Adjust Content Padding */
            .content-box {{ padding: 20px 15px !important; }}
            
            /* Toggle Views */
            .desktop-only {{ display: none !important; }}
            .mobile-only {{ display: block !important; }}
            .mobile-card {{ display: block !important; }}
            
            /* Logo resizing */
            .logo-img {{ height: 40px !important; }}
            
            /* Force table layout tools to behave like blocks */
            .accounts-grid, .account-col {{ display: block; width: 100%; padding: 0; margin-bottom: 20px; }}
        }}
    </style>
    </head>
    <body style="margin:0; padding:20px 0; background-color:{BG_COLOR};">
    
        <!-- MAIN WRAPPER TABLE (GMAIL SAFE) -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%; border-collapse:collapse; background-color:{BG_COLOR};">
          <tr>
            <td align="center" style="padding:0;">
              
              <!-- CENTERED CONTAINER TABLE (700px) -->
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" class="main-table-wrapper"
                     width="700" style="width:700px; max-width:700px; background-color:#FFFFFF; border:1px solid #dce0e6; border-radius:0px; border-collapse:separate; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                
                <!-- TOP BAR (BLUE ACCENT) -->
                <tr>
                  <td bgcolor="{COLOR_PRIMARY}" height="6" style="height:6px; line-height:6px; font-size:6px; background-color:{COLOR_PRIMARY};">&nbsp;</td>
                </tr>

                <!-- HEADER CONTENT (RC-UX-006/007: Dynamic Stacked) -->
                <tr>
                  <td style="padding: 0; border-bottom: 1px solid #eaeaea;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
                      
                      {logo_block_html}
                      
                      <tr>
                        <!-- TITLE & DATE (CENTERED) -->
                        <td align="center" valign="middle" style="padding: {title_padding_top} 40px 25px 40px; font-family:'Segoe UI', Arial, sans-serif; color:{TEXT_COLOR};">
                          <div style="font-size:24px; line-height:30px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase; color:#1f2937;">
                            ESTADO DE CUENTA
                          </div>
                          <div style="font-size:14px; line-height:18px; color:#9ca3af; margin-top:4px; font-weight:500;">
                            Al {current_date}
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                
                <!-- BODY CONTENT ROW -->
                <tr>
                  <td style="padding:0;">
            
            <div class="content-box">
                <div style="font-size: 15px; margin-bottom: 25px; line-height: 1.6; color: #4b5563;">
                    {intro_html}
                </div>
                
                <!-- SUMMARY BOX -->
                <div class="summary-box">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-size: 14px;">
                        {summary_rows_html}
                    </table>
                </div>

                <!-- DETRACCION BLOCK (CONDITIONAL) -->
                {detraccion_block_html}

                <!-- TABLE SECTION -->
                <div style="margin-top: 30px;">
                    <div style="font-size: 13px; font-weight: 700; color: #4b5563; text-transform: uppercase; margin-bottom: 10px;">Detalle de Documentos</div>
                    
                    <!-- PC VIEW -->
                    <table class="data-table desktop-only">
                        <thead>
                            <tr>
                                <th>Documento</th>
                                <th>Emisión</th>
                                <th>Vencimiento</th>
                                <th style="text-align: right;">Importe</th>
                                <th style="text-align: right;">Saldo a DACTA</th>
                                <th style="text-align: right;">Detracción (S/)</th>
                                <th style="text-align: center;">Estado Detr.</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                    
                    <!-- MOBILE VIEW -->
                    <div class="mobile-only">
                        {mobile_cards}
                    </div>
                </div>
                
                <div style="font-size: 13px; color: #64748b; margin-top: 25px; font-style: italic;">
                    Nota: Los montos de detracción deben depositarse exclusivamente al <strong>Banco de la Nación</strong>, Cuenta N°: <strong>00-005-034272</strong> (Siempre en Soles).
                </div>

                <!-- ACCOUNTS FOOTER -->
                <div class="accounts-grid">
                    <div class="account-col">
                        <div class="account-title">Cuentas en Soles (S/)</div>
                        <div class="account-item"><span class="bank-label">BCP:</span> 1931472448010<br>CCI: 00219300147244801019</div>
                        <div class="account-item"><span class="bank-label">BBVA:</span> 001103400200230077<br>CCI: 01134000020023007776</div>
                    </div>
                    <div class="account-col">
                        <div class="account-title">Cuentas en Dólares (US$)</div>
                        <div class="account-item"><span class="bank-label">BCP:</span> 1912078776145<br>CCI: 00219100207877614559</div>
                    </div>
                </div>
            </div>
            
            <!-- FOOTER BLOCK (RC-BUG-018: Inside 700px Container) -->
            <tr>
              <td style="padding: 20px 40px; border-top: 1px solid #f3f4f6; background-color: #fafafa; text-align: center; color: #9ca3af; font-size: 11px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;">
                {footer_block_html}
              </td>
            </tr>

        </table>
        </td>
      </tr>
    </table>
    
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

def send_email_batch(smtp_config, messages, progress_callback=None, logo_path=None, force_resend=False, internal_copies_config=None, qa_mode_active=False):
    """
    Envía lote de correos con reporte de progreso y bloqueo TTL por negocio.
    force_resend: Si True, ignora el bloqueo TTL (Reason: USER_RESEND).
    internal_copies_config: Dict opcional {'cc_list': [...], 'bcc_list': [...]}
    qa_mode_active: Si True, aplica reglas estrictas de supervisión (solo si supervisor en recipient list).
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    
    # RC-UX-002: Return structured detail list for UI
    stats = {'success': 0, 'failed': 0, 'blocked': 0, 'log': [], 'details': []}
    
    # Pre-flight check
    if not messages:
        return stats
    
    # Run ID único para este lote
    run_id = str(uuid.uuid4())[:8]
    
    # Deduplicación en memoria del batch actual (evitar enviar 2 veces al mismo en el mismo loop)
    # RC-BUG-016: Usar Notification Key en lugar de solo email
    seen_keys = set()
    unique_messages = []
    duplicates_count = 0
    
    for m in messages:
        # --- RC-FIX-QA-TYPE: Robust List Handling ---
        raw_email_input = m.get('email', '')
        # Normalize list/str to list[str]
        recips_norm = helpers.normalize_emails(raw_email_input)
        
        # Take primary for Logic/Ledger (or 'unknown')
        primary_email = recips_norm[0] if recips_norm else ''
        email_clean = primary_email.lower()
        
        if not email_clean:
            continue
            
        # Unicidad: Notification Key (Ideal) -> Email (Fallback)
        uniq_key = m.get('notification_key') or email_clean
        
        if uniq_key in seen_keys:
            duplicates_count += 1
            stats['log'].append(f"⚠️ [RunID:{run_id}] Duplicado interno omitido: {uniq_key}")
            continue
        seen_keys.add(uniq_key)
        unique_messages.append(m)
        
    # --- RC-BUG-014 & 015: TTL Ledger & Audit ---
    
    # 1. Forensic Caller Dump
    stack_dump = "".join(traceback.format_stack())
    print(f"DEBUG_FORENSIC: [RunID:{run_id}] CALLER STACK:\n{stack_dump}")
    stats['log'].append(f"🔍 [RunID:{run_id}] Stack Trace recorded.")

    # 2. Initialize Ledger (Schema v15: Dual Table)
    TTL_MINUTES = 10
    
    try:
        conn = sqlite3.connect('email_ledger.db')
        c = conn.cursor()
        
        # State Table (Anti-Duplicado)
        c.execute('''CREATE TABLE IF NOT EXISTS ledger_last_send
                     (ledger_key TEXT PRIMARY KEY, last_sent_at TIMESTAMP, last_msg_id TEXT, send_count INTEGER)''')
        
        # History Table (Auditoría)
        # RC-FEAT-011: Added supervisor_copied column logic could be in 'status' or metadata. 
        # For now we keep schema compatible and log 'SUPERVISOR_COPY' in log or new column if we wanted migration.
        # We will log it in 'reason' or append to status if needed, but lets keep it simple to avoid schema migration risks on hotfix.
        c.execute('''CREATE TABLE IF NOT EXISTS send_attempts
                     (id TEXT PRIMARY KEY, ledger_key TEXT, recipient TEXT, status TEXT, reason TEXT, timestamp TIMESTAMP, run_id TEXT)''')
        conn.commit()
    except Exception as e_db:
        stats['log'].append(f"⚠️ [RunID:{run_id}] Error initializing DB: {e_db}")
        return stats # Abort safety

    try:
        server = smtplib.SMTP(smtp_config['server'], int(smtp_config['port']))
        server.starttls()
        server.login(smtp_config['user'], smtp_config['password'])
        
        stats['log'].append(f"✅ [RunID:{run_id}] Conectado a {smtp_config['server']}")

        total = len(unique_messages)
        send_call_index = 0
        
        for i, msg_data in enumerate(unique_messages):
            send_call_index += 1
            
            client_name = msg_data.get('client_name', 'Unknown')
            client_name = msg_data.get('client_name', 'Unknown')
            
            # --- RC-FIX-QA-TYPE: Robust Ledger Recipient Extraction ---
            # msg_data['email'] can be list in QA mode.
            _recips = helpers.normalize_emails(msg_data['email'])
            recipient_ledger = _recips[0].lower() if _recips else 'unknown_recipient'
            
            # --- Business Key Calculation ---
            if 'notification_key' in msg_data:
                notif_key = msg_data['notification_key']
                ledger_src = f"{recipient_ledger}|{notif_key}"
            else:
                payload_str_ledger = str(msg_data['html_body']) + str(msg_data['subject'])
                payload_hash_ledger = hashlib.md5(payload_str_ledger.encode()).hexdigest()
                notif_key = f"LEGACY_HASH_{payload_hash_ledger}"
                ledger_src = f"{recipient_ledger}|{notif_key}"
            
            ledger_key = hashlib.sha256(ledger_src.encode()).hexdigest()
            now_ts = datetime.utcnow()
            
            # 3. Check TTL (Anti-Duplicado Accidental)
            if not force_resend:
                try:
                    c.execute("SELECT last_sent_at FROM ledger_last_send WHERE ledger_key=?", (ledger_key,))
                    existing = c.fetchone()
                    
                    if existing:
                        last_sent_str = existing[0]
                        # Python sqlite adapter might return str or datetime depending on detection
                        try:
                            last_sent = datetime.strptime(last_sent_str, "%Y-%m-%d %H:%M:%S.%f")
                        except:
                            try:
                                last_sent = datetime.strptime(last_sent_str, "%Y-%m-%d %H:%M:%S")
                            except:
                                last_sent = datetime.min
                                
                        elapsed = (now_ts - last_sent).total_seconds() / 60.0
                        
                        if elapsed < TTL_MINUTES:
                            msg_dup = f"🔒 [RunID:{run_id}] BLOCKED by TTL ({elapsed:.1f}m < {TTL_MINUTES}m). Recipient:{recipient_ledger}"
                            stats['log'].append(msg_dup)
                            print(f"DEBUG_FORENSIC: {msg_dup} | Key={ledger_key}")
                            
                            # Audit Block
                            att_id = str(uuid.uuid4())
                            c.execute("INSERT INTO send_attempts VALUES(?,?,?,?,?,?,?)", 
                                      (att_id, ledger_key, recipient_ledger, 'BLOCKED', 'TTL_BLOCK', now_ts, run_id))
                            conn.commit()
                            
                            duplicates_count += 1
                            stats['blocked'] += 1
                            # Detail Entry
                            stats['details'].append({
                                'Cliente': client_name,
                                'Email': recipient_ledger,
                                'Estado': '🔒 Bloqueado',
                                'Detalle': f"TTL (<{TTL_MINUTES}min). Use 'Reenviar' para forzar.",
                                'RunID': run_id
                            })
                            continue # SKIP SEND
                except Exception as e_chk:
                    stats['log'].append(f"⚠️ [RunID:{run_id}] Ledger Check Error: {e_chk}")

            try:
                # Crear Mensaje
                msg = MIMEMultipart('related') 
                msg['From'] = smtp_config['user']
                
                # --- RC-FIX-QA-TYPE: Ensure 'To' Header is String ---
                # We normalize again (safe) to be sure, or rely on loop var if passed (refactor loop?)
                # msg_data uses 'email' key which might be list.
                all_recipients_clean = helpers.normalize_emails(msg_data['email'])
                
                msg['To'] = ", ".join(all_recipients_clean)
                msg['Subject'] = msg_data['subject']
                msg['Reply-To'] = smtp_config['user']
                msg['Date'] = formatdate(localtime=True)
                
                # Message-ID Forense
                msg_id = make_msgid(domain=smtp_config['user'].split('@')[-1])
                msg['Message-ID'] = msg_id
                
                # Estructura MIME:
                msg_alternative = MIMEMultipart('alternative')
                msg.attach(msg_alternative)
                
                # 1. Plain Text
                plain_text = msg_data.get('plain_body', 'Por favor habilite HTML para ver este mensaje.')
                msg_alternative.attach(MIMEText(plain_text, 'plain'))
                
                # 2. HTML
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
                        stats['log'].append(f"📎 [RunID:{run_id}] INLINE_IMAGE_ATTACHED: True (Size: {len(logo_data)} bytes)")
                    except Exception as e_img:
                         stats['log'].append(f"⚠️ [RunID:{run_id}] No se pudo adjuntar logo: {str(e_img)}")

                # Log PRE-SEND (Forensic)
                stats['log'].append(f"📡 [RunID:{run_id}] SEND_CALL #{send_call_index} PREPARE -> To: {msg_data['email']} | MsgID: {msg_id}")
                
                # --- RC-BUG-009: Explicit Envelope Deduplication ---
                # Use normalized list from above
                all_recipients = all_recipients_clean
                unique_envelope_recipients = list(set(email.lower() for email in all_recipients))
                
                # --- RC-FEAT-013: Internal Copies (CC/BCC) ---
                copies_log_info = ""
                
                if not qa_mode_active:
                    # PROD: Apply Copies
                    cfg_copies = internal_copies_config or {}
                    norm_cc = helpers.normalize_emails(cfg_copies.get('cc_list', []))
                    norm_bcc = helpers.normalize_emails(cfg_copies.get('bcc_list', []))
                    
                    # 1. Update Envelope (Add to unique recipients)
                    # We iterate and add if not present to avoid duplicates
                    added_cc = 0
                    added_bcc = 0
                    
                    for e in norm_cc:
                        if e.lower() not in unique_envelope_recipients:
                            unique_envelope_recipients.append(e.lower())
                            added_cc += 1
                            
                    for e in norm_bcc:
                        if e.lower() not in unique_envelope_recipients:
                            unique_envelope_recipients.append(e.lower())
                            added_bcc += 1
                            
                    if added_cc > 0 or added_bcc > 0:
                        copies_log_info = f"[Copies Added: {added_cc} CC, {added_bcc} BCC]"
                        
                    # 2. Set Headers (Only CC is visible)
                    if norm_cc:
                        msg['Cc'] = ", ".join(norm_cc)
                        
                else:
                    # QA: Ignore Copies
                    # We do not add anything to envelope. Envelope is strictly what came from 'all_recipients_clean' (QA Targets)
                    copies_log_info = "[QA Mode: Internal Copies SKIPPED]"
                
                # --- Advanced Forensic Headers ---
                # Identificadores de Proceso/Hilo
                thread_id = str(threading.get_ident())
                process_id = str(os.getpid())
                
                msg['X-Antay-Run-ID'] = run_id
                msg['X-Antay-MsgID'] = msg_id 
                msg['X-Antay-Ledger-Key'] = ledger_key
                msg['X-Antay-Rcpt-Count'] = str(len(unique_envelope_recipients))
                msg['X-Antay-To-Addrs'] = ",".join(unique_envelope_recipients)
                msg['X-Antay-Timestamp'] = str(now_ts)
                msg['X-Antay-Thread-ID'] = thread_id
                msg['X-Antay-Process-ID'] = process_id
                msg['X-Antay-SMTP-Server'] = smtp_config['server']
                
                # Log Actual RCPT LIST
                recipients_log_str = ", ".join(unique_envelope_recipients)
                print(f"DEBUG_FORENSIC: [RunID:{run_id}] Thread:{thread_id} | RCPT_LIST={recipients_log_str} | LedgerKey={ledger_key}")
                stats['log'].append(f"📧 [RunID:{run_id}] Envelope Targets ({len(unique_envelope_recipients)}): {recipients_log_str} {copies_log_info}")

                # Enviar con sobre explícito (Explicit Envelope)
                server.send_message(msg, to_addrs=unique_envelope_recipients)

                # Log POST-SEND (Forensic)
                stats['log'].append(f"✅ [RunID:{run_id}] SEND_CALL #{send_call_index} SUCCESS -> Sent OK")
                
                # 4. Update Ledger (Confirm Sent)
                reason = "USER_RESEND" if force_resend else "NORMAL"
                if not qa_mode_active and copies_log_info:
                    reason += "_wCOPIES"
                
                try:
                    # Update State
                    c.execute("INSERT OR REPLACE INTO ledger_last_send (ledger_key, last_sent_at, last_msg_id, send_count) VALUES (?, ?, ?, COALESCE((SELECT send_count FROM ledger_last_send WHERE ledger_key=?)+1, 1))", 
                              (ledger_key, now_ts, msg_id, ledger_key))
                    
                    # Audit Entry
                    att_id = str(uuid.uuid4())
                    c.execute("INSERT INTO send_attempts VALUES(?,?,?,?,?,?,?)", 
                              (att_id, ledger_key, recipient_ledger, 'SENT', reason, now_ts, run_id))
                    
                    conn.commit()
                except Exception as e_ins:
                     stats['log'].append(f"⚠️ [RunID:{run_id}] Ledger Write Error: {e_ins}")
                
                stats['success'] += 1
                stats['log'].append(f"[{i+1}/{total}] Enviado a {msg_data['client_name']} ({msg_data['email']})")
                
                # Detail Entry (Success)
                stats['details'].append({
                    'Cliente': client_name,
                    'Email': recipient_ledger,
                    'Estado': '✅ Enviado',
                    'Detalle': f'Entregado SMTP {copies_log_info}',
                    'RunID': run_id
                })

                if progress_callback:
                    progress_callback(i+1, total, f"Enviando a {msg_data['client_name']}...")
                
            except Exception as e:
                # Audit Failure
                try:
                     att_id = str(uuid.uuid4())
                     c.execute("INSERT INTO send_attempts VALUES(?,?,?,?,?,?,?)", 
                              (att_id, ledger_key, recipient_ledger, 'FAILED', str(e)[:50], now_ts, run_id))
                     conn.commit()
                except:
                     pass

                stats['failed'] += 1
                stats['log'].append(f"[{i+1}/{total}] ❌ [RunID:{run_id}] Error para {msg_data['client_name']}: {str(e)}")
                
                # Detail Entry (Fail)
                stats['details'].append({
                    'Cliente': client_name,
                    'Email': recipient_ledger,
                    'Estado': '❌ Falló',
                    'Detalle': str(e)[:100],
                    'RunID': run_id
                })
        
        conn.close() # Close DB
        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        err_msg = "❌ Error de Autenticación (535). \nSi usas Gmail, NECESITAS activar 'Verificación en 2 pasos' y generar una 'Contraseña de Aplicación'. Tu contraseña normal de Google NO funcionará."
        stats['log'].append(err_msg)
        stats['failed'] = len(messages)
    except Exception as e:
        stats['log'].append(f"❌ Error de Conexión SMTP: {str(e)}")
        stats['failed'] = len(messages)
        
    return stats
