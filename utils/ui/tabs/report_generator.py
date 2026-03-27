"""
utils/ui/tabs/report_generator.py
Panel UI para generar el Informe Gerencial (RC-FEAT-039).

Renderiza un st.expander al final del Tab Dashboard con:
  - Selector de ciclo
  - Checkboxes de secciones A-E
  - Botón "Descargar PDF"
  - Botón "Enviar al Directorio" (usa SMTP configurado)
"""

from __future__ import annotations

import io
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import streamlit as st

import utils.db_manager as dbm
from utils.pdf_report import InformeGerencial


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_smtp_config(smtp_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Lee la configuración SMTP del Tab Configuración (config['smtp_config'])."""
    cfg = smtp_config or {}
    return {
        "host":     cfg.get("server", ""),
        "port":     int(cfg.get("port", 587) or 587),
        "user":     cfg.get("user", ""),
        "password": cfg.get("password", ""),
        "from":     cfg.get("user", ""),
        "to_list":  st.session_state.get("informe_destinatarios", ""),
    }


def _enviar_pdf_por_email(
    pdf_bytes: bytes,
    filename: str,
    smtp_cfg: Dict[str, Any],
    cycle_id: str,
    empresa: str,
) -> tuple[bool, str]:
    """Envía el PDF adjunto a los destinatarios configurados."""
    to_raw = smtp_cfg.get("to_list", "")
    to_list = [e.strip() for e in to_raw.replace(";", ",").split(",") if e.strip()]
    if not to_list:
        return False, "Sin destinatarios configurados. Agrega los emails del Directorio."

    host = smtp_cfg.get("host", "")
    port = smtp_cfg.get("port", 587)
    user = smtp_cfg.get("user", "")
    pwd  = smtp_cfg.get("password", "")
    from_addr = smtp_cfg.get("from", "") or user

    if not all([host, user, pwd]):
        return False, "Configuración SMTP incompleta. Revisa Tab Configuración."

    try:
        msg = MIMEMultipart()
        msg["From"]    = from_addr
        msg["To"]      = ", ".join(to_list)
        msg["Subject"] = f"Informe Gerencial — {empresa} — Ciclo {cycle_id}"

        body = (
            f"Estimado Directorio,\n\n"
            f"Se adjunta el Informe Gerencial de Cobranzas correspondiente al ciclo {cycle_id}.\n"
            f"Generado el {datetime.now(timezone.utc).strftime('%d/%m/%Y a las %H:%M UTC')} "
            f"por el sistema ReporteCobranzas.\n\n"
            f"Este informe es CONFIDENCIAL. Uso exclusivo del Directorio y Alta Gerencia.\n\n"
            f"— {empresa}"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(attachment)

        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(user, pwd)
            server.sendmail(from_addr, to_list, msg.as_string())

        return True, f"✅ Informe enviado a: {', '.join(to_list)}"
    except Exception as e:
        return False, f"Error al enviar: {e}"


# ---------------------------------------------------------------------------
# Panel principal
# ---------------------------------------------------------------------------

def render_panel_informe(
    current_cycle_id: Optional[str] = None,
    funnel: Optional[Dict[str, Any]] = None,
    criticos: Optional[List[Dict[str, Any]]] = None,
    empresa: str = "DACTA S.A.C.",
    smtp_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Renderiza el panel colapsable 'Generar Informe para Comité de Directorio'.

    Args:
        current_cycle_id: Ciclo activo en el Dashboard (pre-seleccionado).
        funnel:           Dict de get_funnel_cobranza() ya cargado en Dashboard.
        criticos:         List de get_top_clientes_criticos() ya cargado.
        empresa:          Nombre de la empresa para el encabezado del PDF.
        smtp_config:      Dict con claves server/port/user/password del Tab Configuración.
    """
    is_staging = st.session_state.get("IS_STAGING", False)

    with st.expander("📋 Generar Informe para Comité de Directorio", expanded=False):

        st.markdown(
            """
            <div style="background:#F1F5FB;border-left:4px solid #0D3B66;padding:10px 14px;
                        border-radius:0 6px 6px 0;margin-bottom:12px;font-size:0.88rem;">
                Genera un PDF ejecutivo con los datos del ciclo seleccionado,
                listo para presentar al <strong>Comité de Directorio</strong>.
                Incluye semáforo ejecutivo, distribución de cartera, clientes críticos,
                resumen de gestiones y recomendaciones automáticas.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- Alcance del informe ---
        st.markdown("**Alcance del informe:**")
        scope = st.radio(
            "Alcance",
            options=["activa", "general"],
            format_func=lambda x: (
                "🎯 Cartera Activa — solo clientes notificables (Envío Email = SI)"
                if x == "activa"
                else "📋 Cartera General — todos los clientes con deuda"
            ),
            index=0,
            key="informe_scope",
            label_visibility="collapsed",
            help=(
                "Cartera Activa: base de la gestión operativa (clientes con Envío Email = SI). "
                "Cartera General: incluye además los clientes de trato directo."
            ),
        )
        solo_notificable = (scope == "activa")
        st.markdown("---")

        # --- Selector de ciclo ---
        ciclos = dbm.get_ciclos_para_informe(limit=12)
        if not ciclos:
            st.warning("Sin ciclos disponibles en la nube.")
            return

        options_map = {c["label"]: c["cycle_id"] for c in ciclos}
        # Pre-seleccionar el ciclo activo si coincide
        default_idx = 0
        if current_cycle_id:
            for idx, cid in enumerate(options_map.values()):
                if cid == current_cycle_id:
                    default_idx = idx
                    break

        selected_label = st.selectbox(
            "Ciclo a incluir en el informe:",
            list(options_map.keys()),
            index=default_idx,
            key="informe_ciclo_selector",
        )
        selected_cycle = options_map[selected_label]

        # Mostrar detalle del ciclo elegido
        sel_info = next((c for c in ciclos if c["cycle_id"] == selected_cycle), None)
        if sel_info:
            st.caption(
                f"ID: `{sel_info['cycle_id']}` · Corte: {sel_info['fecha_corte']} · "
                f"Archivo: {sel_info['file_ctas']}"
            )

        st.markdown("---")

        # --- Secciones a incluir ---
        st.markdown("**Secciones a incluir:**")
        col1, col2 = st.columns(2)
        with col1:
            sec_a = st.checkbox("A · Semáforo Ejecutivo",           value=True,  key="inf_sec_a")
            sec_b = st.checkbox("B · Aging — Antigüedad de deuda",  value=True,  key="inf_sec_b")
            sec_c = st.checkbox("C · Clientes Críticos",            value=True,  key="inf_sec_c")
        with col2:
            sec_d = st.checkbox("D · Resumen de Gestiones",         value=True,  key="inf_sec_d")
            sec_e = st.checkbox("E · Recomendaciones Automáticas",  value=True,  key="inf_sec_e")
            sec_f = st.checkbox("F · Detalle de Recuperados",        value=False, key="inf_sec_f",
                                help="Lista cada documento cobrado o amortizado entre ciclos (sustento de Tarjeta 2)")

        secciones_sel = set()
        if sec_a: secciones_sel.add("A")
        if sec_b: secciones_sel.add("B")
        if sec_c: secciones_sel.add("C")
        if sec_d: secciones_sel.add("D")
        if sec_e: secciones_sel.add("E")
        if sec_f: secciones_sel.add("F")

        if not secciones_sel:
            st.warning("Selecciona al menos una sección.")
            return

        st.markdown("---")

        # --- Destinatarios para envío por email ---
        with st.expander("📧 Configurar envío al Directorio", expanded=False):
            st.text_input(
                "Emails del Directorio (separados por comas):",
                key="informe_destinatarios",
                placeholder="director1@empresa.com, director2@empresa.com",
                help="Requiere SMTP configurado en Tab Configuración",
            )

        # --- Botones ---
        btn_col1, btn_col2 = st.columns([1, 1])

        with btn_col1:
            generar = st.button(
                "📥  Generar PDF Gerencial",
                type="primary",
                use_container_width=True,
                key="btn_generar_informe",
                help="Genera el PDF y lo prepara para descarga",
            )

        with btn_col2:
            enviar = st.button(
                "📧  Enviar al Directorio",
                type="secondary",
                use_container_width=True,
                key="btn_enviar_informe",
                disabled=is_staging,
                help="Envía el PDF por email (requiere SMTP configurado). Deshabilitado en Staging.",
            )

        if is_staging:
            st.caption("⚠️ Envío por email deshabilitado en el ambiente de pruebas (Staging).")

        # --- Generar PDF ---
        if generar or enviar:
            with st.spinner("Cargando datos del ciclo seleccionado…"):
                # Funnel: reutilizar del Dashboard si coincide el ciclo (tiene cartera y cartera_total)
                if selected_cycle == current_cycle_id and funnel:
                    _funnel = funnel
                else:
                    _funnel = dbm.get_funnel_cobranza(cycle_id=selected_cycle)
                # Criticos y aging: siempre con el filtro de scope correcto
                _criticos = dbm.get_top_clientes_criticos(
                    n=10, cycle_id=selected_cycle, solo_notificable=solo_notificable
                )

            with st.spinner("Obteniendo distribución de cartera y gestiones…"):
                _aging     = dbm.get_aging_distribution(selected_cycle, solo_notificable=solo_notificable)
                _gestiones = dbm.get_resumen_gestiones_ciclo(selected_cycle, solo_notificable=solo_notificable)
                _recovery  = dbm.get_recovery_stats(selected_cycle, solo_notificable=solo_notificable)

            # Sección F — solo si fue seleccionada (query adicional)
            _docs_rec = []
            if "F" in secciones_sel:
                with st.spinner("Cargando detalle de documentos recuperados…"):
                    _docs_rec = dbm.get_docs_recuperados_detalle(
                        selected_cycle, solo_notificable=solo_notificable
                    )

            with st.spinner("Generando PDF…"):
                pdf_bytes = InformeGerencial(
                    cycle_id=selected_cycle,
                    funnel=_funnel,
                    criticos=_criticos,
                    aging=_aging,
                    gestiones=_gestiones,
                    empresa=empresa,
                    secciones=secciones_sel,
                    recovery=_recovery,
                    scope=scope,
                    docs_recuperados=_docs_rec,
                ).generate()

            fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
            filename  = f"InformeGerencial_{selected_cycle}_{fecha_str}.pdf"

            if generar:
                st.download_button(
                    label="⬇️  Descargar PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dl_informe_{fecha_str}",
                )
                st.success(
                    f"✅ PDF generado correctamente · {len(pdf_bytes) / 1024:.0f} KB · "
                    f"{len(secciones_sel)} sección(es) incluidas."
                )

            if enviar and not is_staging:
                smtp_cfg = _load_smtp_config(smtp_config)
                with st.spinner("Enviando por email…"):
                    ok, msg = _enviar_pdf_por_email(
                        pdf_bytes=pdf_bytes,
                        filename=filename,
                        smtp_cfg=smtp_cfg,
                        cycle_id=selected_cycle,
                        empresa=empresa,
                    )
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
