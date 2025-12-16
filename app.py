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
        
        # Métricas Resumen
        m1, m2, m3 = st.columns(3)
        total_saldo = df_filtered['SALDO'].sum()
        total_detra = df_filtered['DETRACCIÓN'].sum()
        count_docs = len(df_filtered)
        
        m1.markdown(f'<div class="metric-card"><h4>Total Saldo</h4><h3>S/ {total_saldo:,.2f}</h3></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><h4>Total Detracción</h4><h3>S/ {total_detra:,.2f}</h3></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><h4>Documentos</h4><h3>{count_docs}</h3></div>', unsafe_allow_html=True)
        
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
        st.markdown("##### 👥 Selección de Clientes")
        
        if not df_filtered.empty:
            # Agrupar datos por cliente para la lista de selección
            # Calculamos el Total Saldo Real por cliente
            client_group = df_filtered.groupby(['COD CLIENTE', 'EMPRESA', 'TELÉFONO'])['SALDO REAL'].sum().reset_index()
            # Filtrar solo clientes con deuda positiva (opcional, pero lógico para cobrar)
            client_group = client_group[client_group['SALDO REAL'] > 0]
            
            # Crear lista de opciones formateada
            # Opción: "EMPRESA (S/ X,XXX.XX)"
            
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
            
            # 2. Configurar Mensaje (Visible si hay seleccionados)
            if selected_labels:
                st.markdown("---")
                c1, c2 = st.columns([1, 1])
                
                with c1:
                    st.markdown("##### 📝 Configurar Plantilla")
                    default_template = (
                        "Hola *{EMPRESA}*,\n\n"
                        "Le saludamos de DACTA SAC. Le recordamos que tiene documentos pendientes por un *Total de: {TOTAL_SALDO_REAL}*.\n\n"
                        "Detalle:\n{DETALLE_DOCS}\n\n"
                        "Favor de gestionar el pago a la brevedad."
                    )
                    template = st.text_area("Plantilla del Mensaje", value=default_template, height=300)
                    st.caption("Variables: `{EMPRESA}`, `{DETALLE_DOCS}`, `{TOTAL_SALDO_REAL}`, `{TOTAL_SALDO_ORIGINAL}`")

                with c2:
                    st.markdown("##### 🚀 Enviar Mensajes")
                    st.info(f"Se generarán enlaces para **{len(selected_labels)}** clientes seleccionados.")
                    
                    # Generar lista de mensajes
                    msgs_output = []
                    
                    for label in selected_labels:
                        cod_cli = client_map[label]
                        # Filtrar documentos de este cliente
                        docs_cli = df_filtered[df_filtered['COD CLIENTE'] == cod_cli]
                        
                        if docs_cli.empty: continue

                        # Datos del cliente (tomar del primer registro del grupo)
                        empresa = docs_cli['EMPRESA'].iloc[0]
                        telefono = docs_cli['TELÉFONO'].iloc[0]
                        
                        # --- CÁLCULO DE TOTALES POR MONEDA ---
                        # Agrupar saldos reales por moneda
                        # Asumimos que la columna MONEDA tiene valores tipo 'SOL', 'US$', etc.
                        sums_by_currency = docs_cli.groupby('MONEDA')['SALDO REAL'].sum()
                        
                        total_parts = []
                        for curr, amount in sums_by_currency.items():
                            if amount > 0:
                                symbol = "S/" if str(curr).upper().startswith("S") else "$"
                                total_parts.append(f"{symbol} {amount:,.2f}")
                                
                        if total_parts:
                            total_real_str = " y ".join(total_parts)
                        else:
                            total_real_str = "0.00"
                            
                        # Total original (referencial)
                        total_orig_val = docs_cli['SALDO'].sum() 
                        # Nota: Sumar saldo original mezclando monedas no es correcto semanticamente, 
                        # pero por simplicidad de la variable legacy se deja o se ajusta igual.
                        # Para este caso, solo usaremos el Real que es el importante.

                        # --- DETALLE DE DOCUMENTOS ---
                        # Formato deseado:
                        # • [COMPROBANTE] | Venc: [FECHA] | Importe: [MON][MONTO] | Detrac: S/[VAL] ([ESTADO]) | Saldo: [MON][SALDO_REAL]
                        docs_lines = []
                        for _, doc in docs_cli.iterrows():
                            saldo_doc_real = doc['SALDO REAL']
                            
                            # Solo listar si hay deuda o si es relevante
                            if saldo_doc_real > 0:
                                # Preparar valores
                                comprobante = doc['COMPROBANTE']
                                venc = pd.to_datetime(doc['FECH VENC']).strftime('%d/%m/%Y')
                                
                                # Moneda Símbolo
                                mon_code = str(doc['MONEDA'])
                                mon_sym = "S/" if mon_code.upper().startswith("S") else "$"
                                
                                importe = f"{mon_sym}{doc['MONT EMIT']:,.2f}"
                                saldo_fmt = f"{mon_sym}{saldo_doc_real:,.2f}"
                                
                                # Detracción info
                                det_val = doc['DETRACCIÓN']
                                det_estado = doc['ESTADO DETRACCION']
                                
                                # Formatear estado corto para que entre en linea
                                estado_corto = "Pend" if det_estado == "Pendiente" else "Pag"
                                if det_estado in ["-", "No Aplica"]: estado_corto = "-"
                                
                                if det_val > 0:
                                    det_str = f"Det: S/{det_val:,.2f} ({estado_corto})"
                                else:
                                    det_str = ""
                                
                                # Construir línea
                                # Usar pipes | para separar como columnas
                                components = [
                                    f"• {comprobante}",
                                    f"Venc: {venc}",
                                    f"Imp: {importe}",
                                    f"{det_str}",
                                    f"Saldo: *{saldo_fmt}*"
                                ]
                                # Filtrar vacios (ej. sin detraccion)
                                line = " | ".join([c for c in components if c])
                                docs_lines.append(line)
                        
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
                    
                    # Mostrar links generados
                    for item in msgs_output:
                        with st.expander(f"📨 {item['Cliente']}"):
                            st.text(item['Mensaje'])
                            if item['Link']:
                                st.markdown(f'<a href="{item["Link"]}" target="_blank" style="background-color:#25D366;color:white;padding:10px;text-decoration:none;border-radius:5px;">📲 Enviar WhatsApp</a>', unsafe_allow_html=True)
                            else:
                                st.error("Sin número de teléfono válido.")
            else:
                st.warning("Seleccione al menos un cliente para generar mensajes.")
                
        else:
             st.info("No hay datos para mostrar notificaciones.")
    else:
        st.info("Sube los archivos para ver el reporte.")

else:
    st.info("👆 Por favor sube los 3 archivos Excel para comenzar.")
