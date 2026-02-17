import streamlit as st
import pandas as pd
import utils.settings_manager as sm
import base64
import os
import streamlit.components.v1 as components
import utils.storage_manager as storage_mgr

def render_tab(df_filtered, config):
    """
    Renders the WhatsApp Marketing/Notifications tab.
    
    Args:
        df_filtered (pd.DataFrame): The filtered dataframe containing client documents.
        config (dict): The application configuration dictionary.
    """
    st.subheader("Gestión de WhatsApp")

    if not df_filtered.empty:
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown("##### Configurar Plantilla")
            
            # Cargar plantilla de CONFIG o usar default si no existe
            saved_template = config.get('whatsapp_template', (
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
                new_config = config.copy()
                new_config['whatsapp_template'] = template
                if sm.save_settings(new_config):
                    st.success("✅ Plantilla guardada correctamente.")
                    # Actualizamos CONFIG local para la sesión actual (modifies dictionary in place if passed by reference)
                    config['whatsapp_template'] = template
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
                logo_path = storage_mgr.resolve_logo_path(config)
                if not logo_path:
                    assets_dir = os.path.join(os.getcwd(), "assets")
                    fallback_candidates = [
                        os.path.join(assets_dir, "logo_dacta_processed.png"),
                        os.path.join(assets_dir, "logo_dacta.png"),
                    ]
                    for candidate in fallback_candidates:
                        if os.path.exists(candidate):
                            logo_path = candidate
                            break
                logo_b64 = ""
                if logo_path and os.path.exists(logo_path):
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
                        
                        # 1. Colors (logo_b64 ya está cargado en scope global)
                        primary_col = config.get('primary_color', '#007bff')
                        secondary_col = config.get('secondary_color', '#00d4ff')
                        
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
                                    {config.get('company_name', 'DACTA S.A.C.')} | RUC: {config.get('company_ruc', '20375779448')}<br>
                                    Este es un documento formal generado automáticamente. Consultas: {config.get('phone_contact', '')}
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
                    # last_lines = log_text.split('\n')[-3:] # Ver últimas líneas
                    # full_log = log_text
                    
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
                        branding_config=config,      # NUEVO v5.0: Configuración de branding
                        logo_path=logo_path          # NUEVO v5.0: Ruta al logo
                    )
                    
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
