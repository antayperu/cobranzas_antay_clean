import streamlit as st

# Antay enterprise design tokens.
COLORS = {
    "primary": "#0D3B66",
    "primary_soft": "#245D99",
    "accent": "#0B7285",
    "success": "#2B8A3E",
    "warning": "#E67700",
    "danger": "#C92A2A",
    "background": "#F1F5FB",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FBFF",
    "text_main": "#102A43",
    "text_muted": "#486581",
    "border": "#D9E2EC",
}


def load_css():
    """Inject enterprise CSS for app, sidebar and premium cards."""
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

        :root {{
            --antay-primary: {COLORS['primary']};
            --antay-primary-soft: {COLORS['primary_soft']};
            --antay-accent: {COLORS['accent']};
            --antay-bg: {COLORS['background']};
            --antay-surface: {COLORS['surface']};
            --antay-surface-alt: {COLORS['surface_alt']};
            --antay-border: {COLORS['border']};
            --antay-text: {COLORS['text_main']};
            --antay-muted: {COLORS['text_muted']};
        }}

        html, body, [class*="css"] {{
            font-family: 'Manrope', 'IBM Plex Sans', sans-serif;
            color: var(--antay-text);
        }}

        [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(circle at 8% 0%, rgba(13,59,102,0.14), rgba(13,59,102,0) 44%),
                radial-gradient(circle at 95% 12%, rgba(11,114,133,0.12), rgba(11,114,133,0) 38%),
                linear-gradient(180deg, #f7fafd 0%, var(--antay-bg) 100%);
        }}

        header[data-testid="stHeader"] {{
            background-color: transparent;
        }}

        [data-testid="stAppViewBlockContainer"] {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 2.4rem;
            padding-right: 2.4rem;
            max-width: 100% !important;
        }}

        [data-testid="stSidebar"] {{
            background:
                linear-gradient(165deg, #0a2545 0%, #123564 54%, #18457c 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.12);
        }}

        [data-testid="stSidebarContent"] {{
            padding-top: 1.2rem;
        }}

        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3,
        [data-testid="stSidebar"] .stMarkdown h4,
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
            color: #e5efff;
        }}

        [data-testid="stSidebar"] [data-testid="stExpander"] {{
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 12px;
            background: rgba(255,255,255,0.06);
        }}

        [data-testid="stSidebar"] .stAlert {{
            background: rgba(0, 0, 0, 0.24);
            border: 1px solid rgba(255,255,255,0.18);
        }}

        .stButton button {{
            border-radius: 10px;
            font-weight: 650;
            border: 1px solid var(--antay-border);
            transition: all .18s ease;
        }}

        .stButton button[kind="primary"] {{
            background: linear-gradient(130deg, var(--antay-primary) 0%, var(--antay-primary-soft) 100%);
            color: #ffffff;
            border: none;
            box-shadow: 0 8px 18px rgba(13, 59, 102, 0.22);
        }}

        .stButton button:hover {{
            transform: translateY(-1px);
        }}

        [data-testid="stSidebar"] .stButton button {{
            background: #e9f0fb;
            color: #10365f;
            border: 1px solid #9db5d4;
        }}

        [data-testid="stSidebar"] .stButton button:hover {{
            background: #f4f8ff;
            color: #0a2f57;
        }}

        [data-testid="stSidebar"] .stButton button[kind="primary"] {{
            background: linear-gradient(130deg, var(--antay-primary) 0%, var(--antay-primary-soft) 100%);
            color: #ffffff;
            border: none;
            box-shadow: 0 8px 18px rgba(13, 59, 102, 0.28);
        }}

        [data-testid="stSidebar"] .stButton button:disabled {{
            background: #d8e3f3 !important;
            color: #5d7290 !important;
            border: 1px solid #b9cade !important;
            opacity: 1 !important;
        }}

        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            gap: 0.5rem;
            background: transparent;
        }}

        [data-testid="stTabs"] [data-baseweb="tab"] {{
            border-radius: 999px;
            border: 1px solid var(--antay-border);
            background: rgba(255,255,255,0.7);
            font-weight: 600;
            padding: 0.3rem 1rem;
        }}

        [data-testid="stTabs"] [aria-selected="true"] {{
            background: linear-gradient(120deg, #eef5ff 0%, #e4f0ff 100%);
            border-color: #9eb6d8;
            color: var(--antay-primary);
        }}

        [data-testid="stFileUploaderDropzone"] {{
            border-radius: 12px;
            border: 1px dashed #95aac6;
            background: rgba(255, 255, 255, 0.45);
        }}

        .kpi-card {{
            background: var(--antay-surface);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid var(--antay-border);
            box-shadow: 0 8px 20px rgba(16, 42, 67, 0.06);
            transition: transform .18s ease;
        }}

        .kpi-card:hover {{
            transform: translateY(-2px);
        }}

        .antay-sidebar-card {{
            background:
                linear-gradient(145deg, rgba(255,255,255,0.16), rgba(255,255,255,0.06));
            border: 1px solid rgba(255,255,255,0.24);
            border-radius: 14px;
            padding: 14px 14px 12px 14px;
            box-shadow: 0 14px 26px rgba(3, 15, 33, 0.24);
        }}

        .antay-sidebar-card h3 {{
            margin: 8px 0 6px 0;
            color: #f1f6ff;
            font-size: 1.05rem;
            font-weight: 760;
        }}

        .antay-sidebar-card p {{
            margin: 0 0 8px 0;
            color: #d7e5ff;
            font-size: 0.83rem;
            line-height: 1.3rem;
        }}

        .antay-sidebar-card small {{
            color: #b8cdee;
            font-size: 0.76rem;
        }}

        .antay-sidebar-card__top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
        }}

        .antay-pill {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.18rem 0.5rem;
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            background: rgba(217, 238, 255, 0.2);
            color: #f2f7ff;
            border: 1px solid rgba(255,255,255,0.3);
        }}

        .antay-version {{
            font-size: 0.72rem;
            font-weight: 700;
            color: #d0e2ff;
        }}

        .antay-inline-note {{
            background: linear-gradient(120deg, rgba(13,59,102,0.12), rgba(11,114,133,0.10));
            border: 1px solid rgba(164, 193, 231, 0.9);
            border-radius: 10px;
            padding: 0.7rem 0.85rem;
            font-size: 0.84rem;
            line-height: 1.25rem;
            margin-bottom: 0.7rem;
        }}

        [data-testid="stSidebar"] .antay-inline-note {{
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.4);
            color: #eef5ff !important;
        }}

        [data-testid="stSidebar"] .antay-inline-note strong {{
            color: #ffffff !important;
        }}

        [data-testid="stSidebar"] .antay-inline-note code {{
            color: #f8fbff !important;
            background: rgba(6, 30, 60, 0.45);
            border-radius: 6px;
            padding: 0.08rem 0.3rem;
        }}

        .antay-welcome-card {{
            background:
                linear-gradient(125deg, rgba(13,59,102,0.08), rgba(11,114,133,0.05)),
                var(--antay-surface);
            border-radius: 16px;
            border: 1px solid #c9d7ea;
            box-shadow: 0 16px 32px rgba(16, 42, 67, 0.08);
            padding: 22px;
        }}

        .antay-welcome-card h3 {{
            margin: 0 0 8px 0;
            color: var(--antay-primary);
            font-weight: 780;
        }}

        .antay-welcome-card p {{
            margin: 0 0 14px 0;
            color: var(--antay-muted);
            line-height: 1.35rem;
        }}

        .antay-step-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 0.65rem;
        }}

        .antay-step {{
            border: 1px solid var(--antay-border);
            border-radius: 10px;
            background: var(--antay-surface-alt);
            padding: 0.65rem 0.7rem;
        }}

        .antay-step b {{
            color: var(--antay-primary);
            font-size: 0.82rem;
            display: block;
            margin-bottom: 0.2rem;
        }}

        .antay-step span {{
            color: var(--antay-muted);
            font-size: 0.8rem;
        }}

        .antay-animate-in {{
            animation: antay-fade-up .52s ease-out both;
        }}

        @keyframes antay-fade-up {{
            from {{
                opacity: 0;
                transform: translateY(8px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        /* CRM & Clientes Premium enhancements */
        [data-testid="stRadio"] > div {{
            gap: 0.3rem;
        }}

        [data-testid="stRadio"] label {{
            border-radius: 999px;
            border: 1px solid var(--antay-border);
            padding: 0.25rem 0.85rem;
            font-weight: 600;
            font-size: 0.84rem;
            transition: all 0.15s ease;
        }}

        [data-testid="stRadio"] label[data-checked="true"],
        [data-testid="stRadio"] label:has(input:checked) {{
            background: linear-gradient(120deg, #eef5ff 0%, #e4f0ff 100%);
            border-color: #9eb6d8;
            color: var(--antay-primary);
        }}

        .stToggle label {{
            font-weight: 600;
            font-size: 0.84rem;
        }}

        [data-testid="stDataFrame"] {{
            border-radius: 12px;
            border: 1px solid var(--antay-border);
        }}

        [data-testid="stMetric"] {{
            background: var(--antay-surface);
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid var(--antay-border);
            box-shadow: 0 4px 12px rgba(16, 42, 67, 0.04);
        }}

        @media (max-width: 900px) {{
            [data-testid="stAppViewBlockContainer"] {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            .antay-welcome-card {{
                padding: 16px;
            }}
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def kpi_card_html(label, value, sub_value=None, status="neutral", tooltip=None):
    """Generate consistent HTML for KPI cards."""
    color_map = {
        "neutral": COLORS["accent"],
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "danger": COLORS["danger"],
    }
    accent = color_map.get(status, COLORS["primary_soft"])
    sub_html = (
        f"<div style='font-size:13px;color:{COLORS['text_muted']};margin-top:4px;'>{sub_value}</div>"
        if sub_value
        else ""
    )
    tooltip_attr = f'title="{tooltip}"' if tooltip else ""
    cursor_style = "cursor:help;" if tooltip else ""
    return f"""
    <div class="kpi-card" style="border-left:4px solid {accent};{cursor_style}" {tooltip_attr}>
        <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.45px;color:{COLORS['text_muted']};font-weight:650;">
            {label}
        </div>
        <div style="font-size:24px;font-weight:760;color:{COLORS['text_main']};margin-top:8px;">{value}</div>
        {sub_html}
    </div>
    """


def _fmt_number(value, is_currency=True, symbol="S/"):
    try:
        num = float(value)
        if is_currency:
            return f"{symbol} {num:,.2f}"
        return f"{int(num):,}" if num.is_integer() else f"{num:,.2f}"
    except Exception:
        return str(value)


def kpi_card_dashboard(
    title,
    value_s,
    value_d,
    color="#0B7285",
    force_single_s=False,
    is_currency=True,
):
    """
    Compatibility helper for tabs that still consume dual-currency KPI cards.
    """
    if is_currency:
        if force_single_s:
            body = (
                f"<div style='font-size:24px;font-weight:760;color:{COLORS['text_main']};'>"
                f"{_fmt_number(value_s, True, 'S/')}</div>"
            )
        else:
            body = (
                f"<div style='font-size:20px;font-weight:760;color:{COLORS['text_main']};'>"
                f"{_fmt_number(value_s, True, 'S/')}</div>"
                f"<div style='font-size:16px;font-weight:600;color:{COLORS['text_muted']};'>"
                f"{_fmt_number(value_d, True, '$')}</div>"
            )
    else:
        body = (
            f"<div style='font-size:20px;font-weight:760;color:{COLORS['text_main']};'>"
            f"S/: {_fmt_number(value_s, False)}</div>"
            f"<div style='font-size:16px;font-weight:600;color:{COLORS['text_muted']};'>"
            f"$: {_fmt_number(value_d, False)}</div>"
        )

    return f"""
    <div class="kpi-card" style="border-left:4px solid {color}; min-height:104px;">
        <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.45px;color:{COLORS['text_muted']};font-weight:650;">
            {title}
        </div>
        <div style="margin-top:8px;">{body}</div>
    </div>
    """


def get_welcome_html():
    """Welcome card shown before first processing cycle."""
    return """
    <div class="antay-welcome-card antay-animate-in">
        <span class="antay-pill" style="background:rgba(13,59,102,0.1); color:#0d3b66; border-color:#adc2dc;">
            Cloud Workflow
        </span>
        <h3>Centro corporativo de cobranzas listo para operar</h3>
        <p>
            El ciclo principal trabaja con 2 archivos: <strong>CtasxCobrar</strong> y <strong>Cobranza</strong>.
            La cartera maestra se administra desde la TAB <strong>Clientes Premium</strong>.
        </p>
        <div class="antay-step-grid">
            <div class="antay-step">
                <b>Paso 1</b>
                <span>Sube CtasxCobrar y Cobranza desde el panel lateral.</span>
            </div>
            <div class="antay-step">
                <b>Paso 2</b>
                <span>Procesa el ciclo y valida KPIs del Reporte General.</span>
            </div>
            <div class="antay-step">
                <b>Paso 3</b>
                <span>Gestiona clientes solo en la TAB Clientes Premium.</span>
            </div>
        </div>
    </div>
    """
