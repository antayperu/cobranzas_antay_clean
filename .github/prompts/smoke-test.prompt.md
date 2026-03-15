---
mode: agent
description: Ejecuta el smoke test completo TIER 2 en staging (localhost:8502)
---

# Smoke Test TIER 2 — ReporteCobranzas Staging

Ejecuta el checklist completo de smoke test en el ambiente de staging.

## Pre-requisitos

Verificar que staging esté corriendo:
```powershell
# En PowerShell:
$env:SUPABASE_URL="https://hrnqngndnohkkegtzgjg.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="<ver .env.staging>"
streamlit run app.py --server.port 8502
```

## Checklist CA-1: Fresh Load

- [ ] Cargar 2 Excel (CtasxCobrar + Cobranza) en sidebar
- [ ] Reporte General se genera correctamente
- [ ] KPIs Email: Enviados Hoy = 0, Pendientes > 0
- [ ] Ciclo ID visible en sidebar (formato CIC-YYYYMMDD-HHMM)
- [ ] Banner "🧪 AMBIENTE DE PRUEBAS (STAGING)" visible

## Checklist CA-WA: Panel Post-Envío WhatsApp

- [ ] Ir a Tab WhatsApp
- [ ] Seleccionar plantilla (CRM-002)
- [ ] Seleccionar clientes y enviar
- [ ] Panel post-envío aparece con opciones de resultado
- [ ] Registrar resultado "PROMETIO_PAGAR" para un cliente
- [ ] Verificar que gestión aparece en CRM Gestiones
- [ ] Monto muestra `S/ X + $ Y` (no el doble)

## Checklist CA-WA-4: Acuerdos de Pago

- [ ] Ir a CRM → Acuerdos de Pago
- [ ] Crear acuerdo: seleccionar cliente, monto, 3 cuotas, fecha inicio
- [ ] Verificar cálculo automático de fechas por cuota
- [ ] Timeline visual muestra cuotas PENDIENTE
- [ ] Registro persiste en Supabase staging

## Checklist CA-WA-5: Bandeja de Pendientes

- [ ] Ir a CRM → Bandeja Pendientes
- [ ] Verificar que se detectan ítems (WA sin respuesta, cuotas, mora)
- [ ] Botón de acción directa operativo

## Checklist CA-SUP-5: Clientes Premium

- [ ] Ir a Tab Clientes Premium
- [ ] Editar email de un cliente
- [ ] Recargar app y verificar que el cambio persiste

## Resultado

Reportar PASS/FAIL por cada checklist.
Si todo PASS → proceder con merge `dev → main`.
Si algún FAIL → abrir ticket RC-BUG-XXX y corregir antes del merge.
