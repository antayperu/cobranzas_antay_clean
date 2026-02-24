import streamlit as st
import pandas as pd
import os
import hashlib
import base64
from datetime import datetime, date, timedelta
import streamlit.components.v1 as components
import utils.email_sender as es
import utils.helpers as helpers
import utils.ui.styles as styles
import utils.db_manager as dbm
import utils.storage_manager as storage_mgr


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
                
                # Contar clientes enviados HOY
                if 'ESTADO_EMAIL' in df_final.columns and 'FECHA_ULTIMO_ENVIO' in df_final.columns:
                    mask_enviado = df_final['ESTADO_EMAIL'] == 'ENVIADO'
                    mask_hoy = df_final['FECHA_ULTIMO_ENVIO'].astype(str).str.startswith(today_str)
                    mask_enviado_hoy = mask_enviado & mask_hoy
                    
                    # COD_CLIENTE únicos enviados hoy
                    clientes_enviados_hoy_count = df_final[mask_enviado_hoy]['COD CLIENTE'].nunique()
                else:
                    clientes_enviados_hoy_count = 0
                
                # --- Filtrar clientes disponibles (Lógica Movida ANTES de mostrar KPIs) ---
                # Layout de columnas para KPIs y Controles
                c_stat1, c_stat2, c_ctrl = st.columns([1, 1, 2])
                
                hide_sent_today = c_ctrl.toggle("🙈 Ocultar ya enviados hoy", value=True, help="Oculta de la lista los clientes que ya recibieron correo hoy.")
                
                if hide_sent_today:
                    # Obtener COD_CLIENTE de clientes enviados HOY desde df_final (SSOT)
                    today_str = date.today().strftime('%Y-%m-%d')
                    
                    if 'ESTADO_EMAIL' in df_final.columns and 'FECHA_ULTIMO_ENVIO' in df_final.columns:
                        mask_enviado = df_final['ESTADO_EMAIL'] == 'ENVIADO'
                        mask_hoy = df_final['FECHA_ULTIMO_ENVIO'].astype(str).str.startswith(today_str)
                        mask_enviado_hoy = mask_enviado & mask_hoy
                        
                        # Obtener COD_CLIENTE únicos enviados hoy
                        clientes_enviados_hoy = df_final[mask_enviado_hoy]['COD CLIENTE'].unique()
                        
                        # Filtrar: excluir clientes enviados hoy
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
            st.markdown("##### Vista Previa (HTML)")
            
            if sel_emails:
                # Definir ruta de logo (Storage-aware).
                logo_path = _resolve_runtime_logo(config)
                # Convertir imagen a base64 para el preview en iframe
                
                for selected_label in sel_emails:
                    info_sel = email_map[selected_label]
                    # FIX E2E: Usar df_email_view (vista filtrada) en lugar de df_final (dataset completo)
                    # para que la Vista Previa HTML muestre los mismos documentos que el Reporte General filtrado
                    docs_cli_mail = df_email_view[df_email_view['COD CLIENTE'] == info_sel['cod']]
                    
                    mask_soles_prev = docs_cli_mail['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
                    totales_s = docs_cli_mail[mask_soles_prev]['SALDO REAL'].sum()
                    totales_d = docs_cli_mail[~mask_soles_prev]['SALDO REAL'].sum()
                    
                    txt_s = f"S/ {totales_s:,.2f}" if totales_s > 0 else ""
                    txt_d = f"$ {totales_d:,.2f}" if totales_d > 0 else ""
                    
                    # Generar HTML (cid)
                    preview_html_cid = es.generate_premium_email_body_cid(
                        info_sel['empresa'],
                        docs_cli_mail,
                        txt_s,
                        txt_d,
                        config
                    )
                    
                    # Convertir imagen a base64 para el preview en iframe
                    preview_html_view = preview_html_cid
                    if logo_path:
                        try:
                            with open(logo_path, "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode()
                            src_base64 = f"data:image/png;base64,{encoded_string}"
                            preview_html_view = preview_html_cid.replace("cid:logo_dacta", src_base64)
                        except:
                            pass # Fallback (mostrará alt text)
                    
                    with st.expander(f"✉️ {info_sel['empresa']}", expanded=False):
                        components.html(preview_html_view, height=600, scrolling=True)
                
                
                # --- RC-BUG-006 & 010: Protección Avanzada contra Doble Envío ---
                # Generar una firma única del lote actual
                current_batch_hash = hash(tuple(sorted(sel_emails)))
                current_batch_id = f"{len(sel_emails)}_{current_batch_hash}"
                
                if 'last_processed_batch_id' not in st.session_state:
                        st.session_state['last_processed_batch_id'] = None
                
                # 2. Bloqueo de UI si ya se procesó
                is_processed = (st.session_state['last_processed_batch_id'] == current_batch_id)
                
                if is_processed:
                    st.info("ℹ️ Este lote ya fue procesado. Para enviar otro, cambie la selección o recargue (F5).")
                    if st.button("🔄 Resetear Bloqueo (Permitir reenvío)"):
                        st.session_state['last_processed_batch_id'] = None
                        st.rerun()


                # --- RC-BUG-015: Explicit Resend Control ---
                force_resend_ttl = st.checkbox("🔄 Habilitar reenvío (Ignorar bloqueo 10min)", help="Marca esto para reenviar intencionalmente una notificación reciente.")
                
                # Botón Main de Envío
                if st.button("Enviar Correos Masivos", type="primary", disabled=is_processed):
                    if is_processed:
                            st.stop()
                    
                    st.write(f"👷 DEBUG: Iniciando envío... Hash: {current_batch_id} | ForceResend: {force_resend_ttl}")

                    # Credenciales ahora vienen de CONFIG global
                    smtp_cfg = config.get('smtp_config', {})
                    email_user = smtp_cfg.get('user', '')
                    email_pass = smtp_cfg.get('password', '')
                    api_key_sg = smtp_cfg.get('sendgrid_api_key', '')
                    api_key_resend = smtp_cfg.get('resend_api_key', '')

                    # Validation: Requires User AND (Password OR API Key)
                    has_creds = email_user and (email_pass or api_key_sg or api_key_resend)

                    if not has_creds:
                            st.error("❌ Faltan credenciales. Configura SMTP (Usuario/Pass) o API Bridge (Resend/SendGrid Key) en 'Configuración'.")
                    else:
                        # --- Feedback Visual de Supervisión (RC-BUG-017) ---
                        # --- Pre-flight Checks (QA & Internal Copies) RC-BUG-020 ---
                        qa_cfg = config.get('qa_config', {})
                        qa_enabled = qa_cfg.get('enabled', False)
                        
                        if qa_enabled:
                            st.warning(f"🧪 MODO QA ACTIVO: Redirección a lista de pruebas ({len(qa_cfg.get('recipients', []))} destinos).")
                        else:
                            # Prod Mode Info
                            int_copies = config.get('internal_copies', {})
                            n_cc = len(helpers.normalize_emails(int_copies.get('cc_list', [])))
                            n_bcc = len(helpers.normalize_emails(int_copies.get('bcc_list', [])))
                            if n_cc > 0 or n_bcc > 0:
                                st.info(f"👥 En Producción: Se enviarán copias internas ({n_cc} CC, {n_bcc} CCO).")
                        
                        messages_to_send = []
                        # RC-BUG-007: Deduplicación explícita en el origen
                        seen_emails_batch = set()
                        
                        # RC-BUG-LOGO: Resolve logo from Storage/local cache.
                        batch_logo_path = _resolve_runtime_logo(config)
                        
                        for lbl in sel_emails:
                            info = email_map[lbl]
                            
                            # Normalizar email 
                            email_norm = str(info['email']).strip().lower()
                            
                            d_cli = df_filtered[df_filtered['COD CLIENTE'] == info['cod']]
                            
                            # --- RC-BUG-014: Business Key Calculation (Idempotency) ---
                            # 1. Document Fingerprint (Hash de documentos ordenados)
                            if 'MATCH_KEY' in d_cli.columns:
                                doc_ids = sorted(d_cli['MATCH_KEY'].astype(str).unique())
                                doc_str = "|".join(doc_ids)
                            else:
                                # Fallback si no hay MATCH_KEY (usar COMPROBANTE o lo que haya)
                                doc_ids = sorted(d_cli['COMPROBANTE'].astype(str).unique()) if 'COMPROBANTE' in d_cli.columns else []
                                doc_str = "|".join(doc_ids)
                            
                            doc_set_fingerprint = hashlib.md5(doc_str.encode()).hexdigest()[:8]
                            
                            # 2. Notification Key Stable
                            # Key = Company | Email | Date | Type | DocSetHash
                            tipo_notificacion = "Email_EstadoCuenta"
                            fecha_corte = st.session_state.get('config_fecha_corte', date.today())
                            notif_key = f"{config.get('company_name','Antay')}|{email_norm}|{fecha_corte}|{tipo_notificacion}|{doc_set_fingerprint}"
                            
                            # Refined Currency Logic (Robustness fix)
                            mask_soles = d_cli['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)

                            t_s = d_cli[mask_soles]['SALDO REAL'].sum()
                            t_d = d_cli[~mask_soles]['SALDO REAL'].sum()
                            
                            str_s = f"S/ {t_s:,.2f}" if t_s > 0 else ""
                            str_d = f"$ {t_d:,.2f}" if t_d > 0 else ""
                            
                            body = es.generate_premium_email_body_cid(info['empresa'], d_cli, str_s, str_d, config)
                            plain_body = es.generate_plain_text_body(info['empresa'], d_cli, str_s, str_d, config)
                            
                            # Asunto Profesional Anti-Spam
                            company_sender = config.get('company_name', 'DACTA S.A.C.')
                            subject_line = f"Estado de Cuenta {company_sender} | Cliente: {info['empresa']}"
                            
                            # Recolectar MATCH_KEYs para este cliente (para tracking post-envío)
                            if 'MATCH_KEY' in d_cli.columns:
                                match_keys_for_client = d_cli['MATCH_KEY'].tolist()
                            else:
                                match_keys_for_client = []

                            # Vinculo opcional a documento cuando aplica (cliente con un solo documento en el lote).
                            if 'COMPROBANTE' in d_cli.columns:
                                docs_unicos = sorted(d_cli['COMPROBANTE'].astype(str).dropna().unique().tolist())
                            else:
                                docs_unicos = []
                            single_documento_numero = docs_unicos[0] if len(docs_unicos) == 1 else None
                            
                            # Generar ID único para este mensaje (para matching confiable en post-send)
                            import uuid
                            msg_unique_id = str(uuid.uuid4())[:8]
                            
                            messages_to_send.append({
                                'msg_id': msg_unique_id,  # NUEVO: ID único para matching
                                'email': info['email'],
                                'client_name': info['empresa'],
                                'cod_cliente': info['cod'],
                                'match_keys': match_keys_for_client,
                                'subject': subject_line,
                                'html_body': body,
                                'plain_body': plain_body,
                                'notification_key': notif_key,
                                'original_email': info['email'],
                                'documento_numero': single_documento_numero,
                            })
                            
                        # --- GUARD RAIL: Guardar COD CLIENTE seleccionados para tracking preciso ---
                        selected_cod_clientes = [email_map[lbl]['cod'] for lbl in sel_emails]
                        st.session_state['last_send_selected_cod'] = selected_cod_clientes
                        
                        # Enviar Batch con Logo
                        with st.spinner(f"Enviando con Business Lock (Fecha: {fecha_corte})..."):
                            # Obtener cycle_id del session_state
                            current_cycle_id = st.session_state.get('cycle_id', 'default_cycle')

                            results = es.send_email_batch(
                                smtp_cfg,
                                messages_to_send,
                                progress_callback=lambda i, t, m: st.toast(f"{m} ({i}/{t})"),
                                logo_path=batch_logo_path,
                                force_resend=force_resend_ttl,
                                internal_copies_config=config.get('internal_copies', {}),
                                qa_settings=None,
                                cycle_id=current_cycle_id
                            )

                        # Persistir resultado de envio en tabla notificaciones (Supabase).
                        persisted_events = 0
                        persist_errors = 0
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
                                        None
                                    )

                                cliente_id_ctx = str(msg_ctx.get('cod_cliente')).strip() if msg_ctx and msg_ctx.get('cod_cliente') else None
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
                                mensaje_ctx = str(detail.get('Detalle') or '')

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
                            st.warning(
                                f"No se pudieron guardar {persist_errors} eventos en notificaciones."
                            )
                            st.caption(dbm.get_last_error() or "")
                        elif persisted_events > 0:
                            st.caption(f"Notificaciones persistidas en Supabase: {persisted_events}")
                        
                        # Marcar como enviado para prevenir duplicados
                        if results['success'] > 0:
                                st.session_state['last_processed_batch_id'] = current_batch_id
                                
                                # --- FASE 2: Actualizar Columnas de Tracking en SSOT (df_final) ---
                                if 'details' in results and results['details']:
                                    now_timestamp = datetime.now()
                                    updated_match_keys = []
                                    
                                    # Crear mapeo de msg_id -> mensaje para lookup rápido
                                    msg_lookup = {m.get('msg_id'): m for m in messages_to_send if m.get('msg_id')}
                                    
                                    for detail in results['details']:
                                        if detail.get('Estado') == '✅ Enviado':
                                            # Obtener msg_id del detalle (si existe)
                                            msg_id_sent = detail.get('msg_id')
                                            
                                            if msg_id_sent and msg_id_sent in msg_lookup:
                                                msg = msg_lookup[msg_id_sent]
                                            else:
                                                # Fallback: buscar por nombre de cliente
                                                sent_client = detail.get('Cliente')
                                                msg = next((m for m in messages_to_send if m['client_name'] == sent_client), None)
                                            
                                            if msg and msg.get('match_keys'):
                                                # Actualizar por MATCH_KEY
                                                cod_cliente_msg = msg.get('cod_cliente')
                                                
                                                for mk in msg['match_keys']:
                                                    # Filtro doble: MATCH_KEY + COD CLIENTE
                                                    # Use st.session_state['df_final'] instead of df_final passed arg to ensure global update
                                                    mask = (st.session_state['df_final']['MATCH_KEY'] == mk) & \
                                                        (st.session_state['df_final']['COD CLIENTE'] == cod_cliente_msg)
                                                    num_updated = mask.sum()
                                                        
                                                    if num_updated > 0:
                                                        st.session_state['df_final'].loc[mask, 'ESTADO_EMAIL'] = "ENVIADO"
                                                        st.session_state['df_final'].loc[mask, 'FECHA_ULTIMO_ENVIO'] = now_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                                                        if 'ESTADO_ENVIO_TEXTO' in st.session_state['df_final'].columns:
                                                            st.session_state['df_final'].loc[mask, 'ESTADO_ENVIO_TEXTO'] = f"ENVIADO ({now_timestamp.strftime('%H:%M')})"
                                                        updated_match_keys.append(mk)
                                    
                                    # Recalcular df_filtered desde df_final actualizado
                                    df_final_updated = st.session_state['df_final']
                                    df_filtered_new = df_final_updated.copy()
                                    
                                    # Reaplicar filtro de empresa si está activo
                                    if 'filter_empresa' in st.session_state and st.session_state['filter_empresa']:
                                        selected_empresas = st.session_state['filter_empresa']
                                        if selected_empresas:
                                            df_filtered_new = df_filtered_new[df_filtered_new['EMPRESA'].isin(selected_empresas)]
                                    
                                    # Reaplicar filtro "Solo con Correo" si está activo
                                    if st.session_state.get('filter_solo_con_correo', False):
                                        df_filtered_new = df_filtered_new[df_filtered_new['CORREO'].notna() & (df_filtered_new['CORREO'] != '')]
                                    
                                    # Guardar df_filtered actualizado
                                    st.session_state['df_filtered'] = df_filtered_new
                                    
                                    # Guardar info de actualización para display de debug
                                    st.session_state['last_tracking_update'] = {
                                        'count': len(updated_match_keys),
                                        'timestamp': now_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                        'sample_keys': updated_match_keys[:3] if updated_match_keys else []
                                    }
                                    
                                    # IMPORTANTE: Marcar fresh_load=False después del primer envío exitoso
                                    st.session_state['fresh_load'] = False
                                    # GUARD RAIL: Marcar que hay cambios locales de tracking
                                    st.session_state['tracking_dirty'] = True
                                    # Guardar resultados para persistencia post-rerun
                                    st.session_state['last_send_results'] = results
                                    st.session_state['last_send_timestamp'] = now_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                                    
                                    # IMPORTANTE: Forzar rerun para refrescar KPIs
                                    if len(updated_match_keys) > 0:
                                        st.rerun()
                        
                        # --- RC-UX-002: Panel de Resultados Amigable ---
                        st.divider()
                        st.subheader("📊 Resumen del Proceso")
                        
                        # A) Resumen Ejecutivo (Métricas)
                        c1, c2, c3 = st.columns(3)
                        c1.metric("✅ Enviados", results['success'])
                        c2.metric("❌ Fallidos", results['failed'])
                        c3.metric("🔒 Bloqueados (TTL)", results.get('blocked', 0))
                        
                        # B) Tabla de Detalles
                        if 'details' in results and results['details']:
                            df_res = pd.DataFrame(results['details'])
                            st.write("📝 **Detalle por Cliente:**")
                            st.dataframe(df_res[['Cliente', 'Email', 'Estado', 'Detalle']], use_container_width=True, hide_index=True)
                            
                            # QA Traceability
                            qa_cfg_active = config.get('qa_config', {})
                            if qa_cfg_active.get('enabled', False):
                                st.info("ℹ️ Modo QA Activo: Los correos mostrados arriba son los de QA. Abajo el mapeo original.")
                                orig_map = {m['client_name']: m['original_email'] for m in messages_to_send}
                                df_res['Email Original'] = df_res['Cliente'].map(orig_map)
                                st.dataframe(df_res[['Cliente', 'Email Original', 'Email', 'Estado']], use_container_width=True, hide_index=True)
                            
                            csv = df_res.to_csv(index=False).encode('utf-8')
                            st.download_button("📄 Descargar Reporte de Envío (CSV)", data=csv, file_name=f"reporte_envio_{current_batch_id[:8]}.csv", mime="text/csv")
                        
                        # C) Log Técnico
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
            else:
                st.info("Selecciona un cliente para ver la vista previa.")

    else:
            st.info("Sube los archivos y filtra para ver las notificaciones.")

