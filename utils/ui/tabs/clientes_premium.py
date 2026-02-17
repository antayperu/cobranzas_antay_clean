import io
from typing import Dict, List

import pandas as pd
import streamlit as st

import utils.db_manager as dbm


CLIENT_COLUMNS = [
    "cliente_id",
    "nombre",
    "email",
    "telefono",
    "ruc",
    "direccion",
    "estado",
    "notas",
]
ESTADOS_VALIDOS = ["ACTIVO", "INACTIVO", "MOROSO"]


def _normalize_editor_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=CLIENT_COLUMNS)

    out = df.copy()
    for col in CLIENT_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[CLIENT_COLUMNS].copy()

    for col in CLIENT_COLUMNS:
        if col in {"notas", "direccion"}:
            out[col] = out[col].fillna("")
        else:
            out[col] = out[col].astype(str).replace({"nan": "", "None": ""}).str.strip()

    out["estado"] = out["estado"].str.upper().replace({"A": "ACTIVO", "I": "INACTIVO", "M": "MOROSO"})
    out["estado"] = out["estado"].where(out["estado"].isin(ESTADOS_VALIDOS), "ACTIVO")
    return out


def _rows_from_editor(df: pd.DataFrame) -> List[Dict[str, str]]:
    if df is None or df.empty:
        return []
    records: List[Dict[str, str]] = []
    for row in df.to_dict("records"):
        cliente_id = str(row.get("cliente_id", "")).strip()
        nombre = str(row.get("nombre", "")).strip()
        if not cliente_id and not nombre:
            continue
        records.append(
            {
                "cliente_id": cliente_id,
                "nombre": nombre,
                "email": str(row.get("email", "")).strip(),
                "telefono": str(row.get("telefono", "")).strip(),
                "ruc": str(row.get("ruc", "")).strip(),
                "direccion": str(row.get("direccion", "")).strip(),
                "estado": str(row.get("estado", "")).strip().upper(),
                "notas": str(row.get("notas", "")).strip(),
            }
        )
    return records


def render_tab(df_final, config):  # noqa: ARG001
    st.subheader("Clientes Premium")
    st.caption(
        "Gestion integral de cartera maestra en Supabase: editar cualquier cliente/campo, "
        "insertar nuevos registros y migrar cartera desde Excel."
    )

    st.markdown("### 1) Editor Maestro de Clientes")
    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("Buscar por codigo, nombre, correo, telefono o RUC", value="")
    estado_filter = c2.selectbox("Estado", options=["TODOS"] + ESTADOS_VALIDOS, index=0)
    limit = c3.number_input("Max registros", min_value=50, max_value=5000, value=800, step=50)

    rows = dbm.list_clientes_full(
        search=search,
        estado=estado_filter if estado_filter != "TODOS" else "",
        limit=int(limit),
    )

    if not rows:
        st.warning("No se encontraron clientes para el filtro actual.")
    else:
        raw_df = pd.DataFrame(rows)
        editor_df = _normalize_editor_df(raw_df)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total", len(editor_df))
        k2.metric("Activos", int((editor_df["estado"] == "ACTIVO").sum()))
        k3.metric("Inactivos", int((editor_df["estado"] == "INACTIVO").sum()))
        k4.metric("Morosos", int((editor_df["estado"] == "MOROSO").sum()))

        st.caption("Puedes editar celdas, agregar filas nuevas y quitar filas existentes.")
        edited = st.data_editor(
            editor_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="clientes_premium_editor_data",
            column_config={
                "cliente_id": st.column_config.TextColumn("Codigo Cliente", width="small", required=True),
                "nombre": st.column_config.TextColumn("Nombre / Empresa", width="large", required=True),
                "email": st.column_config.TextColumn("Correo", width="medium"),
                "telefono": st.column_config.TextColumn("Telefono", width="small"),
                "ruc": st.column_config.TextColumn("RUC", width="small"),
                "direccion": st.column_config.TextColumn("Direccion", width="large"),
                "estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS_VALIDOS, width="small"),
                "notas": st.column_config.TextColumn("Notas", width="large"),
            },
        )

        allow_delete = st.checkbox(
            "Permitir eliminar en Supabase los clientes que se quiten del editor",
            value=False,
            help="Si esta desactivado, solo se insertan/actualizan filas.",
        )
        if st.button("Guardar Cambios de Cartera", type="primary"):
            records = _rows_from_editor(edited)
            ok_upsert, msg_upsert = dbm.upsert_clientes_rows(records)
            if ok_upsert:
                st.success(msg_upsert)
            else:
                st.error(msg_upsert)

            if allow_delete:
                old_ids = {
                    str(v).strip()
                    for v in editor_df["cliente_id"].tolist()
                    if str(v).strip()
                }
                new_ids = {
                    str(r.get("cliente_id", "")).strip()
                    for r in records
                    if str(r.get("cliente_id", "")).strip()
                }
                to_delete = sorted(old_ids - new_ids)
                if to_delete:
                    ok_del, msg_del = dbm.delete_clientes_by_ids(to_delete)
                    if ok_del:
                        st.warning(msg_del)
                    else:
                        st.error(msg_del)
                else:
                    st.caption("No hay clientes eliminados para aplicar.")

            st.rerun()

    st.markdown("---")
    st.markdown("### 2) Migracion de Cartera desde Excel")
    st.info(
        "Carga un Excel de cartera maestra para insertar/actualizar clientes en bloque "
        "(upsert por `cliente_id`)."
    )
    cartera_file = st.file_uploader(
        "Archivo de Cartera (.xlsx)",
        type=["xlsx"],
        key="clientes_premium_migration_file",
    )
    if cartera_file is not None:
        file_bytes = cartera_file.getvalue()
        try:
            df_preview = pd.read_excel(io.BytesIO(file_bytes))
            st.caption(f"Filas detectadas: {len(df_preview)} | Columnas: {len(df_preview.columns)}")
            st.dataframe(df_preview.head(20), use_container_width=True, height=250)
        except Exception as e_preview:
            st.error("No se pudo leer el archivo de cartera.")
            st.caption(str(e_preview))
            df_preview = None

        if st.button("Migrar Cartera a Supabase", type="primary", disabled=df_preview is None):
            try:
                df_cartera = pd.read_excel(io.BytesIO(file_bytes))
                result = dbm.migrate_clientes_from_cartera_df(df_cartera)
                if result.get("ok"):
                    st.success(result.get("message", "Migracion completada."))
                else:
                    st.error(result.get("message", "Migracion fallida."))
                counts = result.get("counts", {})
                st.caption(
                    f"Registros preparados: {counts.get('rows', 0)} | "
                    f"errores de validacion: {counts.get('errors', 0)}"
                )
                sample_errors = result.get("error_samples") or []
                if sample_errors:
                    with st.expander("Ver errores de validacion (muestra)"):
                        for err in sample_errors:
                            st.text(f"- {err}")
            except Exception as e_mig:
                st.error("No se pudo ejecutar la migracion de cartera.")
                st.caption(str(e_mig))

    st.markdown("---")
    st.markdown("### 3) Operacion Principal (2 archivos)")
    st.success(
        "Modo recomendado: subir solo `CtasxCobrar` y `Cobranza`; "
        "la cartera se toma desde Supabase."
    )
    if st.button("Validar Cartera Maestra Disponible"):
        rows_master = dbm.get_clientes_master(limit=50000)
        if rows_master:
            st.success(f"Cartera maestra lista: {len(rows_master)} clientes en Supabase.")
        else:
            st.error("No hay cartera maestra disponible en Supabase.")
            st.caption(dbm.get_last_error() or "Carga cartera desde esta misma TAB.")
