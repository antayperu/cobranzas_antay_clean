import streamlit as st
import pandas as pd
import os
import hashlib
import base64
from datetime import datetime, date, timedelta, time as dtime
import streamlit.components.v1 as components
import utils.email_sender as es
import utils.helpers as helpers
import utils.ui.styles as styles
import utils.db_manager as dbm
import utils.storage_manager as storage_mgr
from utils.pdf_report import EstadoCuentaCliente

_CDN = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174"


def _build_pdf_js_html(b64: str) -> str:
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#525659;display:flex;flex-direction:column;align-items:center;
       padding:14px 10px;gap:10px;font-family:sans-serif;overflow-y:auto}}
  canvas{{display:block;max-width:100%;box-shadow:0 3px 16px rgba(0,0,0,.45);background:#fff}}
  #msg{{color:#ccc;font-size:13px;padding:40px 0;text-align:center;letter-spacing:.02em}}
</style>
</head>
<body>
<div id="msg">⏳ Cargando vista previa…</div>
<script src="{_CDN}/pdf.min.js" crossorigin="anonymous"></script>
<script>
(function(){{
  var WORKER='{_CDN}/pdf.worker.min.js';
  try{{
    var blob=new Blob(['importScripts("'+WORKER+'");'],{{type:'application/javascript'}});
    pdfjsLib.GlobalWorkerOptions.workerSrc=URL.createObjectURL(blob);
  }}catch(e){{pdfjsLib.GlobalWorkerOptions.workerSrc=WORKER;}}
  var b64="{b64}";
  var raw=atob(b64),buf=new Uint8Array(raw.length);
  for(var i=0;i<raw.length;i++)buf[i]=raw.charCodeAt(i);
  pdfjsLib.getDocument({{data:buf,cMapUrl:'{_CDN}/cmaps/',cMapPacked:true,
    standardFontDataUrl:'{_CDN}/standard_fonts/'}}).promise.then(function(pdf){{
    document.getElementById('msg').remove();
    var scale=Math.min(1.55,(window.innerWidth-28)/595);
    function renderPage(n){{
      pdf.getPage(n).then(function(page){{
        var vp=page.getViewport({{scale:scale}});
        var canvas=document.createElement('canvas');
        canvas.width=vp.width;canvas.height=vp.height;
        document.body.appendChild(canvas);
        return page.render({{canvasContext:canvas.getContext('2d'),viewport:vp}}).promise;
      }}).then(function(){{if(n<pdf.numPages)renderPage(n+1);}});
    }}
    renderPage(1);
  }}).catch(function(e){{
    var m=document.getElementById('msg');
    m.style.color='#ff8080';
    m.textContent='⚠️ No se pudo renderizar el PDF.';
    var br=document.createElement('br');
    var sm=document.createElement('small');
    sm.textContent=e.message||'Error desconocido';
    m.appendChild(br);m.appendChild(sm);
  }});
}})();
</script>
</body></html>"""


def _resolve_runtime_logo(config):
    logo_path = storage_mgr.resolve_logo_path(config)
    if not logo_path:
        assets_dir = os.path.join(os.getcwd(), "assets")
        fallback_candidates = [
            os.path.join(assets_dir, "logo_dacta_processed.png"),
            os.path.join(assets_dir, "logo_dacta.png"),
        ]
        for candidate in fallback_candidates:
            if os.path.exists(candidate):
                logo_path = candidate
                break
    if logo_path and os.path.exists(logo_path):
        config["logo_path"] = logo_path
        return logo_path
    return None

def render_tab(df_final, df_filtered, config):
    """
    Renders the Email Notifications tab.
    
    Args:
        df_final (pd.DataFrame): The master dataframe (SSOT).
        df_filtered (pd.DataFrame): The filtered dataframe from the Report tab.
        config (dict): Global configuration.
    """
    st.subheader("Gestión de Correos")
    
    if not df_final.empty:
        # --- Renderizar Reporte Post-Envío si existe en session_state ---
        if 'last_send_results' in st.session_state and st.session_state['last_send_results']:
            results = st.session_state['last_send_results']
            
            st.success("✅ Envío completado. Resultados del último proceso:")
            
            # --- RC-UX-002: Panel de Resultados Amigable ---
            st.divider()
            st.subheader("📊 Resumen del Proceso")
            
            # A) Resumen Ejecutivo (Métricas)
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Enviados", results['success'])
            c2.metric("❌ Fallidos", results['failed'])
            c3.metric("🔒 Bloqueados (TTL)", results.get('blocked', 0))
            
            # B) Tabla de Detalles (Negocio)
            if 'details' in results and results['details']:
                df_res = pd.DataFrame(results['details'])
                
                st.write("📝 **Detalle por Cliente:**")
                st.dataframe(
                    df_res[['Cliente', 'Email', 'Estado', 'Detalle']], 
                    use_container_width=True,
                    hide_index=True
                )
                
                # Botón descarga
                csv = df_res.to_csv(index=False).encode('utf-8')
                batch_id = st.session_state.get('last_processed_batch_id', 'unknown')
                st.download_button(
                    "📄 Descargar Reporte de Envío (CSV)",
                    data=csv,
                    file_name=f"reporte_envio_{batch_id[:8]}.csv",
                    mime="text/csv"
                )
            
            # Botón para cerrar el reporte
            if st.button("✅ Cerrar Reporte"):
                del st.session_state['last_send_results']
                st.rerun()
            
            st.divider()
        st.caption("La trazabilidad y el historial de notificaciones ahora se gestionan en la TAB 'Centro de Gestiones'.")
        
        c_mail1, c_mail2 = st.columns([1, 1])
        
        with c_mail1:
            st.markdown("##### Destinatarios")
            
            if 'EMAIL_FINAL' in df_filtered.columns:
                # RC-FIX-FILTER: Include clients with Pending Detractions even if Balance is 0
                # FIX E2E: Usar df_filtered (vista filtrada) en lugar de df_final (dataset completo)
                # para respetar los filtros aplicados en Reporte General
                
                # 1. Helper for aggregation (Detraccion Pendiente Amount) on the filtered view
                # We use a lambda to check ESTADO DETRACCION == 'PENDIENTE'
                df_email_view = df_filtered.copy()  # Trabajar sobre vista filtrada
                df_email_view['DETR_PENDIENTE_AMOUNT'] = df_email_view.apply(
                    lambda x: float(x['DETRACCIÓN']) if str(x['ESTADO DETRACCION']).upper().strip() == 'PENDIENTE' else 0.0,
                    axis=1
                )
                
                client_group_email = df_email_view[df_email_view['EMAIL_FINAL'] != ""].groupby(
                    ['COD CLIENTE', 'EMPRESA', 'EMAIL_FINAL']
                )[['SALDO REAL', 'DETR_PENDIENTE_AMOUNT']].sum().reset_index()
                
                # 2. Relaxed Filter: Balance > 0 OR Detraction > 0
                client_group_email = client_group_email[
                    (client_group_email['SALDO REAL'] > 0.01) | 
                    (client_group_email['DETR_PENDIENTE_AMOUNT'] > 0.01)
                ]
                
                # --- RC-FEAT-UX-EMAIL: Smart Filters & Counters (Tower Integration) ---
                # FIX E2E: NO consultar DB si es fresh_load (nuevo ciclo) para evitar contaminación
                is_fresh_load = st.session_state.get('fresh_load', False)
                
                # --- KPIs de Envío (TAB Notificaciones Email) ---
                # Calcular por COD_CLIENTE único para evitar confusión con emails compartidos
                today_str = date.today().strftime('%Y-%m-%d')
                cycle_id = config.get('cycle_id') or st.session_state.get('cycle_id')
                clientes_enviados_hoy = set()
                clientes_enviados_hoy_count = 0
                if cycle_id:
                    try:
                        clientes_enviados_hoy = dbm.get_clientes_email_enviados_hoy(cycle_id, today_str)
                        clientes_enviados_hoy_count = len(clientes_enviados_hoy)
                    except Exception as e:
                        st.warning(f"Error consultando enviados hoy: {e}")
                
                # --- Filtrar clientes disponibles (Lógica Movida ANTES de mostrar KPIs) ---
                # Layout de columnas para KPIs y Controles
                c_stat1, c_stat2, c_ctrl = st.columns([1, 1, 2])
                
                hide_sent_today = c_ctrl.toggle("🙈 Ocultar ya enviados hoy", value=True, help="Oculta de la lista los clientes que ya recibieron correo hoy.")
                
                if hide_sent_today and clientes_enviados_hoy:
                    # Filtrar: excluir clientes enviados hoy según notificaciones reales
                    client_group_email = client_group_email[~client_group_email['COD CLIENTE'].isin(clientes_enviados_hoy)]
                
                # --- Calcular KPIs con la lista FINAL filtrada ---
                # Total de clientes disponibles (coincide con opciones del multiselect)
                total_clientes_disponibles = len(client_group_email)
                pendientes_envio_count = total_clientes_disponibles
                
                # Mostrar KPIs (Ahora sí sincronizados con el multiselect)
                c_stat1.metric("⏳ Pendientes de Envío", pendientes_envio_count)
                c_stat2.metric("📧 Enviados Hoy", clientes_enviados_hoy_count)
                
                st.markdown("---")
                
                email_options = []
                email_map = {}
                
                for idx, row in client_group_email.iterrows():
                    # Calcular desglose por moneda para el label
                    cod_cli = row['COD CLIENTE']
                    docs_cli_temp = df_final[df_final['COD CLIENTE'] == cod_cli]
                    
                    s_temp = docs_cli_temp[docs_cli_temp['MONEDA'].astype(str).str.startswith('S', na=False)]['SALDO REAL'].sum()
                    d_temp = docs_cli_temp[~docs_cli_temp['MONEDA'].astype(str).str.startswith('S', na=False)]['SALDO REAL'].sum()
                    
                    # Label Mejorado: EMPRESA (Email...) | S/ 100 | $ 50
                    # RC-UX-MULTI: Visual Truncation for long lists
                    email_display = str(row['EMAIL_FINAL'])
                    if len(email_display) > 50:
                        email_display = email_display[:47] + "..."
                        
                    label_parts = [f"{row['EMPRESA']} ({email_display})"]
                    if s_temp > 0: label_parts.append(f"S/ {s_temp:,.2f}")
                    if d_temp > 0: label_parts.append(f"$ {d_temp:,.2f}")
                    
                    # RC-UX-DETR: Show detraction explicitly if Saldo is 0 or low
                    detr_pend = row['DETR_PENDIENTE_AMOUNT']
                    if detr_pend > 0.01:
                            label_parts.append(f"Detr: S/ {detr_pend:,.2f}")
                    
                    label = " | ".join(label_parts)
                    
                    email_options.append(label)
                    email_map[label] = {
                        'cod': row['COD CLIENTE'],
                        'email': row['EMAIL_FINAL'],
                        'empresa': row['EMPRESA'],
                        'deb_s': s_temp,
                        'deb_d': d_temp
                    }
                
                # --- FIX SELECT ALL: Usar Session State ---
                if "email_sel_key" not in st.session_state:
                        st.session_state["email_sel_key"] = []
                
                # Limpiar selección si las opciones cambiaron (filtros) para evitar crash de Streamlit
                valid_opts_set = set(email_options)
                st.session_state["email_sel_key"] = [x for x in st.session_state["email_sel_key"] if x in valid_opts_set]

                def select_all_callback():
                    st.session_state["email_sel_key"] = email_options

                sel_emails = st.multiselect(
                    f"Seleccione Clientes con Correo ({len(email_options)} disponibles):",
                    options=email_options,
                    key="email_sel_key"
                )
                
                st.button("Seleccionar Todos (Email)", on_click=select_all_callback)
                
                # --- DASHBOARD RESUMEN DE ENVÍO ---
                if sel_emails:
                    st.markdown("---")
                    st.markdown("###### 📊 Resumen de Envío Seleccionado")
                    
                    total_cli_sel = len(sel_emails)
                    total_s_sel = sum(email_map[x]['deb_s'] for x in sel_emails)
                    total_d_sel = sum(email_map[x]['deb_d'] for x in sel_emails)
                    
                    st.markdown("""
                    <style>
                        .stat-box {
                            background-color: #f8f9fa;
                            border: 1px solid #e9ecef;
                            border-radius: 8px;
                            padding: 15px;
                            text-align: center;
                        }
                        .stat-label { font-size: 0.9em; color: #6c757d; margin-bottom: 5px; }
                        .stat-value { font-size: 1.4em; font-weight: bold; color: #2E86AB; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
                        .stat-value svg { margin-right: 5px; }
                    </style>
                    """, unsafe_allow_html=True)

                    k1, k2, k3 = st.columns(3)
                    
                    with k1:
                        st.markdown(f"""
                        <div class="stat-box">
                            <div class="stat-label">Destinatarios</div>
                            <div class="stat-value">👥 {total_cli_sel}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with k2:
                        st.markdown(f"""
                        <div class="stat-box">
                            <div class="stat-label">Total Soles</div>
                            <div class="stat-value" title="S/ {total_s_sel:,.2f}">S/ {total_s_sel:,.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with k3:
                        st.markdown(f"""
                        <div class="stat-box">
                            <div class="stat-label">Total Dólares</div>
                            <div class="stat-value" title="$ {total_d_sel:,.2f}">$ {total_d_sel:,.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("---")

        
        st.markdown("---")

        with c_mail2:
            st.markdown("##### Vista Previa")

            if sel_emails:
                # ── Vista Previa ──────────────────────────────────────────
                logo_path = _resolve_runtime_logo(config)
                cycle_id_prev = st.session_state.get('cycle_id', 'CIC-PREVIEW')
                _single = len(sel_emails) == 1

                for _idx, selected_label in enumerate(sel_emails):
                    info_sel      = email_map[selected_label]
                    docs_cli_mail = df_email_view[df_email_view['COD CLIENTE'] == info_sel['cod']]

                    cover_html = es.generate_cover_email_html(
                        info_sel['empresa'], docs_cli_mail, cycle_id_prev, config
                    )
                    if logo_path:
                        try:
                            with open(logo_path, "rb") as f:
                                enc = base64.b64encode(f.read()).decode()
                            cover_html = cover_html.replace("cid:logo_dacta",
                                                            f"data:image/png;base64,{enc}")
                        except Exception:
                            pass

                    pdf_bytes_prev  = None
                    pdf_preview_b64 = None
                    try:
                        pdf_bytes_prev = EstadoCuentaCliente(
                            empresa=info_sel['empresa'],
                            cod_cliente=info_sel['cod'],
                            cycle_id=cycle_id_prev,
                            docs_df=docs_cli_mail,
                            settings=config,
                            logo_path=logo_path,
                        ).generate()
                        pdf_preview_b64 = base64.b64encode(pdf_bytes_prev).decode()
                    except Exception as e_prev:
                        st.warning(f"⚠️ Preview PDF no disponible para {info_sel['empresa']}: {e_prev}")

                    _slug = "".join(c for c in info_sel['empresa'][:18]
                                    if c.isalnum() or c in " -_").strip().replace(" ", "_")

                    if _single:
                        st.markdown(
                            f"<div style='font-weight:600;font-size:0.97rem;"
                            f"margin-bottom:6px'>✉️ {info_sel['empresa']}</div>",
                            unsafe_allow_html=True,
                        )
                        _ctx = st.container()
                    else:
                        _ctx = st.expander(
                            f"✉️ {info_sel['empresa']}",
                            expanded=(_idx == 0),
                        )

                    with _ctx:
                        if pdf_preview_b64:
                            components.html(
                                _build_pdf_js_html(pdf_preview_b64),
                                height=820,
                                scrolling=True,
                            )
                            st.download_button(
                                label="⬇️ Descargar PDF",
                                data=pdf_bytes_prev,
                                file_name=f"EstadoCuenta_{_slug}_{cycle_id_prev}.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_prev_{info_sel['cod']}",
                                use_container_width=True,
                            )
                        else:
                            st.info("Vista previa del PDF no disponible.")

                        with st.expander("📧 Ver portada del email", expanded=False):
                            components.html(cover_html, height=580, scrolling=True)

                st.markdown("---")

                # ── Protección contra doble envío (RC-BUG-006 & 010) ─────
                current_batch_hash = hash(tuple(sorted(sel_emails)))
                current_batch_id   = f"{len(sel_emails)}_{current_batch_hash}"

                if 'last_processed_batch_id' not in st.session_state:
                    st.session_state['last_processed_batch_id'] = None

                is_processed = (st.session_state['last_processed_batch_id'] == current_batch_id)

                if is_processed:
                    st.info("ℹ️ Este lote ya fue procesado. Para enviar otro, cambie la selección o recargue (F5).")
                    if st.button("🔄 Resetear Bloqueo (Permitir reenvío)"):
                        st.session_state['last_processed_batch_id'] = None
                        st.rerun()

                force_resend_ttl = st.checkbox(
                    "🔄 Habilitar reenvío (Ignorar bloqueo 10min)",
                    help="Marca esto para reenviar intencionalmente una notificación reciente.",
                )

                if st.button("Enviar Correos Masivos", type="primary", disabled=is_processed):
                    if is_processed:
                        st.stop()

                    st.write(f"👷 DEBUG: Iniciando envío... Hash: {current_batch_id} | ForceResend: {force_resend_ttl}")

                    smtp_cfg       = config.get('smtp_config', {})
                    email_user     = smtp_cfg.get('user', '')
                    email_pass     = smtp_cfg.get('password', '')
                    api_key_sg     = smtp_cfg.get('sendgrid_api_key', '')
                    api_key_resend = smtp_cfg.get('resend_api_key', '')

                    has_creds = email_user and (email_pass or api_key_sg or api_key_resend)

                    if not has_creds:
                        st.error("❌ Faltan credenciales. Configura SMTP (Usuario/Pass) o API Bridge (Resend/SendGrid Key) en 'Configuración'.")
                    else:
                        qa_cfg     = config.get('qa_config', {})
                        qa_enabled = qa_cfg.get('enabled', False)

                        if qa_enabled:
                            st.warning(f"🧪 MODO QA ACTIVO: Redirección a lista de pruebas ({len(qa_cfg.get('recipients', []))} destinos).")
                        else:
                            int_copies = config.get('internal_copies', {})
                            n_cc  = len(helpers.normalize_emails(int_copies.get('cc_list', [])))
                            n_bcc = len(helpers.normalize_emails(int_copies.get('bcc_list', [])))
                            if n_cc > 0 or n_bcc > 0:
                                st.info(f"👥 En Producción: Se enviarán copias internas ({n_cc} CC, {n_bcc} CCO).")

                        messages_to_send  = []
                        seen_emails_batch = set()
                        current_cycle_id  = st.session_state.get('cycle_id', 'default_cycle')
                        batch_logo_path   = _resolve_runtime_logo(config)

                        for lbl in sel_emails:
                            info       = email_map[lbl]
                            email_norm = str(info['email']).strip().lower()
                            d_cli      = df_filtered[df_filtered['COD CLIENTE'] == info['cod']]

                            if 'MATCH_KEY' in d_cli.columns:
                                doc_ids = sorted(d_cli['MATCH_KEY'].astype(str).unique())
                                doc_str = "|".join(doc_ids)
                            else:
                                doc_ids = sorted(d_cli['COMPROBANTE'].astype(str).unique()) if 'COMPROBANTE' in d_cli.columns else []
                                doc_str = "|".join(doc_ids)

                            doc_set_fingerprint = hashlib.md5(doc_str.encode()).hexdigest()[:8]
                            tipo_notificacion   = "Email_EstadoCuenta"
                            fecha_corte         = st.session_state.get('config_fecha_corte', date.today())
                            notif_key           = f"{config.get('company_name','Antay')}|{email_norm}|{fecha_corte}|{tipo_notificacion}|{doc_set_fingerprint}"

                            mask_soles = d_cli['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
                            t_s  = d_cli[mask_soles]['SALDO REAL'].sum()
                            t_d  = d_cli[~mask_soles]['SALDO REAL'].sum()
                            str_s = f"S/ {t_s:,.2f}" if t_s > 0 else ""
                            str_d = f"$ {t_d:,.2f}" if t_d > 0 else ""

                            try:
                                pdf_bytes_client = EstadoCuentaCliente(
                                    empresa=info['empresa'],
                                    cod_cliente=info['cod'],
                                    cycle_id=current_cycle_id,
                                    docs_df=d_cli,
                                    settings=config,
                                    logo_path=batch_logo_path,
                                ).generate()
                            except Exception as e_pdf_gen:
                                st.error(f"❌ No se pudo generar PDF para {info['empresa']}: {e_pdf_gen}. Cliente omitido del envío.")
                                _errs = st.session_state.get('_pdf_gen_errors', [])
                                _errs.append(info['empresa'])
                                st.session_state['_pdf_gen_errors'] = _errs
                                continue

                            empresa_slug  = "".join(c for c in info['empresa'][:20] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
                            pdf_filename  = f"EstadoCuenta_{empresa_slug}_{current_cycle_id}.pdf"
                            body          = es.generate_cover_email_html(info['empresa'], d_cli, current_cycle_id, config)
                            plain_body    = es.generate_plain_text_body(info['empresa'], d_cli, str_s, str_d, config)
                            company_sender = config.get('company_name', 'DACTA S.A.C.')
                            subject_line   = f"Estado de Cuenta {company_sender} | Cliente: {info['empresa']}"

                            match_keys_for_client = d_cli['MATCH_KEY'].tolist() if 'MATCH_KEY' in d_cli.columns else []

                            if 'COMPROBANTE' in d_cli.columns:
                                docs_unicos = sorted(d_cli['COMPROBANTE'].astype(str).dropna().unique().tolist())
                            else:
                                docs_unicos = []
                            single_documento_numero = docs_unicos[0] if len(docs_unicos) == 1 else None

                            import uuid
                            msg_unique_id = str(uuid.uuid4())[:8]

                            messages_to_send.append({
                                'msg_id':           msg_unique_id,
                                'email':            info['email'],
                                'client_name':      info['empresa'],
                                'cod_cliente':      info['cod'],
                                'match_keys':       match_keys_for_client,
                                'subject':          subject_line,
                                'html_body':        body,
                                'plain_body':       plain_body,
                                'pdf_bytes':        pdf_bytes_client,
                                'pdf_filename':     pdf_filename,
                                'notification_key': notif_key,
                                'original_email':   info['email'],
                                'documento_numero': single_documento_numero,
                            })

                        selected_cod_clientes = [email_map[lbl]['cod'] for lbl in sel_emails]
                        st.session_state['last_send_selected_cod'] = selected_cod_clientes

                        with st.spinner(f"Enviando con Business Lock (Fecha: {fecha_corte})..."):
                            results = es.send_email_batch(
                                smtp_cfg,
                                messages_to_send,
                                progress_callback=lambda i, t, m: st.toast(f"{m} ({i}/{t})"),
                                logo_path=batch_logo_path,
                                force_resend=force_resend_ttl,
                                internal_copies_config=config.get('internal_copies', {}),
                                qa_settings=None,
                                cycle_id=current_cycle_id,
                            )

                        persisted_events = 0
                        persist_errors   = 0
                        if 'details' in results and results['details']:
                            msg_lookup = {m.get('msg_id'): m for m in messages_to_send if m.get('msg_id')}
                            for detail in results['details']:
                                status_label = str(detail.get('Estado', '')).upper()
                                if 'ENVIADO' in status_label:
                                    status_code = 'SENT'
                                elif 'BLOQUE' in status_label:
                                    status_code = 'BLOCKED'
                                elif 'FALL' in status_label or 'ERROR' in status_label:
                                    status_code = 'FAILED'
                                else:
                                    status_code = 'PENDING'

                                detail_msg_id = detail.get('msg_id')
                                msg_ctx = msg_lookup.get(detail_msg_id)
                                if msg_ctx is None:
                                    sent_client = detail.get('Cliente')
                                    msg_ctx = next(
                                        (m for m in messages_to_send if m.get('client_name') == sent_client),
                                        None,
                                    )

                                cliente_id_ctx  = str(msg_ctx.get('cod_cliente')).strip() if msg_ctx and msg_ctx.get('cod_cliente') else None
                                destinatario_ctx = (
                                    msg_ctx.get('original_email')
                                    if msg_ctx and msg_ctx.get('original_email')
                                    else detail.get('Email', '')
                                )
                                asunto_ctx = (
                                    msg_ctx.get('subject')
                                    if msg_ctx and msg_ctx.get('subject')
                                    else f"Estado de Cuenta {config.get('company_name', 'Antay')}"
                                )
                                mensaje_ctx    = str(detail.get('Detalle') or '')
                                documento_id_ctx = None
                                if msg_ctx and cliente_id_ctx and msg_ctx.get('documento_numero'):
                                    documento_id_ctx = dbm.get_documento_id_by_numero(
                                        cliente_id=cliente_id_ctx,
                                        numero_documento=str(msg_ctx.get('documento_numero')),
                                    )

                                ok_persist = dbm.persist_notification_event(
                                    cliente_id=cliente_id_ctx,
                                    destinatario=str(destinatario_ctx),
                                    asunto=str(asunto_ctx),
                                    mensaje=mensaje_ctx,
                                    status_code=status_code,
                                    run_id=str(current_batch_id),
                                    notification_key=(msg_ctx.get('notification_key') if msg_ctx else None),
                                    match_keys=(msg_ctx.get('match_keys') if msg_ctx else None),
                                    documento_id=documento_id_ctx,
                                    cycle_id=current_cycle_id,
                                    metadata_extra={
                                        "ui_batch_id": str(current_batch_id),
                                        "msg_id": detail_msg_id,
                                    },
                                )
                                if ok_persist:
                                    persisted_events += 1
                                else:
                                    persist_errors += 1

                        if persist_errors > 0:
                            st.warning(f"No se pudieron guardar {persist_errors} eventos en notificaciones.")
                            st.caption(dbm.get_last_error() or "")
                        elif persisted_events > 0:
                            st.caption(f"Notificaciones persistidas en BD: {persisted_events}")

                        if results['success'] > 0:
                            st.session_state['last_processed_batch_id'] = current_batch_id

                            if 'details' in results and results['details']:
                                now_timestamp    = datetime.now()
                                updated_match_keys = []
                                msg_lookup = {m.get('msg_id'): m for m in messages_to_send if m.get('msg_id')}

                                for detail in results['details']:
                                    if detail.get('Estado') == '✅ Enviado':
                                        msg_id_sent = detail.get('msg_id')
                                        if msg_id_sent and msg_id_sent in msg_lookup:
                                            msg = msg_lookup[msg_id_sent]
                                        else:
                                            sent_client = detail.get('Cliente')
                                            msg = next((m for m in messages_to_send if m['client_name'] == sent_client), None)

                                        if msg and msg.get('match_keys'):
                                            cod_cliente_msg = msg.get('cod_cliente')
                                            for mk in msg['match_keys']:
                                                mask = (
                                                    (st.session_state['df_final']['MATCH_KEY'] == mk) &
                                                    (st.session_state['df_final']['COD CLIENTE'] == cod_cliente_msg)
                                                )
                                                if mask.sum() > 0:
                                                    st.session_state['df_final'].loc[mask, 'ESTADO_EMAIL'] = "ENVIADO"
                                                    st.session_state['df_final'].loc[mask, 'FECHA_ULTIMO_ENVIO'] = now_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                                                    if 'ESTADO_ENVIO_TEXTO' in st.session_state['df_final'].columns:
                                                        st.session_state['df_final'].loc[mask, 'ESTADO_ENVIO_TEXTO'] = f"ENVIADO ({now_timestamp.strftime('%H:%M')})"
                                                    updated_match_keys.append(mk)

                                if updated_match_keys:
                                    dbm.update_estados_email_in_cycle(
                                        cycle_id=st.session_state.get('cycle_id'),
                                        match_keys=updated_match_keys,
                                        fecha=now_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                    )

                                df_final_updated = st.session_state['df_final']
                                df_filtered_new  = df_final_updated.copy()

                                if 'filter_empresa' in st.session_state and st.session_state['filter_empresa']:
                                    selected_empresas = st.session_state['filter_empresa']
                                    if selected_empresas:
                                        df_filtered_new = df_filtered_new[df_filtered_new['EMPRESA'].isin(selected_empresas)]

                                if st.session_state.get('filter_solo_con_correo', False):
                                    df_filtered_new = df_filtered_new[df_filtered_new['CORREO'].notna() & (df_filtered_new['CORREO'] != '')]

                                st.session_state['df_filtered'] = df_filtered_new
                                st.session_state['last_tracking_update'] = {
                                    'count':       len(updated_match_keys),
                                    'timestamp':   now_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                    'sample_keys': updated_match_keys[:3] if updated_match_keys else [],
                                }
                                st.session_state['fresh_load']         = False
                                st.session_state['tracking_dirty']     = True
                                st.session_state['last_send_results']  = results
                                st.session_state['last_send_timestamp'] = now_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                                st.rerun()

                        st.divider()
                        st.subheader("📊 Resumen del Proceso")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("✅ Enviados",          results['success'])
                        c2.metric("❌ Fallidos",          results['failed'])
                        c3.metric("🔒 Bloqueados (TTL)", results.get('blocked', 0))

                        if 'details' in results and results['details']:
                            df_res = pd.DataFrame(results['details'])
                            st.write("📝 **Detalle por Cliente:**")
                            st.dataframe(df_res[['Cliente', 'Email', 'Estado', 'Detalle']], use_container_width=True, hide_index=True)

                            qa_cfg_active = config.get('qa_config', {})
                            if qa_cfg_active.get('enabled', False):
                                st.info("ℹ️ Modo QA Activo: Los correos mostrados arriba son los de QA. Abajo el mapeo original.")
                                orig_map = {m['client_name']: m['original_email'] for m in messages_to_send}
                                df_res['Email Original'] = df_res['Cliente'].map(orig_map)
                                st.dataframe(df_res[['Cliente', 'Email Original', 'Email', 'Estado']], use_container_width=True, hide_index=True)

                            csv = df_res.to_csv(index=False).encode('utf-8')
                            st.download_button("📄 Descargar Reporte de Envío (CSV)", data=csv, file_name=f"reporte_envio_{current_batch_id[:8]}.csv", mime="text/csv")

                        with st.expander("🛠️ Avanzado (QA / Soporte Técnico)", expanded=False):
                            st.write(f"RunID: {current_batch_id}")
                            if 'last_tracking_update' in st.session_state:
                                update_info = st.session_state['last_tracking_update']
                                st.success(f"✅ Tracking actualizado: {update_info['count']} documentos")
                            st.markdown("---")
                            for l in results['log']:
                                st.text(l)
                                if "535" in l:
                                    st.error("Error 535: Revisa tu contraseña de aplicación de Gmail.")

                # ── Programar envío para después ──────────────────────────
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                with st.expander("⏰ Programar envío para después", expanded=False):
                    st.markdown(
                        "<small>Elige una fecha y hora para enviar estos correos automáticamente. "
                        "La app te avisará cuando llegue el momento para que confirmes antes de enviar.</small>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

                    _today = date.today()
                    _weekday = _today.weekday()
                    if _weekday >= 5:
                        _default_date = _today + timedelta(days=7 - _weekday)
                    else:
                        _default_date = _today

                    _col_d, _col_t = st.columns(2)
                    with _col_d:
                        _sched_date = st.date_input(
                            "📅 Fecha de envío",
                            value=_default_date,
                            min_value=_today,
                            key="sched_email_date",
                        )
                    with _col_t:
                        _sched_time = st.time_input(
                            "🕐 Hora de envío",
                            value=dtime(8, 0),
                            key="sched_email_time",
                            step=1800,
                        )

                    if _sched_date.weekday() >= 5:
                        st.warning("⚠️ Fecha en fin de semana. Considera elegir un día hábil.")

                    _sched_dt = datetime.combine(_sched_date, _sched_time)
                    _day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                    st.caption(
                        f"Envío programado para el **{_day_names[_sched_date.weekday()]} "
                        f"{_sched_dt.strftime('%d/%m/%Y')} a las {_sched_dt.strftime('%H:%M')}** "
                        f"· {len(sel_emails)} cliente(s)"
                    )

                    if st.button("📅 Guardar programación", type="secondary",
                                 use_container_width=True, key="btn_schedule_email"):
                        _clientes_prog = [
                            {"cod": email_map[lbl]['cod'],
                             "empresa": email_map[lbl]['empresa'],
                             "email": email_map[lbl]['email']}
                            for lbl in sel_emails
                        ]
                        _cycle_id_sched = st.session_state.get('cycle_id', 'CIC-UNKNOWN')
                        _sched_id = dbm.schedule_email_send(
                            cycle_id=_cycle_id_sched,
                            clientes=_clientes_prog,
                            scheduled_at=_sched_dt,
                        )
                        if _sched_id:
                            st.success(
                                f"✅ Envío programado para el {_sched_dt.strftime('%d/%m/%Y a las %H:%M')} "
                                f"con {len(_clientes_prog)} cliente(s). La app te avisará cuando llegue el momento."
                            )
                        else:
                            st.error("❌ No se pudo guardar la programación. Intente de nuevo.")

            else:
                st.info("Selecciona un cliente para ver la vista previa.")

    else:
        st.info("Sube los archivos y filtra para ver las notificaciones.")

