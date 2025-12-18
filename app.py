import streamlit as st
import pandas as pd
import urllib.parse
from datetime import date, datetime
from utils.processing import load_data, process_data
from utils.excel_export import generate_excel

# Configuración de Página
import utils.email_sender as es
import utils.settings_manager as sm

# Cargar Configuración Global
CONFIG = sm.load_settings()

st.set_page_config(
    page_title=f"{CONFIG['company_name']} | Gestión de Cobranzas",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS - Branding Dinámico
custom_css = f"""
<style>
    .main-header {{
        background: linear-gradient(90deg, {CONFIG['primary_color']}, {CONFIG['secondary_color']});
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .stApp {{
        --primary-color: {CONFIG['primary_color']};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {CONFIG.get('text_color', '#262730')} !important;
    }}
    .stButton>button {{
        background-color: {CONFIG['primary_color']};
        color: white;
        border-radius: 5px;
        border: none;
        height: 3em;
        width: 100%;
    }}
    .stButton>button:hover {{
        background-color: {CONFIG['secondary_color']};
        color: white;
    }}
    .metric-card {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid {CONFIG['primary_color']};
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    /* Compact Sidebar Helpers */
    .sidebar-logo {{
        text-align: center;
        margin-bottom: 20px;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Encabezado
st.markdown('<div class="main-header"><h1>Gestión Centralizada de Cobranzas</h1></div>', unsafe_allow_html=True)

# Sidebar - Logo y Carga
with st.sidebar:
    # Logo
    import os
    logo_path = os.path.join(os.getcwd(), "assets", "logo_dacta.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown(f"## {CONFIG['company_name']}")

    st.markdown("---")
    
    # Uploaders en Expander para limpieza visual
    st.subheader("📂 Cargar Datos")
    
    file_ctas = st.file_uploader("CtasxCobrar.xlsx", type=["xlsx"])
    file_cobranza = st.file_uploader("Cobranza.xlsx", type=["xlsx"])
    file_cartera = st.file_uploader("cartera_clientes.xlsx", type=["xlsx"])
    
    st.markdown("---")

    # Inicializar Estado de Sesión
    if 'data_ready' not in st.session_state:
        st.session_state['data_ready'] = False
    if 'df_final' not in st.session_state:
        st.session_state['df_final'] = pd.DataFrame()

    # Botón Global de Procesamiento
    if file_ctas and file_cobranza and file_cartera:
        if st.button("Procesar Archivos", type="primary"):
            with st.spinner("Procesando..."):
                df_ctas_raw, df_cartera_raw, df_cobranza_raw, error = load_data(file_ctas, file_cartera, file_cobranza)
                
                if error:
                    st.error(f"Error: {error}")
                    st.session_state['data_ready'] = False
                else:
                    try:
                        df_final = process_data(df_ctas_raw, df_cartera_raw, df_cobranza_raw)
                        st.session_state['df_final'] = df_final
                        st.session_state['data_ready'] = True
                        st.success("Actualizado")
                    except Exception as e:
                        st.error(f"Error Lógico: {str(e)}")
                        st.session_state['data_ready'] = False
    else:
        st.info("Sube los 3 archivos para comenzar.")

# --- PASO 2: VISUALIZACIÓN Y FILTROS ---
if st.session_state['data_ready']:
    df_final = st.session_state['df_final']
    
    st.markdown("---")
    
    # DEFINIR TABS DINÁMICAMENTE
    tab_list = ["Reporte General"]
    
    # Feature Flags
    show_analysis = CONFIG.get("features", {}).get("show_analysis", False)
    show_sales = CONFIG.get("features", {}).get("show_sales", False)
    
    if show_analysis: tab_list.append("2. Análisis")
    if show_sales: tab_list.append("3. Ventas")
    
    tab_list.extend(["4. Marketing WhatsApp", "5. Notificaciones Email", "6. Configuración"])
    
    tabs = st.tabs(tab_list)
    
    # Mapper de tabs para acceso seguro
    tab_map = {name: tab for name, tab in zip(tab_list, tabs)}
    
    # --- TAB 1: REPORTE GENERAL ---
    with tab_map["Reporte General"]:
        st.subheader("Reporte General")
    
        if not df_final.empty:
            # --- DISEÑO DE FILTROS V4.3 (Profesional Stacked) ---
            # Fila 1: Filtro Principal (Empresa) - Full Width para evitar desalineación visual
            # Esto permite que el multiselect crezca hacia abajo sin romper la fila de selectbox
            st.markdown("###### 🏢 Filtro Principal")
            empresas = sorted(df_final['EMPRESA'].astype(str).unique().tolist())
            sel_empresa = st.multiselect(
                "Seleccione Empresa(s)", 
                empresas, 
                default=[], 
                placeholder="Todas las empresas (Seleccione para filtrar...)"
            )

            # Fila 2: Filtros Secundarios (Grid limpio)
            # st.markdown("###### 🔍 Filtros Detallados")
            col_f1, col_f2, col_f3 = st.columns(3)
            
            # Filtro Estado Detraccion
            estados_dt = ["Todos"] + sorted(df_final['ESTADO DETRACCION'].astype(str).unique().tolist())
            sel_estado = col_f1.selectbox("Estado Detracción", estados_dt)
            
            # Filtro Moneda
            monedas = ["Todos"] + sorted(df_final['MONEDA'].astype(str).unique().tolist())
            sel_moneda = col_f2.selectbox("Moneda", monedas)
            
            # Buscador Global
            search_term = col_f3.text_input("Buscar Documento/Monto")
            
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
            
            # --- FILTROS AVANZADOS (Tipo Pedido & Saldo) ---
            with st.expander("⚙️ Filtros Avanzados (Tipo Pedido & Saldo Real)", expanded=False):
                # Layout interno del expander
                c_adv1, c_adv2, c_adv3 = st.columns([2, 1, 1])
                
                with c_adv1:
                    # Filtro TIPO PEDIDO
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
                
                # Aplicar Filtros Avanzados
                if sel_tipo_pedido:
                    df_filtered = df_filtered[df_filtered['TIPO PEDIDO'].astype(str).isin(sel_tipo_pedido)]
                
                if opcion_saldo == "Mayor que":
                    df_filtered = df_filtered[df_filtered['SALDO REAL'] > monto_ref]
                elif opcion_saldo == "Mayor o igual que":
                    df_filtered = df_filtered[df_filtered['SALDO REAL'] >= monto_ref]
                elif opcion_saldo == "Menor que":
                    df_filtered = df_filtered[df_filtered['SALDO REAL'] < monto_ref]
                elif opcion_saldo == "Menor o igual que":
                    df_filtered = df_filtered[df_filtered['SALDO REAL'] <= monto_ref]
                elif opcion_saldo == "Igual a":
                    df_filtered = df_filtered[df_filtered['SALDO REAL'] == monto_ref]
            
            # --- KPI DASHBOARD (Separación de Monedas & Conteo) ---
            # Calcular totales separados
            def safe_sum(df, col): return df[col].sum() if col in df.columns else 0.0
            
            df_sol = df_filtered[df_filtered['MONEDA'].str.contains('S', na=False)]
            df_dol = df_filtered[df_filtered['MONEDA'].str.contains('US', na=False)]
            
            # Totales Soles
            t_sal_s = safe_sum(df_sol, 'SALDO')
            t_det_s = safe_sum(df_sol, 'DETRACCIÓN')
            t_real_s = safe_sum(df_sol, 'SALDO REAL')
            count_s = len(df_sol)
            
            # Totales Dólares
            t_sal_d = safe_sum(df_dol, 'SALDO')
            t_det_d = safe_sum(df_dol, 'DETRACCIÓN')
            t_real_d = safe_sum(df_dol, 'SALDO REAL')
            count_d = len(df_dol)
            
            # Renderizar KPIs Custom
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            def kpi_card(label, val_s, val_d, color="#2E86AB", is_currency=True):
                if is_currency:
                    val_s_str = f"S/ {val_s:,.2f}" if val_s != 0 else "-"
                    val_d_str = f"$ {val_d:,.2f}" if val_d != 0 else "-"
                    # Highlight logic
                    if val_s == 0 and val_d == 0: val_s_str = "S/ 0.00"
                else:
                    # Formato Conteo
                    val_s_str = f"{int(val_s)} docs (S/)" if val_s > 0 else "-"
                    val_str_join = []
                    if val_s > 0: val_str_join.append(f"{int(val_s)} (S/)")
                    if val_d > 0: val_str_join.append(f"{int(val_d)} ($)")
                    
                    if not val_str_join:
                        val_s_str = "0"
                        val_d_str = ""
                    elif len(val_str_join) == 1:
                        val_s_str = val_str_join[0]
                        val_d_str = ""
                    else:
                        val_s_str = val_str_join[0]
                        val_d_str = val_str_join[1]

                html = f"""
                <div style="background:#fff; border-left:4px solid {color}; padding:10px; border-radius:5px; box-shadow:0 2px 4px rgba(0,0,0,0.05); min-height:80px;">
                    <div style="font-size:12px; color:#666; font-weight:bold;">{label}</div>
                    <div style="font-size:16px; color:#333; font-weight:bold; margin-top:5px;">{val_s_str}</div>
                    <div style="font-size:14px; color:#555;">{val_d_str}</div>
                </div>
                """
                return html

            with kpi1: st.markdown(kpi_card("Total Saldo", t_sal_s, t_sal_d, "#17a2b8"), unsafe_allow_html=True)
            with kpi2: st.markdown(kpi_card("Total Detracción", t_det_s, t_det_d, "#dc3545"), unsafe_allow_html=True)
            with kpi3: st.markdown(kpi_card("Total Saldo Real", t_real_s, t_real_d, "#28a745"), unsafe_allow_html=True)
            with kpi4: st.markdown(kpi_card("Documentos", count_s, count_d, "#6c757d", is_currency=False), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- FIX INDICE DINAMICO (Empieza en 1) ---
            # --- VIEW TRANSFORMATION (v4.0) ---
            # Preparar dataframe para mostrar y exportar (sin columnas numéricas crudas, usando las formateadas)
            
            # 1. Definir columnas visibles y su orden experto
            view_cols = [
                'COD CLIENTE', 'EMPRESA', 'TELÉFONO', 
                'TIPO PEDIDO', 'COMPROBANTE', 
                'FECH EMIS', 'FECH VENC',
                'DÍAS MORA', 'ESTADO DEUDA', # Critical Analysis
                'MONEDA', 
                'MONT EMIT_DISPLAY', 
                'DETRACCIÓN_DISPLAY', 'ESTADO DETRACCION',
                'AMORTIZACIONES',
                'SALDO_DISPLAY', 
                'SALDO REAL_DISPLAY', # Key Result (Moved here)
                'MATCH_KEY'
            ]
            
            # Filtrar solo las que existan (por si acaso)
            view_cols = [c for c in view_cols if c in df_filtered.columns]
            
            df_display = df_filtered[view_cols].copy()
            
            # 2. Renombrar las columnas _DISPLAY a sus nombres limpios
            rename_map = {
                'MONT EMIT_DISPLAY': 'MONT EMIT',
                'SALDO_DISPLAY': 'SALDO',
                'DETRACCIÓN_DISPLAY': 'DETRACCIÓN',
                'SALDO REAL_DISPLAY': 'SALDO REAL'
            }
            df_display.rename(columns=rename_map, inplace=True)
            
            # 3. Fix Indices
            df_display.reset_index(drop=True, inplace=True)
            df_display.index = df_display.index + 1
            
            # 4. Mostrar DataFrame con Styling (Semaforo)
            def highlight_status(val):
                color = ''
                if 'Por Vencer' in str(val):
                    color = 'background-color: #d4edda; color: #155724' # Verde suave
                elif 'Preventiva' in str(val):
                    color = 'background-color: #fff3cd; color: #856404' # Amarillo suave
                elif 'Administrativa' in str(val):
                    color = 'background-color: #ffeeba; color: #856404' # Naranja suave (usamos amarillo oscuro)
                elif 'Pre-Legal' in str(val):
                    color = 'background-color: #f8d7da; color: #721c24' # Rojo suave
                return color

            st.dataframe(
                df_display.style.map(highlight_status, subset=['ESTADO DEUDA']),
                use_container_width=True
            )
            
            # --- PASO 3: EXPORTAR ---
            st.subheader("Exportar Reporte")
            # Generar Excel usando la vista limpia (Strings formateados)
            excel_data = generate_excel(df_display)
            st.download_button(
                label="Descargar Excel Estilizado",
                data=excel_data,
                file_name=f"Reporte_Cobranzas_DACTA_SAC_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        else:
             st.info("No hay datos cargados en el Reporte.")

    # --- TABS CONDICIONALES ---
    if show_analysis and "2. Análisis" in tab_map:
        with tab_map["2. Análisis"]:
            st.info("Próximamente: Análisis en Profundidad")
            
    if show_sales and "3. Ventas" in tab_map:
        with tab_map["3. Ventas"]:
            st.info("Próximamente: Reporte de Ventas")

    # --- TAB 4: WHATSAPP ---
    with tab_map["4. Marketing WhatsApp"]:
        st.subheader("Gestión de WhatsApp")

        if not df_filtered.empty:
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.markdown("##### Configurar Plantilla")
                default_template = (
                    "Estimados *{EMPRESA}*,\n\n"
                    "Adjuntamos el Estado de Cuenta actualizado. A la fecha, presentan documentos pendientes por un *Total de: {TOTAL_SALDO_REAL}*.\n\n"
                    "**Detalle de Documentos:**\n"
                    "{DETALLE_DOCS}\n\n"
                    "Agradeceremos gestionar el pago a la brevedad.\n\n"
                    "_Este número es solo para notificaciones. Para comunicarse favor llamar al +51 998 080 797 - Nayda Camacho Quinteros_"
                )
                template = st.text_area("Plantilla del Mensaje", value=default_template, height=350)
                st.caption("Variables: `{EMPRESA}`, `{DETALLE_DOCS}`, `{TOTAL_SALDO_REAL}`, `{TOTAL_SALDO_ORIGINAL}`")

            with c2:
                st.markdown("##### Enviar Mensajes")
                
                # Selección de Clientes (Basado en lo filtrado)
                # Agrupar datos por cliente para la lista de selección
                client_group = df_filtered.groupby(['COD CLIENTE', 'EMPRESA', 'TELÉFONO'])['SALDO REAL'].sum().reset_index()
                # Filtrar solo clientes con deuda positiva (opcional, pero lógico para cobrar)
                client_group = client_group[client_group['SALDO REAL'] > 0]

                # Crear lista de opciones formateada
                client_options = []
                client_map = {}
                for idx, row in client_group.iterrows():
                    label = f"{row['EMPRESA']} (Deuda: S/ {row['SALDO REAL']:,.2f})"
                    client_options.append(label)
                    client_map[label] = row['COD CLIENTE']
                
                # Checkbox para seleccionar todos
                col_sel1, col_sel2 = st.columns([3, 1])
                selected_labels = col_sel1.multiselect(
                    "Seleccione Clientes a Notificar:",
                    options=client_options,
                    default=[] # Por defecto ninguno seleccionado para evitar spam accidental
                )
                
                if col_sel2.button("Seleccionar Todos"):
                    selected_labels = client_options

                st.info(f"Se generarán enlaces para **{len(selected_labels)}** clientes seleccionados.")
                
                # BOTON PROCESAR
                # --- LÓGICA DE GENERACIÓN DE MENSAJES (PREVIEW) ---
                contacts_to_send = []
                
                if selected_labels:
                    st.markdown("##### Vista Previa")
                    
                    for label in selected_labels:
                        cod_cli = client_map[label]
                        docs_cli = df_filtered[df_filtered['COD CLIENTE'] == cod_cli]
                        
                        if docs_cli.empty: continue

                        # Datos Básicos
                        empresa = docs_cli['EMPRESA'].iloc[0]
                        telefono = docs_cli['TELÉFONO'].iloc[0]

                        # 1. Totales por Moneda
                        currency_stats = docs_cli.groupby('MONEDA')['SALDO REAL'].agg(['count', 'sum'])
                        
                        total_parts = []
                        
                        for curr, stats in currency_stats.iterrows():
                            count = int(stats['count'])
                            amount = stats['sum']
                            symbol = "S/" if str(curr).upper().startswith("S") else "$"
                            
                            # Formato solicitado: S/ 138.08 (03 documentos)
                            total_parts.append(f"{symbol} {amount:,.2f} ({count:02d} documentos)")
                        
                        # Unir con " y "
                        if total_parts:
                            total_real_str = " y ".join(total_parts)
                        else:
                            total_real_str = "0.00"
                        
                        total_orig_val = docs_cli['SALDO'].sum()

                        # 2. Detalle de Documentos
                        docs_lines = []
                        for _, doc in docs_cli.iterrows():
                            saldo_doc_real = doc['SALDO REAL']
                            comprobante = doc['COMPROBANTE']
                            emis = pd.to_datetime(doc['FECH EMIS']).strftime('%d/%m/%Y')
                            venc = pd.to_datetime(doc['FECH VENC']).strftime('%d/%m/%Y')
                            
                            mon_code = str(doc['MONEDA'])
                            mon_sym = "S/" if mon_code.upper().startswith("S") else "$"
                            monto_emit = f"{mon_sym}{doc['MONT EMIT']:,.2f}"
                            saldo_fmt = f"{mon_sym}{saldo_doc_real:,.2f}"
                            
                            det_val = doc['DETRACCIÓN']
                            det_estado = doc['ESTADO DETRACCION']
                            
                            if det_estado == "Pendiente": estado_str = "Pendiente"
                            elif det_estado in ["-", "No Aplica"]: estado_str = "-"
                            else: estado_str = "Aplicada" 
                            
                            det_info = ""
                            if det_val > 0:
                                det_info = f" | Detr: S/{det_val:,.2f} ({estado_str})"
                            
                            # --- DISEÑO SMART ---
                            venc_short = pd.to_datetime(doc['FECH VENC']).strftime('%d/%m')
                            
                            line1 = f"📄 *{comprobante}* (Venc: {venc_short})"
                            line2 = f"💰 Imp: {monto_emit}  »  Saldo: *{saldo_fmt}*"
                            
                            line3 = ""
                            if det_val > 0:
                                icon_det = "⚠️" if det_estado == "Pendiente" else "ℹ️"
                                line3 = f"\n{icon_det} Detr: S/ {det_val:,.2f} ({estado_str})"

                            block = f"{line1}\n{line2}{line3}\n────────────────"
                            docs_lines.append(block)
                        
                        txt_detalle = "\n".join(docs_lines)

                        # Data dict for replacement (and sending)
                        contact_data = {
                            'nombre_cliente': empresa,
                            'telefono': telefono,
                            'EMPRESA': empresa,
                            'DETALLE_DOCS': txt_detalle,
                            'TOTAL_SALDO_REAL': total_real_str,
                            'TOTAL_SALDO_ORIGINAL': f"{total_orig_val:,.2f}",
                            'venta_neta': total_orig_val, 
                            'numero_transacciones': len(docs_cli)
                        }
                        
                        msg_preview = template
                        msg_preview = msg_preview.replace("{EMPRESA}", str(empresa))
                        msg_preview = msg_preview.replace("{DETALLE_DOCS}", txt_detalle)
                        msg_preview = msg_preview.replace("{TOTAL_SALDO_REAL}", contact_data['TOTAL_SALDO_REAL'])
                        msg_preview = msg_preview.replace("{TOTAL_SALDO_ORIGINAL}", contact_data['TOTAL_SALDO_ORIGINAL'])
                        
                        contact_data['mensaje'] = msg_preview
                        contacts_to_send.append(contact_data)
                        
                        # Mostrar Preview
                        with st.expander(f"📨 {empresa} ({telefono})", expanded=False):
                            st.text_area("Mensaje", value=msg_preview, height=200, key=f"preview_{cod_cli}")

                # BOTON NUEVO: ENVIAR WHATSAPP (Selenium)
                if st.button("Enviar Mensajes por WhatsApp", type="primary"):
                    if not contacts_to_send:
                        st.warning("⚠️ No hay mensajes generados para enviar. Selecciona clientes.")
                    else:
                        import utils.whatsapp_sender as ws
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        log_expander = st.expander("Ver Log de Envío", expanded=True)
                        log_area = log_expander.empty()

                        def update_progress(current, total, text, log_content):
                            if total > 0:
                                progress_bar.progress(min(current / total, 1.0))
                            status_text.markdown(f"**Procesando:** {text}")
                            log_area.code(log_content, language="text")

                        try:
                            result = ws.send_whatsapp_messages_direct(
                                contacts_to_send, 
                                template, 
                                speed="Normal (Recomendado)", 
                                progress_callback=update_progress
                            )
                            
                            st.success(f"✅ Proceso Finalizado. Exitosos: {result['exitosos']}, Fallidos: {result['fallidos']}")
                            if result['errores']:
                                st.error("Errores encontrados:")
                                for err in result['errores']:
                                    st.text(f"• {err}")
                        except Exception as e:
                            st.error(f"Error crítico al iniciar el envío: {str(e)}")
                            st.info("No hay datos para mostrar notificaciones.")
        else:
             st.info("No hay datos para mostrar notificaciones.")
    
    # --- TAB 5: EMAIL ---
    with tab_map["5. Notificaciones Email"]:
        st.subheader("Gestión de Correos")
        
        if not df_filtered.empty:
            c_mail1, c_mail2 = st.columns([1, 1])
            
            with c_mail1:
                st.markdown("##### Destinatarios")
                
                if 'EMAIL_FINAL' in df_filtered.columns:
                    client_group_email = df_filtered[df_filtered['EMAIL_FINAL'] != ""].groupby(
                        ['COD CLIENTE', 'EMPRESA', 'EMAIL_FINAL']
                    )['SALDO REAL'].sum().reset_index()
                    
                    client_group_email = client_group_email[client_group_email['SALDO REAL'] > 0]
                    
                    email_options = []
                    email_map = {}
                    
                    for idx, row in client_group_email.iterrows():
                        # Calcular desglose por moneda para el label
                        cod_cli = row['COD CLIENTE']
                        docs_cli_temp = df_filtered[df_filtered['COD CLIENTE'] == cod_cli]
                        
                        s_temp = docs_cli_temp[docs_cli_temp['MONEDA'].str.contains('S', na=False)]['SALDO REAL'].sum()
                        d_temp = docs_cli_temp[docs_cli_temp['MONEDA'].str.contains('US', na=False)]['SALDO REAL'].sum()
                        
                        # Label Mejorado: EMPRESA (Email) | S/ 100 | $ 50
                        label_parts = [f"{row['EMPRESA']} ({row['EMAIL_FINAL']})"]
                        if s_temp > 0: label_parts.append(f"S/ {s_temp:,.2f}")
                        if d_temp > 0: label_parts.append(f"$ {d_temp:,.2f}")
                        
                        label = " | ".join(label_parts)
                        
                        email_options.append(label)
                        email_map[label] = {
                            'cod': row['COD CLIENTE'],
                            'email': row['EMAIL_FINAL'],
                            'empresa': row['EMPRESA'],
                            'deb_s': s_temp,
                            'deb_d': d_temp
                        }
                    
                    # --- FIX SELECT ALL: Usar Session State ---
                    if "email_sel_key" not in st.session_state:
                         st.session_state["email_sel_key"] = []
                    
                    # Limpiar selección si las opciones cambiaron (filtros) para evitar crash de Streamlit
                    valid_opts_set = set(email_options)
                    st.session_state["email_sel_key"] = [x for x in st.session_state["email_sel_key"] if x in valid_opts_set]

                    def select_all_callback():
                        st.session_state["email_sel_key"] = email_options

                    sel_emails = st.multiselect(
                        f"Seleccione Clientes con Correo ({len(email_options)} disponibles):",
                        options=email_options,
                        key="email_sel_key"
                    )
                    
                    st.button("Seleccionar Todos (Email)", on_click=select_all_callback)
                    
                    # --- DASHBOARD RESUMEN DE ENVÍO ---
                    if sel_emails:
                        st.markdown("---")
                        st.markdown("###### 📊 Resumen de Envío Seleccionado")
                        
                        total_cli_sel = len(sel_emails)
                        total_s_sel = sum(email_map[x]['deb_s'] for x in sel_emails)
                        total_d_sel = sum(email_map[x]['deb_d'] for x in sel_emails)
                        
                        st.markdown("""
                        <style>
                            .stat-box {
                                background-color: #f8f9fa;
                                border: 1px solid #e9ecef;
                                border-radius: 8px;
                                padding: 15px;
                                text-align: center;
                            }
                            .stat-label { font-size: 0.9em; color: #6c757d; margin-bottom: 5px; }
                            .stat-value { font-size: 1.4em; font-weight: bold; color: #2E86AB; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
                            .stat-value svg { margin-right: 5px; }
                        </style>
                        """, unsafe_allow_html=True)

                        k1, k2, k3 = st.columns(3)
                        
                        with k1:
                            st.markdown(f"""
                            <div class="stat-box">
                                <div class="stat-label">Destinatarios</div>
                                <div class="stat-value">👥 {total_cli_sel}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with k2:
                            st.markdown(f"""
                            <div class="stat-box">
                                <div class="stat-label">Total Soles</div>
                                <div class="stat-value" title="S/ {total_s_sel:,.2f}">S/ {total_s_sel:,.2f}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with k3:
                            st.markdown(f"""
                            <div class="stat-box">
                                <div class="stat-label">Total Dólares</div>
                                <div class="stat-value" title="$ {total_d_sel:,.2f}">$ {total_d_sel:,.2f}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("---")
                        
                else:
                    st.warning("⚠️ No se detectó columna de Email. Vuelve a procesar los archivos.")
                    sel_emails = []

            with c_mail2:
                st.markdown("##### Vista Previa (HTML)")
                
                if sel_emails:
                    import utils.email_sender as es
                    import streamlit.components.v1 as components
                    import os
                    import base64
                    
                    logo_path = os.path.join(os.getcwd(), "assets", "logo_dacta.png")
                    
                    for selected_label in sel_emails:
                        info_sel = email_map[selected_label]
                        docs_cli_mail = df_filtered[df_filtered['COD CLIENTE'] == info_sel['cod']]
                        
                        totales_s = docs_cli_mail[docs_cli_mail['MONEDA'].str.contains('S', na=False, case=False)]['SALDO REAL'].sum()
                        totales_d = docs_cli_mail[docs_cli_mail['MONEDA'].str.contains('US', na=False, case=False)]['SALDO REAL'].sum()
                        
                        txt_s = f"S/ {totales_s:,.2f}" if totales_s > 0 else ""
                        txt_d = f"$ {totales_d:,.2f}" if totales_d > 0 else ""
                        
                        # Generar HTML (cid)
                        preview_html_cid = es.generate_premium_email_body_cid(
                            info_sel['empresa'],
                            docs_cli_mail,
                            txt_s,
                            txt_d,
                            CONFIG
                        )
                        
                        # Convertir imagen a base64 para el preview en iframe
                        try:
                            with open(logo_path, "rb") as image_file:
                                    encoded_string = base64.b64encode(image_file.read()).decode()
                            src_base64 = f"data:image/png;base64,{encoded_string}"
                            preview_html_view = preview_html_cid.replace("cid:logo_dacta", src_base64)
                        except:
                            preview_html_view = preview_html_cid # Fallback sin logo visual
                        
                        with st.expander(f"✉️ {info_sel['empresa']}", expanded=False):
                            components.html(preview_html_view, height=500, scrolling=True)
                    
                    st.markdown("---")
                    if st.button("Enviar Correos Masivos", type="primary"):
                        # Credenciales ahora vienen de CONFIG global
                        smtp_cfg = CONFIG.get('smtp_config', {})
                        email_user = smtp_cfg.get('user', '')
                        email_pass = smtp_cfg.get('password', '')

                        if not email_user or not email_pass:
                             st.error("❌ Faltan credenciales SMTP. Configúralas en la pestaña 'Configuración'.")
                        else:
                            messages_to_send = []
                            for lbl in sel_emails:
                                info = email_map[lbl]
                                d_cli = df_filtered[df_filtered['COD CLIENTE'] == info['cod']]
                                
                                t_s = d_cli[d_cli['MONEDA'].str.contains('S', na=False)]['SALDO REAL'].sum()
                                t_d = d_cli[d_cli['MONEDA'].str.contains('US', na=False)]['SALDO REAL'].sum()
                                str_s = f"S/ {t_s:,.2f}" if t_s > 0 else ""
                                str_d = f"$ {t_d:,.2f}" if t_d > 0 else ""
                                
                                str_s = f"S/ {t_s:,.2f}" if t_s > 0 else ""
                                str_d = f"$ {t_d:,.2f}" if t_d > 0 else ""
                                
                                body = es.generate_premium_email_body_cid(info['empresa'], d_cli, str_s, str_d, CONFIG)
                                plain_body = es.generate_plain_text_body(info['empresa'], d_cli, str_s, str_d, CONFIG)
                                
                                # Asunto Profesional Anti-Spam
                                company_sender = CONFIG.get('company_name', 'DACTA S.A.C.')
                                subject_line = f"Estado de Cuenta {company_sender} | Cliente: {info['empresa']}"
                                
                                messages_to_send.append({
                                    'email': info['email'],
                                    'client_name': info['empresa'],
                                    'subject': subject_line,
                                    'html_body': body,
                                    'plain_body': plain_body
                                })
                            
                            smtp_cfg = {
                                'server': CONFIG.get('smtp_config', {}).get('server', 'smtp.gmail.com'),
                                'port': CONFIG.get('smtp_config', {}).get('port', 587),
                                'user': email_user,
                                'password': email_pass
                            }
                            
                            prog_bar = st.progress(0)
                            status_txt = st.empty()
                            
                            def update_prog(curr, tot, txt):
                                prog_bar.progress(curr/tot)
                                status_txt.text(txt)
                            
                            res = es.send_email_batch(smtp_cfg, messages_to_send, update_prog, logo_path=logo_path)
                            
                            st.success(f"✅ Enviados: {res['success']} | Fallidos: {res['failed']}")
                            with st.expander("Ver Log SMTP (Detallado)"):
                                for l in res['log']:
                                    st.text(l)
                                    if "535" in l:
                                        st.error("Error 535: Revisa tu contraseña de aplicación de Gmail.")
                else:
                    st.info("Selecciona un cliente para ver la vista previa.")

        else:
             st.info("Sube los archivos y filtra para ver las notificaciones.")

    # --- TAB 6: CONFIGURACIÓN GLOBAL ---
    with tab_map["6. Configuración"]:
        st.header("Configuración del Sistema")
        
        with st.form("config_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Identidad Corporativa")
                new_company = st.text_input("Nombre de la Empresa", value=CONFIG['company_name'])
                new_ruc = st.text_input("RUC", value=CONFIG['company_ruc'])
                new_phone = st.text_input("Teléfono de Contacto", value=CONFIG['phone_contact'])
                
                st.subheader("Branding (Colores)")
                new_primary = st.color_picker("Color Primario (Encabezados/Botones)", value=CONFIG['primary_color'])
                new_secondary = st.color_picker("Color Secundario (Acentos)", value=CONFIG['secondary_color'])
                # Nuevo: Color de Texto
                curr_text_col = CONFIG.get('text_color', '#262730')
                new_text_color = st.color_picker("Color de Texto (Títulos)", value=curr_text_col, help="Color para títulos y encabezados. El cuerpo se mantiene legible.")

            with col2:
                st.subheader("Funcionalidades (Tabs)")
                f_analysis = st.checkbox("Mostrar Tab Análisis", value=CONFIG.get('features', {}).get('show_analysis', False))
                f_sales = st.checkbox("Mostrar Tab Ventas", value=CONFIG.get('features', {}).get('show_sales', False))
                
                st.markdown("---")
                st.subheader("Configuración de Correo (SMTP)")
                st.info("Credenciales para el envío de correos masivos.")
                st.markdown("""
                > **Nota Importante para Gmail:**  
                > Debes usar una **Contraseña de Aplicación**, no tu clave normal.  
                > 1. Ve a tu Cuenta de Google > Seguridad.  
                > 2. Activa la Verificación en 2 pasos.  
                > 3. Busca "Contraseñas de aplicaciones" y genera una nueva.  
                > [Ver Guía Oficial de Google](https://support.google.com/accounts/answer/185833)
                """)
                new_smtp_server = st.text_input("Servidor SMTP", value=CONFIG['smtp_config']['server'])
                new_smtp_port = st.text_input("Puerto SMTP", value=CONFIG['smtp_config']['port'])
                new_smtp_user = st.text_input("Usuario (Correo)", value=CONFIG['smtp_config']['user'])
                new_smtp_pass = st.text_input("Contraseña App", value=CONFIG['smtp_config']['password'], type="password")

            st.markdown("---")
            st.subheader("Plantilla de Correo")
            col_t1, col_t2 = st.columns(2)
            new_intro = col_t1.text_area("Texto Introductorio", value=CONFIG['email_template']['intro_text'], height=150, help="Texto antes de la tabla de deuda.")
            new_footer = col_t2.text_area("Texto Pie de Página", value=CONFIG['email_template']['footer_text'], height=150, help="Texto después de los totales.")
            new_alert = st.text_area("Texto Alerta Detracción", value=CONFIG['email_template']['alert_text'], help="Mensaje resaltado sobre cuentas de detracción.")

            submitted = st.form_submit_button("Guardar Configuración")
            
            if submitted:
                new_settings = {
                    "company_name": new_company,
                    "company_ruc": new_ruc,
                    "phone_contact": new_phone,
                    "primary_color": new_primary,
                    "secondary_color": new_secondary,
                    "text_color": new_text_color,
                    "features": {
                        "show_analysis": f_analysis,
                        "show_sales": f_sales
                    },
                    "email_template": {
                        "intro_text": new_intro,
                        "footer_text": new_footer,
                        "alert_text": new_alert
                    },
                    "smtp_config": {
                        "server": new_smtp_server,
                        "port": new_smtp_port,
                        "user": new_smtp_user,
                        "password": new_smtp_pass
                    }
                }
                if sm.save_settings(new_settings):
                    st.success("✅ Configuración guardada correctamente. Por favor recarga la página para aplicar cambios visuales.")
                    st.rerun() # Recarga inmediata
                else:
                    st.error("❌ Error al guardar la configuración.")

        st.subheader("Logo de la Empresa")
        uploaded_logo = st.file_uploader("Subir Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        if uploaded_logo:
            import os
            assets_dir = os.path.join(os.getcwd(), "assets")
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir)
            
            logo_path = os.path.join(assets_dir, "logo_dacta.png")
            with open(logo_path, "wb") as f:
                f.write(uploaded_logo.getbuffer())
            st.success("Logo actualizado correctamente!")
            st.image(logo_path, width=200)

else:
    # Mensaje de bienvenida inicial cuando no hay datos
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h3>Bienvenido</h3>
        <p>Por favor utiliza el menú lateral para cargar tus archivos de <strong>CtasxCobrar, Cobranza y Cartera</strong>.</p>
        <p style='color: gray; font-size: 0.9em;'>El sistema procesará automáticamente la información.</p>
    </div>
    """, unsafe_allow_html=True)
