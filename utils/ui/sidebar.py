import streamlit as st
from datetime import date

import utils.state_manager as state_mgr


def _render_sidebar_header() -> None:
    today_label = date.today().strftime("%d %b %Y")
    st.markdown(
        f"""
        <div class="antay-sidebar-card antay-animate-in">
            <div class="antay-sidebar-card__top">
                <span class="antay-pill">Enterprise</span>
                <span class="antay-version">v1.7.0</span>
            </div>
            <h3>Cobranzas Antay</h3>
            <p>Operacion principal con 2 archivos y cartera maestra en Supabase.</p>
            <small>Actualizado: {today_label}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render sidebar with 2-file workflow and explicit replace confirmation."""
    with st.sidebar:
        _render_sidebar_header()
        st.markdown("---")

        if "confirm_new_load" not in st.session_state:
            st.session_state["confirm_new_load"] = False

        if st.session_state.get("data_ready", False):
            ts = st.session_state.get("session_start_ts")
            ts_str = ts.strftime("%d/%m %H:%M") if ts else "--:--"
            row_count = len(st.session_state.get("df_final", []))
            cloud_label = " ☁️" if st.session_state.get("restored_from_cloud", False) else ""
            st.success(f"Sesion activa: {ts_str} ({row_count} filas){cloud_label}")

            if not st.session_state["confirm_new_load"]:
                if st.button(
                    "Cargar nuevos archivos",
                    type="secondary",
                    help="Reemplazar datos actuales con nuevos archivos",
                ):
                    st.session_state["confirm_new_load"] = True
                    st.rerun()
            else:
                st.warning(
                    """
                    Confirmacion requerida:
                    cargar nuevos archivos reemplazara el reporte actual y reiniciara el ciclo.
                    """
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Si, reemplazar", type="primary"):
                        st.session_state["uploaded_files"] = {"ctas": None, "cobranza": None}
                        st.session_state["data_ready"] = False
                        st.session_state["df_final"] = None
                        st.session_state["fresh_load"] = True
                        st.session_state["confirm_new_load"] = False
                        state_mgr.clear_session()
                        st.session_state["loading_new_files"] = True
                        st.toast("Sesion limpiada. Lista para nuevo ciclo.")
                        st.rerun()

                with col_no:
                    if st.button("Cancelar", type="secondary"):
                        st.session_state["confirm_new_load"] = False
                        st.rerun()

            st.markdown("---")

        show_uploaders = not st.session_state.get("data_ready", False)
        if show_uploaders:
            step_1_done = False
            with st.expander("1. Carga base (2 archivos)", expanded=True):
                st.markdown(
                    """
                    <div class="antay-inline-note antay-animate-in">
                        Flujo oficial: carga <strong>CtasxCobrar</strong> y <strong>Cobranza</strong>.
                        La cartera de clientes se administra en <strong>6. Clientes Premium</strong>.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Si no existe cartera maestra en Supabase, migra clientes primero desde la TAB Clientes Premium."
                )

                if "uploaded_files" not in st.session_state:
                    st.session_state["uploaded_files"] = {"ctas": None, "cobranza": None}

                f_ctas = st.file_uploader("CtasxCobrar (.xlsx)", type=["xlsx"], key="u_ctas")
                if f_ctas:
                    st.session_state["uploaded_files"]["ctas"] = f_ctas

                f_cob = st.file_uploader("Cobranza (.xlsx)", type=["xlsx"], key="u_cob")
                if f_cob:
                    st.session_state["uploaded_files"]["cobranza"] = f_cob

                files_ok = (
                    st.session_state["uploaded_files"]["ctas"] is not None
                    and st.session_state["uploaded_files"]["cobranza"] is not None
                )
                if files_ok:
                    st.success("Archivos operativos listos")
                    step_1_done = True

            if step_1_done:
                with st.expander("2. Parametros de ciclo", expanded=True):
                    fecha_corte = st.date_input("Fecha de corte", value=date.today())
                    st.session_state["config_fecha_corte"] = fecha_corte

                    if not st.session_state.get("data_ready", False):
                        if st.button("Procesar y validar", type="primary"):
                            return "PROCESS_TRIGGERED"

        if st.session_state.get("data_ready", False):
            st.markdown(
                """
                <div class="antay-inline-note">
                    Ciclo activo. Para editar clientes, usa la TAB <strong>Clientes Premium</strong>.
                </div>
                """,
                unsafe_allow_html=True,
            )

    return None
