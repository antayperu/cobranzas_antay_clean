import streamlit as st

# --- DESIGN SYSTEM TOKENS (Antay SaaS) ---
COLORS = {
    "primary": "#0F52BA",    # Azul Zafiro (Profesional/Trust)
    "secondary": "#6C757D",  # Gris Neutro
    "success": "#28A745",    # Verde Success
    "warning": "#FFC107",    # Ambar Warning
    "danger": "#DC3545",     # Rojo Danger
    "info": "#17A2B8",       # Cyan Info
    "background": "#F8F9FA", # Gris muy claro
    "surface": "#FFFFFF",    # Blanco puro
    "text_main": "#212529",  # Casi negro
    "text_muted": "#6C757D"
}

def load_css():
    """Injects Enterprise CSS into the Streamlit app."""
    css = f"""
    <style>
        /* GLOBAL FONT & RESET */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: {COLORS['text_main']};
        }}
        
        /* HEADER CLEANUP */
        header[data-testid="stHeader"] {{
            background-color: transparent;
        }}
        
        /* SIDEBAR PREMIUM LOOK */
        [data-testid="stSidebar"] {{
            background-color: #F0F2F6;
            border-right: 1px solid #DEE2E6;
        }}
        
        /* BUTTONS (SaaS Style) */
        .stButton button {{
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        /* KPI CARD CONTAINER */
        .kpi-card {{
            background: {COLORS['surface']};
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #E9ECEF;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: transform 0.2s;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }}
        
        /* WIZARD STEPS */
        .wizard-step {{
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 6px;
            background: {COLORS['surface']};
            border-left: 3px solid {COLORS['secondary']};
        }}
        .wizard-step.active {{
            border-left-color: {COLORS['primary']};
            background: #E8F0FE;
        }}
        .wizard-step.done {{
            border-left-color: {COLORS['success']};
        }}

        /* TABLE HEADER */
        thead tr th {{
            background-color: #F8F9FA !important;
            color: #495057 !important;
            font-weight: 600 !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def kpi_card_html(label, value, sub_value=None, status="neutral"):
    """Generates consistent HTML for KPI Cards."""
    color_map = {
        "neutral": COLORS['info'],
        "success": COLORS['success'],
        "warning": COLORS['warning'],
        "danger": COLORS['danger']
    }
    accent = color_map.get(status, COLORS['secondary'])
    
    sub_html = f"<div style='font-size: 13px; color: {COLORS['text_muted']}; margin-top: 4px;'>{sub_value}</div>" if sub_value else ""
    
    return f"""
    <div class="kpi-card" style="border-left: 4px solid {accent};">
        <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: {COLORS['text_muted']}; font-weight: 600;">{label}</div>
        <div style="font-size: 24px; font-weight: 700; color: {COLORS['text_main']}; margin-top: 8px;">{value}</div>
        {sub_html}
    </div>
    """
