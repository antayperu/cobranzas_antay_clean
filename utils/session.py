import streamlit as st
from datetime import date, datetime

import utils.state_manager as state_mgr


def enforce_cloud_only_policy() -> None:
    """Clear local cache artifacts; cloud is source of truth."""
    try:
        state_mgr.clear_session()
    except Exception:
        pass


def attempt_auto_restore() -> bool:
    """
    Try to restore the last processing session from Supabase.
    Returns True if session was restored successfully.
    """
    if st.session_state.get("data_ready", False):
        return False
    if st.session_state.get("loading_new_files", False):
        return False

    try:
        df, metadata, created_at = state_mgr.load_session_cloud()
        if df is None or df.empty:
            return False

        st.session_state["df_final"] = df
        st.session_state["data_ready"] = True
        st.session_state["fresh_load"] = False
        st.session_state["restored_from_cloud"] = True
        st.session_state["cycle_id"] = (metadata or {}).get("cycle_id", "restored")

        if created_at:
            st.session_state["session_start_ts"] = created_at
        else:
            st.session_state["session_start_ts"] = datetime.now()

        st.session_state["session_metadata"] = metadata or {}
        return True
    except Exception as e:
        print(f"Auto-restore error: {e}")
        return False


def get_cloud_session_info():
    """
    Lightweight check: returns (has_session, created_at, metadata) without loading DataFrame.
    """
    try:
        return state_mgr.has_valid_session_cloud()
    except Exception:
        return False, None, None


def render_recovery_options() -> None:
    """
    Show recovery banner in sidebar if a cloud session exists.
    User can choose to continue or start fresh.
    """
    if st.session_state.get("data_ready", False):
        return
    if st.session_state.get("loading_new_files", False):
        return

    has_session, created_at, metadata = get_cloud_session_info()
    if not has_session:
        return

    row_count = (metadata or {}).get("row_count", 0)
    ts_str = "--"
    if created_at:
        try:
            ts_str = created_at.strftime("%d/%m/%Y %H:%M")
        except Exception:
            ts_str = str(created_at)[:16]

    st.markdown(
        f"""
        <div class="antay-inline-note antay-animate-in">
            <strong>Sesion anterior encontrada</strong><br>
            <span style="font-size:0.82rem;">{ts_str} &mdash; {row_count} registros</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_restore, col_new = st.columns(2)
    with col_restore:
        if st.button("Continuar sesion", type="primary", key="btn_restore_cloud"):
            restored = attempt_auto_restore()
            if restored:
                st.toast("Sesion restaurada desde la nube", icon="☁️")
                st.rerun()
            else:
                st.warning("No se pudo restaurar la sesion.")
    with col_new:
        if st.button("Nuevo ciclo", type="secondary", key="btn_new_cycle"):
            st.session_state["loading_new_files"] = True
            st.rerun()


def init_session_state() -> None:
    """Initializes required in-memory session keys."""
    if "data_ready" not in st.session_state:
        st.session_state["data_ready"] = False

    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = {
            "ctas": None,
            "cobranza": None,
        }

    if "config_fecha_corte" not in st.session_state:
        st.session_state["config_fecha_corte"] = date.today()

    if "tracking_dirty" not in st.session_state:
        st.session_state["tracking_dirty"] = False

    if "fresh_load" not in st.session_state:
        st.session_state["fresh_load"] = False

    if "loading_new_files" not in st.session_state:
        st.session_state["loading_new_files"] = False

    if "restored_from_cloud" not in st.session_state:
        st.session_state["restored_from_cloud"] = False
