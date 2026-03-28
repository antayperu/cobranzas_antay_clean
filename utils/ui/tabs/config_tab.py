import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
import utils.settings_manager as sm
import utils.helpers as helpers
import utils.image_processor as img_proc
import utils.email_sender as es_diag # For diagnostic test
import utils.storage_manager as storage_mgr

def render_tab(config):
    """
    Renders the Configuration Global tab.
    Todas las secciones están colapsadas por defecto (expanded=False).
    Enter-to-submit deshabilitado en todos los formularios de texto.

    Args:
        config (dict): Global configuration.
    """
    # --- HEADER ---
    st.header("⚙️ Configuración del Sistema")
    st.markdown("Despliega cada sección para editar. Cada sección tiene su propio botón de guardar.")
    st.divider()

    # =========================================================================
    # SECCIÓN 1: IDENTIDAD CORPORATIVA + LOGO
    # =========================================================================
    with st.expander("🏢 Identidad Corporativa", expanded=False):
        try:
            _id_form_ctx = st.form(key="form_identidad", enter_to_submit=False)
        except TypeError:
            _id_form_ctx = st.form(key="form_identidad")
        with _id_form_ctx:
            st.caption("Nombre, RUC y teléfono de la empresa — aparecen en correos y documentos")
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
            _id_submitted = st.form_submit_button(
                "💾 Guardar Identidad", type="primary", use_container_width=True
            )
        if _id_submitted:
            _id_changed = (
                new_company != config.get('company_name') or
                new_ruc     != config.get('company_ruc') or
                new_phone   != config.get('phone_contact')
            )
            if _id_changed:
                config.update({"company_name": new_company, "company_ruc": new_ruc, "phone_contact": new_phone})
                if sm.save_settings(config):
                    st.toast("✅ Identidad guardada", icon="💾")
                    st.rerun()
                else:
                    st.error("❌ Error al guardar.")

        # --- Logo (dentro de Identidad, fuera del form) ---
        st.divider()
        st.markdown("##### 📸 Logo Empresarial")
        st.caption("Carga el logo que aparecerá en correos y documentos exportados")

        if 'logo_uploader_key' not in st.session_state:
            st.session_state.logo_uploader_key = 0
        if 'logo_staged' not in st.session_state:
            st.session_state.logo_staged = None

        current_logo_path = storage_mgr.resolve_logo_path(config) or config.get('logo_path')
        logo_active_exists = bool(current_logo_path and os.path.exists(current_logo_path))

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
                            st.success("✅ Logo eliminado.")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar cambios.")
            elif not logo_active_exists and st.session_state.logo_staged is None:
                st.info("🟡 **Sin Logo** — Los correos se enviarán sin logo. Carga uno en 'Cargar Nuevo'")
            elif st.session_state.logo_staged:
                st.info("📦 Tienes un logo en **revisión** (staging). Ve a 'Cargar Nuevo' para completar.")

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
                    raw_bytes = uploaded_logo.getbuffer()
                    file_hash = hashlib.md5(raw_bytes).hexdigest()
                    with st.spinner("Procesando logo..."):
                        proc_bytes, proc_w, proc_h = img_proc.process_logo_image(raw_bytes)
                        st.session_state.logo_staged = {
                            'bytes': proc_bytes, 'w': proc_w, 'h': proc_h,
                            'name': uploaded_logo.name, 'orig_bytes': raw_bytes
                        }
                        st.session_state.logo_last_hash = file_hash
                    st.rerun()
            with st.expander("ℹ️ Recomendaciones"):
                st.markdown("""
                - **Formato:** PNG (fondo transparente) o JPG
                - **Tamaño:** Mayor a 800px de ancho
                - **Automático:** Recorte y redimensión sin perder calidad
                """)
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
                    st.warning("⚠️ Cambios en staging — no se aplican hasta guardar")
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
                            st.success("✅ Logo guardado y sincronizado.")
                        else:
                            st.warning("⚠️ Logo guardado localmente sin sincronización cloud.")
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

    # =========================================================================
    # SECCIÓN 2: BRANDING & COLORES
    # =========================================================================
    with st.expander("🎨 Branding & Colores", expanded=False):
        try:
            _brand_form_ctx = st.form(key="form_branding", enter_to_submit=False)
        except TypeError:
            _brand_form_ctx = st.form(key="form_branding")
        with _brand_form_ctx:
            st.caption("Paleta de colores corporativa usada en correos y reportes")
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
            _brand_submitted = st.form_submit_button(
                "💾 Guardar Branding", type="primary", use_container_width=True
            )
        if _brand_submitted:
            _brand_changed = (
                new_primary    != config.get('primary_color') or
                new_secondary  != config.get('secondary_color') or
                new_text_color != config.get('text_color', '#262730')
            )
            if _brand_changed:
                config.update({"primary_color": new_primary, "secondary_color": new_secondary, "text_color": new_text_color})
                if sm.save_settings(config):
                    st.toast("✅ Branding guardado", icon="🎨")
                    st.rerun()
                else:
                    st.error("❌ Error al guardar.")

    # =========================================================================
    # SECCIÓN 3: FUNCIONALIDADES
    # =========================================================================
    with st.expander("📊 Funcionalidades", expanded=False):
        with st.form(key="form_funcionalidades"):
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
            _feat_submitted = st.form_submit_button(
                "💾 Guardar Funcionalidades", type="primary", use_container_width=True
            )
        if _feat_submitted:
            _feat_changed = (
                f_analysis != config.get('features', {}).get('show_analysis', False) or
                f_sales    != config.get('features', {}).get('show_sales', False)
            )
            if _feat_changed:
                config.update({"features": {"show_analysis": f_analysis, "show_sales": f_sales}})
                if sm.save_settings(config):
                    st.toast("✅ Funcionalidades guardadas", icon="📊")
                    st.rerun()
                else:
                    st.error("❌ Error al guardar.")

    # =========================================================================
    # SECCIÓN 4: CORREO ELECTRÓNICO (SMTP)
    # =========================================================================
    with st.expander("📧 Correo Electrónico (SMTP)", expanded=False):
        # Estado dinámico basado en session_state
        smtp_status = st.session_state.get('smtp_test_ok', False)
        smtp_tested_user = st.session_state.get('smtp_test_user', '')
        saved_smtp_user = config['smtp_config'].get('user', '')

        # Indicador de Estado — muestra el correo guardado para evitar confusión prod/staging
        col_status, col_actions = st.columns([3, 1])
        with col_status:
            if smtp_status and smtp_tested_user:
                st.caption(f"🟢 **Estado:** Operativo  ·  `{smtp_tested_user}`")
            elif saved_smtp_user:
                st.caption(f"🟡 **Estado:** Pendiente de validación  ·  Guardado: `{saved_smtp_user}`")
            else:
                st.caption("🔴 **Estado:** Sin configurar — completa las credenciales y guarda")
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
        
        # ---- FORM: SMTP — input batching, zero rerenders mientras tipeas ----
        # enter_to_submit=False evita submits accidentales con Enter en los inputs.
        try:
            _smtp_form_ctx = st.form(key="form_smtp", enter_to_submit=False)
        except TypeError:
            # Compatibilidad con versiones antiguas de Streamlit.
            _smtp_form_ctx = st.form(key="form_smtp")

        with _smtp_form_ctx:
            st.caption("Edita las credenciales y haz clic en **Guardar SMTP** para aplicar.")

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

            # NOTA: disabled= dentro de st.form no funciona porque los valores de
            # los widgets solo se envían a Python al hacer submit (no mientras el
            # usuario escribe). Por eso ambos botones siempre están habilitados y
            # la validación se hace en los handlers de abajo, tras el submit.
            st.write("")
            col_smtp_test, col_smtp_save, col_smtp_hint = st.columns([1, 1, 2])
            with col_smtp_test:
                _smtp_test_submitted = st.form_submit_button(
                    "🔍 Probar Conexión", type="secondary", use_container_width=True
                )
            with col_smtp_save:
                _smtp_submitted = st.form_submit_button(
                    "💾 Guardar SMTP", type="primary", use_container_width=True
                )
            with col_smtp_hint:
                st.caption("💡 Flujo recomendado: **1) Guardar SMTP  2) Probar Conexión**.")

        # Probar Conexión con credenciales del formulario (no requiere guardar)
        if _smtp_test_submitted:
            _missing = [f for f, v in [
                ("Servidor", new_smtp_server), ("Puerto", new_smtp_port),
                ("Usuario", new_smtp_user), ("Contraseña", new_smtp_pass)
            ] if not str(v).strip()]
            if _missing:
                st.warning(f"⚠️ Completa los campos requeridos: {', '.join(_missing)}")
            else:
                test_smtp_cfg = {
                    "server": new_smtp_server,
                    "port": new_smtp_port,
                    "user": new_smtp_user,
                    "password": new_smtp_pass,
                    "resend_api_key": config['smtp_config'].get('resend_api_key', ''),
                    "sendgrid_api_key": config['smtp_config'].get('sendgrid_api_key', ''),
                    "force_smtp": force_smtp,
                }
                with st.spinner("Realizando diagnóstico..."):
                    diag_stats = es_diag.test_smtp_connectivity(test_smtp_cfg)
                    if diag_stats['ok']:
                        st.session_state['smtp_test_ok'] = True
                        st.session_state['smtp_test_user'] = new_smtp_user
                    else:
                        st.session_state['smtp_test_ok'] = False
                        st.session_state['smtp_test_user'] = ''
                    st.session_state['smtp_diag_result'] = diag_stats
                st.rerun()

        # Submission handler — guarda siempre que sea enviado
        if _smtp_submitted:
            if not any([str(new_smtp_server).strip(), str(new_smtp_user).strip()]):
                st.warning("⚠️ Ingresa al menos el servidor y el usuario antes de guardar.")
            else:
                config['smtp_config'].update({
                    "server":   new_smtp_server,
                    "port":     new_smtp_port,
                    "user":     new_smtp_user,
                    "password": new_smtp_pass,
                    "force_smtp": force_smtp,
                })
                if sm.save_settings(config):
                    st.session_state['smtp_test_ok'] = False
                    st.session_state['smtp_test_user'] = ''
                    st.session_state['smtp_diag_result'] = None
                    st.success(f"✅ SMTP guardado · `{new_smtp_user}` — valida con **Probar Conexión**.")
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar SMTP.")

        _smtp_diag_result = st.session_state.get('smtp_diag_result')
        if _smtp_diag_result:
            if _smtp_diag_result.get('ok'):
                st.success(_smtp_diag_result.get('msg', 'Conexión SMTP validada.'))
            else:
                st.error(_smtp_diag_result.get('msg', 'Error en diagnóstico SMTP.'))
            with st.expander("Ver detalles técnicos"):
                for l in _smtp_diag_result.get('log', []):
                    st.text(l)

    # =========================================================================
    # SECCIÓN 5: PLANTILLAS DE CORREO
    # =========================================================================
    with st.expander("📝 Plantillas de Correo", expanded=False):
        _tmpl = config.get('email_template', {})

        # Helper: leer cuentas bancarias del config
        def _get_cuentas(moneda: str) -> list:
            key = f"cuentas_{moneda}"
            cuentas = _tmpl.get(key, [])
            if not isinstance(cuentas, list):
                return []
            return cuentas

        _cuentas_sol = _get_cuentas("sol")
        _cuentas_usd = _get_cuentas("usd")

        # Valores por defecto para cuentas (hasta 2 en soles, 1 en USD)
        def _cuenta_val(lista: list, idx: int, campo: str) -> str:
            try:
                return lista[idx].get(campo, "") or ""
            except IndexError:
                return ""

        # ------ Chips de variables disponibles ------
        _VARS_EMAIL = ["{CLIENTE}", "{DEUDA_SOL}", "{DOCS_SOL}", "{DEUDA_USD}", "{DOCS_USD}", "{DETRACCION}", "{FECHA}"]
        _VARS_PDF   = ["{CLIENTE}"]
        _vars_chip_email = " &nbsp; ".join(f"<code style='background:#EEF4FB;color:#0D3B66;padding:2px 7px;border-radius:4px;font-size:12px'>{v}</code>" for v in _VARS_EMAIL)
        _vars_chip_pdf   = " &nbsp; ".join(f"<code style='background:#EEF4FB;color:#0D3B66;padding:2px 7px;border-radius:4px;font-size:12px'>{v}</code>" for v in _VARS_PDF)

        try:
            _plant_form_ctx = st.form(key="form_plantillas", enter_to_submit=False)
        except TypeError:
            _plant_form_ctx = st.form(key="form_plantillas")

        with _plant_form_ctx:

            # ── SECCIÓN A: CORREO ELECTRÓNICO ─────────────────────────────────
            st.markdown("#### 📧 Correo Electrónico")
            st.caption("Define el asunto y el cuerpo breve del correo que recibirá el cliente.")
            st.markdown(f"**Variables disponibles:** {_vars_chip_email}", unsafe_allow_html=True)
            st.markdown("")

            new_subject = st.text_input(
                "Asunto del correo",
                value=_tmpl.get("email_subject", "Estado de Cuenta | {CLIENTE}"),
                help="Línea de asunto. Usa {CLIENTE} para incluir el nombre de la empresa.",
                key="planta_subject"
            )
            new_email_body = st.text_area(
                "Cuerpo del mensaje",
                value=_tmpl.get("email_body_text", ""),
                height=110,
                help="Texto principal del correo. Breve y directo. El resumen de deuda se inserta automáticamente.",
                key="planta_email_body"
            )

            st.divider()

            # ── SECCIÓN B: CABECERA DEL DOCUMENTO PDF ─────────────────────────
            st.markdown("#### 📄 Cabecera del Documento PDF")
            st.caption("Título que aparece en la parte superior del documento Estado de Cuenta.")

            new_pdf_title = st.text_input(
                "Título del documento",
                value=_tmpl.get("pdf_title", "ESTADO DE CUENTA"),
                help="Ejemplo: ESTADO DE CUENTA · NOTIFICACIÓN DE COBRANZA",
                key="planta_pdf_title"
            )

            st.divider()

            # ── SECCIÓN C: CUERPO DE LA CARTA (PDF) ───────────────────────────
            st.markdown("#### ✉️ Cuerpo de la Carta (PDF)")
            st.caption("Texto que se dirige directamente al cliente en el documento PDF.")
            st.markdown(f"**Variables disponibles:** {_vars_chip_pdf}", unsafe_allow_html=True)
            st.markdown("")

            new_pdf_saludo = st.text_input(
                "Saludo / Apertura",
                value=_tmpl.get("pdf_saludo", "Estimado cliente: {CLIENTE},"),
                help="Primera línea de la carta. Usa {CLIENTE} para personalizar.",
                key="planta_pdf_saludo"
            )
            new_intro = st.text_area(
                "Texto introductorio",
                value=_tmpl.get("intro_text", ""),
                height=100,
                help="Párrafo principal de la carta. Explica el motivo del documento.",
                key="planta_intro"
            )

            st.divider()

            # ── SECCIÓN D: ALERTA DE DETRACCIÓN ───────────────────────────────
            st.markdown("#### ⚠️ Alerta de Detracción SUNAT")
            st.caption("Este bloque aparece en el PDF **solo si** el cliente tiene documentos afectos a detracción. Déjalo vacío para no mostrar nada.")

            new_alert = st.text_area(
                "Texto de alerta detracción",
                value=_tmpl.get("alert_text", ""),
                height=80,
                help="Instrucción sobre el Banco de la Nación y número de cuenta de detracciones.",
                key="planta_alert"
            )

            st.divider()

            # ── SECCIÓN E: INFORMACIÓN DE PAGO ────────────────────────────────
            st.markdown("#### 🏦 Información de Pago")
            st.caption("Cuentas bancarias que aparecerán tanto en el correo como en el PDF. Deja vacío los campos que no apliquen.")

            st.markdown("**Cuentas en Soles (S/)**")
            _col_s1, _col_s2 = st.columns(2)
            with _col_s1:
                new_sol_b1_banco  = st.text_input("Banco 1 — Nombre",  value=_cuenta_val(_cuentas_sol, 0, "banco"),  key="planta_sol_b1_banco", placeholder="BCP")
                new_sol_b1_num    = st.text_input("Banco 1 — Número",  value=_cuenta_val(_cuentas_sol, 0, "numero"), key="planta_sol_b1_num",   placeholder="1234567890")
                new_sol_b1_cci    = st.text_input("Banco 1 — CCI",     value=_cuenta_val(_cuentas_sol, 0, "cci"),    key="planta_sol_b1_cci",   placeholder="00210300...")
            with _col_s2:
                new_sol_b2_banco  = st.text_input("Banco 2 — Nombre",  value=_cuenta_val(_cuentas_sol, 1, "banco"),  key="planta_sol_b2_banco", placeholder="BBVA")
                new_sol_b2_num    = st.text_input("Banco 2 — Número",  value=_cuenta_val(_cuentas_sol, 1, "numero"), key="planta_sol_b2_num",   placeholder="0011034...")
                new_sol_b2_cci    = st.text_input("Banco 2 — CCI",     value=_cuenta_val(_cuentas_sol, 1, "cci"),    key="planta_sol_b2_cci",   placeholder="01134000...")

            st.markdown("**Cuentas en Dólares (US$)**")
            _col_u1, _col_u2 = st.columns(2)
            with _col_u1:
                new_usd_b1_banco  = st.text_input("Banco 1 — Nombre",  value=_cuenta_val(_cuentas_usd, 0, "banco"),  key="planta_usd_b1_banco", placeholder="BCP")
                new_usd_b1_num    = st.text_input("Banco 1 — Número",  value=_cuenta_val(_cuentas_usd, 0, "numero"), key="planta_usd_b1_num",   placeholder="1912078...")
                new_usd_b1_cci    = st.text_input("Banco 1 — CCI",     value=_cuenta_val(_cuentas_usd, 0, "cci"),    key="planta_usd_b1_cci",   placeholder="00219100...")

            st.markdown("**Datos de contacto para pagos**")
            _col_c1, _col_c2 = st.columns(2)
            with _col_c1:
                new_contact_email = st.text_input(
                    "Correo para envío de vouchers",
                    value=_tmpl.get("contact_email", ""),
                    key="planta_contact_email",
                    placeholder="cobranzas@empresa.com"
                )
            with _col_c2:
                new_contact_phone = st.text_input(
                    "Teléfono de consulta",
                    value=_tmpl.get("contact_phone", ""),
                    key="planta_contact_phone",
                    placeholder="+51 999 000 000"
                )
            new_voucher = st.text_area(
                "Instrucciones adicionales de pago (opcional)",
                value=_tmpl.get("voucher_text", ""),
                height=60,
                help="Texto libre para instrucciones específicas. Déjalo vacío para no mostrar.",
                key="planta_voucher"
            )

            st.divider()

            # ── SECCIÓN F: PIE DE PÁGINA Y FIRMA ──────────────────────────────
            st.markdown("#### 📝 Pie de Página y Firma")
            st.caption("Texto final del documento y cargo del área que firma.")

            new_footer = st.text_area(
                "Texto de cierre / pie de página",
                value=_tmpl.get("footer_text", ""),
                height=100,
                help='Incluye siempre: "En caso de haber realizado el pago recientemente, por favor hacer caso omiso a este mensaje."',
                key="planta_footer"
            )
            new_firma_cargo = st.text_input(
                "Cargo para la firma",
                value=_tmpl.get("firma_cargo", "Area de Cobranzas y Facturacion"),
                help="Ejemplo: Área de Cobranzas y Facturación",
                key="planta_firma_cargo"
            )

            st.markdown("")
            _plant_submitted = st.form_submit_button(
                "💾 Guardar Plantillas", type="primary", use_container_width=True
            )

        if _plant_submitted:
            # Reconstruir cuentas bancarias desde los campos del formulario
            _new_cuentas_sol = []
            if new_sol_b1_banco.strip() or new_sol_b1_num.strip():
                _new_cuentas_sol.append({"banco": new_sol_b1_banco.strip(), "numero": new_sol_b1_num.strip(), "cci": new_sol_b1_cci.strip()})
            if new_sol_b2_banco.strip() or new_sol_b2_num.strip():
                _new_cuentas_sol.append({"banco": new_sol_b2_banco.strip(), "numero": new_sol_b2_num.strip(), "cci": new_sol_b2_cci.strip()})

            _new_cuentas_usd = []
            if new_usd_b1_banco.strip() or new_usd_b1_num.strip():
                _new_cuentas_usd.append({"banco": new_usd_b1_banco.strip(), "numero": new_usd_b1_num.strip(), "cci": new_usd_b1_cci.strip()})

            _new_tmpl = {
                # Correo
                "email_subject":   new_subject.strip(),
                "email_body_text": new_email_body,
                # PDF cabecera
                "pdf_title":       new_pdf_title.strip(),
                # PDF cuerpo
                "pdf_saludo":      new_pdf_saludo.strip(),
                "intro_text":      new_intro,
                # Alerta
                "alert_text":      new_alert,
                # Cuentas
                "cuentas_sol":     _new_cuentas_sol,
                "cuentas_usd":     _new_cuentas_usd,
                "contact_email":   new_contact_email.strip(),
                "contact_phone":   new_contact_phone.strip(),
                "voucher_text":    new_voucher,
                # Pie y firma
                "footer_text":     new_footer,
                "firma_cargo":     new_firma_cargo.strip(),
            }

            _plant_changed = _new_tmpl != {k: _tmpl.get(k) for k in _new_tmpl}
            if not _plant_changed:
                st.info("✅ Sin cambios en plantillas.")
            else:
                config['email_template'] = _new_tmpl
                if sm.save_settings(config):
                    st.toast("✅ Plantillas actualizadas", icon="📝")
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar las plantillas.")

    # =========================================================================
    # SECCIÓN 6: COPIAS INTERNAS (CC / CCO)
    # =========================================================================
    with st.expander("👥 Copias Internas (CC / CCO)", expanded=False):
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

    # =========================================================================
    # SECCIÓN 7: WHATSAPP — DISPOSITIVO DE ENVÍO
    # =========================================================================
    with st.expander("📱 WhatsApp — Dispositivo de Envío", expanded=False):
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
                    spinner_container = st.empty()
                    result_container = st.empty()
                    
                    with spinner_container.container():
                        with st.spinner("Abriendo Chrome — escanea el QR en el navegador..."):
                            try:
                                ok, phone, profile, err = connect_wa_session(timeout_seconds=120)
                            except Exception as e:
                                import traceback
                                err = f"EXCEPTION: {str(e)}\n\n{traceback.format_exc()}"
                                ok = False
                                phone = ""
                                profile = ""
                    
                    # Limpiar spinner
                    spinner_container.empty()
                    
                    # Mostrar resultado
                    with result_container.container():
                        if ok:
                            _label = f"**{profile}**" if profile else "dispositivo"
                            _ph    = f" (`{phone}`)" if phone else ""
                            st.success(f"✅ Sesión conectada: {_label}{_ph}")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {err}")

    st.divider()

    # =========================================================================
    # SECCIÓN 8: MENSAJE DE PRUEBA WHATSAPP (RC-FEAT-026)
    # =========================================================================
    with st.expander("🧪 Mensaje de Prueba WhatsApp", expanded=False):
        st.caption("Envía un mensaje de prueba a un número para verificar que la conexión WA funciona correctamente")

        from utils.whatsapp_sender import send_whatsapp_messages_direct, get_wa_session_info

        _wa_activo = get_wa_session_info().get("status") == "active"
        if not _wa_activo:
            st.warning("⚠️ No hay sesión WhatsApp activa. Conéctala primero en la sección **📱 WhatsApp — Dispositivo de Envío**.")
        else:
            col_test_phone, col_test_speed = st.columns([2, 1])
            with col_test_phone:
                test_phone = st.text_input(
                    "Número destino (con código de país)",
                    value="+51921566036",
                    key="wa_test_phone",
                    help="Formato: +51XXXXXXXXX",
                )
            with col_test_speed:
                test_speed = st.selectbox(
                    "Velocidad",
                    ["Normal (Recomendado)", "Rápida", "Lenta (Más seguro)"],
                    key="wa_test_speed",
                )

            test_msg = st.text_area(
                "Mensaje de prueba",
                value="🧪 *Mensaje de prueba* — ReporteCobranzas Antay.\n\nSi recibes esto, la conexión WhatsApp funciona correctamente. ✅",
                height=100,
                key="wa_test_message",
            )

            if st.button("📤 Enviar Prueba", type="primary", use_container_width=False, key="btn_wa_send_test"):
                if not test_phone.strip():
                    st.error("❌ Ingresa un número de destino.")
                elif not test_msg.strip():
                    st.error("❌ El mensaje no puede estar vacío.")
                else:
                    dummy_contact = {
                        "telefono":       test_phone.strip(),
                        "nombre_cliente": "Prueba",
                        "nombre":         "Prueba",
                        "Empresa":        "Prueba",
                        "SaldoReal":      0,
                    }
                    with st.spinner(f"Enviando mensaje de prueba a {test_phone.strip()}..."):
                        try:
                            resultado = send_whatsapp_messages_direct(
                                contacts=[dummy_contact],
                                message=test_msg,
                                speed=test_speed,
                                send_mode="texto",
                            )
                        except Exception as e:
                            resultado = {"exitosos": 0, "fallidos": 1, "errores": [str(e)]}

                    if resultado.get("exitosos", 0) > 0:
                        st.success(f"✅ Mensaje enviado correctamente a `{test_phone.strip()}`.")
                        st.toast("✅ Prueba WA exitosa", icon="✅")
                    else:
                        errs = resultado.get("errores", [])
                        detalle = errs[0] if errs else "Error desconocido"
                        st.error(f"❌ No se pudo enviar el mensaje.\n\n**Detalle:** {detalle}")

    st.divider()

    # --- SECTION 9: OPCIONES AVANZADAS ---
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
