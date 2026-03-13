import streamlit as st
import pandas as pd
import utils.settings_manager as sm
import utils.db_manager as dbm
import base64
import os
import streamlit.components.v1 as components
import utils.storage_manager as storage_mgr
from datetime import datetime, date

def render_tab(df_filtered, config):
    """
    Renders the WhatsApp Marketing/Notifications tab.
    
    Args:
        df_filtered (pd.DataFrame): The filtered dataframe containing client documents.
        config (dict): The application configuration dictionary.
    """
    st.subheader("Gestión de WhatsApp")

    # --- Panel de sesion WhatsApp (solo lectura; gestión en Configuración) ---
    from utils.whatsapp_sender import get_wa_session_info, _SELENIUM_OK as _WA_SELENIUM_OK
    _wa_info = get_wa_session_info()
    _wa_session_active = _wa_info.get("status") == "active"

    if _wa_session_active:
        _phone = _wa_info.get("phone", "")
        _name  = _wa_info.get("profile_name", "")
        _ts    = _wa_info.get("verified_at", "")
        _device_label = f"**{_name}**" if _name else "Dispositivo desconocido"
        _phone_label  = f"  ·  `{_phone}`" if _phone else ""
        st.success(
            f"Dispositivo activo: {_device_label}{_phone_label}  ·  verificado {_ts}"
        )
    else:
        st.warning(
            "Sin dispositivo conectado. Ve a **Configuración → WhatsApp** para vincular tu teléfono antes de enviar."
        )
    st.divider()

    # --- Panel post-envío persistente (igual que Email tab) ---
    if 'last_wa_send_results' in st.session_state and st.session_state['last_wa_send_results']:
        wa_res = st.session_state['last_wa_send_results']
        st.success("✅ Envío WhatsApp completado. Resultados del último proceso:")
        st.divider()
        st.subheader("📊 Resumen del Proceso WA")
        c_r1, c_r2 = st.columns(2)
        c_r1.metric("✅ Enviados", wa_res.get('exitosos', 0))
        c_r2.metric("❌ Fallidos", wa_res.get('fallidos', 0))
        if wa_res.get('details'):
            df_wa_res = pd.DataFrame(wa_res['details'])
            st.write("📝 **Detalle por Cliente:**")
            # Mostrar solo columnas visibles (ocultar CodCliente)
            cols_display = [c for c in df_wa_res.columns if c != 'CodCliente']
            st.dataframe(df_wa_res[cols_display], use_container_width=True, hide_index=True)
            csv_wa = df_wa_res[cols_display].to_csv(index=False).encode('utf-8')
            st.download_button(
                "📄 Descargar Reporte WA (CSV)",
                data=csv_wa,
                file_name=f"reporte_wa_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

        # --- RC-FEAT-019: Panel de Resultado por Cliente ---
        st.divider()
        st.subheader("🎯 Registrar Resultado de la Gestión")
        st.caption("Indica qué respondió cada cliente. Se guarda en Supabase para alimentar el Dashboard de Efectividad.")

        _OPCIONES_RESULTADO = [
            "⏳ Sin registrar",
            "✅ Acordó pagar",
            "🤝 Prometió pagar",
            "📵 Sin respuesta",
            "🔴 Escalar / Pre-Legal",
            "💬 Solicitó más plazo",
        ]
        _RESULTADO_MAP = {
            "✅ Acordó pagar": "EXITOSO",
            "🤝 Prometió pagar": "PENDIENTE",
            "📵 Sin respuesta": "SIN_RESPUESTA",
            "🔴 Escalar / Pre-Legal": "REPROGRAMADO",
            "💬 Solicitó más plazo": "PENDIENTE",
        }

        resultados_guardados: dict = wa_res.get('resultados_registrados', {})
        details = wa_res.get('details', [])
        cycle_id_lote = wa_res.get('cycle_id', st.session_state.get('cycle_id', ''))

        with st.form(key='form_resultados_wa'):
            selecciones = {}
            for i, det in enumerate(details):
                cod = det.get('CodCliente', '')
                ya_guardado = resultados_guardados.get(cod)
                col_a, col_b = st.columns([2, 2])
                with col_a:
                    st.markdown(f"**{det.get('Cliente', '')}**  "
                                f"<span style='color:#556B82;font-size:0.85em;'>Deuda: {det.get('Deuda','')}</span>",
                                unsafe_allow_html=True)
                with col_b:
                    if ya_guardado:
                        st.success(f"✅ Guardado: {ya_guardado}")
                        selecciones[cod] = None  # ya procesado
                    else:
                        selecciones[cod] = st.selectbox(
                            f"Resultado_{i}",
                            _OPCIONES_RESULTADO,
                            key=f"wa_res_{i}_{cod}",
                            label_visibility="collapsed",
                        )

            submitted = st.form_submit_button("💾 Guardar Resultados en Supabase", type="primary")
            if submitted:
                guardados = 0
                errores = 0
                for det in details:
                    cod = det.get('CodCliente', '')
                    if not cod:
                        continue
                    opcion = selecciones.get(cod)
                    if opcion is None or opcion == "⏳ Sin registrar":
                        continue
                    resultado_norm = _RESULTADO_MAP.get(opcion, "PENDIENTE")
                    ok, _ = dbm.insert_gestion(
                        cliente_id=cod,
                        tipo_gestion='WHATSAPP',
                        resultado=resultado_norm,
                        notas=f"Resultado post-envío WA: {opcion} | Deuda: {det.get('Deuda', '')}",
                        cycle_id=cycle_id_lote,
                        metadata_extra={
                            'source': 'panel_resultado_post_envio',
                            'opcion_gestor': opcion,
                        },
                    )
                    if ok:
                        resultados_guardados[cod] = opcion
                        guardados += 1
                    else:
                        errores += 1

                wa_res['resultados_registrados'] = resultados_guardados
                st.session_state['last_wa_send_results'] = wa_res
                if guardados:
                    st.success(f"✅ {guardados} resultado(s) guardado(s) en Supabase.")
                if errores:
                    st.warning(f"⚠️ {errores} resultado(s) no pudieron guardarse.")
                st.rerun()
        # --- Fin RC-FEAT-019 ---

        if st.button("✅ Cerrar Reporte WA"):
            del st.session_state['last_wa_send_results']
            st.rerun()
        st.divider()

    if not df_filtered.empty:
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown("##### Configurar Plantilla")
            
            # Cargar plantilla de CONFIG o usar default si no existe
            saved_template = config.get('whatsapp_template', (
                "Estimados *{EMPRESA}*,\n\n"
                "Adjuntamos el Estado de Cuenta actualizado. A la fecha, presentan documentos pendientes de pago:\n\n"
                "{RESUMEN_DEUDA}\n\n"
                "*Detalle de Documentos:*\n"
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
            
            st.caption("Variables: `{EMPRESA}`, `{RESUMEN_DEUDA}`, `{DETALLE_DOCS}`, `{TOTAL_SALDO_REAL}`, `{TOTAL_SALDO_ORIGINAL}`")

        with c2:
            st.markdown("##### Enviar Mensajes")
            
            # Selección de Clientes (Basado en lo filtrado)
            # Agrupar datos por cliente para la lista de selección
            # RC-FEAT-WA-FILTER: incluir clientes con detracción pendiente aunque saldo real sea 0
            # (mismo criterio que tab Email: SALDO REAL > 0.01 OR DETR_PENDIENTE > 0.01)
            df_wa_view = df_filtered.copy()
            df_wa_view['DETR_PENDIENTE_AMOUNT'] = df_wa_view.apply(
                lambda x: float(x['DETRACCIÓN']) if str(x['ESTADO DETRACCION']).upper().strip() == 'PENDIENTE' else 0.0,
                axis=1
            )
            client_group = df_wa_view.groupby(
                ['COD CLIENTE', 'EMPRESA', 'TELÉFONO']
            )[['SALDO REAL', 'DETR_PENDIENTE_AMOUNT']].sum().reset_index()
            client_group = client_group[
                (client_group['SALDO REAL'] > 0.01) |
                (client_group['DETR_PENDIENTE_AMOUNT'] > 0.01)
            ]

            # --- RC-FEAT-WA-UX: KPIs + "Ocultar ya enviados hoy" (estándar con Email tab) ---
            today_str_wa = date.today().strftime('%Y-%m-%d')
            df_ssot = st.session_state.get('df_final', pd.DataFrame())
            if not df_ssot.empty and 'ESTADO_WHATSAPP' in df_ssot.columns and 'FECHA_ULTIMO_WA' in df_ssot.columns:
                mask_wa_env = df_ssot['ESTADO_WHATSAPP'] == 'ENVIADO'
                mask_wa_hoy = df_ssot['FECHA_ULTIMO_WA'].astype(str).str.startswith(today_str_wa)
                clientes_wa_hoy_count = df_ssot[mask_wa_env & mask_wa_hoy]['COD CLIENTE'].nunique()
                cods_wa_env_hoy = df_ssot[mask_wa_env & mask_wa_hoy]['COD CLIENTE'].unique()
            else:
                clientes_wa_hoy_count = 0
                cods_wa_env_hoy = []

            c_wa_s1, c_wa_s2, c_wa_ctrl = st.columns([1, 1, 2])
            hide_wa_sent = c_wa_ctrl.toggle(
                "🙈 Ocultar ya enviados hoy", value=True,
                help="Oculta clientes que ya recibieron WhatsApp hoy."
            )
            if hide_wa_sent and len(cods_wa_env_hoy) > 0:
                client_group = client_group[~client_group['COD CLIENTE'].isin(cods_wa_env_hoy)]

            pendientes_wa = len(client_group)
            c_wa_s1.metric("⏳ Pendientes WA", pendientes_wa)
            c_wa_s2.metric("📱 Enviados Hoy WA", clientes_wa_hoy_count)
            st.markdown("---")

            # Crear lista de opciones formateada
            client_options = []
            client_map = {}
            for idx, row in client_group.iterrows():
                saldo = row['SALDO REAL']
                detr  = row.get('DETR_PENDIENTE_AMOUNT', 0.0)
                if saldo > 0.01 and detr > 0.01:
                    label = f"{row['EMPRESA']} (Deuda: S/ {saldo:,.2f} | Detr. pend.: S/ {detr:,.2f})"
                elif detr > 0.01:
                    label = f"{row['EMPRESA']} (Detr. pend.: S/ {detr:,.2f})"
                else:
                    label = f"{row['EMPRESA']} (Deuda: S/ {saldo:,.2f})"
                client_options.append(label)
                client_map[label] = row['COD CLIENTE']
            
            # Multiselect con session_state (igual que Email tab para consistencia)
            if "wa_sel_key" not in st.session_state:
                st.session_state["wa_sel_key"] = []
            # Limpiar selección si las opciones cambiaron (evita crash de Streamlit)
            valid_wa_opts = set(client_options)
            st.session_state["wa_sel_key"] = [x for x in st.session_state["wa_sel_key"] if x in valid_wa_opts]

            def select_all_wa_callback():
                st.session_state["wa_sel_key"] = client_options

            col_sel1, col_sel2 = st.columns([3, 1])
            selected_labels = col_sel1.multiselect(
                f"Seleccione Clientes a Notificar ({len(client_options)} disponibles):",
                options=client_options,
                key="wa_sel_key"
            )
            col_sel2.button("Seleccionar Todos", on_click=select_all_wa_callback)

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
                        venc_short = pd.to_datetime(doc['FECH VENC']).strftime('%d/%m/%Y')
                        
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

                    # RC-FEAT-019: Detracciones pendientes (igual que email_sender.py)
                    try:
                        mask_det_cli = (
                            (docs_cli['DETRACCIÓN'] > 0.01) &
                            (docs_cli['ESTADO DETRACCION'].astype(str).str.strip().str.upper() == 'PENDIENTE')
                        )
                        df_detr_cli = docs_cli[mask_det_cli]
                        sum_detr_cli = df_detr_cli['DETRACCIÓN'].sum()
                        count_detr_cli = len(df_detr_cli)
                    except Exception:
                        sum_detr_cli, count_detr_cli = 0.0, 0

                    # RC-FEAT-019: Bloque resumen igual al correo (3 líneas estándar)
                    kpi_s_wa = f"S/ {sum_s_cli:,.2f} ({count_s_cli:02d} documentos)" if (sum_s_cli > 0 or count_s_cli > 0) else "S/ 0.00 (00 documentos)"
                    kpi_d_wa = f"US$ {sum_d_cli:,.2f} ({count_d_cli:02d} documentos)" if (sum_d_cli > 0 or count_d_cli > 0) else "US$ 0.00 (00 documentos)"
                    kpi_sunat_wa = f"S/ {sum_detr_cli:,.2f} ({count_detr_cli:02d} documentos afectos)"
                    resumen_deuda_wa = (
                        f"• Deuda Total Soles: {kpi_s_wa}\n"
                        f"• Deuda Total Dólares: {kpi_d_wa}\n"
                        f"• Detracciones SUNAT Pendientes: {kpi_sunat_wa}"
                    )

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
                        'cod_cliente': cod_cli,  # Para referencia
                        'RESUMEN_DEUDA': resumen_deuda_wa,  # RC-FEAT-019
                    }
                    
                    msg_preview = template
                    msg_preview = msg_preview.replace("{EMPRESA}", str(empresa))
                    msg_preview = msg_preview.replace("{RESUMEN_DEUDA}", contact_data['RESUMEN_DEUDA'])
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
                

            
            # --- Batch lock (igual que Email tab) ---
            if contacts_to_send:
                current_wa_batch_id = f"{len(contacts_to_send)}_{hash(tuple(sorted(c['nombre_cliente'] for c in contacts_to_send)))}"
            else:
                current_wa_batch_id = None

            if 'last_wa_batch_id' not in st.session_state:
                st.session_state['last_wa_batch_id'] = None
            is_wa_processed = bool(current_wa_batch_id and st.session_state['last_wa_batch_id'] == current_wa_batch_id)

            if is_wa_processed:
                st.info("ℹ️ Este lote WA ya fue procesado. Cambia la selección o recarga (F5) para enviar otro.")
                if st.button("🔄 Resetear Bloqueo WA"):
                    st.session_state['last_wa_batch_id'] = None
                    st.rerun()

            # BOTON ENVIAR WHATSAPP
            if not _wa_session_active:
                st.warning("⚠️ Conecta un dispositivo en **Configuración → WhatsApp** para habilitar el envío.")
            if st.button("Enviar Mensajes por WhatsApp", type="primary",
                         disabled=is_wa_processed or not _wa_session_active):
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

                from utils.whatsapp_sender import send_whatsapp_messages_direct, _SELENIUM_OK
                if not _SELENIUM_OK:
                    st.error(
                        "**Selenium no está instalado** en este servidor. "
                        "Ejecuta `_install_deps.bat` en el servidor QA y reinicia la app."
                    )
                    st.code("pip install selenium webdriver-manager", language="bash")
                    st.stop()
                
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
                    
                    # --- RC-FEAT-018: Persistir envíos en gestiones (Supabase) ---
                    now_wa = datetime.now()
                    resultado_lote = 'EXITOSO' if results['exitosos'] > 0 else 'FALLIDO'
                    persisted_wa = 0
                    current_cycle_id = st.session_state.get('cycle_id', 'default_cycle')
                    for contact in contacts_to_send:
                        cod = str(contact.get('cod_cliente', '')).strip()
                        if not cod:
                            continue
                        ok, _ = dbm.insert_gestion(
                            cliente_id=cod,
                            tipo_gestion='WHATSAPP',
                            resultado=resultado_lote,
                            notas=f"WA masivo | {contact.get('TOTAL_SALDO_REAL', '')} | Tel: {contact.get('telefono', '')}",
                            fecha=now_wa.isoformat(),
                            cycle_id=current_cycle_id,
                            metadata_extra={},
                        )
                        if ok:
                            persisted_wa += 1

                    # Actualizar df_final en session_state con tracking WA
                    if 'df_final' in st.session_state and not st.session_state['df_final'].empty:
                        cods_enviados = {str(c.get('cod_cliente', '')).strip() for c in contacts_to_send}
                        wa_ts = now_wa.strftime('%Y-%m-%d %H:%M:%S')
                        mask_wa = st.session_state['df_final']['COD CLIENTE'].astype(str).str.strip().isin(cods_enviados)
                        if 'ESTADO_WHATSAPP' in st.session_state['df_final'].columns:
                            st.session_state['df_final'].loc[mask_wa, 'ESTADO_WHATSAPP'] = 'ENVIADO'
                        if 'FECHA_ULTIMO_WA' in st.session_state['df_final'].columns:
                            st.session_state['df_final'].loc[mask_wa, 'FECHA_ULTIMO_WA'] = wa_ts

                    # SSOT: Sincronizar estado_whatsapp en documentos_ciclo (Supabase)
                    if cods_enviados:
                        dbm.update_estado_whatsapp_in_cycle(
                            cycle_id=st.session_state.get('cycle_id'),
                            cliente_ids=list(cods_enviados),
                            fecha=wa_ts,
                        )

                    # --- RC-FEAT-WA-UX: Guardar resultados + rerun (igual que Email tab) ---
                    wa_details = []
                    for c in contacts_to_send:
                        wa_details.append({
                            'Cliente': c['nombre_cliente'],
                            'CodCliente': str(c.get('cod_cliente', '')).strip(),
                            'Teléfono': c['telefono'],
                            'Estado': '✅ Enviado' if resultado_lote == 'EXITOSO' else '❌ Fallido',
                            'Deuda': c.get('TOTAL_SALDO_REAL', ''),
                        })
                    st.session_state['last_wa_send_results'] = {
                        'exitosos': results['exitosos'],
                        'fallidos': results['fallidos'],
                        'details': wa_details,
                        'cycle_id': current_cycle_id,
                        'resultados_registrados': {},
                    }
                    if current_wa_batch_id:
                        st.session_state['last_wa_batch_id'] = current_wa_batch_id
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    with st.expander("Ver detalles del error"):
                        st.code(traceback.format_exc())

    else:
            st.info("No hay datos para mostrar notificaciones.")
