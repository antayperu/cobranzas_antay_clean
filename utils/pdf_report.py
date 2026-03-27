"""
utils/pdf_report.py
Generación de PDF ejecutivo para Comités de Directorio.
RC-FEAT-039 — Informe Gerencial

Uso:
    from utils.pdf_report import InformeGerencial
    pdf_bytes = InformeGerencial(
        cycle_id=cycle_id,
        funnel=funnel,
        criticos=criticos,
        aging=aging,
        gestiones=gestiones,
        empresa="DACTA S.A.C.",
    ).generate()
"""

from __future__ import annotations

import io
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Tipografía personalizada — Manrope + IBM Plex Sans (Antay Design System)
# Fallback graceful a Helvetica si los archivos TTF no están disponibles.
# ---------------------------------------------------------------------------
_FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")


def _reg(alias: str, filename: str) -> bool:
    path = os.path.join(_FONTS_DIR, filename)
    try:
        pdfmetrics.registerFont(TTFont(alias, path))
        return True
    except Exception:
        return False


_HAS_MANROPE = _reg("Manrope-Bold",           "Manrope-Bold.ttf")
_HAS_IBM     = _reg("IBMPlexSans",             "IBMPlexSans-Regular.ttf")
_reg("IBMPlexSans-SemiBold", "IBMPlexSans-SemiBold.ttf")

_F_HEADING = "Manrope-Bold"         if _HAS_MANROPE else "Helvetica-Bold"
_F_BODY    = "IBMPlexSans"          if _HAS_IBM     else "Helvetica"
_F_BOLD    = "IBMPlexSans-SemiBold" if _HAS_IBM     else "Helvetica-Bold"

# ---------------------------------------------------------------------------
# Paleta de colores (Antay Design System)
# ---------------------------------------------------------------------------
C_PRIMARY   = colors.HexColor("#0D3B66")
C_ACCENT    = colors.HexColor("#0B7285")
C_SUCCESS   = colors.HexColor("#2B8A3E")
C_WARNING   = colors.HexColor("#E67700")
C_DANGER    = colors.HexColor("#C92A2A")
C_BG        = colors.HexColor("#F1F5FB")
C_BORDER    = colors.HexColor("#D9E2EC")
C_TEXT      = colors.HexColor("#102A43")
C_MUTED     = colors.HexColor("#486581")
C_WHITE     = colors.white
C_LIGHT_ROW = colors.HexColor("#EEF4FB")

# Colores por nivel de riesgo de aging
RIESGO_COLORS = {
    "BAJO":    colors.HexColor("#D3F9D8"),
    "MEDIO":   colors.HexColor("#FFF3BF"),
    "ALTO":    colors.HexColor("#FFE8CC"),
    "CRÍTICO": colors.HexColor("#FFE3E3"),
}
RIESGO_TEXT = {
    "BAJO":    colors.HexColor("#2B8A3E"),
    "MEDIO":   colors.HexColor("#A05C00"),
    "ALTO":    colors.HexColor("#E67700"),
    "CRÍTICO": colors.HexColor("#C92A2A"),
}

# ---------------------------------------------------------------------------
# Estilos tipográficos
# ---------------------------------------------------------------------------
_BASE = getSampleStyleSheet()


def _style(name: str, parent: str = "Normal", **kwargs) -> ParagraphStyle:
    return ParagraphStyle(name=name, parent=_BASE[parent], **kwargs)


ST_TITLE       = _style("RC_Title",   "Normal",  fontSize=20, leading=24, textColor=C_PRIMARY,  fontName=_F_HEADING, alignment=TA_LEFT)
ST_SUBTITLE    = _style("RC_Sub",     "Normal",  fontSize=11, leading=14, textColor=C_MUTED,    fontName=_F_BODY,    alignment=TA_LEFT)
ST_SECTION     = _style("RC_Sec",     "Normal",  fontSize=13, leading=16, textColor=C_PRIMARY,  fontName=_F_HEADING, alignment=TA_LEFT, spaceAfter=4)
ST_BODY        = _style("RC_Body",    "Normal",  fontSize=9,  leading=12, textColor=C_TEXT,     fontName=_F_BODY)
ST_BODY_BOLD   = _style("RC_BodyB",   "Normal",  fontSize=9,  leading=12, textColor=C_TEXT,     fontName=_F_BOLD)
ST_SMALL       = _style("RC_Small",   "Normal",  fontSize=7.5, leading=10, textColor=C_MUTED,   fontName=_F_BODY)
ST_CENTER      = _style("RC_Center",  "Normal",  fontSize=9,  leading=12, textColor=C_TEXT,     fontName=_F_BODY,    alignment=TA_CENTER)
ST_CARD_VAL    = _style("RC_CardVal",  "Normal",  fontSize=13, leading=17, textColor=C_PRIMARY,  fontName=_F_HEADING, alignment=TA_CENTER)
ST_CARD_LBL    = _style("RC_CardLbl",  "Normal",  fontSize=7,  leading=9,  textColor=C_MUTED,    fontName=_F_BODY,    alignment=TA_CENTER)
ST_CARD_LBL_W  = _style("RC_CardLblW", "Normal",  fontSize=6.5, leading=8.5, textColor=C_WHITE,  fontName=_F_BOLD,    alignment=TA_CENTER)
ST_CARD_SUB    = _style("RC_CardSub",  "Normal",  fontSize=6.5, leading=9,  textColor=C_MUTED,   fontName=_F_BODY,    alignment=TA_CENTER)
ST_TH          = _style("RC_TH",      "Normal",  fontSize=8.5, leading=11, textColor=C_WHITE,   fontName=_F_BOLD,    alignment=TA_CENTER)
ST_TH_SM       = _style("RC_TH_SM",   "Normal",  fontSize=7,   leading=9,  textColor=C_WHITE,   fontName=_F_BOLD,    alignment=TA_CENTER)
ST_TD          = _style("RC_TD",      "Normal",  fontSize=8.5, leading=11, textColor=C_TEXT,    fontName=_F_BODY,    alignment=TA_LEFT)
ST_TD_RIGHT    = _style("RC_TDR",     "Normal",  fontSize=8.5, leading=11, textColor=C_TEXT,    fontName=_F_BODY,    alignment=TA_RIGHT)
ST_TD_CENTER   = _style("RC_TDC",     "Normal",  fontSize=8.5, leading=11, textColor=C_TEXT,    fontName=_F_BODY,    alignment=TA_CENTER)
ST_REC_CAT     = _style("RC_RecCat",  "Normal",  fontSize=10, leading=13, textColor=C_WHITE,    fontName=_F_HEADING)
ST_REC_TXT     = _style("RC_RecTxt",  "Normal",  fontSize=8.5, leading=12, textColor=C_TEXT,    fontName=_F_BODY)
ST_NOTE        = _style("RC_Note",    "Normal",  fontSize=7,  leading=9,  textColor=C_MUTED,    fontName=_F_BODY)
ST_CONFIDENTIAL= _style("RC_Conf",    "Normal",  fontSize=8,  leading=10, textColor=C_DANGER,   fontName=_F_BOLD,    alignment=TA_RIGHT)

# Estilos ejecutivos v2 — hero banner, section bands, KPI strip
ST_HERO_TITLE  = _style("RC_HeroTitle", "Normal", fontSize=22, leading=27, textColor=C_WHITE,                     fontName=_F_HEADING)
ST_HERO_SUB    = _style("RC_HeroSub",   "Normal", fontSize=11, leading=14, textColor=colors.HexColor("#A8D4F5"), fontName=_F_BODY)
ST_HERO_META   = _style("RC_HeroMeta",  "Normal", fontSize=8,  leading=11, textColor=colors.HexColor("#7CB9E8"), fontName=_F_BODY)
ST_SECTION_TH  = _style("RC_SecBand",   "Normal", fontSize=12, leading=15, textColor=C_WHITE,                     fontName=_F_HEADING)
ST_KPI_BIG_V   = _style("RC_KpiBigV",   "Normal", fontSize=18, leading=22, textColor=C_PRIMARY,                   fontName=_F_HEADING, alignment=TA_CENTER)
ST_KPI_BIG_L   = _style("RC_KpiBigL",   "Normal", fontSize=7,  leading=9,  textColor=C_MUTED,                     fontName=_F_BODY,    alignment=TA_CENTER)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_sol(v: float) -> str:
    if v == 0:
        return "S/ —"
    if abs(v) >= 1_000:
        return f"S/ {v:,.0f}"
    return f"S/ {v:,.2f}"


def _fmt_usd(v: float) -> str:
    if v == 0:
        return "—"
    return f"US$ {v:,.2f}"


def _pct(num: float, den: float, fmt: str = ".1f") -> str:
    if den <= 0:
        return "—"
    return f"{num / den * 100:{fmt}}%"


def _hr(color=C_BORDER, thickness=0.5) -> HRFlowable:
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=4)


def _spacer(h: float = 0.3) -> Spacer:
    return Spacer(1, h * cm)


_MESES_ES = {
    1: "enero",      2: "febrero",   3: "marzo",     4: "abril",
    5: "mayo",       6: "junio",     7: "julio",     8: "agosto",
    9: "septiembre", 10: "octubre",  11: "noviembre", 12: "diciembre",
}


def _fecha_es(dt: datetime) -> str:
    """Devuelve la fecha en español: '27 de marzo de 2026, 14:30 UTC'."""
    return f"{dt.day} de {_MESES_ES[dt.month]} de {dt.year}, {dt.strftime('%H:%M')} UTC"


def _section_title(text: str, page_w: float = None) -> List:
    if page_w is None:
        return [
            _hr(C_BORDER, 0.5),
            Paragraph(text, ST_SECTION),
            _hr(C_PRIMARY, 1.5),
        ]
    tbl = Table([[Paragraph(f"  {text}", ST_SECTION_TH)]], colWidths=[page_w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_PRIMARY),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("LINEBELOW",     (0, 0), (-1, -1), 3, C_ACCENT),
    ]))
    return [_spacer(0.2), tbl, _spacer(0.15)]


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class InformeGerencial:
    """Genera el PDF del Informe Gerencial para Comité de Directorio.

    Args:
        cycle_id:   ID del ciclo (ej: 'CIC-20260322-1256')
        funnel:     Dict de get_funnel_cobranza()
        criticos:   List de get_top_clientes_criticos()
        aging:      List de get_aging_distribution()
        gestiones:  Dict de get_resumen_gestiones_ciclo()
        empresa:    Nombre de la empresa cliente (aparece en el encabezado)
        secciones:         Conjunto de letras de secciones a incluir; None = todas
        docs_recuperados:  Lista de get_docs_recuperados_detalle() para Sección F
    """

    LOGO_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets", "logo_dacta_processed.png",
    )

    def __init__(
        self,
        cycle_id: str,
        funnel: Dict[str, Any],
        criticos: List[Dict[str, Any]],
        aging: List[Dict[str, Any]],
        gestiones: Dict[str, Any],
        empresa: str = "DACTA S.A.C.",
        secciones: Optional[set] = None,
        recovery: Optional[Dict[str, Any]] = None,
        scope: str = "activa",
        docs_recuperados: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.cycle_id         = cycle_id
        self.funnel           = funnel
        self.criticos         = criticos
        self.aging            = aging
        self.gestiones        = gestiones
        self.empresa          = empresa
        self.secciones        = secciones or {"A", "B", "C", "D", "E"}
        self.recovery         = recovery or {}
        self.scope            = scope   # "activa" | "general"
        self.docs_recuperados = docs_recuperados or []
        self.generated_at = datetime.now(timezone.utc)
        # Ancho disponible para contenido (A4 portrait con márgenes 1.8cm)
        self._page_w = A4[0] - 2 * 1.8 * cm

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def generate(self) -> bytes:
        """Genera el PDF y lo devuelve como bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=1.8 * cm,
            rightMargin=1.8 * cm,
            topMargin=3.2 * cm,   # espacio para el header fijo
            bottomMargin=2.0 * cm,
            title=f"Informe Gerencial — {self.cycle_id}",
            author=f"ReporteCobranzas · {self.empresa}",
            subject="Informe para Comité de Directorio",
        )

        story: List = []

        # Página de portada (título + resumen ejecutivo)
        story += self._portada()
        story.append(PageBreak())

        # Secciones seleccionadas
        if "A" in self.secciones:
            story += self._seccion_a_semaforo()
            story.append(_spacer(0.5))

        if "B" in self.secciones:
            story += self._seccion_b_aging()
            story.append(_spacer(0.5))

        if "C" in self.secciones:
            story += self._seccion_c_criticos()
            story.append(_spacer(0.5))

        if "D" in self.secciones:
            story += self._seccion_d_gestiones()
            story.append(_spacer(0.5))

        if "E" in self.secciones:
            story += self._seccion_e_recomendaciones()
            story.append(_spacer(0.5))

        if "F" in self.secciones:
            story += self._seccion_f_recuperados()

        # Nota al pie del informe
        story.append(_spacer(0.8))
        story.append(_hr())
        story.append(Paragraph(
            "⚠️ Los montos recuperados reflejan acuerdos firmados y cuotas registradas como pagadas en el CRM. "
            "Para conciliación exacta con caja, contrastar con el sistema contable de la empresa.",
            ST_NOTE,
        ))
        story.append(Paragraph(
            f"Informe generado automáticamente el {self.generated_at.strftime('%d/%m/%Y a las %H:%M UTC')} "
            f"por {self.empresa}. "
            f"Ciclo: {self.cycle_id}. CONFIDENCIAL.",
            ST_NOTE,
        ))

        doc.build(story, onFirstPage=self._draw_header_footer, onLaterPages=self._draw_header_footer)
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # Header y footer de página
    # ------------------------------------------------------------------

    def _draw_header_footer(self, canvas_obj, doc) -> None:
        canvas_obj.saveState()
        page_w, page_h = A4

        # --- Header ---
        # Línea superior azul
        canvas_obj.setFillColor(C_PRIMARY)
        canvas_obj.rect(0, page_h - 1.8 * cm, page_w, 1.8 * cm, fill=1, stroke=0)

        # Logo
        if os.path.exists(self.LOGO_PATH):
            try:
                canvas_obj.drawImage(
                    self.LOGO_PATH,
                    0.5 * cm, page_h - 1.6 * cm,
                    width=1.4 * cm, height=1.4 * cm,
                    preserveAspectRatio=True, mask="auto",
                )
            except Exception:
                pass

        # Empresa + título
        canvas_obj.setFillColor(C_WHITE)
        canvas_obj.setFont(_F_BOLD, 10)
        canvas_obj.drawString(2.2 * cm, page_h - 0.9 * cm, self.empresa)
        canvas_obj.setFont(_F_BODY, 8)
        canvas_obj.drawString(2.2 * cm, page_h - 1.4 * cm, "Informe Gerencial para Comité de Directorio")

        # CONFIDENCIAL
        canvas_obj.setFillColor(colors.HexColor("#FFD700"))
        canvas_obj.setFont(_F_BOLD, 8)
        canvas_obj.drawRightString(page_w - 0.5 * cm, page_h - 0.85 * cm, "CONFIDENCIAL")
        canvas_obj.setFillColor(C_WHITE)
        canvas_obj.setFont(_F_BODY, 7)
        canvas_obj.drawRightString(page_w - 0.5 * cm, page_h - 1.35 * cm,
                                   f"Ciclo: {self.cycle_id}")

        # --- Footer ---
        canvas_obj.setFillColor(C_BG)
        canvas_obj.rect(0, 0, page_w, 1.4 * cm, fill=1, stroke=0)
        canvas_obj.setFillColor(C_PRIMARY)
        canvas_obj.rect(0, 1.35 * cm, page_w, 0.05 * cm, fill=1, stroke=0)

        canvas_obj.setFillColor(C_MUTED)
        canvas_obj.setFont(_F_BODY, 7)
        canvas_obj.drawString(
            0.5 * cm, 0.55 * cm,
            f"{self.empresa} — Confidencial  |  {self.generated_at.strftime('%d/%m/%Y %H:%M UTC')}",
        )
        canvas_obj.drawRightString(
            page_w - 0.5 * cm, 0.55 * cm,
            f"Página {canvas_obj.getPageNumber()}",
        )

        canvas_obj.restoreState()

    # ------------------------------------------------------------------
    # Portada
    # ------------------------------------------------------------------

    def _portada(self) -> List:
        story = []

        # --- Datos del ciclo (necesarios para hero y KPI strip) ---
        funnel = self.funnel
        cartera = funnel.get("cartera", 0)
        cartera_total = funnel.get("cartera_total", cartera)
        alcanzados = funnel.get("alcanzados", 0)
        sin_contactar = funnel.get("sin_contactar", 0)
        con_respuesta = funnel.get("con_respuesta", 0)

        aging = self.aging or []
        total_sol = sum(b.get("saldo_sol", 0) for b in aging)
        total_usd = sum(b.get("saldo_usd", 0) for b in aging)
        total_clientes = sum(b.get("clientes", 0) for b in aging)

        cobertura_pct_val = alcanzados / cartera if cartera > 0 else 0.0
        tasa_cobertura_p = f"{cobertura_pct_val * 100:.0f}%" if cartera > 0 else "—"

        # --- Hero banner ---
        fecha_gen = self.generated_at.strftime("%d/%m/%Y  %H:%M UTC")
        scope_hero = (
            "🎯 Cartera Activa — solo clientes notificables (Envío Email = SI)"
            if self.scope == "activa"
            else "📋 Cartera General — todos los clientes con deuda"
        )
        hero_content = Table([
            [Paragraph(self.empresa, ST_HERO_TITLE)],
            [Paragraph("Informe Gerencial para Comité de Directorio", ST_HERO_SUB)],
            [Paragraph(scope_hero, ST_HERO_META)],
            [Spacer(1, 0.10 * cm)],
            [Paragraph(
                f"Ciclo analizado: {self.cycle_id}  ·  Generado: {fecha_gen}  ·  CONFIDENCIAL",
                ST_HERO_META,
            )],
        ], colWidths=[self._page_w - 1.5 * cm])
        hero_content.setStyle(TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        hero_banner = Table([[hero_content]], colWidths=[self._page_w])
        hero_banner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C_PRIMARY),
            ("TOPPADDING",    (0, 0), (-1, -1), 18),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
            ("LEFTPADDING",   (0, 0), (-1, -1), 16),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
            ("LINEBELOW",     (0, 0), (-1, -1), 4, C_ACCENT),
        ]))
        story.append(hero_banner)
        story.append(_spacer(0.4))

        # --- KPI strip: 4 métricas clave al primer vistazo ---
        kpi_def = [
            (_fmt_sol(total_sol),  "CARTERA VENCIDA TOTAL",      C_PRIMARY),
            (tasa_cobertura_p,     "COBERTURA DEL CICLO",         C_ACCENT if cobertura_pct_val >= 0.7 else C_WARNING),
            (str(con_respuesta),   "CON RESULTADO REGISTRADO",    C_SUCCESS),
            (
                str(sin_contactar),
                "SIN CONTACTO — ALERTA" if sin_contactar > 0 else "SIN CONTACTO",
                C_DANGER if sin_contactar > 0 else C_SUCCESS,
            ),
        ]
        strip_cells = []
        cell_w = self._page_w / 4 - 0.4 * cm
        for kpi_val, kpi_lbl, kpi_col in kpi_def:
            cell_tbl = Table([
                [Paragraph(kpi_val, ST_KPI_BIG_V)],
                [Spacer(1, 0.05 * cm)],
                [Paragraph(kpi_lbl, ST_KPI_BIG_L)],
            ], colWidths=[cell_w])
            cell_tbl.setStyle(TableStyle([
                ("TOPPADDING",    (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING",   (0, 0), (-1, -1), 4),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
                ("LINEABOVE",     (0, 0), (-1, 0),  3, kpi_col),
                ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
                ("BACKGROUND",    (0, 0), (-1, -1), C_WHITE),
            ]))
            strip_cells.append(cell_tbl)

        kpi_strip = Table(
            [strip_cells],
            colWidths=[self._page_w / 4] * 4,
            hAlign="LEFT",
        )
        kpi_strip.setStyle(TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(kpi_strip)
        story.append(_spacer(0.5))

        scope_label = (
            "Cartera Activa — solo clientes notificables (Envío Email = SI)"
            if self.scope == "activa"
            else "Cartera General — todos los clientes con deuda real"
        )
        resumen_data = [
            ["Empresa", self.empresa],
            ["Ciclo analizado", self.cycle_id],
            ["Fecha de generación", _fecha_es(self.generated_at)],
            ["Alcance del informe", scope_label],
            ["Total cartera del ciclo", f"{cartera_total} clientes"],
            ["Cartera activa (notificable)", f"{cartera} clientes"],
            ["Saldo total en Soles", _fmt_sol(total_sol)],
            ["Saldo total en Dólares", _fmt_usd(total_usd)],
            ["Clientes alcanzados", f"{alcanzados} ({_pct(alcanzados, cartera)} de cartera)"],
            ["Sin ningún contacto", f"{sin_contactar} clientes {'⚠️' if sin_contactar > 0 else '✅'}"],
            ["Con resultado registrado", f"{con_respuesta} clientes"],
        ]

        tbl = Table(resumen_data, colWidths=[5.5 * cm, self._page_w - 5.5 * cm])
        tbl.setStyle(TableStyle([
            ("FONTNAME",    (0, 0), (-1, -1), _F_BODY),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("FONTNAME",    (0, 0), (0, -1),  _F_BOLD),
            ("TEXTCOLOR",   (0, 0), (0, -1),  C_PRIMARY),
            ("TEXTCOLOR",   (1, 0), (1, -1),  C_TEXT),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_WHITE, C_LIGHT_ROW]),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("BOX",         (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LINEBELOW",   (0, 0), (-1, -1), 0.25, C_BORDER),
        ]))
        story.append(tbl)
        story.append(_spacer(0.5))
        story.append(Paragraph("CONFIDENCIAL — Uso exclusivo del Directorio y Alta Gerencia", ST_CONFIDENTIAL))
        return story

    # ------------------------------------------------------------------
    # Sección A — Semáforo Ejecutivo
    # ------------------------------------------------------------------

    def _seccion_a_semaforo(self) -> List:
        story: List = []
        story += _section_title("A.  Semáforo Ejecutivo", self._page_w)

        # Badge de alcance bajo el título de sección
        scope_badge = (
            "Vista: Cartera Activa — solo clientes notificables (Envío Email = SI)"
            if self.scope == "activa"
            else "Vista: Cartera General — todos los clientes con deuda real"
        )
        story.append(Paragraph(scope_badge, ST_SMALL))
        story.append(_spacer(0.2))

        funnel = self.funnel
        gestiones = self.gestiones or {}
        aging = self.aging or []

        # Para scope "activa": usar "cartera" (notificables)
        # Para scope "general": usar "cartera_total" (todos con deuda)
        cartera = (
            funnel.get("cartera", 0)
            if self.scope == "activa"
            else funnel.get("cartera_total", 0)
        )
        alcanzados = funnel.get("alcanzados", 0)
        # sin_contactar solo es operativamente válido en scope "activa"
        sin_contactar = funnel.get("sin_contactar", 0) if self.scope == "activa" else 0
        con_respuesta = funnel.get("con_respuesta", 0)

        total_sol = sum(b.get("saldo_sol", 0) for b in aging)
        total_usd = sum(b.get("saldo_usd", 0) for b in aging)

        acuerdos_activos = gestiones.get("acuerdos_activos", 0)
        acuerdos_monto   = gestiones.get("acuerdos_monto", 0.0)
        legal            = gestiones.get("legal", 0)

        # Recuperacion real desde resumen_ciclo (comparacion CxC entre ciclos)
        rec_sol      = self.recovery.get("monto_recuperado_sol", 0.0)
        rec_usd      = self.recovery.get("monto_recuperado_usd", 0.0)
        docs_rec     = self.recovery.get("docs_recuperados", 0)
        docs_amort   = self.recovery.get("docs_amortizados", 0)
        tasa_recup   = self.recovery.get("tasa_recuperacion", 0.0)
        tiene_ant    = self.recovery.get("tiene_anterior", False)

        saldo_pendiente_sol = max(total_sol - rec_sol, 0.0)
        saldo_pendiente_usd = max(total_usd - rec_usd, 0.0)

        tasa_cobertura = f"{alcanzados / cartera * 100:.0f}%" if cartera > 0 else "—"
        tasa_gestion   = f"{con_respuesta / alcanzados * 100:.0f}%" if alcanzados > 0 else "—"

        def _card(label: str, value: str, sub: str, color: Any) -> Table:
            pad = 0.3 * cm
            inner = [
                [Paragraph(label, ST_CARD_LBL)],
                [Paragraph(value, ST_CARD_VAL)],
                [Paragraph(sub,   ST_CARD_SUB)],
            ]
            t = Table(inner, colWidths=[self._page_w / 4 - 0.35 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), C_WHITE),
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING",   (0, 0), (-1, -1), pad),
                ("RIGHTPADDING",  (0, 0), (-1, -1), pad),
                ("TOPPADDING",    (0, 0), (0, 0),   pad),       # espacio extra arriba del label
                ("BOTTOMPADDING", (0, 2), (-1, 2),  pad),       # espacio extra abajo del sub
                ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
                ("LINEABOVE",     (0, 0), (-1, 0),  4,   color),
            ]))
            return t

        # --- FRD v4.0 Sección A — 4 tarjetas exactas ---
        # Tarjeta 1: Cartera Vencida Total — mostrar nro de documentos por moneda
        total_docs_sol = sum(b.get("docs_sol", 0) for b in aging)
        total_docs_usd = sum(b.get("docs_usd", 0) for b in aging)
        _sub1_parts = []
        if total_docs_sol > 0:
            _sub1_parts.append(f"{total_docs_sol} docs S/")
        if total_docs_usd > 0:
            _sub1_parts.append(f"{total_docs_usd} docs US$")
        sub1 = "  ·  ".join(_sub1_parts) if _sub1_parts else f"{cartera} clientes"

        # Tarjeta 1: Cartera Vencida Total — valor con salto de línea si hay ambas monedas
        val1 = _fmt_sol(total_sol)
        if total_usd > 0:
            val1 += f"<br/>{_fmt_usd(total_usd)}"

        # Tarjeta 2: Recuperado en el Período (fuente: resumen_ciclo, diferencia CxC)
        # monto_recuperado_sol ya es combinado (docs completos + amortizaciones parciales)
        if not tiene_ant:
            val2 = _fmt_sol(0)
            sub2 = "Sin ciclo anterior  ·  Meta: 55%"
        elif rec_sol > 0 or rec_usd > 0:
            val2 = _fmt_sol(rec_sol)
            if rec_usd > 0:
                val2 += f"<br/>{_fmt_usd(rec_usd)}"
            if docs_amort > 0:
                sub2 = f"{docs_rec} docs + {docs_amort} amortiz.<br/>Tasa: {tasa_recup:.1f}%  ·  Meta: 55%"
            else:
                sub2 = f"{docs_rec} docs<br/>Tasa: {tasa_recup:.1f}%  ·  Meta: 55%"
        else:
            val2 = _fmt_sol(0)
            sub2 = f"Tasa: 0.0%  ·  Meta: 55%  ·  {docs_rec} docs"

        # Tarjeta 3: Saldo Pendiente (cartera - recuperado, por moneda)
        val3 = _fmt_sol(saldo_pendiente_sol) if saldo_pendiente_sol > 0 else _fmt_sol(total_sol)
        if saldo_pendiente_usd > 0:
            val3 += f"<br/>{_fmt_usd(saldo_pendiente_usd)}"
        sub3_parts = [f"{cartera} clientes"]
        if legal > 0:
            sub3_parts.append(f"{legal} en Legal")
        sub3 = "  ·  ".join(sub3_parts)

        # Tarjeta 4: En Acuerdos de Pago
        if acuerdos_monto > 0:
            val4 = _fmt_sol(acuerdos_monto)
            sub4 = f"{acuerdos_activos} acuerdo(s) activo(s)"
        elif acuerdos_activos > 0:
            val4 = f"{acuerdos_activos} acuerdo(s)"
            sub4 = "Monto por registrar"
        else:
            val4 = "Sin acuerdos"
            sub4 = "0 acuerdos activos"

        cards = [
            _card("CARTERA VENCIDA",  val1,  sub1,  C_PRIMARY),
            _card("RECUPERADO",       val2,  sub2,  C_SUCCESS),
            _card("SALDO PENDIENTE",  val3,  sub3,  C_WARNING),
            _card("EN ACUERDOS",      val4,  sub4,  C_ACCENT),
        ]

        cards_row = Table(
            [cards],
            colWidths=[self._page_w / 4] * 4,
            hAlign="LEFT",
        )
        cards_row.setStyle(TableStyle([
            ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",  (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(cards_row)

        # Indicadores secundarios
        story.append(_spacer(0.4))
        kpi_data = [
            [
                Paragraph("Indicador", ST_TH),
                Paragraph("Valor", ST_TH),
                Paragraph("Indicador", ST_TH),
                Paragraph("Valor", ST_TH),
            ],
            [
                Paragraph("Cobertura de cartera", ST_TD),
                Paragraph(tasa_cobertura, ST_TD_CENTER),
                Paragraph("Efectividad de gestión", ST_TD),
                Paragraph(tasa_gestion, ST_TD_CENTER),
            ],
            [
                Paragraph("Clientes sin contacto", ST_TD),
                Paragraph(
                    f"{'⚠️ ' if sin_contactar > 0 else '✅ '}{sin_contactar}",
                    ParagraphStyle("rc_kpi_alert", parent=ST_TD_CENTER,
                                   textColor=C_DANGER if sin_contactar > 0 else C_SUCCESS),
                ),
                Paragraph("Cuotas cobradas S/", ST_TD),
                Paragraph(_fmt_sol(rec_sol) if rec_sol > 0 else "Sin registros", ST_TD_CENTER),
            ],
        ]
        w = self._page_w / 4
        _kpi_style_cmds = [
            ("BACKGROUND",    (0, 0), (-1, 0),  C_PRIMARY),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_LIGHT_ROW]),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.25, C_BORDER),
            ("LINEBEFORE",    (2, 0), (2, -1),  0.5,  C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]
        if sin_contactar > 0:
            _kpi_style_cmds.append(("BACKGROUND", (1, 2), (1, 2), colors.HexColor("#FFE3E3")))
        kpi_tbl = Table(kpi_data, colWidths=[w * 1.5, w * 0.5, w * 1.5, w * 0.5])
        kpi_tbl.setStyle(TableStyle(_kpi_style_cmds))
        story.append(kpi_tbl)
        return story

    # ------------------------------------------------------------------
    # Sección B — Distribución por Antigüedad de Deuda (Aging)
    # ------------------------------------------------------------------

    def _seccion_b_aging(self) -> List:
        story: List = []
        story += _section_title("B.  Distribución de Cartera por Antigüedad de Deuda", self._page_w)
        story.append(_spacer(0.2))

        aging = self.aging or []
        total_clientes = sum(b.get("clientes", 0) for b in aging)
        total_sol = sum(b.get("saldo_sol", 0) for b in aging)
        total_usd = sum(b.get("saldo_usd", 0) for b in aging)

        total_docs = sum(b.get("documentos", 0) for b in aging)

        # 8 columnas — anchos calibrados para que los encabezados no desborden
        w = self._page_w
        col_w = [w*0.21, w*0.08, w*0.07, w*0.07, w*0.16, w*0.08, w*0.13, w*0.20]

        header = [
            Paragraph("Segmento",  ST_TH),
            Paragraph("Clientes",  ST_TH_SM),
            Paragraph("% Cli.",    ST_TH_SM),
            Paragraph("Docs",      ST_TH_SM),
            Paragraph("Saldo S/",  ST_TH),
            Paragraph("%",         ST_TH_SM),
            Paragraph("Saldo US$", ST_TH),
            Paragraph("Riesgo",    ST_TH_SM),
        ]

        rows = [header]
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
            ("BOX",        (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LINEBELOW",  (0, 0), (-1, -1), 0.25, C_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]

        for i, b in enumerate(aging, start=1):
            riesgo = b.get("riesgo", "")
            bg = RIESGO_COLORS.get(riesgo, C_WHITE)
            tc = RIESGO_TEXT.get(riesgo, C_TEXT)
            docs_b = b.get("documentos", b.get("docs_sol", 0) + b.get("docs_usd", 0))
            row = [
                Paragraph(b.get("segmento", "—"), ST_TD),
                Paragraph(str(b.get("clientes", 0)), ST_TD_CENTER),
                Paragraph(_pct(b.get("clientes", 0), total_clientes), ST_TD_CENTER),
                Paragraph(str(docs_b), ST_TD_CENTER),
                Paragraph(_fmt_sol(b.get("saldo_sol", 0)), ST_TD_RIGHT),
                Paragraph(f"{b.get('pct_sol', 0):.1f}%", ST_TD_CENTER),
                Paragraph(_fmt_usd(b.get("saldo_usd", 0)), ST_TD_RIGHT),
                Paragraph(riesgo, ParagraphStyle("rc_riesgo", parent=ST_TD_CENTER, textColor=tc, fontName=_F_BOLD)),
            ]
            rows.append(row)
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

        # Fila totales
        rows.append([
            Paragraph("<b>TOTAL</b>", ST_TD_CENTER),
            Paragraph(f"<b>{total_clientes}</b>", ST_TD_CENTER),
            Paragraph("<b>100%</b>", ST_TD_CENTER),
            Paragraph(f"<b>{total_docs}</b>", ST_TD_CENTER),
            Paragraph(f"<b>{_fmt_sol(total_sol)}</b>", ST_TD_RIGHT),
            Paragraph("<b>100%</b>", ST_TD_CENTER),
            Paragraph(f"<b>{_fmt_usd(total_usd)}</b>", ST_TD_RIGHT),
            Paragraph("", ST_TD),
        ])
        style_cmds.append(("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), C_BG))
        style_cmds.append(("FONTNAME",   (0, len(rows) - 1), (-1, len(rows) - 1), _F_BOLD))

        tbl = Table(rows, colWidths=col_w)
        tbl.setStyle(TableStyle(style_cmds))
        story.append(tbl)

        # Leyenda de acciones
        story.append(_spacer(0.3))
        acciones = [
            ("🟢 0–14 días",  "Primer aviso preventivo por WhatsApp o Email"),
            ("🟡 15–30 días", "Recordatorio + llamada si no responde en 48h"),
            ("🟠 31–60 días", "Aviso firme + oferta de acuerdo de pago"),
            ("🔴 +60 días",   "Derivar a Legal de forma inmediata"),
        ]
        acc_rows = [[Paragraph("<b>Segmento</b>", ST_BODY_BOLD), Paragraph("<b>Acción recomendada</b>", ST_BODY_BOLD)]]
        for seg, acc in acciones:
            acc_rows.append([Paragraph(seg, ST_BODY), Paragraph(acc, ST_BODY)])
        acc_tbl = Table(acc_rows, colWidths=[4.5 * cm, self._page_w - 4.5 * cm])
        acc_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_BG),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_LIGHT_ROW]),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.25, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        story.append(acc_tbl)
        return story

    # ------------------------------------------------------------------
    # Sección C — Clientes Críticos
    # ------------------------------------------------------------------

    def _seccion_c_criticos(self) -> List:
        story: List = []
        story += _section_title("C.  Clientes Críticos — Requieren Decisión del Directorio", self._page_w)
        story.append(_spacer(0.2))

        # Filtrar: mora > 60 días, sin acuerdo activo, ordenar por saldo desc
        criticos_alerta = [
            c for c in (self.criticos or [])
            if int(c.get("dias_mora_max", 0)) > 60
        ][:8]  # máximo 8 en el informe

        if not criticos_alerta:
            story.append(Paragraph(
                "✅ Sin clientes con mora crítica (>60 días) en este ciclo.",
                ST_BODY,
            ))
            return story

        # 8 columnas — anchos calibrados para caber en A4
        w = self._page_w
        col_w = [w*0.04, w*0.25, w*0.08, w*0.12, w*0.10, w*0.06, w*0.07, w*0.28]

        header = [
            Paragraph("#",             ST_TH_SM),
            Paragraph("Cliente",       ST_TH),
            Paragraph("Días mora",     ST_TH_SM),
            Paragraph("Saldo S/",      ST_TH),
            Paragraph("Saldo US$",     ST_TH),
            Paragraph("Docs",          ST_TH_SM),
            Paragraph("Gest.",         ST_TH_SM),
            Paragraph("Recomendación", ST_TH),
        ]

        rows = [header]
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
            ("BOX",        (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LINEBELOW",  (0, 0), (-1, -1), 0.25, C_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]

        for i, c in enumerate(criticos_alerta, start=1):
            mora      = int(c.get("dias_mora_max", 0))
            gest      = int(c.get("gestiones_count", 0))
            docs_c    = int(c.get("docs_count", c.get("docs_sol", 0) + c.get("docs_usd", 0)))
            saldo_sol = float(c.get("saldo_sol", 0))
            saldo_usd = float(c.get("saldo_usd", 0))
            nombre    = str(c.get("nombre") or c.get("cliente_id") or "—")[:40]
            rec = _accion_pdf(mora, gest)
            bg = RIESGO_COLORS["CRÍTICO"] if mora > 90 else RIESGO_COLORS["ALTO"]
            row = [
                Paragraph(str(i), ST_TD_CENTER),
                Paragraph(nombre, ST_TD),
                Paragraph(f"{mora}d", ST_TD_CENTER),
                Paragraph(_fmt_sol(saldo_sol), ST_TD_RIGHT),
                Paragraph(_fmt_usd(saldo_usd) if saldo_usd > 0 else "—", ST_TD_RIGHT),
                Paragraph(str(docs_c), ST_TD_CENTER),
                Paragraph(str(gest), ST_TD_CENTER),
                Paragraph(rec, ST_TD),
            ]
            rows.append(row)
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

        tbl = Table(rows, colWidths=col_w)
        tbl.setStyle(TableStyle(style_cmds))
        story.append(tbl)
        return story

    # ------------------------------------------------------------------
    # Sección D — Resumen de Gestiones del Período
    # ------------------------------------------------------------------

    def _seccion_d_gestiones(self) -> List:
        story: List = []
        story += _section_title("D.  Resumen de Gestiones del Período", self._page_w)
        story.append(_spacer(0.2))

        g = self.gestiones or {}

        wa    = g.get("wa_envios", 0)
        email = g.get("email_envios", 0)
        llam  = g.get("llamadas", 0)
        vis   = g.get("visitas", 0)
        notas = g.get("notas", 0)
        otros = g.get("otros", 0)
        legal = g.get("legal", 0)
        exit_ = g.get("exitosos", 0)
        ac_n  = g.get("acuerdos_count", 0)
        ac_m  = g.get("acuerdos_monto", 0.0)
        ac_a  = g.get("acuerdos_activos", 0)
        cuot  = g.get("cuotas_pagadas_monto", 0.0)

        total_contacto = wa + email + llam + vis
        total_manual   = llam + vis + notas + otros

        canal_data = [
            [Paragraph("<b>Canal / Actividad</b>", ST_BODY_BOLD), Paragraph("<b>Registros</b>", ST_BODY_BOLD)],
            [Paragraph("📱 WhatsApp enviados (masivo)", ST_BODY), Paragraph(str(wa), ST_BODY_BOLD)],
            [Paragraph("📧 Emails enviados", ST_BODY), Paragraph(str(email), ST_BODY_BOLD)],
            [Paragraph("📞 Llamadas registradas", ST_BODY), Paragraph(str(llam), ST_BODY_BOLD)],
            [Paragraph("🏢 Visitas presenciales", ST_BODY), Paragraph(str(vis), ST_BODY_BOLD)],
            [Paragraph("📝 Notas y observaciones", ST_BODY), Paragraph(str(notas), ST_BODY_BOLD)],
            [Paragraph("⚖️ Derivados a Legal", ST_BODY), Paragraph(
                f"⚠️  {legal}" if legal > 0 else str(legal),
                ParagraphStyle("rc_legal", parent=ST_BODY_BOLD,
                               textColor=C_DANGER if legal > 0 else C_TEXT),
            )],
            [Paragraph("✅ Con resultado exitoso / promesa", ST_BODY), Paragraph(str(exit_), ST_BODY_BOLD)],
        ]

        acuerdo_data = [
            [Paragraph("<b>Acuerdos de Pago</b>", ST_BODY_BOLD), Paragraph("<b>Valor</b>", ST_BODY_BOLD)],
            [Paragraph("Acuerdos firmados en el ciclo", ST_BODY), Paragraph(str(ac_n), ST_BODY_BOLD)],
            [Paragraph("Acuerdos activos vigentes", ST_BODY), Paragraph(str(ac_a), ST_BODY_BOLD)],
            [Paragraph("Monto comprometido S/", ST_BODY), Paragraph(_fmt_sol(ac_m), ST_BODY_BOLD)],
            [Paragraph("Cuotas pagadas registradas S/", ST_BODY), Paragraph(
                _fmt_sol(cuot) if cuot > 0 else "Sin registros aún",
                ST_BODY_BOLD,
            )],
        ]

        half_w = (self._page_w - 0.4 * cm) / 2
        tbl_style = TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_BG),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_LIGHT_ROW]),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.25, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 7),
            ("ALIGN",         (1, 0), (1, -1),  "RIGHT"),
            ("RIGHTPADDING",  (1, 0), (1, -1),  10),
        ])

        t_canal   = Table(canal_data,   colWidths=[half_w * 0.78, half_w * 0.22])
        t_acuerdo = Table(acuerdo_data, colWidths=[half_w * 0.78, half_w * 0.22])
        t_canal.setStyle(tbl_style)
        t_acuerdo.setStyle(tbl_style)

        two_col = Table(
            [[t_canal, t_acuerdo]],
            colWidths=[half_w, half_w],
            hAlign="LEFT",
        )
        two_col.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, -1),  int(0.4 * cm)),
        ]))
        story.append(two_col)
        return story

    # ------------------------------------------------------------------
    # Sección E — Recomendaciones Automáticas
    # ------------------------------------------------------------------

    def _seccion_e_recomendaciones(self) -> List:
        story: List = []
        story += _section_title("E.  Recomendaciones para el Directorio", self._page_w)
        story.append(_spacer(0.2))

        funnel = self.funnel or {}
        g      = self.gestiones or {}
        aging  = self.aging or []

        cartera       = funnel.get("cartera", 0)
        sin_contactar = funnel.get("sin_contactar", 0)
        alcanzados    = funnel.get("alcanzados", 0)
        con_respuesta = funnel.get("con_respuesta", 0)
        legal         = g.get("legal", 0)
        acuerdos_n    = g.get("acuerdos_count", 0)
        exitosos      = g.get("exitosos", 0)
        critico_sol   = next((b["saldo_sol"] for b in aging if b.get("riesgo") == "CRÍTICO"), 0.0)
        critico_cl    = next((b["clientes"]  for b in aging if b.get("riesgo") == "CRÍTICO"), 0)
        alto_cl       = next((b["clientes"]  for b in aging if b.get("riesgo") == "ALTO"), 0)

        recs = []

        # Acción inmediata: clientes críticos sin acuerdo
        criticos_sin_acuerdo = [
            c for c in (self.criticos or [])
            if int(c.get("dias_mora_max", 0)) > 60
        ]
        if criticos_sin_acuerdo:
            nombres = ", ".join(
                str(c.get("nombre") or c.get("cliente_id", "—"))[:30]
                for c in criticos_sin_acuerdo[:3]
            )
            recs.append((
                "🚨  ACCIÓN INMEDIATA",
                C_DANGER,
                (
                    f"{len(criticos_sin_acuerdo)} cliente(s) con mora superior a 60 días representan "
                    f"{_fmt_sol(critico_sol)} en riesgo de incobrabilidad. "
                    f"Clientes prioritarios: {nombres}{'...' if len(criticos_sin_acuerdo) > 3 else ''}. "
                    "Se recomienda iniciar proceso legal o negociación formal urgente."
                ),
            ))

        # Atención prioritaria: sin contacto
        if sin_contactar > 0:
            recs.append((
                "⚠️   ATENCIÓN PRIORITARIA",
                C_WARNING,
                (
                    f"{sin_contactar} cliente(s) de la cartera activa aún no han sido contactados en este ciclo. "
                    "Cada día sin gestión aumenta el riesgo de incobrabilidad. "
                    "Asignar responsable de seguimiento esta semana."
                ),
            ))

        # Mejora: cobertura baja
        cobertura_pct = alcanzados / cartera if cartera > 0 else 0
        if cobertura_pct < 0.7 and cartera > 0:
            recs.append((
                "📊  OPORTUNIDAD DE MEJORA",
                C_ACCENT,
                (
                    f"La cobertura de gestión actual es del {cobertura_pct * 100:.0f}% "
                    f"({alcanzados} de {cartera} clientes). "
                    "Meta recomendada: ≥ 80%. Considerar aumentar frecuencia de envíos o asignar más gestores."
                ),
            ))
        elif alto_cl > 0:
            recs.append((
                "📊  OPORTUNIDAD DE MEJORA",
                C_ACCENT,
                (
                    f"{alto_cl} cliente(s) en segmento de riesgo ALTO (31–60 días) aún no han llegado a la mora crítica. "
                    "Contacto inmediato con oferta de acuerdo de pago puede prevenir escalamiento a Legal."
                ),
            ))

        # Logro destacado
        if acuerdos_n > 0:
            recs.append((
                "✅  LOGRO DESTACADO",
                C_SUCCESS,
                (
                    f"Se firmaron {acuerdos_n} acuerdo(s) de pago en este ciclo. "
                    f"{exitosos} cliente(s) confirmaron compromiso de pago (EXITOSO / PROMESA). "
                    "El seguimiento oportuno de cuotas es clave para materializar la recuperación."
                ),
            ))
        elif exitosos > 0:
            recs.append((
                "✅  LOGRO DESTACADO",
                C_SUCCESS,
                (
                    f"{exitosos} cliente(s) confirmaron intención de pago en este ciclo. "
                    "Priorizar el cierre formal con acuerdo de pago para asegurar el compromiso."
                ),
            ))
        else:
            if cobertura_pct >= 0.8:
                recs.append((
                    "✅  LOGRO DESTACADO",
                    C_SUCCESS,
                    (
                        f"Se alcanzó una cobertura del {cobertura_pct * 100:.0f}% de la cartera en este ciclo. "
                        "El equipo de cobranzas logró contactar a la mayoría de clientes con deuda activa."
                    ),
                ))

        if not recs:
            story.append(Paragraph(
                "Sin recomendaciones automáticas generadas para este ciclo. Revisar manualmente el estado de la cartera.",
                ST_BODY,
            ))
            return story

        for cat, color, texto in recs:
            cat_tbl = Table(
                [[Paragraph(cat, ST_REC_CAT)]],
                colWidths=[self._page_w],
            )
            cat_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), color),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ]))
            txt_tbl = Table(
                [[Paragraph(texto, ST_REC_TXT)]],
                colWidths=[self._page_w],
            )
            txt_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(
                    "#FFF5F5" if color == C_DANGER else
                    "#FFFBEC" if color == C_WARNING else
                    "#F0FFF4" if color == C_SUCCESS else
                    "#E3FAFC"
                )),
                ("TOPPADDING",    (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
                ("BOX",           (0, 0), (-1, -1), 0.5, color),
            ]))
            story.append(KeepTogether([cat_tbl, txt_tbl]))
            story.append(_spacer(0.2))

        return story

    # ------------------------------------------------------------------
    # Sección F — Sustento de Recuperados (RC-BUG-070)
    # ------------------------------------------------------------------

    def _seccion_f_recuperados(self) -> List:
        """Tabla de documentos cobrados total o parcialmente entre ciclos."""
        story: List = []
        C_COMPL  = C_SUCCESS   # verde para docs completos
        C_AMORT  = C_ACCENT    # teal para amortizaciones

        # Cabecera de sección
        story += _section_title(
            "F.  Sustento — Recuperado en el Período",
            self._page_w,
        )
        story.append(_spacer(0.3))

        cycle_ant = self.recovery.get("cycle_id_anterior")
        scope_label = "Cartera Activa" if self.scope == "activa" else "Cartera General"
        nota = (
            f"Documentos del ciclo anterior ({cycle_ant or 'N/D'}) cobrados total o "
            f"parcialmente en {self.cycle_id} · Vista: {scope_label}"
        )
        story.append(Paragraph(nota, ST_SMALL))
        story.append(_spacer(0.3))

        docs = self.docs_recuperados
        if not docs:
            story.append(Paragraph(
                "Sin documentos recuperados para mostrar. "
                "Verifique que exista un ciclo anterior y que la migración 104 esté ejecutada en Supabase.",
                ST_BODY,
            ))
            return story

        # ---- Construcción de la tabla ----
        _MONEDAS_USD = {"USD", "US$", "$", "DOLARES", "DÓLARES"}

        def _fmt_m(val: float, moneda: str) -> str:
            sym = "US$" if moneda in _MONEDAS_USD else "S/"
            return f"{sym} {val:,.2f}"

        # Anchos de columna (proporciones suman 1.0)
        w = self._page_w
        col_w = [
            w * 0.05,    # # — suficiente para 2 dígitos
            w * 0.22,    # Cliente
            w * 0.21,    # Documento
            w * 0.12,    # Tipo
            w * 0.075,   # Moneda
            w * 0.165,   # Saldo anterior
            w * 0.16,    # Recuperado
        ]

        ST_TH_C = ST_TH   # reutiliza el estilo de encabezado de tabla

        header = [
            Paragraph("#",             ST_TH_C),
            Paragraph("Cliente",       ST_TH_C),
            Paragraph("Documento",     ST_TH_C),
            Paragraph("Tipo",          ST_TH_C),
            Paragraph("Moneda",        ST_TH_C),
            Paragraph("Saldo Ant.",    ST_TH_C),
            Paragraph("Recuperado",    ST_TH_C),
        ]

        rows = [header]
        row_styles: List = []
        # Header style
        row_styles += [
            ("BACKGROUND",    (0, 0), (-1, 0), C_PRIMARY),
            ("TOPPADDING",    (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ]

        # Contadores para totales
        tot_sol_compl = tot_usd_compl = 0.0
        tot_sol_amort = tot_usd_amort = 0.0
        n_compl = n_amort = 0
        n_docs_sol = n_docs_usd = 0   # para la fila de totales por moneda
        current_tipo = None
        idx = 0

        for doc in docs:
            tipo = doc["tipo"]
            moneda = str(doc.get("moneda", "PEN")).upper().strip()
            es_usd = moneda in _MONEDAS_USD
            monto = doc["monto_recuperado"]
            saldo_ant = doc["saldo_anterior"]
            r = len(rows)  # índice fila en la tabla

            # Separador de grupo cuando cambia el tipo
            if tipo != current_tipo:
                current_tipo = tipo
                tipo_label = "Documentos cobrados al 100%" if tipo == "COMPLETO" else "Amortizaciones parciales"
                tipo_color = C_COMPL if tipo == "COMPLETO" else C_AMORT
                sep_row = [
                    Paragraph(f"  {tipo_label}", _style(
                        f"RC_GrpHdr_{tipo}", "Normal",
                        fontSize=7.5, leading=9.5, textColor=C_WHITE, fontName=_F_BOLD
                    )),
                    "", "", "", "", "", "",
                ]
                rows.append(sep_row)
                sep_r = len(rows) - 1
                row_styles += [
                    ("BACKGROUND",   (0, sep_r), (-1, sep_r), tipo_color),
                    ("SPAN",         (0, sep_r), (-1, sep_r)),
                    ("TOPPADDING",   (0, sep_r), (-1, sep_r), 4),
                    ("BOTTOMPADDING",(0, sep_r), (-1, sep_r), 4),
                    ("LEFTPADDING",  (0, sep_r), (-1, sep_r), 6),
                ]

            idx += 1
            tipo_cell = "✔ Completo" if tipo == "COMPLETO" else "↓ Amortiz."
            tipo_st = _style(
                f"RC_Tipo_{tipo}_{idx}", "Normal",
                fontSize=7, leading=9,
                textColor=C_COMPL if tipo == "COMPLETO" else C_AMORT,
                fontName=_F_BOLD, alignment=TA_CENTER
            )
            nombre = doc.get("nombre", doc.get("cliente_id", "—"))
            if len(nombre) > 28:
                nombre = nombre[:26] + "…"
            mk = doc.get("match_key", "—")
            if len(mk) > 26:
                mk = mk[:24] + "…"

            rows.append([
                Paragraph(str(idx), ST_TD_CENTER),
                Paragraph(nombre,   ST_TD),
                Paragraph(mk,       ST_TD),
                Paragraph(tipo_cell, tipo_st),
                Paragraph("US$" if es_usd else "S/", ST_TD_CENTER),
                Paragraph(_fmt_m(saldo_ant, moneda), ST_TD_RIGHT),
                Paragraph(_fmt_m(monto, moneda),     ST_TD_RIGHT),
            ])
            r = len(rows) - 1
            # Zebra stripe
            if idx % 2 == 0:
                row_styles.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F7FAFC")))

            # Acumular totales
            if tipo == "COMPLETO":
                n_compl += 1
                if es_usd: tot_usd_compl += monto
                else:      tot_sol_compl += monto
            else:
                n_amort += 1
                if es_usd: tot_usd_amort += monto
                else:      tot_sol_amort += monto
            # Conteo por moneda (para filas finales)
            if es_usd: n_docs_usd += 1
            else:      n_docs_sol += 1

        # --- Filas de total por moneda ---
        tot_sol = tot_sol_compl + tot_sol_amort
        tot_usd = tot_usd_compl + tot_usd_amort

        _st_tot_lbl = _style("RC_TotLbl", "Normal",
                             fontSize=8, leading=10, textColor=C_WHITE, fontName=_F_BOLD)
        _st_tot_val = _style("RC_TotVal", "Normal",
                             fontSize=8, leading=10, textColor=C_WHITE, fontName=_F_BOLD,
                             alignment=TA_RIGHT)

        def _add_tot_row(label: str, monto_str: str, bg_color: Any) -> None:
            rows.append([
                Paragraph(label, _st_tot_lbl),
                "", "", "", "", "",
                Paragraph(monto_str, _st_tot_val),
            ])
            r = len(rows) - 1
            row_styles.extend([
                ("BACKGROUND",    (0, r), (-1, r), bg_color),
                ("SPAN",          (0, r), (5, r)),
                ("TOPPADDING",    (0, r), (-1, r), 6),
                ("BOTTOMPADDING", (0, r), (-1, r), 6),
                ("LEFTPADDING",   (0, r), (-1, r), 8),
            ])

        # Siempre mostrar la fila de Soles
        _n_s = n_docs_sol
        _sol_lbl = (
            f"TOTAL S/ — {_n_s} documento{'s' if _n_s != 1 else ''}"
            if tot_usd > 0
            else f"TOTAL RECUPERADO — {_n_s} documento{'s' if _n_s != 1 else ''} en Soles"
        )
        _add_tot_row(_sol_lbl, _fmt_m(tot_sol, "PEN"), C_PRIMARY)

        # Fila de Dólares solo si hay documentos en esa moneda
        if tot_usd > 0:
            _n_u = n_docs_usd
            _usd_lbl = f"TOTAL US$ — {_n_u} documento{'s' if _n_u != 1 else ''}"
            _add_tot_row(_usd_lbl, _fmt_m(tot_usd, "USD"), C_ACCENT)

        # Estilos comunes de todas las filas
        common_styles = [
            ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
            ("ROWBACKGROUND", (0, 1), (-1, -2), [C_WHITE, colors.HexColor("#F7FAFC")]),
            ("TOPPADDING",    (0, 1), (-1, -2), 3),
            ("BOTTOMPADDING", (0, 1), (-1, -2), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#D9E2EC")),
            ("ALIGN",         (5, 1), (-1, -1), "RIGHT"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]

        tbl = Table(rows, colWidths=col_w, repeatRows=1)
        tbl.setStyle(TableStyle(common_styles + row_styles))
        story.append(tbl)

        # Nota de validación
        story.append(_spacer(0.2))
        story.append(Paragraph(
            f"✔ {n_compl} doc(s) cobrados al 100%  ·  "
            f"↓ {n_amort} doc(s) amortizados parcialmente  ·  "
            f"Total S/: {_fmt_m(tot_sol, 'PEN')}"
            + (f"  ·  Total US$: {_fmt_m(tot_usd, 'USD')}" if tot_usd > 0 else ""),
            ST_NOTE,
        ))

        return story


# ---------------------------------------------------------------------------
# Helper local
# ---------------------------------------------------------------------------

def _accion_pdf(mora: int, gestiones: int) -> str:
    if mora > 90:
        return "Carta notarial / Legal"
    if mora > 60:
        return "Aviso firme + acuerdo urgente"
    if mora > 30:
        return "Llamada + oferta acuerdo"
    if gestiones == 0:
        return "Primer contacto preventivo"
    return "Seguimiento habitual"
