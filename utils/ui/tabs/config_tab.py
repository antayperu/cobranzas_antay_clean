import streamlit as st
import pandas as pd
import os
import hashlib
import io
from PIL import Image
from datetime import datetime
import utils.settings_manager as sm
import utils.helpers as helpers
import utils.image_processor as img_proc
import utils.email_sender as es_diag # For diagnostic test
import utils.db_manager as dbm
import utils.storage_manager as storage_mgr

def render_tab(config):
    """
    Renders the Configuration Global tab.
    
    Args:
        config (dict): Global configuration.
    """
    st.header("Configuración del Sistema")
    
    # Identity and Visuals Column
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Identidad Corporativa")
        new_company = st.text_input("Nombre de la Empresa", value=config['company_name'])
        new_ruc = st.text_input("RUC", value=config['company_ruc'])
        new_phone = st.text_input("Teléfono de Contacto", value=config['phone_contact'])
        
        st.subheader("Branding (Colores)")
        new_primary = st.color_picker("Color Primario (Encabezados/Botones)", value=config['primary_color'])
        new_secondary = st.color_picker("Color Secundario (Acentos)", value=config['secondary_color'])
        # Nuevo: Color de Texto
        curr_text_col = config.get('text_color', '#262730')
        new_text_color = st.color_picker("Color de Texto (Títulos)", value=curr_text_col, help="Color para títulos y encabezados. El cuerpo se mantiene legible.")

    with col2:
        st.subheader("Funcionalidades (Tabs)")
        f_analysis = st.checkbox("Mostrar Tab Análisis", value=config.get('features', {}).get('show_analysis', False))
        f_sales = st.checkbox("Mostrar Tab Ventas", value=config.get('features', {}).get('show_sales', False))
        
        st.markdown("---")
        st.info(f"📧 **Configuración de Correo (SMTP)**", icon="📧")
        st.caption("Credenciales para el envío de correos masivos.")
        
        col_serv, col_port = st.columns([3, 1])
        with col_serv:
            new_smtp_server = st.text_input("Servidor SMTP", value=config['smtp_config']['server'])
        with col_port:
            new_smtp_port = st.text_input("Puerto SMTP", value=config['smtp_config']['port'])
        
        new_smtp_user = st.text_input("Usuario (Correo)", value=config['smtp_config']['user'])
        new_smtp_pass = st.text_input("Contraseña App", value=config['smtp_config']['password'], type="password")

        st.markdown("---")
        force_smtp = st.checkbox("🔌 Usar Protocolo Local (Directo desde Laptop)", value=config['smtp_config'].get('force_smtp', True), help="Activa esta opción para usar tu conexión local y evitar bloqueos de Gmail.")

        # --- Botón de Diagnóstico (Interactive, No Form) ---
        if st.button("🔌 Probar Conexión (Diagnóstico)", help="Verifica DNS, Red, SMTP y API Key"):
            test_smtp_cfg = {
                "server": new_smtp_server,
                "port": new_smtp_port,
                "user": new_smtp_user,
                "password": new_smtp_pass,
                "resend_api_key": "",
                "sendgrid_api_key": "",
                "force_smtp": force_smtp
            }
            with st.spinner("Realizando diagnóstico de red..."):
                diag_stats = es_diag.test_smtp_connectivity(test_smtp_cfg)
                if diag_stats['ok']:
                    st.success(diag_stats['msg'])
                else:
                    st.error(diag_stats['msg'])
                with st.expander("Ver Bitácora de Diagnóstico"):
                    for l in diag_stats['log']:
                        st.text(l)

        pass

    st.markdown("---")
    st.subheader("Plantilla de Correo")
    col_t1, col_t2 = st.columns(2)
    new_intro = col_t1.text_area("Texto Introductorio", value=config['email_template']['intro_text'], height=150, help="Texto antes de la tabla de deuda. Usa {CLIENTE} para insertar el nombre del cliente.")
    new_footer = col_t2.text_area("Texto Pie de Página", value=config['email_template']['footer_text'], height=150, help="Texto después de los totales.")
    new_alert = st.text_area("Texto Alerta Detracción", value=config['email_template']['alert_text'], help="Mensaje resaltado sobre cuentas de detracción.")
    new_voucher = st.text_area("Texto Nota (Vouchers)", value=config['email_template'].get('voucher_text', ''), help="Texto al final del correo (ej: instrucciones de envío de vouchers). Deja vacío para no mostrar.")

    if st.button("💾 Guardar Configuración", type="primary", use_container_width=True):
        new_settings = {
            "company_name": new_company,
            "company_ruc": new_ruc,
            "phone_contact": new_phone,
            "primary_color": new_primary,
            "secondary_color": new_secondary,
            "text_color": new_text_color,
            "features": {
                "show_analysis": f_analysis,
                "show_sales": f_sales
            },
            "email_template": {
                "intro_text": new_intro,
                "footer_text": new_footer,
                "alert_text": new_alert,
                "voucher_text": new_voucher
            },
            "smtp_config": {
                "server": new_smtp_server,
                "port": new_smtp_port,
                "user": new_smtp_user,
                "password": new_smtp_pass,
                "resend_api_key": "",
                "sendgrid_api_key": "",
                "force_smtp": force_smtp
            }
        }
        if sm.save_settings(new_settings):
            st.success("✅ Configuración guardada correctamente.")
            st.rerun()
        else:
            st.error("❌ Error al guardar la configuración.")

    # --- SECCION INDEPENDIENTE: COPIAS INTERNAS (RC-FEAT-013) ---
    st.markdown("---")
    st.subheader("👥 Copias Internas (CC / CCO)")
    st.info("Configura las listas de distribución interna. Estas copias se envían con cada correo a cliente (Solo en Producción).")
    
    # --- State Management for Dirty Check (Internal Copies) ---
    current_internal_copies = config.get('internal_copies', {})
    if 'prev_internal_copies' not in st.session_state:
        st.session_state['prev_internal_copies'] = current_internal_copies.copy()
        
    saved_cc = ", ".join(current_internal_copies.get('cc_list', []))
    saved_bcc = ", ".join(current_internal_copies.get('bcc_list', []))

    c_copy1, c_copy2 = st.columns(2)
    with c_copy1:
        st.markdown("##### CC (Copia Visible)")
        cc_input = st.text_area("Emails visibles (separados por coma/línea)", value=saved_cc, height=100, help="Estos correos aparecerán en el header 'Cc' del correo.")
        
    with c_copy2:
        st.markdown("##### CCO (Copia Oculta)")
        bcc_input = st.text_area("Emails ocultos (separados por coma/línea)", value=saved_bcc, height=100, help="Estos correos recibirán copia pero NO aparecerán en el header.")
        
    # Preview & Diff Logic
    norm_cc = helpers.normalize_emails(cc_input)
    norm_bcc = helpers.normalize_emails(bcc_input)
    
    # Calculate Changes
    has_changes_copies = (
        norm_cc != current_internal_copies.get('cc_list', []) or 
        norm_bcc != current_internal_copies.get('bcc_list', [])
    )
    
    if True: # Force render
            st.caption(f"📝 Vista Previa: Se enviarán **{len(norm_cc)}** copias visibles y **{len(norm_bcc)}** ocultas por cada correo.")
            if norm_cc or norm_bcc:
                p_c1, p_c2 = st.columns(2)
                with p_c1:
                    if norm_cc: st.info(f"**CC**: {', '.join(norm_cc)}")
                with p_c2:
                    if norm_bcc: st.warning(f"**CCO**: {', '.join(norm_bcc)}")

    if st.button("💾 Guardar Copias Internas", disabled=not has_changes_copies, type="primary" if has_changes_copies else "secondary"):
        new_copies_cfg = {
            "cc_list": norm_cc,
            "bcc_list": norm_bcc
        }
        config['internal_copies'] = new_copies_cfg
        
        if sm.save_settings(config):
            st.session_state['prev_internal_copies'] = new_copies_cfg # Update State
            st.success(f"✅ Guardado: {len(norm_cc)} CCs y {len(norm_bcc)} CCOs configurados.")
            st.toast("Listas de distribución actualizadas", icon="👥")
            import time
            time.sleep(1)
            st.rerun()
        else:
            st.error("Error al guardar configuración.")

    # --- SUPABASE-MIG-005: Mantenimiento de Clientes ---
    st.markdown("---")
    st.subheader("👤 Mantenimiento de Clientes (Supabase)")
    st.caption("Edita telefono, correo y estado de cliente sin recargar Excel.")

    search_cliente = st.text_input(
        "Buscar cliente (codigo, nombre o correo)",
        value="",
        key="cliente_mantenimiento_search",
    )

    try:
        clientes_admin = dbm.list_clientes_for_admin(search=search_cliente, limit=200)
    except Exception as e_clientes:
        clientes_admin = []
        st.error("No se pudo cargar clientes desde Supabase.")
        st.caption(str(e_clientes))

    if clientes_admin:
        option_labels = [
            f"{c.get('cliente_id', '')} | {c.get('nombre', '')} | {c.get('email', '') or '-'}"
            for c in clientes_admin
        ]
        selected_label = st.selectbox(
            f"Clientes encontrados ({len(option_labels)})",
            options=option_labels,
            key="cliente_mantenimiento_selector",
        )
        selected_idx = option_labels.index(selected_label)
        selected_cliente = clientes_admin[selected_idx]

        cid = selected_cliente.get("cliente_id", "")
        email_val = selected_cliente.get("email") or ""
        telefono_val = selected_cliente.get("telefono") or ""
        estado_val = (selected_cliente.get("estado") or "ACTIVO").upper()
        estados_validos = ["ACTIVO", "INACTIVO", "MOROSO"]
        estado_index = estados_validos.index(estado_val) if estado_val in estados_validos else 0

        c_cli1, c_cli2, c_cli3 = st.columns(3)
        with c_cli1:
            nuevo_email = st.text_input(
                "Correo del cliente",
                value=email_val,
                key=f"cliente_email_{cid}",
            )
        with c_cli2:
            nuevo_telefono = st.text_input(
                "Telefono del cliente",
                value=telefono_val,
                key=f"cliente_telefono_{cid}",
            )
        with c_cli3:
            nuevo_estado = st.selectbox(
                "Estado del cliente",
                options=estados_validos,
                index=estado_index,
                key=f"cliente_estado_{cid}",
            )

        if st.button("💾 Guardar Cliente", type="primary", key="cliente_save_btn"):
            ok, msg = dbm.update_cliente_fields(
                cliente_id=cid,
                email=nuevo_email,
                telefono=nuevo_telefono,
                estado=nuevo_estado,
            )
            if ok:
                # Reflejar cambios en el dataset de sesión si está cargado.
                if "df_final" in st.session_state and st.session_state.get("df_final") is not None:
                    df_live = st.session_state["df_final"]
                    mask = df_live["COD CLIENTE"].astype(str) == str(cid)
                    if mask.any():
                        if "CORREO" in df_live.columns:
                            df_live.loc[mask, "CORREO"] = (nuevo_email or "").strip().lower()
                        if "EMAIL_FINAL" in df_live.columns:
                            df_live.loc[mask, "EMAIL_FINAL"] = (nuevo_email or "").strip().lower()
                        if "TELÉFONO" in df_live.columns:
                            df_live.loc[mask, "TELÉFONO"] = (nuevo_telefono or "").strip()
                        st.session_state["df_final"] = df_live
                st.success("✅ Cliente actualizado en Supabase.")
                st.caption(msg)
                st.rerun()
            else:
                st.error("❌ No se pudo actualizar cliente.")
                st.caption(msg)
    else:
        st.info("Sin clientes para mostrar con ese filtro.")
            
    # --- RC-FEAT-012: MARCHA BLANCA (QA) MODE ---
    # --- RC-FEAT-012: MARCHA BLANCA (QA) MODE ---
    # (Header removed to avoid duplication with line 1728)
    
    # ... (Existing QA visual logic can remain if present, or we can just append Danger Zone after)
    # Assuming QA logic follows. We will insert Danger Zone AFTER QA section if possible, 
    # or just here if this is the end of the file view.
    
    # NOTE: View cut off at 1650. I should append. 
    # But wait, I see "st.subheader" for QA above.
    # Let's verify if more content exists. 
    # Actually, let's just insert the Danger Zone BEFORE QA or AFTER copies.
    # Safer to insert at the very end of the Tab 6 block.
    # But since I don't see the end, I'll insert it *before* "Modo Marcha Blanca" for now, or just after Internal Copies.
    
    # Better: Append a new expader "Zona de Peligro" at the bottom of the config form area or independent.
    # Let's insert it right after the Internal Copies block finishes (line 1647).

    # --- RC-FEAT-LEGGER: MANTENIMIENTO ---
    st.markdown("---")
    # st.subheader("Gestión de Sesión") # Clean subheader or removed
    with st.expander("⚙️ Opciones Avanzadas (Reenvío)", expanded=False):
        # st.warning("Estas acciones afectan el historial de envíos. Úsalas con precaución.") # Removed warning if logic is safe now
        
        c_dang1, c_dang2 = st.columns([3, 1])
        with c_dang1:
            st.markdown("**Nuevo Ciclo de Envíos**")
            st.caption("Reinicia el contador de envíos para esta sesión. Útil si deseas volver a notificar a clientes ya gestionados hoy.")
        with c_dang2:
            # Initialize confirmation state
            if 'confirm_reset' not in st.session_state:
                st.session_state['confirm_reset'] = False
            
            if not st.session_state['confirm_reset']:
                # Step 1: Show confirmation button
                if st.button("Reiniciar Sesión", type="secondary", help="Limpia visualización de enviados"):
                    # Calculate how many records will be affected
                    affected_count = 0
                    if 'df_final' in st.session_state and st.session_state['df_final'] is not None:
                        df = st.session_state['df_final']
                        # Count records with EMAIL_FINAL populated
                        if 'EMAIL_FINAL' in df.columns:
                            affected_count = (df['EMAIL_FINAL'].notna() & (df['EMAIL_FINAL'] != "")).sum()
                    
                    st.session_state['confirm_reset'] = True
                    st.session_state['affected_count'] = affected_count
                    st.rerun()
            else:
                # Step 2: Show confirmation dialog
                affected_count = st.session_state.get('affected_count', 0)
                
                st.warning(f"""
                ⚠️ **Confirmación Requerida**
                
                Esto reiniciará el ciclo de envíos:
                - Limpiará: `EMAIL_FINAL`, `ESTADO_EMAIL`, `FECHA_ULTIMO_ENVIO`
                - **{affected_count} registros** volverán a estado "Pendiente"
                
                ¿Deseas continuar?
                """)
                
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Sí, Reiniciar", type="primary"):
                        # Execute reset
                        st.session_state['session_start_ts'] = datetime.now()
                        
                        reset_details = []
                        if 'df_final' in st.session_state and st.session_state['df_final'] is not None:
                            df = st.session_state['df_final']
                            
                            # Track what was cleared
                            if 'EMAIL_FINAL' in df.columns:
                                cleared_emails = (df['EMAIL_FINAL'].notna() & (df['EMAIL_FINAL'] != "")).sum()
                                df['EMAIL_FINAL'] = ""
                                reset_details.append(f"EMAIL_FINAL: {cleared_emails} registros")
                            
                            if 'ESTADO_EMAIL' in df.columns:
                                df['ESTADO_EMAIL'] = ""
                                reset_details.append("ESTADO_EMAIL: limpiado")
                            
                            if 'ESTADO_ENVIO_TEXTO' in df.columns:
                                df['ESTADO_ENVIO_TEXTO'] = "PENDIENTE"
                                reset_details.append("ESTADO_ENVIO_TEXTO: reset a PENDIENTE")
                            
                            if 'FECHA_ULTIMO_ENVIO' in df.columns:
                                df['FECHA_ULTIMO_ENVIO'] = pd.NaT
                                reset_details.append("FECHA_ULTIMO_ENVIO: limpiado")
                            
                            st.session_state['df_final'] = df
                        
                        # Store reset details for display after rerun
                        st.session_state['reset_complete'] = True
                        st.session_state['reset_details'] = reset_details
                        st.session_state['confirm_reset'] = False
                        
                        st.toast("🔄 Ciclo reiniciado", icon="✅")
                        import time
                        time.sleep(0.5)
                        st.rerun()
                
                with col_no:
                    if st.button("❌ Cancelar", type="secondary"):
                        st.session_state['confirm_reset'] = False
                        st.rerun()
            
            # Show success message if reset was just completed
            if st.session_state.get('reset_complete', False):
                affected = st.session_state.get('affected_count', 0)
                st.success(f"✅ Ciclo reiniciado: **{affected} registros** pendientes nuevamente")
                
                with st.expander("📋 Ver detalle"):
                    for detail in st.session_state.get('reset_details', []):
                        st.caption(f"• {detail}")
                
                # Clear the flag
                st.session_state['reset_complete'] = False

    st.markdown("---")
    st.subheader("🧪 Modo Marcha Blanca (QA)")
    st.warning("⚠️ Zona de Seguridad: Configura el entorno de pruebas para envíos seguros. Controla To, CC, BCC.")
    
    qa_cfg_defaults = config.get('qa_config', {
        'enabled': False,
        'mode': 'ALL', # ALL | PRIMARY
        'recipients': ['cortega@antayperu.com', 'acamacho@integrens.com'],
        'allowlist_domains': []
    })
    
    # UI Components
    qa_enabled = st.toggle("🚨 Activar Modo Marcha Blanca (QA)", value=qa_cfg_defaults.get('enabled', False))
    
    c_qa1, c_qa2 = st.columns(2)
    with c_qa1:
        qa_recipients_txt = st.text_area(
            "Destinatarios QA (Separados por coma o línea)",
            value=",\n".join(qa_cfg_defaults.get('recipients', [])),
            height=100,
            disabled=not qa_enabled,
            help="Todos los correos del sistema se redirigirán a esta lista."
        )
    
    with c_qa2:
        st.write("Estrategia de Envío QA:")
        qa_mode_sel = st.radio(
            "Comportamiento",
            options=["ALL", "PRIMARY"],
            format_func=lambda x: "Enviar a TODOS los QA (Recomendado)" if x == "ALL" else "Enviar solo al PRIMERO (Rápido)",
            index=0 if qa_cfg_defaults.get('mode', 'ALL') == 'ALL' else 1,
            disabled=not qa_enabled
        )
        
    st.markdown("##### Copias Internas en QA")
    c_qacc, c_qabcc = st.columns(2)
    with c_qacc:
        qa_cc_txt = st.text_area(
            "CC QA (Visible)", 
            value=",\n".join(qa_cfg_defaults.get('cc_recipients', [])),
            height=80,
            disabled=not qa_enabled,
            help="Estos correos aparecerán en el header CC y recibirán copia."
        )
    with c_qabcc:
        qa_bcc_txt = st.text_area(
            "BCC QA (Oculto)", 
            value=",\n".join(qa_cfg_defaults.get('bcc_recipients', [])),
            height=80,
            disabled=not qa_enabled,
            help="Estos correos recibirán copia oculta."
        )
        
    # --- Dirty Check Logic QA ---
    # Parse Lists for Preview & Diff
    curr_qa_recipients = [x.strip() for x in qa_recipients_txt.replace('\n', ',').replace(';',',').split(',') if x.strip()]
    curr_qa_cc = [x.strip() for x in qa_cc_txt.replace('\n', ',').replace(';',',').split(',') if x.strip()]
    curr_qa_bcc = [x.strip() for x in qa_bcc_txt.replace('\n', ',').replace(';',',').split(',') if x.strip()]
    
    # Check against Saved Defaults
    qa_changes = (
        qa_enabled != qa_cfg_defaults.get('enabled') or
        qa_mode_sel != qa_cfg_defaults.get('mode') or
        curr_qa_recipients != qa_cfg_defaults.get('recipients', []) or
        curr_qa_cc != qa_cfg_defaults.get('cc_recipients', []) or
        curr_qa_bcc != qa_cfg_defaults.get('bcc_recipients', [])
    )

    # --- QA Live Preview ---
    if qa_enabled:
        st.markdown(f"""
        <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 1px solid #ffeeba; margin-bottom: 10px;">
            <strong>📝 Vista Previa QA (Simulación):</strong><br>
            Por cada correo enviado, se armará el siguiente esquema:<br>
            <ul>
                <li><strong>To (Destino):</strong> {len(curr_qa_recipients)} correos (Lista QA)</li>
                <li><strong>Cc (Visible):</strong> {len(curr_qa_cc)} correos (Lista QA)</li>
                <li><strong>Bcc (Oculto):</strong> {len(curr_qa_bcc)} correos (Lista QA)</li>
            </ul>
            <small><em>* Los correos de Producción serán IGNORADOS completamente.</em></small>
        </div>
        """, unsafe_allow_html=True)

    if st.button("💾 Guardar Configuración QA", type="primary" if qa_changes else "secondary", disabled=not qa_changes):
        new_qa_config = {
            'enabled': qa_enabled,
            'mode': qa_mode_sel,
            'recipients': curr_qa_recipients,
            'cc_recipients': curr_qa_cc,
            'bcc_recipients': curr_qa_bcc,
            'allowlist_domains': [] # Future proof
        }
        
        config['qa_config'] = new_qa_config
        if sm.save_settings(config):
            st.success(f"✅ Modo QA Actualizado. Destinos: {len(curr_qa_recipients)} To | {len(curr_qa_cc)} CC | {len(curr_qa_bcc)} BCC")
            if qa_enabled:
                st.toast("🚨 MODO QA ACTIVO: No saldrán correos a clientes.", icon="🧪")
            import time
            time.sleep(1)
            st.rerun()
    # -------------------------------------------------------

    st.markdown("---")
    st.subheader("Logo de la Empresa (Visuals Enterprise)")
    # --- RC-UX-LOGO-STD: Enterprise Staging Flow + Anti-Loop ---
    
    # 1. Initialization & State Management
    if 'logo_uploader_key' not in st.session_state:
        st.session_state.logo_uploader_key = 0
        
    if 'logo_staged' not in st.session_state:
        st.session_state.logo_staged = None # {bytes, w, h, name}

    # 2. Display Active Logo (Current State)
    current_logo_path = storage_mgr.resolve_logo_path(config) or config.get('logo_path')
    logo_active_exists = False
    if current_logo_path and os.path.exists(current_logo_path):
        logo_active_exists = True
        
    st.markdown("##### Logo Activo (En Producción)")
    if logo_active_exists and st.session_state.logo_staged is None:
        # Show Active only if not staging (or show both? User wants "Vista previa final" on upload)
        # Strategy: Show Active. If Staged exists, show Staged below in "Review" section.
        
        c_active_img, c_active_info = st.columns([1, 2])
        with c_active_img:
            st.image(current_logo_path, width=200)
        with c_active_info:
            st.success("✅ Logo configurado y visible en correos.")
            if st.button("🗑️ Eliminar Logo Actual", type="secondary", key="btn_del_logo"):
                try:
                    delete_info = storage_mgr.delete_logo_assets(config)
                    config.update(delete_info.get("config_patch", {}))
                except Exception:
                    # Limpieza minima local/config aunque Storage falle.
                    config['logo_path'] = None
                    config['logo_storage_bucket'] = None
                    config['logo_storage_path'] = None
                    config['logo_storage_public_url'] = None
                    config['logo_storage_original_path'] = None
                    config['logo_storage_synced_at'] = None
                if sm.save_settings(config):
                    st.success("✅ Logo eliminado en configuracion.")
                    st.rerun()
                else:
                    st.error("❌ No se pudo guardar la eliminacion del logo.")
    elif not logo_active_exists and st.session_state.logo_staged is None:
            st.info("ℹ️ No hay logo configurado. El correo saldrá SIN logo.")

    
    st.markdown("---")
    st.markdown("##### Cargar Nuevo Logo (Staging Area)")
    
    # 3. Uploader (Staging Trigger)
    # Using dynamic key to reset uploader after Save/Cancel
    uploaded_logo = st.file_uploader(
        "Seleccionar archivo (PNG/JPG)", 
        type=['png', 'jpg', 'jpeg'],
        key=f"uploader_logo_{st.session_state.logo_uploader_key}"
    )
    
    # Recomendaciones (Collapsed)
    with st.expander("ℹ️ Recomendaciones Técnicas"):
        st.markdown("""
        *   **Formato**: PNG (transparente) o JPG.
        *   **Dimensiones**: > 800px ancho.
        *   **Proceso**: Se aplica corte de bordes (trim) y redimensionado (resize) automático.
        """)

    # 4. Processing Logic (Run once per file)
    if uploaded_logo:
            import hashlib
            # Hash check to avoid loop/re-processing
            raw_bytes = uploaded_logo.getbuffer()
            file_hash = hashlib.md5(raw_bytes).hexdigest()
            
            # If new file or different from last staged
            last_hash = st.session_state.get('logo_last_hash')
            
            if last_hash != file_hash:
                with st.spinner("Procesando logo (Trim + Resize)..."):
                    # Process
                    proc_bytes, proc_w, proc_h = img_proc.process_logo_image(raw_bytes)
                    
                    # Update Staging State
                    st.session_state.logo_staged = {
                        'bytes': proc_bytes,
                        'w': proc_w,
                        'h': proc_h, 
                        'name': uploaded_logo.name,
                        'orig_bytes': raw_bytes
                    }
                    st.session_state.logo_last_hash = file_hash

    # 5. Staging Review & Commit (Save)
    if st.session_state.logo_staged:
        st.divider()
        st.warning("⚠️ Tienes cambios pendientes (Logo en Staging). No se usarán hasta que guardes.")
        
        staged = st.session_state.logo_staged
        
        col_rev1, col_rev2 = st.columns(2)
        with col_rev1:
            st.caption("Previsualización Final")
            st.image(staged['bytes'], width=300)
            st.caption(f"Dim: {staged['w']}x{staged['h']} px | {len(staged['bytes'])//1024} KB")
        
        with col_rev2:
            st.caption("Acciones")
            
            # SAVE ACTION
            if st.button("💾 GUARDAR Y APLICAR", type="primary", use_container_width=True):
                # Persist to Disk
                assets_dir = os.path.join(os.getcwd(), "assets")
                if not os.path.exists(assets_dir):
                    os.makedirs(assets_dir)
                
                # Save Original
                fn_orig = f"logo_original_{staged['name']}"
                with open(os.path.join(assets_dir, fn_orig), "wb") as f:
                    f.write(staged['orig_bytes'])
                    
                # Save Processed (Canonical)
                path_proc = os.path.join(assets_dir, "logo_dacta_processed.png")
                with open(path_proc, "wb") as f:
                    f.write(staged['bytes'])
                
                # Update Config
                config['logo_path'] = path_proc

                storage_sync_ok = False
                storage_sync_error = None
                try:
                    sync_info = storage_mgr.upload_logo_assets(
                        original_bytes=bytes(staged['orig_bytes']),
                        processed_bytes=bytes(staged['bytes']),
                        original_name=staged['name'],
                    )
                    config.update(sync_info.get("config_patch", {}))
                    storage_sync_ok = True
                except Exception as e_sync:
                    storage_sync_error = str(e_sync)

                if not sm.save_settings(config):
                    st.error("❌ Error al guardar configuracion del logo.")
                    return
                
                # Clear Staging & Reset Uploader
                st.session_state.logo_staged = None
                st.session_state.logo_last_hash = None
                st.session_state.logo_uploader_key += 1 # Forces uploader reset
                
                if storage_sync_ok:
                    st.success("✅ Logo guardado y sincronizado en Supabase Storage.")
                else:
                    st.warning("⚠️ Logo guardado localmente, pero no se pudo sincronizar en Storage.")
                    if storage_sync_error:
                        st.caption(storage_sync_error)
                import time
                time.sleep(1)
                st.rerun()

            st.write("")
            # CANCEL ACTION
            if st.button("✖️ Cancelar / Descartar", use_container_width=True):
                st.session_state.logo_staged = None
                st.session_state.logo_last_hash = None
                st.session_state.logo_uploader_key += 1 # Reset uploader
                st.rerun()
