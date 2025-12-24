import streamlit as st
import pandas as pd
import urllib.parse
from datetime import date, datetime
import hashlib
from utils.processing import load_data, process_data
from utils.excel_export import generate_excel

# Configuración de Página
import utils.email_sender as es
import utils.settings_manager as sm
import utils.helpers as helpers
import utils.image_processor as img_proc
import utils.qa_mode as qa_lib
import streamlit.components.v1 as components
import os
import base64

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
    
    # Inicializar estado de archivos en sesión
    if 'uploaded_files' not in st.session_state:
        st.session_state['uploaded_files'] = {
            'ctas': None,
            'cobranza': None,
            'cartera': None
        }
    
    # Uploaders con persistencia
    file_ctas_new = st.file_uploader("CtasxCobrar.xlsx", type=["xlsx"], key="uploader_ctas")
    file_cobranza_new = st.file_uploader("Cobranza.xlsx", type=["xlsx"], key="uploader_cobranza")
    file_cartera_new = st.file_uploader("cartera_clientes.xlsx", type=["xlsx"], key="uploader_cartera")
    
    # Actualizar archivos en sesión si se cargan nuevos
    if file_ctas_new:
        st.session_state['uploaded_files']['ctas'] = file_ctas_new
    if file_cobranza_new:
        st.session_state['uploaded_files']['cobranza'] = file_cobranza_new
    if file_cartera_new:
        st.session_state['uploaded_files']['cartera'] = file_cartera_new
    
    # Usar archivos de sesión
    file_ctas = st.session_state['uploaded_files']['ctas']
    file_cobranza = st.session_state['uploaded_files']['cobranza']
    file_cartera = st.session_state['uploaded_files']['cartera']
    
    # Mostrar estado de archivos cargados
    if file_ctas or file_cobranza or file_cartera:
        st.success(f"✅ Archivos en memoria: {sum([1 for f in [file_ctas, file_cobranza, file_cartera] if f is not None])}/3")
        
        # Botón para limpiar archivos
        if st.button("🗑️ Limpiar Archivos", help="Elimina los archivos cargados de la memoria"):
            st.session_state['uploaded_files'] = {
                'ctas': None,
                'cobranza': None,
                'cartera': None
            }
            st.session_state['data_ready'] = False
            st.rerun()
    
    st.markdown("---")
    
    # --- RC-BUG-014: Business Key Inputs ---
    # Fecha de Corte Explícita para Business Key (Idempotencia)
    st.subheader("📅 Parámetros de Reporte")
    fecha_corte = st.date_input("Fecha de Corte (Business Key)", value=date.today(), help="Define el periodo para evitar duplicados en la misma fecha")

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
            
            # FIX v4.3.1: Usar startswith para evitar que 'US$' (contiene S) caiga en Soles
            df_sol = df_filtered[df_filtered['MONEDA'].astype(str).str.startswith('S', na=False)]
            # Para Dolares asumimos el resto o que contiene U/$.
            df_dol = df_filtered[~df_filtered['MONEDA'].astype(str).str.startswith('S', na=False)]
            
            # Totales Soles
            t_sal_s = safe_sum(df_sol, 'SALDO')
            # REGLA DE NEGOCIO: Detracciones SIEMPRE suman en Soles, sin importar moneda del doc.
            # Agrupamos todas las detracciones del filtro actual.
            t_detru_global_s = safe_sum(df_filtered, 'DETRACCIÓN') 
            t_real_s = safe_sum(df_sol, 'SALDO REAL')
            count_s = len(df_sol)
            
            # Totales Dólares
            t_sal_d = safe_sum(df_dol, 'SALDO')
            # t_det_d = safe_sum(df_dol, 'DETRACCIÓN') # Eliminado: Detracción NO existe en Dólares
            t_real_d = safe_sum(df_dol, 'SALDO REAL')
            count_d = len(df_dol)
            
            # Renderizar KPIs Custom
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            def kpi_card(label, val_s, val_d, color="#2E86AB", is_currency=True, force_single_s=False):
                if is_currency:
                    # Lógica de visualización: Solo mostrar lo que tiene valor > 0
                    # Si ambos 0, mostrar S/ 0.00
                    s_visible = abs(val_s) > 0.01
                    d_visible = abs(val_d) > 0.01
                    
                    if force_single_s:
                        # Caso especial Detracción: Solo mostrar línea S/
                        lines = [f"<div style='font-size:16px; color:#333; font-weight:bold; margin-top:5px;'>S/ {val_s:,.2f}</div>"]
                    elif not s_visible and not d_visible:
                        lines = [f"<div style='font-size:16px; color:#333; font-weight:bold; margin-top:5px;'>S/ 0.00</div>"]
                    else:
                        lines = []
                        if s_visible:
                             lines.append(f"<div style='font-size:16px; color:#333; font-weight:bold; margin-top:5px;'>S/ {val_s:,.2f}</div>")
                        if d_visible:
                             # Si dolar es el único, lo ponemos grande, si es segundo, un poco dif
                             style = "font-size:16px; color:#333; font-weight:bold; margin-top:5px;" if not s_visible else "font-size:14px; color:#555;"
                             lines.append(f"<div style='{style}'>$ {val_d:,.2f}</div>")
                    
                    html_content = "".join(lines)

                else:
                    # Formato Conteo
                    # Solo mostrar los que tienen > 0
                    lines = []
                    if val_s > 0: lines.append(f"<div style='font-size:16px; color:#333; font-weight:bold; margin-top:5px;'>{int(val_s)} (S/)</div>")
                    if val_d > 0:
                        style = "font-size:16px; color:#333; font-weight:bold; margin-top:5px;" if val_s == 0 else "font-size:14px; color:#555;"
                        lines.append(f"<div style='{style}'>{int(val_d)} ($)</div>")
                    
                    if not lines:
                         lines.append("<div style='font-size:16px; color:#333; font-weight:bold; margin-top:5px;'>0</div>")
                    
                    html_content = "".join(lines)

                html = f"""
                <div style="background:#fff; border-left:4px solid {color}; padding:10px; border-radius:5px; box-shadow:0 2px 4px rgba(0,0,0,0.05); min-height:80px;">
                    <div style="font-size:12px; color:#666; font-weight:bold;">{label}</div>
                    {html_content}
                </div>
                """
                return html

            with kpi1: st.markdown(kpi_card("Total Saldo", t_sal_s, t_sal_d, "#17a2b8"), unsafe_allow_html=True)
            with kpi2: st.markdown(kpi_card("Total Detracción", t_detru_global_s, 0, "#dc3545", force_single_s=True), unsafe_allow_html=True)
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
                'MONEDA', 'TIPO CAMBIO',
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
            
            # [FIX RC-BUG-004] Usar columnas NUMÉRICAS para el Excel (no strings formateados)
            # Definir columnas de exportación (misma estructura que view, pero usando valores raw)
            export_cols = [
                'COD CLIENTE', 'EMPRESA', 'TELÉFONO', 
                'TIPO PEDIDO', 'COMPROBANTE', 
                'FECH EMIS', 'FECH VENC',
                'DÍAS MORA', 'ESTADO DEUDA',
                'MONEDA', 'TIPO CAMBIO',
                'MONT EMIT', # Numérico
                'DETRACCIÓN', # Numérico
                'ESTADO DETRACCION',
                'AMORTIZACIONES',
                'SALDO', # Numérico
                'SALDO REAL', # Numérico
                'MATCH_KEY'
            ]
            # Filtrar existentes
            export_cols = [c for c in export_cols if c in df_filtered.columns]
            
            df_export = df_filtered[export_cols].copy()
            
            # Reset Index para que coincida con lo visual (si se usa index en excel)
            df_export.reset_index(drop=True, inplace=True)
            df_export.index = df_export.index + 1
            
            # Generar Excel con datos numéricos (excel_export se encarga del formato visual)
            excel_data = generate_excel(df_export)
            
            # [FIX RC-UX-001] Nombre dinámico (Empresa + Timestamp)
            company = CONFIG.get('company_name', 'Empresa_No_Definida')
            export_fname = helpers.get_export_filename(company)
            
            st.download_button(
                label="Descargar Excel Estilizado",
                data=excel_data,
                file_name=export_fname,
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
                
                # Cargar plantilla de CONFIG o usar default si no existe
                saved_template = CONFIG.get('whatsapp_template', (
                    "Estimados *{EMPRESA}*,\n\n"
                    "Adjuntamos el Estado de Cuenta actualizado. A la fecha, presentan documentos pendientes por un *Total de: {TOTAL_SALDO_REAL}*.\n\n"
                    "**Detalle de Documentos:**\n"
                    "{DETALLE_DOCS}\n\n"
                    "Agradeceremos gestionar el pago a la brevedad.\n\n"
                    "_DACTA S.A.C. | RUC: 20375779448 Este es un mensaje automático de notificación de deuda. Consultas: +51 998 080 797_"
                ))
                
                template = st.text_area("Plantilla del Mensaje", value=saved_template, height=350)
                
                # --- BOTÓN GUARDAR PLANTILLA ---
                if st.button("💾 Guardar como Plantilla Predeterminada"):
                    new_config = CONFIG.copy()
                    new_config['whatsapp_template'] = template
                    if sm.save_settings(new_config):
                        st.success("✅ Plantilla guardada correctamente.")
                        # Actualizamos CONFIG local para la sesión actual
                        CONFIG['whatsapp_template'] = template
                    else:
                        st.error("❌ No se pudo guardar la plantilla.")
                
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
                
                # ========== NUEVO: SELECTOR DE MODO DE ENVÍO v5.0 ==========
                st.markdown("---")
                st.markdown("### ⚙️ Configuración de Envío WhatsApp")
                
                # Información general
                st.info("💡 **v5.0 Pro Upgrade**: Elige cómo enviar tus notificaciones de cobranza")
                
                # Selector de modo simplificado
                send_mode_options = [
                    ("texto", "📝 Solo Texto (Estable)", "Mensaje de texto plano sin archivos adjuntos")
                ]
                
                send_mode_index = st.radio(
                    "**Modo de Envío:**",
                    range(len(send_mode_options)),
                    format_func=lambda x: send_mode_options[x][1],
                    index=0,  # Default: Texto
                    help="Elige cómo se enviarán los mensajes a tus clientes"
                )
                
                # Bloque informativo de mantenimiento
                st.info("ℹ️ **Nota:** Los modos *Tarjeta Ejecutiva* y *PDF* se encuentran en mantenimiento por actualización a v5.0. Estarán disponibles próximamente.")
                send_mode_value = send_mode_options[send_mode_index][0]
                
                # Mostrar descripción del modo seleccionado con colores
                selected_description = send_mode_options[send_mode_index][2]
                if send_mode_value == "texto":
                    st.warning(f"💬 {selected_description}")
                elif send_mode_value == "imagen_ejecutiva":
                    st.success(f"🎴 {selected_description}")
                else:
                    st.info(f"📊 {selected_description}")
                
                # ========== FIN SELECTOR DE MODO ==========
                
                # BOTON PROCESAR
                # --- LÓGICA DE GENERACIÓN DE MENSAJES (PREVIEW) ---
                contacts_to_send = []
                
                if selected_labels:
                    st.markdown("##### Vista Previa")
                    
                    # SOLUCIÓN 1: Cargar logo en scope global (antes del loop)
                    # Esto garantiza que logo_b64 esté disponible tanto para preview como para envío
                    import base64
                    import os
                    logo_path = os.path.join(os.getcwd(), "assets", "logo_dacta.png")
                    logo_b64 = ""
                    if os.path.exists(logo_path):
                        try:
                            with open(logo_path, "rb") as img_file:
                                logo_b64 = base64.b64encode(img_file.read()).decode()
                        except:
                            pass
                    
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

                        # ========== NUEVO v5.0: Preparar datos para tarjeta ejecutiva y PDF ==========
                        # Calcular totales por moneda para la tarjeta ejecutiva
                        df_sol_cli = docs_cli[docs_cli['MONEDA'].astype(str).str.startswith('S', na=False)]
                        df_dol_cli = docs_cli[~docs_cli['MONEDA'].astype(str).str.startswith('S', na=False)]
                        
                        sum_s_cli = df_sol_cli['SALDO REAL'].sum() if len(df_sol_cli) > 0 else 0
                        sum_d_cli = df_dol_cli['SALDO REAL'].sum() if len(df_dol_cli) > 0 else 0
                        count_s_cli = len(df_sol_cli)
                        count_d_cli = len(df_dol_cli)
                        
                        # Data dict for replacement (and sending)
                        contact_data = {
                            'nombre_cliente': empresa,
                            'telefono': telefono,
                            'EMPRESA': empresa,
                            'DETALLE_DOCS': txt_detalle,
                            'TOTAL_SALDO_REAL': total_real_str,
                            'TOTAL_SALDO_ORIGINAL': f"{total_orig_val:,.2f}",
                            'venta_neta': total_orig_val, 
                            'numero_transacciones': len(docs_cli),
                            # NUEVO v5.0: Datos para tarjeta ejecutiva y PDF
                            'docs_df': docs_cli,  # DataFrame completo de documentos
                            'TOTAL_SALDO_S': f"S/ {sum_s_cli:,.2f}",
                            'TOTAL_SALDO_D': f"$ {sum_d_cli:,.2f}",
                            'COUNT_DOCS_S': count_s_cli,
                            'COUNT_DOCS_D': count_d_cli,
                            'cod_cliente': cod_cli  # Para referencia
                        }
                        
                        msg_preview = template
                        msg_preview = msg_preview.replace("{EMPRESA}", str(empresa))
                        msg_preview = msg_preview.replace("{DETALLE_DOCS}", txt_detalle)
                        msg_preview = msg_preview.replace("{TOTAL_SALDO_REAL}", contact_data['TOTAL_SALDO_REAL'])
                        msg_preview = msg_preview.replace("{TOTAL_SALDO_ORIGINAL}", contact_data['TOTAL_SALDO_ORIGINAL'])
                        
                        contact_data['mensaje'] = msg_preview
                        contacts_to_send.append(contact_data)
                        
                        # Mostrar Preview
                        # Mostrar Preview (Rich HTML Card)
                        with st.expander(f"📨 {empresa} ({telefono})", expanded=False):
                            # --- v4.4 PREMIUM PREVIEW (Dynamic Branding) ---
                            import streamlit.components.v1 as components
                            
                            # 1. Colors (logo_b64 ya está cargado en scope global)
                            primary_col = CONFIG.get('primary_color', '#007bff')
                            secondary_col = CONFIG.get('secondary_color', '#00d4ff')
                            
                            # --- HELPER FUNCTION: CREATE WHATSAPP DOCUMENT HTML (TABULAR) ---
                            def create_whatsapp_document_html(client_name, docs_df, p_col, s_col, logo_data_b64):
                                # 1. Generar Filas de la Tabla (Estilo Email PC)
                                table_rows = ""
                                for _, row in docs_df.iterrows():
                                    mon = str(row.get('MONEDA', ''))
                                    sym = "S/" if mon.upper().startswith('S') else "$"
                                    f_venc = pd.to_datetime(row.get('FECH VENC')).strftime('%d/%m/%y')
                                    
                                    m_emit = f"{sym}{row['MONT EMIT']:,.2f}"
                                    m_saldo = f"{sym}{row['SALDO REAL']:,.2f}"
                                    
                                    # Detracción (Solo Soles)
                                    det_val = row.get('DETRACCIÓN', 0)
                                    det_fmt = f"S/ {det_val:,.2f}" if det_val > 0 else "-"
                                    
                                    table_rows += f"""
                                    <tr style="border-bottom: 1px solid #eee;">
                                        <td style="padding: 12px 8px; font-weight: 500;">{row['COMPROBANTE']}</td>
                                        <td style="padding: 12px 8px; color: #666;">{f_venc}</td>
                                        <td style="padding: 12px 8px; text-align: right;">{m_emit}</td>
                                        <td style="padding: 12px 8px; text-align: right; font-weight: bold; color: {p_col};">{m_saldo}</td>
                                        <td style="padding: 12px 8px; text-align: right; font-size: 0.9em; color: #888;">{det_fmt}</td>
                                    </tr>
                                    """

                                img_tag_html = ""
                                if logo_data_b64:
                                    img_tag_html = f'<div style="text-align:center; padding: 40px 0 30px 0; background: #fff;"><img src="data:image/png;base64,{logo_data_b64}" style="max-height: 160px; max-width: 80%; object-fit: contain;" alt="Logo"/></div>'
                                
                                # HTML FINAL (Estilo Documento Formal)
                                return f"""
                                <style>
                                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                                    .doc-container {{
                                        width: 900px;
                                        background: white;
                                        margin: 0 auto;
                                        font-family: 'Inter', sans-serif;
                                        padding: 0;
                                        border: 1px solid #eee;
                                        color: #1a1a1a;
                                    }}
                                    .doc-header {{
                                        text-align: center;
                                        border-bottom: 6px solid {p_col};
                                        padding-bottom: 20px;
                                    }}
                                    .doc-title {{
                                        font-size: 32px;
                                        font-weight: 700;
                                        text-transform: uppercase;
                                        letter-spacing: 2px;
                                        margin: 20px 0;
                                        color: #000;
                                    }}
                                    .doc-body {{ padding: 60px 70px; }}
                                    .greeting {{ font-size: 24px; font-weight: 600; margin-bottom: 25px; color: {p_col}; }}
                                    .intro {{ font-size: 19px; line-height: 1.6; margin-bottom: 40px; color: #333; }}
                                    .table-wrapper {{ width: 100%; margin-bottom: 40px; }}
                                    table {{ width: 100%; border-collapse: collapse; font-size: 18px; }}
                                    th {{ background: #f9f9f9; padding: 15px 8px; text-align: left; font-weight: 700; border-bottom: 3px solid {p_col}; color: #444; }}
                                    .totals-block {{ 
                                        background: #f4f8fb; 
                                        padding: 25px 35px; 
                                        border-radius: 8px; 
                                        text-align: right; 
                                        margin-top: 30px;
                                        border-left: 5px solid {s_col};
                                    }}
                                    .total-label {{ font-size: 18px; color: #666; font-weight: 500; }}
                                    .total-value {{ font-size: 24px; font-weight: 700; color: {s_col}; margin-left: 20px; }}
                                    .doc-footer {{ 
                                        background: #1a1a1a; 
                                        color: #999; 
                                        padding: 40px; 
                                        text-align: center; 
                                        font-size: 15px;
                                        line-height: 1.5;
                                    }}
                                </style>
                                <div class="doc-container" id="card">
                                    <div class="doc-header">
                                        {img_tag_html}
                                        <div class="doc-title">Estado de Cuenta Oficial</div>
                                    </div>
                                    <div class="doc-body">
                                        <div class="greeting">Estimados {client_name},</div>
                                        <div class="intro">
                                            Le informamos que a la fecha presenta documentos pendientes de pago por un <b>Total de: {total_real_str}</b>.<br>
                                            Agradeceremos gestionar la cancelación a la brevedad posible.
                                        </div>
                                        
                                        <div class="table-wrapper">
                                            <table>
                                                <thead>
                                                    <tr>
                                                        <th>Documento</th>
                                                        <th>Venc.</th>
                                                        <th style="text-align: right;">Importe</th>
                                                        <th style="text-align: right;">Saldo</th>
                                                        <th style="text-align: right;">Detr.</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {table_rows}
                                                </tbody>
                                            </table>
                                        </div>

                                        <div class="totals-block">
                                            <span class="total-label">SALDO TOTAL PENDIENTE:</span>
                                            <span class="total-value">{total_real_str}</span>
                                        </div>
                                    </div>
                                    <div class="doc-footer">
                                        {CONFIG.get('company_name', 'DACTA S.A.C.')} | RUC: {CONFIG.get('company_ruc', '20375779448')}<br>
                                        Este es un documento formal generado automáticamente. Consultas: {CONFIG.get('phone_contact', '')}
                                    </div>
                                </div>
                                """

                            # Para el preview en pantalla, usamos una versión más compacta pero similar
                            def get_preview_html(msg):
                                import re
                                def _fmt(text):
                                    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                    t = re.sub(r'\*(.*?)\*', r'<b>\1</b>', t)
                                    return t.replace("\n", "<br>")
                                return f"""<div style='background:#fff; padding:20px; border-radius:8px; border:1px solid #ddd; font-family:sans-serif; font-size:14px;'>{_fmt(msg)}</div>"""

                            # GENERATE HTML PREVIEW (Usa Document Mode para consistencia visual)
                            # Pero en el expander de Streamlit mostramos solo el texto por velocidad
                            # y guardamos el HTML complejo para la generación de imagen
                            card_html = create_whatsapp_document_html(empresa, docs_cli, primary_col, secondary_col, logo_b64)
                            
                            contact_data['card_html'] = card_html
                            contact_data['image_path'] = None 

                            # --- RENDERIZADO INMEDIATO (User Preference) ---
                            st.markdown(get_preview_html(msg_preview), unsafe_allow_html=True)
                    

                
                # Separador eliminado por solicitud de UI limpia

                
                # BOTON NUEVO: ENVIAR WHATSAPP (Selenium)
                if st.button("Enviar Mensajes por WhatsApp", type="primary"):
                    # --- DEDUPLICACIÓN DE SEGURIDAD ---
                    # Aseguramos que no se envíen mensajes dobles si hubo duplicados en la lista UI
                    seen_keys = set()
                    unique_contacts = []
                    for c in contacts_to_send:
                        key = (c['nombre_cliente'], c['telefono'])
                        if key not in seen_keys:
                            seen_keys.add(key)
                            unique_contacts.append(c)
                    contacts_to_send = unique_contacts
                    # ----------------------------------

                    from utils.whatsapp_sender import send_whatsapp_messages_direct
                    import tempfile
                    import os
                    
                    status_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    
                    # UI: Tabla de Resultados en Vivo
                    st.markdown("##### 📊 Estado del Envío")
                    results_placeholder = st.empty()
                    
                    # UI: Log Oculto
                    with st.expander("🛠️ Ver Log Técnico (Solo para depuración)", expanded=False):
                        log_area = st.empty()

                    # Inicializar estado de resultados
                    session_results = []
                    for c in contacts_to_send:
                        session_results.append({
                            "Cliente": c['nombre_cliente'],
                            "Teléfono": c['telefono'],
                            "Estado": "⏳ Pendiente",
                            "Detalle": ""
                        })
                    
                    results_df = pd.DataFrame(session_results)
                    results_placeholder.dataframe(results_df, hide_index=True, use_container_width=True)

                    def progress_callback(current, total, status, log_text):
                        progress = current / total if total > 0 else 0
                        progress_bar.progress(progress)
                        status_placeholder.info(f"{status} ({current}/{total})")
                        log_area.code(log_text)
                        
                        # Actualizar tabla de resultados en vivo
                        # Identificamos el índice actual (current-1 es el que se acaba de procesar o se está procesando)
                        # Nota: La lógica de 'current' en el sender a veces es el inicio o el fin. 
                        # Ajustaremos según el mensaje de status.
                        
                        if "Enviando a" in status:
                            # Estamos procesando current
                            idx = current
                            if 0 <= idx < len(session_results):
                                session_results[idx]["Estado"] = "🔄 Enviando..."
                        
                        # Si hay logs de éxito/error, actualizar el anterior
                        last_lines = log_text.split('\n')[-3:] # Ver últimas líneas
                        full_log = log_text
                        
                        # Parsear log para actualizar estados finales (Naive approach pero funcional visualmente)
                        # Una mejor forma sería que el callback reciba el índice exacto y el resultado, 
                        # pero por ahora parseamos el log o usamos el índice.
                        
                        # Update visual
                        results_placeholder.dataframe(pd.DataFrame(session_results), hide_index=True, use_container_width=True)
                    
                    
                    # ========== NUEVO v5.0: ENVÍO UNIFICADO CON MULTI-MODO ==========
                    # La generación de imágenes y PDFs se maneja automáticamente en el backend
                    # según el modo seleccionado (send_mode_value)
                    
                    status_placeholder.info("⏳ Preparando envío...")
                    
                    try:
                        results = send_whatsapp_messages_direct(
                            contacts=contacts_to_send, 
                            message=template, 
                            speed="Normal (Recomendado)",
                            progress_callback=progress_callback,
                            send_mode=send_mode_value,  # NUEVO v5.0: Modo de envío
                            branding_config=CONFIG,      # NUEVO v5.0: Configuración de branding
                            logo_path=logo_path          # NUEVO v5.0: Ruta al logo
                        )
                        
                        # Actualización Final de la Tabla
                        final_data = []
                        for i, res in enumerate(results.get('resultados_detallados', [])): # Assuming new return format or map
                             # Fallback si no cambiamos el return del sender todavía
                             pass
                        
                        # Como no cambié el return de send_whatsapp_messages_direct para devolver lista detallada ordenada,
                        # reconstruyo basado en lo que tenemos o simplemente mostramos el resumen final.
                        # Para hacerlo bien, el sender debería devolver el estado de cada uno.
                        # Por ahora, marcaremos todos como completados si no hubo error fatal, o parseamos el log final.
                        
                        st.success("✅ Proceso Finalizado")
                        
                        # Mostrar resumen final limpio
                        col_res1, col_res2 = st.columns(2)
                        col_res1.metric("Exitosos", results['exitosos'])
                        col_res2.metric("Fallidos", results['fallidos'])
                        
                        if results['fallidos'] > 0:
                            st.error("Algunos mensajes fallaron. Revisa el log técnico.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        with st.expander("Ver detalles del error"):
                            st.code(traceback.format_exc())

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
                        
                        s_temp = docs_cli_temp[docs_cli_temp['MONEDA'].astype(str).str.startswith('S', na=False)]['SALDO REAL'].sum()
                        d_temp = docs_cli_temp[~docs_cli_temp['MONEDA'].astype(str).str.startswith('S', na=False)]['SALDO REAL'].sum()
                        
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
                    # Definir ruta de logo (Stable Scope for Preview)
                    # RC-BUG-LOGO: Prefer processed logo
                    assets_dir = os.path.join(os.getcwd(), "assets")
                    logo_path = os.path.join(assets_dir, "logo_dacta_processed.png")
                    
                    if not os.path.exists(logo_path):
                         # Fallback to legacy
                         legacy_path = os.path.join(assets_dir, "logo_dacta.png")
                         if os.path.exists(legacy_path):
                             logo_path = legacy_path
                         else:
                             logo_path = None
                    else:
                         # Ensure CONFIG has it
                         CONFIG['logo_path'] = logo_path
                    # Convertir imagen a base64 para el preview en iframe
                    
                    for selected_label in sel_emails:
                        info_sel = email_map[selected_label]
                        docs_cli_mail = df_filtered[df_filtered['COD CLIENTE'] == info_sel['cod']]
                        
                        mask_soles_prev = docs_cli_mail['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
                        totales_s = docs_cli_mail[mask_soles_prev]['SALDO REAL'].sum()
                        totales_d = docs_cli_mail[~mask_soles_prev]['SALDO REAL'].sum()
                        
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
                        preview_html_view = preview_html_cid
                        if logo_path:
                            try:
                                with open(logo_path, "rb") as image_file:
                                        encoded_string = base64.b64encode(image_file.read()).decode()
                                src_base64 = f"data:image/png;base64,{encoded_string}"
                                preview_html_view = preview_html_cid.replace("cid:logo_dacta", src_base64)
                            except:
                                pass # Fallback (mostrará alt text)
                        
                        with st.expander(f"✉️ {info_sel['empresa']}", expanded=False):
                            components.html(preview_html_view, height=600, scrolling=True)
                    
                    
                    # --- RC-BUG-006 & 010: Protección Avanzada contra Doble Envío ---
                    # Generar una firma única del lote actual
                    current_batch_hash = hash(tuple(sorted(sel_emails)))
                    current_batch_id = f"{len(sel_emails)}_{current_batch_hash}"
                    
                    if 'last_processed_batch_id' not in st.session_state:
                         st.session_state['last_processed_batch_id'] = None
                    
                    # 2. Bloqueo de UI si ya se procesó
                    is_processed = (st.session_state['last_processed_batch_id'] == current_batch_id)
                    
                    if is_processed:
                        st.info("ℹ️ Este lote ya fue procesado. Para enviar otro, cambie la selección o recargue (F5).")
                        if st.button("🔄 Resetear Bloqueo (Permitir reenvío)"):
                            st.session_state['last_processed_batch_id'] = None
                            st.rerun()


                    # --- RC-BUG-015: Explicit Resend Control ---
                    force_resend_ttl = st.checkbox("🔄 Habilitar reenvío (Ignorar bloqueo 10min)", help="Marca esto para reenviar intencionalmente una notificación reciente.")
                    
                    # Botón Main de Envío
                    if st.button("Enviar Correos Masivos", type="primary", disabled=is_processed):
                        if is_processed:
                             st.stop()
                        
                        st.write(f"👷 DEBUG: Iniciando envío... Hash: {current_batch_id} | ForceResend: {force_resend_ttl}")

                        # Credenciales ahora vienen de CONFIG global
                        smtp_cfg = CONFIG.get('smtp_config', {})
                        email_user = smtp_cfg.get('user', '')
                        email_pass = smtp_cfg.get('password', '')

                        if not email_user or not email_pass:
                             st.error("❌ Faltan credenciales SMTP. Configúralas en la pestaña 'Configuración'.")
                        else:
                            # --- Feedback Visual de Supervisión (RC-BUG-017) ---
                            sup_cfg_active = CONFIG.get('supervisor_config', {})
                            if sup_cfg_active.get('enabled', False):
                                sup_mode_act = sup_cfg_active.get('mode', 'BCC')
                                st.success(f"👮 Copia de Supervisión ACTIVADA ({sup_mode_act}): {sup_cfg_active.get('email')}")
                            
                            messages_to_send = []
                            # RC-BUG-007: Deduplicación explícita en el origen
                            seen_emails_batch = set()
                            
                            # RC-BUG-LOGO: Ensure logo_path is set correctly for the batch
                            # Prioritize processed logo
                            assets_dir = os.path.join(os.getcwd(), "assets")
                            batch_logo_path = os.path.join(assets_dir, "logo_dacta_processed.png")
                            
                            if os.path.exists(batch_logo_path):
                                CONFIG['logo_path'] = batch_logo_path
                            else:
                                # Fallback
                                legacy_path = os.path.join(assets_dir, "logo_dacta.png")
                                if os.path.exists(legacy_path):
                                    batch_logo_path = legacy_path
                                    CONFIG['logo_path'] = legacy_path
                                else:
                                    CONFIG['logo_path'] = None
                                    batch_logo_path = None
                            
                            for lbl in sel_emails:
                                info = email_map[lbl]
                                
                                # Normalizar email 
                                email_norm = str(info['email']).strip().lower()
                                
                                # RC-BUG-016: Permitir múltiple envío al mismo email si son clientes distintos
                                # (Ya no bloqueamos por email único en el batch)
                                # if email_norm in seen_emails_batch:
                                #     continue
                                # seen_emails_batch.add(email_norm)
                                
                                d_cli = df_filtered[df_filtered['COD CLIENTE'] == info['cod']]
                                
                                # --- RC-BUG-014: Business Key Calculation (Idempotency) ---
                                # 1. Document Fingerprint (Hash de documentos ordenados)
                                if 'MATCH_KEY' in d_cli.columns:
                                    doc_ids = sorted(d_cli['MATCH_KEY'].astype(str).unique())
                                    doc_str = "|".join(doc_ids)
                                else:
                                    # Fallback si no hay MATCH_KEY (usar COMPROBANTE o lo que haya)
                                    doc_ids = sorted(d_cli['COMPROBANTE'].astype(str).unique()) if 'COMPROBANTE' in d_cli.columns else []
                                    doc_str = "|".join(doc_ids)
                                
                                doc_set_fingerprint = hashlib.md5(doc_str.encode()).hexdigest()[:8]
                                
                                # 2. Notification Key Stable
                                # Key = Company | Email | Date | Type | DocSetHash
                                tipo_notificacion = "Email_EstadoCuenta"
                                notif_key = f"{CONFIG.get('company_name','Antay')}|{email_norm}|{fecha_corte}|{tipo_notificacion}|{doc_set_fingerprint}"
                                
                                # Refined Currency Logic (Robustness fix)
                                mask_soles = d_cli['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)

                                t_s = d_cli[mask_soles]['SALDO REAL'].sum()
                                t_d = d_cli[~mask_soles]['SALDO REAL'].sum()
                                
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
                                    'plain_body': plain_body,
                                    'html_body': body,
                                    'plain_body': plain_body,
                                    'notification_key': notif_key, # New Field
                                    'original_email': info['email'] # Traceability
                                })
                                
                                # --- RC-FEAT-012: QA Mode Injection ---
                                # Override destination and content if QA Enabled
                                qa_cfg = CONFIG.get('qa_config', {})
                                qa_recipients, qa_status, is_qa = qa_lib.resolve_recipients(info['email'], qa_cfg)
                                
                                if is_qa:
                                    # 1. Update Recipient
                                    # send_email_batch expects string (comma sep) or list. 
                                    # We use the list returned by resolve_recipients.
                                    messages_to_send[-1]['email'] = qa_recipients 
                                    
                                    # 2. Update Subject
                                    messages_to_send[-1]['subject'] = qa_lib.modify_subject_for_qa(subject_line)
                                    
                                    # 3. Update Body (Banner Injection)
                                    # Html: Prepend banner
                                    banner_html = qa_lib.get_qa_banner_html()
                                    messages_to_send[-1]['html_body'] = banner_html + body
                                    # Plain: Prepend text
                                    messages_to_send[-1]['plain_body'] = "[PRUEBA QA] " + plain_body
                                    
                                    # 4. Log Trace
                                    # We rely on 'original_email' field stored above for reporting
                            
                            # Enviar Batch con Logo
                            with st.spinner(f"Enviando con Business Lock (Fecha: {fecha_corte})..."):
                                results = es.send_email_batch(
                                    smtp_cfg, 
                                    messages_to_send, 
                                    progress_callback=lambda i, t, m: st.toast(f"{m} ({i}/{t})"),
                                    logo_path=batch_logo_path, # Use the verified batch path
                                    force_resend=force_resend_ttl, # RC-BUG-015
                                    supervisor_config=CONFIG.get('supervisor_config', None) # RC-FEAT-011
                                )
                            
                            # Marcar como enviado para prevenir duplicados
                            if results['success'] > 0:
                                 st.session_state['last_processed_batch_id'] = current_batch_id
                            
                            # --- RC-UX-002: Panel de Resultados Amigable ---
                            st.divider()
                            st.subheader("📊 Resumen del Proceso")
                            
                            # A) Resumen Ejecutivo (Métricas)
                            c1, c2, c3 = st.columns(3)
                            c1.metric("✅ Enviados", results['success'])
                            c2.metric("❌ Fallidos", results['failed'])
                            c3.metric("🔒 Bloqueados (TTL)", results.get('blocked', 0))
                            
                            # B) Tabla de Detalles (Negocio)
                            if 'details' in results and results['details']:
                                df_res = pd.DataFrame(results['details'])
                                
                                # Estilizar tabla simple
                                st.write("📝 **Detalle por Cliente:**")
                                st.dataframe(
                                    df_res[['Cliente', 'Email', 'Estado', 'Detalle']], 
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                # --- RC-FEAT-012: Traceability (Original vs Sent) ---
                                qa_cfg_active = CONFIG.get('qa_config', {})
                                if qa_cfg_active.get('enabled', False):
                                    st.info("ℹ️ Modo QA Activo: Los correos mostrados arriba son los de QA. Abajo el mapeo original.")
                                    # Rebuild mapping from messages_to_send
                                    # msg['client_name'] -> msg['original_email']
                                    orig_map = {m['client_name']: m['original_email'] for m in messages_to_send}
                                    
                                    # Add column to DF view
                                    df_res['Email Original'] = df_res['Cliente'].map(orig_map)
                                    st.dataframe(
                                        df_res[['Cliente', 'Email Original', 'Email', 'Estado']],
                                        use_container_width=True,
                                        hide_index=True
                                    )
                                
                                # Botón descarga
                                csv = df_res.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    "📄 Descargar Reporte de Envío (CSV)",
                                    data=csv,
                                    file_name=f"reporte_envio_{current_batch_id[:8]}.csv",
                                    mime="text/csv"
                                )
                            
                            # C) Log Técnico (Oculto)
                            with st.expander("🛠️ Avanzado (QA / Soporte Técnico)", expanded=False):
                                st.write(f"RunID: {current_batch_id}")
                                for l in results['log']:
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

        # --- SECCION INDEPENDIENTE: SUPERVISION (RC-BUG-017 & UX Feedback) ---
        st.markdown("---")
        st.subheader("🛠️ Supervisión de Cobranza")
        st.info("Configuración de copia de auditoría. Estos cambios se aplican inmediatamente.")
        
        # Cargar config actual
        curr_sup_cfg = CONFIG.get('supervisor_config', sm.DEFAULT_SETTINGS['supervisor_config'])
        
        # 1. Main Toggle (Control Principal)
        sup_enabled_ui = st.toggle("✅ Activar Copia a Supervisión", value=curr_sup_cfg.get('enabled', True))
        
        # 2. Options (Disabled if Main Toggle is OFF)
        c_sup1, c_sup2 = st.columns([2, 2])
        
        with c_sup1:
            sup_email_ui = st.text_input(
                "Email Supervisor", 
                value=curr_sup_cfg.get('email', ''), 
                help="Este correo recibirá copia de TODOS los envíos.",
                disabled=not sup_enabled_ui
            )
            
        with c_sup2:
            # Mapping Logic for Verbose UI
            mode_map = {
                "BCC": "Copia oculta (BCC) – Recomendado",
                "CC": "Copia visible (CC)"
            }
            rev_mode_map = {v: k for k, v in mode_map.items()}
            
            # Determine current value for UI
            curr_mode_code = curr_sup_cfg.get('mode', 'BCC')
            curr_mode_ui = mode_map.get(curr_mode_code, mode_map["BCC"])
            
            selected_mode_ui = st.selectbox(
                "Modo de Envío", 
                options=list(mode_map.values()),
                index=list(mode_map.values()).index(curr_mode_ui),
                help="BCC: El cliente NO VE a la supervisión.\nCC: El cliente SÍ VE a la supervisión.",
                disabled=not sup_enabled_ui
            )
            # Resolve back to code
            sup_mode_ui = rev_mode_map[selected_mode_ui]
            
        if st.button("💾 Guardar Configuración de Supervisión"):
            # 1. Update Global Config Wrapper
            new_sup_settings = {
                "email": sup_email_ui,
                "enabled": sup_enabled_ui,
                "mode": sup_mode_ui
            }
            CONFIG['supervisor_config'] = new_sup_settings
            
            # 2. Persist to Disk
            if sm.save_settings(CONFIG):
                status_msg = f"Copia {'ACTIVADA' if sup_enabled_ui else 'DESACTIVADA'}"
                if sup_enabled_ui:
                    status_msg += f" ({sup_mode_ui}) a {sup_email_ui}"
                
                st.success(f"✅ Guardado: {status_msg}")
                st.toast("Configuración de supervisión actualizada", icon="👮")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Error guardando config.json")
                
        # --- RC-FEAT-012: MARCHA BLANCA (QA) MODE ---
        st.markdown("---")
        st.subheader("🧪 Modo Marcha Blanca (QA)")
        st.warning("⚠️ Zona de Seguridad: Configura el entorno de pruebas para envíos seguros.")
        
        qa_cfg_defaults = CONFIG.get('qa_config', {
            'enabled': False,
            'mode': 'ALL', # ALL | PRIMARY
            'recipients': ['cortega@antayperu.com', 'acamacho@integrens.com'],
            'allowlist_domains': []
        })
        
        # UI Components
        qa_enabled = st.toggle("🚨 Activar Modo Marcha Blanca (QA)", value=qa_cfg_defaults.get('enabled', False))
        
        c_qa1, c_qa2 = st.columns(2)
        with c_qa1:
            qa_recipients_txt = st.text_area(
                "Destinatarios QA (Separados por coma o línea)",
                value=",\n".join(qa_cfg_defaults.get('recipients', [])),
                height=100,
                disabled=not qa_enabled,
                help="Todos los correos del sistema se redirigirán a esta lista."
            )
        
        with c_qa2:
            st.write("Estrategia de Envío QA:")
            qa_mode_sel = st.radio(
                "Comportamiento",
                options=["ALL", "PRIMARY"],
                format_func=lambda x: "Enviar a TODOS los QA (Recomendado)" if x == "ALL" else "Enviar solo al PRIMERO (Rápido)",
                index=0 if qa_cfg_defaults.get('mode', 'ALL') == 'ALL' else 1,
                disabled=not qa_enabled
            )
            
        if st.button("💾 Guardar Configuración QA", type="primary"):
            # Parse List
            raw_qa_list = [x.strip() for x in qa_recipients_txt.replace('\n', ',').split(',') if x.strip()]
            
            new_qa_config = {
                'enabled': qa_enabled,
                'mode': qa_mode_sel,
                'recipients': raw_qa_list,
                'allowlist_domains': [] # Future proof
            }
            
            CONFIG['qa_config'] = new_qa_config
            if sm.save_settings(CONFIG):
                st.success(f"✅ Modo QA {'ACTIVADO' if qa_enabled else 'DESACTIVADO'}. Lista: {len(raw_qa_list)} destinatarios.")
                if qa_enabled:
                    st.toast("🚨 MODO QA ACTIVO: No saldrán correos a clientes.", icon="🧪")
                import time
                time.sleep(1)
                st.rerun()
        # -------------------------------------------------------

        st.markdown("---")
        st.subheader("Logo de la Empresa (Visuals Enterprise)")
        # --- RC-UX-LOGO-STD: Enterprise Staging Flow + Anti-Loop ---
        
        # 1. Initialization & State Management
        if 'logo_uploader_key' not in st.session_state:
            st.session_state.logo_uploader_key = 0
            
        if 'logo_staged' not in st.session_state:
            st.session_state.logo_staged = None # {bytes, w, h, name}

        # 2. Display Active Logo (Current State)
        current_logo_path = CONFIG.get('logo_path')
        logo_active_exists = False
        if current_logo_path and os.path.exists(current_logo_path):
            logo_active_exists = True
            
        st.markdown("##### Logo Activo (En Producción)")
        if logo_active_exists and st.session_state.logo_staged is None:
            # Show Active only if not staging (or show both? User wants "Vista previa final" on upload)
            # Strategy: Show Active. If Staged exists, show Staged below in "Review" section.
            
            c_active_img, c_active_info = st.columns([1, 2])
            with c_active_img:
                st.image(current_logo_path, width=200)
            with c_active_info:
                st.success("✅ Logo configurado y visible en correos.")
                if st.button("🗑️ Eliminar Logo Actual", type="secondary", key="btn_del_logo"):
                    # IMMEDIATE ACTION requested by user (Clean config + files)
                    CONFIG['logo_path'] = None
                    try:
                        if os.path.exists(current_logo_path):
                            os.remove(current_logo_path)
                    except:
                        pass
                    sm.save_settings(CONFIG)
                    st.rerun()
        elif not logo_active_exists and st.session_state.logo_staged is None:
             st.info("ℹ️ No hay logo configurado. El correo saldrá SIN logo.")

        
        st.markdown("---")
        st.markdown("##### Cargar Nuevo Logo (Staging Area)")
        
        # 3. Uploader (Staging Trigger)
        # Using dynamic key to reset uploader after Save/Cancel
        uploaded_logo = st.file_uploader(
            "Seleccionar archivo (PNG/JPG)", 
            type=['png', 'jpg', 'jpeg'],
            key=f"uploader_logo_{st.session_state.logo_uploader_key}"
        )
        
        # Recomendaciones (Collapsed)
        with st.expander("ℹ️ Recomendaciones Técnicas"):
            st.markdown("""
            *   **Formato**: PNG (transparente) o JPG.
            *   **Dimensiones**: > 800px ancho.
            *   **Proceso**: Se aplica corte de bordes (trim) y redimensionado (resize) automático.
            """)

        # 4. Processing Logic (Run once per file)
        if uploaded_logo:
             import hashlib
             # Hash check to avoid loop/re-processing
             raw_bytes = uploaded_logo.getbuffer()
             file_hash = hashlib.md5(raw_bytes).hexdigest()
             
             # If new file or different from last staged
             last_hash = st.session_state.get('logo_last_hash')
             
             if last_hash != file_hash:
                 with st.spinner("Procesando logo (Trim + Resize)..."):
                     import io
                     from PIL import Image
                     
                     # Process
                     proc_bytes, proc_w, proc_h = img_proc.process_logo_image(raw_bytes)
                     
                     # Update Staging State
                     st.session_state.logo_staged = {
                         'bytes': proc_bytes,
                         'w': proc_w,
                         'h': proc_h, 
                         'name': uploaded_logo.name,
                         'orig_bytes': raw_bytes
                     }
                     st.session_state.logo_last_hash = file_hash

        # 5. Staging Review & Commit (Save)
        if st.session_state.logo_staged:
            st.divider()
            st.warning("⚠️ Tienes cambios pendientes (Logo en Staging). No se usarán hasta que guardes.")
            
            staged = st.session_state.logo_staged
            
            col_rev1, col_rev2 = st.columns(2)
            with col_rev1:
                st.caption("Previsualización Final")
                st.image(staged['bytes'], width=300)
                st.caption(f"Dim: {staged['w']}x{staged['h']} px | {len(staged['bytes'])//1024} KB")
            
            with col_rev2:
                st.caption("Acciones")
                
                # SAVE ACTION
                if st.button("💾 GUARDAR Y APLICAR", type="primary", use_container_width=True):
                    # Persist to Disk
                    assets_dir = os.path.join(os.getcwd(), "assets")
                    if not os.path.exists(assets_dir):
                        os.makedirs(assets_dir)
                    
                    # Save Original
                    fn_orig = f"logo_original_{staged['name']}"
                    with open(os.path.join(assets_dir, fn_orig), "wb") as f:
                        f.write(staged['orig_bytes'])
                        
                    # Save Processed (Canonical)
                    path_proc = os.path.join(assets_dir, "logo_dacta_processed.png")
                    with open(path_proc, "wb") as f:
                        f.write(staged['bytes'])
                    
                    # Update Config
                    CONFIG['logo_path'] = path_proc
                    sm.save_settings(CONFIG)
                    
                    # Clear Staging & Reset Uploader
                    st.session_state.logo_staged = None
                    st.session_state.logo_last_hash = None
                    st.session_state.logo_uploader_key += 1 # Forces uploader reset
                    
                    st.success("✅ Logo guardado correctamente.")
                    import time
                    time.sleep(1)
                    st.rerun()

                st.write("")
                # CANCEL ACTION
                if st.button("✖️ Cancelar / Descartar", use_container_width=True):
                    st.session_state.logo_staged = None
                    st.session_state.logo_last_hash = None
                    st.session_state.logo_uploader_key += 1 # Reset uploader
                    st.rerun()

else:
    # Mensaje de bienvenida inicial cuando no hay datos
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h3>Bienvenido</h3>
        <p>Por favor utiliza el menú lateral para cargar tus archivos de <strong>CtasxCobrar, Cobranza y Cartera</strong>.</p>
        <p style='color: gray; font-size: 0.9em;'>El sistema procesará automáticamente la información.</p>
    </div>
    """, unsafe_allow_html=True)
