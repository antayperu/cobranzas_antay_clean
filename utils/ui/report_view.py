import streamlit as st
import pandas as pd
from datetime import datetime, date
import utils.ui.styles as styles
import utils.settings_manager as sm

# --- COLUMN DEFINITIONS ---
# Listado maestro de todas las posibles columnas (para el configurador)
ALL_POSSIBLE_COLS = [
    'COD CLIENTE', 'EMPRESA', 'COMPROBANTE', 'FECH EMIS', 'MONEDA',
    'MONT EMIT', 'TIPO CAMBIO', 'SALDO', 'DETRACCIÓN', 'ESTADO DETRACCION',
    'AMORTIZACIONES', 'SALDO REAL', 'ESTADO_EMAIL', 'FECHA_ULTIMO_ENVIO',
    'ESTADO_WHATSAPP', 'FECHA_ULTIMO_WA',
    'NOTA', 'ENVIAR EMAIL', 'CORREO', 'TELÉFONO', 'FECH VENC', 'ESTADO DEUDA'
]

# Vista Ejecutiva: Orden histórico (fallback)
EXECUTIVE_COLS_DEFAULT = [
    'COD CLIENTE', 'EMPRESA', 'COMPROBANTE', 'FECH EMIS', 'MONEDA',
    'MONT EMIT', 'TIPO CAMBIO', 'SALDO', 'DETRACCIÓN', 'ESTADO DETRACCION',
    'AMORTIZACIONES', 'SALDO REAL', 'ESTADO_EMAIL', 'FECHA_ULTIMO_ENVIO',
    'ESTADO_WHATSAPP', 'FECHA_ULTIMO_WA',
    'NOTA', 'ENVIAR EMAIL'
]

# Column config for semantic labels and tooltips
COLUMN_CONFIG = {
    # --- TRACKING COLUMNS ---
    "ESTADO_EMAIL": st.column_config.TextColumn(
        "Estado", 
        width="small",
        help="Estado de Notificación: PENDIENTE | ENVIADO | FALLIDO"
    ),
    "FECHA_ULTIMO_ENVIO": st.column_config.TextColumn(
        "Último Email",
        width="medium"
    ),
    "ESTADO_WHATSAPP": st.column_config.TextColumn(
        "WA Estado",
        width="small",
        help="Estado de WhatsApp: PENDIENTE | ENVIADO | FALLIDO"
    ),
    "FECHA_ULTIMO_WA": st.column_config.TextColumn(
        "Último WA",
        width="medium"
    ),
    "ESTADO DETRACCION": st.column_config.TextColumn(
        "Estado Detracción",
        width="medium"
    ),
    "DETRACCIÓN": st.column_config.NumberColumn(
        "Detracción",
        format="S/ %.2f",
        width="small"
    ),
    "SALDO REAL": st.column_config.TextColumn(
        "Saldo Real", 
        width="small"
    ),
    "SALDO": st.column_config.TextColumn(
        "Saldo",
        width="small"
    ),
    "MONT EMIT": st.column_config.TextColumn(
        "Monto Emitido",
        width="small"
    ),
    "TIPO CAMBIO": st.column_config.NumberColumn(
        "TC",
        format="%.3f",
        width="small"
    ),
    "FECH EMIS": st.column_config.DateColumn(
        "F. Emis.",
        format="DD/MM/YY",
        width="small"
    ),
    "FECH VENC": st.column_config.DateColumn(
        "F. Venc.",
        format="DD/MM/YY",
        width="small"
    ),
    "ENVIAR EMAIL": st.column_config.TextColumn(
        "¿Email?",
        width="small"
    ),
    "CORREO": st.column_config.TextColumn(
        "Email", 
        width="medium"
    ),
    "TELÉFONO": st.column_config.TextColumn(
        "Teléf.",
        width="small"
    ),
    "COD CLIENTE": st.column_config.TextColumn(
        "ID",
        width="small"
    ),
    "EMPRESA": st.column_config.TextColumn(
        "EMPRESA",
        width="large"
    ),
    "COMPROBANTE": st.column_config.TextColumn(
        "Comprobante",
        width="medium"
    ),
    "AMORTIZACIONES": st.column_config.TextColumn(
        "Amortizaciones",
        width="medium"
    ),
    "NOTA": st.column_config.TextColumn(
        "Nota",
        width="large"
    ),
    "ESTADO DEUDA": st.column_config.TextColumn(
        "Estado Deuda",
        width="medium"
    ),
}

def highlight_status(val):
    """Applies Enterprise Status Colors (Badges) to the dataframe."""
    color = ''
    s = str(val).lower()
    if 'por vencer' in s or '🟢' in s or 'enviado' in s:
        color = f'background-color: #D4EDDA; color: {styles.COLORS["success"]}; font-weight: 600'
    elif 'preventiva' in s or '🟡' in s:
        color = f'background-color: #FFF3CD; color: #856404; font-weight: 600'
    elif 'administrativa' in s or '🟠' in s:
        color = f'background-color: #FFE5D0; color: #E65100; font-weight: 600'
    elif 'pre-legal' in s or 'vencido' in s or '🔴' in s or 'fallido' in s or 'error' in s:
        color = f'background-color: #F8D7DA; color: {styles.COLORS["danger"]}; font-weight: 600'
    return color

def highlight_kpi(val):
    """Highlights main KPI in bold/corporate color."""
    return f'color: {styles.COLORS["primary"]}; font-weight: 700; font-size: 14px;'

def format_human_date(val):
    """Converts timestamp to human-readable format like 'Hoy, 15:40'."""
    if not val or pd.isna(val) or str(val).strip() == "":
        return "-"
    try:
        # Intentar parsear fecha (asumiendo formato ISO o similar del sistema)
        dt = pd.to_datetime(val)
        today = date.today()
        if dt.date() == today:
            return f"📅 Hoy, {dt.strftime('%H:%M')}"
        elif dt.date() == (today - pd.Timedelta(days=1)):
            return f"📅 Ayer, {dt.strftime('%H:%M')}"
        else:
            return f"📅 {dt.strftime('%d %b, %H:%M')}"
    except:
        return str(val)

def render_report(df_filtered):
    """
    Renders the Main Report Table with Customizable Enterprise UX.
    - User can configure visible columns and their order.
    - Settings are preserved in Supabase app_config.
    """
    # 0. Cargar configuración de vistas
    settings = sm.load_settings()
    report_views = settings.get('report_views', {})
    
    # --- 1. VIEW CONTROLS ---
    c_title, c_toggle, c_config = st.columns([2, 1.5, 1])
    with c_title:
        cycle_id = st.session_state.get("cycle_id", "")
        if cycle_id:
            st.caption(f"Ciclo: **{cycle_id}**")
    with c_toggle:
        view_mode = st.radio("Modo de Vista", ["Ejecutiva", "Completa"],
                             horizontal=True, label_visibility="collapsed")
    with c_config:
        show_config = st.toggle("⚙️ Configurar Vista", False)

    # --- 1.1 CONFIGURATION UI ---
    view_key = view_mode.lower()
    current_cols = report_views.get(view_key, EXECUTIVE_COLS_DEFAULT)
    
    if show_config:
        with st.expander(f"🛠️ Personalizar Vista {view_mode}", expanded=True):
            st.info("Selecciona las columnas y usa las flechas para reordenarlas. Se guarda automáticamente.")
            
            # Selector de columnas (preserva orden de selección)
            all_cols = [c for c in df_filtered.columns if not c.endswith('_DISPLAY')]
            new_selection = st.multiselect(
                "Columnas Visibles", 
                options=all_cols,
                default=[c for c in current_cols if c in all_cols]
            )
            
            # Reordenamiento fino con botones
            if new_selection:
                st.write("**Orden de Columnas (Arrastrar no disponible, usar flechas):**")
                ordered_cols = list(new_selection)
                for i, col in enumerate(ordered_cols):
                    cols_btn = st.columns([6, 1, 1])
                    with cols_btn[0]:
                        st.markdown(f"**{i+1}.** {col}")
                    with cols_btn[1]:
                        if i > 0:
                            if st.button("↑", key=f"up_{view_key}_{col}_{i}"):
                                ordered_cols[i], ordered_cols[i-1] = ordered_cols[i-1], ordered_cols[i]
                                report_views[view_key] = ordered_cols
                                settings['report_views'] = report_views
                                sm.save_settings(settings)
                                st.rerun()
                    with cols_btn[2]:
                        if i < len(ordered_cols) - 1:
                            if st.button("↓", key=f"down_{view_key}_{col}_{i}"):
                                ordered_cols[i], ordered_cols[i+1] = ordered_cols[i+1], ordered_cols[i]
                                report_views[view_key] = ordered_cols
                                settings['report_views'] = report_views
                                sm.save_settings(settings)
                                st.rerun()
                
                # Guardar selección si cambió el multiselect
                if list(new_selection) != list(current_cols):
                    report_views[view_key] = list(new_selection)
                    settings['report_views'] = report_views
                    sm.save_settings(settings)
                    st.rerun()
                    
            if st.button("🔄 Restaurar Predeterminado", key=f"reset_{view_key}"):
                report_views[view_key] = EXECUTIVE_COLS_DEFAULT
                settings['report_views'] = report_views
                sm.save_settings(settings)
                st.rerun()

    # --- 2. COLUMN SELECTION (From Settings) ---
    cols_to_show = [c for c in current_cols if c in df_filtered.columns]
    
    # Si no hay configuración o está vacía, usar lógica de parse_full_columns para 'Completa'
    if not cols_to_show:
        if view_mode == "Ejecutiva":
            cols_to_show = [c for c in EXECUTIVE_COLS_DEFAULT if c in df_filtered.columns]
        else:
            cols_to_show = parse_full_columns(df_filtered.columns)

    # --- 3. PREPARE DISPLAY DATA ---
    df_display = df_filtered[cols_to_show].copy()

    # Apply Human Date to FECHA_ULTIMO_ENVIO and FECHA_ULTIMO_WA
    if 'FECHA_ULTIMO_ENVIO' in df_display.columns:
        df_display['FECHA_ULTIMO_ENVIO'] = df_display['FECHA_ULTIMO_ENVIO'].apply(format_human_date)
    if 'FECHA_ULTIMO_WA' in df_display.columns:
        df_display['FECHA_ULTIMO_WA'] = df_display['FECHA_ULTIMO_WA'].apply(format_human_date)

    # Add Visual Badges to Status columns
    if 'ESTADO_EMAIL' in df_display.columns:
        df_display['ESTADO_EMAIL'] = df_display['ESTADO_EMAIL'].replace({
            'ENVIADO': '🟢 ENVIADO',
            'PENDIENTE': '⚪ PENDIENTE',
            'FALLIDO': '🔴 FALLIDO'
        })
    if 'ESTADO_WHATSAPP' in df_display.columns:
        df_display['ESTADO_WHATSAPP'] = df_display['ESTADO_WHATSAPP'].replace({
            'ENVIADO': '🟢 ENVIADO',
            'PENDIENTE': '⚪ PENDIENTE',
            'FALLIDO': '🔴 FALLIDO'
        })
    
    if 'ESTADO DETRACCION' in df_display.columns:
        # Solo aplicar badge si es texto (no info de banco larga)
        mask_pend = df_display['ESTADO DETRACCION'] == 'Pendiente'
        df_display.loc[mask_pend, 'ESTADO DETRACCION'] = '🟡 PENDIENTE'
        mask_napl = df_display['ESTADO DETRACCION'] == 'No Aplica'
        df_display.loc[mask_napl, 'ESTADO DETRACCION'] = '⚪ NO APLICA'

    # Swap _DISPLAY columns for clean names
    for c in cols_to_show:
        if c == 'SALDO REAL' and 'SALDO REAL_DISPLAY' in df_filtered.columns:
             df_display['SALDO REAL'] = df_filtered['SALDO REAL_DISPLAY']
        elif c == 'SALDO' and 'SALDO_DISPLAY' in df_filtered.columns:
             df_display['SALDO'] = df_filtered['SALDO_DISPLAY']
        elif c == 'MONT EMIT' and 'MONT EMIT_DISPLAY' in df_filtered.columns:
             df_display['MONT EMIT'] = df_filtered['MONT EMIT_DISPLAY']
        elif c == 'DETRACCIÓN' and 'DETRACCIÓN_DISPLAY' in df_filtered.columns:
             df_display['DETRACCIÓN'] = df_filtered['DETRACCIÓN_DISPLAY']

    # --- 4. RENDER TABLE ---
    # --- 5. STYLE & RENDER ---
    # Colores por estado de deuda
    styler = df_display.style.map(highlight_status, subset=['ESTADO DEUDA']) if 'ESTADO DEUDA' in df_display.columns else df_display.style
    
    # Colores por estado de email
    if 'ESTADO_EMAIL' in df_display.columns:
        styler = styler.map(highlight_status, subset=['ESTADO_EMAIL'])

    # Colores por estado de WhatsApp
    if 'ESTADO_WHATSAPP' in df_display.columns:
        styler = styler.map(highlight_status, subset=['ESTADO_WHATSAPP'])
        
    # Colores por estado detracción
    if 'ESTADO DETRACCION' in df_display.columns:
        styler = styler.map(highlight_status, subset=['ESTADO DETRACCION'])

    # Resalte de KPI (Saldo Real)
    if 'SALDO REAL' in df_display.columns:
        styler = styler.map(highlight_kpi, subset=['SALDO REAL'])
    
    # Build column_config for displayed columns only
    active_config = {k: v for k, v in COLUMN_CONFIG.items() if k in cols_to_show}
    
    st.dataframe(
        styler,
        use_container_width=True,
        height=600,
        column_config=active_config
    )
    
    # --- 7. SUMMARY FOOTER ---
    if 'SALDO REAL' in df_filtered.columns:
        try:
             total_s = df_filtered['SALDO REAL'].sum()
             st.caption(f"Total Listado: S/ {total_s:,.2f} | Registros: {len(df_filtered)}")
        except:
             pass


def parse_full_columns(all_cols):
    """Helper to order columns nicely in Full View."""
    # Vista Completa: Mismo orden base que Ejecutiva + columnas adicionales al final
    priority = [
        'COD CLIENTE',
        'EMPRESA',
        'COMPROBANTE',
        'FECHA EMISIÓN',
        'MONEDA',
        'MONT EMIT',
        'TIPO CAMBIO',
        'SALDO',
        'DETRACCIÓN',
        'ESTADO DETRACCION',
        'AMORTIZACIONES',
        'SALDO REAL',
        'ESTADO_EMAIL',
        'FECHA_ULTIMO_ENVIO',
        'ESTADO_WHATSAPP',
        'FECHA_ULTIMO_WA',
        'NOTA',
        'ENVIAR EMAIL'
    ]
    # Agregar columnas restantes que no están en priority (excepto _DISPLAY)
    remainder = [c for c in all_cols if c not in priority and not c.endswith('_DISPLAY')]
    return [c for c in priority if c in all_cols] + remainder


