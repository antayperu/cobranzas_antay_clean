import streamlit as st
import pandas as pd
import utils.settings_manager as sm
import utils.db_manager as dbm
import base64
import os
import streamlit.components.v1 as components
import utils.storage_manager as storage_mgr
from datetime import datetime, date

# RC-FEAT-020: Biblioteca de 7 Plantillas WA
WA_PLANTILLAS_BIBLIOTECA = {
    "📋 Cobranza Estándar": (
        "Estimados señores de *{EMPRESA}*,\n\n"
        "Por medio del presente, les informamos que su cuenta registra los siguientes servicios pendientes de pago:\n\n"
        "{RESUMEN_DEUDA}\n\n"
        "*Detalle de comprobantes:*\n"
        "{DETALLE_DOCS}\n\n"
        "Les solicitamos gestionar la cancelación a la brevedad para mantener la continuidad de los servicios contratados.\n\n"
        "Quedamos a su disposición para cualquier coordinación.\n\n"
        "DACTA S.A.C. | Gestión de Cobranzas | +51 998 080 797"
    ),
    "🔔 Primer Recordatorio": (
        "Estimados señores de *{EMPRESA}*,\n\n"
        "Les recordamos que su cuenta presenta comprobantes próximos a vencer o con vencimiento reciente:\n\n"
        "{RESUMEN_DEUDA}\n\n"
        "📅 Próximo vencimiento: *{PROX_VENC}*\n\n"
        "Les pedimos regularizar el pago en la fecha acordada para evitar cargos adicionales y asegurar la continuidad del servicio.\n\n"
        "Estamos disponibles para cualquier consulta.\n\n"
        "DACTA S.A.C. | Gestión de Cobranzas | +51 998 080 797"
    ),
    "⚠️ Segundo Recordatorio": (
        "Estimados señores de *{EMPRESA}*,\n\n"
        "A la fecha, su cuenta aún registra deuda pendiente de regularización pese a las comunicaciones previas:\n\n"
        "{RESUMEN_DEUDA}\n\n"
        "*Comprobantes vencidos:*\n"
        "{DETALLE_DOCS}\n\n"
        "Les solicitamos efectuar el pago a la brevedad o contactarnos para acordar una fecha de cancelación.\n\n"
        "La atención oportuna de esta obligación garantiza la continuidad de los servicios.\n\n"
        "DACTA S.A.C. | Gestión de Cobranzas | +51 998 080 797"
    ),
    "🔴 Urgente / Pre-Legal": (
        "Estimados señores de *{EMPRESA}*,\n\n"
        "⚠️ AVISO IMPORTANTE: Su cuenta registra una deuda vencida de *S/ {TOTAL_SALDO_REAL}* que no ha sido regularizada pese a los avisos previos.\n\n"
        "*Comprobantes pendientes:*\n"
        "{DETALLE_DOCS}\n\n"
        "De no efectuarse el pago ni establecerse un acuerdo formal dentro de las próximas 48 horas, el expediente será derivado al área legal para las acciones que correspondan.\n\n"
        "Para evitar este proceso, contáctenos de inmediato.\n\n"
        "DACTA S.A.C. | Gestión de Cobranzas | +51 998 080 797"
    ),
    "💰 Solo Total": (
        "Estimados señores de *{EMPRESA}*,\n\n"
        "Les informamos que su cuenta presenta un saldo pendiente de cancelación por *S/ {TOTAL_SALDO_REAL}*.\n\n"
        "Les solicitamos regularizar este importe a la brevedad posible.\n\n"
        "Para el detalle de comprobantes o coordinar el pago, pueden contactarnos directamente.\n\n"
        "DACTA S.A.C. | Gestión de Cobranzas | +51 998 080 797"
    ),
    "🤝 Confirmación de Acuerdo": (
        "Estimados señores de *{EMPRESA}*,\n\n"
        "Confirmamos el acuerdo de pago suscrito para regularizar su deuda de *S/ {TOTAL_SALDO_REAL}*.\n\n"
        "El cumplimiento puntual de las cuotas pactadas es indispensable para mantener vigente el acuerdo y evitar acciones adicionales de cobranza.\n\n"
        "Ante cualquier cambio en las condiciones acordadas, les pedimos comunicarse con anticipación.\n\n"
        "Agradecemos su disposición para regularizar esta obligación.\n\n"
        "DACTA S.A.C. | Gestión de Cobranzas | +51 998 080 797"
    ),
    "✅ Reconocimiento de Pago": (
        "Estimados señores de *{EMPRESA}*,\n\n"
        "Hemos registrado su pago reciente en nuestro sistema. Agradecemos su puntualidad.\n\n"
        "Si realizaron una transferencia pendiente de confirmación, pueden enviarnos el comprobante por este medio para su registro inmediato.\n\n"
        "Ante cualquier consulta sobre su estado de cuenta, estamos a su disposición.\n\n"
        "DACTA S.A.C. | Gestión de Cobranzas | +51 998 080 797"
    ),
}

_NOMBRE_PLANTILLA_PERSONALIZADA = "✏️ Personalizada (tu plantilla guardada)"


def render_tab(df_filtered, config):
    """
    Renders the WhatsApp Marketing/Notifications tab.
    
    Args:
        df_filtered (pd.DataFrame): The filtered dataframe containing client documents.
        config (dict): The application configuration dictionary.
    """
    st.subheader("Gestión de WhatsApp")

    # --- Banner de dispositivo WA (visible en ambos sub-tabs) ---
    from utils.whatsapp_sender import get_wa_session_info, _SELENIUM_OK as _WA_SELENIUM_OK
    _wa_info = get_wa_session_info()
    _wa_session_active = _wa_info.get("status") == "active"

    if _wa_session_active:
        _phone = _wa_info.get("phone", "")
        _name  = _wa_info.get("profile_name", "")
        _ts    = _wa_info.get("verified_at", "")
        _device_label = f"**{_name}**" if _name else "Dispositivo desconocido"
        _phone_label  = f"  ·  `{_phone}`" if _phone else ""
        st.success(f"Dispositivo activo: {_device_label}{_phone_label}  ·  verificado {_ts}")
    else:
        st.warning("Sin dispositivo conectado. Ve a **Configuración → WhatsApp** para vincular tu teléfono antes de enviar.")

    # ── Sub-tabs principales ──────────────────────────────────────────────────
    _hay_resultados = bool(
        st.session_state.get('last_wa_send_results')
    )
    _label_seguimiento = "📋 Seguimiento Post-Envío" + (" 🔴" if _hay_resultados else "")

    # Navegación persistente por ÍNDICE — inmune a cambios de label (el 🔴 cambia el string,
    # lo que rompía el match de string y reseteaba al tab 0 en cada rerun de widget)
    _subtab_opts = ["📤 Enviar Mensajes", _label_seguimiento]
    if 'wa_subtab_idx' not in st.session_state:
        st.session_state['wa_subtab_idx'] = 0
    _subtab_sel = st.radio(
        "subtab_wa", _subtab_opts,
        index=st.session_state['wa_subtab_idx'],
        horizontal=True, label_visibility="collapsed",
    )
    st.session_state['wa_subtab_idx'] = _subtab_opts.index(_subtab_sel)
    st.markdown("<hr style='margin:0 0 12px 0;border:none;border-top:2px solid #e2e8f0;'>", unsafe_allow_html=True)
    _en_envio       = (st.session_state['wa_subtab_idx'] == 0)
    _en_seguimiento = not _en_envio

    # ══════════════════════════════════════════════════════════════════════════
    # SUB-TAB 1 — ENVIAR MENSAJES
    # ══════════════════════════════════════════════════════════════════════════
    if _en_envio:
      # Resumen del último envío (persiste tras el rerun)
      _wa_res_env = st.session_state.get('last_wa_send_results')
      if _wa_res_env:
          _env_ok  = _wa_res_env.get('exitosos', 0)
          _env_fail = _wa_res_env.get('fallidos', 0)
          _env_tot  = _env_ok + _env_fail
          with st.expander(
              f"📊 Último envío — {_env_ok} enviados · {_env_fail} fallidos · {_env_tot} total  "
              f"*(clic para ver detalle)*",
              expanded=False
          ):
              _rk1, _rk2, _rk3 = st.columns(3)
              _rk1.metric("✅ Enviados", _env_ok)
              _rk2.metric("❌ Fallidos", _env_fail)
              _rk3.metric("📨 Total", _env_tot)
              if _wa_res_env.get('details'):
                  _df_res_env = pd.DataFrame(_wa_res_env['details'])
                  _cols_env = [c for c in _df_res_env.columns if c != 'CodCliente']
                  st.dataframe(_df_res_env[_cols_env], use_container_width=True, hide_index=True)
              st.info("Ve al sub-tab **📋 Seguimiento Post-Envío** para registrar el resultado de cada gestión.")
              if st.button("✅ Cerrar Resumen", key="btn_cerrar_resumen_envio"):
                  del st.session_state['last_wa_send_results']
                  st.rerun()
          st.divider()

      if not df_filtered.empty:
        c1, c2 = st.columns([55, 45])
        
        with c1:
            st.markdown("##### 📋 ¿A quién enviar?")

        with c2:
            st.markdown("##### ✉️ ¿Qué y cuándo enviar?")

            # ── Datos empresa + plantilla (computación, siempre disponible) ──────────────
            _empresa  = config.get('company_name', 'DACTA S.A.C.')
            _ruc      = config.get('company_ruc', '20375779448')
            _telefono_emp = config.get('phone_contact', '+51 998 080 797')

            def _aplicar_firma(texto):
                """Reemplaza datos hardcodeados por los de Identidad Corporativa."""
                return (texto
                    .replace("DACTA S.A.C.", _empresa)
                    .replace("RUC: 20375779448", f"RUC: {_ruc}")
                    .replace("+51 998 080 797", _telefono_emp))

            _biblioteca_dinamica = {
                nombre: _aplicar_firma(texto)
                for nombre, texto in WA_PLANTILLAS_BIBLIOTECA.items()
            }
            _default_saved = _aplicar_firma(
                config.get('whatsapp_template', list(_biblioteca_dinamica.values())[0])
            )
            if 'wa_template_editor' not in st.session_state:
                st.session_state['wa_template_editor'] = _default_saved

            _opciones_lib = [_NOMBRE_PLANTILLA_PERSONALIZADA] + list(_biblioteca_dinamica.keys())
            _sel_lib_actual = st.session_state.get('wa_sel_lib', _NOMBRE_PLANTILLA_PERSONALIZADA)
            _sel_lib_prev   = st.session_state.get('_wa_sel_lib_prev', _sel_lib_actual)
            if _sel_lib_actual != _sel_lib_prev:
                if _sel_lib_actual == _NOMBRE_PLANTILLA_PERSONALIZADA:
                    st.session_state['wa_template_editor'] = _default_saved
                elif _sel_lib_actual in _biblioteca_dinamica:
                    st.session_state['wa_template_editor'] = _biblioteca_dinamica[_sel_lib_actual]
            st.session_state['_wa_sel_lib_prev'] = _sel_lib_actual
            template = st.session_state.get('wa_template_editor', _default_saved)

            _sel_lib_label = _sel_lib_actual
            with st.expander(f"✏️ Plantilla · {_sel_lib_label}", expanded=False):
                st.selectbox(
                    "📚 Cargar desde biblioteca",
                    options=_opciones_lib,
                    key="wa_sel_lib",
                    help="Selecciona una plantilla para cargarla en el editor.",
                )
                template = st.text_area(
                    "Plantilla del Mensaje",
                    height=280,
                    key="wa_template_editor",
                )
                if st.button("💾 Guardar como Plantilla Predeterminada", type="primary", use_container_width=True):
                    new_config = config.copy()
                    new_config['whatsapp_template'] = template
                    if sm.save_settings(new_config):
                        config['whatsapp_template'] = template
                        st.toast("✅ Plantilla guardada. Persistirá al recargar la app.", icon="💾")
                    else:
                        st.error("❌ No se pudo guardar la plantilla.")
                st.caption("Variables: `{EMPRESA}`, `{RESUMEN_DEUDA}`, `{DETALLE_DOCS}`, `{TOTAL_SALDO_REAL}`, `{TOTAL_SALDO_ORIGINAL}`, `{PROX_VENC}`")

            # modo de envío fijado silenciosamente (texto plano estable)
            send_mode_value = "texto"

        # ── Bloque QUIÉN — dentro de c1 ───────────────────────────────────────────────
        with c1:
            # Selección de Clientes
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

            # KPIs + toggle
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
            if clientes_wa_hoy_count > 0 and not df_ssot.empty and 'FECHA_ULTIMO_WA' in df_ssot.columns:
                try:
                    _ultimas = pd.to_datetime(
                        df_ssot[mask_wa_env & mask_wa_hoy]['FECHA_ULTIMO_WA'], errors='coerce'
                    ).dropna()
                    if not _ultimas.empty:
                        _delta_h = (datetime.now() - _ultimas.max().to_pydatetime()).total_seconds() / 3600
                        _hace_str = f"{int(_delta_h)}h" if _delta_h >= 1 else f"{int(_delta_h*60)}min"
                        c_wa_s2.metric("📱 Enviados Hoy WA", clientes_wa_hoy_count, delta=f"hace {_hace_str}",
                                       delta_color="off")
                    else:
                        c_wa_s2.metric("📱 Enviados Hoy WA", clientes_wa_hoy_count)
                except Exception:
                    c_wa_s2.metric("📱 Enviados Hoy WA", clientes_wa_hoy_count)
            else:
                c_wa_s2.metric("📱 Enviados Hoy WA", clientes_wa_hoy_count)
            st.markdown("---")

            # Crear lista de opciones
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

            if "wa_sel_key" not in st.session_state:
                st.session_state["wa_sel_key"] = []
            valid_wa_opts = set(client_options)
            st.session_state["wa_sel_key"] = [x for x in st.session_state["wa_sel_key"] if x in valid_wa_opts]

            # Pre-selección por Reintentar
            _reintentar_cod = st.session_state.pop('wa_reintentar_cod', None)
            if _reintentar_cod:
                _match_lbl = next((lbl for lbl, cod in client_map.items() if cod == _reintentar_cod), None)
                if _match_lbl and _match_lbl in valid_wa_opts:
                    st.session_state["wa_sel_key"] = [_match_lbl]
                    st.info(f"📌 Cliente pre-seleccionado: **{_match_lbl.split(' (')[0]}**")

            # Banner sin-respuesta
            _last_res_data = st.session_state.get('last_wa_send_results', {})
            if _last_res_data:
                _last_rg = _last_res_data.get('resultados_registrados', {})
                _sin_resp_labels = []
                for _d_sr in _last_res_data.get('details', []):
                    _rk_sr = _d_sr.get('RowKey', _d_sr.get('CodCliente', ''))
                    _r_sr = _last_rg.get(_rk_sr, '')
                    for _p in ['✅ ', '🤝 ', '📵 ', '🔴 ', '💬 ', '⏳ ']:
                        if _r_sr.startswith(_p): _r_sr = _r_sr[len(_p):]; break
                    if _r_sr == 'Sin respuesta':
                        _lbl_sr = next((l for l, c in client_map.items() if c == _d_sr.get('CodCliente', '')), None)
                        if _lbl_sr and _lbl_sr in valid_wa_opts:
                            _sin_resp_labels.append(_lbl_sr)
                if _sin_resp_labels:
                    _ya_sel = set(st.session_state.get('wa_sel_key', []))
                    _nuevos_sr = [l for l in _sin_resp_labels if l not in _ya_sel]
                    if _nuevos_sr:
                        _bc1, _bc2 = st.columns([5, 1])
                        _bc1.info(f"↩ {len(_nuevos_sr)} cliente(s) sin respuesta del último lote disponibles para reenvío.")
                        if _bc2.button("↩ Seleccionar", key="sel_sin_resp_banner", use_container_width=True):
                            st.session_state['wa_sel_key'] = list(_ya_sel | set(_sin_resp_labels))
                            st.rerun()

            # Filtro rápido por segmento — selectbox compacto
            _aging_col = next((c for c in df_ssot.columns if 'AGING' in c.upper() or 'DIAS' in c.upper() or 'DÍAS' in c.upper()), None)
            _FILTRO_OPTS = [
                "— Todos —",
                "🔴 Mora crítica (+60d)",
                "⚫ Sin contacto WA",
                "↩ Sin respuesta último lote",
            ]
            _filtro_sel = st.selectbox(
                "Filtro rápido",
                options=_FILTRO_OPTS,
                index=0,
                key="wa_filtro_rapido",
                help="Aplica un preset de selección rápida sobre el multiselect",
            )
            if _filtro_sel != "— Todos —":
                _preset_cods: list = []
                if _filtro_sel == "🔴 Mora crítica (+60d)":
                    for _lbl_m, _cod_m in client_map.items():
                        if not df_ssot.empty and _aging_col:
                            _dias_mora = df_ssot[df_ssot['COD CLIENTE'] == _cod_m][_aging_col]
                            if not _dias_mora.empty and pd.to_numeric(_dias_mora, errors='coerce').max() > 60:
                                _preset_cods.append(_lbl_m)
                        else:
                            _row_m = client_group[client_group['COD CLIENTE'] == _cod_m]
                            if not _row_m.empty and _row_m['SALDO REAL'].values[0] >= 5000:
                                _preset_cods.append(_lbl_m)
                elif _filtro_sel == "⚫ Sin contacto WA":
                    for _lbl_sc, _cod_sc in client_map.items():
                        if not df_ssot.empty and 'ESTADO_WHATSAPP' in df_ssot.columns:
                            _est = df_ssot[df_ssot['COD CLIENTE'] == _cod_sc]['ESTADO_WHATSAPP']
                            if _est.empty or _est.iloc[0] in ('PENDIENTE', '', None):
                                _preset_cods.append(_lbl_sc)
                        else:
                            _preset_cods.append(_lbl_sc)
                elif _filtro_sel == "↩ Sin respuesta último lote":
                    _lr = st.session_state.get('last_wa_send_results', {})
                    if _lr:
                        _lrg = _lr.get('resultados_registrados', {})
                        for _d_c in _lr.get('details', []):
                            _rk_c = _d_c.get('RowKey', _d_c.get('CodCliente', ''))
                            _r_c = _lrg.get(_rk_c, '')
                            for _p in ['✅ ', '🤝 ', '📵 ', '🔴 ', '💬 ', '⏳ ']:
                                if _r_c.startswith(_p): _r_c = _r_c[len(_p):]; break
                            if _r_c == 'Sin respuesta':
                                _lbl_c = next((l for l, c in client_map.items() if c == _d_c.get('CodCliente', '')), None)
                                if _lbl_c and _lbl_c in valid_wa_opts:
                                    _preset_cods.append(_lbl_c)
                if _preset_cods and set(_preset_cods) != set(st.session_state.get('wa_sel_key', [])):
                    st.session_state['wa_sel_key'] = _preset_cods
                    st.session_state['wa_filtro_rapido'] = "— Todos —"
                    st.rerun()
                elif not _preset_cods:
                    st.toast("No hay clientes para ese filtro en la vista actual", icon="ℹ️")
                    st.session_state['wa_filtro_rapido'] = "— Todos —"

            def select_all_wa_callback():
                st.session_state["wa_sel_key"] = client_options

            col_sel1, col_sel2 = st.columns([3, 1])
            selected_labels = col_sel1.multiselect(
                f"Seleccione Clientes a Notificar ({len(client_options)} disponibles):",
                options=client_options,
                key="wa_sel_key"
            )
            col_sel2.button("Seleccionar Todos", on_click=select_all_wa_callback)

            # BOTON PROCESAR
            # --- LÓGICA DE GENERACIÓN DE MENSAJES (PREVIEW) ---
            contacts_to_send = []
            
            if selected_labels:
                _n_prev = len(selected_labels)
                st.markdown(f"##### 👁 Vista Previa · {_n_prev} cliente{'s' if _n_prev > 1 else ''}")
                
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

                    # RC-FEAT-020: {PROX_VENC} — fecha de vencimiento más próxima del cliente
                    try:
                        _fechas_venc = pd.to_datetime(docs_cli['FECH VENC'], errors='coerce').dropna()
                        _prox_venc = _fechas_venc.min().strftime('%d/%m/%Y') if not _fechas_venc.empty else "—"
                    except Exception:
                        _prox_venc = "—"

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
                        'PROX_VENC': _prox_venc,            # RC-FEAT-020: próximo vencimiento
                    }
                    
                    msg_preview = template
                    msg_preview = msg_preview.replace("{EMPRESA}", str(empresa))
                    msg_preview = msg_preview.replace("{RESUMEN_DEUDA}", contact_data['RESUMEN_DEUDA'])
                    msg_preview = msg_preview.replace("{DETALLE_DOCS}", txt_detalle)
                    msg_preview = msg_preview.replace("{TOTAL_SALDO_REAL}", contact_data['TOTAL_SALDO_REAL'])
                    msg_preview = msg_preview.replace("{TOTAL_SALDO_ORIGINAL}", contact_data['TOTAL_SALDO_ORIGINAL'])
                    msg_preview = msg_preview.replace("{PROX_VENC}", _prox_venc)
                    
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

            # BOTON ENVIAR — Mejora 2: label dinámico con conteo y estado
            if not _wa_session_active:
                st.warning("⚠️ Conecta un dispositivo en **Configuración → WhatsApp** para habilitar el envío.")
            _n_sel = len(contacts_to_send)
            _btn_label = (
                f"📤 Enviar a {_n_sel} cliente{'s' if _n_sel != 1 else ''}"
                if _n_sel > 0 else "📤 Selecciona clientes para enviar"
            )
            if st.button(_btn_label, type="primary", use_container_width=True,
                         disabled=is_wa_processed or not _wa_session_active or _n_sel == 0):
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
                        # Evidencia de auditoría: conservar en metadata el mensaje exacto enviado.
                        _meta_envio = {
                            'origen': 'wa_envio_masivo',
                            'template_label': st.session_state.get('wa_sel_lib', _sel_lib_actual),
                            'template_text': str(template or ''),
                            'mensaje_enviado': str(contact.get('mensaje', '') or ''),
                            'telefono_destino': str(contact.get('telefono', '') or ''),
                            'send_mode': str(send_mode_value or 'texto'),
                        }
                        if current_wa_batch_id:
                            _meta_envio['batch_id'] = current_wa_batch_id
                        ok, _ = dbm.insert_gestion(
                            cliente_id=cod,
                            tipo_gestion='WHATSAPP',
                            resultado=resultado_lote,
                            notas=f"WA masivo | {contact.get('TOTAL_SALDO_REAL', '')} | Tel: {contact.get('telefono', '')}",
                            fecha=now_wa.isoformat(),
                            cycle_id=current_cycle_id,
                            metadata_extra=_meta_envio,
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
                        _cod_c = str(c.get('cod_cliente', '')).strip()
                        wa_details.append({
                            'Cliente': c['nombre_cliente'],
                            'CodCliente': _cod_c,
                            'Teléfono': c['telefono'],
                            'Estado': '✅ Enviado' if resultado_lote == 'EXITOSO' else '❌ Fallido',
                            'Deuda': c.get('TOTAL_SALDO_REAL', ''),
                            'DeudaS': c.get('TOTAL_SALDO_S', ''),  # "S/ 623.00"
                            'DeudaD': c.get('TOTAL_SALDO_D', ''),  # "$ 373.94"
                            # RC-BUG-047: registrar hora/tipo/rowkey para que el cálculo
                            # "último envío" vs "última gestión" funcione en casos de reenvío.
                            'Hora': now_wa.strftime('%d/%m/%Y %H:%M'),
                            'HoraISO': now_wa.isoformat(),  # RC-BUG-051: timestamp para gestiones posteriores
                            'Tipo': 'Envío WA',
                            'RowKey': f"{_cod_c}_{now_wa.strftime('%Y%m%d%H%M%S')}_envio",
                            'Notas': f"WA masivo | {c.get('TOTAL_SALDO_REAL', '')} | Tel: {c.get('telefono', '')}",
                            'Mensaje': str(c.get('mensaje', '') or ''),
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
        st.info("No hay datos disponibles. Carga un archivo para enviar notificaciones.")

    # ══════════════════════════════════════════════════════════════════════════
    # SUB-TAB 2 — SEGUIMIENTO POST-ENVÍO
    # ══════════════════════════════════════════════════════════════════════════
    if _en_seguimiento:
        _cycle_id_actual = st.session_state.get('cycle_id', '')
        _wa_res_sesion   = st.session_state.get('last_wa_send_results')

        # Obtener datos del último envío en sesión para la tabla interactiva
        # RC-BUG-048: list() crea una COPIA local, no una referencia al objeto en session_state.
        # Sin esto, cada rerun iba acumulando filas de Supabase sobre el mismo objeto → duplicados.
        _details_sesion = list(_wa_res_sesion.get('details', [])) if _wa_res_sesion else []
        _cycle_id_lote  = _wa_res_sesion.get('cycle_id', _cycle_id_actual) if _wa_res_sesion else _cycle_id_actual

        if not _details_sesion and not _cycle_id_actual:
            st.info("📭 No hay ciclo activo ni envíos registrados. Carga un archivo y envía mensajes para ver el seguimiento.")
        else:
            # ── Leer Supabase — siempre, para incluir lotes anteriores del ciclo ──
            _gestiones_wa  = dbm.get_wa_gestiones_by_cycle(_cycle_id_actual) if _cycle_id_actual else []
            _df_gest       = pd.DataFrame(_gestiones_wa) if _gestiones_wa else pd.DataFrame()

            # ── Merge: añadir a _details_sesion los clientes del ciclo en Supabase
            # que no estén ya presentes (evita duplicados del lote actual en sesión).
            # Esto permite ver TODOS los lotes del mismo cycle_id sin recargar.
            _RESULTADO_DISPLAY_MAP = {
                'EXITOSO':      '✅ Acordó pagar',
                'PENDIENTE':    '🤝 Prometió pagar',
                'SIN_RESPUESTA':'📵 Sin respuesta',
                'REPROGRAMADO': '🔴 Derivar a Legal',
            }
            _resultados_supabase = {}
            if not _df_gest.empty:
                # CodClientes ya presentes en la sesión actual (lote recién enviado)
                _cids_sesion = {str(d.get('CodCliente', '')) for d in _details_sesion}
                _df_gest_sorted = _df_gest.copy()
                if 'created_at' in _df_gest_sorted.columns:
                    _df_gest_sorted['created_at'] = pd.to_datetime(_df_gest_sorted['created_at'], errors='coerce')
                    _df_gest_sorted = _df_gest_sorted.sort_values('created_at', ascending=True)
                for _idx, (_, _g) in enumerate(_df_gest_sorted.iterrows()):
                    _cid = str(_g.get('cliente_id', ''))
                    if not _cid:
                        continue
                    _meta_fb   = _g.get('metadata') or {}
                    _source_fb = _meta_fb.get('source', '') if isinstance(_meta_fb, dict) else ''
                    _tipo_fb   = 'Gestión' if _source_fb else 'Envío WA'
                    # Solo añadir filas de "Envío WA" si ese cliente no viene ya del lote de sesión.
                    # Recalcular _cids_sesion después de cada append para evitar duplicar el mismo
                    # cliente que aparezca en múltiples lotes históricos de Supabase.
                    if _tipo_fb == 'Envío WA' and _cid in _cids_sesion:
                        # El lote de sesión ya lo tiene — solo actualizamos resultados si hay gestión
                        pass
                    else:
                        _empresa, _tel, _saldo = _cid, '', ''
                        _deuda_s_fb, _deuda_d_fb = '', ''
                        if not df_filtered.empty and 'COD CLIENTE' in df_filtered.columns:
                            _filas = df_filtered[df_filtered['COD CLIENTE'].astype(str) == _cid]
                            if not _filas.empty:
                                _r = _filas.iloc[0]
                                _empresa = str(_r.get('EMPRESA', _cid))
                                _tel     = str(_r.get('TELÉFONO', ''))
                                _saldo   = str(_r.get('SALDO REAL', ''))
                                if 'MONEDA' in _filas.columns and 'SALDO REAL' in _filas.columns:
                                    _df_sol_fb = _filas[_filas['MONEDA'].astype(str).str.startswith('S', na=False)]
                                    _df_dol_fb = _filas[~_filas['MONEDA'].astype(str).str.startswith('S', na=False)]
                                    _sum_s_fb  = float(_df_sol_fb['SALDO REAL'].sum()) if len(_df_sol_fb) > 0 else 0.0
                                    _sum_d_fb  = float(_df_dol_fb['SALDO REAL'].sum()) if len(_df_dol_fb) > 0 else 0.0
                                    if _sum_s_fb > 0: _deuda_s_fb = f"S/ {_sum_s_fb:,.2f}"
                                    if _sum_d_fb > 0: _deuda_d_fb = f"$ {_sum_d_fb:,.2f}"
                        _fecha_hora_g = ''
                        try:
                            _fecha_hora_g = pd.to_datetime(_g.get('created_at', '')).strftime('%d/%m/%Y %H:%M')
                        except Exception:
                            pass
                        _notas_fb   = str(_g.get('notas', '') or '')
                        _msg_fb     = ''
                        # RC-BUG-049: metadata viene como STRING JSON desde Supabase, hay que parsear.
                        if isinstance(_meta_fb, str):
                            try:
                                import json as _json_parse
                                _meta_fb = _json_parse.loads(_meta_fb)
                            except Exception:
                                _meta_fb = {}
                        if isinstance(_meta_fb, dict):
                            _msg_fb = str(_meta_fb.get('mensaje_enviado', '') or '')
                        _row_key_fb = f"{_cid}_{_idx}"
                        _details_sesion.append({
                            'Cliente': _empresa, 'CodCliente': _cid,
                            'Teléfono': _tel, 'Deuda': _saldo, 'Hora': _fecha_hora_g,
                            'RowKey': _row_key_fb, 'Tipo': _tipo_fb, 'Notas': _notas_fb,
                            'DeudaS': _deuda_s_fb, 'DeudaD': _deuda_d_fb,
                            'Mensaje': _msg_fb,
                        })
                        _cids_sesion.add(_cid)  # evita duplicar cliente si aparece en otro lote histórico
                    # Gestiones manuales → marcar como ya guardadas
                    if _tipo_fb == 'Gestión':
                        _meta = _g.get('metadata') or {}
                        _opcion = _meta.get('opcion_gestor', '') if isinstance(_meta, dict) else ''
                        if not _opcion:
                            _opcion = _RESULTADO_DISPLAY_MAP.get(str(_g.get('resultado', '')), '')
                        if _opcion:
                            _rk_g = f"{_cid}_{_idx}"
                            _resultados_supabase[_rk_g] = _opcion
            # Sincronizar session_state
            if not _wa_res_sesion:
                _wa_res_sesion = {'details': _details_sesion, 'cycle_id': _cycle_id_actual,
                                  'resultados_registrados': _resultados_supabase}
                st.session_state['last_wa_send_results'] = _wa_res_sesion
            else:
                _wa_res_sesion['resultados_registrados'] = {
                    **_resultados_supabase,
                    **_wa_res_sesion.get('resultados_registrados', {}),
                }

            # ── KPIs coloreados ───────────────────────────────────────────────
            # "Enviados"        = registros de Envío WA (metadata sin source)
            # "Con gestión"     = registros manuales del cobrador (metadata con source)
            # "Pendientes"      = clientes enviados sin gestión manual aún
            # "Sin contacto"    = gestiones manuales con resultado SIN_RESPUESTA
            import json as _json
            def _es_envio_masivo_kpi(row):
                _m = row.get('metadata') or {}
                if isinstance(_m, str):
                    try: _m = _json.loads(_m)
                    except Exception: _m = {}
                return not bool(_m.get('source', ''))

            if not _df_gest.empty and 'resultado' in _df_gest.columns:
                _mask_envio    = _df_gest.apply(_es_envio_masivo_kpi, axis=1)
                _mask_gestion  = ~_mask_envio
                _cids_enviados = set(_df_gest[_mask_envio]['cliente_id'].astype(str))
                _cids_gestion  = set(_df_gest[_mask_gestion]['cliente_id'].astype(str))
                _total_env     = len(_cids_enviados)          # clientes únicos con envío WA
                _con_gestion   = len(_cids_gestion)           # clientes únicos con gestión registrada
                _pend_resp     = len(_cids_enviados - _cids_gestion)
                _sin_contacto  = int((_df_gest[_mask_gestion]['resultado'] == 'SIN_RESPUESTA').sum())
            else:
                _total_env    = len(_details_sesion)
                _con_gestion  = 0
                _pend_resp    = 0
                _sin_contacto = 0

            # Monto gestionado por moneda — un cliente puede tener varias filas (Envío WA + Gestión manual).
            # Contar cada CodCliente UNA SOLA VEZ para evitar doble conteo.
            import re as _re
            _monto_pen = 0.0
            _monto_usd = 0.0
            _cids_contados_monto: set = set()
            for _d in _details_sesion:
                _cid_monto = str(_d.get('CodCliente', ''))
                if _cid_monto and _cid_monto in _cids_contados_monto:
                    continue
                if _cid_monto:
                    _cids_contados_monto.add(_cid_monto)
                _deuda_s   = str(_d.get('DeudaS', ''))  # "S/ 623.00" o ""
                _deuda_d   = str(_d.get('DeudaD', ''))  # "$ 373.94" o ""
                if _deuda_s or _deuda_d:
                    # Campos explícitos — extracción directa, sin ambigüedad
                    if _deuda_s:
                        for _m in _re.finditer(r'S/\s*([\d,\.]+)', _deuda_s):
                            try: _monto_pen += float(_m.group(1).replace(',', ''))
                            except Exception: pass
                    if _deuda_d:
                        for _m in _re.finditer(r'\$\s*([\d,\.]+)', _deuda_d):
                            try: _monto_usd += float(_m.group(1).replace(',', ''))
                            except Exception: pass
                else:
                    # Fallback: Notas (si tiene prefijos S/ o $) o Deuda (número plano)
                    _notas_val = str(_d.get('Notas', ''))
                    _deuda_val = str(_d.get('Deuda', ''))
                    if _re.search(r'S/', _notas_val) or '$ ' in _notas_val:
                        _fuente = _notas_val
                    else:
                        _fuente = _deuda_val
                    for _m in _re.finditer(r'S/\s*([\d,\.]+)', _fuente):
                        try: _monto_pen += float(_m.group(1).replace(',', ''))
                        except Exception: pass
                    for _m in _re.finditer(r'\$\s*([\d,\.]+)', _fuente):
                        try: _monto_usd += float(_m.group(1).replace(',', ''))
                        except Exception: pass
                    if not _re.search(r'[S$]', _fuente) and _fuente.strip():
                        try:
                            _num = _re.search(r'[\d,\.]+', _fuente)
                            if _num: _monto_pen += float(_num.group().replace(',', ''))
                        except Exception: pass
            _monto_parts = []
            if _monto_pen: _monto_parts.append(f"S/ {_monto_pen:,.0f}")
            if _monto_usd: _monto_parts.append(f"$ {_monto_usd:,.0f}")
            _monto_fmt = " + ".join(_monto_parts) if _monto_parts else "—"

            # KPI efectividad: % de enviados con gestión registrada (#3)
            _efectividad_pct = round(_con_gestion / _total_env * 100) if _total_env > 0 else 0
            _efec_lbl = f"Con gestión registrada"
            _efec_sub = f"{_efectividad_pct}% efectividad"

            _kpi_css = """
            <style>
            .kpi-grid{display:flex;gap:12px;margin-bottom:18px;flex-wrap:wrap;}
            .kpi-card{flex:1;min-width:120px;border-radius:10px;padding:18px 12px;text-align:center;color:#fff;}
            .kpi-card .kpi-val{font-size:2.2rem;font-weight:700;line-height:1.1;}
            .kpi-card .kpi-lbl{font-size:0.78rem;margin-top:4px;opacity:.9;}
            .kpi-card .kpi-sub{font-size:0.72rem;margin-top:3px;opacity:.75;font-style:italic;}
            .kpi-blue{background:#1a4f8a;} .kpi-green{background:#1e7e34;}
            .kpi-orange{background:#d97706;} .kpi-red{background:#b91c1c;} .kpi-teal{background:#0e7490;}
            </style>
            """
            _kpi_html = f"""
            {_kpi_css}
            <div class="kpi-grid">
              <div class="kpi-card kpi-blue"><div class="kpi-val">{_total_env}</div><div class="kpi-lbl">Clientes contactados</div></div>
              <div class="kpi-card kpi-green"><div class="kpi-val">{_con_gestion}</div><div class="kpi-lbl">{_efec_lbl}</div><div class="kpi-sub">{_efec_sub}</div></div>
              <div class="kpi-card kpi-orange"><div class="kpi-val">{_pend_resp}</div><div class="kpi-lbl">Pendientes de gestión</div></div>
              <div class="kpi-card kpi-red"><div class="kpi-val">{_sin_contacto}</div><div class="kpi-lbl">Sin contacto</div></div>
              <div class="kpi-card kpi-teal"><div class="kpi-val" style="font-size:1.5rem;">{_monto_fmt}</div><div class="kpi-lbl">💰 Monto gestionado</div></div>
            </div>
            """
            st.markdown(_kpi_html, unsafe_allow_html=True)

            # ── Tabla de gestiones ────────────────────────────────────────────
            if not _details_sesion:
                st.info("📭 No hay clientes registrados en este ciclo.")
            else:
                _OPCIONES_RESULTADO = [
                    "⏳ Sin registrar",
                    "Acordó pagar",
                    "Prometió pagar",
                    "Sin respuesta",
                    "Derivar a Legal",
                    "Solicitó más plazo",
                ]
                _RESULTADO_MAP = {
                    "Acordó pagar":       "EXITOSO",
                    "Prometió pagar":     "PENDIENTE",
                    "Sin respuesta":      "SIN_RESPUESTA",
                    "Derivar a Legal":    "REPROGRAMADO",
                    "Solicitó más plazo": "PENDIENTE",
                }
                # Mapa resultado → (color texto, color fondo) para badges
                _RES_COLOR = {
                    "Acordó pagar":       ("#166534", "#dcfce7"),
                    "Prometió pagar":     ("#1e40af", "#dbeafe"),
                    "Sin respuesta":      ("#6b7280", "#f3f4f6"),
                    "Derivar a Legal":    ("#991b1b", "#fee2e2"),
                    "Solicitó más plazo": ("#92400e", "#fef3c7"),
                    "Enviado OK":         ("#0369a1", "#e0f2fe"),
                    "Fallo envío":        ("#7f1d1d", "#fef2f2"),
                }

                _resultados_guard = _wa_res_sesion.get('resultados_registrados', {}) if _wa_res_sesion else {}

                # ── Separar filas según Tipo ────────────────────────────────────
                # Pendientes = Envío WA SIN gestión posterior del cobrador
                # Regla: si el último WA enviado es más reciente que la última gestión → pendiente
                def _parse_hora_dt(h):
                    if not h:
                        return datetime.min
                    for _fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                        try:
                            return datetime.strptime(h, _fmt)
                        except Exception:
                            pass
                    return datetime.min

                _ultima_gestion: dict = {}   # CodCliente → datetime de última Gestión
                _ultimo_envio:   dict = {}   # CodCliente → datetime de último Envío WA
                for _d_ts in _details_sesion:
                    _cid_ts = _d_ts.get('CodCliente', '')
                    _h_ts   = _parse_hora_dt(_d_ts.get('Hora', ''))
                    if _d_ts.get('Tipo') == 'Gestión':
                        if _cid_ts not in _ultima_gestion or _h_ts > _ultima_gestion[_cid_ts]:
                            _ultima_gestion[_cid_ts] = _h_ts
                    else:
                        if _cid_ts not in _ultimo_envio or _h_ts > _ultimo_envio[_cid_ts]:
                            _ultimo_envio[_cid_ts] = _h_ts

                # Gestionado = última gestión >= último envío WA (no hay envío posterior sin gestionar)
                _cids_gestion_manual = {
                    _cid_ts for _cid_ts, _g_t in _ultima_gestion.items()
                    if _g_t >= _ultimo_envio.get(_cid_ts, datetime.min)
                }
                # #1 Ordenar pendientes por saldo mayor → menor para priorizar deudas grandes
                def _parse_saldo(d):
                    _s = d.get('DeudaS', '') or ''
                    _dol = d.get('DeudaD', '') or ''
                    import re as _re2
                    _tot = 0.0
                    for _m in _re2.findall(r'[\d,\.]+', _s): 
                        try: _tot += float(_m.replace(',',''))
                        except: pass
                    for _m in _re2.findall(r'[\d,\.]+', _dol):
                        try: _tot += float(_m.replace(',','')) * 3.7  # tipo cambio aprox para ordenar
                        except: pass
                    if not _tot:  # fallback a campo Deuda
                        try: _tot = float(str(d.get('Deuda','') or '0').replace(',',''))
                        except: pass
                    return _tot

                _rows_pending = sorted(
                    [(i, d) for i, d in enumerate(_details_sesion)
                     if d.get('Tipo', '') != 'Gestión'
                     and d.get('CodCliente', '') not in _cids_gestion_manual
                     and not _resultados_guard.get(d.get('RowKey', d.get('CodCliente', '')))],
                    key=lambda x: _parse_saldo(x[1]),
                    reverse=True  # mayor saldo primero
                )
                # Clientes con Gestión formal en Supabase → excluir su entrada de Envío WA (evita duplicados)
                _cids_with_gestion = {d.get('CodCliente', '') for d in _details_sesion if d.get('Tipo') == 'Gestión'}
                _rows_saved = [
                    (i, d) for i, d in enumerate(_details_sesion)
                    if d.get('Tipo') == 'Gestión'                         # gestiones del cobrador
                    or (
                        _resultados_guard.get(d.get('RowKey', d.get('CodCliente', '')))
                        and d.get('CodCliente', '') not in _cids_with_gestion  # sin Gestión formal aún
                    )
                ]

                # ── Pendientes (requieren acción del cobrador) ────────────────
                if _rows_pending:
                    # #8 Barra de progreso del ciclo
                    _total_ciclo  = len(_rows_pending) + len(_rows_saved)
                    _pct_ciclo    = int(len(_rows_saved) / _total_ciclo * 100) if _total_ciclo else 0
                    st.markdown(
                        f'<div style="margin-bottom:10px;">' 
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
                        f'<span style="font-size:0.78rem;color:#475569;font-weight:600;">Progreso del ciclo</span>'
                        f'<span style="font-size:0.78rem;color:#475569;">{len(_rows_saved)} de {_total_ciclo} gestionados · {_pct_ciclo}%</span>'
                        f'</div>'
                        f'<div style="background:#e2e8f0;border-radius:999px;height:8px;">'
                        f'<div style="background:#1e7e34;width:{_pct_ciclo}%;height:8px;border-radius:999px;transition:width 0.4s ease;"></div>'
                        f'</div></div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("**Registrar resultado de gestión**")

                    # ── Acción masiva ─────────────────────────────────────────
                    _n_pend = len(_rows_pending)
                    # Mapa chk_key → (_ai, _ad, _ak) para aplicar resultado
                    _chk_det_map = {}
                    for _ai, _ad in _rows_pending:
                        _ak = _ad.get('RowKey', _ad.get('CodCliente', ''))
                        _chk_det_map[f"seg_chk_{_ai}_{_ak}"] = (_ai, _ad, _ak)
                    _chk_keys = list(_chk_det_map.keys())
                    st.session_state['_seg_pending_chk_keys'] = _chk_keys
                    _n_sel_am = sum(1 for _k in _chk_keys if st.session_state.get(_k, False))

                    def _seg_sel_all_toggle():
                        _v = st.session_state.get('seg_chk_all', False)
                        for _k in st.session_state.get('_seg_pending_chk_keys', []):
                            st.session_state[_k] = _v

                    _am_lbl_col, _am_res_col, _am_btn_col = st.columns([3, 2.5, 2])
                    _am_lbl_col.markdown(
                        f'<span style="font-size:0.82rem;font-weight:700;color:#0369a1;">⚡ Acción masiva</span>'
                        f'<span style="font-size:0.78rem;color:#94a3b8;margin-left:6px;">'
                        f'— Marca filas y asigna resultado · <b>{_n_sel_am}</b> seleccionado(s)</span>',
                        unsafe_allow_html=True
                    )
                    _am_resultado = _am_res_col.selectbox(
                        "Resultado masivo",
                        options=[o for o in _OPCIONES_RESULTADO if o != "⏳ Sin registrar"],
                        key="seg_accion_masiva_res",
                        label_visibility="collapsed",
                    )
                    if _am_btn_col.button(
                        f"✅ Aplicar a marcados ({_n_sel_am})",
                        key="seg_btn_am_aplicar",
                        type="primary",
                        disabled=(_n_sel_am == 0),
                        use_container_width=True,
                    ):
                        for _k, (_ai_am, _ad_am, _ak_am) in _chk_det_map.items():
                            if st.session_state.get(_k, False):
                                st.session_state[f"seg_res_{_ai_am}_{_ak_am}"] = _am_resultado
                                st.session_state[_k] = False
                        st.session_state.pop('seg_chk_all', None)
                        st.toast(f"⚡ '{_am_resultado}' aplicado a {_n_sel_am} clientes.", icon="✅")
                        st.rerun()
                    # ── Fin acción masiva ────────────────────────────────────

                    _COL_P = [0.4, 0.4, 1.2, 2.8, 1.5, 1.5, 2.5, 2, 1.5]
                    _hdr_p = st.columns(_COL_P)
                    _hdr_p[0].checkbox("", key="seg_chk_all",
                                       on_change=_seg_sel_all_toggle,
                                       label_visibility="collapsed")
                    for _hp, _ht in zip(_hdr_p[1:], ["#", "Código", "Cliente", "Saldo Real", "Enviado",
                                                      "Resultado", "Notas", "Acción"]):
                        _hp.markdown(f"<span style='font-size:0.75rem;color:#64748b;font-weight:700;"
                                     f"letter-spacing:.04em;text-transform:uppercase;'>{_ht}</span>",
                                     unsafe_allow_html=True)
                    st.divider()
                    for _ri, (_i, _det) in enumerate(_rows_pending):
                        _cod     = _det.get('CodCliente', '')
                        _row_key = _det.get('RowKey', _cod)
                        _cli     = _det.get('Cliente', '')
                        _deu_s_p = _det.get('DeudaS', '')
                        _deu_d_p = _det.get('DeudaD', '')
                        if _deu_s_p or _deu_d_p:
                            _deu = ' + '.join([p for p in [_deu_s_p, _deu_d_p] if p])
                        else:
                            _raw_p = _det.get('Deuda', '')
                            try:
                                _deu = f"S/ {float(_raw_p):,.2f}" if _raw_p else '—'
                            except (ValueError, TypeError):
                                _deu = str(_raw_p) if _raw_p else '—'
                        _hora_raw = _det.get('Hora', '')
                        if _hora_raw and len(_hora_raw) <= 5:   # solo HH:MM
                            _hora = datetime.now().strftime('%d/%m/%Y ') + _hora_raw
                        elif not _hora_raw:
                            _hora = datetime.now().strftime('%d/%m/%Y %H:%M')
                        else:
                            _hora = _hora_raw
                        _cols_p = st.columns(_COL_P)
                        _cols_p[0].checkbox("", key=f"seg_chk_{_i}_{_row_key}",
                                            label_visibility="collapsed")
                        _cols_p[1].markdown(f"<span style='color:#94a3b8;font-size:0.82rem;'>{_ri+1}</span>",
                                            unsafe_allow_html=True)
                        _cols_p[2].markdown(f"<code style='font-size:0.78rem;background:#f1f5f9;"
                                            f"padding:1px 5px;border-radius:3px;'>{_cod}</code>",
                                            unsafe_allow_html=True)
                        _cols_p[3].markdown(f"<span style='font-weight:600;color:#0f172a;'>{_cli}</span>",
                                            unsafe_allow_html=True)
                        # #7 Color semántico en saldo — rojo para deuda alta, verde para baja
                        import re as _re_saldo
                        _saldo_num = 0.0
                        for _sm in _re_saldo.findall(r'[\d,\.]+', _deu):
                            try: _saldo_num += float(_sm.replace(',', ''))
                            except: pass
                        if _saldo_num >= 5000:
                            _saldo_color = '#b91c1c'   # rojo — deuda alta
                        elif _saldo_num >= 1000:
                            _saldo_color = '#d97706'   # naranja — deuda media
                        else:
                            _saldo_color = '#374151'   # gris — deuda baja
                        _cols_p[4].markdown(
                            f"<span style='color:{_saldo_color};font-weight:600;'>{_deu}</span>",
                            unsafe_allow_html=True
                        )
                        _cols_p[5].markdown(f"<span style='font-size:0.82rem;color:#64748b;'>{_hora}</span>",
                                            unsafe_allow_html=True)
                        _sel = _cols_p[6].selectbox(
                            f"res_{_i}", _OPCIONES_RESULTADO,
                            key=f"seg_res_{_i}_{_row_key}",
                            label_visibility="collapsed",
                        )
                        _nota = _cols_p[7].text_input(
                            f"nota_{_i}",
                            key=f"seg_nota_{_i}_{_row_key}",
                            placeholder="Agregar nota...",
                            label_visibility="collapsed",
                        )
                        _btn_t = "primary" if _sel == "Acordó pagar" else "secondary"
                        if _cols_p[8].button("Guardar", key=f"seg_btn_{_i}_{_row_key}",
                                             type=_btn_t, use_container_width=True):
                            if _sel != "⏳ Sin registrar":
                                _res_norm = _RESULTADO_MAP.get(_sel, "PENDIENTE")
                                # RC-BUG-051: Recuperar timestamp original del envío para consistencia de fecha
                                _hora_iso = None
                                if _wa_res_sesion:
                                    for _d in _wa_res_sesion.get('details', []):
                                        if _d.get('RowKey') == _row_key or _d.get('CodCliente') == _cod:
                                            _hora_iso = _d.get('HoraISO')
                                            break
                                _ok, _ = dbm.insert_gestion(
                                    cliente_id=_cod, tipo_gestion='WHATSAPP',
                                    resultado=_res_norm,
                                    notas=_nota if _nota else f"Resultado: {_sel}",
                                    fecha=_hora_iso,  # RC-BUG-051: fecha explícita del envío original
                                    cycle_id=_cycle_id_lote,
                                    metadata_extra={'source': 'seguimiento_post_envio', 'opcion_gestor': _sel},
                                )
                                if _ok:
                                    _resultados_guard[_row_key] = _sel
                                    if _wa_res_sesion:
                                        # RC-BUG-032: persistir nota en session_state para que
                                        # el historial la muestre tras st.rerun()
                                        for _d in _wa_res_sesion.get('details', []):
                                            if _d.get('RowKey') == _row_key:
                                                _d['Notas'] = _nota if _nota else f"Resultado: {_sel}"
                                                break
                                        _wa_res_sesion['resultados_registrados'] = _resultados_guard
                                        st.session_state['last_wa_send_results'] = _wa_res_sesion
                                    st.toast(f"Guardado: {_cli}", icon="✅")
                                    st.rerun()
                                else:
                                    st.error(f"No se pudo guardar el resultado de {_cli}.")
                            else:
                                st.warning("Selecciona un resultado antes de guardar.")

                # ── Historial registrado (tabla HTML) ─────────────────────────
                if _rows_saved:
                    if _rows_pending:
                        st.markdown("---")
                    st.markdown("**Historial de gestiones registradas**")

                    _html_rows = ''
                    import html as _html_utils
                    for _ri, (_i, _det) in enumerate(_rows_saved):
                        _cod_h      = _det.get('CodCliente', '')
                        _row_key_h  = _det.get('RowKey', _cod_h)
                        _cli_h      = _det.get('Cliente', '')
                        _tel_h      = _det.get('Teléfono', '')
                        _deu_s_h    = _det.get('DeudaS', '')
                        _deu_d_h    = _det.get('DeudaD', '')
                        if _deu_s_h or _deu_d_h:
                            _parts = [p for p in [_deu_s_h, _deu_d_h] if p]
                            _deu_h = ' + '.join(_parts)
                        else:
                            _raw = _det.get('Deuda', '')
                            try:
                                _deu_h = f"S/ {float(_raw):,.2f}" if _raw else '—'
                            except (ValueError, TypeError):
                                _deu_h = str(_raw) if _raw else '—'
                        _tipo_h     = _det.get('Tipo', 'Envío WA')
                        _notas_h    = _det.get('Notas', '')
                        _msg_h      = str(_det.get('Mensaje', '') or '')
                        # Si es envío WA con nota de plantilla y ya tiene resultado registrado → nota limpia
                        if _tipo_h != 'Gestión' and _notas_h.startswith('WA masivo'):
                            _notas_h = ''
                        _msg_h_safe = _html_utils.escape(_msg_h)
                        _msg_h_short = _msg_h_safe if len(_msg_h_safe) <= 90 else (_msg_h_safe[:87] + '...')
                        _notas_h_safe = _html_utils.escape(_notas_h)
                        _hora_h_raw = _det.get('Hora', '')
                        if _hora_h_raw and len(_hora_h_raw) <= 5:
                            _hora_h = datetime.now().strftime('%d/%m/%Y ') + _hora_h_raw
                        else:
                            _hora_h = _hora_h_raw
                        _res_h  = _resultados_guard.get(_row_key_h, '')
                        _res_clean = _res_h
                        for _pfx in ['✅ ', '🤝 ', '📵 ', '🔴 ', '💬 ', '⏳ ']:
                            if _res_clean.startswith(_pfx):
                                _res_clean = _res_clean[len(_pfx):]
                                break
                        _ftxt, _fbg = _RES_COLOR.get(_res_clean, ('#374151', '#f1f5f9'))
                        # "↩ Reintentar" — llama goEnviar() definido en <script> del iframe
                        # (sin comillas anidadas → no rompe el atributo onclick)
                        _reintentar_html = (
                            '&nbsp;<a href="#" onclick="goEnviar();return false;" '
                            'style="font-size:0.72rem;background:#e0f2fe;color:#0369a1;'
                            'border-radius:3px;padding:2px 6px;text-decoration:none;cursor:pointer;'
                            'white-space:nowrap;" '
                            'title="Reintentar: ir a Enviar Mensajes con este cliente">'
                            '&#8617;</a>'
                            if _res_clean == 'Sin respuesta' else ''
                        )
                        _tipo_icon  = '📋' if _tipo_h == 'Gestión' else '📤'
                        _tipo_title = 'Gestión manual del cobrador' if _tipo_h == 'Gestión' else 'Envío masivo WA'
                        _row_bg = '#ffffff' if _ri % 2 == 0 else '#f9fafb'
                        _html_rows += (
                            f'<tr style="background:{_row_bg}">'
                            f'<td style="color:#94a3b8;text-align:center;padding:9px 8px;">{_ri+1}</td>'
                            f'<td style="padding:9px 8px;"><span style="background:#f1f5f9;border-radius:3px;'
                            f'padding:2px 6px;font-family:monospace;font-size:0.76rem;">{_cod_h}</span></td>'
                            f'<td style="padding:9px 12px;font-weight:600;color:#0f172a;">{_cli_h}</td>'
                            f'<td style="padding:9px 8px;color:#374151;font-size:0.85rem;">{_tel_h or "—"}</td>'
                            f'<td style="padding:9px 8px;color:#0f172a;font-weight:500;">{_deu_h}</td>'
                            f'<td style="padding:9px 8px;color:#64748b;font-size:0.82rem;white-space:nowrap;">{_hora_h}</td>'
                            f'<td style="padding:9px 8px;text-align:center;" title="{_tipo_title}">'
                            f'<span style="font-size:1rem;">{_tipo_icon}</span></td>'
                            f'<td style="padding:9px 8px;">'
                            f'<span style="background:{_fbg};color:{_ftxt};'
                            f'border-radius:4px;padding:3px 8px;font-size:0.80rem;font-weight:500;'
                            f'white-space:nowrap;">{_res_clean}</span>'
                            f'{_reintentar_html}'
                            f'</td>'
                            f'<td style="padding:9px 12px;color:#64748b;font-size:0.82rem;'
                            f'font-style:{"normal" if _notas_h else "italic"};'
                            f'max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" '
                            f'title="{_notas_h_safe}">{_notas_h_safe or "—"}</td>'
                            f'<td style="padding:9px 12px;color:#334155;font-size:0.80rem;'
                            f'max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" '
                            f'title="{_msg_h_safe}">{_msg_h_short or "—"}</td>'
                            f'</tr>'
                        )

                    _tbl_html = (
                        '<script>'
                        # goEnviar: busca el radio label que contiene "Enviar" y lo clickea
                        # window.parent funciona porque components.html tiene sandbox=allow-same-origin
                        'function goEnviar(){'
                        '  var doc=window.parent.document;'
                        '  doc.querySelectorAll("[data-testid=\'stRadio\'] label").forEach(function(l){'
                        '    if(l.innerText.indexOf("Enviar")>-1)l.click();'
                        '  });'
                        '}'
                        '</script>'
                        '<style>'
                        'body{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}'
                        '.seg-tbl{width:100%;border-collapse:collapse;font-size:0.875rem;}'
                        '.seg-tbl th{background:#f8fafc;color:#64748b;font-weight:700;font-size:0.72rem;'
                        'letter-spacing:.06em;text-transform:uppercase;padding:10px 8px;text-align:left;'
                        'border-bottom:2px solid #e2e8f0;white-space:nowrap;}'
                        '.seg-tbl td{border-bottom:1px solid #f1f5f9;vertical-align:middle;}'
                        '</style>'
                        '<table class="seg-tbl"><thead><tr>'
                        '<th>#</th><th>Código</th><th>Cliente</th><th>Teléfono</th>'
                        '<th>Saldo Real</th><th>Enviado</th><th>Tipo</th><th>Resultado</th><th>Notas</th><th>Mensaje WA</th>'
                        f'</tr></thead><tbody>{_html_rows}</tbody></table>'
                    )
                    # components.html usa sandbox=allow-same-origin → JS puede clickear
                    # el radio de sub-tabs en window.parent.document
                    _tbl_height = max(80, 52 + len(_rows_saved) * 52)
                    components.html(_tbl_html, height=_tbl_height, scrolling=False)

                st.markdown("")
                # Botones de pie
                _col_exp, _col_save = st.columns([1, 1])
                _csv_seg = pd.DataFrame(_details_sesion).to_csv(index=False).encode('utf-8')
                _col_exp.download_button(
                    "Exportar CSV",
                    data=_csv_seg,
                    file_name=f"seguimiento_wa_{_cycle_id_lote}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                # #9 Tooltip mejorado en "Guardar todos"
                if _col_save.button(
                    "Guardar todos los resultados", type="primary", use_container_width=True,
                    help=(
                        "Guarda en Supabase los resultados seleccionados en los desplegables de la sección "
                        "'Registrar resultado de gestión'. Solo guarda filas con resultado distinto a "
                        "'⏳ Sin registrar'. Las gestiones ya guardadas individualmente no se duplican."
                    )
                ):
                    _guardados_tot = 0
                    for _i2, _det2 in enumerate(_details_sesion):
                        _cod2     = _det2.get('CodCliente', '')
                        _row_key2 = _det2.get('RowKey', _cod2)
                        if not _cod2 or _resultados_guard.get(_row_key2):
                            continue
                        _sel2  = st.session_state.get(f"seg_res_{_i2}_{_row_key2}", "⏳ Sin registrar")
                        _nota2 = st.session_state.get(f"seg_nota_{_i2}_{_row_key2}", "")
                        if _sel2 == "⏳ Sin registrar":
                            continue
                        _res_norm2 = _RESULTADO_MAP.get(_sel2, "PENDIENTE")
                        # RC-BUG-051: Recuperar timestamp original del envío para consistencia de fecha
                        _hora_iso2 = None
                        if _wa_res_sesion:
                            for _d in _wa_res_sesion.get('details', []):
                                if _d.get('RowKey') == _row_key2 or _d.get('CodCliente') == _cod2:
                                    _hora_iso2 = _d.get('HoraISO')
                                    break
                        _ok2, _ = dbm.insert_gestion(
                            cliente_id=_cod2, tipo_gestion='WHATSAPP',
                            resultado=_res_norm2,
                            notas=_nota2 if _nota2 else f"Resultado: {_sel2}",
                            fecha=_hora_iso2,  # RC-BUG-051: fecha explícita del envío original
                            cycle_id=_cycle_id_lote,
                            metadata_extra={'source': 'seguimiento_guardar_todos', 'opcion_gestor': _sel2},
                        )
                        if _ok2:
                            _resultados_guard[_row_key2] = _sel2
                            _guardados_tot += 1
                    if _wa_res_sesion:
                        _wa_res_sesion['resultados_registrados'] = _resultados_guard
                        st.session_state['last_wa_send_results'] = _wa_res_sesion
                    if _guardados_tot:
                        st.success(f"{_guardados_tot} resultado(s) guardados en Supabase.")
                    else:
                        st.info("No hay resultados nuevos para guardar.")
                    st.rerun()


