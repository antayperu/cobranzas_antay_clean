import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from email.utils import make_msgid, formatdate
import pandas as pd
import uuid
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
    Refinado v2 (RC-UX-003): Header Compacto, Lenguaje Formal, Layout Reordenado.
    """
    
    # 1. Branding y Config
    COLOR_PRIMARY = branding_config.get('primary_color', '#2E86AB')
    COLOR_SECONDARY = branding_config.get('secondary_color', '#A23B72')
    BG_COLOR = "#f4f4f4"
    TEXT_COLOR = "#333333"
    COMPANY_NAME = branding_config.get('company_name', 'DACTA S.A.C.')
    TEMPLATE = branding_config.get('email_template', {})
    
    # --- PROCESAMIENTO DE TOTALES Y KPIs ---
    try:
        mask_soles = docs_df['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
        
        # Dataframes por moneda
        df_sol = docs_df[mask_soles]
        df_dol = docs_df[~mask_soles]
        
        # 1. Deuda DACTA Soles
        sum_s = df_sol['SALDO REAL'].sum()
        count_s = len(df_sol)
        # Format Formal (US$ y documentos)
        kpi_dacta_s = f"S/ {sum_s:,.2f} ({count_s:02d} documentos)" if (sum_s > 0 or count_s > 0) else None

        # 2. Deuda DACTA Dolares
        sum_d = df_dol['SALDO REAL'].sum()
        count_d = len(df_dol)
        # Format Formal (US$ y documentos)
        kpi_dacta_d = f"US$ {sum_d:,.2f} ({count_d:02d} documentos)" if (sum_d > 0 or count_d > 0) else None
        
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
        
        kpi_sunat = f"S/ {sum_detr:,.2f} ({count_detr:02d} documentos afectos)" if sum_detr > 0 else "S/ 0.00 (00 documentos)"

        # Construir Lista de Totales Formal
        intro_totals_html = ""
        if kpi_dacta_s:
            intro_totals_html += f"<li>Deuda a DACTA (Soles): <strong>{kpi_dacta_s}</strong></li>"
        if kpi_dacta_d:
            intro_totals_html += f"<li>Deuda a DACTA (Dólares): <strong>{kpi_dacta_d}</strong></li>"
        
        # Detracción siempre se menciona en resumen si hay
        if sum_detr > 0:
             # Refined styling: no red text line, just standard text with clear label
             intro_totals_html += f"<li class='detr-item'>Detracción SUNAT (Total S/): <strong>{kpi_sunat}</strong></li>"

        if not intro_totals_html:
             intro_totals_html = "<li>Sin deuda pendiente.</li>"

    except Exception as e:
        intro_totals_html = "<li>Error calculando totales.</li>"

    # Header Compacto (Fecha actual)
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    FOOTER_TEXT = TEMPLATE.get('footer_text', '').replace('\n', '<br>')
    # Alert Text is unused in new layout logic, replaced by Dedicated Section

    # --- GENERACIÓN DE FILAS (PC y MÓVIL) ---
    table_rows = ""
    mobile_cards = ""
    
    for _, row in docs_df.iterrows():
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
        # Regla Visual: Si det_val > 0, mostrar S/. Si no -
        if det_val > 0:
            m_det = f"S/ {det_val:,.2f}"
            style_det = "color: #d9534f; fontWeight: bold;"
        else:
            m_det = "-"
            style_det = "color: #ccc;"

        estado_dt = str(row.get('ESTADO DETRACCION', ''))
        if estado_dt.upper() == "PENDIENTE":
            st_class = "st-pend"
            st_text = "Pendiente"
            style_st = "color: #d9534f; font-weight: bold;"
        elif estado_dt.upper() == "NO APLICA":
             st_class = "st-na"
             st_text = "No aplica"
             style_st = "color: #999;"
        else:
             st_class = "st-ok"
             st_text = "Cobrado" # o el texto que venga
             style_st = "color: #28a745;"
             
        # Regla visual: Si Saldo Dacta es 0 pero Detraccion Pendiente -> Alerta visual explícita
        row_bg = "#ffffff"
        m_sal_display = m_sal
        
        # "Saldo a DACTA: 0.00 — Solo falta detracción SUNAT"
        if sal_val <= 0.1 and det_val > 0 and st_text == "Pendiente":
            m_sal_display = "<span style='color:#999;'>0.00</span><br><span style='font-size:10px; color:#d9534f'>(Solo falta Detracción)</span>"
            row_bg = "#fffcfc"

        # --- A) HTML TABLE ROW (PC) ---
        table_rows += f"""
        <tr style="background-color: {row_bg};">
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">{doc}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">{f_emis}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">{f_venc}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee; text-align: right;">{m_imp}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold; color: {COLOR_PRIMARY};">{m_sal_display}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee; text-align: right; {style_det}">{m_det}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee; text-align: center; font-size: 12px; {style_st}">{st_text}</td>
        </tr>
        """
        
        # --- B) HTML CARD (MOBILE) ---
        # Card Layout: Header (Doc, Venc) | Body (Importe) | Footer (Saldo Dacta / Detr Sunat)
        
        mobile_cards += f"""
        <div class="mobile-card" style="display:none; background:{row_bg}; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 12px; padding: 15px;">
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
                 <span style="{style_det}">{m_det} <small>({st_text})</small></span>
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
        body {{ font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: {BG_COLOR}; margin: 0; padding: 0; color: {TEXT_COLOR}; }}
        .container {{ max-width: 720px; margin: 0 auto; background-color: #ffffff; }}
        
        /* PC Styles */
        .desktop-only {{ display: table; }}
        .mobile-only {{ display: none; }}
        
        /* Header v5 (Restored Initial Model - Centered Stack) */
        /* Adjusted padding to balance larger logo (20px top/15px bottom) */
        .header-container {{ padding: 20px 20px 15px 20px; background-color: #ffffff; border-bottom: 1px solid #e5e7eb; }}
        
        /* Table overrides */
        .header-table {{ width: 100%; border-collapse: collapse; border: none; margin: 0; }}
        .header-td-center {{ text-align: center; vertical-align: middle; padding-bottom: 5px; }}
        
        /* Logo: Dominant Presence (Increased to 90px) */
        .header-logo img {{ max-height: 90px; width: auto; display: block; margin: 0 auto; }}
        
        /* Title: Standalone section */
        .header-title {{ font-size: 16px; font-weight: 700; color: #111827; letter-spacing: 1px; text-transform: uppercase; margin-top: 15px; margin-bottom: 5px; }}
        
        /* Date: Subtle below title */
        .header-date {{ font-size: 12px; color: #9ca3af; font-family: 'Helvetica', sans-serif; margin-bottom: 5px; }}
        
        .content-box {{ padding: 30px 40px; }}
        
        .greeting {{ font-size: 15px; margin-bottom: 15px; color: #000; font-weight: bold; }}
        .section-title {{ font-size: 13px; font-weight: bold; color: {COLOR_PRIMARY}; text-transform: uppercase; margin-top: 25px; margin-bottom: 10px; border-bottom: 2px solid {COLOR_PRIMARY}; display: inline-block; padding-bottom: 3px; }}
        
        /* KPI List Refined (Formal) */
        .kpi-list {{ list-style: none; padding: 0; margin: 0 0 20px 0; font-size: 14px; line-height: 1.8; color: #374151; }}
        .kpi-list li {{ margin-bottom: 4px; }}
        /* Detracción softer style: no red text, just bold amount */
        .detr-item {{ color: #374151; }}
        
        /* Accounts Block */
        .payment-methods {{ background-color: #fafafa; padding: 20px; border-radius: 4px; border: 1px solid #eee; margin-top: 30px; font-size: 12px; line-height: 1.6; color: #333; }}
        .payment-group {{ margin-bottom: 12px; }}
        .bank-label {{ font-weight: bold; color: #000; display: inline-block; width: 90px; }}
        
        /* Specific Detraccion Warning (Single location) - Premium Gray */
        .detraccion-box {{ background-color: #f8fafc; border-left: 3px solid #d9534f; padding: 15px; margin: 25px 0; font-size: 13px; color: #333333; }}
        
        /* Tables */
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 20px; }}
        th {{ background-color: #f8f8f8; color: #333; padding: 10px; text-align: left; border-bottom: 2px solid #ddd; font-weight: bold; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }}
        
        /* Footer */
        .footer {{ background-color: #f4f4f4; color: #777; padding: 20px; text-align: center; font-size: 11px; line-height: 1.5; border-top: 1px solid #ddd; }}
        
        /* MEDIA QUERIES (MOBILE) */
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
            .content-box {{ padding: 20px 15px !important; }}
            
            /* Toggle Views */
            .desktop-only {{ display: none !important; }}
            .mobile-only {{ display: block !important; }}
            .mobile-card {{ display: block !important; }}
            
            /* Adjusted Header Mobile - Centered Stack matches PC */
            .header-container {{ padding: 20px 15px; }}
            .header-logo img {{ max-height: 60px; }}
            
            /* Adjust fonts */
            .kpi-list {{ font-size: 13px; }}
            .payment-methods {{ font-size: 11px; }}
        }}
    </style>
    </head>
    <body>
        <div class="container">
            <!-- Header V5: Centered Stack (Robust Table) -->
            <div class="header-container">
                <table class="header-table" width="100%" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                        <td class="header-td-center">
                            <img src="cid:logo_dacta" alt="{COMPANY_NAME}" class="header-logo-img" height="90" style="display:block; margin:0 auto; max-height:90px; width:auto; height:auto;">
                        </td>
                    </tr>
                    <tr>
                        <td class="header-td-center">
                            <div class="header-title">ESTADO DE CUENTA</div>
                        </td>
                    </tr>
                    <tr>
                        <td class="header-td-center">
                            <div class="header-date">{current_date}</div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div class="content-box">
                <div class="greeting">Estimados {client_name},</div>
                <div style="font-size: 13px; margin-bottom: 15px;">
                    A la fecha, el sistema de cobranzas registra los siguientes pendientes de pago:
                </div>
                
                <ul class="kpi-list">
                    {intro_totals_html}
                </ul>
                
                <div class="section-title">Detalle de Documentos</div>

                <!-- PC VIEW: TABLE -->
                <table class="desktop-only">
                    <thead>
                        <tr>
                            <th>Documento</th>
                            <th>Emisión</th>
                            <th>Vencimiento</th>
                            <th style="text-align: right;">Importe</th>
                            <th style="text-align: right;">Saldo a DACTA</th>
                            <th style="text-align: right;">Detracción SUNAT (S/)</th>
                            <th style="text-align: center;">Estado Detr.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                
                <!-- MOBILE VIEW: CARDS -->
                <div class="mobile-only">
                    {mobile_cards}
                </div>
                
                <!-- DETRACCIÓN BLOCK (Single Instance) -->
                <div class="detraccion-box" style="background-color: #f8fafc; border-left: 3px solid #d9534f; padding: 15px; margin: 25px 0; font-size: 13px; color: #333333;">
                    <strong>IMPORTANTE - Detracción SUNAT:</strong><br>
                    Si el documento está afecto, el monto de detracción debe depositarse exclusivamente al 
                    <strong>Banco de la Nación</strong>, Cuenta N°: <strong>00-005-034272</strong>.<br>
                    <em>Nota: La detracción siempre se expresa y deposita en Soles (S/).</em>
                </div>

                <!-- MEDIOS DE PAGO BLOCK (Bottom) -->
                <div class="section-title">Medios de Pago (DACTA S.A.C.)</div>
                <div class="payment-methods">
                    <div class="payment-group">
                        <div style="margin-bottom:4px; font-weight:bold; color: {COLOR_PRIMARY};">CUENTAS EN SOLES (S/):</div>
                        <div><span class="bank-label">BCP:</span> 1931472448010 &nbsp;|&nbsp; <strong>CCI:</strong> 00219300147244801019</div>
                        <div><span class="bank-label">BBVA:</span> 001103400200230077 &nbsp;|&nbsp; <strong>CCI:</strong> 01134000020023007776</div>
                    </div>
                    <div class="payment-group" style="margin-top: 12px;">
                        <div style="margin-bottom:4px; font-weight:bold; color: {COLOR_PRIMARY};">CUENTAS EN DÓLARES (US$):</div>
                        <div><span class="bank-label">BCP:</span> 1912078776145 &nbsp;|&nbsp; <strong>CCI:</strong> 00219100207877614559</div>
                    </div>
                </div>

                <div style="font-size: 12px; color: #555; margin-top: 25px;">
                    Si ya realizó el pago recientemente, por favor omita este mensaje o envíe el comprobante para actualizar el estado.
                </div>
            </div>
            
            <div class="footer">
                <strong>{COMPANY_NAME}</strong><br>
                Área de Cobranzas y Facturación<br>
                RUC: {branding_config.get('company_ruc', '')}
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

def send_email_batch(smtp_config, messages, progress_callback=None, logo_path=None, force_resend=False, supervisor_config=None):
    """
    Envía lote de correos con reporte de progreso y bloqueo TTL por negocio.
    force_resend: Si True, ignora el bloqueo TTL (Reason: USER_RESEND).
    supervisor_config: Dict opcional {'email': '...', 'enabled': True/False, 'mode': 'BCC'/'CC'}
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
        email_clean = str(m.get('email', '')).strip().lower()
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
            recipient_ledger = msg_data['email'].strip().lower()
            
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
                msg['To'] = msg_data['email']
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
                    except Exception as e_img:
                         stats['log'].append(f"⚠️ [RunID:{run_id}] No se pudo adjuntar logo: {str(e_img)}")

                # Log PRE-SEND (Forensic)
                stats['log'].append(f"📡 [RunID:{run_id}] SEND_CALL #{send_call_index} PREPARE -> To: {msg_data['email']} | MsgID: {msg_id}")
                
                # --- RC-BUG-009: Explicit Envelope Deduplication ---
                raw_to = str(msg_data['email']).split(',')
                all_recipients = [e.strip() for e in raw_to if e.strip()]
                unique_envelope_recipients = list(set(email.lower() for email in all_recipients))
                
                # --- RC-FEAT-011: Copia Supervisión (BCC/CC) ---
                supervisor_copy_target = None
                supervisor_log_info = ""
                
                if supervisor_config and supervisor_config.get('enabled', False):
                    sup_email = str(supervisor_config.get('email', '')).strip()
                    if sup_email and '@' in sup_email:
                        supervisor_copy_target = sup_email
                        sup_mode = str(supervisor_config.get('mode', 'BCC')).upper()
                        
                        # Agregar al envelope siempre (se enviará a esta direcicón)
                        if sup_email.lower() not in unique_envelope_recipients:
                            unique_envelope_recipients.append(sup_email.lower())
                            
                        # Configurar Headers (CC vs BCC)
                        if sup_mode == 'CC':
                            msg['Cc'] = sup_email
                            supervisor_log_info = f"[CC: {sup_email}]"
                        else:
                            # BCC (Default): No header, just envelope
                            supervisor_log_info = f"[BCC: {sup_email}]"
                
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
                stats['log'].append(f"📧 [RunID:{run_id}] Envelope Targets ({len(unique_envelope_recipients)}): {recipients_log_str} {supervisor_log_info}")

                # Enviar con sobre explícito (Explicit Envelope)
                server.send_message(msg, to_addrs=unique_envelope_recipients)

                # Log POST-SEND (Forensic)
                stats['log'].append(f"✅ [RunID:{run_id}] SEND_CALL #{send_call_index} SUCCESS -> Sent OK")
                
                # 4. Update Ledger (Confirm Sent)
                reason = "USER_RESEND" if force_resend else "NORMAL"
                if supervisor_copy_target:
                    reason += f"_wCOPY_{supervisor_config.get('mode','BCC')}"
                
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
                    'Detalle': f'Entregado SMTP {supervisor_log_info}',
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
