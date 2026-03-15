"""
Genera FRD_REPORTECOBRANZAS_v2.0.pdf desde docs/FRD_REPORTECOBRANZAS_v2.0.md
Usa Playwright (ya instalado) para renderizar HTML -> PDF con estilos Antay.
Ejecutar: python generar_frd_pdf.py
"""

import asyncio
import os
import pathlib
import markdown
import re

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = pathlib.Path(__file__).parent
MD_PATH  = BASE_DIR / "docs" / "FRD_REPORTECOBRANZAS_v2.0.md"
PDF_PATH = BASE_DIR / "docs" / "FRD_REPORTECOBRANZAS_v2.0.pdf"

# ── Design tokens Antay ────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --primary:      #0D3B66;
  --primary-soft: #245D99;
  --accent:       #0B7285;
  --light-bg:     #F7F9FC;
  --border:       #E2E8F0;
  --text:         #1A202C;
  --text-muted:   #6B7280;
  --success:      #38A169;
  --warning:      #D69E2E;
  --danger:       #E53E3E;
  --info:         #3182CE;
}

body {
  font-family: 'Manrope', 'Segoe UI', Arial, sans-serif;
  color: var(--text);
  background: #fff;
  font-size: 10.5pt;
  line-height: 1.7;
}

/* ── PORTADA ── */
.cover {
  background: linear-gradient(145deg, #0D3B66 0%, #1a5a9e 50%, #0B7285 100%);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 80px 100px;
  color: white;
  page-break-after: always;
  position: relative;
  overflow: hidden;
}
.cover::before {
  content: '';
  position: absolute;
  top: -120px; right: -120px;
  width: 450px; height: 450px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
}
.cover-badge {
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 24px;
  padding: 6px 20px;
  font-size: 9pt;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 32px;
  display: inline-block;
}
.cover-title {
  font-size: 38pt;
  font-weight: 800;
  letter-spacing: -1px;
  margin-bottom: 12px;
  line-height: 1.1;
}
.cover-subtitle {
  font-size: 15pt;
  font-weight: 300;
  opacity: 0.85;
  margin-bottom: 40px;
}
.cover-meta {
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 12px;
  padding: 24px 40px;
  display: inline-block;
  margin-top: 20px;
}
.cover-meta table { border-collapse: collapse; }
.cover-meta td {
  padding: 4px 16px;
  font-size: 10pt;
  text-align: left;
  opacity: 0.9;
  border: none;
  background: transparent;
}
.cover-meta td:first-child {
  font-weight: 600;
  opacity: 0.65;
  letter-spacing: 0.5px;
}
.cover-version {
  margin-top: 48px;
  font-size: 11pt;
  opacity: 0.6;
  font-weight: 500;
}

/* ── CONTENIDO ── */
.content {
  max-width: 820px;
  margin: 0 auto;
  padding: 48px 60px;
}

/* ── HEADINGS ── */
h1 {
  font-size: 22pt;
  font-weight: 800;
  color: var(--primary);
  border-bottom: 3px solid var(--primary);
  padding-bottom: 10px;
  margin: 40px 0 20px 0;
  page-break-after: avoid;
}
h2 {
  font-size: 14pt;
  font-weight: 700;
  color: var(--primary);
  border-left: 4px solid var(--accent);
  padding-left: 12px;
  margin: 32px 0 14px 0;
  page-break-after: avoid;
}
h3 {
  font-size: 12pt;
  font-weight: 600;
  color: var(--primary-soft);
  margin: 22px 0 10px 0;
  page-break-after: avoid;
}

/* ── PÁRRAFOS ── */
p {
  margin-bottom: 10px;
  color: var(--text);
}

/* ── BLOCKQUOTE ── */
blockquote {
  background: var(--light-bg);
  border-left: 4px solid var(--accent);
  padding: 10px 18px;
  margin: 14px 0;
  border-radius: 0 8px 8px 0;
  color: var(--text-muted);
  font-size: 9.5pt;
}
blockquote p { margin: 0; }

/* ── TABLAS ── */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 9.5pt;
  font-family: 'IBM Plex Sans', monospace;
  page-break-inside: avoid;
}
thead tr {
  background: var(--primary);
  color: white;
}
thead th {
  padding: 9px 14px;
  text-align: left;
  font-weight: 600;
  font-size: 9pt;
  letter-spacing: 0.3px;
  border: none;
}
tbody tr:nth-child(even) { background: var(--light-bg); }
tbody tr:hover { background: #eef2f7; }
tbody td {
  padding: 8px 14px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  color: var(--text);
}

/* ── LISTAS ── */
ul, ol {
  margin: 10px 0 10px 22px;
}
li {
  margin-bottom: 4px;
  line-height: 1.6;
}

/* ── CÓDIGO INLINE ── */
code {
  font-family: 'IBM Plex Sans', 'Consolas', monospace;
  background: var(--light-bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 9pt;
  color: var(--accent);
}

/* ── BLOQUES DE CÓDIGO ── */
pre {
  background: #1e2a3a;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 16px 20px;
  margin: 14px 0;
  font-family: 'IBM Plex Sans', 'Consolas', monospace;
  font-size: 9pt;
  line-height: 1.5;
  overflow: hidden;
  page-break-inside: avoid;
}
pre code {
  background: none;
  border: none;
  padding: 0;
  color: inherit;
  font-size: inherit;
}

/* ── BOLD / EM ── */
strong { font-weight: 700; color: var(--primary); }
em { color: var(--text-muted); font-style: italic; }

/* ── SEPARADORES ── */
hr {
  border: none;
  border-top: 2px solid var(--border);
  margin: 32px 0;
}

/* ── PILLS de estado ── */
.pill-done {
  display: inline-block;
  background: #c6f6d5;
  color: #276749;
  border-radius: 12px;
  padding: 2px 10px;
  font-size: 8.5pt;
  font-weight: 600;
}
.pill-pending {
  display: inline-block;
  background: #fefcbf;
  color: #744210;
  border-radius: 12px;
  padding: 2px 10px;
  font-size: 8.5pt;
  font-weight: 600;
}

/* ══════════════════════════════════════════════════════
   SECCIÓN DISEÑOS / WIREFRAMES
   ══════════════════════════════════════════════════════ */

/* ── Divisor de sección de diseños ── */
.design-cover {
  background: linear-gradient(135deg, #0D3B66 0%, #0B7285 100%);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: white;
  page-break-before: always;
  page-break-after: always;
}
.design-cover-eyebrow {
  font-size: 9pt;
  font-weight: 600;
  letter-spacing: 3px;
  text-transform: uppercase;
  opacity: 0.6;
  margin-bottom: 20px;
}
.design-cover-title {
  font-size: 30pt;
  font-weight: 800;
  margin-bottom: 16px;
  line-height: 1.1;
}
.design-cover-sub {
  font-size: 13pt;
  font-weight: 300;
  opacity: 0.8;
  max-width: 500px;
  margin: 0 auto 40px;
}
.design-cover-tiers {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}
.design-cover-tier {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 12px;
  padding: 16px 28px;
  min-width: 140px;
}
.design-cover-tier .tier-label {
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  opacity: 0.65;
  margin-bottom: 6px;
}
.design-cover-tier .tier-count {
  font-size: 22pt;
  font-weight: 800;
  color: #48CAE4;
}
.design-cover-tier .tier-desc {
  font-size: 8.5pt;
  opacity: 0.75;
  margin-top: 4px;
}

/* ── Página de diseño individual ── */
.design-page {
  page-break-before: always;
  padding: 36px 52px 32px;
}
.design-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid var(--border);
  padding-bottom: 12px;
  margin-bottom: 24px;
}
.design-page-logo {
  font-size: 8.5pt;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: 1px;
  text-transform: uppercase;
}
.design-page-section {
  font-size: 8.5pt;
  color: var(--text-muted);
}
.tier-badge-inline {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-right: 8px;
}
.tier2 { background: #0B7285; color: white; }
.tier3 { background: #556B82; color: white; }

.design-section-header {
  margin-bottom: 18px;
}
.design-section-header h2 {
  font-size: 15pt;
  font-weight: 800;
  color: var(--primary);
  border: none;
  padding: 0;
  margin: 0 0 6px 0;
}
.design-section-header p {
  color: var(--text-muted);
  font-size: 9.5pt;
  margin: 0;
}

/* ── Mockup de ventana del browser / Streamlit ── */
.ui-mockup {
  border: 1.5px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  margin: 16px 0;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  page-break-inside: avoid;
}
.ui-mockup-bar {
  background: #e8ecf0;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid #d0d7de;
}
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.dot-r { background: #ff5f57; }
.dot-y { background: #febc2e; }
.dot-g { background: #28c840; }
.ui-mockup-title {
  font-size: 8.5pt;
  color: #555;
  margin-left: 8px;
  font-weight: 500;
  flex: 1;
  text-align: center;
}
.ui-mockup-body {
  background: #f8fafc;
  padding: 16px 18px;
}

/* ── Sidebar mockup ── */
.streamlit-layout {
  display: flex;
  gap: 0;
  min-height: 320px;
}
.mock-sidebar {
  width: 200px;
  background: linear-gradient(180deg, #0a2545 0%, #18457c 100%);
  padding: 14px 12px;
  color: white;
  flex-shrink: 0;
  border-right: 1px solid #ddd;
}
.mock-sidebar-title {
  font-size: 7.5pt;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  opacity: 0.6;
  margin-bottom: 12px;
}
.mock-sidebar-item {
  font-size: 8.5pt;
  padding: 6px 8px;
  border-radius: 6px;
  margin-bottom: 3px;
  opacity: 0.8;
  cursor: pointer;
}
.mock-sidebar-item.active {
  background: rgba(255,255,255,0.15);
  opacity: 1;
  font-weight: 600;
}
.mock-main {
  flex: 1;
  padding: 14px 18px;
  background: #f8fafc;
}

/* ── KPI row ── */
.kpi-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.kpi-mock {
  flex: 1;
  min-width: 90px;
  background: white;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 10px 14px;
  text-align: center;
}
.kpi-mock.green { border-color: #38A169; background: #f0fff4; }
.kpi-mock.orange { border-color: #D69E2E; background: #fffbeb; }
.kpi-mock.red { border-color: #E53E3E; background: #fff5f5; }
.kpi-mock.teal { border-color: #0B7285; background: #e6fffa; }
.kpi-mock.blue { border-color: #3182CE; background: #ebf8ff; }
.kpi-val { font-size: 16pt; font-weight: 800; color: var(--primary); line-height: 1; }
.kpi-mock.green .kpi-val { color: #276749; }
.kpi-mock.orange .kpi-val { color: #744210; }
.kpi-mock.red .kpi-val { color: #9b2c2c; }
.kpi-mock.teal .kpi-val { color: #0B7285; }
.kpi-mock.blue .kpi-val { color: #2c5282; }
.kpi-lbl { font-size: 7.5pt; color: var(--text-muted); margin-top: 4px; font-weight: 500; }

/* ── Tablas de mockup ── */
.mock-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 8.5pt;
  font-family: 'IBM Plex Sans', monospace;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}
.mock-table thead tr { background: var(--primary); color: white; }
.mock-table thead th {
  padding: 7px 10px;
  text-align: left;
  font-weight: 600;
  font-size: 7.5pt;
  letter-spacing: 0.3px;
  border: none;
}
.mock-table tbody tr:nth-child(even) { background: #f7f9fc; }
.mock-table tbody td {
  padding: 7px 10px;
  border-bottom: 1px solid #e9ecef;
  vertical-align: middle;
  color: #1A202C;
}

/* ── Buttons ── */
.btn {
  display: inline-block;
  padding: 5px 14px;
  border-radius: 6px;
  font-size: 8pt;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary { background: var(--primary); color: white; }
.btn-green { background: #38A169; color: white; }
.btn-orange { background: #D69E2E; color: white; }
.btn-red { background: #E53E3E; color: white; }
.btn-teal { background: #0B7285; color: white; }
.btn-outline { background: white; color: var(--primary); border: 1.5px solid var(--border); }

/* ── Badges / Pills ── */
.badge {
  display: inline-block;
  border-radius: 12px;
  padding: 3px 10px;
  font-size: 7.5pt;
  font-weight: 600;
}
.badge-green { background: #c6f6d5; color: #276749; }
.badge-orange { background: #feebc8; color: #744210; }
.badge-red { background: #fed7d7; color: #9b2c2c; }
.badge-blue { background: #bee3f8; color: #2c5282; }
.badge-gray { background: #e2e8f0; color: #4a5568; }
.badge-teal { background: #b2f5ea; color: #0B7285; }
.badge-purple { background: #e9d8fd; color: #553c9a; }

/* ── Segmento Aging ── */
.aging-segment {
  flex: 1;
  padding: 12px;
  text-align: center;
  border-radius: 8px;
  margin: 0 4px;
}
.aging-row { display: flex; gap: 8px; margin: 12px 0; }
.seg-verde { background: #f0fff4; border: 2px solid #38A169; }
.seg-amarillo { background: #fffbeb; border: 2px solid #D69E2E; }
.seg-naranja { background: #fff8f0; border: 2px dashed #ED8936; }
.seg-rojo { background: #fff5f5; border: 2px solid #E53E3E; }
.seg-days { font-size: 11pt; font-weight: 800; margin-bottom: 4px; }
.seg-label { font-size: 7.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.seg-template { font-size: 8pt; font-style: italic; opacity: 0.8; }
.seg-arrow {
  display: flex;
  align-items: center;
  font-size: 14pt;
  color: #aaa;
  margin: 0 4px;
}

/* ── Chart bars ── */
.chart-bar-container {
  background: white;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 14px 18px;
  margin: 10px 0;
}
.chart-title {
  font-size: 8.5pt;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 12px;
}
.bar-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}
.bar-label { width: 120px; font-size: 8pt; color: var(--text-muted); text-align: right; flex-shrink: 0; }
.bar-track { flex: 1; background: #e9ecef; border-radius: 4px; height: 16px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 6px; }
.bar-fill-primary { background: var(--primary); }
.bar-fill-green { background: #38A169; }
.bar-fill-teal { background: #0B7285; }
.bar-fill-orange { background: #D69E2E; }
.bar-fill-red { background: #E53E3E; }
.bar-value { font-size: 7.5pt; font-weight: 700; color: white; white-space: nowrap; }
.bar-pct { width: 40px; font-size: 8pt; font-weight: 700; color: var(--text-muted); }

/* ── Callout ── */
.callout {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  margin: 12px 0;
  page-break-inside: avoid;
}
.callout-info { background: #ebf8ff; border-left: 4px solid #3182CE; }
.callout-success { background: #f0fff4; border-left: 4px solid #38A169; }
.callout-warning { background: #fffbeb; border-left: 4px solid #D69E2E; }
.callout-icon { font-size: 14pt; flex-shrink: 0; margin-top: 2px; }
.callout-body { font-size: 9pt; line-height: 1.5; color: var(--text); }
.callout-body strong { color: inherit; font-weight: 700; }

/* ── Ficha técnica ── */
.tech-pills { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
.tech-pill {
  background: #e9ecef;
  color: #4a5568;
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 7.5pt;
  font-weight: 600;
  font-family: 'IBM Plex Sans', monospace;
}
.tech-pill.file { background: #ebf8ff; color: #2c5282; }
.tech-pill.sql  { background: #e6fffa; color: #0B7285; }
.tech-pill.time { background: #fefcbf; color: #744210; }

/* ── Timeline cuotas ── */
.timeline { display: flex; gap: 0; margin: 10px 0; }
.tl-item {
  flex: 1;
  text-align: center;
  position: relative;
}
.tl-item::before {
  content: '';
  position: absolute;
  top: 13px; left: 50%;
  width: 100%; height: 2px;
  background: #e2e8f0;
  z-index: 0;
}
.tl-item:last-child::before { display: none; }
.tl-dot {
  width: 26px; height: 26px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10pt;
  position: relative; z-index: 1;
  margin-bottom: 6px;
}
.tl-pagada { background: #c6f6d5; }
.tl-pendiente { background: #bee3f8; }
.tl-vencida { background: #fed7d7; }
.tl-fecha { font-size: 7.5pt; color: var(--text-muted); }
.tl-monto { font-size: 8pt; font-weight: 700; color: var(--primary); }

/* ── PIE DE PÁGINA (simulado) ── */
@page {
  margin: 20mm 18mm 18mm 18mm;
  @bottom-center {
    content: counter(page);
    font-family: 'Manrope', Arial, sans-serif;
    font-size: 9pt;
    color: #aaa;
  }
}
"""

COVER_HTML = """
<div class="cover">
  <div class="cover-badge">Antay Fábrica de Software</div>
  <div class="cover-title">ReporteCobranzas</div>
  <div class="cover-subtitle">Functional Requirements Document</div>
  <div class="cover-meta">
    <table>
      <tr><td>Versión FRD</td><td>v2.0</td></tr>
      <tr><td>Versión app</td><td>v1.7.3</td></tr>
      <tr><td>Fecha</td><td>2026-03-15</td></tr>
      <tr><td>Product Owner</td><td>Camilo Ortega F.R.</td></tr>
      <tr><td>Estado CRM WA</td><td>TIER 1 completado — 141/141 tests ✓</td></tr>
      <tr><td>Supabase</td><td>Migración completa (MIG-000 → MIG-009)</td></tr>
    </table>
  </div>
  <div class="cover-version">FRD consolidado — Antay® 2026</div>
</div>
"""


def md_to_html(md_text: str) -> str:
    """Convierte el markdown a HTML con extensiones de tabla."""
    html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    return html


# ── Apéndice visual: diseños/wireframes de features pendientes ─────────────
DESIGNS_HTML = """

<!-- ══════════════════ PORTADA APÉNDICE DISEÑOS ══════════════════════════ -->
<div class="design-cover">
  <div class="design-cover-eyebrow">FRD ReporteCobranzas v2.0 — Antay</div>
  <div class="design-cover-title">Apéndice UI/UX<br>Diseños y Wireframes</div>
  <div class="design-cover-sub">Visualización de features pendientes — TIER 2 y TIER 3</div>
  <div class="design-cover-tiers">
    <div class="design-cover-tier">
      <div class="tier-label">TIER 2</div>
      <div class="tier-count">2</div>
      <div class="tier-desc">Features</div>
    </div>
    <div class="design-cover-tier">
      <div class="tier-label">TIER 3</div>
      <div class="tier-count">2</div>
      <div class="tier-desc">Features</div>
    </div>
    <div class="design-cover-tier">
      <div class="tier-label">Páginas de diseño</div>
      <div class="tier-count">4</div>
      <div class="tier-desc">Wireframes</div>
    </div>
  </div>
</div>


<!-- ════════════════ DISEÑO 1: RC-FEAT-027 AGING AUTOMÁTICO ══════════════ -->
<div class="design-page">
  <div class="design-page-header">
    <span class="design-page-logo">Antay · ReporteCobranzas</span>
    <span class="design-page-section">Diseño 1 de 4 — RC-FEAT-027</span>
  </div>

  <div class="design-section-header">
    <h2><span class="tier-badge-inline tier2">TIER 2</span>RC-FEAT-027 — Selección Automática de Plantilla por Aging</h2>
    <p>Al abrir Tab WhatsApp, el sistema sugiere automáticamente la plantilla según días de mora de cada cliente. El gestor puede sobreescribir antes de enviar.</p>
  </div>

  <h3 style="font-size:10pt;font-weight:700;color:var(--primary);margin:14px 0 8px;">Regla de segmentación por días de mora</h3>
  <div class="aging-row">
    <div class="aging-segment seg-verde">
      <div class="seg-days" style="color:#276749;">0–14</div>
      <div class="seg-label" style="color:#276749;">Deuda reciente</div>
      <div class="seg-template">Primer Aviso</div>
    </div>
    <div class="seg-arrow">→</div>
    <div class="aging-segment seg-amarillo">
      <div class="seg-days" style="color:#744210;">15–30</div>
      <div class="seg-label" style="color:#744210;">Sin respuesta</div>
      <div class="seg-template">Recordatorio</div>
    </div>
    <div class="seg-arrow">→</div>
    <div class="aging-segment seg-naranja">
      <div class="seg-days" style="color:#c05621;">31–60</div>
      <div class="seg-label" style="color:#c05621;">Mora significativa</div>
      <div class="seg-template">Aviso Firme</div>
    </div>
    <div class="seg-arrow">→</div>
    <div class="aging-segment seg-rojo">
      <div class="seg-days" style="color:#9b2c2c;">60+</div>
      <div class="seg-label" style="color:#9b2c2c;">Mora crítica</div>
      <div class="seg-template">Pre-Legal</div>
    </div>
  </div>

  <h3 style="font-size:10pt;font-weight:700;color:var(--primary);margin:16px 0 8px;">Wireframe — Tab WhatsApp con columna Segmento y plantilla pre-seleccionada</h3>

  <div class="ui-mockup">
    <div class="ui-mockup-bar">
      <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
      <span class="ui-mockup-title">Tab: Marketing WhatsApp — Seleccion de Clientes</span>
    </div>
    <div class="ui-mockup-body">
      <div style="display:flex;gap:10px;margin-bottom:12px;align-items:center;">
        <div style="flex:1;background:white;border:1.5px solid var(--border);border-radius:6px;padding:7px 12px;font-size:8.5pt;color:var(--text-muted);">Buscar cliente...</div>
        <div style="background:white;border:1.5px solid #0B7285;border-radius:6px;padding:7px 14px;font-size:8.5pt;font-weight:600;color:#0B7285;">Plantilla sugerida por Aging</div>
        <div style="background:white;border:1.5px solid var(--border);border-radius:6px;padding:7px 14px;font-size:8.5pt;color:var(--text-muted);">Seleccionar todos</div>
      </div>
      <table class="mock-table">
        <thead>
          <tr><th>Check</th><th>Cliente</th><th>Telefono</th><th>Saldo Real</th><th>Dias Mora</th><th>Segmento</th><th>Plantilla Sugerida</th><th>Cambiar</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>[x]</td>
            <td><strong>COMERCIAL LIMA S.A.</strong></td>
            <td>+51 987-654-321</td>
            <td><strong>S/ 12,400</strong></td>
            <td><span style="color:#9b2c2c;font-weight:700;">68 dias</span></td>
            <td><span class="badge badge-red">Mora critica</span></td>
            <td><span class="badge badge-red">Pre-Legal</span></td>
            <td><span class="btn btn-outline" style="font-size:7pt;padding:3px 8px;">Cambiar</span></td>
          </tr>
          <tr>
            <td>[x]</td>
            <td><strong>INVERSIONES NORTE</strong></td>
            <td>+51 912-345-678</td>
            <td><strong>S/ 8,750</strong></td>
            <td><span style="color:#c05621;font-weight:700;">45 dias</span></td>
            <td><span class="badge badge-orange">Mora significativa</span></td>
            <td><span class="badge badge-orange">Aviso Firme</span></td>
            <td><span class="btn btn-outline" style="font-size:7pt;padding:3px 8px;">Cambiar</span></td>
          </tr>
          <tr>
            <td>[x]</td>
            <td><strong>DISTRIBUIDORA SUR</strong></td>
            <td>+51 945-678-901</td>
            <td><strong>$ 3,200</strong></td>
            <td><span style="color:#744210;font-weight:700;">18 dias</span></td>
            <td><span class="badge badge-orange" style="background:#feebc8;color:#744210;">Sin respuesta</span></td>
            <td><span class="badge" style="background:#feebc8;color:#744210;">Recordatorio</span></td>
            <td><span class="btn btn-outline" style="font-size:7pt;padding:3px 8px;">Cambiar</span></td>
          </tr>
          <tr>
            <td>[ ]</td>
            <td><strong>SERVICIOS ANDINOS</strong></td>
            <td>+51 956-789-012</td>
            <td><strong>S/ 2,100</strong></td>
            <td><span style="color:#276749;font-weight:700;">8 dias</span></td>
            <td><span class="badge badge-green">Deuda reciente</span></td>
            <td><span class="badge badge-green">Primer Aviso</span></td>
            <td><span class="btn btn-outline" style="font-size:7pt;padding:3px 8px;">Cambiar</span></td>
          </tr>
        </tbody>
      </table>
      <div style="margin-top:12px;display:flex;gap:8px;justify-content:flex-end;align-items:center;">
        <span style="font-size:8pt;color:var(--text-muted);">3 clientes seleccionados &middot; Monto total: <strong style="color:var(--primary);">S/ 21,150 + $ 3,200</strong></span>
        <span class="btn btn-primary">Enviar WA (3 clientes)</span>
      </div>
    </div>
  </div>

  <div class="callout callout-info">
    <span class="callout-icon">&#128161;</span>
    <div class="callout-body">
      <strong>Control humano siempre presente:</strong> el sistema <em>sugiere</em> la plantilla pero el gestor puede cambiarla cliente por cliente antes de enviar. Nunca hay envio automatico.
    </div>
  </div>

  <div class="tech-pills">
    <span class="tech-pill file">utils/ui/tabs/whatsapp.py</span>
    <span class="tech-pill time">~2 horas</span>
    <span class="tech-pill">Solo logica Python — Sin cambios BD</span>
  </div>
</div>


<!-- ════════════════ DISEÑO 2: RC-FEAT-028 KPIs EFECTIVIDAD ═══════════════ -->
<div class="design-page">
  <div class="design-page-header">
    <span class="design-page-logo">Antay · ReporteCobranzas</span>
    <span class="design-page-section">Diseño 2 de 4 — RC-FEAT-028</span>
  </div>

  <div class="design-section-header">
    <h2><span class="tier-badge-inline tier2">TIER 2</span>RC-FEAT-028 — KPIs Expandidos de Efectividad de Cobranza</h2>
    <p>Panel de metricas cruzadas visible en Tab WA y Centro de Gestiones. Calculado en tiempo real desde Supabase.</p>
  </div>

  <div class="ui-mockup">
    <div class="ui-mockup-bar">
      <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
      <span class="ui-mockup-title">Tab: Centro de Gestiones — Panel de Efectividad</span>
    </div>
    <div class="ui-mockup-body">
      <div style="font-weight:700;font-size:9pt;color:var(--primary);margin-bottom:10px;">Efectividad de Cobranza — Ciclo activo</div>
      <div class="kpi-row">
        <div class="kpi-mock"><div class="kpi-val">47</div><div class="kpi-lbl">WA enviados hoy</div></div>
        <div class="kpi-mock green"><div class="kpi-val">18</div><div class="kpi-lbl">Con respuesta positiva</div></div>
        <div class="kpi-mock orange"><div class="kpi-val">21</div><div class="kpi-lbl">Sin respuesta</div></div>
        <div class="kpi-mock red"><div class="kpi-val">8</div><div class="kpi-lbl">Escalados a Legal</div></div>
      </div>
      <div class="kpi-row">
        <div class="kpi-mock blue"><div class="kpi-val">12</div><div class="kpi-lbl">Acuerdos activos</div></div>
        <div class="kpi-mock orange"><div class="kpi-val">3</div><div class="kpi-lbl">Cuotas vencen en 3 dias</div></div>
        <div class="kpi-mock teal"><div class="kpi-val">S/ 186K</div><div class="kpi-lbl">Monto gestionado</div></div>
        <div class="kpi-mock green"><div class="kpi-val">S/ 43K</div><div class="kpi-lbl">Monto con acuerdo formal</div></div>
      </div>
      <div style="display:flex;gap:12px;margin-top:4px;">
        <div class="chart-bar-container" style="flex:1;">
          <div class="chart-title">Respuestas por resultado — ultimos 7 dias</div>
          <div class="bar-row"><span class="bar-label">Exitoso / Pago</span><div class="bar-track"><div class="bar-fill bar-fill-green" style="width:38%;"><span class="bar-value">38%</span></div></div><span class="bar-pct">18</span></div>
          <div class="bar-row"><span class="bar-label">Prometio pagar</span><div class="bar-track"><div class="bar-fill bar-fill-teal" style="width:22%;"><span class="bar-value">22%</span></div></div><span class="bar-pct">10</span></div>
          <div class="bar-row"><span class="bar-label">Sin respuesta</span><div class="bar-track"><div class="bar-fill bar-fill-orange" style="width:28%;"><span class="bar-value">28%</span></div></div><span class="bar-pct">13</span></div>
          <div class="bar-row"><span class="bar-label">Escalado</span><div class="bar-track"><div class="bar-fill bar-fill-red" style="width:12%;"><span class="bar-value">12%</span></div></div><span class="bar-pct">6</span></div>
        </div>
        <div class="chart-bar-container" style="flex:1;">
          <div class="chart-title">Conversion por plantilla WA</div>
          <div class="bar-row"><span class="bar-label">Acuerdo de Pago</span><div class="bar-track"><div class="bar-fill bar-fill-green" style="width:72%;"><span class="bar-value">72%</span></div></div><span class="bar-pct">alta</span></div>
          <div class="bar-row"><span class="bar-label">Primer Aviso</span><div class="bar-track"><div class="bar-fill bar-fill-teal" style="width:55%;"><span class="bar-value">55%</span></div></div><span class="bar-pct">media</span></div>
          <div class="bar-row"><span class="bar-label">Recordatorio</span><div class="bar-track"><div class="bar-fill bar-fill-primary" style="width:48%;"><span class="bar-value">48%</span></div></div><span class="bar-pct">media</span></div>
          <div class="bar-row"><span class="bar-label">Pre-Legal</span><div class="bar-track"><div class="bar-fill bar-fill-orange" style="width:18%;"><span class="bar-value">18%</span></div></div><span class="bar-pct">baja</span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="callout callout-success">
    <span class="callout-icon">&#127919;</span>
    <div class="callout-body"><strong>Sin impacto en flujo principal:</strong> todos los KPIs se calculan con consultas directas a Supabase. No modifica <code>df_final</code> ni <code>df_filtered</code>.</div>
  </div>

  <div class="tech-pills">
    <span class="tech-pill file">utils/ui/tabs/whatsapp.py</span>
    <span class="tech-pill file">utils/ui/tabs/crm_gestiones.py</span>
    <span class="tech-pill file">utils/db_manager.py</span>
    <span class="tech-pill sql">gestiones · acuerdos_pago · cuotas_acuerdo · resumen_ciclo</span>
    <span class="tech-pill time">~2 horas</span>
  </div>
</div>


<!-- ════════════════ DISEÑO 3: RC-FEAT-029 PAGOS TIEMPO REAL ═════════════ -->
<div class="design-page">
  <div class="design-page-header">
    <span class="design-page-logo">Antay · ReporteCobranzas</span>
    <span class="design-page-section">Diseño 3 de 4 — RC-FEAT-029</span>
  </div>

  <div class="design-section-header">
    <h2><span class="tier-badge-inline tier3">TIER 3</span>RC-FEAT-029 — Registro de Pagos en Tiempo Real</h2>
    <p>El gestor registra un pago recibido directamente en la app sin esperar el ERP. El registro es provisional hasta que el siguiente ciclo Excel lo confirme.</p>
  </div>

  <div class="ui-mockup">
    <div class="ui-mockup-bar">
      <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
      <span class="ui-mockup-title">Tab: Centro de Gestiones — Registrar Pago Recibido</span>
    </div>
    <div class="ui-mockup-body">
      <div style="display:flex;gap:14px;">
        <div style="flex:1;">
          <div style="font-weight:700;font-size:9pt;color:var(--primary);margin-bottom:10px;">Registrar pago provisional</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div style="background:white;border:1.5px solid var(--border);border-radius:6px;padding:8px 10px;"><div style="font-size:7.5pt;color:var(--text-muted);margin-bottom:3px;">Cliente *</div><div style="font-size:9pt;font-weight:600;color:var(--primary);">COMERCIAL LIMA S.A.</div></div>
            <div style="background:white;border:1.5px solid var(--border);border-radius:6px;padding:8px 10px;"><div style="font-size:7.5pt;color:var(--text-muted);margin-bottom:3px;">Fecha de pago *</div><div style="font-size:9pt;">14/03/2026</div></div>
            <div style="background:white;border:1.5px solid var(--border);border-radius:6px;padding:8px 10px;"><div style="font-size:7.5pt;color:var(--text-muted);margin-bottom:3px;">Monto *</div><div style="font-size:9pt;font-weight:600;">S/ 8,000.00</div></div>
            <div style="background:white;border:1.5px solid var(--border);border-radius:6px;padding:8px 10px;"><div style="font-size:7.5pt;color:var(--text-muted);margin-bottom:3px;">Forma de pago *</div><div style="font-size:9pt;">Transferencia bancaria</div></div>
            <div style="background:white;border:1.5px solid var(--border);border-radius:6px;padding:8px 10px;"><div style="font-size:7.5pt;color:var(--text-muted);margin-bottom:3px;">Banco</div><div style="font-size:9pt;">BCP</div></div>
            <div style="background:white;border:1.5px solid var(--border);border-radius:6px;padding:8px 10px;"><div style="font-size:7.5pt;color:var(--text-muted);margin-bottom:3px;">Referencia</div><div style="font-size:9pt;font-family:monospace;">TRF-2026031412345</div></div>
          </div>
          <div style="background:white;border:1.5px solid var(--border);border-radius:6px;padding:8px 10px;margin-top:8px;"><div style="font-size:7.5pt;color:var(--text-muted);margin-bottom:3px;">Nota del gestor</div><div style="font-size:9pt;color:#9ca3af;font-style:italic;">Cliente confirmo abono parcial por WhatsApp...</div></div>
          <div style="display:flex;align-items:center;gap:8px;margin-top:8px;"><input type="checkbox" checked disabled><span style="font-size:8.5pt;">Enviar WA de agradecimiento automaticamente (plantilla Felicitacion)</span></div>
          <div style="display:flex;gap:8px;margin-top:12px;"><span class="btn btn-outline">Cancelar</span><span class="btn btn-green">Registrar pago provisional</span></div>
        </div>
        <div style="width:200px;flex-shrink:0;">
          <div style="font-weight:700;font-size:9pt;color:var(--primary);margin-bottom:10px;">Estado actual del cliente</div>
          <div style="background:white;border:1.5px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px;">
            <div style="font-size:7.5pt;color:var(--text-muted);">Saldo pendiente</div>
            <div style="font-size:14pt;font-weight:800;color:#E53E3E;">S/ 12,400</div>
            <div style="font-size:7.5pt;color:var(--text-muted);margin-top:6px;">Dias mora</div>
            <div style="font-size:12pt;font-weight:700;color:#9b2c2c;">68 dias</div>
          </div>
          <div style="background:#fffbeb;border:1.5px solid #D69E2E;border-radius:8px;padding:10px;">
            <div style="font-size:8pt;font-weight:700;color:#744210;">Registro provisional</div>
            <div style="font-size:7.5pt;color:#92400e;margin-top:4px;line-height:1.4;">Marcado como <strong>pendiente de confirmacion ERP</strong> hasta que el siguiente ciclo Excel lo confirme.</div>
          </div>
          <div style="margin-top:10px;">
            <div style="font-weight:700;font-size:8.5pt;color:var(--primary);margin-bottom:6px;">Acuerdo activo:</div>
            <div class="timeline">
              <div class="tl-item"><div class="tl-dot tl-pagada">+</div><div class="tl-fecha">01/03</div><div class="tl-monto">S/ 4,100</div></div>
              <div class="tl-item"><div class="tl-dot tl-vencida">!</div><div class="tl-fecha">15/03</div><div class="tl-monto">S/ 4,150</div></div>
              <div class="tl-item"><div class="tl-dot tl-pendiente">o</div><div class="tl-fecha">30/03</div><div class="tl-monto">S/ 4,150</div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="callout callout-warning">
    <span class="callout-icon">&#9888;</span>
    <div class="callout-body"><strong>Riesgo documentado:</strong> si el siguiente ciclo Excel llega tarde o no llega, el registro provisional permanece. Se muestra indicador visual diferenciador en toda la UI.</div>
  </div>

  <div class="tech-pills">
    <span class="tech-pill file">utils/ui/tabs/crm_gestiones.py</span>
    <span class="tech-pill file">utils/db_manager.py</span>
    <span class="tech-pill sql">documentos (monto_pendiente + flag provisional)</span>
    <span class="tech-pill sql">cuotas_acuerdo (estado PAGADA)</span>
    <span class="tech-pill time">~4 horas</span>
  </div>
</div>


<!-- ════════════════ DISEÑO 4: RC-FEAT-030 DASHBOARD ANALYTICS ═══════════ -->
<div class="design-page">
  <div class="design-page-header">
    <span class="design-page-logo">Antay · ReporteCobranzas</span>
    <span class="design-page-section">Diseño 4 de 4 — RC-FEAT-030</span>
  </div>

  <div class="design-section-header">
    <h2><span class="tier-badge-inline tier3">TIER 3</span>RC-FEAT-030 — Dashboard de Efectividad de Cobranza</h2>
    <p>Nuevo Tab Analytics con reportes ejecutivos para supervisor/direccion. Requiere 2+ ciclos en produccion para tener datos suficientes.</p>
  </div>

  <div class="ui-mockup">
    <div class="ui-mockup-bar">
      <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
      <span class="ui-mockup-title">Tab: Analytics — Dashboard de Efectividad de Cobranza</span>
    </div>
    <div class="streamlit-layout">
      <div class="mock-sidebar">
        <div class="mock-sidebar-title">Filtros</div>
        <div style="font-size:8pt;opacity:0.6;margin-bottom:8px;">Periodo</div>
        <div class="mock-sidebar-item active">Ultimo mes</div>
        <div class="mock-sidebar-item">Ultimos 3 meses</div>
        <div class="mock-sidebar-item">Acumulado</div>
        <div style="font-size:8pt;opacity:0.6;margin:12px 0 6px;">Ciclo</div>
        <div class="mock-sidebar-item active">CIC-20260315</div>
        <div class="mock-sidebar-item">CIC-20260301</div>
        <div class="mock-sidebar-item">CIC-20260215</div>
        <div style="margin-top:16px;">
          <div class="mock-sidebar-item" style="background:rgba(255,255,255,0.1);">Exportar Excel</div>
          <div class="mock-sidebar-item" style="margin-top:4px;">Exportar CSV</div>
        </div>
      </div>
      <div class="mock-main">
        <div class="kpi-row" style="margin-bottom:12px;">
          <div class="kpi-mock teal"><div class="kpi-val">38%</div><div class="kpi-lbl">Tasa conversion WA→Pago (30d)</div></div>
          <div class="kpi-mock green"><div class="kpi-val">S/ 186K</div><div class="kpi-lbl">Saldo recuperado este mes</div></div>
          <div class="kpi-mock blue"><div class="kpi-val">85%</div><div class="kpi-lbl">Acuerdos cumplidos</div></div>
          <div class="kpi-mock orange"><div class="kpi-val">14.2 dias</div><div class="kpi-lbl">Tiempo medio de cobro</div></div>
        </div>
        <div style="display:flex;gap:12px;">
          <div class="chart-bar-container" style="flex:1.2;">
            <div class="chart-title">Recuperacion mensual (S/)</div>
            <div class="bar-row"><span class="bar-label">Febrero</span><div class="bar-track"><div class="bar-fill bar-fill-primary" style="width:62%;"><span class="bar-value">S/ 142K</span></div></div><span class="bar-pct"></span></div>
            <div class="bar-row"><span class="bar-label">Marzo (parcial)</span><div class="bar-track"><div class="bar-fill bar-fill-green" style="width:81%;"><span class="bar-value">S/ 186K</span></div></div><span class="bar-pct">+31%</span></div>
            <div class="bar-row"><span class="bar-label">Meta del mes</span><div class="bar-track"><div class="bar-fill" style="width:100%;background:#e2e8f0;"><span class="bar-value" style="color:#4a5568;">S/ 230K</span></div></div><span class="bar-pct"></span></div>
          </div>
          <div style="flex:1;">
            <div class="chart-bar-container">
              <div class="chart-title">Ranking: clientes dificiles de cobrar</div>
              <table class="mock-table" style="font-size:7.5pt;">
                <thead><tr><th>#</th><th>Cliente</th><th>Gestiones</th><th>Mora</th></tr></thead>
                <tbody>
                  <tr><td>1</td><td>DIST. SUR S.A.</td><td>8 sin resultado</td><td><span class="badge badge-red">68d</span></td></tr>
                  <tr><td>2</td><td>SERV. ANDINOS</td><td>5 sin resultado</td><td><span class="badge badge-red">55d</span></td></tr>
                  <tr><td>3</td><td>LOGISTICA NORTE</td><td>4 sin resultado</td><td><span class="badge badge-orange">42d</span></td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="chart-bar-container" style="margin-top:8px;">
          <div class="chart-title">Efectividad por plantilla WA — % que resultaron en pago (30 dias)</div>
          <div style="display:flex;gap:12px;">
            <div class="bar-row" style="flex:1;"><span class="bar-label">Acuerdo de Pago</span><div class="bar-track"><div class="bar-fill bar-fill-green" style="width:72%;"><span class="bar-value">72%</span></div></div></div>
            <div class="bar-row" style="flex:1;"><span class="bar-label">Primer Aviso</span><div class="bar-track"><div class="bar-fill bar-fill-teal" style="width:55%;"><span class="bar-value">55%</span></div></div></div>
            <div class="bar-row" style="flex:1;"><span class="bar-label">Pre-Legal</span><div class="bar-track"><div class="bar-fill bar-fill-orange" style="width:18%;"><span class="bar-value">18%</span></div></div></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="callout callout-info">
    <span class="callout-icon">&#128204;</span>
    <div class="callout-body"><strong>Prerequisito:</strong> RC-FEAT-023 (Trazabilidad) debe tener 2+ ciclos en produccion. Los datos vienen de <code>resumen_cliente_ciclo</code> y <code>resumen_ciclo</code>.</div>
  </div>

  <div class="tech-pills">
    <span class="tech-pill file">utils/ui/tabs/analytics.py (nuevo)</span>
    <span class="tech-pill file">utils/db_manager.py</span>
    <span class="tech-pill sql">resumen_cliente_ciclo · resumen_ciclo · gestiones · acuerdos_pago</span>
    <span class="tech-pill time">~6 horas</span>
  </div>
</div>
"""


async def generate_pdf():
    from playwright.async_api import async_playwright

    # Leer y convertir markdown
    md_content = MD_PATH.read_text(encoding="utf-8")
    body_html  = md_to_html(md_content)

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>FRD ReporteCobranzas v2.0</title>
<style>{CSS}</style>
</head>
<body>
{COVER_HTML}
<div class="content">
{body_html}
</div>
{DESIGNS_HTML}
</body>
</html>"""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page    = await browser.new_page()

        await page.set_content(full_html, wait_until="networkidle")

        await page.pdf(
            path=str(PDF_PATH),
            format="A4",
            print_background=True,
            margin={
                "top":    "18mm",
                "bottom": "18mm",
                "left":   "18mm",
                "right":  "18mm",
            },
        )

        await browser.close()

    print(f"✅  PDF generado: {PDF_PATH}")


if __name__ == "__main__":
    if not MD_PATH.exists():
        print(f"❌  No se encontró: {MD_PATH}")
        raise SystemExit(1)

    asyncio.run(generate_pdf())
