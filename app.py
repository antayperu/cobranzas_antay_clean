import streamlit as st
import pandas as pd
import urllib.parse
from datetime import date, datetime
from utils.processing import load_data, process_data
from utils.excel_export import generate_excel

# Configuración de Página
st.set_page_config(
    page_title="Reporte Cobranzas Antay",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS - Branding Antay (#2E86AB a #A23B72)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E86AB, #A23B72);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background-color: #2E86AB;
        color: white;
        border-radius: 5px;
        border: none;
        height: 3em;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #A23B72;
        color: white;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #2E86AB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Encabezado
st.markdown('<div class="main-header"><h1>📊 Reporte de Cobranzas y WhatsApp</h1></div>', unsafe_allow_html=True)

# Sidebar - Instrucciones
st.sidebar.title("📖 Cómo usar")
st.sidebar.info("""
1. **Sube los archivos**:
    - `CtasxCobrar.xlsx`
    - `Cobranza.xlsx`
    - `cartera_clientes.xlsx`
2. **Revisa la Tabla**:
    - Usa los filtros en la parte superior.
    - Verifica el cálculo de detracción.
3. **Exporta**:
    - Descarga el Excel consolidado.
4. **WhatsApp**:
    - Ve a la sección inferior.
    - Personaliza el mensaje.
    - Genera enlaces de cobro.
""")

st.sidebar.markdown("---")
st.sidebar.caption("Desarrollado para **Antay Perú**")

# --- PASO 1: CARGA DE ARCHIVOS ---
st.subheader("1. Carga de Archivos 📂")
col1, col2, col3 = st.columns(3)

file_ctas = col1.file_uploader("CtasxCobrar.xlsx", type=["xlsx"])
file_cobranza = col2.file_uploader("Cobranza.xlsx", type=["xlsx"])
file_cartera = col3.file_uploader("cartera_clientes.xlsx", type=["xlsx"])

# Inicializar Estado de Sesión
if 'data_ready' not in st.session_state:
    st.session_state['data_ready'] = False
if 'df_final' not in st.session_state:
    st.session_state['df_final'] = pd.DataFrame()

# Botón Global de Procesamiento
if file_ctas and file_cobranza and file_cartera:
    if st.button("🚀 Procesar Archivos", type="primary"):
        with st.spinner("Procesando y consolidando información..."):
            df_ctas_raw, df_cartera_raw, df_cobranza_raw, error = load_data(file_ctas, file_cartera, file_cobranza)
            
            if error:
                st.error(f"Error al cargar archivos: {error}")
                st.session_state['data_ready'] = False
            else:
                try:
                    df_final = process_data(df_ctas_raw, df_cartera_raw, df_cobranza_raw)
                    st.session_state['df_final'] = df_final
                    st.session_state['data_ready'] = True
                    st.success("✅ Procesamiento completado exitosamente.")
                except Exception as e:
                    st.error(f"Error en lógica de negocio: {str(e)}")
                    st.session_state['data_ready'] = False

# --- PASO 2: VISUALIZACIÓN Y FILTROS ---
if st.session_state['data_ready']:
    df_final = st.session_state['df_final']
    
    st.markdown("---")
    st.subheader("2. Reporte General 📋")
    
    # Filtros
    if not df_final.empty:
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        # Filtro Empresa
        empresas = ["Todos"] + sorted(df_final['EMPRESA'].astype(str).unique().tolist())
        sel_empresa = col_f1.selectbox("Filtrar por Empresa", empresas)
        
        # Filtro Estado Detraccion
        estados_dt = ["Todos"] + sorted(df_final['ESTADO DETRACCION'].astype(str).unique().tolist())
        sel_estado = col_f2.selectbox("Estado Detracción", estados_dt)
        
        # Filtro Moneda
        monedas = ["Todos"] + sorted(df_final['MONEDA'].astype(str).unique().tolist())
        sel_moneda = col_f3.selectbox("Moneda", monedas)
        
        # Buscador Global
        search_term = col_f4.text_input("🔍 Buscar (Cliente, Comp...)")
        
        # Aplicar filtros
        df_filtered = df_final.copy()
        
        if sel_empresa != "Todos":
            df_filtered = df_filtered[df_filtered['EMPRESA'].astype(str) == sel_empresa]
        if sel_estado != "Todos":
            df_filtered = df_filtered[df_filtered['ESTADO DETRACCION'].astype(str) == sel_estado]
        if sel_moneda != "Todos":
            df_filtered = df_filtered[df_filtered['MONEDA'].astype(str) == sel_moneda]
            
        if search_term:
            mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            df_filtered = df_filtered[mask]
        
        # --- FILTROS AVANZADOS ("Lo que ves es lo que es") ---
        with st.expander("🔍 Filtros Avanzados (Saldo Real)", expanded=False):
            c_fil1, c_fil2 = st.columns(2)
            with c_fil1:
                opcion_saldo = st.selectbox(
                    "Condición Saldo Real", 
                    ["Todos", "Mayor que", "Mayor o igual que", "Menor que", "Menor o igual que", "Igual a"],
                    index=0 # Default: Todos
                )
            with c_fil2:
                monto_ref = st.number_input("Monto Referencia", value=0.0, step=10.0)
            
            # Aplicar filtro
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
        
        # Métricas Resumen (KPIs Actualizados)
        m1, m2, m3, m4 = st.columns(4)
        total_saldo = df_filtered['SALDO'].sum()
        total_detra = df_filtered['DETRACCIÓN'].sum()
        total_real = df_filtered['SALDO REAL'].sum()
        count_docs = len(df_filtered)
        
        m1.metric("Total Saldo", f"S/ {total_saldo:,.2f}")
        m2.metric("Total Detracción", f"S/ {total_detra:,.2f}")
        m3.metric("Total Saldo Real", f"S/ {total_real:,.2f}")
        m4.metric("Documentos", f"{count_docs}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- FIX INDICE DINAMICO (Empieza en 1) ---
        df_display = df_filtered.copy()
        df_display.reset_index(drop=True, inplace=True)
        df_display.index = df_display.index + 1
        st.dataframe(df_display, use_container_width=True)
        
        # --- PASO 3: EXPORTAR ---
        st.subheader("3. Exportar Reporte 📥")
        excel_data = generate_excel(df_filtered)
        st.download_button(
            label="Descargar Excel Estilizado",
            data=excel_data,
            file_name=f"Reporte_Cobranzas_DACTA_SAC_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # --- PASO 4: MÓDULO WHATSAPP (NOTIFICACIONES) ---
        st.markdown("---")
        st.subheader("4. Notificaciones WhatsApp 📨")

        # 1. Selector de Clientes
        if not df_filtered.empty:
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.markdown("##### 📝 Configurar Plantilla")
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
                st.markdown("##### 🚀 Enviar Mensajes")
                
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
                    st.markdown("##### 👁️ Vista Previa")
                    
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
                            # Usamos :02d para que salga 03 en lugar de 3
                            total_parts.append(f"{symbol} {amount:,.2f} ({count:02d} documentos)")
                        
                        # Unir con " y "
                        if total_parts:
                            total_real_str = " y ".join(total_parts)
                        else:
                            total_real_str = "0.00"
                        
                        # No necesitamos variable separada para count string ya que está integrada
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
                            
                            # --- DISEÑO SMART (UX v3.2) ---
                            # Línea 1: 📄 *F201-3227* (Venc: 20/11)
                            # Línea 2: 💰 Imp: $206.50  »  Saldo: *$31.65*
                            # Línea 3 (Condicional): ⚠️ Detr: S/ 20.00 (Pendiente)
                            # ────────────────
                            
                            venc_short = pd.to_datetime(doc['FECH VENC']).strftime('%d/%m')
                            
                            # Línea 1
                            line1 = f"📄 *{comprobante}* (Venc: {venc_short})"
                            
                            # Línea 2
                            line2 = f"💰 Imp: {monto_emit}  »  Saldo: *{saldo_fmt}*"
                            
                            # Línea 3 (Solo si hay detracción)
                            line3 = ""
                            if det_val > 0:
                                # Icono de alerta si es pendiente
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
                        
                        # Generar mensaje final para preview
                        # Importamos funcion helper (o la replicamos simple aqui para visualizacion)
                        # Idealmente utils.whatsapp_sender.replace_variables pero para preview rápido usamos string replace básico
                        # Para consistencia exacta, usaremos la funcion del modulo si es posible, o duplicamos logica UI
                        
                        msg_preview = template
                        msg_preview = msg_preview.replace("{EMPRESA}", str(empresa))
                        msg_preview = msg_preview.replace("{DETALLE_DOCS}", txt_detalle)
                        msg_preview = msg_preview.replace("{TOTAL_SALDO_REAL}", contact_data['TOTAL_SALDO_REAL'])
                        msg_preview = msg_preview.replace("{TOTAL_SALDO_ORIGINAL}", contact_data['TOTAL_SALDO_ORIGINAL'])
                        
                        # Guardar el mensaje FINAL en el contacto para envio
                        contact_data['mensaje'] = msg_preview
                        contacts_to_send.append(contact_data)
                        
                        # Mostrar Preview
                        with st.expander(f"📨 {empresa} ({telefono})", expanded=False):
                            st.text_area("Mensaje", value=msg_preview, height=200, key=f"preview_{cod_cli}")

                # BOTON NUEVO: ENVIAR WHATSAPP (Selenium)
                if st.button("🚀 Enviar Mensajes por WhatsApp", type="primary"):
                    if not contacts_to_send:
                        st.warning("⚠️ No hay mensajes generados para enviar. Selecciona clientes.")
                    else:
                        import utils.whatsapp_sender as ws
                        
                        # Contenedores para UI dinámica
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        log_expander = st.expander("Ver Log de Envío", expanded=True)
                        log_area = log_expander.empty()

                        def update_progress(current, total, text, log_content):
                            if total > 0:
                                progress_bar.progress(min(current / total, 1.0))
                            status_text.markdown(f"**Procesando:** {text}")
                            log_area.code(log_content, language="text")

                        # Ejecutar envío
                        try:
                            # Pasamos contacts_to_send que YA TIENE la llave 'mensaje' con el texto procesado
                            # El script de envio volverá a intentar reemplazar variables si las encuentra, 
                            # pero como ya estan reemplazadas, no afectará. 
                            # Sin embargo, el script 'replace_variables' usa 'message' argument.
                            # Para evitar doble reemplazo o inconsistencias, pasamos el template.
                            # PERO: nuestra UI preview mostró YA el reemplazo. 
                            # EL script whatsapp_sender hace el reemplazo internamente.
                            # SOLUCION: Pasamos el 'template' original al script, y dejamos que el script haga el replace.
                            # OJO: La preview que mostramos debe coincidir. Coincide porque usamos la misma logica de replace arriba.
                            
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
        else:
             st.info("No hay datos para mostrar notificaciones.")
    else:
         st.info("Sube los archivos para ver el reporte.")
else:
    st.info("👆 Por favor sube los 3 archivos Excel para comenzar.")
