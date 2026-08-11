# FIX: Aplicar nest_asyncio y usar ProactorEventLoop en Windows
# Esto permite que asyncio.run() + Playwright funcione correctamente dentro de Streamlit
import asyncio
import sys

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# En Windows, usar ProactorEventLoop para subprocesses async (requerido por Playwright)
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception as e:
        print(f"[WARN] No se pudo configurar ProactorEventLoop: {e}")

import streamlit as st
import pandas as pd
from datetime import datetime
import os

from utils.processing import process_data
# utils.excel_export moved to specific tabs

# Configuración de Página
import utils.settings_manager as sm
import utils.helpers as helpers
import utils.db_manager as dbm
import utils.ui.styles as styles        # Antay Design System
import utils.session as session_lib   # Session Management
import utils.ui.sidebar as ui_sidebar   # New Wizard Sidebar
import utils.ui.report_view as ui_report # New Report Table
import utils.ui.tabs.whatsapp as tab_whatsapp # WhatsApp Tab Module
import utils.ui.tabs.general_report as tab_general # General Report Tab Module
import utils.ui.tabs.email_notifications as tab_email # Email Notifications Tab Module
import utils.ui.tabs.clientes_premium as tab_clientes_premium # Premium Clients Tab Module
import utils.ui.tabs.crm_gestiones as tab_crm  # CRM & Gestiones Tab Module
import utils.ui.tabs.config_tab as tab_config # Configuration Tab Module
import utils.ui.tabs.dashboard as tab_dashboard  # RC-FEAT-038 Dashboard de Efectividad
import utils.supabase_cycle_service as supabase_cycle_service
import utils.storage_manager as storage_mgr
import utils.state_manager as state_mgr
import streamlit.components.v1 as components

# ... (rest of imports)

# Cargar Configuración Global
# Se guarda en session_state para que save_settings() + st.rerun() reflejen
# los cambios sin necesidad de reiniciar la app completa.
if 'app_config' not in st.session_state:
    st.session_state['app_config'] = sm.load_settings()
CONFIG = st.session_state['app_config']

# --- RC-UX-PREMIUM: Page Layout Wide & Corporate Title ---
st.set_page_config(
    page_title=CONFIG.get('company_name', 'Antay Reportes'),
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INYECTAR ENTERPRISE CSS ---
styles.load_css()

# --- VISTA NORMAL ---

# --- RC-UX-PREMIUM: Enterprise CSS System ---
# Typography: System UI for speed + clear hierarchy
# Spacing: More padding for "breathing room"
# Cards: Subtle shadows (Glassmorphism lite)


# --- CLOUD-ONLY: remove stale local cache/session artifacts ---
session_lib.enforce_cloud_only_policy()

# Sidebar - Logo y Carga
with st.sidebar:
    # Logo
    logo_path = storage_mgr.resolve_logo_path(CONFIG)
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
        CONFIG["logo_path"] = logo_path
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown(f"## {CONFIG['company_name']}")

    # Logo only — ciclos y recovery se gestionan en render_sidebar()
    


# --- INIT SESSION STATE (CRITICAL) ---
session_lib.init_session_state()

# --- CLOUD-ONLY HEALTH CHECK ---
if not dbm.initialize_db():
    st.error("Supabase no esta disponible. Operacion bloqueada hasta restablecer conexion.")
    st.caption(dbm.get_last_error() or "Sin detalle tecnico de conexion.")
    st.stop()

# --- CRM: AUTO-RESTORE del último ciclo al abrir la app ---
# Si Supabase tiene ciclos guardados, el más reciente se carga automáticamente.
# El gestor llega directamente a los tabs (WA, Email, CRM) sin interacción previa.
# Si no hay ciclos, se muestra el selector/upload en la barra lateral como siempre.
if not st.session_state.get("data_ready", False) and not st.session_state.get("loading_new_files", False) and not st.session_state.get("skip_auto_restore", False):
    with st.spinner("Conectando con Supabase y restaurando sesión..."):
        session_lib.attempt_auto_restore()

# Render Sidebar Wizard
wizard_action = ui_sidebar.render_sidebar()

# Check trigger from Sidebar
if wizard_action == "PROCESS_TRIGGERED":
    # Get files from session (set by sidebar)
    file_ctas = st.session_state['uploaded_files']['ctas']
    file_cobranza = st.session_state['uploaded_files']['cobranza']
    
    if file_ctas and file_cobranza:
        with st.status("🚀 Generando ciclo nuevo...", expanded=True) as _cycle_status:
            # Flujo oficial: 2 archivos + cartera maestra en Supabase.
            try:
                st.write("📂 Leyendo archivos Excel...")
                df_ctas_raw = pd.read_excel(file_ctas)
                df_cobranza_raw = pd.read_excel(file_cobranza)

                st.write("☁️ Descargando cartera maestra desde Supabase...")
                cartera_rows = dbm.get_clientes_master(limit=50000)
                if not cartera_rows:
                    _detail = dbm.get_last_error()
                    error = (
                        "No hay cartera maestra en Supabase. "
                        "Gestiona o migra clientes en la TAB Clientes Premium y vuelve a procesar."
                    )
                    if _detail:
                        error += f" — Detalle: {_detail}"
                    df_cartera_raw = pd.DataFrame()
                else:
                    df_cartera_raw = pd.DataFrame(cartera_rows).rename(
                        columns={
                            "cliente_id": "codigo_cliente",
                            "nombre": "nombre_cliente",
                            "email": "correo",
                            "enviar_email": "Enviar Email",
                            "estado": "estado_cliente",
                            "notas": "nota",
                        }
                    )
                    error = None
            except Exception as e_load_2files:
                df_ctas_raw, df_cartera_raw, df_cobranza_raw = None, None, None
                error = str(e_load_2files)

            if error:
                _cycle_status.update(label="❌ Error al cargar archivos", state="error")
                st.error(f"❌ Error de Carga: {error}")
                st.session_state['data_ready'] = False
            else:
                # ── VALIDACIÓN DE INTEGRIDAD: todos los COD CLIENTE del CxC deben existir en clientes ──
                if 'codcli' in df_ctas_raw.columns:
                    _cxc_codes = set(
                        df_ctas_raw['codcli'].astype(str).str.strip().str.zfill(6)
                    )
                    _clientes_codes = set(
                        str(r['cliente_id']).strip()
                        for r in cartera_rows
                        if r.get('cliente_id')
                    )
                    _missing_codes = _cxc_codes - _clientes_codes

                    if _missing_codes:
                        _names_map = {}
                        if 'nomcli' in df_ctas_raw.columns:
                            _names_map = (
                                df_ctas_raw
                                .assign(_cod=df_ctas_raw['codcli'].astype(str).str.strip().str.zfill(6))
                                .groupby('_cod')['nomcli'].first()
                                .to_dict()
                            )
                        _df_missing = pd.DataFrame({
                            'COD CLIENTE': sorted(_missing_codes),
                            'EMPRESA (según CxC)': [_names_map.get(c, '—') for c in sorted(_missing_codes)],
                        })
                        _cycle_status.update(label="⛔ Error de integridad — clientes faltantes", state="error")
                        st.error(
                            f"⛔ Error de Integridad: {len(_missing_codes)} cliente(s) del archivo CxC "
                            "no están registrados en la tabla maestra de clientes (Supabase)."
                        )
                        st.warning(
                            "El proceso ha sido **cancelado**. Ve a la pestaña **Clientes Premium → Importar** "
                            "para registrar los clientes faltantes y vuelve a intentar."
                        )
                        st.dataframe(_df_missing, use_container_width=True, hide_index=True)
                        st.caption(
                            "💡 Consejo: Anota o exporta estos códigos, agrégalos en Clientes Premium, "
                            "luego presiona 'Procesar' nuevamente."
                        )
                        st.session_state['data_ready'] = False
                        st.stop()

                try:
                    st.write("⚙️ Procesando y cruzando datos...")
                    df_final = process_data(df_ctas_raw, df_cartera_raw, df_cobranza_raw)

                    # --- CYCLE_ID: Generar ID único para este ciclo (formato legible) ---
                    from datetime import datetime
                    cycle_id = datetime.now().strftime('CIC-%Y%m%d-%H%M')

                    st.session_state['df_final'] = df_final
                    st.session_state['data_ready'] = True

                    # FIX: Resetear flag de carga nueva después de procesar exitosamente
                    st.session_state['loading_new_files'] = False

                    # Mark as fresh load (for tracking init)
                    st.session_state['fresh_load'] = True
                    st.session_state['cycle_id'] = cycle_id

                    # --- LIMPIEZA TTL: Purgar bloqueos del ciclo anterior ---
                    st.write("🧹 Preparando ciclo en Supabase...")
                    if not dbm.clear_all_ledger():
                        st.session_state['data_ready'] = False
                        _cycle_status.update(label="❌ Error al preparar ciclo en Supabase", state="error")
                        st.error("No se pudo preparar el ciclo en Supabase. Operacion bloqueada.")
                        st.caption(dbm.get_last_error() or "Fallo al limpiar control TTL en ledger_last_send.")
                        st.stop()

                    # --- PERSISTENCIA DEL CICLO EN SUPABASE (UI -> DB) ---
                    st.write("💾 Guardando clientes, documentos y cobranzas en Supabase...")
                    persist_result = supabase_cycle_service.persist_cycle_to_supabase(
                        df_ctas=df_ctas_raw,
                        df_cartera=df_cartera_raw,
                        df_cobranza=df_cobranza_raw,
                    )
                    if not persist_result.get("ok", False):
                        st.session_state['data_ready'] = False
                        _cycle_status.update(label="❌ Error al guardar ciclo en Supabase", state="error")
                        st.error("No se pudo persistir el ciclo en Supabase. Operacion bloqueada.")
                        st.caption(persist_result.get("message", "Error no especificado en persistencia."))
                        st.stop()

                    counts = persist_result.get("counts", {})
                    st.toast(
                        f"Supabase OK: clientes={counts.get('clientes', 0)}, "
                        f"documentos={counts.get('documentos', 0)}, "
                        f"cobranzas={counts.get('cobranzas', 0)}",
                        icon="✅",
                    )
                    errors = persist_result.get("errors", {})
                    if errors.get("cobranzas", 0) > 0:
                        st.warning(
                            f"Se detectaron {errors.get('cobranzas', 0)} filas de cobranza sin match documental. "
                            "No fueron insertadas por regla de integridad."
                        )

                    # --- RC-FEAT-023: TRAZABILIDAD — reconcile recovery vs ciclo anterior ---
                    st.write("🔍 Verificando trazabilidad con ciclo anterior...")
                    _prev_cycle = dbm.get_prev_cycle_id(cycle_id)
                    if _prev_cycle:
                        _rec_result = dbm.reconcile_ciclo_recovery(
                            cycle_id_anterior=_prev_cycle,
                            cycle_id_nuevo=cycle_id,
                        )
                        if _rec_result.get("ok"):
                            _s = _rec_result["stats"]
                            st.toast(
                                f"🔍 Trazabilidad: {_s.get('docs_recuperados', 0)} docs recuperados "
                                f"({_s.get('tasa_recuperacion', 0)}%)",
                                icon="📊",
                            )

                    # Mark session start
                    st.session_state['session_start_ts'] = datetime.now()

                    # Mark as fresh load (for tracking init)
                    st.session_state['fresh_load'] = True
                    st.session_state['restored_from_cloud'] = False

                    # --- GUARDAR SESION EN CLOUD ---
                    st.write("☁️ Guardando sesión en la nube...")
                    ok_cloud, msg_cloud = state_mgr.save_session_cloud(
                        df=df_final,
                        cycle_id=cycle_id,
                        metadata={
                            "cycle_id": cycle_id,
                            "file_ctas": file_ctas.name if file_ctas else None,
                            "file_cobranza": file_cobranza.name if file_cobranza else None,
                            "fecha_corte": str(st.session_state.get('config_fecha_corte', '')),
                            "row_count": len(df_final),
                            "columns": list(df_final.columns),
                            "cycle_timestamp": cycle_id,
                        },
                    )
                    if not ok_cloud:
                        st.session_state['data_ready'] = False
                        st.session_state['df_final'] = pd.DataFrame()
                        _cycle_status.update(label="❌ Error al guardar sesión en la nube", state="error")
                        st.error("No se pudo guardar el ciclo en Supabase. Operacion bloqueada.")
                        st.caption(msg_cloud or "Persistencia de ciclo fallida en cloud.")
                        st.stop()

                    st.toast("Sesion guardada en la nube", icon="☁️")
                    _cycle_status.update(label="✅ Ciclo generado exitosamente", state="complete")
                    st.session_state['_cycle_just_created'] = cycle_id
                    st.rerun()
                except Exception as e:
                    _cycle_status.update(label="❌ Error inesperado en el procesamiento", state="error")
                    st.error(f"❌ Error de Procesamiento: {e}")
                    st.session_state['data_ready'] = False

    # Main Area Placeholder if no data
    if not st.session_state.get('data_ready', False):
        st.info("👈 Utiliza el panel lateral para cargar tus archivos y comenzar.")

# --- PASO 2: VISUALIZACIÓN Y FILTROS ---
if st.session_state['data_ready']:
    _new_cycle_id = st.session_state.pop('_cycle_just_created', None)
    if _new_cycle_id:
        st.success(f"✅ Ciclo **{_new_cycle_id}** generado correctamente — los datos están listos para operar.")

    df_final = st.session_state['df_final']
    # RC-FIX-SCOPE: Initialize df_filtered safely to avoid NameError if df_final is empty
    df_filtered = pd.DataFrame()
    
    # Check Session TS
    if 'session_start_ts' not in st.session_state:
         # Fallback if coming from old session without TS, use Today 00:00 or Now?
         # Logic: If restoring old session, we want to see history.
         # Ideally load_session should provide the TS. For now, default to Today Start.
         st.session_state['session_start_ts'] = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    st.markdown("---")
    
    # DEFINIR TABS DINÁMICAMENTE
    tab_list = ["Reporte General"]
    
    # Feature Flags
    show_analysis = CONFIG.get("features", {}).get("show_analysis", False)
    show_sales = CONFIG.get("features", {}).get("show_sales", False)
    
    if show_analysis: tab_list.append("2. Análisis")
    if show_sales: tab_list.append("3. Ventas")
    
    tab_list.extend(
        [
            "4. Marketing WhatsApp",
            "5. Notificaciones Email",
            "6. Clientes Premium",
            "7. Centro de Gestiones",
            "8. Dashboard",
            "9. Configuración",
        ]
    )
    
    tabs = st.tabs(tab_list)
    
    # Mapper de tabs para acceso seguro
    tab_map = {name: tab for name, tab in zip(tab_list, tabs)}
    
    # --- TAB 1: REPORTE GENERAL ---
    with tab_map["Reporte General"]:
        # Logic extracted to utils/ui/tabs/general_report.py
        df_filtered = tab_general.render_tab(df_final, CONFIG)

    # --- TABS CONDICIONALES ---
    if show_analysis and "2. Análisis" in tab_map:
        with tab_map["2. Análisis"]:
            st.info("Próximamente: Análisis en Profundidad")
            
    if show_sales and "3. Ventas" in tab_map:
        with tab_map["3. Ventas"]:
            st.info("Próximamente: Reporte de Ventas")

    # --- TAB 4: WHATSAPP ---
    with tab_map["4. Marketing WhatsApp"]:
        tab_whatsapp.render_tab(df_filtered, CONFIG)
    
    # --- TAB 5: EMAIL ---
    with tab_map["5. Notificaciones Email"]:
        # Logic extracted to utils/ui/tabs/email_notifications.py
        tab_email.render_tab(df_final, df_filtered, CONFIG)

    # --- TAB 6: CLIENTES PREMIUM ---
    with tab_map["6. Clientes Premium"]:
        tab_clientes_premium.render_tab(df_final, CONFIG)

    # --- TAB 7: CENTRO DE GESTIONES (CRM) ---
    with tab_map["7. Centro de Gestiones"]:
        tab_crm.render_tab(df_final, CONFIG)

    # --- TAB 8: DASHBOARD DE EFECTIVIDAD (RC-FEAT-038) ---
    with tab_map["8. Dashboard"]:
        tab_dashboard.render_tab(df_final, CONFIG)

    # --- TAB 9: CONFIGURACIÓN GLOBAL ---
    with tab_map["9. Configuración"]:
        # Logic extracted to utils/ui/tabs/config_tab.py
        tab_config.render_tab(CONFIG)

else:
    # Permitir operacion de clientes/config/CRM incluso sin ciclo cargado.
    base_tabs = st.tabs(["Inicio", "6. Clientes Premium", "7. Centro de Gestiones", "8. Configuración"])

    with base_tabs[0]:
        st.markdown(styles.get_welcome_html(), unsafe_allow_html=True)

    with base_tabs[1]:
        tab_clientes_premium.render_tab(pd.DataFrame(), CONFIG)

    with base_tabs[2]:
        tab_crm.render_tab(pd.DataFrame(), CONFIG)

    with base_tabs[3]:
        tab_config.render_tab(CONFIG)
