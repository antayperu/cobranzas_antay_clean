import streamlit as st
import pandas as pd
import hashlib
import utils.db_manager as dbm
import utils.ui.styles as styles
import utils.ui.report_view as ui_report
import utils.helpers as helpers
import utils.storage_manager as storage_mgr
from utils.excel_export import build_export_dataframe, generate_excel
from datetime import datetime


def _normalize_enviar_email(value) -> str:
    raw = str(value).strip().upper()
    if raw in {"SI", "SÍ", "YES", "Y", "1", "TRUE", "ENVIAR"}:
        return "SI"
    if raw in {"NO", "N", "0", "FALSE", "NO ENVIAR"}:
        return "NO"
    if raw in {"", "NAN", "NAT", "NONE", "NULL", "SIN CONFIGURAR", "SINCONFIGURAR"}:
        return "SIN CONFIGURAR"
    return raw


def render_tab(df_final, config):
    """
    Renders the General Report tab with filters, KPIs, and the main table.
    
    Args:
        df_final (pd.DataFrame): The master dataframe.
        config (dict): Configuration dictionary.
        
    Returns:
        pd.DataFrame: The filtered dataframe (df_filtered) to be used by other tabs.
    """
    st.subheader("Reporte General")
    
    if df_final.empty:
        st.info("No hay datos cargados en el Reporte.")
        return pd.DataFrame()

    # --- DISEÑO DE FILTROS V4.3 (Profesional Stacked) ---
    st.markdown("###### 🏢 Filtro Principal")
    empresas = sorted(df_final['EMPRESA'].astype(str).unique().tolist())
    sel_empresa = st.multiselect(
        "Seleccione Empresa(s)", 
        empresas, 
        default=[], 
        placeholder="Todas las empresas (Seleccione para filtrar...)"
    )

    # Fila 2: Filtros Secundarios (Grid limpio)
    col_f1, col_f2, col_f3 = st.columns(3)
    
    # Filtro Estado Detraccion
    estados_dt = ["Todos"] + sorted(df_final['ESTADO DETRACCION'].astype(str).unique().tolist())
    sel_estado = col_f1.selectbox("Estado Detracción", estados_dt)
    
    # Filtro Moneda
    monedas = ["Todos"] + sorted(df_final['MONEDA'].astype(str).unique().tolist())
    sel_moneda = col_f2.selectbox("Moneda", monedas)
    
    # Buscador Global
    search_term = col_f3.text_input("Buscar Documento/Monto")

    # Fila 3: Filtros de Disponibilidad (Email/Telefono)
    col_b1, col_b2, col_b3 = st.columns(3)
    filter_has_email = col_b1.checkbox("☑️ Solo con Correo", value=False)
    filter_has_phone = col_b2.checkbox("☑️ Solo con Teléfono", value=False)
    
    # Aplicar filtros
    df_filtered = df_final.copy()
    
    if sel_empresa:
        df_filtered = df_filtered[df_filtered['EMPRESA'].astype(str).isin(sel_empresa)]

    if sel_estado != "Todos":
        df_filtered = df_filtered[df_filtered['ESTADO DETRACCION'].astype(str) == sel_estado]
    if sel_moneda != "Todos":
        df_filtered = df_filtered[df_filtered['MONEDA'].astype(str) == sel_moneda]
        
    if search_term:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        df_filtered = df_filtered[mask]
    
    # --- RC-FEAT-FILTERS: Email/Phone Availability ---
    if filter_has_email:
        df_filtered = df_filtered[df_filtered['CORREO'].notna() & (df_filtered['CORREO'].str.strip() != '')]
        
    if filter_has_phone:
            df_filtered = df_filtered[df_filtered['TELÉFONO'].notna() & (df_filtered['TELÉFONO'].astype(str).str.strip() != '')]
    
    # --- FILTROS AVANZADOS (Tipo Pedido & Saldo & Enviar Email) ---
    with st.expander("⚙️ Filtros Avanzados (Tipo Pedido, Saldo Real & Enviar Email)", expanded=False):
        c_adv1, c_adv2, c_adv3 = st.columns([2, 1, 1])
        
        with c_adv1:
            tipos_pedido = sorted(df_final['TIPO PEDIDO'].astype(str).unique().tolist())
            default_tipos = [t for t in tipos_pedido if t not in ['PAV', 'DSP']]
            sel_tipo_pedido = st.multiselect("Tipo Pedido", tipos_pedido, default=default_tipos)
        
        with c_adv2:
            opcion_saldo = st.selectbox(
                "Condición Saldo Real", 
                ["Todos", "Mayor que", "Mayor o igual que", "Menor que", "Menor o igual que", "Igual a"],
                index=0
            )
        with c_adv3:
            monto_ref = st.number_input("Monto Referencia", value=0.0, step=10.0)
        
        # Filtro ENVIAR EMAIL (nueva fila)
        if 'Enviar Email' in df_final.columns:
            enviar_norm = df_final['Enviar Email'].apply(_normalize_enviar_email)
            valores_set = set(enviar_norm.tolist())
            preferred = ["SI", "NO", "SIN CONFIGURAR"]
            valores_enviar = [v for v in preferred if v in valores_set]
            valores_enviar.extend(sorted(v for v in valores_set if v not in preferred))
            default_enviar = ["SI"] if "SI" in valores_enviar else []
            sel_enviar_email = st.multiselect(
                "Enviar Email (por defecto: 'SI')", 
                valores_enviar, 
                default=default_enviar,
                help="Filtra por el campo 'Enviar Email'. Por defecto selecciona 'SI'."
            )
        else:
            sel_enviar_email = None
        
        # Aplicar Filtros Avanzados
        if sel_tipo_pedido:
            df_filtered = df_filtered[df_filtered['TIPO PEDIDO'].astype(str).isin(sel_tipo_pedido)]
        
        # Aplicar filtro Saldo Real (con redondeo a 2 decimales para consistencia con Excel)
        # REGLA CRÍTICA: Un documento con Saldo Real = 0 pero con Detracción Pendiente
        # SIEMPRE debe mantenerse en la vista — el cliente aún tiene deuda con el Estado.
        if opcion_saldo != "Todos":
            saldo_col = df_filtered['SALDO REAL'].round(2)
            if opcion_saldo == "Mayor que":
                mask_saldo = saldo_col > monto_ref
            elif opcion_saldo == "Mayor o igual que":
                mask_saldo = saldo_col >= monto_ref
            elif opcion_saldo == "Menor que":
                mask_saldo = saldo_col < monto_ref
            elif opcion_saldo == "Menor o igual que":
                mask_saldo = saldo_col <= monto_ref
            elif opcion_saldo == "Igual a":
                mask_saldo = saldo_col == monto_ref
            else:
                mask_saldo = pd.Series(True, index=df_filtered.index)

            # Preservar documentos con detracción pendiente aunque no cumplan el filtro de saldo
            mask_detrac_pendiente = (
                df_filtered['DETRACCIÓN'].fillna(0) > 0
            ) & (
                df_filtered['ESTADO DETRACCION'].astype(str).str.upper() == 'PENDIENTE'
            )
            df_filtered = df_filtered[mask_saldo | mask_detrac_pendiente]
        
        # Aplicar filtro Enviar Email
        if sel_enviar_email and 'Enviar Email' in df_filtered.columns:
            enviar_norm_filtered = df_filtered['Enviar Email'].apply(_normalize_enviar_email)
            df_filtered = df_filtered[
                enviar_norm_filtered.isin(sel_enviar_email)
            ]
    
    # --- KPI DASHBOARD (Separación de Monedas & Conteo) ---
    def safe_sum(df, col): return df[col].sum() if col in df.columns else 0.0
    
    df_sol = df_filtered[df_filtered['MONEDA'].astype(str).str.startswith('S', na=False)]
    df_dol = df_filtered[~df_filtered['MONEDA'].astype(str).str.startswith('S', na=False)]
    
    # Totales Soles
    t_sal_s = safe_sum(df_sol, 'SALDO')
    # REGLA DE NEGOCIO: Detracciones SIEMPRE suman en Soles, sin importar moneda del doc.
    t_detru_global_s = safe_sum(df_filtered, 'DETRACCIÓN') 
    t_real_s = safe_sum(df_sol, 'SALDO REAL')
    count_s = len(df_sol)
    
    # Totales Dólares
    t_sal_d = safe_sum(df_dol, 'SALDO')
    t_real_d = safe_sum(df_dol, 'SALDO REAL')
    count_d = len(df_dol)
    
    # Renderizar KPIs Custom
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1: st.markdown(styles.kpi_card_dashboard("Total Saldo", t_sal_s, t_sal_d, "#17a2b8"), unsafe_allow_html=True)
    with kpi2: st.markdown(styles.kpi_card_dashboard("Total Detracción", t_detru_global_s, 0, "#dc3545", force_single_s=True), unsafe_allow_html=True)
    with kpi3: st.markdown(styles.kpi_card_dashboard("Total Saldo Real", t_real_s, t_real_d, "#28a745"), unsafe_allow_html=True)
    with kpi4: st.markdown(styles.kpi_card_dashboard("Documentos", count_s, count_d, "#6c757d", is_currency=False), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- RC-FEAT-LEDGER: Status Control Tower (SSOT) ---
    if 'CORREO' in df_filtered.columns:
        unique_emails = df_filtered['CORREO'].dropna().unique().tolist()
        unique_emails = [e for e in unique_emails if str(e).strip() != '']
        
        if unique_emails:
            try:
                status_map = dbm.get_status_map(unique_emails)
            except Exception as e:
                st.error("No se pudo sincronizar tracking de envio desde Supabase.")
                st.caption(str(e))
                status_map = {}
        
            # Update SSOT Tracking Columns from Database
            is_fresh_load = st.session_state.get('fresh_load', False)
            tracking_dirty = st.session_state.get('tracking_dirty', False)
            
            if not is_fresh_load and not tracking_dirty:
                for email, info in status_map.items():
                    mask = (df_final['CORREO'] == email) & (df_final['ESTADO_EMAIL'] == "PENDIENTE")
                    if mask.sum() == 0: continue

                    status = info.get('status', 'PENDIENTE')
                    time_str = info.get('time', '')
                    ts_raw = info.get('ts_raw', '')

                    if status == 'SENT':
                        if 'ESTADO_EMAIL' in df_final.columns: df_final.loc[mask, 'ESTADO_EMAIL'] = "ENVIADO"
                        if 'ESTADO_ENVIO_TEXTO' in df_final.columns: df_final.loc[mask, 'ESTADO_ENVIO_TEXTO'] = f"ENVIADO ({time_str})"
                        if 'FECHA_ULTIMO_ENVIO' in df_final.columns: df_final.loc[mask, 'FECHA_ULTIMO_ENVIO'] = ts_raw
                    elif status == 'FAILED':
                        if 'ESTADO_EMAIL' in df_final.columns: df_final.loc[mask, 'ESTADO_EMAIL'] = "FALLIDO"
                        if 'ESTADO_ENVIO_TEXTO' in df_final.columns: df_final.loc[mask, 'ESTADO_ENVIO_TEXTO'] = "FALLIDO"
                    elif status == 'BLOCKED':
                        if 'ESTADO_EMAIL' in df_final.columns: df_final.loc[mask, 'ESTADO_EMAIL'] = "BLOQUEADO"
                        if 'ESTADO_ENVIO_TEXTO' in df_final.columns: df_final.loc[mask, 'ESTADO_ENVIO_TEXTO'] = f"BLOQUEADO ({time_str})"
                
                st.session_state['df_final'] = df_final

    # --- RC-UX-PREMIUM: ENTERPRISE REPORT TABLE ---
    ui_report.render_report(df_filtered)
    
    # --- DEBUG TOGGLE (QA Only) ---
    with st.expander("🔧 Debug: Tracking Stats (QA)", expanded=False):
        if 'ESTADO_EMAIL' in df_final.columns:
            total_records = len(df_final)
            total_enviados = (df_final['ESTADO_EMAIL'] == "ENVIADO").sum()
            total_pendientes = total_records - total_enviados
            
            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("Total Registros", total_records)
            col_d2.metric("✅ Enviados", total_enviados)
            col_d3.metric("⏳ Pendientes", total_pendientes)
            
            if 'last_tracking_update' in st.session_state:
                st.caption(f"Última actualización: {st.session_state['last_tracking_update'].get('count', 0)} registros a las {st.session_state['last_tracking_update'].get('timestamp', 'N/A')}")
        else:
            st.warning("Columnas de tracking no encontradas en df_final")
    
    # --- PASO 3: EXPORTAR ---
    st.subheader("Exportar Reporte")

    df_export = build_export_dataframe(df_filtered)

    excel_data = generate_excel(df_export)
    
    company = config.get('company_name', 'Empresa_No_Definida')
    export_fname = helpers.get_export_filename(company)
    
    download_clicked = st.download_button(
        label="Descargar Excel Estilizado",
        data=excel_data,
        file_name=export_fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if download_clicked:
        export_digest = hashlib.sha1(excel_data).hexdigest()
        if st.session_state.get("last_export_storage_digest") != export_digest:
            try:
                upload_info = storage_mgr.upload_export_excel(
                    excel_bytes=excel_data,
                    filename=export_fname,
                    company_name=company,
                )
                st.session_state["last_export_storage_digest"] = export_digest
                st.caption(
                    f"Backup Storage: {upload_info['bucket']}/{upload_info['path']}"
                )
            except Exception as e_storage:
                st.warning("No se pudo guardar copia del export en Supabase Storage.")
                st.caption(str(e_storage))
    
    return df_filtered
