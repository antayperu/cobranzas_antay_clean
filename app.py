import streamlit as st
import pandas as pd
import urllib.parse
from datetime import date
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

if file_ctas and file_cobranza and file_cartera:
    # Cargar y Procesar
    with st.spinner("Procesando archivos..."):
        df_ctas_raw, df_cartera_raw, df_cobranza_raw, error = load_data(file_ctas, file_cartera, file_cobranza)
        
        if error:
            st.error(f"Error al cargar archivos: {error}")
            st.stop()
            
        try:
            df_final = process_data(df_ctas_raw, df_cartera_raw, df_cobranza_raw)
            st.success("✅ Procesamiento completado exitosamente.")
        except Exception as e:
            st.error(f"Error en lógica de negocio: {str(e)}")
            st.stop()

    # --- PASO 2: VISUALIZACIÓN Y FILTROS ---
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
                    index=1 # Default: Mayor que
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
        st.dataframe(df_filtered, use_container_width=True)
        
        # --- PASO 3: EXPORTAR ---
        st.subheader("3. Exportar Reporte 📥")
        excel_data = generate_excel(df_filtered)
        st.download_button(
            label="Descargar Excel Estilizado",
            data=excel_data,
            file_name="Reporte_Cobranzas_Antay.xlsx",
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
                    "Hola *{EMPRESA}*,\n\n"
                    "Le saludamos de DACTA SAC. Le recordamos que tiene documentos pendientes por un *Total de: {TOTAL_SALDO_REAL}*.\n\n"
                    "Detalle:\n{DETALLE_DOCS}\n\n"
                    "Favor de gestionar el pago a la brevedad.\n\n"
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
                if st.button("🔄 Procesar y Generar Mensajes", type="primary"):
                    # Generar lista de mensajes
                    msgs_output = []
                    
                    for label in selected_labels:
                        cod_cli = client_map[label]
                        # Filtrar documentos de este cliente (Usando df_filtered para respetar el filtro global)
                        docs_cli = df_filtered[df_filtered['COD CLIENTE'] == cod_cli]
                        
                        if docs_cli.empty: continue

                        # Datos del cliente (tomar del primer registro del grupo)
                        empresa = docs_cli['EMPRESA'].iloc[0]
                        telefono = docs_cli['TELÉFONO'].iloc[0]
                        
                        # --- CÁLCULO DE TOTALES POR MONEDA ---
                        # Agrupar saldos reales por moneda
                        sums_by_currency = docs_cli.groupby('MONEDA')['SALDO REAL'].sum()
                        
                        total_parts = []
                        for curr, amount in sums_by_currency.items():
                            # Mostrar total incluso si es negativo o cero para consistencia
                            symbol = "S/" if str(curr).upper().startswith("S") else "$"
                            total_parts.append(f"{symbol} {amount:,.2f}")
                                
                        if total_parts:
                            total_real_str = " y ".join(total_parts)
                        else:
                            total_real_str = "0.00"
                            
                        # Total original (referencial)
                        total_orig_val = docs_cli['SALDO'].sum() 

                        # --- DETALLE DE DOCUMENTOS (UX MEJORADA v1.8 - TIPO TARJETA) ---
                        # Diseño Final:
                        # 📄 *F201-00003200*
                        # 📅 Emisión: 10/11/25 | Venc: 13/11/25
                        # ℹ️ Imp: S/ 2,478.00 | Detr: S/ 297.36 (Pendiente)
                        # 📉 Saldo: *S/ -0.36*
                        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        docs_lines = []
                        for _, doc in docs_cli.iterrows():
                            saldo_doc_real = doc['SALDO REAL']
                            
                            # Preparar valores
                            comprobante = doc['COMPROBANTE']
                            emis = pd.to_datetime(doc['FECH EMIS']).strftime('%d/%m/%Y')
                            venc = pd.to_datetime(doc['FECH VENC']).strftime('%d/%m/%Y')
                            
                            # Moneda Símbolo
                            mon_code = str(doc['MONEDA'])
                            mon_sym = "S/" if mon_code.upper().startswith("S") else "$"
                            
                            monto_emit = f"{mon_sym}{doc['MONT EMIT']:,.2f}"
                            saldo_fmt = f"{mon_sym}{saldo_doc_real:,.2f}"
                            
                            # Detracción info
                            det_val = doc['DETRACCIÓN']
                            det_estado = doc['ESTADO DETRACCION']
                            
                            if det_estado == "Pendiente":
                                estado_str = "Pend"
                            elif det_estado in ["-", "No Aplica"]:
                                estado_str = "-"
                            else:
                                estado_str = "Aplic" 
                            
                            det_info = ""
                            if det_val > 0:
                                det_info = f" | Detr: S/{det_val:,.2f} ({estado_str})"
                            
                            # Construir Bloque
                            block = (
                                f"📄 *{comprobante}*\n"
                                f"📅 Emis: {emis} | Venc: {venc}\n"
                                f"ℹ️ Imp: {monto_emit}{det_info}\n"
                                f"📉 Saldo: *{saldo_fmt}*\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                            )
                            docs_lines.append(block)
                        
                        txt_detalle = "\n".join(docs_lines)
                        
                        # Reemplazo variables
                        msg = template.replace("{EMPRESA}", str(empresa))
                        msg = msg.replace("{DETALLE_DOCS}", txt_detalle)
                        msg = msg.replace("{TOTAL_SALDO_REAL}", total_real_str)
                        msg = msg.replace("{TOTAL_SALDO_ORIGINAL}", f"{total_orig_val:,.2f}") # Referencial
                        
                        # Link
                        link_wa = None
                        if telefono and len(telefono) > 8:
                            msg_enc = urllib.parse.quote(msg)
                            link_wa = f"https://wa.me/{telefono.replace('+', '')}?text={msg_enc}"
                        
                        msgs_output.append({
                            "Cliente": empresa,
                            "Link": link_wa,
                            "Mensaje": msg
                        })
                    
                    # Mostrar resultados si hay
                    if msgs_output:
                        for item in msgs_output:
                            with st.expander(f"📨 {item['Cliente']}", expanded=True):
                                st.text_area("Mensaje Generado", value=item['Mensaje'], height=250, key=f"txt_{item['Cliente']}")
                                if item['Link']:
                                    st.markdown(f'<a href="{item["Link"]}" target="_blank" style="background-color:#25D366;color:white;padding:10px;text-decoration:none;border-radius:5px;">📲 Enviar WhatsApp</a>', unsafe_allow_html=True)
                                else:
                                    st.warning("Número de teléfono no válido o faltante.")
                    else:
                        st.warning("No se generaron mensajes (revise la selección o filtros).")
        else:
             st.info("No hay datos para mostrar notificaciones.")
    else:
        st.info("Sube los archivos para ver el reporte.")

else:
    st.info("👆 Por favor sube los 3 archivos Excel para comenzar.")
