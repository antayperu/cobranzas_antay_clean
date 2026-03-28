import smtplib
import html
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
import traceback
import socket
import ssl
import base64
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId
    HAS_SENDGRID = True
except ImportError:
    HAS_SENDGRID = False

try:
    import resend
    HAS_RESEND = True
except ImportError:
    HAS_RESEND = False
from . import helpers
from . import db_manager

# Colores Branding
COLOR_PRIMARY = "#2E86AB"
COLOR_SECONDARY = "#A23B72"
COLOR_BG = "#f4f4f4"
COLOR_TEXT = "#333333"


def generate_cover_email_html(client_name, docs_df, cycle_id, branding_config):
    """
    Genera el cuerpo HTML premium del correo de notificación de cobranza.
    RC-FEAT-041: Email corporativo de clase mundial — solo resumen ejecutivo,
    sin tabla de documentos (el detalle completo va en el PDF adjunto).

    Contenido 100% configurable desde Tab Configuración → Plantillas de Correo:
      email_body_text — cuerpo breve con variables dinámicas
      footer_text     — cierre (incluye mensaje "caso omiso")
      firma_cargo     — cargo del área firmante
      cuentas_sol/usd — cuentas bancarias (antes hardcodeadas)

    Variables en email_body_text: {CLIENTE}, {DEUDA_SOL}, {DOCS_SOL},
                                   {DEUDA_USD}, {DOCS_USD}, {DETRACCION}, {FECHA}
    """
    company_name  = branding_config.get("company_name", "DACTA S.A.C.")
    company_ruc   = branding_config.get("company_ruc", "")
    phone         = branding_config.get("phone_contact", "")
    primary_color = branding_config.get("primary_color", "#0D3B66")
    tmpl          = branding_config.get("email_template", {})

    def _nl2br(txt):
        return html.escape(str(txt or "")).replace("\n", "<br>")

    # ── Calcular KPIs ─────────────────────────────────────────────────────────
    sum_s = sum_d = sum_detr = 0.0
    count_s = count_d = count_detr = 0
    try:
        df_calc = docs_df.copy()
        df_calc['SALDO_REAL_CLEAN'] = df_calc['SALDO REAL'].apply(helpers.safe_clean_decimal)
        df_calc['DETRACCION_CLEAN'] = df_calc['DETRACCIÓN'].apply(helpers.safe_clean_decimal)
        mask_soles = df_calc['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
        df_sol  = df_calc[mask_soles]
        df_dol  = df_calc[~mask_soles]
        sum_s   = df_sol['SALDO_REAL_CLEAN'].sum()
        count_s = len(df_sol)
        sum_d   = df_dol['SALDO_REAL_CLEAN'].sum()
        count_d = len(df_dol)
        try:
            mask_dv    = df_calc['DETRACCION_CLEAN'] > 0.01
            mask_ds    = df_calc['ESTADO DETRACCION'].astype(str).str.strip().str.upper() == 'PENDIENTE'
            df_detr    = df_calc[mask_dv & mask_ds]
            sum_detr   = df_detr['DETRACCION_CLEAN'].sum()
            count_detr = len(df_detr)
        except Exception:
            pass
    except Exception:
        pass

    kpi_sol   = f"S/ {sum_s:,.2f}"
    kpi_sol_n = f"{count_s:02d} doc{'umento' if count_s == 1 else 'umentos'}"
    kpi_usd   = f"US$ {sum_d:,.2f}"
    kpi_usd_n = f"{count_d:02d} doc{'umento' if count_d == 1 else 'umentos'}"
    kpi_detr  = f"S/ {sum_detr:,.2f}"
    kpi_detr_n = f"{count_detr:02d} doc{'umento afecto' if count_detr == 1 else 'umentos afectos'}"

    fecha_str = datetime.now().strftime("%d/%m/%Y")
    safe_client = html.escape(str(client_name))

    # ── Variables para sustitución en email_body_text ─────────────────────────
    _var_map = {
        "{CLIENTE}":    safe_client,
        "{cliente}":    safe_client,
        "{DEUDA_SOL}":  f"S/ {sum_s:,.2f}",
        "{DOCS_SOL}":   f"{count_s:02d} documentos",
        "{DEUDA_USD}":  f"US$ {sum_d:,.2f}",
        "{DOCS_USD}":   f"{count_d:02d} documentos",
        "{DETRACCION}": f"S/ {sum_detr:,.2f}",
        "{FECHA}":      fecha_str,
    }

    def _apply_vars(raw: str) -> str:
        result = html.escape(str(raw or ""))
        for var, val in _var_map.items():
            result = result.replace(html.escape(var), val)
        return result.replace("\n", "<br>")

    # ── Textos configurables ──────────────────────────────────────────────────
    body_raw    = (tmpl.get("email_body_text") or tmpl.get("intro_text") or "").strip()
    footer_raw  = (tmpl.get("footer_text") or "").strip()
    firma_cargo = html.escape(tmpl.get("firma_cargo", "Area de Cobranzas y Facturacion").strip())

    body_html = _apply_vars(body_raw) if body_raw else (
        f"Estimado {safe_client},<br><br>"
        "Le informamos que a la fecha presenta documentos pendientes de pago.<br>"
        "Le agradeceremos gestionar la cancelaci&#243;n para mantener su servicio activo."
    )
    footer_html = _nl2br(footer_raw) if footer_raw else (
        "En caso de haber realizado el pago recientemente, por favor hacer caso omiso a este mensaje."
    )

    # ── Logo ──────────────────────────────────────────────────────────────────
    has_logo = bool(branding_config.get("logo_path") or branding_config.get("logo_bytes"))
    logo_img = (
        f'<img src="cid:logo_dacta" width="160" alt="{html.escape(company_name)}"'
        ' style="max-width:160px;max-height:64px;height:auto;display:block;margin:0 auto">'
        if has_logo else
        f'<div style="font-size:20px;font-weight:700;color:{primary_color};'
        f'letter-spacing:1px;font-family:Georgia,serif">{html.escape(company_name)}</div>'
    )

    # ── Barra inferior empresa ────────────────────────────────────────────────
    company_parts = [html.escape(company_name)]
    if company_ruc:
        company_parts.append(f"RUC {html.escape(company_ruc)}")
    if phone:
        company_parts.append(html.escape(phone))
    company_line = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join(company_parts)

    # ── KPI rows del resumen de cuenta ────────────────────────────────────────
    def _kpi_row(label: str, amount: str, qty: str, show: bool = True) -> str:
        if not show:
            return ""
        return (
            f'<tr>'
            f'<td style="padding:12px 0;color:#4A5568;font-size:13px;'
            f'border-bottom:1px solid #EDF2F7;font-weight:400;'
            f'font-family:\'Helvetica Neue\',Arial,sans-serif">{label}</td>'
            f'<td style="padding:12px 0;text-align:right;border-bottom:1px solid #EDF2F7">'
            f'<span style="font-weight:700;font-size:16px;color:{primary_color};'
            f'font-family:Georgia,serif">{amount}</span>'
            f'<br><span style="font-size:11px;color:#A0AEC0;font-family:\'Helvetica Neue\',Arial,sans-serif">{qty}</span>'
            f'</td>'
            f'</tr>'
        )

    resumen_rows = (
        _kpi_row("Deuda Total <strong>Soles</strong>", kpi_sol, kpi_sol_n)
        + _kpi_row("Deuda Total <strong>D&oacute;lares</strong>", kpi_usd, kpi_usd_n)
        + _kpi_row("Detracciones SUNAT Pendientes", kpi_detr, kpi_detr_n, show=(sum_detr > 0.01))
    )

    # ── Sección cuentas bancarias ─────────────────────────────────────────────
    def _render_cuenta_col(cuentas: list, titulo: str) -> str:
        cuentas_validas = [c for c in (cuentas or []) if isinstance(c, dict) and c.get("numero", "").strip()]
        if not cuentas_validas:
            return ""
        items_html = ""
        for c in cuentas_validas:
            banco  = html.escape(c.get("banco",  "").strip())
            numero = html.escape(c.get("numero", "").strip())
            cci    = html.escape(c.get("cci",    "").strip())
            items_html += (
                f'<p style="margin:0 0 8px;font-size:13px;color:#2D3748;'
                f'font-family:\'Helvetica Neue\',Arial,sans-serif">'
                f'<span style="font-weight:600">{banco}:</span> {numero}'
                + (f'<br><span style="font-size:11px;color:#718096">CCI: {cci}</span>' if cci else "")
                + '</p>'
            )
        return (
            f'<td style="padding:20px 24px;vertical-align:top;width:50%">'
            f'<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:1px;'
            f'color:{primary_color};text-transform:uppercase;'
            f'font-family:\'Helvetica Neue\',Arial,sans-serif">{titulo}</p>'
            f'{items_html}'
            f'</td>'
        )

    _col_sol = _render_cuenta_col(tmpl.get("cuentas_sol", []), "Cuentas en Soles (S/)")
    _col_usd = _render_cuenta_col(tmpl.get("cuentas_usd", []), "Cuentas en D&oacute;lares (US$)")
    _contact_email = html.escape(tmpl.get("contact_email", "").strip())
    _contact_phone = html.escape(tmpl.get("contact_phone", "").strip())
    _voucher_raw   = (tmpl.get("voucher_text") or "").strip()

    cuentas_block = ""
    if _col_sol or _col_usd:
        contact_row = ""
        if _contact_email or _contact_phone:
            parts = []
            if _contact_email:
                parts.append(f"Envío de vouchers: <strong>{_contact_email}</strong>")
            if _contact_phone:
                parts.append(f"Tel: {_contact_phone}")
            contact_row = (
                f'<tr><td colspan="2" style="padding:4px 24px 16px;font-size:12px;'
                f'color:#718096;border-top:1px solid #EDF2F7;'
                f'font-family:\'Helvetica Neue\',Arial,sans-serif">'
                + " &nbsp;&bull;&nbsp; ".join(parts)
                + "</td></tr>"
            )
        if _voucher_raw:
            contact_row += (
                f'<tr><td colspan="2" style="padding:0 24px 16px;font-size:12px;'
                f'color:#718096;font-family:\'Helvetica Neue\',Arial,sans-serif">'
                + _nl2br(_voucher_raw) + "</td></tr>"
            )
        cuentas_block = f"""
        <tr>
          <td style="padding:0 44px 0">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="border:1px solid #E2E8F0;border-top:3px solid {primary_color}">
              <tr>
                <td colspan="2" style="padding:14px 24px 8px">
                  <span style="font-size:10px;font-weight:700;letter-spacing:1px;
                               color:{primary_color};text-transform:uppercase;
                               font-family:'Helvetica Neue',Arial,sans-serif">
                    Datos para el Pago
                  </span>
                </td>
              </tr>
              <tr>
                {_col_sol}
                {_col_usd if _col_usd else '<td style="width:50%"></td>'}
              </tr>
              {contact_row}
            </table>
          </td>
        </tr>
        <tr><td style="height:32px;font-size:0">&nbsp;</td></tr>"""

    # ── Mes en español para el encabezado ─────────────────────────────────────
    _MESES = ["enero","febrero","marzo","abril","mayo","junio",
              "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    _now = datetime.now()
    fecha_larga = f"{_now.day} de {_MESES[_now.month-1]} de {_now.year}"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Estado de Cuenta</title>
</head>
<body style="margin:0;padding:0;background:#E8ECF1;
             font-family:'Helvetica Neue',Helvetica,Arial,sans-serif">

<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
  <tr>
    <td align="center" style="padding:36px 16px 48px">

      <!-- ╔═══════════════ CARD 600px ═══════════════╗ -->
      <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0"
             style="max-width:600px;width:100%;background:#FFFFFF;
                    box-shadow:0 2px 4px rgba(0,0,0,.06),0 12px 40px rgba(0,0,0,.10)">

        <!-- ── LOGO (fondo blanco — siempre visible) ─────────────────── -->
        <tr>
          <td align="center"
              style="background:#FFFFFF;padding:28px 48px 24px;
                     border-bottom:1px solid #E2E8F0">
            {logo_img}
          </td>
        </tr>

        <!-- ── HEADER CORPORATIVO (título + fecha) ──────────────────── -->
        <tr>
          <td align="center"
              style="background:{primary_color};padding:28px 48px 26px">

            <!-- Separador decorativo -->
            <div style="width:40px;height:1px;background:rgba(255,255,255,.30);
                        margin:0 auto 18px"></div>

            <!-- Título principal -->
            <div style="font-family:Georgia,'Times New Roman',serif;
                        font-size:24px;font-weight:400;font-style:normal;
                        color:#FFFFFF;letter-spacing:3px;text-transform:uppercase;
                        line-height:1.2;margin-bottom:8px">
              Estado de Cuenta
            </div>

            <!-- Fecha -->
            <div style="font-family:'Helvetica Neue',Arial,sans-serif;
                        font-size:11px;color:rgba(255,255,255,.60);
                        letter-spacing:1.5px;text-transform:uppercase">
              Al {fecha_larga}
            </div>

          </td>
        </tr>

        <!-- ── CUERPO DEL MENSAJE ─────────────────────────────────────── -->
        <tr>
          <td align="center" style="padding:40px 52px 0">
            <p style="margin:0;font-size:15px;line-height:27px;
                      color:#4A5568;text-align:center;
                      font-family:'Helvetica Neue',Arial,sans-serif">
              {body_html}
            </p>
          </td>
        </tr>

        <!-- ── RESUMEN FINANCIERO ─────────────────────────────────────── -->
        <tr>
          <td style="padding:32px 44px 0">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="border:1px solid #E2E8F0;border-top:3px solid {primary_color}">
              <tr>
                <td style="padding:16px 24px 8px">
                  <span style="font-size:10px;font-weight:700;letter-spacing:1px;
                               color:{primary_color};text-transform:uppercase;
                               font-family:'Helvetica Neue',Arial,sans-serif">
                    Resumen de Cuenta
                  </span>
                </td>
              </tr>
              <tr>
                <td style="padding:0 24px 16px">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                    {resumen_rows}
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ── AVISO PDF ADJUNTO ──────────────────────────────────────── -->
        <tr>
          <td style="padding:20px 44px 0">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="border:1px dashed #CBD5E0;background:#F7FAFC">
              <tr>
                <td style="padding:14px 20px;font-size:13px;color:#718096;line-height:20px;
                           font-family:'Helvetica Neue',Arial,sans-serif">
                  <strong style="color:#2D3748;font-size:13px">
                    &#128206; Estado de Cuenta adjunto en PDF
                  </strong><br>
                  El documento adjunto incluye el detalle completo de sus facturas pendientes.
                  Puede abrirlo, imprimirlo o archivarlo para su registro.
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ── ESPACIADO ──────────────────────────────────────────────── -->
        <tr><td style="height:32px;font-size:0;line-height:0">&nbsp;</td></tr>

        {cuentas_block}

        <!-- ── SEPARADOR ─────────────────────────────────────────────── -->
        <tr>
          <td style="padding:0 44px">
            <div style="height:1px;background:#EDF2F7"></div>
          </td>
        </tr>

        <!-- ── PIE Y FIRMA ────────────────────────────────────────────── -->
        <tr>
          <td style="padding:24px 52px 32px;
                     font-family:'Helvetica Neue',Arial,sans-serif">
            <p style="margin:0 0 20px;font-size:13px;line-height:22px;color:#718096">
              {footer_html}
            </p>
            <p style="margin:0;font-size:13px;font-weight:600;
                      color:#2D3748;letter-spacing:.2px">
              {firma_cargo}
            </p>
          </td>
        </tr>

        <!-- ── FOOTER EMPRESA ─────────────────────────────────────────── -->
        <tr>
          <td align="center"
              style="background:{primary_color};padding:16px 48px;
                     font-size:11px;color:rgba(255,255,255,.55);
                     letter-spacing:.5px;text-transform:uppercase;
                     font-family:'Helvetica Neue',Arial,sans-serif">
            {company_line}
          </td>
        </tr>

      </table>
      <!-- ╚═══════════════════════════════════════════════╝ -->

    </td>
  </tr>
</table>

</body>
</html>"""


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
        # RC-FIX-SLICE: Explicit copy to ensure we own the DF (fixes SettingWithCopy / silent fail)
        df_calc = docs_df.copy() # Use a distinct name to avoid shadowing confusion

        # Apply cleanup to vector (RC-FIX-STRINGS) using shared helper
        df_calc['SALDO_REAL_CLEAN'] = df_calc['SALDO REAL'].apply(helpers.safe_clean_decimal)
        df_calc['DETRACCION_CLEAN'] = df_calc['DETRACCIÓN'].apply(helpers.safe_clean_decimal)
        
        mask_soles = df_calc['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
        
        # Dataframes por moneda
        df_sol = df_calc[mask_soles]
        df_dol = df_calc[~mask_soles]
        
        # 1. Deuda DACTA Soles
        sum_s = df_sol['SALDO_REAL_CLEAN'].sum()
        count_s = len(df_sol)
        kpi_dacta_s = f"S/ {sum_s:,.2f} ({count_s:02d} documentos)" if (sum_s > 0 or count_s > 0) else "S/ 0.00 (00 documentos)"

        # 2. Deuda DACTA Dolares
        sum_d = df_dol['SALDO_REAL_CLEAN'].sum()
        count_d = len(df_dol)
        kpi_dacta_d = f"US$ {sum_d:,.2f} ({count_d:02d} documentos)" if (sum_d > 0 or count_d > 0) else "US$ 0.00 (00 documentos)"
        
        # 3. Detracción SUNAT (Solo documentos afectos)
        # 3. Detracción SUNAT (Solo documentos afectos + Pendientes)
        # RC-FIX-KEYERROR: Consolidate filtering on df_calc directly to avoid intermediate column loss
        try:
            mask_d_val = df_calc['DETRACCION_CLEAN'] > 0.01
            # Handle potential missing column or NaN in ESTADO DETRACCION
            mask_d_st = df_calc['ESTADO DETRACCION'].astype(str).str.strip().str.upper() == 'PENDIENTE'
            
            df_detr_pending = df_calc[mask_d_val & mask_d_st]
            
            sum_detr = df_detr_pending['DETRACCION_CLEAN'].sum()
            count_detr = len(df_detr_pending)
        except Exception as e_det:
             # Fallback if specific calculation fails (should not happen with df_calc)
             print(f"DEBUG DETR FAIL: {e_det}")
             sum_detr = 0.0
             count_detr = 0
        
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
        # RC-DEBUG: Expose error to UI
        print(f"DEBUG EXCEPTION: {e}")
        traceback.print_exc()
        summary_rows_html = f"<tr><td colspan='2' style='color:red;'>Error calculando totales: {str(e)}</td></tr>"

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
    
    # Process Intro: Safe render + Client Name injection (case-insensitive)
    safe_cliente = html.escape(str(client_name))
    intro_html = nl2br_safe(raw_intro).replace("{CLIENTE}", safe_cliente).replace("{cliente}", safe_cliente)

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

    # D. Voucher/Bank Note Block (Configurable - RC-HOTFIX-HTML-001)
    voucher_block_html = ""
    raw_voucher = email_config.get('voucher_text', '').strip()
    if raw_voucher:
        voucher_content_html = nl2br_safe(raw_voucher)
        voucher_block_html = f"""
        <div style="font-size: 13px; color: #64748b; margin-top: 25px; font-style: italic;">
            {voucher_content_html}
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
                
                {voucher_block_html}

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

def send_email_batch(smtp_config, messages, progress_callback=None, logo_path=None, force_resend=False, internal_copies_config=None, qa_settings=None, cycle_id=None):
    """
    Envía lote de correos con reporte de progreso y bloqueo TTL por negocio.
    force_resend: Si True, ignora el bloqueo TTL (Reason: USER_RESEND).
    internal_copies_config: Dict opcional {'cc_list': [...], 'bcc_list': [...]}
    qa_settings: Dict de configuración QA o None. Si está presente y enabled, se aplica lógica QA.
    cycle_id: ID único del ciclo de carga (para aislar TTL entre ciclos). Si None, usa 'default_cycle'.
    """
    import smtplib
    
    # Resolve Cycle ID
    if not cycle_id:
        cycle_id = 'default_cycle'
    
    # Resolve QA State
    is_qa_mode = False
    if qa_settings and qa_settings.get('enabled', False):
        is_qa_mode = True

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

    # 2. Initialize Ledger (Hybrid Mode via db_manager)
    TTL_MINUTES = 10
    db_manager.initialize_db()

    # --- RC-DEBUG-v2: Enhanced Connection & Egress Check ---
    # NEW: First check if we should use API Bridge (Resend or SendGrid)
    resend_key = smtp_config.get('resend_api_key', '')
    sendgrid_key = smtp_config.get('sendgrid_api_key', '')
    force_smtp = smtp_config.get('force_smtp', False)
    
    # Prioritize Resend over SendGrid, but respect force_smtp
    use_resend = HAS_RESEND and bool(resend_key) and not force_smtp
    use_sendgrid = HAS_SENDGRID and bool(sendgrid_key) and not use_resend and not force_smtp
    use_api = use_resend or use_sendgrid
    
    if use_resend:
        stats['log'].append("🚀 [Modo] Usando BRIDGE API (Resend) para saltar bloqueos SMTP.")
    elif use_sendgrid:
        stats['log'].append("🚀 [Modo] Usando BRIDGE API (SendGrid) para saltar bloqueos SMTP.")
    else:
        stats['log'].append("🔌 [Modo] Usando Protocolo SMTP Estándar.")

    host = smtp_config.get('server', 'smtp.gmail.com')
    port = int(smtp_config.get('port', 465))
    
    # DNS Check (Standard diagnostics)
    target_ip = None
    try:
        target_ip = socket.gethostbyname(host)
        stats['log'].append(f"🔍 [DNS] Resolución OK: {host} -> {target_ip}")
    except Exception as dns_e:
        stats['log'].append(f"⚠️ [DNS] No se pudo resolver {host}: {dns_e}")

    # Connectivity Check
    try:
        socket.create_connection(("google.com", 443), timeout=3)
        stats['log'].append("🌐 [Red] Acceso HTTPS (443) OK.")
    except Exception as net_e:
        stats['log'].append(f"🚨 [Red] SIN ACCESO HTTPS: {net_e}")

    try:
        # Connection Handling
        server = None
        if not use_api:
            try:
                stats['log'].append(f"🔌 Conectando a {target_ip or host} vía Puerto {port}...")
                if port == 465:
                    server = smtplib.SMTP_SSL(target_ip or host, port, timeout=25)
                else:
                    server = smtplib.SMTP(target_ip or host, port, timeout=25)
                    server.ehlo()
                    if server.has_extn('starttls'):
                        server.starttls()
                        server.ehlo()
                
                user = str(smtp_config.get('user', '')).strip()
                password = str(smtp_config.get('password', '')).replace(' ', '').strip()
                if not user or not password:
                    raise ValueError("Credenciales SMTP vacías: define usuario y contraseña/app-password.")
                server.login(user, password)
                stats['log'].append(f"✅ [RunID:{run_id}] Conexión SMTP Exitosa.")
            except smtplib.SMTPAuthenticationError:
                err_auth = "❌ Error de Autenticación (535). Si usas Gmail con 2FA, NECESITAS una 'Contraseña de Aplicación'. Tu clave normal de Google no funcionará."
                stats['log'].append(err_auth)
                stats['failed'] = len(messages)
                return stats
            except Exception as conn_e:
                stats['log'].append(f"❌ [Error] Falló conexión SMTP inicial: {conn_e}")
                stats['failed'] = len(messages)
                return stats
        else:
            # API Client (Resend or SendGrid)
            try:
                if use_resend:
                    resend.api_key = resend_key
                    stats['log'].append("✅ [Resend] Cliente API inicializado.")
                elif use_sendgrid:
                    sg_client = SendGridAPIClient(sendgrid_key)
                    stats['log'].append("✅ [SendGrid] Cliente API inicializado.")
            except Exception as e_api_init:
                api_name = "Resend" if use_resend else "SendGrid"
                stats['log'].append(f"❌ [Error] Falló inicialización de {api_name}: {e_api_init}")
                stats['failed'] = len(messages)
                return stats

        total = len(unique_messages)
        send_call_index = 0
        
        for i, msg_data in enumerate(unique_messages):
            send_call_index += 1
            
            client_name = msg_data.get('client_name', 'Unknown')
            
            # --- RC-FIX-QA-TYPE: Robust Ledger Recipient Extraction ---
            # msg_data['email'] can be list in QA mode.
            _recips = helpers.normalize_emails(msg_data['email'])
            recipient_ledger = _recips[0].lower() if _recips else 'unknown_recipient'
            
            # --- Business Key Calculation ---
            if 'notification_key' in msg_data:
                notif_key = msg_data['notification_key']
                ledger_src = f"{cycle_id}|{recipient_ledger}|{notif_key}"  # NUEVO: Incluir cycle_id
            else:
                payload_str_ledger = str(msg_data['html_body']) + str(msg_data['subject'])
                payload_hash_ledger = hashlib.md5(payload_str_ledger.encode()).hexdigest()
                notif_key = f"LEGACY_HASH_{payload_hash_ledger}"
                ledger_src = f"{cycle_id}|{recipient_ledger}|{notif_key}"  # NUEVO: Incluir cycle_id
            
            ledger_key = hashlib.sha256(ledger_src.encode()).hexdigest()
            now_ts = datetime.now()
            
            # 3. Check TTL (Anti-Duplicado Accidental)
            if not force_resend:
                try:
                    existing = db_manager.get_last_sent_info(ledger_key)
                    
                    if existing:
                        last_sent_val = existing['last_sent_at']
                        # Normalizar a datetime
                        if isinstance(last_sent_val, str):
                            try:
                                last_sent = datetime.strptime(last_sent_val.split('.')[0].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                            except:
                                last_sent = datetime.min
                        else:
                            last_sent = last_sent_val
                        
                        elapsed = (now_ts - last_sent).total_seconds() / 60.0
                        
                        if elapsed < TTL_MINUTES:
                            msg_dup = f"🔒 [RunID:{run_id}] BLOCKED by TTL ({elapsed:.1f}m < {TTL_MINUTES}m). Recipient:{recipient_ledger}"
                            stats['log'].append(msg_dup)
                            print(f"DEBUG_FORENSIC: {msg_dup} | Key={ledger_key}")
                            
                            # Audit Block
                            db_manager.log_attempt(recipient_ledger, 'BLOCKED', run_id, ledger_key, reason='TTL_BLOCK')
                            
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
                
                # Adjuntar Logo Inline (si existe) - Only for SMTP, SendGrid handles it differently
                if logo_path and not use_api:
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

                # Adjuntar PDF Estado de Cuenta (RC-FEAT-040)
                if not use_api:
                    pdf_data   = msg_data.get('pdf_bytes')
                    pdf_name   = msg_data.get('pdf_filename', 'EstadoCuenta.pdf')
                    if pdf_data:
                        try:
                            from email.mime.application import MIMEApplication
                            pdf_part = MIMEApplication(pdf_data, _subtype="pdf")
                            pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_name)
                            msg.attach(pdf_part)
                            stats['log'].append(f"📄 [RunID:{run_id}] PDF_ATTACHED: {pdf_name} ({len(pdf_data)} bytes)")
                        except Exception as e_pdf:
                            stats['log'].append(f"⚠️ [RunID:{run_id}] No se pudo adjuntar PDF: {e_pdf}")

                # Log PRE-SEND (Forensic)
                stats['log'].append(f"📡 [RunID:{run_id}] SEND_CALL #{send_call_index} PREPARE -> To: {msg_data['email']} | MsgID: {msg_id}")
                
                # --- RC-BUG-009: Explicit Envelope Deduplication ---
                # Use normalized list from above
                all_recipients = all_recipients_clean
                unique_envelope_recipients = list(set(email.lower() for email in all_recipients))
                
                # --- RC-FEAT-013 & 014: Internal Copies + QA Logic (Strict Separation) ---
                copies_log_info = ""
                
                if not is_qa_mode:
                    # --- [MODE=PROD] ---
                    # Load PROD Copies
                    cfg_copies = internal_copies_config or {}
                    prod_cc_raw = helpers.normalize_emails(cfg_copies.get('cc_list', []))
                    prod_bcc_raw = helpers.normalize_emails(cfg_copies.get('bcc_list', []))
                    
                    # 1. Update Envelope (Add to unique recipients)
                    added_cc = 0
                    added_bcc = 0
                    
                    for e in prod_cc_raw:
                        if e.lower() not in unique_envelope_recipients:
                            unique_envelope_recipients.append(e.lower())
                            added_cc += 1
                            
                    for e in prod_bcc_raw:
                        if e.lower() not in unique_envelope_recipients:
                            unique_envelope_recipients.append(e.lower())
                            added_bcc += 1
                    
                    # 2. Set PROD Headers
                    if prod_cc_raw:
                        msg['Cc'] = ", ".join(prod_cc_raw)
                        
                    if added_cc > 0 or added_bcc > 0:
                        copies_log_info = f"[MODE=PROD] Added: {added_cc} CC, {added_bcc} BCC"
                    else:
                        copies_log_info = "[MODE=PROD] No copies"
                        
                else:
                    # --- [MODE=QA] ---
                    # Strictly use QA Lists. Ignore Prod Copies entirely.
                    # Envelope = QA_TO (already set) + QA_CC + QA_BCC
                    
                    qa_cc = helpers.normalize_emails(qa_settings.get('cc_recipients', []))
                    qa_bcc = helpers.normalize_emails(qa_settings.get('bcc_recipients', []))
                    
                    # 1. Update Envelope
                    added_cc_qa = 0
                    added_bcc_qa = 0
                    for e in qa_cc:
                        if e.lower() not in unique_envelope_recipients:
                            unique_envelope_recipients.append(e.lower())
                            added_cc_qa += 1
                    for e in qa_bcc:
                        if e.lower() not in unique_envelope_recipients:
                            unique_envelope_recipients.append(e.lower())
                            added_bcc_qa += 1
                            
                    # 2. Set QA Headers
                    if qa_cc:
                        msg['Cc'] = ", ".join(qa_cc)
                        
                    copies_log_info = f"[MODE=QA] Added: {added_cc_qa} CC, {added_bcc_qa} BCC"
                
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

                # --- DELIVERY BRANCH ---
                if use_api:
                    # API Delivery (Resend or SendGrid)
                    try:
                        if use_resend:
                            # Resend API Delivery
                            params = {
                                "from": smtp_config['user'],
                                "to": unique_envelope_recipients,
                                "subject": msg_data['subject'],
                                "html": msg_data['html_body']
                            }

                            attachments = []
                            # Logo inline
                            if logo_path:
                                with open(logo_path, 'rb') as f:
                                    logo_data = f.read()
                                attachments.append({
                                    "filename": "logo.png",
                                    "content": list(logo_data)
                                })
                            # PDF adjunto (RC-FEAT-040)
                            pdf_data = msg_data.get('pdf_bytes')
                            pdf_name = msg_data.get('pdf_filename', 'EstadoCuenta.pdf')
                            if pdf_data:
                                attachments.append({
                                    "filename": pdf_name,
                                    "content": list(pdf_data)
                                })
                            if attachments:
                                params["attachments"] = attachments

                            response = resend.Emails.send(params)
                            stats['log'].append(f"[{i+1}/{total}] ✅ [API] Enviado vía Resend (ID: {response.get('id', 'N/A')})")
                        
                        elif use_sendgrid:
                            # SendGrid API Delivery
                            message = Mail(
                                from_email=smtp_config['user'],
                                to_emails=unique_envelope_recipients,
                                subject=msg_data['subject'],
                                html_content=msg_data['html_body']
                            )

                            if logo_path:
                                with open(logo_path, 'rb') as f:
                                    encoded_file = base64.b64encode(f.read()).decode()
                                attached_file = Attachment(
                                    FileContent(encoded_file),
                                    FileName('logo.png'),
                                    FileType('image/png'),
                                    Disposition('inline'),
                                    ContentId('logo_dacta')
                                )
                                message.add_attachment(attached_file)

                            # PDF adjunto (RC-FEAT-040)
                            pdf_data = msg_data.get('pdf_bytes')
                            pdf_name = msg_data.get('pdf_filename', 'EstadoCuenta.pdf')
                            if pdf_data:
                                pdf_att = Attachment(
                                    FileContent(base64.b64encode(pdf_data).decode()),
                                    FileName(pdf_name),
                                    FileType('application/pdf'),
                                    Disposition('attachment'),
                                )
                                message.add_attachment(pdf_att)

                            response = sg_client.send(message)
                            stats['log'].append(f"[{i+1}/{total}] ✅ [API] Enviado vía SendGrid (Status: {response.status_code})")
                    except Exception as e_api:
                        api_name = "Resend" if use_resend else "SendGrid"
                        raise Exception(f"{api_name} API Error: {e_api}")
                else:
                    # Standard SMTP Delivery
                    # IMPORTANTE: Pasamos to_addrs explícitamente para que el Envelope incluya BCC (invisible en headers).
                    server.send_message(msg, from_addr=smtp_config['user'], to_addrs=unique_envelope_recipients)

                # Log POST-SEND (Forensic)
                stats['log'].append(f"✅ [RunID:{run_id}] SEND_CALL #{send_call_index} SUCCESS -> Sent OK")
                
                # 4. Update Ledger (Confirm Sent)
                reason = "USER_RESEND" if force_resend else "NORMAL"
                if not is_qa_mode and copies_log_info:
                    reason += "_wCOPIES"
                
                db_manager.log_attempt(recipient_ledger, 'SENT', run_id, ledger_key, reason=reason)
                
                
                stats['success'] += 1
                stats['log'].append(f"[{i+1}/{total}] Enviado a {msg_data['client_name']} ({msg_data['email']})")
                
                # Detail Entry (Success)
                stats['details'].append({
                    'msg_id': msg_data.get('msg_id'),  # NUEVO: Para matching en app.py
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
                db_manager.log_attempt(recipient_ledger, 'FAILED', run_id, ledger_key, reason=str(e)[:100])

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
        
        if server:
            server.quit()
        
    except smtplib.SMTPAuthenticationError:
        err_msg = "❌ Error de Autenticación (535). \nSi usas Gmail, NECESITAS activar 'Verificación en 2 pasos' y generar una 'Contraseña de Aplicación'. Tu contraseña normal de Google NO funcionará."
        stats['log'].append(err_msg)
        stats['failed'] = len(messages)
    except Exception as e:
        stats['log'].append(f"❌ Error de Conexión SMTP: {str(e)}")
        stats['failed'] = len(messages)
        
    return stats


def test_smtp_connectivity(smtp_config):
    """Diagnóstico rápido de conectividad SMTP o API Bridge para la UI."""
    import socket
    import smtplib
    log = []
    
    # 0. API BRIDGE CHECK (Priority)
    resend_key = smtp_config.get('resend_api_key', '')
    sg_key = smtp_config.get('sendgrid_api_key', '')
    force_smtp = smtp_config.get('force_smtp', False)
    
    if resend_key and HAS_RESEND and not force_smtp:
        log.append("🚀 [Modo] Detectada API Key de Resend. Probando conexión API (Puerto 443)...")
        try:
            log.append("🌐 Verificando acceso HTTPS a API Resend...")
            socket.create_connection(("resend.com", 443), timeout=5)
            log.append("✅ [Red] Acceso a resend.com:443 OK.")
            return {'ok': True, 'msg': "✅ Conexión Exitosa vía API Bridge (Resend). El bloqueo SMTP de Railway NO afectará tus envíos.", 'log': log}
        except Exception as e_api:
            log.append(f"❌ [API] Error conectando a Resend: {e_api}")
            return {'ok': False, 'msg': f"Falla de API Resend: {e_api}", 'log': log}
            
    elif sg_key and HAS_SENDGRID and not force_smtp:
        log.append("🚀 [Modo] Detectada API Key de SendGrid. Probando conexión API (Puerto 443)...")
        try:
            log.append("🌐 Verificando acceso HTTPS a API SendGrid...")
            socket.create_connection(("api.sendgrid.com", 443), timeout=5)
            log.append("✅ [Red] Acceso a api.sendgrid.com:443 OK.")
            return {'ok': True, 'msg': "✅ Conexión Exitosa vía API Bridge (SendGrid). El bloqueo SMTP de Railway NO afectará tus envíos.", 'log': log}
        except Exception as e_api:
            log.append(f"❌ [API] Error conectando a SendGrid: {e_api}")
            return {'ok': False, 'msg': f"Falla de API SendGrid: {e_api}", 'log': log}

    # If no API key, proceed with SMTP Standard
    try:
        host = smtp_config.get('server', 'smtp.gmail.com')
        port = int(smtp_config.get('port', 465))
        
        # 0. Red General
        log.append("🌐 Verificando acceso general a Internet (Port 443)...")
        try:
            socket.create_connection(("google.com", 443), timeout=5)
            log.append("✅ [Red] Acceso a google.com:443 OK.")
        except Exception as e:
            log.append(f"❌ [Red] No hay acceso a google.com:443: {e}")
            log.append("🚨 Esto indica que la red de Railway está restringida o no tiene salida.")

        # 1. DNS
        ip = None
        try:
            ip = socket.gethostbyname(host)
            log.append(f"🔍 [DNS] OK: {host} -> {ip}")
        except:
            ip = "142.251.2.108" # Fallback literal
            log.append(f"⚠️ [DNS] FALLÓ resolución. Usando Fallback IP: {ip}")
            
        # 2. Conexión TCP SMTP
        log.append(f"🔌 Intentando conexión a {ip}:{port}...")
        try:
            if str(port) == "465":
                server = smtplib.SMTP_SSL(ip, port, timeout=12)
            else:
                server = smtplib.SMTP(ip, port, timeout=12)
                server.ehlo()
                if server.has_extn('starttls'):
                    server.starttls()
                    server.ehlo()
            log.append(f"✅ [SMTP] Conexión TCP a Puerto {port} establecida.")
        except Exception as e:
            log.append(f"❌ [SMTP] Falla de Conexión a Puerto {port}: {e}")
            if str(port) == "465":
                log.append("💡 TIP: Railway a veces bloquea el puerto 465. Prueba con el puerto 587.")
            else:
                log.append("💡 TIP: Verifica si tu cuenta de Railway tiene restricciones de salida (Egress).")
            return {'ok': False, 'msg': f"Falla de Red/Puerto {port}: {e}", 'log': log}
            
        # 3. Login
        try:
            user = str(smtp_config.get('user', '')).strip()
            password = str(smtp_config.get('password', '')).replace(' ', '').strip()
            if not user or not password:
                return {
                    'ok': False,
                    'msg': "Faltan credenciales SMTP (usuario/contraseña). Guarda SMTP o define SMTP_USER/SMTP_PASSWORD en el entorno.",
                    'log': log,
                }
            server.login(user, password)
            log.append("✅ [Auth] Autenticación Exitosa.")
            server.quit()
            return {'ok': True, 'msg': "Conexión y credenciales válidas.", 'log': log}
        except Exception as e:
            log.append(f"❌ [Auth] Error: {e}")
            return {'ok': False, 'msg': f"Falla de Login: {e}", 'log': log}
            
    except Exception as ge:
        return {'ok': False, 'msg': f"Error inesperado: {ge}", 'log': log}
