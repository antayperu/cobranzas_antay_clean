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
    # El usuario pidió explícitamente el selector de ciclos: no auto-restaurar.
    if st.session_state.get("skip_auto_restore", False):
        return False

    try:
        df, metadata, created_at = state_mgr.load_session_cloud()
        if df is None or df.empty:
            return False

        cycle_id = (metadata or {}).get("cycle_id", "restored")

        import utils.db_manager as dbm
        df = dbm.reconcile_tracking_from_notifications(df, cycle_id)

        st.session_state["df_final"] = df
        st.session_state["data_ready"] = True
        st.session_state["fresh_load"] = False
        st.session_state["restored_from_cloud"] = True
        st.session_state["cycle_id"] = cycle_id

        if created_at:
            st.session_state["session_start_ts"] = created_at
        else:
            st.session_state["session_start_ts"] = datetime.now()

        st.session_state["session_metadata"] = metadata or {}
        return True
    except Exception as e:
        print(f"Auto-restore error: {e}")
        return False


def restore_session_by_id(cycle_id: str) -> bool:
    """
    Restore a specific cycle by ID and reconcile notification tracking.
    Returns True if session was restored successfully.
    """
    try:
        df, metadata, created_at = state_mgr.load_session_by_id(cycle_id)
        if df is None or df.empty:
            return False

        import utils.db_manager as dbm
        df = dbm.reconcile_tracking_from_notifications(df, cycle_id)

        st.session_state["df_final"] = df
        st.session_state["data_ready"] = True
        st.session_state["fresh_load"] = False
        st.session_state["restored_from_cloud"] = True
        st.session_state["cycle_id"] = cycle_id
        # El usuario seleccionó un ciclo manualmente: el auto-restore puede operar con normalidad.
        st.session_state["skip_auto_restore"] = False

        if created_at:
            st.session_state["session_start_ts"] = created_at
        else:
            st.session_state["session_start_ts"] = datetime.now()

        st.session_state["session_metadata"] = metadata or {}
        return True
    except Exception as e:
        print(f"restore_session_by_id error: {e}")
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
    Show cycle selector in sidebar if cloud sessions exist.
    User can choose which cycle to restore or start a new one.
    """
    if st.session_state.get("data_ready", False):
        return
    if st.session_state.get("loading_new_files", False):
        return

    sessions = state_mgr.list_sessions_cloud(limit=10)
    if not sessions:
        # No cloud history → go directly to upload mode
        st.session_state["loading_new_files"] = True
        return

    st.markdown(
        """
        <div class="antay-inline-note antay-animate-in">
            <strong>Ciclos disponibles en la nube</strong><br>
            <span style="font-size:0.82rem;">Selecciona un ciclo para restaurar o inicia uno nuevo.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    options_map = {}
    seen_labels: dict = {}
    for s in sessions:
        ts = s["created_at"]
        ts_str = ts.strftime("%d/%m/%Y %H:%M") if ts else "--"
        # Compact label: date+time + rows. Add seconds to disambiguate same-minute cycles.
        cid = s["cycle_id"]
        if cid.startswith("CIC-"):
            suffix = cid[-4:]  # HHMM
        else:
            parts = cid.split("_")
            suffix = parts[1][4:6] if len(parts) >= 2 and len(parts[1]) >= 6 else cid[-4:]  # SS
        base_label = f"{ts_str}  ·  {s['row_count']} filas"
        label = base_label if base_label not in seen_labels else f"{base_label} [{suffix}]"
        seen_labels[base_label] = True
        options_map[label] = s["cycle_id"]

    selected_label = st.selectbox(
        "Ciclo:",
        list(options_map.keys()),
        key="cycle_selector_box",
    )
    selected_cycle_id = options_map[selected_label]

    sel = next((s for s in sessions if s["cycle_id"] == selected_cycle_id), None)
    if sel:
        st.caption(
            f"ID: {sel['cycle_id']}  |  {sel['file_ctas']}  |  Corte: {sel['fecha_corte']}"
        )

    col_restore, col_new = st.columns(2)
    with col_restore:
        if st.button("Recuperar", type="primary", key="btn_restore_cloud"):
            restored = restore_session_by_id(selected_cycle_id)
            if restored:
                st.toast(f"Ciclo {selected_cycle_id} restaurado ☁️")
                st.rerun()
            else:
                st.warning("No se pudo restaurar el ciclo.")
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

    if "skip_auto_restore" not in st.session_state:
        st.session_state["skip_auto_restore"] = False
