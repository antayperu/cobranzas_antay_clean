import streamlit as st
import utils.state_manager as state_mgr
import json
from datetime import datetime, date

def restore_session_state(df, meta, ts):
    """Updates session state with loaded data."""
    st.session_state['df_final'] = df
    st.session_state['data_ready'] = True
    st.session_state['session_start_ts'] = ts
    st.session_state['fresh_load'] = False
    
    # Robust metadata handling
    meta_dict = {}
    if isinstance(meta, dict):
        meta_dict = meta
    elif isinstance(meta, str):
        try:
            meta_dict = json.loads(meta)
        except:
             # If not JSON, assume it's just a string message and ignore for dict props
             pass
             
    st.session_state['uploaded_files'] = meta_dict.get('uploaded_files', {
        'ctas': None, 'cobranza': None, 'cartera': None
    })

def attempt_auto_restore():
    """
    Attempts to silent auto-restore session if conditions are met.
    Returns True if restored, False otherwise.
    """
    # Logic from app.py
    if (not st.session_state.get('data_ready', False) and 
        not st.session_state.get('loading_new_files', False) and
        not st.session_state.get('tracking_dirty', False)):
        
        has_session, cache_time, _ = state_mgr.has_valid_session()
        if has_session:
            try:
                df, meta, ts = state_mgr.load_session()
                if df is not None and not df.empty:
                    restore_session_state(df, meta, ts)
                    return True
            except Exception as e:
                # Silent fail
                pass
    return False

def render_recovery_options():
    """Renders manual recovery options in the sidebar."""
    # Only show if no data loaded
    if st.session_state.get('data_ready', False):
        return

    has_session, cache_time, _ = state_mgr.has_valid_session()
    if has_session:
        st.info(f"📂 Sesión previa encontrada ({cache_time.strftime('%d/%m %H:%M')})")
        if st.button("🔄 Continuar Trabajo Anterior", use_container_width=True, key="btn_restore_session"):
            with st.spinner("Recuperando sesión..."):
                try:
                    df, meta, ts = state_mgr.load_session()
                    if df is not None and not df.empty:
                        restore_session_state(df, meta, ts)
                        st.success("✅ Sesión recuperada exitosamente")
                        st.rerun()
                    else:
                        st.error("❌ No se pudo recuperar la sesión (Archivo vacío o corrupto)")
                except Exception as e:
                    st.error(f"❌ Error al recuperar: {e}")
        st.markdown("---")

def init_session_state():
    """Initializes all required session state variables with default values."""
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False

    if 'uploaded_files' not in st.session_state:
        st.session_state['uploaded_files'] = {
            'ctas': None,
            'cobranza': None,
            'cartera': None
        }

    # Enterprise UI features
    if 'config_fecha_corte' not in st.session_state:
        # Default to today
        st.session_state['config_fecha_corte'] = date.today()

    # Tracking system needed for UI updates
    if 'tracking_dirty' not in st.session_state:
        st.session_state['tracking_dirty'] = False
        
    if 'fresh_load' not in st.session_state:
        st.session_state['fresh_load'] = False
        
    if 'loading_new_files' not in st.session_state:
        st.session_state['loading_new_files'] = False

