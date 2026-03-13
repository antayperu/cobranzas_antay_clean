"""
Script de uso único: genera PROPUESTA_CRM_WHATSAPP_v1.0.pdf en la raíz del proyecto.
Usa Playwright (ya instalado) para renderizar HTML → PDF.
Ejecutar: python generar_propuesta_pdf.py
"""

import asyncio
import os
import sys

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Propuesta CRM WhatsApp — Antay/DACTA</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    color: #1a2332;
    background: #fff;
    font-size: 11pt;
    line-height: 1.6;
  }

  /* ── PÁGINA ── */
  .page { width: 100%; page-break-after: always; padding: 0; }
  .page:last-child { page-break-after: avoid; }

  /* ── PORTADA ── */
  .cover {
    background: linear-gradient(145deg, #0D3B66 0%, #1a6fa8 50%, #0B7285 100%);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 60px 80px;
    color: white;
    position: relative;
    overflow: hidden;
  }
  .cover::before {
    content: '';
    position: absolute;
    top: -100px; right: -100px;
    width: 400px; height: 400px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
  }
  .cover::after {
    content: '';
    position: absolute;
    bottom: -80px; left: -80px;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
  }
  .cover-badge {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 30px;
    padding: 8px 24px;
    font-size: 10pt;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 40px;
  }
  .cover-title {
    font-size: 38pt;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 20px;
    letter-spacing: -0.5px;
  }
  .cover-title span { color: #48CAE4; }
  .cover-subtitle {
    font-size: 16pt;
    font-weight: 300;
    opacity: 0.9;
    margin-bottom: 50px;
    max-width: 600px;
  }
  .cover-meta {
    display: flex;
    gap: 40px;
    margin-top: 10px;
  }
  .cover-meta-item { text-align: center; }
  .cover-meta-item .val {
    font-size: 22pt;
    font-weight: 800;
    color: #48CAE4;
    display: block;
  }
  .cover-meta-item .lbl {
    font-size: 9pt;
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .cover-footer {
    position: absolute;
    bottom: 30px;
    font-size: 9pt;
    opacity: 0.5;
  }

  /* ── CONTENIDO GENERAL ── */
  .content { padding: 50px 60px; }

  /* ── CABECERAS DE SECCIÓN ── */
  .section-header {
    border-left: 5px solid #0D3B66;
    padding: 6px 0 6px 18px;
    margin: 40px 0 20px 0;
  }
  .section-header h2 {
    font-size: 16pt;
    font-weight: 700;
    color: #0D3B66;
  }
  .section-header p {
    font-size: 10pt;
    color: #556B82;
    margin-top: 3px;
  }

  .feature-number {
    display: inline-block;
    background: #0D3B66;
    color: white;
    border-radius: 50%;
    width: 28px; height: 28px;
    text-align: center;
    line-height: 28px;
    font-size: 11pt;
    font-weight: 700;
    margin-right: 10px;
    vertical-align: middle;
  }

  /* ── GAP TABLE ── */
  .gap-table, .schema-table, .timeline-table, .data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 10pt;
  }
  .gap-table th, .schema-table th, .timeline-table th, .data-table th {
    background: #0D3B66;
    color: white;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
  }
  .gap-table td, .schema-table td, .timeline-table td, .data-table td {
    padding: 9px 14px;
    border-bottom: 1px solid #e8eef5;
    vertical-align: top;
  }
  .gap-table tr:nth-child(even) td,
  .schema-table tr:nth-child(even) td,
  .data-table tr:nth-child(even) td {
    background: #f7fafd;
  }
  .impact-high { color: #c0392b; font-weight: 600; }
  .impact-med  { color: #e67700; font-weight: 600; }

  /* ── MOCKUP UI ── */
  .ui-mockup {
    border: 2px solid #d1dce8;
    border-radius: 10px;
    overflow: hidden;
    margin: 20px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  }
  .ui-mockup-bar {
    background: #f0f4f8;
    border-bottom: 1px solid #d1dce8;
    padding: 9px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
  .dot-r { background: #ff6b6b; }
  .dot-y { background: #ffd43b; }
  .dot-g { background: #51cf66; }
  .ui-mockup-title {
    margin-left: 8px;
    font-size: 9pt;
    font-weight: 600;
    color: #4a5568;
  }
  .ui-mockup-body { padding: 20px; background: #fff; }

  /* ── KPI ROW ── */
  .kpi-row {
    display: flex;
    gap: 12px;
    margin-bottom: 18px;
  }
  .kpi-card {
    flex: 1;
    background: linear-gradient(135deg, #0D3B66, #1a6fa8);
    border-radius: 8px;
    padding: 14px 16px;
    color: white;
    text-align: center;
  }
  .kpi-card.green { background: linear-gradient(135deg, #2B8A3E, #43aa5c); }
  .kpi-card.orange { background: linear-gradient(135deg, #e67700, #f59f00); }
  .kpi-card.red { background: linear-gradient(135deg, #c0392b, #e74c3c); }
  .kpi-card.teal { background: linear-gradient(135deg, #0B7285, #1098ad); }
  .kpi-val { font-size: 20pt; font-weight: 800; }
  .kpi-lbl { font-size: 8pt; opacity: 0.85; margin-top: 3px; }

  /* ── TABLA DE CLIENTES MOCKUP ── */
  .mock-table { width: 100%; border-collapse: collapse; font-size: 9pt; }
  .mock-table th {
    background: #f0f4f8;
    color: #4a5568;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #d1dce8;
  }
  .mock-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #edf2f7;
    vertical-align: middle;
  }
  .mock-table tr:hover td { background: #f7fafd; }

  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 8pt;
    font-weight: 600;
  }
  .badge-pending   { background: #fff3cd; color: #856404; }
  .badge-sent      { background: #d1fae5; color: #065f46; }
  .badge-agreed    { background: #dbeafe; color: #1e40af; }
  .badge-nocontact { background: #f1f5f9; color: #475569; }
  .badge-tolegal   { background: #ffe4e6; color: #9f1239; }
  .badge-promised  { background: #fef3c7; color: #92400e; }

  .resultado-select {
    border: 1px solid #cbd5e0;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 8pt;
    background: white;
    color: #4a5568;
  }

  .btn {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 8.5pt;
    font-weight: 600;
    cursor: pointer;
    border: none;
  }
  .btn-primary { background: #0D3B66; color: white; }
  .btn-green   { background: #2B8A3E; color: white; }
  .btn-orange  { background: #e67700; color: white; }
  .btn-outline { background: white; color: #0D3B66; border: 1px solid #0D3B66; }

  /* ── TEMPLATE CARDS ── */
  .template-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin: 16px 0;
  }
  .template-card {
    border: 1px solid #d1dce8;
    border-radius: 8px;
    padding: 14px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .template-card.active {
    border: 2px solid #0D3B66;
    background: #f0f7ff;
  }
  .template-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }
  .template-icon { font-size: 18pt; }
  .template-name { font-weight: 700; font-size: 10pt; color: #0D3B66; }
  .template-desc { font-size: 8.5pt; color: #556B82; }
  .template-mora  {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 7.5pt;
    font-weight: 600;
    margin-top: 6px;
  }
  .mora-green  { background: #d1fae5; color: #065f46; }
  .mora-yellow { background: #fef9c3; color: #854d0e; }
  .mora-orange { background: #ffedd5; color: #9a3412; }
  .mora-red    { background: #fee2e2; color: #991b1b; }
  .mora-blue   { background: #dbeafe; color: #1e40af; }
  .mora-purple { background: #ede9fe; color: #5b21b6; }
  .mora-teal   { background: #ccfbf1; color: #065f46; }

  /* ── MENSAJE WHATSAPP PREVIEW ── */
  .wa-preview {
    background: #e5ddd5;
    border-radius: 10px;
    padding: 20px;
    margin: 12px 0;
  }
  .wa-bubble {
    background: #dcf8c6;
    border-radius: 8px 8px 0 8px;
    padding: 12px 16px;
    max-width: 85%;
    margin-left: auto;
    font-size: 9pt;
    white-space: pre-wrap;
    line-height: 1.5;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
  }
  .wa-bubble-label {
    font-size: 7.5pt;
    color: #888;
    text-align: right;
    margin-top: 4px;
  }
  .wa-header {
    background: #075E54;
    color: white;
    padding: 10px 16px;
    border-radius: 10px 10px 0 0;
    margin: -20px -20px 16px -20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 9.5pt;
    font-weight: 600;
  }
  .wa-avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: #25D366;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14pt;
  }

  /* ── ACUERDOS ── */
  .acuerdo-form {
    background: #f7fafd;
    border: 1px solid #d1dce8;
    border-radius: 8px;
    padding: 20px;
    margin: 14px 0;
  }
  .form-row {
    display: flex;
    gap: 14px;
    margin-bottom: 12px;
  }
  .form-field { flex: 1; }
  .form-label { font-size: 8pt; font-weight: 600; color: #4a5568; margin-bottom: 4px; }
  .form-input {
    width: 100%;
    border: 1px solid #cbd5e0;
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 9pt;
    background: white;
    color: #4a5568;
  }

  .cuotas-timeline { margin: 16px 0; }
  .cuota-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-left: 3px solid #d1dce8;
    margin-bottom: 6px;
    background: #f7fafd;
    border-radius: 0 6px 6px 0;
  }
  .cuota-item.paid { border-left-color: #2B8A3E; background: #f0fdf4; }
  .cuota-item.due  { border-left-color: #e67700; background: #fffbeb; }
  .cuota-item.overdue { border-left-color: #c0392b; background: #fef2f2; }
  .cuota-num { width: 28px; height: 28px; border-radius: 50%; background: #0D3B66; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 9pt; flex-shrink: 0; }
  .cuota-info { flex: 1; font-size: 9pt; }
  .cuota-monto { font-weight: 700; font-size: 10pt; color: #0D3B66; }

  /* ── BANDEJA DE PENDIENTES ── */
  .pending-item {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 14px 16px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-bottom: 10px;
  }
  .pending-item.urgent { border-left: 4px solid #c0392b; background: #fef2f2; }
  .pending-item.warn   { border-left: 4px solid #e67700; background: #fffbeb; }
  .pending-item.info   { border-left: 4px solid #0B7285; background: #f0fdfa; }
  .pending-icon { font-size: 22pt; }
  .pending-body { flex: 1; }
  .pending-title { font-weight: 700; font-size: 10pt; color: #1a2332; }
  .pending-detail { font-size: 9pt; color: #556B82; margin-top: 3px; }
  .pending-actions { display: flex; gap: 8px; margin-top: 10px; }

  /* ── AGING SMART ── */
  .aging-row {
    display: flex;
    gap: 0;
    border-radius: 8px;
    overflow: hidden;
    margin: 14px 0;
  }
  .aging-segment {
    flex: 1;
    padding: 16px 12px;
    text-align: center;
    color: white;
  }
  .aging-segment.g1 { background: #2B8A3E; }
  .aging-segment.g2 { background: #e67700; }
  .aging-segment.g3 { background: #d63031; }
  .aging-segment.g4 { background: #6c1c1c; }
  .aging-days { font-size: 13pt; font-weight: 800; }
  .aging-label { font-size: 8pt; opacity: 0.9; margin-top: 4px; }
  .aging-template { font-size: 8pt; background: rgba(255,255,255,0.2); border-radius: 4px; padding: 2px 8px; margin-top: 6px; display: inline-block; }

  /* ── ROADMAP ── */
  .roadmap { margin: 20px 0; }
  .roadmap-item {
    display: flex;
    gap: 20px;
    padding: 16px 0;
    border-bottom: 1px solid #e8eef5;
  }
  .roadmap-item:last-child { border-bottom: none; }
  .roadmap-tier {
    width: 90px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding-top: 4px;
  }
  .tier-badge {
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 8pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .tier-1 { background: #0D3B66; color: white; }
  .tier-2 { background: #0B7285; color: white; }
  .tier-3 { background: #556B82; color: white; }
  .roadmap-content { flex: 1; }
  .roadmap-title { font-weight: 700; font-size: 11pt; color: #0D3B66; margin-bottom: 6px; }
  .roadmap-desc { font-size: 9.5pt; color: #4a5568; margin-bottom: 8px; }
  .roadmap-pills { display: flex; gap: 8px; flex-wrap: wrap; }
  .pill {
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 8pt;
    font-weight: 600;
  }
  .pill-time { background: #eff6ff; color: #1e40af; }
  .pill-file { background: #f0fdf4; color: #065f46; }
  .pill-sql  { background: #fdf4ff; color: #7e22ce; }

  /* ── SQL BLOCK ── */
  .sql-block {
    background: #1a2332;
    color: #a8d8ea;
    border-radius: 8px;
    padding: 18px 20px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 8.5pt;
    margin: 14px 0;
    line-height: 1.7;
    overflow: hidden;
  }
  .sql-kw  { color: #f9ca24; font-weight: 700; }
  .sql-type { color: #55efc4; }
  .sql-comment { color: #636e72; font-style: italic; }
  .sql-str { color: #fd79a8; }

  /* ── CALLOUTS ── */
  .callout {
    border-radius: 8px;
    padding: 14px 18px;
    margin: 14px 0;
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }
  .callout-info    { background: #eff6ff; border-left: 4px solid #3b82f6; }
  .callout-success { background: #f0fdf4; border-left: 4px solid #22c55e; }
  .callout-warn    { background: #fffbeb; border-left: 4px solid #f59e0b; }
  .callout-icon { font-size: 16pt; flex-shrink: 0; }
  .callout-body { font-size: 9.5pt; color: #374151; }
  .callout-body strong { display: block; font-weight: 700; margin-bottom: 3px; }

  /* ── PAGE HEADER ── */
  .page-header {
    background: #f7fafd;
    border-bottom: 2px solid #e2e8f0;
    padding: 16px 60px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .page-header-logo { font-weight: 800; font-size: 11pt; color: #0D3B66; }
  .page-header-section { font-size: 9pt; color: #556B82; }

  /* ── FOOTER ── */
  .page-footer {
    border-top: 1px solid #e2e8f0;
    padding: 10px 60px;
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: #9ca3af;
    margin-top: 40px;
  }

  h3 { font-size: 12pt; font-weight: 700; color: #0D3B66; margin: 20px 0 10px 0; }
  h4 { font-size: 10.5pt; font-weight: 600; color: #1a2332; margin: 16px 0 8px 0; }
  p  { margin: 8px 0; font-size: 10pt; color: #374151; }
  ul { margin: 8px 0 8px 20px; }
  li { font-size: 10pt; color: #374151; margin-bottom: 4px; }
  strong { font-weight: 700; }

  @media print {
    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
</style>
</head>
<body>

<!-- ═══════════════════════════════════════ PORTADA ═══════════════════════ -->
<div class="page">
<div class="cover">
  <div class="cover-badge">Propuesta Técnica v1.0 — Marzo 2026</div>
  <div class="cover-title">
    Sistema de Gestión de<br>Cobranza <span>WhatsApp CRM</span>
  </div>
  <div class="cover-subtitle">
    Transformando el módulo de notificaciones en un motor de cobranza inteligente,
    trazable y orientado a resultados para DACTA S.A.C.
  </div>
  <div class="cover-meta">
    <div class="cover-meta-item">
      <span class="val">8</span>
      <span class="lbl">Mejoras propuestas</span>
    </div>
    <div class="cover-meta-item">
      <span class="val">3</span>
      <span class="lbl">Tiers de prioridad</span>
    </div>
    <div class="cover-meta-item">
      <span class="val">2</span>
      <span class="lbl">Nuevas tablas SQL</span>
    </div>
    <div class="cover-meta-item">
      <span class="val">7</span>
      <span class="lbl">Templates WA</span>
    </div>
  </div>
  <div class="cover-footer">ReporteCobranzas · Antay Methodology · Supabase + Streamlit + Playwright</div>
</div>
</div>


<!-- ════════════════════════════════ SECCIÓN 1: DIAGNÓSTICO ═══════════════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 1 — Diagnóstico del Sistema Actual</span>
</div>
<div class="content">

<div class="section-header">
  <h2>1. Diagnóstico: ¿Dónde está el límite actual?</h2>
  <p>El sistema hoy funciona como un "lanzador de mensajes". Necesita convertirse en un flujo de trabajo de cobranza.</p>
</div>

<div class="callout callout-warn">
  <span class="callout-icon">⚠️</span>
  <div class="callout-body">
    <strong>Problema central</strong>
    El módulo WhatsApp actual envía el mensaje y "se olvida". No hay seguimiento de si el cliente respondió, si llegó a un acuerdo, si prometió pagar. El gestor trabaja a ciegas después del envío.
  </div>
</div>

<table class="gap-table">
  <thead>
    <tr>
      <th>Gap identificado</th>
      <th>Situación actual</th>
      <th>Impacto operativo</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Plantilla única</strong></td>
      <td>Un solo mensaje para todos los clientes, sin importar días de mora</td>
      <td class="impact-high">El primer aviso suena igual que el ultimátum</td>
    </tr>
    <tr>
      <td><strong>Sin resultado post-envío</strong></td>
      <td>Después de enviar el WA, el CRM queda ciego</td>
      <td class="impact-high">No se sabe quién respondió, quién ignoró, quién prometió pagar</td>
    </tr>
    <tr>
      <td><strong>Sin acuerdos de pago</strong></td>
      <td>"Me comprometo a pagar el viernes" no se puede registrar</td>
      <td class="impact-high">El acuerdo vive solo en la memoria del gestor</td>
    </tr>
    <tr>
      <td><strong>Sin escalation automática</strong></td>
      <td>Sin recordatorios basados en aging ni comportamiento</td>
      <td class="impact-med">Todo es manual, no escala con el volumen de cartera</td>
    </tr>
    <tr>
      <td><strong>Sin lógica por días de mora</strong></td>
      <td>Cliente de 5 días = cliente de 90 días (mismo trato)</td>
      <td class="impact-high">Riesgo de perder clientes buenos + suavizar morosos crónicos</td>
    </tr>
    <tr>
      <td><strong>Centro de Gestiones pasivo</strong></td>
      <td>Solo lectura / historial. No hay lista de acción diaria</td>
      <td class="impact-med">El gestor no tiene un "tablero de trabajo" del día</td>
    </tr>
    <tr>
      <td><strong>Sin KPIs de efectividad</strong></td>
      <td>No se mide tasa de respuesta, monto recuperado, acuerdos cumplidos</td>
      <td class="impact-med">No se puede medir si la gestión está funcionando</td>
    </tr>
  </tbody>
</table>

<h3>Flujo actual vs. flujo propuesto</h3>

<div style="display:flex; gap:20px; margin:16px 0;">
  <div style="flex:1; border:2px solid #fee2e2; border-radius:8px; padding:16px; background:#fef2f2;">
    <div style="font-weight:700; color:#991b1b; margin-bottom:10px; font-size:10pt;">❌ HOY — Flujo incompleto</div>
    <div style="font-size:9pt; color:#4a5568; line-height:2;">
      1. Cargar Excel → Procesar ciclo<br>
      2. Ir a tab WhatsApp<br>
      3. Click "Enviar a todos"<br>
      4. ✅ Enviado → ¿Y ahora? NADA.<br>
      <br>
      <em>El gestor anota en un papel o en Excel aparte qué dijo cada cliente.</em>
    </div>
  </div>
  <div style="flex:1; border:2px solid #d1fae5; border-radius:8px; padding:16px; background:#f0fdf4;">
    <div style="font-weight:700; color:#065f46; margin-bottom:10px; font-size:10pt;">✅ PROPUESTO — Flujo completo</div>
    <div style="font-size:9pt; color:#4a5568; line-height:2;">
      1. Cargar Excel → Procesar ciclo<br>
      2. Sistema sugiere template por días de mora<br>
      3. Enviar con template correcto por segmento<br>
      4. Registrar resultado por cliente (acordó / prometió / no contestó)<br>
      5. Acuerdos de pago en Supabase con cuotas<br>
      6. Bandeja de pendientes con trabajo del día<br>
      7. KPIs: monto gestionado, tasa de respuesta, recuperación
    </div>
  </div>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 2</span>
</div>
</div>


<!-- ════════════════════════════════ SECCIÓN 2: RESULTADO POST-ENVÍO ═══════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 2 — Feature 1: Resultado Post-Envío</span>
</div>
<div class="content">

<div class="section-header">
  <h2><span class="feature-number">1</span>Resultado Post-Envío en el Tab WhatsApp</h2>
  <p>Convierte el tab de "lanzador de mensajes" en un flujo de trabajo de cobranza activo.</p>
</div>

<div class="callout callout-success">
  <span class="callout-icon">💡</span>
  <div class="callout-body">
    <strong>Valor inmediato para el gestor</strong>
    Después de enviar el lote de WhatsApp, el gestor puede registrar en la misma pantalla qué respondió cada cliente. Un click actualiza <code>gestiones.resultado</code> en Supabase y queda trazado para siempre.
  </div>
</div>

<h3>Diseño de ventana propuesto</h3>

<div class="ui-mockup">
  <div class="ui-mockup-bar">
    <span class="dot dot-r"></span>
    <span class="dot dot-y"></span>
    <span class="dot dot-g"></span>
    <span class="ui-mockup-title">Tab: 📲 Marketing WhatsApp — Panel de Seguimiento Post-Envío</span>
  </div>
  <div class="ui-mockup-body">

    <!-- KPI row -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-val">24</div>
        <div class="kpi-lbl">📤 Enviados hoy</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-val">8</div>
        <div class="kpi-lbl">✅ Con respuesta</div>
      </div>
      <div class="kpi-card orange">
        <div class="kpi-val">5</div>
        <div class="kpi-lbl">⏰ Pendientes respuesta</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-val">2</div>
        <div class="kpi-lbl">❌ Sin contacto</div>
      </div>
      <div class="kpi-card teal">
        <div class="kpi-val">S/ 48,200</div>
        <div class="kpi-lbl">💰 Monto gestionado</div>
      </div>
    </div>

    <!-- Tabla de clientes con resultado -->
    <div style="font-weight:700; font-size:9.5pt; color:#0D3B66; margin-bottom:8px;">
      📋 Clientes contactados hoy — Registre el resultado de cada gestión
    </div>
    <table class="mock-table">
      <thead>
        <tr>
          <th>Cliente</th>
          <th>Teléfono</th>
          <th>Saldo Real</th>
          <th>Días Mora</th>
          <th>Enviado</th>
          <th>Resultado de Gestión</th>
          <th>Notas</th>
          <th>Acción</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>COMERCIAL LIMA S.A.</strong></td>
          <td>+51 987-654-321</td>
          <td><strong>S/ 12,400</strong></td>
          <td><span style="color:#c0392b;font-weight:700;">47 días</span></td>
          <td>10:32 AM</td>
          <td>
            <select class="resultado-select">
              <option value="ACORDÓ_PAGO" selected>✅ Acordó pago</option>
            </select>
          </td>
          <td><span style="font-size:8pt;color:#065f46;">Paga el viernes 14/03</span></td>
          <td><span class="btn btn-green" style="font-size:7.5pt;padding:4px 10px;">📋 Registrar Acuerdo</span></td>
        </tr>
        <tr>
          <td><strong>INVERSIONES NORTE</strong></td>
          <td>+51 912-345-678</td>
          <td><strong>S/ 8,750</strong></td>
          <td><span style="color:#e67700;font-weight:700;">22 días</span></td>
          <td>10:33 AM</td>
          <td>
            <select class="resultado-select">
              <option>⏳ Pendiente respuesta</option>
              <option selected>📞 Prometió pagar</option>
              <option>❌ No contesta</option>
            </select>
          </td>
          <td><span style="font-size:8pt;color:#92400e;">Esta semana deposita</span></td>
          <td><span class="btn btn-outline" style="font-size:7.5pt;padding:4px 10px;">💾 Guardar</span></td>
        </tr>
        <tr>
          <td><strong>DISTRIBUIDORA SUR</strong></td>
          <td>+51 945-678-901</td>
          <td><strong>$ 3,200</strong></td>
          <td><span style="color:#c0392b;font-weight:700;">68 días</span></td>
          <td>10:35 AM</td>
          <td>
            <select class="resultado-select">
              <option>⏳ Pendiente respuesta</option>
              <option selected>⚖️ Derivar a Legal</option>
            </select>
          </td>
          <td><span style="font-size:8pt;color:#9f1239;">3er aviso sin respuesta</span></td>
          <td><span class="btn btn-orange" style="font-size:7.5pt;padding:4px 10px;">⚖️ Escalar</span></td>
        </tr>
        <tr style="opacity:0.6;">
          <td><strong>SERVICIOS ANDINOS</strong></td>
          <td>+51 956-789-012</td>
          <td><strong>S/ 2,100</strong></td>
          <td><span style="color:#2B8A3E;font-weight:700;">8 días</span></td>
          <td>10:36 AM</td>
          <td>
            <select class="resultado-select">
              <option selected>⏳ Pendiente respuesta</option>
            </select>
          </td>
          <td><span style="font-size:8pt;color:#9ca3af;font-style:italic;">Sin novedad aún...</span></td>
          <td><span class="btn btn-outline" style="font-size:7.5pt;padding:4px 10px;">💾 Guardar</span></td>
        </tr>
      </tbody>
    </table>

    <div style="margin-top:14px; display:flex; gap:10px; justify-content:flex-end;">
      <span class="btn btn-outline">📥 Exportar resultados CSV</span>
      <span class="btn btn-primary">💾 Guardar todos los resultados</span>
    </div>

  </div>
</div>

<h3>Opciones de resultado disponibles</h3>
<div style="display:flex; flex-wrap:wrap; gap:8px; margin:10px 0;">
  <span class="badge badge-pending">⏳ Pendiente respuesta</span>
  <span class="badge badge-agreed">✅ Acordó pago</span>
  <span class="badge badge-promised">📞 Prometió pagar</span>
  <span class="badge badge-nocontact">❌ No contesta</span>
  <span style="background:#f0fdf4;color:#065f46;" class="badge">💳 Ya pagó</span>
  <span style="background:#ede9fe;color:#5b21b6;" class="badge">🔄 Pago parcial</span>
  <span class="badge badge-tolegal">⚖️ Derivar a Legal</span>
  <span style="background:#e2e8f0;color:#475569;" class="badge">📵 Número inválido</span>
</div>

<h3>Cambios técnicos requeridos</h3>
<div class="roadmap-pills" style="margin-top:8px;">
  <span class="pill pill-file">utils/ui/tabs/whatsapp.py</span>
  <span class="pill pill-file">utils/db_manager.py</span>
  <span class="pill pill-time">Estimado: 1–2 horas</span>
  <span class="pill pill-sql">gestiones.resultado (campo existente)</span>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 3</span>
</div>
</div>


<!-- ════════════════════════════════ SECCIÓN 3: BIBLIOTECA DE PLANTILLAS ══ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 3 — Feature 2: Biblioteca de Plantillas WA</span>
</div>
<div class="content">

<div class="section-header">
  <h2><span class="feature-number">2</span>Biblioteca de 7 Plantillas WhatsApp por Escenario</h2>
  <p>El mensaje correcto, en el momento correcto, con el tono adecuado para cada situación de cobranza.</p>
</div>

<h3>Selector de plantilla en el tab WhatsApp (diseño propuesto)</h3>

<div class="ui-mockup">
  <div class="ui-mockup-bar">
    <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
    <span class="ui-mockup-title">Selección de Plantilla — se muestra antes del envío del lote</span>
  </div>
  <div class="ui-mockup-body">
    <div style="font-size:9pt; color:#556B82; margin-bottom:14px;">
      📌 Seleccione la plantilla apropiada para este lote. La app sugerirá automáticamente según los días de mora promedio.
    </div>
    <div class="template-grid">
      <div class="template-card active">
        <div class="template-card-header">
          <span class="template-icon">📋</span>
          <span class="template-name">PRIMER AVISO</span>
        </div>
        <div class="template-desc">Notificación inicial de deuda. Tono informativo y profesional. Incluye detalle completo de documentos.</div>
        <span class="template-mora mora-green">✅ 0–14 días mora · Sugerido para este lote</span>
      </div>
      <div class="template-card">
        <div class="template-card-header">
          <span class="template-icon">⏰</span>
          <span class="template-name">RECORDATORIO</span>
        </div>
        <div class="template-desc">Seguimiento sin respuesta al primer aviso. Tono amable pero firme. Menciona el aviso anterior.</div>
        <span class="template-mora mora-yellow">15–30 días mora</span>
      </div>
      <div class="template-card">
        <div class="template-card-header">
          <span class="template-icon">🔴</span>
          <span class="template-name">AVISO FIRME</span>
        </div>
        <div class="template-desc">Deuda con mora significativa. Urgencia clara. Solicita comunicación inmediata con el ejecutivo.</div>
        <span class="template-mora mora-orange">31–60 días mora</span>
      </div>
      <div class="template-card">
        <div class="template-card-header">
          <span class="template-icon">⚖️</span>
          <span class="template-name">PRE-LEGAL</span>
        </div>
        <div class="template-desc">Aviso formal de derivación al área legal. Solo si no hubo respuesta previa. Requiere aprobación.</div>
        <span class="template-mora mora-red">60+ días mora</span>
      </div>
      <div class="template-card">
        <div class="template-card-header">
          <span class="template-icon">✅</span>
          <span class="template-name">CONFIRMAR ACUERDO</span>
        </div>
        <div class="template-desc">Confirma el acuerdo de pago registrado. Detalla monto, fecha y forma de pago acordados.</div>
        <span class="template-mora mora-blue">Acuerdos recién registrados</span>
      </div>
      <div class="template-card">
        <div class="template-card-header">
          <span class="template-icon">📅</span>
          <span class="template-name">RECORDATORIO DE CUOTA</span>
        </div>
        <div class="template-desc">Recuerda que una cuota del acuerdo vence en los próximos días. Incluye monto y fecha exacta.</div>
        <span class="template-mora mora-purple">Cuotas venciendo en 1–3 días</span>
      </div>
    </div>
    <div style="margin-top:6px; display:flex; gap:10px;">
      <span class="btn btn-primary">✅ Confirmar plantilla y continuar</span>
      <span class="btn btn-outline">✏️ Editar plantilla antes de enviar</span>
    </div>
  </div>
</div>

<h3>Ejemplos de mensajes WhatsApp por cada plantilla</h3>

<h4>📋 PRIMER AVISO — Ejemplo real generado por la app</h4>
<div class="wa-preview">
  <div class="wa-header">
    <div class="wa-avatar">🏢</div>
    <div>
      <div>DACTA S.A.C.</div>
      <div style="font-size:8pt;opacity:0.8;">En línea</div>
    </div>
  </div>
  <div class="wa-bubble">Estimados COMERCIAL LIMA S.A.C.,

Les saludamos de DACTA S.A.C. y les comunicamos el estado de sus cuentas pendientes al 13/03/2026:

📊 *RESUMEN DE SALDOS:*
  · Total Soles: S/ 12,400.00
  · Total Dólares: $ 0.00
  · Detracciones SUNAT Pendientes: S/ 1,488.00

📄 *DETALLE DE DOCUMENTOS:*
  · FAC 001-00012458 | Vence: 20/02/2026 | Importe: S/ 12,400.00 | Saldo: S/ 10,912.00 | Detracción Pdta.: S/ 1,488.00

💰 *SALDO TOTAL REAL: S/ 12,400.00*

Agradecemos su atención a la brevedad. Para consultas o coordinación de pago, comuníquese con nuestro ejecutivo de cobranzas.

Atentamente,
*DACTA S.A.C.* | Cobranzas | +51 1 234-5678</div>
  <div class="wa-bubble-label">10:32 AM ✓✓</div>
</div>

<h4>⏰ RECORDATORIO — Seguimiento sin respuesta (día 22)</h4>
<div class="wa-preview">
  <div class="wa-header">
    <div class="wa-avatar">🏢</div>
    <div><div>DACTA S.A.C.</div><div style="font-size:8pt;opacity:0.8;">En línea</div></div>
  </div>
  <div class="wa-bubble">Estimados INVERSIONES NORTE S.R.L.,

Les escribimos nuevamente de *DACTA S.A.C.* Notamos que no hemos recibido respuesta a nuestra comunicación anterior del 22/02/2026.

⏰ *Su deuda acumula ya 22 días de mora.*

📄 Saldo pendiente: *S/ 8,750.00*

Le solicitamos amablemente comunicarse con nosotros a la brevedad para coordinar el pago o un plan que se ajuste a sus posibilidades.

📞 Ejecutivo: +51 1 234-5678
📧 cobranzas@dacta.pe

Atentamente,
*DACTA S.A.C.*</div>
  <div class="wa-bubble-label">10:33 AM ✓✓</div>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 4</span>
</div>
</div>


<!-- ════════════════════════════════ SECCIÓN 4: ACUERDOS DE PAGO ══════════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 4 — Feature 3: Módulo de Acuerdos de Pago</span>
</div>
<div class="content">

<div class="section-header">
  <h2><span class="feature-number">3</span>Módulo de Acuerdos de Pago con Cuotas</h2>
  <p>El activo más valioso para la cobranza: registrar, trackear y recordar compromisos de pago.</p>
</div>

<div class="callout callout-info">
  <span class="callout-icon">🎯</span>
  <div class="callout-body">
    <strong>¿Por qué es el más importante?</strong>
    Hoy los acuerdos de pago "viven" en la memoria del gestor o en un papel. Con este módulo, cada convenio queda documentado en Supabase con todas sus cuotas, fechas de vencimiento, y estado de cumplimiento. La app genera automáticamente el mensaje WA de confirmación.
  </div>
</div>

<h3>Schema de nuevas tablas SQL</h3>

<div class="sql-block">
<span class="sql-comment">-- Tabla principal de convenios de pago acordados con el cliente</span>
<span class="sql-kw">CREATE TABLE</span> acuerdos_pago (
  id                <span class="sql-type">UUID</span>           <span class="sql-kw">PRIMARY KEY DEFAULT</span> gen_random_uuid(),
  cliente_id        <span class="sql-type">TEXT</span>           <span class="sql-kw">NOT NULL REFERENCES</span> clientes(cliente_id),
  cycle_id          <span class="sql-type">TEXT</span>,          <span class="sql-comment">-- Ciclo en que se originó la deuda</span>
  monto_total       <span class="sql-type">DECIMAL(12,2)</span>  <span class="sql-kw">NOT NULL</span>,
  moneda            <span class="sql-type">TEXT</span>           <span class="sql-kw">DEFAULT</span> <span class="sql-str">'PEN'</span>,
  n_cuotas          <span class="sql-type">INTEGER</span>        <span class="sql-kw">NOT NULL DEFAULT</span> 1,
  fecha_primer_pago <span class="sql-type">DATE</span>           <span class="sql-kw">NOT NULL</span>,
  periodicidad      <span class="sql-type">TEXT</span>           <span class="sql-kw">DEFAULT</span> <span class="sql-str">'MENSUAL'</span>,  <span class="sql-comment">-- SEMANAL/QUINCENAL/MENSUAL/UNICO</span>
  estado            <span class="sql-type">TEXT</span>           <span class="sql-kw">DEFAULT</span> <span class="sql-str">'ACTIVO'</span>,    <span class="sql-comment">-- ACTIVO/CUMPLIDO/INCUMPLIDO/CANCELADO</span>
  notas             <span class="sql-type">TEXT</span>,
  registrado_en     <span class="sql-type">TIMESTAMPTZ</span>    <span class="sql-kw">DEFAULT</span> now(),
  registrado_por    <span class="sql-type">TEXT</span>
);

<span class="sql-comment">-- Detalle de cada cuota del acuerdo</span>
<span class="sql-kw">CREATE TABLE</span> cuotas_acuerdo (
  id               <span class="sql-type">UUID</span>           <span class="sql-kw">PRIMARY KEY DEFAULT</span> gen_random_uuid(),
  acuerdo_id       <span class="sql-type">UUID</span>           <span class="sql-kw">NOT NULL REFERENCES</span> acuerdos_pago(id) <span class="sql-kw">ON DELETE CASCADE</span>,
  numero_cuota     <span class="sql-type">INTEGER</span>        <span class="sql-kw">NOT NULL</span>,
  monto_cuota      <span class="sql-type">DECIMAL(12,2)</span>  <span class="sql-kw">NOT NULL</span>,
  fecha_vencimiento <span class="sql-type">DATE</span>          <span class="sql-kw">NOT NULL</span>,
  fecha_pago       <span class="sql-type">DATE</span>,          <span class="sql-comment">-- NULL = no pagada aún</span>
  estado           <span class="sql-type">TEXT</span>           <span class="sql-kw">DEFAULT</span> <span class="sql-str">'PENDIENTE'</span>,  <span class="sql-comment">-- PENDIENTE/PAGADA/VENCIDA</span>
  monto_pagado     <span class="sql-type">DECIMAL(12,2)</span>  <span class="sql-comment">-- puede ser parcial</span>
);
</div>

<h3>Ventana de registro de acuerdo de pago</h3>

<div class="ui-mockup">
  <div class="ui-mockup-bar">
    <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
    <span class="ui-mockup-title">Centro de Gestiones → Acuerdos → Nuevo Acuerdo de Pago</span>
  </div>
  <div class="ui-mockup-body">

    <div style="background:#eff6ff; border-left:4px solid #3b82f6; border-radius:6px; padding:12px 16px; margin-bottom:16px; font-size:9pt; color:#1e40af;">
      <strong>COMERCIAL LIMA S.A.C.</strong> · Saldo total: S/ 12,400.00 · 47 días de mora
    </div>

    <div class="acuerdo-form">
      <div style="font-weight:700; color:#0D3B66; font-size:10pt; margin-bottom:14px;">📋 Registrar Convenio de Pago</div>
      <div class="form-row">
        <div class="form-field">
          <div class="form-label">MONTO TOTAL DEL ACUERDO</div>
          <div class="form-input">S/ 12,400.00</div>
        </div>
        <div class="form-field">
          <div class="form-label">MONEDA</div>
          <div class="form-input">Soles (PEN)</div>
        </div>
        <div class="form-field">
          <div class="form-label">NÚMERO DE CUOTAS</div>
          <div class="form-input">3 cuotas</div>
        </div>
      </div>
      <div class="form-row">
        <div class="form-field">
          <div class="form-label">FECHA PRIMER PAGO</div>
          <div class="form-input">14/03/2026</div>
        </div>
        <div class="form-field">
          <div class="form-label">PERIODICIDAD</div>
          <div class="form-input">Mensual</div>
        </div>
        <div class="form-field">
          <div class="form-label">REGISTRADO POR</div>
          <div class="form-input">Gestor: María López</div>
        </div>
      </div>
      <div class="form-row">
        <div class="form-field">
          <div class="form-label">NOTAS DEL ACUERDO</div>
          <div class="form-input">Cliente llama el lunes para confirmar primer depósito. Solicitó facilidades por cierre de balance.</div>
        </div>
      </div>
    </div>

    <div style="font-weight:600; font-size:9.5pt; color:#0D3B66; margin:14px 0 8px;">
      📅 Cuotas generadas automáticamente
    </div>
    <div class="cuotas-timeline">
      <div class="cuota-item">
        <div class="cuota-num">1</div>
        <div class="cuota-info">
          <div>Cuota 1 de 3 · Vence: <strong>14/03/2026</strong></div>
          <div style="color:#556B82; font-size:8pt;">Primer pago acordado en llamada</div>
        </div>
        <div class="cuota-monto">S/ 4,133.33</div>
        <span class="badge badge-pending" style="margin-left:10px;">PENDIENTE</span>
      </div>
      <div class="cuota-item">
        <div class="cuota-num">2</div>
        <div class="cuota-info">
          <div>Cuota 2 de 3 · Vence: <strong>14/04/2026</strong></div>
        </div>
        <div class="cuota-monto">S/ 4,133.33</div>
        <span class="badge badge-pending" style="margin-left:10px;">PENDIENTE</span>
      </div>
      <div class="cuota-item">
        <div class="cuota-num">3</div>
        <div class="cuota-info">
          <div>Cuota 3 de 3 · Vence: <strong>14/05/2026</strong></div>
        </div>
        <div class="cuota-monto">S/ 4,133.34</div>
        <span class="badge badge-pending" style="margin-left:10px;">PENDIENTE</span>
      </div>
    </div>

    <div style="margin-top:14px; display:flex; gap:10px;">
      <span class="btn btn-primary">💾 Guardar Acuerdo en Supabase</span>
      <span class="btn btn-green">📲 Guardar y Enviar Confirmación WA</span>
      <span class="btn btn-outline">✖ Cancelar</span>
    </div>
  </div>
</div>

<h4>💳 Mensaje WA de Confirmación de Acuerdo (generado automáticamente)</h4>
<div class="wa-preview">
  <div class="wa-header">
    <div class="wa-avatar">🏢</div>
    <div><div>DACTA S.A.C.</div><div style="font-size:8pt;opacity:0.8;">En línea</div></div>
  </div>
  <div class="wa-bubble">Estimados COMERCIAL LIMA S.A.C.,

Confirmamos el convenio de pago acordado para regularizar su deuda con *DACTA S.A.C.*:

✅ *ACUERDO DE PAGO REGISTRADO*
  · Monto total: *S/ 12,400.00*
  · Número de cuotas: *3 pagos mensuales*

📅 *CALENDARIO DE PAGOS:*
  · Cuota 1: S/ 4,133.33 → *14 de Marzo 2026*
  · Cuota 2: S/ 4,133.33 → *14 de Abril 2026*
  · Cuota 3: S/ 4,133.34 → *14 de Mayo 2026*

Le enviaremos un recordatorio 2 días antes de cada vencimiento.
Para coordinaciones: +51 1 234-5678

Gracias por su compromiso.
*DACTA S.A.C.*</div>
  <div class="wa-bubble-label">11:05 AM ✓✓</div>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 5</span>
</div>
</div>


<!-- ════════════════════════════════ SECCIÓN 5: BANDEJA PENDIENTES ════════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 5 — Feature 4 y 5: Bandeja de Pendientes + Escalation Inteligente</span>
</div>
<div class="content">

<div class="section-header">
  <h2><span class="feature-number">4</span>Bandeja de Pendientes — El Trabajo del Día del Gestor</h2>
  <p>Una lista priorizada, generada automáticamente cada mañana, con todo lo que necesita atención hoy.</p>
</div>

<div class="ui-mockup">
  <div class="ui-mockup-bar">
    <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
    <span class="ui-mockup-title">Centro de Gestiones → 📋 Pendientes del Día — Viernes 13/03/2026</span>
  </div>
  <div class="ui-mockup-body">

    <div style="font-size:9pt; color:#556B82; margin-bottom:16px;">
      🤖 El sistema identificó <strong style="color:#0D3B66;">7 acciones prioritarias</strong> para hoy
    </div>

    <!-- URGENTE -->
    <div style="font-size:8.5pt; font-weight:700; color:#991b1b; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">🚨 URGENTE — Acción inmediata</div>

    <div class="pending-item urgent">
      <span class="pending-icon">⚖️</span>
      <div class="pending-body">
        <div class="pending-title">DISTRIBUIDORA SUR E.I.R.L. — 68 días de mora</div>
        <div class="pending-detail">Saldo: $ 3,200.00 · Tercer aviso enviado hace 5 días sin respuesta · Recomendado: escalar a área legal</div>
        <div class="pending-actions">
          <span class="btn btn-orange" style="font-size:7.5pt;padding:4px 10px;">⚖️ Enviar Pre-Legal WA</span>
          <span class="btn btn-outline" style="font-size:7.5pt;padding:4px 10px;">📞 Registrar llamada</span>
        </div>
      </div>
      <span class="badge" style="background:#fee2e2;color:#991b1b;white-space:nowrap;">68 días mora</span>
    </div>

    <div class="pending-item urgent">
      <span class="pending-icon">📅</span>
      <div class="pending-body">
        <div class="pending-title">COMERCIAL LIMA S.A.C. — Cuota vence HOY</div>
        <div class="pending-detail">Acuerdo de pago activo · Cuota 1/3 de S/ 4,133.33 vence hoy 14/03/2026 · Sin confirmar pago aún</div>
        <div class="pending-actions">
          <span class="btn btn-primary" style="font-size:7.5pt;padding:4px 10px;">📲 Enviar Recordatorio WA</span>
          <span class="btn btn-green" style="font-size:7.5pt;padding:4px 10px;">✅ Marcar cuota pagada</span>
        </div>
      </div>
      <span class="badge" style="background:#fef3c7;color:#92400e;white-space:nowrap;">Vence hoy</span>
    </div>

    <!-- ESTA SEMANA -->
    <div style="font-size:8.5pt; font-weight:700; color:#b45309; text-transform:uppercase; letter-spacing:1px; margin:16px 0 8px;">⏰ ESTA SEMANA — Seguimiento pendiente</div>

    <div class="pending-item warn">
      <span class="pending-icon">📵</span>
      <div class="pending-body">
        <div class="pending-title">INVERSIONES NORTE S.R.L. — Sin respuesta 72 horas</div>
        <div class="pending-detail">WA enviado el 11/03 · Prometió pagar "esta semana" · Saldo S/ 8,750.00 · 22 días mora</div>
        <div class="pending-actions">
          <span class="btn btn-orange" style="font-size:7.5pt;padding:4px 10px;">⏰ Enviar Recordatorio WA</span>
          <span class="btn btn-outline" style="font-size:7.5pt;padding:4px 10px;">❌ Marcar no contesta</span>
        </div>
      </div>
      <span class="badge" style="background:#ffedd5;color:#9a3412;white-space:nowrap;">72h sin resp.</span>
    </div>

    <div class="pending-item warn">
      <span class="pending-icon">📅</span>
      <div class="pending-body">
        <div class="pending-title">GRUPO ANDINO S.A.C. — Cuota vence en 2 días</div>
        <div class="pending-detail">Acuerdo activo · Cuota 2/3 de S/ 2,500.00 vence el 16/03/2026 · Enviar recordatorio preventivo</div>
        <div class="pending-actions">
          <span class="btn btn-primary" style="font-size:7.5pt;padding:4px 10px;">📲 Enviar Recordatorio de Cuota</span>
        </div>
      </div>
      <span class="badge" style="background:#fef9c3;color:#854d0e;white-space:nowrap;">En 2 días</span>
    </div>

    <!-- INFO -->
    <div style="font-size:8.5pt; font-weight:700; color:#065f46; text-transform:uppercase; letter-spacing:1px; margin:16px 0 8px;">ℹ️ INFORMATIVOS — Para tener en cuenta</div>

    <div class="pending-item info">
      <span class="pending-icon">✅</span>
      <div class="pending-body">
        <div class="pending-title">SERVICIOS ANDINOS SAC — Primer aviso pendiente de resultado</div>
        <div class="pending-detail">WA enviado ayer (12/03) · Primer contacto · 8 días mora · Sin respuesta aún (normal en esta etapa)</div>
        <div class="pending-actions">
          <span class="btn btn-outline" style="font-size:7.5pt;padding:4px 10px;">📝 Registrar resultado</span>
        </div>
      </div>
      <span class="badge" style="background:#ccfbf1;color:#065f46;white-space:nowrap;">8 días mora</span>
    </div>

  </div>
</div>

<div class="section-header" style="margin-top:30px;">
  <h2><span class="feature-number">5</span>Selección Inteligente de Plantilla por Aging</h2>
  <p>La app sugiere automáticamente la plantilla correcta según los días de mora de cada cliente del lote.</p>
</div>

<div class="aging-row">
  <div class="aging-segment g1">
    <div class="aging-days">0–14 días</div>
    <div class="aging-label">DEUDA RECIENTE</div>
    <span class="aging-template">📋 PRIMER AVISO</span>
  </div>
  <div class="aging-segment g2">
    <div class="aging-days">15–30 días</div>
    <div class="aging-label">SIN RESPUESTA</div>
    <span class="aging-template">⏰ RECORDATORIO</span>
  </div>
  <div class="aging-segment g3">
    <div class="aging-days">31–60 días</div>
    <div class="aging-label">MORA SIGNIFICATIVA</div>
    <span class="aging-template">🔴 AVISO FIRME</span>
  </div>
  <div class="aging-segment g4">
    <div class="aging-days">60+ días</div>
    <div class="aging-label">MORA CRÍTICA</div>
    <span class="aging-template">⚖️ PRE-LEGAL</span>
  </div>
</div>

<div class="callout callout-info">
  <span class="callout-icon">🤖</span>
  <div class="callout-body">
    <strong>No es automático — es asistido</strong>
    El sistema <em>sugiere</em> la plantilla, pero el gestor siempre puede cambiarla antes de enviar. Esto garantiza control humano sobre mensajes críticos (pre-legal, escalation), cumpliendo con las políticas de comunicación comercial.
  </div>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 6</span>
</div>
</div>


<!-- ════════════════════════════════ SECCIÓN 6: ROADMAP ══════════════════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 6 — Roadmap de Implementación</span>
</div>
<div class="content">

<div class="section-header">
  <h2>Roadmap de Implementación</h2>
  <p>Orden de prioridad basado en impacto para el gestor y complejidad técnica.</p>
</div>

<div class="roadmap">

  <div class="roadmap-item">
    <div class="roadmap-tier"><span class="tier-badge tier-1">TIER 1</span></div>
    <div class="roadmap-content">
      <div class="roadmap-title">1️⃣ Resultado Post-Envío en Tab WhatsApp</div>
      <div class="roadmap-desc">Panel de seguimiento que aparece después de cada lote enviado. El gestor registra con un click si el cliente acordó, prometió, no contestó o hay que escalar. Actualiza <code>gestiones.resultado</code> en Supabase en tiempo real.</div>
      <div class="roadmap-pills">
        <span class="pill pill-time">⏱ 1–2 horas</span>
        <span class="pill pill-file">📄 whatsapp.py</span>
        <span class="pill pill-file">📄 db_manager.py</span>
        <span class="pill pill-sql">🗄 gestiones (campo existente)</span>
      </div>
    </div>
  </div>

  <div class="roadmap-item">
    <div class="roadmap-tier"><span class="tier-badge tier-1">TIER 1</span></div>
    <div class="roadmap-content">
      <div class="roadmap-title">2️⃣ Biblioteca de 7 Plantillas WhatsApp</div>
      <div class="roadmap-desc">Selector visual de plantilla antes del envío. Cada plantilla con su propio texto, variables y etiqueta de escenario. Editables desde el Tab Configuración. Guardadas en <code>config.json</code> + Supabase <code>app_config</code>.</div>
      <div class="roadmap-pills">
        <span class="pill pill-time">⏱ 3–4 horas</span>
        <span class="pill pill-file">📄 whatsapp.py</span>
        <span class="pill pill-file">📄 config_tab.py</span>
        <span class="pill pill-file">📄 settings_manager.py</span>
        <span class="pill pill-sql">🗄 app_config (nuevo key)</span>
      </div>
    </div>
  </div>

  <div class="roadmap-item">
    <div class="roadmap-tier"><span class="tier-badge tier-1">TIER 1</span></div>
    <div class="roadmap-content">
      <div class="roadmap-title">3️⃣ Módulo de Acuerdos de Pago con Cuotas</div>
      <div class="roadmap-desc">Nueva sección en el Centro de Gestiones. Formulario para registrar convenios de pago, cálculo automático de cuotas, timeline visual del estado. Genera WA de confirmación automáticamente. Requiere crear 2 nuevas tablas en Supabase.</div>
      <div class="roadmap-pills">
        <span class="pill pill-time">⏱ 4–6 horas</span>
        <span class="pill pill-file">📄 crm_gestiones.py</span>
        <span class="pill pill-file">📄 db_manager.py</span>
        <span class="pill pill-sql">🗄 CREATE TABLE acuerdos_pago</span>
        <span class="pill pill-sql">🗄 CREATE TABLE cuotas_acuerdo</span>
      </div>
    </div>
  </div>

  <div class="roadmap-item">
    <div class="roadmap-tier"><span class="tier-badge tier-1">TIER 1</span></div>
    <div class="roadmap-content">
      <div class="roadmap-title">4️⃣ Bandeja de Pendientes del Día</div>
      <div class="roadmap-desc">Nueva pestaña en el Centro de Gestiones: lista priorizada de acciones diarias generada automáticamente. Detecta: WA sin respuesta +48h, cuotas venciendo hoy/en 3 días, clientes con mora crítica sin contacto. Cada ítem tiene botones de acción directa.</div>
      <div class="roadmap-pills">
        <span class="pill pill-time">⏱ 2–3 horas</span>
        <span class="pill pill-file">📄 crm_gestiones.py</span>
        <span class="pill pill-file">📄 db_manager.py</span>
        <span class="pill pill-sql">🗄 consulta cuotas_acuerdo + gestiones</span>
      </div>
    </div>
  </div>

  <div class="roadmap-item">
    <div class="roadmap-tier"><span class="tier-badge tier-2">TIER 2</span></div>
    <div class="roadmap-content">
      <div class="roadmap-title">5️⃣ Selección Automática de Plantilla por Aging</div>
      <div class="roadmap-desc">Al abrir el tab WhatsApp, la app asigna automáticamente la plantilla sugerida por cliente según sus días de mora. El gestor puede sobreescribir por cliente antes de enviar. Indica visualmente qué segmento tiene cada cliente.</div>
      <div class="roadmap-pills">
        <span class="pill pill-time">⏱ 2 horas</span>
        <span class="pill pill-file">📄 whatsapp.py</span>
      </div>
    </div>
  </div>

  <div class="roadmap-item">
    <div class="roadmap-tier"><span class="tier-badge tier-2">TIER 2</span></div>
    <div class="roadmap-content">
      <div class="roadmap-title">6️⃣ KPIs Expandidos de Efectividad de Cobranza</div>
      <div class="roadmap-desc">Panel de métricas: enviados hoy, con/sin respuesta, acuerdos activos, cuotas venciendo, monto total gestionado vs monto con acuerdo. Dashboard visible en el tab WA y en el Centro de Gestiones.</div>
      <div class="roadmap-pills">
        <span class="pill pill-time">⏱ 2 horas</span>
        <span class="pill pill-file">📄 whatsapp.py</span>
        <span class="pill pill-file">📄 crm_gestiones.py</span>
        <span class="pill pill-file">📄 db_manager.py</span>
      </div>
    </div>
  </div>

  <div class="roadmap-item">
    <div class="roadmap-tier"><span class="tier-badge tier-3">TIER 3</span></div>
    <div class="roadmap-content">
      <div class="roadmap-title">7️⃣ Registro de Pagos en Tiempo Real (sin esperar ERP)</div>
      <div class="roadmap-desc">El gestor puede registrar un pago recibido directamente en la app, sin esperar sincronización del ERP. Actualiza <code>documentos.monto_pendiente</code> y genera WA de agradecimiento automáticamente.</div>
      <div class="roadmap-pills">
        <span class="pill pill-time">⏱ 3–4 horas</span>
        <span class="pill pill-file">📄 crm_gestiones.py</span>
        <span class="pill pill-file">📄 db_manager.py</span>
        <span class="pill pill-sql">🗄 documentos (actualizar monto_pendiente)</span>
      </div>
    </div>
  </div>

  <div class="roadmap-item">
    <div class="roadmap-tier"><span class="tier-badge tier-3">TIER 3</span></div>
    <div class="roadmap-content">
      <div class="roadmap-title">8️⃣ Dashboard de Efectividad de Cobranza</div>
      <div class="roadmap-desc">Reportes analíticos: % WA que resultan en pago (7/15/30 días), ranking de clientes por dificultad de cobranza, saldo total gestionado vs recuperado, evolución mensual, acuerdos cumplidos vs incumplidos.</div>
      <div class="roadmap-pills">
        <span class="pill pill-time">⏱ 5–6 horas</span>
        <span class="pill pill-file">📄 Nuevo tab analytics</span>
        <span class="pill pill-file">📄 db_manager.py</span>
      </div>
    </div>
  </div>

</div>

<h3>Resumen de esfuerzo total</h3>
<table class="data-table">
  <thead>
    <tr><th>Tier</th><th>Features</th><th>Estimado</th><th>Complejidad SQL</th><th>Valor para el gestor</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>TIER 1</strong></td>
      <td>Features 1–4</td>
      <td><strong>~12–15 horas</strong></td>
      <td>2 nuevas tablas + ALTER TABLE</td>
      <td class="impact-high">CRÍTICO — Transforma el flujo de trabajo diario</td>
    </tr>
    <tr>
      <td><strong>TIER 2</strong></td>
      <td>Features 5–6</td>
      <td><strong>~4 horas</strong></td>
      <td>Solo consultas</td>
      <td class="impact-med">ALTO — Automatiza decisiones repetitivas</td>
    </tr>
    <tr>
      <td><strong>TIER 3</strong></td>
      <td>Features 7–8</td>
      <td><strong>~10 horas</strong></td>
      <td>2 nuevas tablas analytics</td>
      <td>MEDIO — Analytics y cierre del ciclo</td>
    </tr>
  </tbody>
</table>

<div class="callout callout-success">
  <span class="callout-icon">🚀</span>
  <div class="callout-body">
    <strong>Punto de partida recomendado</strong>
    Implementar el <strong>Feature 1 (Resultado post-envío)</strong> primero por ser el de menor esfuerzo y mayor impacto inmediato: transforma el tab WhatsApp de "lanzador" a CRM activo con solo las modificaciones en <code>whatsapp.py</code> y <code>db_manager.py</code>, sin cambios en el schema de base de datos.
  </div>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 7</span>
</div>
</div>


<!-- ══════════════════════ SECCIÓN 7: DASHBOARD EFECTIVIDAD (DETALLE) ═════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 7 — Feature 8: Dashboard de Efectividad de Cobranza</span>
</div>
<div class="content">

<div class="section-header">
  <h2><span class="feature-number">8</span>Dashboard de Efectividad de Cobranza — Visión Completa</h2>
  <p>Mide, en tiempo real, si la gestión de cobranza realmente está funcionando. Responde la pregunta que el directorio siempre hace: ¿cuánto recuperamos y en cuánto tiempo?</p>
</div>

<div class="callout callout-info">
  <span class="callout-icon">🎯</span>
  <div class="callout-body">
    <strong>Propósito del dashboard</strong>
    Hoy se sabe cuántos mensajes se enviaron. Este dashboard responde lo que importa: ¿cuántos de esos mensajes resultaron en un pago? ¿Cuánto tiempo tarda un cliente en pagar desde el primer contacto? ¿Qué plantilla convierte más? ¿Qué clientes siempre incumplen?
  </div>
</div>

<!-- BLOQUE 1: FUNNEL -->
<h3>Bloque 1 — Funnel de Cobranza (el flujo completo)</h3>
<p style="font-size:9.5pt;color:#556B82;margin-bottom:12px;">Muestra cuántos clientes pasan de cada etapa a la siguiente. Identifica dónde se "cae" la gestión.</p>

<div class="ui-mockup">
  <div class="ui-mockup-bar">
    <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
    <span class="ui-mockup-title">Dashboard Efectividad → Funnel del Ciclo Actual (CIC-20260313-1020)</span>
  </div>
  <div class="ui-mockup-body">
    <div style="display:flex;gap:0;align-items:stretch;margin:10px 0 20px;">
      <!-- Funnel steps -->
      <div style="flex:1;text-align:center;padding:18px 8px;background:linear-gradient(180deg,#0D3B66,#1a6fa8);color:white;border-radius:8px 0 0 8px;">
        <div style="font-size:22pt;font-weight:800;">48</div>
        <div style="font-size:8pt;opacity:0.85;margin-top:4px;">TOTAL CARTERA<br>CON DEUDA</div>
        <div style="font-size:8pt;background:rgba(255,255,255,0.15);border-radius:4px;padding:2px 6px;margin-top:8px;">100%</div>
      </div>
      <div style="display:flex;align-items:center;color:#ccc;font-size:14pt;padding:0 4px;">▶</div>
      <div style="flex:1;text-align:center;padding:18px 8px;background:linear-gradient(180deg,#0B7285,#1098ad);color:white;">
        <div style="font-size:22pt;font-weight:800;">38</div>
        <div style="font-size:8pt;opacity:0.85;margin-top:4px;">WA ENVIADOS<br>(con teléfono)</div>
        <div style="font-size:8pt;background:rgba(255,255,255,0.15);border-radius:4px;padding:2px 6px;margin-top:8px;">79%</div>
      </div>
      <div style="display:flex;align-items:center;color:#ccc;font-size:14pt;padding:0 4px;">▶</div>
      <div style="flex:1;text-align:center;padding:18px 8px;background:linear-gradient(180deg,#2B8A3E,#43aa5c);color:white;">
        <div style="font-size:22pt;font-weight:800;">22</div>
        <div style="font-size:8pt;opacity:0.85;margin-top:4px;">RESPONDIERON<br>O PROMETIERON</div>
        <div style="font-size:8pt;background:rgba(255,255,255,0.15);border-radius:4px;padding:2px 6px;margin-top:8px;">58%</div>
      </div>
      <div style="display:flex;align-items:center;color:#ccc;font-size:14pt;padding:0 4px;">▶</div>
      <div style="flex:1;text-align:center;padding:18px 8px;background:linear-gradient(180deg,#e67700,#f59f00);color:white;">
        <div style="font-size:22pt;font-weight:800;">11</div>
        <div style="font-size:8pt;opacity:0.85;margin-top:4px;">ACUERDO DE<br>PAGO FIRMADO</div>
        <div style="font-size:8pt;background:rgba(255,255,255,0.15);border-radius:4px;padding:2px 6px;margin-top:8px;">29%</div>
      </div>
      <div style="display:flex;align-items:center;color:#ccc;font-size:14pt;padding:0 4px;">▶</div>
      <div style="flex:1;text-align:center;padding:18px 8px;background:linear-gradient(180deg,#c0392b,#e74c3c);color:white;border-radius:0 8px 8px 0;">
        <div style="font-size:22pt;font-weight:800;">7</div>
        <div style="font-size:8pt;opacity:0.85;margin-top:4px;">PAGO RECIBIDO<br>CONFIRMADO</div>
        <div style="font-size:8pt;background:rgba(255,255,255,0.15);border-radius:4px;padding:2px 6px;margin-top:8px;">18%</div>
      </div>
    </div>
    <div style="font-size:8.5pt;color:#556B82;text-align:center;">
      ⚡ <strong>Tasa de conversión global: 18%</strong> (7 de cada 48 clientes con deuda pagaron en este ciclo)  ·  
      📉 Pérdida principal en etapa <strong>"Respondieron → Acuerdo"</strong>: oportunidad de mejora
    </div>
  </div>
</div>

<!-- BLOQUE 2: KPIs FINANCIEROS -->
<h3>Bloque 2 — KPIs Financieros de Efectividad</h3>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin:12px 0;">
  <!-- DSO -->
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:16px;background:#f7fafd;">
    <div style="font-size:8.5pt;font-weight:700;color:#556B82;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">DSO — Días Promedio de Cobro</div>
    <div style="font-size:28pt;font-weight:800;color:#0D3B66;line-height:1;">34</div>
    <div style="font-size:8pt;color:#556B82;">días desde emisión hasta pago</div>
    <div style="margin-top:10px;padding:6px 10px;background:#fff3cd;border-radius:5px;font-size:8pt;color:#856404;">
      ⚠️ Meta: 25 días · <strong>+9 días sobre meta</strong>
    </div>
    <div style="font-size:8pt;color:#556B82;margin-top:6px;">
      Tendencia: ↗ +3 días vs mes anterior
    </div>
  </div>
  <!-- Tasa recuperación -->
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:16px;background:#f7fafd;">
    <div style="font-size:8.5pt;font-weight:700;color:#556B82;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Tasa de Recuperación Mensual</div>
    <div style="font-size:28pt;font-weight:800;color:#2B8A3E;line-height:1;">62%</div>
    <div style="font-size:8pt;color:#556B82;">de la cartera vencida fue cobrada</div>
    <div style="margin-top:10px;padding:6px 10px;background:#d1fae5;border-radius:5px;font-size:8pt;color:#065f46;">
      ✅ Meta: 55% · <strong>+7% sobre meta</strong>
    </div>
    <div style="font-size:8pt;color:#556B82;margin-top:6px;">
      Tendencia: ↗ +5% vs mes anterior
    </div>
  </div>
  <!-- Efectividad WA -->
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:16px;background:#f7fafd;">
    <div style="font-size:8.5pt;font-weight:700;color:#556B82;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Efectividad Canal WhatsApp</div>
    <div style="font-size:28pt;font-weight:800;color:#0B7285;line-height:1;">58%</div>
    <div style="font-size:8pt;color:#556B82;">de los WA recibieron respuesta</div>
    <div style="margin-top:10px;padding:6px 10px;background:#ccfbf1;border-radius:5px;font-size:8pt;color:#065f46;">
      ✅ Meta: 40% · <strong>+18% sobre meta</strong>
    </div>
    <div style="font-size:8pt;color:#556B82;margin-top:6px;">
      Tendencia: → igual vs mes anterior
    </div>
  </div>
  <!-- Monto recuperado -->
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:16px;background:#f7fafd;">
    <div style="font-size:8.5pt;font-weight:700;color:#556B82;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Monto Recuperado (Mes)</div>
    <div style="font-size:22pt;font-weight:800;color:#0D3B66;line-height:1;">S/ 87,400</div>
    <div style="font-size:8pt;color:#556B82;">sobre cartera vencida de S/ 141,200</div>
    <div style="margin-top:10px;padding:6px 10px;background:#d1fae5;border-radius:5px;font-size:8pt;color:#065f46;">
      ✅ Meta: S/ 70,000 · <strong>+S/ 17,400</strong>
    </div>
    <div style="font-size:8pt;color:#556B82;margin-top:6px;">
      Dólares: $ 12,800 recuperados
    </div>
  </div>
  <!-- Acuerdos -->
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:16px;background:#f7fafd;">
    <div style="font-size:8.5pt;font-weight:700;color:#556B82;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Acuerdos de Pago — Cumplimiento</div>
    <div style="font-size:28pt;font-weight:800;color:#2B8A3E;line-height:1;">73%</div>
    <div style="font-size:8pt;color:#556B82;">de las cuotas pagadas en fecha</div>
    <div style="margin-top:10px;padding:6px 10px;background:#fef3c7;border-radius:5px;font-size:8pt;color:#92400e;">
      ⚠️ Meta: 80% · <strong>-7% bajo meta</strong>
    </div>
    <div style="font-size:8pt;color:#556B82;margin-top:6px;">
      11 acuerdos activos · 3 cuotas vencidas sin pagar
    </div>
  </div>
  <!-- Tiempo respuesta -->
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:16px;background:#f7fafd;">
    <div style="font-size:8.5pt;font-weight:700;color:#556B82;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Tiempo Promedio de Respuesta WA</div>
    <div style="font-size:28pt;font-weight:800;color:#0B7285;line-height:1;">4.2h</div>
    <div style="font-size:8pt;color:#556B82;">desde envío hasta primera respuesta</div>
    <div style="margin-top:10px;padding:6px 10px;background:#d1fae5;border-radius:5px;font-size:8pt;color:#065f46;">
      ✅ Meta: &lt;8 horas · <strong>Óptimo</strong>
    </div>
    <div style="font-size:8pt;color:#556B82;margin-top:6px;">
      Pico de respuesta: 10 AM – 12 PM
    </div>
  </div>
</div>

<!-- BLOQUE 3: PLANTILLA MÁS EFECTIVA + RANKING CLIENTES DIFÍCILES -->
<div style="display:flex;gap:16px;margin-top:6px;">
  <div style="flex:1;">
    <h3>Bloque 3 — Efectividad por Plantilla WA</h3>
    <table class="data-table" style="font-size:8.5pt;">
      <thead><tr><th>Plantilla</th><th>Enviados</th><th>Respuesta</th><th>Acuerdo</th><th>Pago efectivo</th></tr></thead>
      <tbody>
        <tr><td>📋 Primer Aviso</td><td>18</td><td style="color:#2B8A3E;font-weight:700;">72%</td><td>33%</td><td>22%</td></tr>
        <tr><td>⏰ Recordatorio</td><td>12</td><td style="color:#2B8A3E;font-weight:700;">67%</td><td>42%</td><td>33%</td></tr>
        <tr><td>🔴 Aviso Firme</td><td>6</td><td style="color:#e67700;font-weight:700;">50%</td><td>17%</td><td>17%</td></tr>
        <tr><td>⚖️ Pre-Legal</td><td>2</td><td style="color:#c0392b;font-weight:700;">0%</td><td>0%</td><td>0%</td></tr>
      </tbody>
    </table>
    <div style="font-size:8pt;color:#556B82;margin-top:6px;">
      🏆 <strong>RECORDATORIO</strong> tiene la mayor tasa de conversión a pago (33%)
    </div>
  </div>
  <div style="flex:1;">
    <h3>Bloque 4 — Top 5 Clientes Críticos</h3>
    <table class="data-table" style="font-size:8.5pt;">
      <thead><tr><th>Cliente</th><th>Mora</th><th>Saldo</th><th>Gestiones</th><th>Estado</th></tr></thead>
      <tbody>
        <tr><td>DISTRIBUIDORA SUR</td><td style="color:#c0392b;font-weight:700;">68d</td><td>$3,200</td><td>3 WA</td><td><span class="badge badge-tolegal" style="font-size:7pt;">Pre-Legal</span></td></tr>
        <tr><td>GRUPO NORTE SAC</td><td style="color:#c0392b;font-weight:700;">55d</td><td>S/21,400</td><td>2 WA</td><td><span class="badge badge-nocontact" style="font-size:7pt;">Sin contacto</span></td></tr>
        <tr><td>COMERCIAL LIMA</td><td style="color:#e67700;font-weight:700;">47d</td><td>S/12,400</td><td>2 WA, 1 llamada</td><td><span class="badge badge-agreed" style="font-size:7pt;">Acuerdo activo</span></td></tr>
        <tr><td>IMP. ANDINA</td><td style="color:#e67700;font-weight:700;">38d</td><td>S/9,800</td><td>1 WA</td><td><span class="badge badge-promised" style="font-size:7pt;">Prometió pagar</span></td></tr>
        <tr><td>TRÁFICO LISTO</td><td style="color:#e67700;font-weight:700;">31d</td><td>$1,900</td><td>1 WA</td><td><span class="badge badge-pending" style="font-size:7pt;">Sin respuesta</span></td></tr>
      </tbody>
    </table>
  </div>
</div>

<!-- BLOQUE 5: QUÉ ALIMENTA EL DASHBOARD -->
<h3 style="margin-top:20px;">Bloque 5 — ¿Qué datos alimentan el dashboard?</h3>
<table class="data-table" style="font-size:9pt;">
  <thead><tr><th>Métrica</th><th>Fuente de datos en Supabase</th><th>Se actualiza cuando...</th></tr></thead>
  <tbody>
    <tr><td>Funnel (enviados/respuesta/acuerdo/pago)</td><td>gestiones + acuerdos_pago + cuotas_acuerdo</td><td>El gestor registra resultado post-envío o marca pago</td></tr>
    <tr><td>DSO (días promedio de cobro)</td><td>documentos.fecha_vencimiento + cuotas_acuerdo.fecha_pago</td><td>Al marcar cuota pagada o registrar pago directo</td></tr>
    <tr><td>Tasa de recuperación</td><td>documentos.monto_pendiente vs monto_total</td><td>Al registrar pagos recibidos (Feature 7)</td></tr>
    <tr><td>Efectividad por plantilla</td><td>gestiones.metadata.template + gestiones.resultado</td><td>Al registrar resultado del WA enviado</td></tr>
    <tr><td>Cumplimiento de acuerdos</td><td>cuotas_acuerdo.estado (PAGADA/VENCIDA)</td><td>Diariamente por job automático o flag manual</td></tr>
    <tr><td>Tiempo de respuesta WA</td><td>gestiones.fecha (envío) + gestiones.updated_at (resultado registrado)</td><td>Al guardar resultado post-envío</td></tr>
  </tbody>
</table>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 8</span>
</div>
</div>


<!-- ══════════════════════════════ SECCIÓN 8: INFORME GERENCIAL ═══════════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 8 — Informe Gerencial para Comités de Directorio</span>
</div>
<div class="content">

<div class="section-header">
  <h2>Informe Gerencial de Cobranza — Diseño para Comités</h2>
  <p>Reporte mensual ejecutivo, generado automáticamente desde la app, listo para presentar al directorio.</p>
</div>

<div class="callout callout-warn">
  <span class="callout-icon">🏛️</span>
  <div class="callout-body">
    <strong>Propósito del informe gerencial</strong>
    El directorio necesita 3 respuestas en 30 segundos: ¿cuánto se debe cobrar?, ¿cuánto se recuperó?, ¿qué riesgo hay. Este informe les responde todo con semáforos, montos claros y recomendaciones accionables — sin tecnicismos, sin tablas imposibles de leer.
  </div>
</div>

<!-- ════ MOCKUP DEL INFORME ════ -->
<div class="ui-mockup">
  <div class="ui-mockup-bar">
    <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
    <span class="ui-mockup-title">Informe Gerencial de Cobranza → Botón "Generar Informe PDF" en el Dashboard</span>
  </div>
  <div class="ui-mockup-body" style="padding:0;background:#f4f6f9;">

    <!-- HEADER DEL INFORME -->
    <div style="background:linear-gradient(135deg,#0D3B66,#1a6fa8);color:white;padding:24px 30px;display:flex;justify-content:space-between;align-items:flex-start;">
      <div>
        <div style="font-size:8pt;opacity:0.7;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px;">Informe Ejecutivo de Gestión de Cobranza</div>
        <div style="font-size:18pt;font-weight:800;line-height:1.2;">DACTA S.A.C.</div>
        <div style="font-size:10pt;opacity:0.85;margin-top:4px;">Cartera Cuentas por Cobrar · Período: Febrero 2026</div>
      </div>
      <div style="text-align:right;font-size:8.5pt;opacity:0.8;">
        <div>Generado: 13/03/2026</div>
        <div>Elaborado por: Área de Cobranzas</div>
        <div style="margin-top:8px;background:rgba(255,255,255,0.15);border-radius:5px;padding:4px 12px;">
          📄 Versión para Comité de Directorio
        </div>
      </div>
    </div>

    <div style="padding:20px 24px;">

    <!-- SEMÁFORO EJECUTIVO -->
    <div style="font-weight:700;font-size:9pt;color:#0D3B66;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
      🚦 RESUMEN EJECUTIVO — Estado de la Cartera
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-bottom:20px;">
      <!-- Cartera total -->
      <div style="background:white;border-radius:8px;padding:14px;border-top:4px solid #e67700;box-shadow:0 1px 6px rgba(0,0,0,0.07);">
        <div style="font-size:7.5pt;color:#556B82;font-weight:700;text-transform:uppercase;margin-bottom:6px;">CARTERA VENCIDA TOTAL</div>
        <div style="font-size:18pt;font-weight:800;color:#0D3B66;line-height:1;">S/ 141,200</div>
        <div style="font-size:8pt;color:#556B82;margin-top:2px;">+ $ 24,800 en dólares</div>
        <div style="margin-top:8px;font-size:8pt;color:#e67700;font-weight:600;">↗ +8% vs enero</div>
      </div>
      <!-- Recuperado -->
      <div style="background:white;border-radius:8px;padding:14px;border-top:4px solid #2B8A3E;box-shadow:0 1px 6px rgba(0,0,0,0.07);">
        <div style="font-size:7.5pt;color:#556B82;font-weight:700;text-transform:uppercase;margin-bottom:6px;">RECUPERADO EN FEBRERO</div>
        <div style="font-size:18pt;font-weight:800;color:#2B8A3E;line-height:1;">S/ 87,400</div>
        <div style="font-size:8pt;color:#556B82;margin-top:2px;">Tasa de recuperación: <strong>62%</strong></div>
        <div style="margin-top:8px;font-size:8pt;color:#2B8A3E;font-weight:600;">✅ Meta cumplida (55%)</div>
      </div>
      <!-- Pendiente -->
      <div style="background:white;border-radius:8px;padding:14px;border-top:4px solid #c0392b;box-shadow:0 1px 6px rgba(0,0,0,0.07);">
        <div style="font-size:7.5pt;color:#556B82;font-weight:700;text-transform:uppercase;margin-bottom:6px;">SALDO AÚN PENDIENTE</div>
        <div style="font-size:18pt;font-weight:800;color:#c0392b;line-height:1;">S/ 53,800</div>
        <div style="font-size:8pt;color:#556B82;margin-top:2px;">28 clientes activos en gestión</div>
        <div style="margin-top:8px;font-size:8pt;color:#c0392b;font-weight:600;">⚠️ 3 clientes en riesgo legal</div>
      </div>
      <!-- En acuerdos -->
      <div style="background:white;border-radius:8px;padding:14px;border-top:4px solid #0B7285;box-shadow:0 1px 6px rgba(0,0,0,0.07);">
        <div style="font-size:7.5pt;color:#556B82;font-weight:700;text-transform:uppercase;margin-bottom:6px;">EN ACUERDOS DE PAGO</div>
        <div style="font-size:18pt;font-weight:800;color:#0B7285;line-height:1;">S/ 31,200</div>
        <div style="font-size:8pt;color:#556B82;margin-top:2px;">11 acuerdos activos vigentes</div>
        <div style="margin-top:8px;font-size:8pt;color:#0B7285;font-weight:600;">73% de cuotas al día</div>
      </div>
    </div>

    <!-- TABLA DISTRIBUCIÓN POR AGING -->
    <div style="font-weight:700;font-size:9pt;color:#0D3B66;text-transform:uppercase;letter-spacing:1px;margin:16px 0 10px;">
      📊 DISTRIBUCIÓN DE CARTERA POR ANTIGÜEDAD DE DEUDA
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:8.5pt;">
      <thead>
        <tr style="background:#0D3B66;color:white;">
          <th style="padding:8px 12px;text-align:left;">Segmento</th>
          <th style="padding:8px 12px;text-align:right;">Clientes</th>
          <th style="padding:8px 12px;text-align:right;">Saldo Soles</th>
          <th style="padding:8px 12px;text-align:right;">% Cartera</th>
          <th style="padding:8px 12px;text-align:center;">Riesgo</th>
          <th style="padding:8px 12px;text-align:left;">Acción recomendada</th>
        </tr>
      </thead>
      <tbody>
        <tr style="background:#f0fdf4;">
          <td style="padding:8px 12px;font-weight:600;">🟢 0 – 14 días (Corriente)</td>
          <td style="padding:8px 12px;text-align:right;">12</td>
          <td style="padding:8px 12px;text-align:right;font-weight:700;">S/ 28,400</td>
          <td style="padding:8px 12px;text-align:right;">20%</td>
          <td style="padding:8px 12px;text-align:center;"><span style="background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:4px;font-size:7.5pt;font-weight:700;">BAJO</span></td>
          <td style="padding:8px 12px;font-size:8pt;">Primer aviso WA preventivo</td>
        </tr>
        <tr>
          <td style="padding:8px 12px;font-weight:600;">🟡 15 – 30 días</td>
          <td style="padding:8px 12px;text-align:right;">16</td>
          <td style="padding:8px 12px;text-align:right;font-weight:700;">S/ 51,200</td>
          <td style="padding:8px 12px;text-align:right;">36%</td>
          <td style="padding:8px 12px;text-align:center;"><span style="background:#fef9c3;color:#854d0e;padding:2px 8px;border-radius:4px;font-size:7.5pt;font-weight:700;">MEDIO</span></td>
          <td style="padding:8px 12px;font-size:8pt;">Recordatorio + llamada si no responde</td>
        </tr>
        <tr style="background:#fffbeb;">
          <td style="padding:8px 12px;font-weight:600;">🟠 31 – 60 días</td>
          <td style="padding:8px 12px;text-align:right;">9</td>
          <td style="padding:8px 12px;text-align:right;font-weight:700;">S/ 41,800</td>
          <td style="padding:8px 12px;text-align:right;">30%</td>
          <td style="padding:8px 12px;text-align:center;"><span style="background:#ffedd5;color:#9a3412;padding:2px 8px;border-radius:4px;font-size:7.5pt;font-weight:700;">ALTO</span></td>
          <td style="padding:8px 12px;font-size:8pt;">Aviso firme + oferta de acuerdo</td>
        </tr>
        <tr style="background:#fef2f2;">
          <td style="padding:8px 12px;font-weight:600;">🔴 Más de 60 días</td>
          <td style="padding:8px 12px;text-align:right;">5</td>
          <td style="padding:8px 12px;text-align:right;font-weight:700;color:#c0392b;">S/ 19,800</td>
          <td style="padding:8px 12px;text-align:right;color:#c0392b;">14%</td>
          <td style="padding:8px 12px;text-align:center;"><span style="background:#fee2e2;color:#991b1b;padding:2px 8px;border-radius:4px;font-size:7.5pt;font-weight:700;">CRÍTICO</span></td>
          <td style="padding:8px 12px;font-size:8pt;color:#991b1b;font-weight:600;">Derivar a Legal inmediatamente</td>
        </tr>
      </tbody>
    </table>

    <!-- TOP 5 CLIENTES CRÍTICOS -->
    <div style="font-weight:700;font-size:9pt;color:#0D3B66;text-transform:uppercase;letter-spacing:1px;margin:16px 0 10px;">
      🚨 CLIENTES CRÍTICOS — REQUIEREN ATENCIÓN DEL DIRECTORIO
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:8.5pt;">
      <thead>
        <tr style="background:#c0392b;color:white;">
          <th style="padding:7px 10px;text-align:left;">Cliente</th>
          <th style="padding:7px 10px;text-align:right;">Días Mora</th>
          <th style="padding:7px 10px;text-align:right;">Saldo Total</th>
          <th style="padding:7px 10px;text-align:center;">Gestiones</th>
          <th style="padding:7px 10px;text-align:center;">Estado actual</th>
          <th style="padding:7px 10px;text-align:left;">Recomendación</th>
        </tr>
      </thead>
      <tbody>
        <tr style="background:#fef2f2;">
          <td style="padding:7px 10px;font-weight:700;">DISTRIBUIDORA SUR E.I.R.L.</td>
          <td style="padding:7px 10px;text-align:right;color:#c0392b;font-weight:800;">68 días</td>
          <td style="padding:7px 10px;text-align:right;font-weight:700;">$ 3,200</td>
          <td style="padding:7px 10px;text-align:center;">3 WA enviados</td>
          <td style="padding:7px 10px;text-align:center;"><span style="background:#fee2e2;color:#991b1b;padding:2px 8px;border-radius:4px;font-size:7.5pt;font-weight:700;">SIN RESPUESTA</span></td>
          <td style="padding:7px 10px;font-size:8pt;color:#991b1b;font-weight:600;">Carta notarial + derivar a legal</td>
        </tr>
        <tr>
          <td style="padding:7px 10px;font-weight:700;">GRUPO NORTE S.A.C.</td>
          <td style="padding:7px 10px;text-align:right;color:#c0392b;font-weight:800;">55 días</td>
          <td style="padding:7px 10px;text-align:right;font-weight:700;">S/ 21,400</td>
          <td style="padding:7px 10px;text-align:center;">2 WA enviados</td>
          <td style="padding:7px 10px;text-align:center;"><span style="background:#fee2e2;color:#991b1b;padding:2px 8px;border-radius:4px;font-size:7.5pt;font-weight:700;">SIN CONTACTO</span></td>
          <td style="padding:7px 10px;font-size:8pt;color:#991b1b;font-weight:600;">Visita presencial urgente</td>
        </tr>
        <tr style="background:#fef2f2;">
          <td style="padding:7px 10px;font-weight:700;">COMERCIAL LIMA S.A.C.</td>
          <td style="padding:7px 10px;text-align:right;color:#e67700;font-weight:800;">47 días</td>
          <td style="padding:7px 10px;text-align:right;font-weight:700;">S/ 12,400</td>
          <td style="padding:7px 10px;text-align:center;">2 WA + acuerdo</td>
          <td style="padding:7px 10px;text-align:center;"><span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:4px;font-size:7.5pt;font-weight:700;">ACUERDO ACTIVO</span></td>
          <td style="padding:7px 10px;font-size:8pt;color:#1e40af;">Monitorear primera cuota (14/03)</td>
        </tr>
      </tbody>
    </table>

    <!-- GESTIONES REALIZADAS -->
    <div style="display:flex;gap:14px;margin-top:16px;">
      <div style="flex:1;background:white;border-radius:8px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="font-weight:700;font-size:9pt;color:#0D3B66;margin-bottom:10px;">📲 GESTIONES REALIZADAS EN FEBRERO</div>
        <div style="display:flex;flex-direction:column;gap:6px;font-size:8.5pt;">
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;">
            <span>WhatsApp enviados</span><strong>38</strong>
          </div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;">
            <span>Emails enviados</span><strong>42</strong>
          </div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;">
            <span>Llamadas registradas</span><strong>8</strong>
          </div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;">
            <span>Acuerdos firmados</span><strong style="color:#2B8A3E;">11</strong>
          </div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;">
            <span>Clientes derivados a Legal</span><strong style="color:#c0392b;">2</strong>
          </div>
        </div>
      </div>
      <div style="flex:1;background:white;border-radius:8px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="font-weight:700;font-size:9pt;color:#0D3B66;margin-bottom:10px;">📈 COMPARATIVO VS MES ANTERIOR</div>
        <div style="display:flex;flex-direction:column;gap:6px;font-size:8.5pt;">
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;">
            <span>Recuperación (S/)</span>
            <strong style="color:#2B8A3E;">↗ +S/ 11,200</strong>
          </div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;">
            <span>Tasa de recuperación</span>
            <strong style="color:#2B8A3E;">↗ +5% (57%→62%)</strong>
          </div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;">
            <span>DSO (días promedio)</span>
            <strong style="color:#c0392b;">↗ +3 días (31→34)</strong>
          </div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f4f8;">
            <span>Efectividad WA</span>
            <strong style="color:#2B8A3E;">→ igual (58%)</strong>
          </div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;">
            <span>Acuerdos activos</span>
            <strong style="color:#2B8A3E;">↗ +4 acuerdos</strong>
          </div>
        </div>
      </div>
    </div>

    <!-- RECOMENDACIONES -->
    <div style="font-weight:700;font-size:9pt;color:#0D3B66;text-transform:uppercase;letter-spacing:1px;margin:16px 0 10px;">
      💡 RECOMENDACIONES PARA EL DIRECTORIO
    </div>
    <div style="display:flex;flex-direction:column;gap:8px;">
      <div style="display:flex;gap:10px;padding:10px 14px;background:#fef2f2;border-left:4px solid #c0392b;border-radius:0 6px 6px 0;font-size:8.5pt;">
        <span style="font-size:14pt;flex-shrink:0;">🚨</span>
        <div><strong style="color:#991b1b;">Acción inmediata:</strong> Autorizar inicio de proceso legal para DISTRIBUIDORA SUR E.I.R.L. ($ 3,200 · 68 días). Ya se han enviado 3 comunicaciones sin respuesta.</div>
      </div>
      <div style="display:flex;gap:10px;padding:10px 14px;background:#fffbeb;border-left:4px solid #e67700;border-radius:0 6px 6px 0;font-size:8.5pt;">
        <span style="font-size:14pt;flex-shrink:0;">⚠️</span>
        <div><strong style="color:#b45309;">Atención prioritaria:</strong> GRUPO NORTE S.A.C. (S/ 21,400 · 55 días) no ha respondido ningún canal. Se recomienda visita presencial del jefe de ventas esta semana.</div>
      </div>
      <div style="display:flex;gap:10px;padding:10px 14px;background:#eff6ff;border-left:4px solid #3b82f6;border-radius:0 6px 6px 0;font-size:8.5pt;">
        <span style="font-size:14pt;flex-shrink:0;">📊</span>
        <div><strong style="color:#1e40af;">Oportunidad de mejora:</strong> El DSO subió 3 días vs. enero. Implementar la biblioteca de plantillas WA (Feature 2) y el seguimiento automático de cuotas (Feature 3) proyecta reducirlo en 5–8 días en 60 días.</div>
      </div>
      <div style="display:flex;gap:10px;padding:10px 14px;background:#f0fdf4;border-left:4px solid #22c55e;border-radius:0 6px 6px 0;font-size:8.5pt;">
        <span style="font-size:14pt;flex-shrink:0;">✅</span>
        <div><strong style="color:#15803d;">Logro destacado:</strong> La tasa de recuperación de 62% superó la meta de 55%. El canal WhatsApp tuvo 58% de tasa de respuesta, muy por encima del benchmark de email (28%).</div>
      </div>
    </div>

    <!-- FIRMA -->
    <div style="margin-top:20px;padding-top:14px;border-top:2px solid #e2e8f0;display:flex;justify-content:space-between;font-size:8pt;color:#9ca3af;">
      <div>
        <strong style="color:#4a5568;">Área de Cobranzas — DACTA S.A.C.</strong><br>
        Generado automáticamente desde ReporteCobranzas · v2.0<br>
        Datos al: 13/03/2026 10:18 AM
      </div>
      <div style="text-align:right;">
        <strong style="color:#4a5568;">Próximo comité:</strong> 28/03/2026<br>
        Este documento es confidencial.<br>
        Solo para uso interno del Directorio.
      </div>
    </div>

    </div>
  </div>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 9</span>
</div>
</div>


<!-- ══════════════════════════════ SECCIÓN 9: IMPLEMENTACIÓN INFORME ══════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 9 — Cómo se genera el Informe Gerencial</span>
</div>
<div class="content">

<div class="section-header">
  <h2>Cómo se integra el Informe Gerencial en la app</h2>
  <p>Un solo botón genera el PDF listo para imprimir o compartir con el directorio.</p>
</div>

<h3>Flujo de generación (diseño de ventana)</h3>

<div class="ui-mockup">
  <div class="ui-mockup-bar">
    <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
    <span class="ui-mockup-title">Dashboard Efectividad → Panel de Informes Gerenciales</span>
  </div>
  <div class="ui-mockup-body">
    <div style="display:flex;gap:16px;margin-bottom:16px;">
      <div style="flex:2;background:#f7fafd;border:1px solid #d1dce8;border-radius:8px;padding:16px;">
        <div style="font-weight:700;font-size:10pt;color:#0D3B66;margin-bottom:12px;">📄 Generar Informe para Comité</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
          <div>
            <div style="font-size:8pt;font-weight:600;color:#4a5568;margin-bottom:4px;">PERÍODO</div>
            <div style="border:1px solid #cbd5e0;border-radius:5px;padding:7px 10px;font-size:9pt;background:white;">Febrero 2026</div>
          </div>
          <div>
            <div style="font-size:8pt;font-weight:600;color:#4a5568;margin-bottom:4px;">TIPO DE INFORME</div>
            <div style="border:1px solid #cbd5e0;border-radius:5px;padding:7px 10px;font-size:9pt;background:white;">Mensual — Comité de Directorio</div>
          </div>
          <div>
            <div style="font-size:8pt;font-weight:600;color:#4a5568;margin-bottom:4px;">INCLUIR SECCIÓN</div>
            <div style="font-size:8.5pt;color:#374151;line-height:2;">
              ☑ Resumen ejecutivo y semáforos<br>
              ☑ Distribución por antigüedad (aging)<br>
              ☑ Top clientes críticos<br>
              ☑ Gestiones del período<br>
              ☑ Comparativo vs. mes anterior<br>
              ☑ Recomendaciones automáticas<br>
              ☐ Detalle de acuerdos de pago
            </div>
          </div>
          <div>
            <div style="font-size:8pt;font-weight:600;color:#4a5568;margin-bottom:4px;">DESTINATARIO</div>
            <div style="border:1px solid #cbd5e0;border-radius:5px;padding:7px 10px;font-size:9pt;background:white;">Comité de Directorio</div>
            <div style="font-size:8pt;font-weight:600;color:#4a5568;margin:8px 0 4px;">ELABORADO POR</div>
            <div style="border:1px solid #cbd5e0;border-radius:5px;padding:7px 10px;font-size:9pt;background:white;">Jefa de Cobranzas · DACTA</div>
          </div>
        </div>
        <div style="display:flex;gap:10px;">
          <span class="btn btn-primary">📥 Generar PDF Gerencial</span>
          <span class="btn btn-green">📧 Enviar por Email al Directorio</span>
          <span class="btn btn-outline">👁️ Vista previa</span>
        </div>
      </div>
      <div style="flex:1;background:#f7fafd;border:1px solid #d1dce8;border-radius:8px;padding:16px;">
        <div style="font-weight:700;font-size:10pt;color:#0D3B66;margin-bottom:10px;">📋 Informes anteriores</div>
        <div style="font-size:8.5pt;color:#4a5568;">
          <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #e2e8f0;">
            <span>Enero 2026</span>
            <span class="btn btn-outline" style="font-size:7pt;padding:3px 8px;">📥 Ver</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #e2e8f0;">
            <span>Diciembre 2025</span>
            <span class="btn btn-outline" style="font-size:7pt;padding:3px 8px;">📥 Ver</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #e2e8f0;">
            <span>Noviembre 2025</span>
            <span class="btn btn-outline" style="font-size:7pt;padding:3px 8px;">📥 Ver</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:7px 0;">
            <span>Octubre 2025</span>
            <span class="btn btn-outline" style="font-size:7pt;padding:3px 8px;">📥 Ver</span>
          </div>
        </div>
        <div style="margin-top:12px;font-size:8pt;color:#556B82;font-style:italic;">
          Los informes históricos se almacenan en Supabase Storage y están disponibles en cualquier momento.
        </div>
      </div>
    </div>
  </div>
</div>

<h3>Indicadores clave que el directorio puede cuestionar — y cómo los respondemos</h3>

<table class="data-table">
  <thead>
    <tr>
      <th>Pregunta del directorio</th>
      <th>KPI que responde</th>
      <th>Ubicación en el informe</th>
      <th>Fuente de datos</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><em>"¿Cuánto se debe cobrar en total?"</em></td>
      <td>Cartera vencida total (S/ + $)</td>
      <td>Bloque semáforo, celda 1</td>
      <td>documentos_ciclo.saldo_real</td>
    </tr>
    <tr>
      <td><em>"¿Cuánto recuperamos este mes?"</em></td>
      <td>Monto recuperado + tasa de recuperación %</td>
      <td>Bloque semáforo, celda 2</td>
      <td>cuotas_acuerdo.monto_pagado + pagos directos</td>
    </tr>
    <tr>
      <td><em>"¿Qué riesgo de incobrabilidad hay?"</em></td>
      <td>Tabla aging: % cartera en +60 días</td>
      <td>Distribución por antigüedad</td>
      <td>documentos_ciclo.dias_mora</td>
    </tr>
    <tr>
      <td><em>"¿Qué clientes son los más problemáticos?"</em></td>
      <td>Top clientes críticos con historial</td>
      <td>Tabla clientes críticos</td>
      <td>gestiones + acuerdos_pago + documentos_ciclo</td>
    </tr>
    <tr>
      <td><em>"¿Estamos mejorando o empeorando?"</em></td>
      <td>Comparativo mensual con flechas</td>
      <td>Comparativo vs. mes anterior</td>
      <td>ciclos_procesamiento históricos</td>
    </tr>
    <tr>
      <td><em>"¿Qué tan efectiva es nuestra gestión?"</em></td>
      <td>Tasa de respuesta WA + funnel conversión</td>
      <td>Dashboard efectividad</td>
      <td>gestiones.resultado</td>
    </tr>
    <tr>
      <td><em>"¿Cuánto tiempo tardamos en cobrar?"</em></td>
      <td>DSO — Days Sales Outstanding</td>
      <td>KPIs financieros (dashboard)</td>
      <td>fecha_vencimiento vs. fecha_pago</td>
    </tr>
    <tr>
      <td><em>"¿Los acuerdos se están cumpliendo?"</em></td>
      <td>% cuotas pagadas en fecha</td>
      <td>Bloque semáforo, celda 4</td>
      <td>cuotas_acuerdo.estado</td>
    </tr>
    <tr>
      <td><em>"¿Qué acciones se tomaron este mes?"</em></td>
      <td>Gestiones realizadas por tipo</td>
      <td>Panel gestiones del período</td>
      <td>gestiones (agrupado por tipo_gestion)</td>
    </tr>
    <tr>
      <td><em>"¿Cuál es el plan para lo que queda?"</em></td>
      <td>Recomendaciones automáticas priorizadas</td>
      <td>Bloque recomendaciones</td>
      <td>Reglas de negocio sobre aging + resultados</td>
    </tr>
  </tbody>
</table>

<div class="callout callout-success">
  <span class="callout-icon">🏆</span>
  <div class="callout-body">
    <strong>El informe se genera en 1 click — sin trabajo manual del gestor</strong>
    Todos los datos provienen de lo que el gestor ya registró durante su trabajo diario (resultados post-envío, acuerdos, pagos). No hay que "preparar" el informe: la app lo ensambla automáticamente con los datos reales del período seleccionado, listo para imprimir o enviar por email al directorio.
  </div>
</div>

<h3>Archivos a crear/modificar para este feature</h3>
<div class="roadmap-pills">
  <span class="pill pill-file">📄 utils/ui/tabs/crm_gestiones.py (nueva sección "Informes")</span>
  <span class="pill pill-file">📄 utils/db_manager.py (queries de agregación por período)</span>
  <span class="pill pill-file">📄 utils/report_generator.py (nuevo — genera el HTML del informe)</span>
  <span class="pill pill-sql">🗄 Supabase Storage: bucket "informes_gerenciales"</span>
  <span class="pill pill-time">⏱ Estimado: 5–6 horas</span>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Páginas 8–10</span>
</div>
</div>


<!-- ═══════════════════ FEATURE 9: TRAZABILIDAD COMPLETA ════════════════════ -->
<div class="page">
<div class="page-header">
  <span class="page-header-logo">DACTA · CRM WhatsApp</span>
  <span class="page-header-section">Sección 10 — Feature 9: Trazabilidad Completa por Documento, Cliente y Ciclo</span>
</div>
<div class="content">

<div class="section-header">
  <h2><span class="feature-number">9</span>Trazabilidad Completa — La Base de Todo lo Demás</h2>
  <p>Sin este feature, los dashboards muestran números calculados en memoria. Con él, cada cifra tiene respaldo en Supabase: quién pagó, cuándo, cómo y a través de qué banco — extraído directamente del ERP Integrens.</p>
</div>

<div class="callout callout-warn">
  <span class="callout-icon">🔍</span>
  <div class="callout-body">
    <strong>El problema que resuelve</strong>
    Hoy el Excel de cobranza de Integrens ya trae fecha exacta de pago, forma de pago (efectivo, depósito, transferencia) y banco. El sistema lo guarda en la tabla <code>cobranzas</code>. Pero <strong>nunca cruza esa información con los documentos</strong> para decir explícitamente "esta factura fue cobrada". Los datos están — solo falta conectarlos.
  </div>
</div>

<!-- LOS 3 NIVELES -->
<h3>Los 3 niveles de trazabilidad que necesita un gestor de cobranza</h3>

<div style="display:flex;flex-direction:column;gap:0;">

  <!-- Nivel 1 -->
  <div style="display:flex;gap:0;margin-bottom:2px;">
    <div style="width:32px;background:#0D3B66;color:white;display:flex;align-items:center;justify-content:center;font-size:14pt;font-weight:800;border-radius:8px 0 0 0;flex-shrink:0;">1</div>
    <div style="flex:1;border:2px solid #0D3B66;border-left:none;padding:14px 18px;border-radius:0 8px 0 0;background:#f7fafd;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <span style="font-weight:700;font-size:10pt;color:#0D3B66;">Por Documento — "¿Qué factura específica está pendiente?"</span>
          <div style="font-size:8.5pt;color:#4a5568;margin-top:4px;">
            Tabla: <code>documentos_ciclo</code> — <strong>Ya existe ✅</strong><br>
            Cada factura, con su saldo real, días de mora y estado — guardada por ciclo.
          </div>
        </div>
        <span style="background:#d1fae5;color:#065f46;padding:4px 12px;border-radius:5px;font-size:8pt;font-weight:700;white-space:nowrap;flex-shrink:0;margin-left:10px;">EXISTE HOY</span>
      </div>
      <div style="margin-top:10px;font-size:8pt;background:white;border:1px solid #d1dce8;border-radius:5px;padding:8px 12px;font-family:monospace;color:#374151;">
        cycle_id: CIC-20260201  |  cod_cliente: CLI-001  |  comprobante: FAC-001234<br>
        empresa: GRUPO NORTE SAC  |  saldo_real: 21,400  |  dias_mora: 55  |  estado: 🔴 Pre-Legal
      </div>
      <div style="margin-top:6px;font-size:8pt;color:#556B82;">
        ✅ Sirve para: tabla detallada de cartera, consulta de disputas, proceso legal, auditoría
      </div>
    </div>
  </div>

  <!-- Nivel 2 -->
  <div style="display:flex;gap:0;margin-bottom:2px;">
    <div style="width:32px;background:#e67700;color:white;display:flex;align-items:center;justify-content:center;font-size:14pt;font-weight:800;flex-shrink:0;">2</div>
    <div style="flex:1;border:2px solid #e67700;border-left:none;padding:14px 18px;background:#fffbeb;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <span style="font-weight:700;font-size:10pt;color:#9a3412;">Por Cliente + Ciclo — "¿Este cliente está mejorando o empeorando?"</span>
          <div style="font-size:8.5pt;color:#4a5568;margin-top:4px;">
            Tabla: <code>resumen_cliente_ciclo</code> — <strong>Falta crear ❌</strong><br>
            Un solo número por empresa en cada ciclo: total deuda, documentos vencidos, días mora promedio.
          </div>
        </div>
        <span style="background:#ffedd5;color:#9a3412;padding:4px 12px;border-radius:5px;font-size:8pt;font-weight:700;white-space:nowrap;flex-shrink:0;margin-left:10px;">FALTA CREAR</span>
      </div>
      <div style="margin-top:10px;font-size:8pt;background:white;border:1px solid #fed7aa;border-radius:5px;padding:8px 12px;font-family:monospace;color:#374151;">
        cycle_id: CIC-20260201  |  cod_cliente: CLI-001  |  empresa: GRUPO NORTE SAC<br>
        total_deuda: 29,600  |  docs_vencidos: 2  |  dias_mora_max: 55  |  tendencia: ↗ EMPEORA
      </div>
      <div style="margin-top:6px;font-size:8pt;color:#556B82;">
        ✅ Sirve para: negociación inteligente, Top 5 clientes críticos, detección de patrones de comportamiento, recomendación de límite de crédito al área comercial
      </div>
    </div>
  </div>

  <!-- Nivel 3 -->
  <div style="display:flex;gap:0;">
    <div style="width:32px;background:#2B8A3E;color:white;display:flex;align-items:center;justify-content:center;font-size:14pt;font-weight:800;border-radius:0 0 0 8px;flex-shrink:0;">3</div>
    <div style="flex:1;border:2px solid #2B8A3E;border-left:none;padding:14px 18px;border-radius:0 0 8px 0;background:#f0fdf4;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <span style="font-weight:700;font-size:10pt;color:#15803d;">Por Ciclo Total — "¿Cómo evolucionó toda la cartera este año?"</span>
          <div style="font-size:8.5pt;color:#4a5568;margin-top:4px;">
            Tabla: <code>resumen_ciclo</code> — <strong>Falta crear ❌</strong><br>
            Una fila por mes: totales de cartera, vencida, pre-legal, recuperado y tasa de recuperación.
          </div>
        </div>
        <span style="background:#bbf7d0;color:#15803d;padding:4px 12px;border-radius:5px;font-size:8pt;font-weight:700;white-space:nowrap;flex-shrink:0;margin-left:10px;">FALTA CREAR</span>
      </div>
      <div style="margin-top:10px;font-size:8pt;background:white;border:1px solid #bbf7d0;border-radius:5px;padding:8px 12px;font-family:monospace;color:#374151;">
        cycle_id: CIC-20260301  |  fecha: 2026-03-01  |  cartera_total: 141,200<br>
        cartera_vencida: 72,800  |  prelegal: 53,800  |  recuperado_vs_ant: 21,600  |  tasa: 24.3%
      </div>
      <div style="margin-top:6px;font-size:8pt;color:#556B82;">
        ✅ Sirve para: informe gerencial, gráficas de tendencia 12 meses, presentaciones al directorio, metas anuales
      </div>
    </div>
  </div>

</div>

<!-- INTEGRACIÓN CON INTEGRENS -->
<h3 style="margin-top:20px;">La clave: el ERP Integrens ya tiene los datos — solo falta el cruce</h3>

<div class="callout callout-success" style="margin-bottom:14px;">
  <span class="callout-icon">💡</span>
  <div class="callout-body">
    <strong>Confirmado en revisión del código:</strong> el Excel de "Detalle Cobranza" de Integrens ya exporta <code>fecpro</code> (fecha exacta del pago), <code>forpag</code> (forma de pago), <code>nombco</code> (banco), <code>nudopa</code> (número de operación) y <code>monpag</code> (monto cobrado). El sistema ya los guarda en la tabla <code>cobranzas</code>. <strong>Lo que falta es conectar esos registros con los documentos para marcarlos como RECUPERADOS.</strong>
  </div>
</div>

<table class="data-table">
  <thead>
    <tr>
      <th>Campo en Excel Integrens</th>
      <th>Significado</th>
      <th>Ya en Supabase (tabla cobranzas)</th>
      <th>Falta conectar con...</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>fecpro</code></td>
      <td>Fecha exacta del pago en el ERP</td>
      <td style="color:#2B8A3E;font-weight:700;">✅ fecha_gestion</td>
      <td>documentos_ciclo → marcar RECUPERADO con esta fecha</td>
    </tr>
    <tr>
      <td><code>forpag</code></td>
      <td>Forma de pago (EFECTIVO, DEPOSITO, TRANSFERENCIA...)</td>
      <td style="color:#2B8A3E;font-weight:700;">✅ tipo_gestion + metadata.forpag</td>
      <td>resumen_cliente_ciclo → historial de comportamiento de pago</td>
    </tr>
    <tr>
      <td><code>nombco</code> + <code>codbco</code></td>
      <td>Banco donde se realizó el pago</td>
      <td style="color:#2B8A3E;font-weight:700;">✅ notas + metadata</td>
      <td>Informe gerencial → detalle de cobros por banco</td>
    </tr>
    <tr>
      <td><code>nudopa</code> / <code>numope</code></td>
      <td>Número de operación / voucher</td>
      <td style="color:#2B8A3E;font-weight:700;">✅ metadata.nudopa</td>
      <td>Auditoría → comprobante trazable por operación</td>
    </tr>
    <tr>
      <td><code>monpag</code></td>
      <td>Monto cobrado (puede ser pago parcial)</td>
      <td style="color:#2B8A3E;font-weight:700;">✅ monto_gestionado</td>
      <td>documentos_ciclo → calcular saldo residual si pago parcial</td>
    </tr>
  </tbody>
</table>

<!-- QUÉ SE IMPLEMENTA -->
<h3>Qué se implementa en este Feature 9</h3>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:10px;">
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:14px;background:#f7fafd;">
    <div style="font-weight:700;font-size:9pt;color:#0D3B66;margin-bottom:8px;">🔗 Cruce documentos ↔ cobranzas</div>
    <div style="font-size:8.5pt;color:#4a5568;line-height:1.6;">
      Al cargar ciclo nuevo, compara <code>documentos_ciclo</code> anterior con el actual y la tabla <code>cobranzas</code>.<br><br>
      Documentos que desaparecen del Excel → busca el cobro en <code>cobranzas</code> y los marca <strong>RECUPERADO</strong> con fecha, forma y banco.
    </div>
  </div>
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:14px;background:#f7fafd;">
    <div style="font-weight:700;font-size:9pt;color:#0D3B66;margin-bottom:8px;">📊 Tabla resumen_cliente_ciclo</div>
    <div style="font-size:8.5pt;color:#4a5568;line-height:1.6;">
      Al cierre de cada ciclo, agrega por cliente:<br><br>
      Total deuda · documentos vencidos · días mora · tendencia vs. ciclo anterior · patrones de comportamiento de pago.
    </div>
  </div>
  <div style="border:1px solid #d1dce8;border-radius:8px;padding:14px;background:#f7fafd;">
    <div style="font-weight:700;font-size:9pt;color:#0D3B66;margin-bottom:8px;">📈 Tabla resumen_ciclo</div>
    <div style="font-size:8.5pt;color:#4a5568;line-height:1.6;">
      Al cierre de cada ciclo, una sola fila con los totales de toda la cartera.<br><br>
      Base del informe gerencial mensual: cartera total · vencida · pre-legal · recuperado · tasa de recuperación.
    </div>
  </div>
</div>

<!-- DIAGRAMA DE FLUJO -->
<h3 style="margin-top:18px;">Flujo de datos al cargar los 3 Excel de Integrens</h3>

<div class="ui-mockup">
  <div class="ui-mockup-bar">
    <span class="dot dot-r"></span><span class="dot dot-y"></span><span class="dot dot-g"></span>
    <span class="ui-mockup-title">Flujo al hacer clic en "Procesar archivos" — con Feature 9 implementado</span>
  </div>
  <div class="ui-mockup-body">
    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:8.5pt;">

      <div style="background:#0D3B66;color:white;padding:10px 14px;border-radius:8px;text-align:center;min-width:90px;">
        <div style="font-size:10pt;">📂</div>
        <div style="font-weight:700;margin-top:2px;">3 Excel</div>
        <div style="opacity:0.8;font-size:7.5pt;">Integrens</div>
      </div>
      <div style="color:#9ca3af;font-size:16pt;">→</div>

      <div style="background:#1a6fa8;color:white;padding:10px 14px;border-radius:8px;text-align:center;min-width:90px;">
        <div style="font-size:10pt;">⚙️</div>
        <div style="font-weight:700;margin-top:2px;">Procesar</div>
        <div style="opacity:0.8;font-size:7.5pt;">SALDO REAL · DÍAS MORA</div>
      </div>
      <div style="color:#9ca3af;font-size:16pt;">→</div>

      <div style="display:flex;flex-direction:column;gap:6px;">
        <div style="background:#2B8A3E;color:white;padding:7px 12px;border-radius:6px;text-align:center;font-size:8pt;">
          <strong>documentos_ciclo</strong> — 1 fila por factura ✅ ya existe
        </div>
        <div style="background:#e67700;color:white;padding:7px 12px;border-radius:6px;text-align:center;font-size:8pt;">
          <strong>cobranzas</strong> — 1 fila por pago recibido ✅ ya existe
        </div>
        <div style="background:#9333ea;color:white;padding:7px 12px;border-radius:6px;text-align:center;font-size:8pt;">
          <strong>NUEVO: cruce</strong> → marca RECUPERADO con fecha+banco ❌ Feature 9
        </div>
        <div style="background:#0B7285;color:white;padding:7px 12px;border-radius:6px;text-align:center;font-size:8pt;">
          <strong>NUEVO: resumen_cliente_ciclo</strong> — 1 fila por cliente ❌ Feature 9
        </div>
        <div style="background:#c0392b;color:white;padding:7px 12px;border-radius:6px;text-align:center;font-size:8pt;">
          <strong>NUEVO: resumen_ciclo</strong> — 1 fila por mes ❌ Feature 9
        </div>
      </div>

      <div style="color:#9ca3af;font-size:16pt;">→</div>
      <div style="background:#f0fdf4;border:2px solid #22c55e;padding:10px 14px;border-radius:8px;text-align:center;min-width:100px;">
        <div style="font-size:10pt;">🏆</div>
        <div style="font-weight:700;margin-top:2px;color:#15803d;font-size:9pt;">Dashboard + Informe Gerencial</div>
        <div style="color:#556B82;font-size:7.5pt;">con datos reales de Supabase</div>
      </div>
    </div>
  </div>
</div>

<!-- CONSULTA QUE RESPONDE CADA PREGUNTA -->
<h3>Qué pregunta del directorio responde cada nivel</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:10px;">
  <div>
    <div style="font-weight:700;font-size:9pt;color:#0D3B66;margin-bottom:8px;">Preguntas que ya responde hoy</div>
    <div style="font-size:8.5pt;color:#4a5568;line-height:2;">
      ✅ ¿Qué debe el cliente X, factura por factura?<br>
      ✅ ¿Le enviamos WA o email? ¿Respondió?<br>
      ✅ ¿Tiene acuerdo de pago vigente?<br>
      ✅ ¿Cuántas gestiones hicimos este ciclo?
    </div>
  </div>
  <div>
    <div style="font-weight:700;font-size:9pt;color:#9333ea;margin-bottom:8px;">Preguntas que responde con Feature 9</div>
    <div style="font-size:8.5pt;color:#4a5568;line-height:2;">
      🆕 ¿Cuándo exactamente pagó, cómo y en qué banco?<br>
      🆕 ¿Este cliente está mejorando o empeorando su comportamiento de pago?<br>
      🆕 ¿Cuánto de la cartera pre-legal se recuperó en los últimos 6 meses?<br>
      🆕 ¿Cuál es la tendencia de DSO de los últimos 12 meses?
    </div>
  </div>
</div>

<!-- ESFUERZO -->
<div class="roadmap-pills" style="margin-top:18px;">
  <span class="pill pill-file">📄 utils/db_manager.py — función reconcile_ciclo_recovery()</span>
  <span class="pill pill-sql">🗄 SQL: CREATE TABLE resumen_cliente_ciclo</span>
  <span class="pill pill-sql">🗄 SQL: CREATE TABLE resumen_ciclo</span>
  <span class="pill pill-file">📄 app.py — llamada a reconcile al cierre del ciclo</span>
  <span class="pill pill-time">⏱ Estimado: 4–5 horas</span>
</div>

</div>
<div class="page-footer">
  <span>Propuesta CRM WhatsApp v1.0 — DACTA S.A.C.</span>
  <span>Página 11 — Fin del documento</span>
</div>
</div>

</body>
</html>"""


async def generate_pdf():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright no instalado. Ejecute: pip install playwright && playwright install chromium")
        sys.exit(1)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PROPUESTA_CRM_WHATSAPP_v1.0.pdf")
    html_tmp   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_propuesta_tmp.html")

    # Escribir HTML temporal
    with open(html_tmp, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)

    print("Generando PDF con Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"file:///{html_tmp.replace(chr(92), '/')}", wait_until="networkidle")
        await page.wait_for_timeout(1500)  # tiempo para que carguen fuentes

        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
        )
        await browser.close()

    os.remove(html_tmp)
    print(f"\n✅ PDF generado exitosamente:")
    print(f"   {output_path}")
    print(f"   Tamaño: {os.path.getsize(output_path) / 1024:.1f} KB")


if __name__ == "__main__":
    # Compatibilidad Windows con nest_asyncio si ya hay un loop activo
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass

    asyncio.run(generate_pdf())
