import streamlit as st
from datetime import datetime, date

def render_sidebar():
    """Renders the Enterprise Sidebar with Wizard Flow and No Sorpresas confirmation."""
    with st.sidebar:
        # --- 1. HEADER (Brand) ---
        st.markdown("### 🏢 Cobranzas Antay")
        st.caption(f"v1.5.0 Enterprise | {date.today().strftime('%d %b %Y')}")
        st.markdown("---")

        # --- 2. SESIÓN (Persistence) ---
        # Initialize confirmation states
        if 'confirm_new_load' not in st.session_state:
            st.session_state['confirm_new_load'] = False
        
        # Mostrar solo si hay datos listos (Resume Mode)
        if st.session_state.get('data_ready', False):
            ts = st.session_state.get('session_start_ts', None)
            ts_str = ts.strftime('%H:%M') if ts else "--:--"
            st.success(f"⚡ Sesión Activa desde {ts_str}")
            
            # --- NO SORPRESAS: Confirmation for New Load ---
            if not st.session_state['confirm_new_load']:
                # Step 1: Show "Cargar Nuevos Archivos" button
                if st.button("📂 Cargar Nuevos Archivos", type="secondary", help="Reemplazar datos actuales con nuevos archivos"):
                    st.session_state['confirm_new_load'] = True
                    st.rerun()
            else:
                # Step 2: Show confirmation dialog
                st.warning("""
                ⚠️ **Confirmación Requerida**
                
                Cargar nuevos archivos **reemplazará el reporte actual** y reiniciará el ciclo.
                
                Se perderá el estado de la sesión actual (enviados/pendientes).
                
                ¿Deseas continuar?
                """)
                
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Sí, reemplazar", type="primary"):
                        # Clear SSOT and all tracking
                        st.session_state['uploaded_files'] = {'ctas': None, 'cobranza': None, 'cartera': None}
                        st.session_state['data_ready'] = False
                        st.session_state['df_final'] = None
                        st.session_state['fresh_load'] = True
                        st.session_state['confirm_new_load'] = False
                        # FIX: Flag persistente para indicar que estamos cargando archivos nuevos
                        # Este flag NO se limpia hasta que los archivos se carguen exitosamente
                        st.session_state['loading_new_files'] = True
                        st.toast("🔄 Sesión limpiada. Listo para nuevos archivos.", icon="✅")
                        st.rerun()
                
                with col_no:
                    if st.button("❌ Cancelar", type="secondary"):
                        st.session_state['confirm_new_load'] = False
                        st.rerun()
            
            st.markdown("---")

        # --- 3. WIZARD: CARGA DE DATOS ---
        # Only show uploaders if NO data exists OR user confirmed replacement
        show_uploaders = not st.session_state.get('data_ready', False)
        
        if show_uploaders:
            step_1_done = False
            
            # Step 1: Upload
            with st.expander("📂 1. Carga de Archivos", expanded=True):
                st.info("Sube los 3 reportes base para iniciar.")
                
                # Init Files
                if 'uploaded_files' not in st.session_state:
                    st.session_state['uploaded_files'] = {'ctas': None, 'cobranza': None, 'cartera': None}

                f_ctas = st.file_uploader("CtasxCobrar", type=["xlsx"], key="u_ctas")
                if f_ctas: st.session_state['uploaded_files']['ctas'] = f_ctas
                
                f_cob = st.file_uploader("Cobranza", type=["xlsx"], key="u_cob")
                if f_cob: st.session_state['uploaded_files']['cobranza'] = f_cob

                f_cart = st.file_uploader("Cartera", type=["xlsx"], key="u_cart")
                if f_cart: st.session_state['uploaded_files']['cartera'] = f_cart
                
                # Check Status
                files_ok = all(st.session_state['uploaded_files'].values())
                if files_ok:
                    st.success("✅ Archivos listos")
                    step_1_done = True
            
            # Step 2: Parametros (Solo si step 1 ok)
            if step_1_done:
                with st.expander("⚙️ 2. Parámetros", expanded=True):
                    fecha_corte = st.date_input("Fecha de Corte", value=date.today())
                    st.session_state['config_fecha_corte'] = fecha_corte
                    
                    # Validation Action
                    if not st.session_state.get('data_ready', False):
                        if st.button("🚀 Procesar y Validar", type="primary"):
                            return "PROCESS_TRIGGERED" # Signal to App to run processing
        
        # Step 3: Navigation (Result)
        if st.session_state.get('data_ready', False):
            pass # App.py handles main tabs
            
    return None

