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
import utils.storage_manager as storage_mgr

def render_tab(config):
    """
    Renders the Configuration Global tab with premium AU/UX design.
    
    Args:
        config (dict): Global configuration.
    """
    # --- HEADER PREMIUM ---
    st.header("⚙️ Configuración del Sistema")
    st.markdown("Personaliza la empresa, branding, comunicaciones y dispositivos de envío.")
    st.divider()
    
    # Get colors for consistent theming
    primary_color = config.get('primary_color', '#2E86AB')
    secondary_color = config.get('secondary_color', '#00D4FF')
    
    # --- SECTION 1: IDENTIDAD CORPORATIVA ---
    with st.container(border=True):
        st.markdown("### 🏢 Identidad Corporativa")
        st.caption("Datos básicos de tu empresa que aparecen en correos y documentos")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_company = st.text_input(
                "Nombre de la Empresa",
                value=config['company_name'],
                placeholder="Ej: DACTA S.A.C.",
                help="Se mostrará en cada correo y documento"
            )
        with col2:
            new_ruc = st.text_input(
                "RUC",
                value=config['company_ruc'],
                placeholder="Ej: 20375779448",
                help="Número de identificación tributaria"
            )
        with col3:
            new_phone = st.text_input(
                "Teléfono de Contacto",
                value=config['phone_contact'],
                placeholder="Ej: +51 998 080 797",
                help="Para contactos a través de documentos"
            )
    
    st.write("")  # Spacing
    
    # --- SECTION 2: BRANDING (COLORES) ---
    with st.container(border=True):
        st.markdown("### 🎨 Branding & Colores")
        st.caption("Personaliza la paleta de colores corporativa")
        
        col_brand1, col_brand2, col_brand3 = st.columns(3)
        with col_brand1:
            new_primary = st.color_picker(
                "Color Primario",
                value=config['primary_color'],
                help="Usado en encabezados, botones principales"
            )
            st.caption("Encabezados & Botones")
        
        with col_brand2:
            new_secondary = st.color_picker(
                "Color Secundario",
                value=config['secondary_color'],
                help="Usado en acentos y elementos secundarios"
            )
            st.caption("Acentos & Elementos")
        
        with col_brand3:
            curr_text_col = config.get('text_color', '#262730')
            new_text_color = st.color_picker(
                "Color de Texto",
                value=curr_text_col,
                help="Para títulos y encabezados principales"
            )
            st.caption("Títulos & Encabezados")
    
    st.write("")  # Spacing
    
    # --- SECTION 3: FUNCIONALIDADES ---
    with st.container(border=True):
        st.markdown("### 📊 Funcionalidades Disponibles")
        st.caption("Controla qué tabs se muestran en la aplicación")
        
        col_feat1, col_feat2 = st.columns(2)
        with col_feat1:
            f_analysis = st.checkbox(
                "📈 Mostrar Tab Análisis",
                value=config.get('features', {}).get('show_analysis', False),
                help="Análisis avanzados de cobranza"
            )
        with col_feat2:
            f_sales = st.checkbox(
                "💰 Mostrar Tab Ventas",
                value=config.get('features', {}).get('show_sales', False),
                help="Gestión de información de ventas"
            )

    st.write("")  # Spacing
    
    # --- SECTION 4: CORREO ELECTRÓNICO (EMAIL) ---
    with st.container(border=True):
        st.markdown("### 📧 Correo Electrónico (SMTP)")
        
        # Estado dinámico basado en session_state
        smtp_status = st.session_state.get('smtp_test_ok', False)
        
        # Indicador de Estado
        col_status, col_actions = st.columns([3, 1])
        with col_status:
            if smtp_status:
                st.caption("🟢 **Estado:** Operativo")
            else:
                st.caption("🟡 **Estado:** Pendiente de configuración")
        with col_actions:
            with st.popover("ℹ️"):
                st.markdown("""
                **¿Qué significan estos estados?**
                
                🟡 **PENDIENTE** 
                - Aún no has probado la conexión
                - Las credenciales están vacías o no validadas
                - *Acción:* Completa los datos y haz clic en "Probar Conexión"
                
                🟢 **OPERATIVO** 
                - La conexión SMTP funciona correctamente
                - Los correos se enviarán exitosamente
                - *Estado ideal:* Sistema listo para envíos masivos
                
                🔴 **ERROR** 
                - La conexión falló (credenciales inválidas, servidor incorrecto)
                - El servidor rechazó la autenticación
                - *Acción:* Revisa usuario/contraseña y vuelve a probar
                """)
        
        st.caption("Configura las credenciales para envío de correos masivos")
        
        col_serv, col_port = st.columns([3, 1])
        with col_serv:
            new_smtp_server = st.text_input(
                "Servidor SMTP",
                value=config['smtp_config']['server'],
                placeholder="Ej: smtp.gmail.com",
                help="Servidor SMTP de tu proveedor de correo"
            )
        with col_port:
            new_smtp_port = st.text_input(
                "Puerto",
                value=config['smtp_config']['port'],
                placeholder="587",
                help="Puerto SMTP (generalmente 587)"
            )
        
        col_user, col_pass = st.columns(2)
        with col_user:
            new_smtp_user = st.text_input(
                "Usuario (Correo)",
                value=config['smtp_config']['user'],
                placeholder="tu_email@gmail.com",
                help="Tu correo de envío"
            )
        with col_pass:
            new_smtp_pass = st.text_input(
                "Contraseña App",
                value=config['smtp_config']['password'],
                type="password",
                placeholder="••••••••",
                help="Contraseña o App Password"
            )
        
        force_smtp = st.checkbox(
            "🔌 Usar Protocolo Local (Directo desde Laptop)",
            value=config['smtp_config'].get('force_smtp', True),
            help="Conecta directamente sin pasar por servidor externo"
        )
        
        # Diagnóstico Button
        col_diag1, col_diag2, col_diag3 = st.columns([2, 1, 1])
        with col_diag1:
            if st.button("🔍 Probar Conexión (Diagnóstico)", use_container_width=True, type="secondary"):
                test_smtp_cfg = {
                    "server": new_smtp_server,
                    "port": new_smtp_port,
                    "user": new_smtp_user,
                    "password": new_smtp_pass,
                    "resend_api_key": "",
                    "sendgrid_api_key": "",
                    "force_smtp": force_smtp
                }
                with st.spinner("Realizando diagnóstico..."):
                    diag_stats = es_diag.test_smtp_connectivity(test_smtp_cfg)
                    if diag_stats['ok']:
                        st.success(diag_stats['msg'])
                        # Guardar estado exitoso
                        st.session_state['smtp_test_ok'] = True
                    else:
                        st.error(diag_stats['msg'])
                        st.session_state['smtp_test_ok'] = False
                    with st.expander("Ver detalles técnicos"):
                        for l in diag_stats['log']:
                            st.text(l)
                import time
                time.sleep(1)
                st.rerun()
    
    st.write("")  # Spacing
    
    # --- SECTION 5: PLANTILLA DE CORREO ---
    with st.container(border=True):
        st.markdown("### 📝 Plantillas de Correo")
        st.caption("Personaliza el contenido de los correos que se enviarán automáticamente")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            new_intro = st.text_area(
                "Texto Introductorio",
                value=config['email_template']['intro_text'],
                height=120,
                help="Texto antes de la tabla de deuda. Usa {CLIENTE} para el nombre."
            )
        with col_t2:
            new_footer = st.text_area(
                "Texto Pie de Página",
                value=config['email_template']['footer_text'],
                height=120,
                help="Texto después de los totales."
            )
        
        new_alert = st.text_area(
            "Texto Alerta Detracción",
            value=config['email_template']['alert_text'],
            height=80,
            help="Mensaje sobre cuentas de detracción SUNAT."
        )
        new_voucher = st.text_area(
            "Texto Nota (Vouchers)",
            value=config['email_template'].get('voucher_text', ''),
            height=80,
            help="Instrucciones finales (ej: envío de vouchers). Déjalo vacío para no mostrar."
        )
        
        st.caption("💡 **Nota:** Edita los textos y haz clic en 'Guardar Plantillas' para guardar los cambios")
        
        if st.button("💾 Guardar Plantillas", type="primary", use_container_width=True):
            # Guardar plantillas
            config['email_template'] = {
                "intro_text": new_intro,
                "footer_text": new_footer,
                "alert_text": new_alert,
                "voucher_text": new_voucher
            }
            
            if sm.save_settings(config):
                st.success("✅ Plantillas de correo guardadas correctamente.")
                st.toast("Plantillas actualizadas", icon="📝")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Error al guardar las plantillas.")

    st.write("")  # Spacing
    
    # --- BOTÓN GUARDAR CONFIGURACIÓN PRINCIPAL ---
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
    
    st.divider()
    
    # --- SECTION 6: COPIAS INTERNAS (CC/CCO) ---
    with st.container(border=True):
        st.markdown("### 👥 Copias Internas (CC / CCO)")
        st.caption("Configura listas de distribución que recibirán copia de cada correo")
        
        # --- State Management for Dirty Check (Internal Copies) ---
        current_internal_copies = config.get('internal_copies', {})
        if 'prev_internal_copies' not in st.session_state:
            st.session_state['prev_internal_copies'] = current_internal_copies.copy()
            
        saved_cc = ", ".join(current_internal_copies.get('cc_list', []))
        saved_bcc = ", ".join(current_internal_copies.get('bcc_list', []))

        col_cc1, col_cc2 = st.columns(2)
        with col_cc1:
            st.markdown("##### 📋 CC (Visible)")
            st.caption("Aparecerá en header 'Cc' del correo")
            cc_input = st.text_area(
                "Emails separados por coma o salto de línea",
                value=saved_cc,
                height=100,
                help="Estos correos verán quién más recibió el mensaje",
                key="cc_input_area"
            )
            
        with col_cc2:
            st.markdown("##### 🔒 CCO (Oculto)")
            st.caption("NO aparecerá en header del correo")
            bcc_input = st.text_area(
                "Emails separados por coma o salto de línea",
                value=saved_bcc,
                height=100,
                help="Estos correos recibirán copia pero será oculta",
                key="bcc_input_area"
            )
        
        st.caption("💡 **Nota:** Escribe los emails y haz clic en el botón 'Guardar Copias Internas' para guardar los cambios")
        if st.button("💾 Guardar Copias Internas", type="primary", use_container_width=True):
            # Normalizar SOLO aquí (al guardar, no mientras escribe)
            norm_cc = helpers.normalize_emails(cc_input)
            norm_bcc = helpers.normalize_emails(bcc_input)
            
            # Mostrar preview ANTES de guardar
            st.caption(f"📝 Vista Previa: Se enviarán **{len(norm_cc)}** copias visibles y **{len(norm_bcc)}** ocultas por cada correo.")
            if norm_cc or norm_bcc:
                p_c1, p_c2 = st.columns(2)
                with p_c1:
                    if norm_cc: st.info(f"**CC**: {', '.join(norm_cc)}")
                with p_c2:
                    if norm_bcc: st.warning(f"**CCO**: {', '.join(norm_bcc)}")
            
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

    st.divider()
    
    # --- SECTION 7: WHATSAPP — DISPOSITIVO DE ENVÍO ---
    with st.container(border=True):
        st.markdown("### 📱 WhatsApp — Dispositivo de Envío")
        st.caption("Conecta tu teléfono para enviar mensajes de cobranza automáticamente")
        
        from utils.whatsapp_sender import (
            get_wa_session_info,
            connect_wa_session,
            clear_wa_session,
            update_wa_session_alias,
            _SELENIUM_OK as _WA_SELENIUM_OK,
        )

        _wa_info = get_wa_session_info()
        _wa_active = _wa_info.get("status") == "active"

        # Indicador de Estado
        if _wa_active:
            _wa_phone   = _wa_info.get("phone", "")
            _wa_name    = _wa_info.get("profile_name", "")
            _wa_ts      = _wa_info.get("verified_at", "")
            _device_lbl = f"**{_wa_name}**" if _wa_name else "Dispositivo conectado"
            _phone_lbl  = f"  ·  `{_wa_phone}`" if _wa_phone else ""
            
            st.success(f"🟢 **ACTIVO** - {_device_lbl}{_phone_lbl}")
            st.caption(f"Verificado: {_wa_ts}")
            
            col_wa_edit, col_wa_disco = st.columns(2)
            with col_wa_edit:
                if st.button("✏️ Editar Etiqueta", type="secondary", use_container_width=True, key="btn_wa_edit_alias"):
                    st.session_state['wa_edit_mode'] = True
            
            with col_wa_disco:
                if st.button("🔌 Desconectar Dispositivo", type="secondary", use_container_width=True, key="btn_wa_disconnect"):
                    clear_wa_session()
                    st.toast("Sesión de WhatsApp eliminada.", icon="🔴")
                    st.rerun()
            
            # Formulario de edición (expandible)
            if st.session_state.get('wa_edit_mode', False):
                with st.expander("✏️ Editar información del dispositivo", expanded=True):
                    _edit_c1, _edit_c2 = st.columns(2)
                    _new_alias = _edit_c1.text_input(
                        "Nombre del Dispositivo",
                        value=_wa_info.get("profile_name", ""),
                        key="wa_alias_input",
                        placeholder="Ej: WhatsApp Cobranzas",
                    )
                    _new_phone_lbl = _edit_c2.text_input(
                        "Número de Teléfono",
                        value=_wa_info.get("phone", ""),
                        key="wa_phone_label_input",
                        placeholder="Ej: +51 998 080 797",
                    )
                    _alias_changed = (
                        _new_alias != _wa_info.get("profile_name", "") or
                        _new_phone_lbl != _wa_info.get("phone", "")
                    )
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 Guardar", key="btn_wa_save_alias",
                                     disabled=not _alias_changed,
                                     type="primary" if _alias_changed else "secondary",
                                     use_container_width=True):
                            if update_wa_session_alias(alias=_new_alias, phone=_new_phone_lbl):
                                st.success("✅ Información actualizada.")
                                st.session_state['wa_edit_mode'] = False
                                st.rerun()
                            else:
                                st.error("❌ Error al guardar. Verifica que la sesión sigue activa.")
                    
                    with col_cancel:
                        if st.button("Cancelar", key="btn_wa_cancel", use_container_width=True):
                            st.session_state['wa_edit_mode'] = False
                            st.rerun()
        
        else:
            # Sin conexión activa
            st.warning("🟡 **INACTIVO** - Sin dispositivo conectado")
            st.caption("Necesitas vincular tu teléfono para enviar mensajes WhatsApp")
            
            if not _WA_SELENIUM_OK:
                st.error(
                    "⚠️ **Selenium no está instalado**  \n"
                    "Ejecuta `_install_deps.bat` en el servidor QA y reinicia la app."
                )
            else:
                st.info(
                    "**Proceso:**  \n"
                    "1. Al hacer clic, Chrome se abrirá en el servidor  \n"
                    "2. Escanea el código QR con tu teléfono  \n"
                    "3. Se guardará automáticamente (disponible 120 segundos)"
                )
                
                if st.button("📲 Conectar Dispositivo", type="primary", use_container_width=True, key="btn_wa_connect"):
                    with st.spinner("Abriendo Chrome — escanea el QR en el navegador..."):
                        try:
                            ok, phone, profile, err = connect_wa_session(timeout_seconds=120)
                        except Exception as e:
                            import traceback
                            err = f"EXCEPTION: {str(e)}\n\n{traceback.format_exc()}"
                            ok = False
                            phone = ""
                            profile = ""
                    
                    if ok:
                        _label = f"**{profile}**" if profile else "dispositivo"
                        _ph    = f" (`{phone}`)" if phone else ""
                        st.success(f"✅ Sesión conectada: {_label}{_ph}")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {err}")

    st.divider()
    
    # --- SECTION 8: OPCIONES AVANZADAS ---
    with st.expander("⚙️ Opciones Avanzadas (Reenvío)", expanded=False):
        st.markdown("##### Gestión Avanzada de Ciclos")
        st.caption("⚠️ Estas acciones son sensibles. Úsalas con precaución")
        
        with st.container(border=True):
            st.markdown("###### 🔄 Reiniciar Ciclo de Envíos")
            st.caption("Limpia el estado de envíos para renotificar a clientes ya gestionados hoy")
            
            # Initialize confirmation state
            if 'confirm_reset' not in st.session_state:
                st.session_state['confirm_reset'] = False
            
            if not st.session_state['confirm_reset']:
                if st.button("🔄 Reiniciar Ciclo", type="secondary", use_container_width=True):
                    # Calculate affected
                    affected_count = 0
                    if 'df_final' in st.session_state and st.session_state['df_final'] is not None:
                        df = st.session_state['df_final']
                        if 'EMAIL_FINAL' in df.columns:
                            affected_count = (df['EMAIL_FINAL'].notna() & (df['EMAIL_FINAL'] != "")).sum()
                    
                    st.session_state['confirm_reset'] = True
                    st.session_state['affected_count'] = affected_count
                    st.rerun()
            else:
                affected_count = st.session_state.get('affected_count', 0)
                
                st.warning(f"""
                ⚠️ **Confirmación Requerida**
                
                **Se reiniciará el ciclo de envíos:**
                - EMAIL_FINAL, ESTADO_EMAIL, FECHA_ULTIMO_ENVIO serán limpiados
                - **{affected_count} registros** volverán a "Pendiente"
                """)
                
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Sí, Reiniciar Ahora", type="primary", use_container_width=True):
                        st.session_state['session_start_ts'] = datetime.now()
                        
                        reset_details = []
                        if 'df_final' in st.session_state and st.session_state['df_final'] is not None:
                            df = st.session_state['df_final']
                            
                            if 'EMAIL_FINAL' in df.columns:
                                cleared_emails = (df['EMAIL_FINAL'].notna() & (df['EMAIL_FINAL'] != "")).sum()
                                df['EMAIL_FINAL'] = ""
                                reset_details.append(f"📧 EMAIL_FINAL: {cleared_emails} registros")
                            
                            if 'ESTADO_EMAIL' in df.columns:
                                df['ESTADO_EMAIL'] = ""
                                reset_details.append("📧 ESTADO_EMAIL: limpiado")
                            
                            if 'ESTADO_ENVIO_TEXTO' in df.columns:
                                df['ESTADO_ENVIO_TEXTO'] = "PENDIENTE"
                                reset_details.append("📱 ESTADO_ENVIO_TEXTO: → PENDIENTE")
                            
                            if 'FECHA_ULTIMO_ENVIO' in df.columns:
                                df['FECHA_ULTIMO_ENVIO'] = pd.NaT
                                reset_details.append("📅 FECHA_ULTIMO_ENVIO: limpiado")
                            
                            st.session_state['df_final'] = df
                        
                        st.session_state['reset_complete'] = True
                        st.session_state['reset_details'] = reset_details
                        st.session_state['confirm_reset'] = False
                        
                        st.toast("🔄 Ciclo reiniciado", icon="✅")
                        import time
                        time.sleep(0.5)
                        st.rerun()
                
                with col_no:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.session_state['confirm_reset'] = False
                        st.rerun()
            
            # Success message
            if st.session_state.get('reset_complete', False):
                affected = st.session_state.get('affected_count', 0)
                st.success(f"✅ Ciclo reiniciado: {affected} registros ahora en 'Pendiente'")
                
                with st.expander("📋 Ver detalles"):
                    for detail in st.session_state.get('reset_details', []):
                        st.caption(f"✓ {detail}")
                
                st.session_state['reset_complete'] = False
    # --- SECTION 9: Logo Empresarial (Enterprise Staging Flow) ---
    with st.container(border=True):
        st.markdown("### 📸 Logo Empresarial")
        st.caption("Carga y personaliza el logo que aparecerá en correos y documentos exportados")
        st.write("")
        
        # Initialize state
        if 'logo_uploader_key' not in st.session_state:
            st.session_state.logo_uploader_key = 0
        if 'logo_staged' not in st.session_state:
            st.session_state.logo_staged = None
        
        # Determine current logo status
        current_logo_path = storage_mgr.resolve_logo_path(config) or config.get('logo_path')
        logo_active_exists = False
        if current_logo_path and os.path.exists(current_logo_path):
            logo_active_exists = True
        
        # TAB 1: View Active Logo
        tab_view, tab_upload = st.tabs(["📋 Logo Activo", "📤 Cargar Nuevo"])
        
        with tab_view:
            if logo_active_exists and st.session_state.logo_staged is None:
                col_img, col_actions = st.columns([1.5, 2])
                with col_img:
                    st.markdown("**Previsualización Actual**")
                    st.image(current_logo_path, width=220)
                
                with col_actions:
                    st.markdown("**Estado**")
                    st.success("🟢 **ACTIVO** — Visible en correos y exportes")
                    st.write("")
                    
                    if st.button("🗑️ Eliminar Logo", type="secondary", use_container_width=True, key="btn_del_logo"):
                        try:
                            delete_info = storage_mgr.delete_logo_assets(config)
                            config.update(delete_info.get("config_patch", {}))
                        except Exception:
                            config['logo_path'] = None
                            config['logo_storage_bucket'] = None
                            config['logo_storage_path'] = None
                            config['logo_storage_public_url'] = None
                            config['logo_storage_original_path'] = None
                            config['logo_storage_synced_at'] = None
                        
                        if sm.save_settings(config):
                            st.success("✅ Logo eliminado. El siguiente exporte no lo incluirá.")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar cambios.")
            
            elif not logo_active_exists and st.session_state.logo_staged is None:
                st.info("🟡 **Sin Logo** — Los correos se enviarán sin logo. Carga uno en la pestaña 'Cargar Nuevo'")
            
            elif st.session_state.logo_staged:
                st.info("📦 Tienes un logo en **revisión** (staging). Ve a la pestaña 'Cargar Nuevo' para completar.")
        
        with tab_upload:
            st.markdown("**Paso 1: Selecciona archivo**")
            uploaded_logo = st.file_uploader(
                "PNG o JPG", 
                type=['png', 'jpg', 'jpeg'],
                key=f"uploader_logo_{st.session_state.logo_uploader_key}",
                label_visibility="collapsed"
            )
            
            if uploaded_logo:
                st.markdown("**Paso 2: Procesar**")
                if st.button("▶️ Procesar y Previsualizar", type="secondary", use_container_width=True):
                    import hashlib
                    raw_bytes = uploaded_logo.getbuffer()
                    file_hash = hashlib.md5(raw_bytes).hexdigest()
                    
                    with st.spinner("Procesando logo..."):
                        proc_bytes, proc_w, proc_h = img_proc.process_logo_image(raw_bytes)
                        st.session_state.logo_staged = {
                            'bytes': proc_bytes,
                            'w': proc_w,
                            'h': proc_h,
                            'name': uploaded_logo.name,
                            'orig_bytes': raw_bytes
                        }
                        st.session_state.logo_last_hash = file_hash
                    st.rerun()
            
            with st.expander("ℹ️ Recomendaciones"):
                st.markdown("""
                - **Formato:** PNG (para fondo transparente) o JPG
                - **Tamaño:** Mayor a 800px de ancho
                - **Automático:** Se aplica recorte y redimensión sin perder calidad
                """)
            
            # Staging Review Section
            if st.session_state.logo_staged:
                st.divider()
                staged = st.session_state.logo_staged
                
                st.markdown("**Paso 3: Revisar y guardar**")
                col_preview, col_confirm = st.columns([1.5, 2])
                
                with col_preview:
                    st.markdown("**Previsualización Final**")
                    st.image(staged['bytes'], width=220)
                    st.caption(f"📐 {staged['w']}×{staged['h']}px | 💾 {len(staged['bytes'])//1024}KB")
                
                with col_confirm:
                    st.markdown("**Acciones**")
                    st.warning("⚠️ Cambios en staging — no se aplicarán hasta guardar")
                    
                    if st.button("💾 GUARDAR Y APLICAR", type="primary", use_container_width=True):
                        assets_dir = os.path.join(os.getcwd(), "assets")
                        if not os.path.exists(assets_dir):
                            os.makedirs(assets_dir)
                        
                        fn_orig = f"logo_original_{staged['name']}"
                        with open(os.path.join(assets_dir, fn_orig), "wb") as f:
                            f.write(staged['orig_bytes'])
                        
                        path_proc = os.path.join(assets_dir, "logo_dacta_processed.png")
                        with open(path_proc, "wb") as f:
                            f.write(staged['bytes'])
                        
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
                            st.error("❌ Error al guardar configuración.")
                            return
                        
                        st.session_state.logo_staged = None
                        st.session_state.logo_last_hash = None
                        st.session_state.logo_uploader_key += 1
                        
                        if storage_sync_ok:
                            st.success("✅ Logo guardado y sincronizado. Ya está en uso.")
                        else:
                            st.warning("⚠️ Logo guardado localmente pero sin sincronización cloud.")
                            if storage_sync_error:
                                st.caption(f"Error: {storage_sync_error}")
                        
                        import time
                        time.sleep(1)
                        st.rerun()
                    
                    if st.button("✖️ Cancelar", use_container_width=True):
                        st.session_state.logo_staged = None
                        st.session_state.logo_last_hash = None
                        st.session_state.logo_uploader_key += 1
                        st.rerun()
