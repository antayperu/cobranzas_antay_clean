import io
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

import utils.db_manager as dbm
import utils.ui.styles as styles

# ---------------------------------------------------------------------------
# Constants & mappings
# ---------------------------------------------------------------------------

REQUIRED_GRID_COLUMNS = [
    "codigo_cliente",
    "nombre_cliente",
    "correo",
    "telefono",
    "dni",
    "ruc",
    "Enviar Email",
    "estado_cliente",
    "nota",
]

GRID_TO_DB = {
    "codigo_cliente": "cliente_id",
    "nombre_cliente": "nombre",
    "nota": "notas",
    "Enviar Email": "enviar_email",
    "dni": "dni",
    "ruc": "ruc",
    "correo": "email",
    "telefono": "telefono",
    "estado_cliente": "estado",
}

ESTADOS_VALIDOS = ["ACTIVO", "INACTIVO", "MOROSO"]
ENVIAR_EMAIL_VALIDOS = ["SI", "NO", "SIN CONFIGURAR"]


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _normalize_estado(value: Any) -> str:
    raw = str(value or "").strip().upper()
    alias = {"A": "ACTIVO", "AC": "ACTIVO", "I": "INACTIVO", "IN": "INACTIVO", "M": "MOROSO", "MO": "MOROSO"}
    raw = alias.get(raw, raw)
    return raw if raw in ESTADOS_VALIDOS else "ACTIVO"


def _normalize_enviar_email(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if raw in {"SI", "SÍ", "YES", "Y", "1", "TRUE", "ENVIAR"}:
        return "SI"
    if raw in {"NO", "N", "0", "FALSE", "NO ENVIAR"}:
        return "NO"
    if raw in {"", "NAN", "NONE", "NAT", "NULL", "SIN CONFIGURAR", "SINCONFIGURAR"}:
        return "SIN CONFIGURAR"
    return raw if raw in ENVIAR_EMAIL_VALIDOS else "SIN CONFIGURAR"


def _extract_optional_columns(raw_df: pd.DataFrame) -> List[str]:
    optional: set = set()
    known_db_cols = set(GRID_TO_DB.values()) | {"id", "created_at", "updated_at", "extra_fields"}
    for col in raw_df.columns:
        if col not in known_db_cols:
            optional.add(str(col))
    if "extra_fields" in raw_df.columns:
        for item in raw_df["extra_fields"].tolist():
            if isinstance(item, dict):
                for key in item.keys():
                    if str(key).strip():
                        optional.add(str(key))
    return sorted(optional)


def _build_editor_df(raw_df: pd.DataFrame, selected_optional: List[str]) -> pd.DataFrame:
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=REQUIRED_GRID_COLUMNS + selected_optional)

    records: List[Dict[str, Any]] = []
    for _, row in raw_df.iterrows():
        record: Dict[str, Any] = {}
        for grid_col, db_col in GRID_TO_DB.items():
            val = row.get(db_col)
            if pd.isna(val):
                val = ""
            record[grid_col] = str(val).strip() if val is not None else ""

        record["estado_cliente"] = _normalize_estado(record.get("estado_cliente"))
        record["Enviar Email"] = _normalize_enviar_email(record.get("Enviar Email"))

        extra_fields = row.get("extra_fields")
        if not isinstance(extra_fields, dict):
            extra_fields = {}
        for col in selected_optional:
            val = row.get(col)
            if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() == "":
                val = extra_fields.get(col, "")
            record[col] = str(val).strip() if val is not None else ""
        records.append(record)

    return pd.DataFrame(records, columns=REQUIRED_GRID_COLUMNS + selected_optional)


def _rows_from_editor(df: pd.DataFrame, selected_optional: List[str]) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    rows: List[Dict[str, Any]] = []
    for row in df.to_dict("records"):
        cliente_id = str(row.get("codigo_cliente", "")).strip()
        nombre = str(row.get("nombre_cliente", "")).strip()
        if not cliente_id and not nombre:
            continue
        extras: Dict[str, Any] = {}
        for col in selected_optional:
            value = str(row.get(col, "")).strip()
            if value:
                extras[col] = value
        rows.append({
            "cliente_id": cliente_id,
            "nombre": nombre,
            "notas": str(row.get("nota", "")).strip(),
            "enviar_email": _normalize_enviar_email(row.get("Enviar Email")),
            "dni": str(row.get("dni", "")).strip(),
            "ruc": str(row.get("ruc", "")).strip(),
            "email": str(row.get("correo", "")).strip(),
            "telefono": str(row.get("telefono", "")).strip(),
            "estado": _normalize_estado(row.get("estado_cliente")),
            "extra_fields": extras,
        })
    return rows


# ---------------------------------------------------------------------------
# Main tab render
# ---------------------------------------------------------------------------

def render_tab(df_final, config):  # noqa: ARG001
    # ── Header ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:2px;">
            <h2 style="margin:0; font-weight:780; color:#0D3B66;">Clientes Premium</h2>
            <span class="antay-pill" style="background:rgba(13,59,102,0.1); color:#0d3b66; border-color:#adc2dc;">
                Cartera Maestra
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── KPI metrics ─────────────────────────────────────────────────────
    all_rows = dbm.list_clientes_full(limit=5000)
    _render_kpis(all_rows)

    st.markdown("---")

    # ── Barra de filtros + acciones en una sola fila ─────────────────────
    fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([3, 1, 1, 1, 1, 1])
    search = fc1.text_input(
        "Buscar cliente",
        placeholder="Codigo, nombre, correo, telefono, DNI, RUC...",
        key="cp_search",
    )
    estado_filter = fc2.selectbox("Estado", ["TODOS"] + ESTADOS_VALIDOS, key="cp_estado")
    email_filter = fc3.selectbox("Enviar Email", ["TODOS"] + ENVIAR_EMAIL_VALIDOS, key="cp_email_filter")

    # Botones alineados verticalmente con los inputs (spacer = altura del label)
    with fc4:
        st.write("")
        if st.button("➕ Agregar", key="cp_btn_add", use_container_width=True):
            st.session_state["cp_panel"] = "add"
            st.rerun()
    with fc5:
        st.write("")
        if st.button("📥 Importar", key="cp_btn_import", use_container_width=True):
            st.session_state["cp_panel"] = "import"
            st.rerun()
    with fc6:
        st.write("")
        if st.button("🗑️ Eliminar", key="cp_btn_delete", use_container_width=True):
            st.session_state["cp_panel"] = "delete"
            st.rerun()

    # ── Fetch & filter data ─────────────────────────────────────────────
    rows = dbm.list_clientes_full(
        search=search,
        estado=estado_filter if estado_filter != "TODOS" else "",
        limit=5000,
    )
    if email_filter != "TODOS" and rows:
        rows = [r for r in rows if _normalize_enviar_email(r.get("enviar_email")) == email_filter]

    if not rows:
        st.info(
            "No se encontraron clientes para los filtros actuales. "
            "Usa 'Importar' o 'Agregar' para poblar la cartera."
        )

    raw_df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=list(GRID_TO_DB.values()) + ["extra_fields"])
    optional_cols = _extract_optional_columns(raw_df) if rows else []
    selected_optional: List[str] = []
    if optional_cols:
        with st.expander("Columnas adicionales", expanded=False):
            selected_optional = st.multiselect(
                "Columnas extra", options=optional_cols, default=[], key="cp_optional_cols",
            )

    editor_df = _build_editor_df(raw_df, selected_optional)

    # ── Determine panel state ───────────────────────────────────────────
    panel = st.session_state.get("cp_panel", None)

    # ── Show action panels if active ────────────────────────────────────
    if panel == "add":
        _render_add_client_form()
    elif panel == "import":
        _render_import_wizard()
    elif panel == "delete":
        # Deletion mode: show selectable dataframe
        if editor_df.empty:
            st.info("No hay clientes para eliminar. Importa o agrega clientes primero.")
            if st.button("Cerrar", key="cp_delete_close_empty"):
                st.session_state["cp_panel"] = None
                st.rerun()
            return
        _render_delete_view(editor_df)
        return  # Don't show the editor while in delete mode

    # ── Toolbar secundaria: Export + contador ───────────────────────────
    _tb1, _tb2 = st.columns([1, 4])
    with _tb1:
        _render_export(editor_df)
    with _tb2:
        st.caption(f"{len(editor_df)} clientes")

    # ── Data grid (editable, no extra checkbox column) ──────────────────
    column_config: Dict[str, Any] = {
        "codigo_cliente": st.column_config.TextColumn("Codigo", width="small", required=True),
        "nombre_cliente": st.column_config.TextColumn("Nombre", width="large", required=True),
        "correo": st.column_config.TextColumn("Correo", width="medium"),
        "telefono": st.column_config.TextColumn("Telefono", width="small"),
        "dni": st.column_config.TextColumn("DNI", width="small"),
        "ruc": st.column_config.TextColumn("RUC", width="small"),
        "Enviar Email": st.column_config.SelectboxColumn("Enviar Email", options=ENVIAR_EMAIL_VALIDOS, width="small"),
        "estado_cliente": st.column_config.SelectboxColumn("Estado", options=ESTADOS_VALIDOS, width="small"),
        "nota": st.column_config.TextColumn("Nota", width="medium"),
    }
    for col in selected_optional:
        column_config[col] = st.column_config.TextColumn(col, width="medium")

    edited = st.data_editor(
        editor_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="cp_editor_data",
        column_config=column_config,
        height=560,
    )

    # ── Save button ─────────────────────────────────────────────────────
    if st.button("💾 Guardar cambios", type="primary", key="cp_save_btn"):
        records = _rows_from_editor(edited, selected_optional)
        if not records:
            st.warning("No hay registros para guardar. Importa o agrega clientes primero.")
            return
        ok, msg = dbm.upsert_clientes_rows(records)
        if ok:
            st.success(msg)
        else:
            st.error(msg)
        st.rerun()


# ---------------------------------------------------------------------------
# Sub-components
# ---------------------------------------------------------------------------

def _render_kpis(rows: list):
    if not rows:
        return
    total = len(rows)
    activos = sum(1 for r in rows if r.get("estado", "").upper() == "ACTIVO")
    inactivos = sum(1 for r in rows if r.get("estado", "").upper() == "INACTIVO")
    morosos = sum(1 for r in rows if r.get("estado", "").upper() == "MOROSO")
    con_email = sum(1 for r in rows if r.get("email"))

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(styles.kpi_card_html("Total Clientes", f"{total:,}"), unsafe_allow_html=True)
    k2.markdown(styles.kpi_card_html("Activos", f"{activos:,}", status="success"), unsafe_allow_html=True)
    k3.markdown(styles.kpi_card_html("Inactivos", f"{inactivos:,}"), unsafe_allow_html=True)
    k4.markdown(styles.kpi_card_html("Morosos", f"{morosos:,}", status="danger"), unsafe_allow_html=True)
    k5.markdown(styles.kpi_card_html("Con Email", f"{con_email:,}", status="neutral"), unsafe_allow_html=True)


def _render_delete_view(editor_df: pd.DataFrame):
    """Show a selectable dataframe for deletion — native Streamlit row selection."""
    st.markdown(
        '<div class="antay-inline-note">'
        '<strong>Modo eliminacion</strong> &mdash; Selecciona filas en la grilla y confirma.'
        '</div>',
        unsafe_allow_html=True,
    )

    event = st.dataframe(
        editor_df,
        use_container_width=True,
        hide_index=True,
        height=480,
        on_select="rerun",
        selection_mode="multi-row",
        key="cp_delete_grid",
    )

    selected_indices = event.selection.rows if event and event.selection else []

    dc1, dc2, dc3 = st.columns([2, 1, 2])
    with dc1:
        if selected_indices:
            st.warning(f"{len(selected_indices)} cliente(s) seleccionado(s) para eliminar.")
            if st.button("Confirmar eliminacion", type="primary", key="cp_delete_confirm"):
                selected_rows = editor_df.iloc[selected_indices]
                ids = [str(r).strip() for r in selected_rows["codigo_cliente"].tolist() if str(r).strip()]
                if ids:
                    ok, msg = dbm.delete_clientes_by_ids(ids)
                    if ok:
                        st.success(msg)
                        st.session_state["cp_panel"] = None
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("Selecciona filas haciendo click en ellas.")
    with dc2:
        if st.button("Cancelar", key="cp_delete_cancel"):
            st.session_state["cp_panel"] = None
            st.rerun()


def _render_import_wizard():
    st.markdown(
        '<div class="antay-inline-note"><strong>Importar cartera desde Excel</strong></div>',
        unsafe_allow_html=True,
    )
    ic1, ic2 = st.columns([3, 1])
    with ic1:
        cartera_file = st.file_uploader("Archivo .xlsx", type=["xlsx"], key="cp_import_file", label_visibility="collapsed")
    with ic2:
        if st.button("Cerrar", key="cp_import_close"):
            st.session_state["cp_panel"] = None
            st.rerun()

    if cartera_file is not None:
        file_bytes = cartera_file.getvalue()
        try:
            df_preview = pd.read_excel(io.BytesIO(file_bytes))
            st.caption(f"{len(df_preview)} filas | {len(df_preview.columns)} columnas")
            st.dataframe(df_preview.head(10), use_container_width=True, height=200)
        except Exception as e:
            st.error(f"No se pudo leer: {e}")
            df_preview = None

        if st.button("Migrar a Supabase", type="primary", disabled=df_preview is None, key="cp_migrate_btn"):
            try:
                df_cartera = pd.read_excel(io.BytesIO(file_bytes))
                result = dbm.migrate_clientes_from_cartera_df(df_cartera)
                if result.get("ok"):
                    st.success(result.get("message", "Migracion completada."))
                    st.session_state["cp_panel"] = None
                else:
                    st.error(result.get("message", "Migracion fallida."))
                counts = result.get("counts", {})
                st.caption(f"Preparados: {counts.get('rows', 0)} | Errores: {counts.get('errors', 0)}")
            except Exception as e:
                st.error(f"Error: {e}")


def _render_add_client_form():
    st.markdown(
        '<div class="antay-inline-note"><strong>Agregar nuevo cliente</strong></div>',
        unsafe_allow_html=True,
    )
    ac1, ac2, ac3, ac4 = st.columns(4)
    new_codigo = ac1.text_input("Codigo", key="cp_new_codigo")
    new_nombre = ac2.text_input("Nombre", key="cp_new_nombre")
    new_correo = ac3.text_input("Correo", key="cp_new_correo")
    new_telefono = ac4.text_input("Telefono", key="cp_new_telefono")

    ac5, ac6, ac7, ac8 = st.columns(4)
    new_dni = ac5.text_input("DNI", key="cp_new_dni")
    new_ruc = ac6.text_input("RUC", key="cp_new_ruc")
    new_estado = ac7.selectbox("Estado", ESTADOS_VALIDOS, key="cp_new_estado")
    new_enviar = ac8.selectbox("Enviar Email", ENVIAR_EMAIL_VALIDOS, key="cp_new_enviar")

    bc1, bc2 = st.columns([1, 3])
    with bc1:
        if st.button("Agregar", type="primary", key="cp_add_btn"):
            if not new_codigo or not new_nombre:
                st.warning("Codigo y nombre son obligatorios.")
            else:
                ok, msg = dbm.upsert_clientes_rows([{
                    "cliente_id": new_codigo.strip(),
                    "nombre": new_nombre.strip(),
                    "email": new_correo.strip(),
                    "telefono": new_telefono.strip(),
                    "dni": new_dni.strip(),
                    "ruc": new_ruc.strip(),
                    "estado": new_estado,
                    "enviar_email": new_enviar,
                    "notas": "",
                    "extra_fields": {},
                }])
                if ok:
                    st.success(f"Cliente {new_codigo} agregado.")
                    st.session_state["cp_panel"] = None
                    st.rerun()
                else:
                    st.error(msg)
    with bc2:
        if st.button("Cerrar", key="cp_add_close"):
            st.session_state["cp_panel"] = None
            st.rerun()


def _render_export(df: pd.DataFrame):
    if df is not None and not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📤 Exportar",
            data=csv,
            file_name="cartera_clientes.csv",
            mime="text/csv",
            key="cp_export_csv",
        )
