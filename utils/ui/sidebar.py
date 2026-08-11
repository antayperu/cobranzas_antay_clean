import os

import streamlit as st
from datetime import date

import utils.state_manager as _state_mgr
from utils.session import restore_session_by_id

# ── Ambiente detection ────────────────────────────────────────────────────────
_STAGING_URL = "hrnqngndnohkkegtzgjg.supabase.co"
_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
IS_STAGING = _STAGING_URL in _SUPABASE_URL


def _render_env_banner() -> None:
    """Muestra un banner visible cuando la app corre en staging."""
    if IS_STAGING:
        st.warning(
            "🧪 **AMBIENTE DE PRUEBAS (STAGING)**  \n"
            "Los datos aquí **no son reales** y no afectan producción.",
            icon=None,
        )


def _render_sidebar_header() -> None:
    today_label = date.today().strftime("%d %b %Y")
    st.markdown(
        f"""
        <div class="antay-sidebar-card antay-animate-in">
            <div class="antay-sidebar-card__top">
                <span class="antay-pill">Enterprise</span>
                <span class="antay-version">v2.2.0</span>
            </div>
            <h3>Cobranzas Antay</h3>
            <p>Operacion principal con 2 archivos y cartera maestra en Supabase.</p>
            <small>Actualizado: {today_label}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stepper(step: int) -> None:
    """Indicador de progreso: Paso 1/2 — Archivos  ›  Paso 2/2 — Generar."""
    done  = step > 1
    s1_cls = "sb-step sb-step--done"    if done  else "sb-step sb-step--active"
    s2_cls = "sb-step sb-step--active"  if step == 2 else "sb-step sb-step--pending"
    s1_dot = "✓" if done  else "●"
    s2_dot = "●" if step == 2 else "○"
    st.markdown(
        f"""
        <div class="sb-stepper antay-animate-in">
            <span class="{s1_cls}">{s1_dot} Archivos</span>
            <span class="sb-step-sep">›</span>
            <span class="{s2_cls}">{s2_dot} Generar</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Sidebar con progressive disclosure — máximo 4 elementos por estado."""
    with st.sidebar:
        _render_env_banner()
        _render_sidebar_header()
        st.markdown("---")

        # Inicializar flags de estado
        if "confirm_new_load" not in st.session_state:
            st.session_state["confirm_new_load"] = False
        if "uploaded_files" not in st.session_state:
            st.session_state["uploaded_files"] = {"ctas": None, "cobranza": None}

        data_ready  = st.session_state.get("data_ready", False)
        loading_new = st.session_state.get("loading_new_files", False)
        confirming  = st.session_state.get("confirm_new_load", False)

        # ──────────────────────────────────────────────────────────────────
        # ESTADO 3b — Confirmación de reemplazo (prioridad máxima)
        # ──────────────────────────────────────────────────────────────────
        if data_ready and confirming:
            cycle_label = st.session_state.get("cycle_id", "ciclo actual")
            st.markdown(
                f"""
                <div class="sb-confirm-card antay-animate-in">
                    <div class="sb-confirm-title">⚠️ Nuevo ciclo</div>
                    <div class="sb-confirm-body">
                        El ciclo <strong>{cycle_label}</strong> seguirá activo
                        en los tabs mientras cargas los nuevos archivos.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button("Sí, continuar", type="primary",
                         use_container_width=True, key="btn_confirm_yes"):
                st.session_state["uploaded_files"]   = {"ctas": None, "cobranza": None}
                st.session_state["confirm_new_load"] = False
                st.session_state["loading_new_files"] = True
                st.rerun()
            if st.button("Cancelar", type="secondary",
                         use_container_width=True, key="btn_confirm_no"):
                st.session_state["confirm_new_load"] = False
                st.rerun()
            return None

        # ──────────────────────────────────────────────────────────────────
        # ESTADO 2 — Carga de archivos (slots unificados con feedback visual)
        # ──────────────────────────────────────────────────────────────────
        if loading_new:
            files   = st.session_state["uploaded_files"]
            f_ctas  = files.get("ctas")
            f_cob   = files.get("cobranza")
            both_ok = f_ctas is not None and f_cob is not None

            _render_stepper(2 if both_ok else 1)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ── SLOT 1: CtasxCobrar ────────────────────────────────────
            if f_ctas is not None:
                _kb = round(f_ctas.size / 1024, 1) if hasattr(f_ctas, "size") else "?"
                _nm = f_ctas.name if hasattr(f_ctas, "name") else "CtasxCobrar.xlsx"
                st.markdown(
                    f"""
                    <div class="sb-file-card antay-animate-in">
                        <div class="sb-file-card__check">✅</div>
                        <div class="sb-file-card__info">
                            <div class="sb-file-card__name">{_nm}</div>
                            <div class="sb-file-card__meta">CxC &middot; {_kb} KB &middot; listo</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("✕  Cambiar CxC", type="secondary",
                             use_container_width=True, key="btn_clear_ctas"):
                    st.session_state["uploaded_files"]["ctas"] = None
                    st.rerun()
            else:
                uploaded_ctas = st.file_uploader(
                    "📂 CtasxCobrar (.xlsx)", type=["xlsx"], key="u_ctas",
                )
                if uploaded_ctas:
                    st.session_state["uploaded_files"]["ctas"] = uploaded_ctas
                    st.rerun()

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            # ── SLOT 2: Cobranza ──────────────────────────────────────
            if f_cob is not None:
                _kb = round(f_cob.size / 1024, 1) if hasattr(f_cob, "size") else "?"
                _nm = f_cob.name if hasattr(f_cob, "name") else "Cobranza.xlsx"
                st.markdown(
                    f"""
                    <div class="sb-file-card antay-animate-in">
                        <div class="sb-file-card__check">✅</div>
                        <div class="sb-file-card__info">
                            <div class="sb-file-card__name">{_nm}</div>
                            <div class="sb-file-card__meta">Cobranza &middot; {_kb} KB &middot; listo</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("✕  Cambiar Cobranza", type="secondary",
                             use_container_width=True, key="btn_clear_cob"):
                    st.session_state["uploaded_files"]["cobranza"] = None
                    st.rerun()
            else:
                uploaded_cob = st.file_uploader(
                    "📂 Cobranza (.xlsx)", type=["xlsx"], key="u_cob",
                )
                if uploaded_cob:
                    st.session_state["uploaded_files"]["cobranza"] = uploaded_cob
                    st.rerun()

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

            # ── Fecha de corte (visible solo cuando ambos archivos OK) ─
            if both_ok:
                fecha_corte = st.date_input(
                    "📅 Fecha de corte", value=date.today(), key="di_fecha_corte",
                )
                st.session_state["config_fecha_corte"] = fecha_corte
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            # ── Botón generar — siempre visible, disabled hasta both_ok ─
            if st.button(
                "🚀  Generar ciclo",
                type="primary",
                use_container_width=True,
                key="btn_procesar",
                disabled=not both_ok,
            ):
                return "PROCESS_TRIGGERED"

            if not both_ok:
                st.markdown(
                    """
                    <div class="sb-upload-hint">
                        Carga los 2 archivos para continuar.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ── Cancelar siempre disponible ────────────────────────────
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("✕  Cancelar", type="secondary",
                         use_container_width=True, key="btn_cancelar"):
                st.session_state["loading_new_files"] = False
                st.session_state["confirm_new_load"]  = False
                st.session_state["uploaded_files"]    = {"ctas": None, "cobranza": None}
                st.rerun()
            return None

        # ──────────────────────────────────────────────────────────────────
        # ESTADO 3 — Ciclo activo (estado por defecto al abrir la app)
        # ──────────────────────────────────────────────────────────────────
        if data_ready:
            cycle_id  = st.session_state.get("cycle_id", "—")
            ts        = st.session_state.get("session_start_ts")
            ts_str    = ts.strftime("%d/%m/%Y") if ts else date.today().strftime("%d/%m/%Y")
            df        = st.session_state.get("df_final")
            try:
                clientes = int(df["CodCliente"].nunique()) if df is not None and "CodCliente" in df.columns else (len(df) if df is not None else 0)
            except Exception:
                clientes = 0

            st.markdown(
                f"""
                <div class="sb-cycle-card antay-animate-in">
                    <div class="sb-cycle-label">☁️  Ciclo activo</div>
                    <div class="sb-cycle-id">{cycle_id}</div>
                    <div class="sb-cycle-meta">{ts_str} · {clientes} clientes</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            if st.button("☁️  Recuperar ciclo", type="secondary",
                         use_container_width=True, key="btn_recuperar",
                         help="Cargar un ciclo anterior desde la nube"):
                st.session_state["data_ready"]          = False
                st.session_state["df_final"]            = None
                st.session_state["restored_from_cloud"] = False
                st.session_state["loading_new_files"]   = False
                st.session_state["confirm_new_load"]    = False
                st.session_state["skip_auto_restore"]   = True
                st.rerun()

            if st.button("＋  Nuevo ciclo", type="primary",
                         use_container_width=True, key="btn_nuevo",
                         help="Cargar archivos de un período nuevo"):
                st.session_state["confirm_new_load"] = True
                st.rerun()
            return None

        # ──────────────────────────────────────────────────────────────────
        # ESTADO 1 — Sin ciclo activo (primer uso o tras "Recuperar ciclo")
        # ──────────────────────────────────────────────────────────────────
        sessions = _state_mgr.list_sessions_cloud(limit=10)

        if sessions:
            # Hay historial en la nube — mostrar selector de ciclos
            st.markdown(
                """
                <div class="sb-empty-state antay-animate-in">
                    Selecciona un ciclo para restaurar<br>
                    o inicia uno nuevo.
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            options_map: dict = {}
            seen_labels: dict = {}
            for s in sessions:
                ts = s.get("created_at")
                ts_str = ts.strftime("%d/%m/%Y %H:%M") if ts else "--"
                cid = s.get("cycle_id", "")
                if cid.startswith("CIC-"):
                    suffix = cid[-4:]
                else:
                    parts = cid.split("_")
                    suffix = parts[1][4:6] if len(parts) >= 2 and len(parts[1]) >= 6 else cid[-4:]
                base_label = f"{ts_str}  ·  {s.get('row_count', 0)} filas"
                label = base_label if base_label not in seen_labels else f"{base_label} [{suffix}]"
                seen_labels[base_label] = True
                options_map[label] = cid

            selected_label = st.selectbox(
                "Ciclo:", list(options_map.keys()), key="cycle_selector_box"
            )
            selected_cycle_id = options_map[selected_label]

            sel = next((s for s in sessions if s.get("cycle_id") == selected_cycle_id), None)
            if sel:
                st.caption(f"ID: {sel['cycle_id']}  ·  Corte: {sel.get('fecha_corte', '—')}")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("☁️  Recuperar ciclo", type="primary",
                         use_container_width=True, key="btn_restore_cloud"):
                restored = restore_session_by_id(selected_cycle_id)
                if restored:
                    st.toast(f"Ciclo {selected_cycle_id} restaurado ☁️")
                    st.rerun()
                else:
                    st.warning("No se pudo restaurar el ciclo seleccionado.")

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("＋  Nuevo ciclo", type="secondary",
                         use_container_width=True, key="btn_nuevo_empty"):
                st.session_state["loading_new_files"] = True
                st.session_state["uploaded_files"]    = {"ctas": None, "cobranza": None}
                st.rerun()

        else:
            # Sin historial — primer uso: ir directo a carga
            st.markdown(
                """
                <div class="sb-empty-state antay-animate-in">
                    Sin ciclos activos.<br>
                    Carga los archivos para comenzar.
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button("＋  Nuevo ciclo", type="primary",
                         use_container_width=True, key="btn_nuevo_empty"):
                st.session_state["loading_new_files"] = True
                st.session_state["uploaded_files"]    = {"ctas": None, "cobranza": None}
                st.rerun()

    return None
