import streamlit as st
import pandas as pd
import utils.ui.styles as styles

# --- COLUMN DEFINITIONS ---
# Vista Ejecutiva: Simple, operativa, "1 vistazo" (NO muestra tracking)
EXECUTIVE_COLS = [
    'COD CLIENTE', 'EMPRESA', 
    'ESTADO DEUDA',        # Status Debt (Badge)
    'CORREO',              # Email del cliente
    'TELÉFONO',
    'SALDO REAL',          # Key KPI
    'FECH VENC',           # Critical Date
    'NOTA'                 # Notes
]

# Column config for semantic labels and tooltips
COLUMN_CONFIG = {
    # --- TRACKING COLUMNS (ONLY 2 - Visible only in Complete view) ---
    "ESTADO_EMAIL": st.column_config.TextColumn(
        "Estado Notificación (Email)", 
        width="medium",
        help="PENDIENTE: no enviado | ENVIADO: confirmado | FALLIDO: error en envío"
    ),
    "FECHA_ULTIMO_ENVIO": st.column_config.TextColumn(
        "Último Envío", 
        width="medium",
        help="Fecha y hora del último envío exitoso (vacío si no se ha enviado)"
    ),
    
    # --- OTHER COLUMNS ---
    "CORREO": st.column_config.TextColumn(
        "Email", 
        width="medium",
        help="Email del cliente para notificaciones"
    ),
    "SALDO REAL": st.column_config.TextColumn(
        "Saldo Real", 
        help="Monto actualizado en Soles"
    ),
    "ESTADO DEUDA": st.column_config.TextColumn(
        "Estado Deuda",
        help="Semaforización por días de mora"
    ),
}

def highlight_status(val):
    """Applies Enterprise Status Colors (Badges) to the dataframe."""
    color = ''
    s = str(val).lower()
    if 'por vencer' in s:
        color = f'background-color: #D4EDDA; color: {styles.COLORS["success"]}; font-weight: 500'
    elif 'preventiva' in s:
        color = f'background-color: #FFF3CD; color: #856404; font-weight: 500'
    elif 'administrativa' in s:
        color = f'background-color: #FFE5D0; color: #E65100; font-weight: 500'
    elif 'pre-legal' in s or 'vencido' in s:
        color = f'background-color: #F8D7DA; color: {styles.COLORS["danger"]}; font-weight: 500'
    return color

def render_report(df_filtered):
    """
    Renders the Main Report Table with Simplified Enterprise UX.
    - View Toggle (Executive vs Complete)
    - Executive view: NO tracking columns (clean business view)
    - Complete view: ALL columns including 2 tracking columns
    """
    
    # --- 1. VIEW CONTROLS ---
    c_title, c_toggle = st.columns([3, 1])
    with c_title:
        st.write("")
    with c_toggle:
        view_mode = st.radio("Modo de Vista", ["Ejecutiva", "Completa"], 
                             horizontal=True, label_visibility="collapsed")

    # --- 2. COLUMN SELECTION ---
    if view_mode == "Ejecutiva":
        # Vista Ejecutiva: Simple, NO tracking
        cols_to_show = [c for c in EXECUTIVE_COLS if c in df_filtered.columns]
    else:
        # Vista Completa: Todo, incluyendo tracking
        cols_to_show = parse_full_columns(df_filtered.columns)

    # --- 3. PREPARE DISPLAY DATA ---
    df_display = df_filtered[cols_to_show].copy()

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

    # --- 4. FULLSCREEN BUTTON (Solo en Vista Completa) ---
    if view_mode == "Completa":
        # Link para abrir en la MISMA pestaña (preserva session_state)
        # FIX: target="_self" en lugar de "_blank" para mantener sesión
        st.markdown("""
        <div style="text-align: right; margin-bottom: 10px;">
            <a href="?view=full_table" target="_self" style="
                display: inline-block;
                padding: 8px 16px;
                background-color: #2E86AB;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: 500;
                font-size: 14px;
            ">
                🖥️ Ver en Pantalla Completa
            </a>
        </div>
        """, unsafe_allow_html=True)

    
    # --- 5. RENDER TABLE (Normal) ---
    styler = df_display.style.map(highlight_status, subset=['ESTADO DEUDA']) if 'ESTADO DEUDA' in df_display.columns else df_display.style
    
    # Build column_config for displayed columns only
    active_config = {k: v for k, v in COLUMN_CONFIG.items() if k in cols_to_show}
    
    st.dataframe(
        styler,
        width="stretch",
        height=500,
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
    priority = [
        'COD CLIENTE', 'EMPRESA', 
        'ESTADO_EMAIL',            # Tracking column 1 of 2
        'FECHA_ULTIMO_ENVIO',      # Tracking column 2 of 2
        'ESTADO DEUDA', 
        'CORREO',
        'TELÉFONO',
        'SALDO REAL',
        'FECH VENC',
        'NOTA'
    ]
    remainder = [c for c in all_cols if c not in priority and not c.endswith('_DISPLAY')]
    return [c for c in priority if c in all_cols] + remainder

def render_report_fullscreen(df_filtered):
    """
    Renderiza la tabla en modo pantalla completa dedicada (nueva pestaña).
    Ocupa 100% del viewport sin sidebar ni elementos decorativos.
    """
    
    # Preparar columnas (siempre Vista Completa en fullscreen)
    cols_to_show = parse_full_columns(df_filtered.columns)
    
    # Preparar datos para display
    df_display = df_filtered[cols_to_show].copy()
    
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
    
    # Aplicar estilos
    styler = df_display.style.map(highlight_status, subset=['ESTADO DEUDA']) if 'ESTADO DEUDA' in df_display.columns else df_display.style
    
    # Build column_config
    active_config = {k: v for k, v in COLUMN_CONFIG.items() if k in cols_to_show}
    
    # Renderizar tabla ocupando TODO el espacio disponible
    # FIX: height debe ser un entero (pixels), NO None
    st.dataframe(
        styler,
        width="stretch",
        height=800,  # Altura fija válida para pantalla completa
        column_config=active_config
    )
    
    # Footer con resumen
    if 'SALDO REAL' in df_filtered.columns:
        try:
            total_s = df_filtered['SALDO REAL'].sum()
            st.caption(f"📊 **Total Listado:** S/ {total_s:,.2f} | **Registros:** {len(df_filtered)}")
        except:
            pass

