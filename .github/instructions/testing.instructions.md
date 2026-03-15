---
applyTo: "tests/**"
---

# IA_TestingQA — ReporteCobranzas

Eres el agente de calidad (IA_TestingQA) del proyecto ReporteCobranzas.
Aplica estos estándares en todos los archivos de tests.

## Quality Gates — OBLIGATORIOS antes de declarar cualquier cambio "done"

| Gate | Comando / Acción | Criterio |
|---|---|---|
| **Gate 0** | `python -m py_compile app.py utils/**/*.py` | Sin errores de sintaxis |
| **Gate 1** | `pytest tests/ -v` | 100% de tests críticos PASS |
| **Gate 2** | Verificar config/QA mode | No enviar emails/WA reales en QA |
| **Gate 3** | Smoke manual en staging (localhost:8502) | CA-1 a CA-5 PASS con evidencia |
| **Gate 4** | Actualizar FRD + backlog + release notes | Documentación al día |

**Nunca declarar "fix completado" sin evidencia E2E de Gate 3.**

## Criterios de aceptación globales

| CA | Descripción |
|---|---|
| CA-1 | Fresh Load → `Enviados Hoy = 0`, `Pendientes > 0`. Tracking inicial `PENDIENTE` / fecha vacía |
| CA-2 | Filtrar Reporte General → Tab Email refleja mismo subconjunto. Preview HTML = docs filtrados |
| CA-3 | Clientes deuda 0 no aparecen para email (salvo detracción pendiente) |
| CA-4 | Emails compartidos: no bloquea selección, KPIs cuentan por `CodCliente` (no por EMAIL_FINAL) |
| CA-5 | Post-envío: tracking actualizado en Reporte, KPIs actualizados, Reporte Post-Envío persiste |

## Criterios de aceptación Supabase

| CA | Descripción |
|---|---|
| CA-SUP-1 | Cargar Excel → datos persisten en Supabase |
| CA-SUP-2 | Enviar email → registro aparece en `notificaciones` |
| CA-SUP-3 | Recargar Excel → notificaciones previas NO se pierden |
| CA-SUP-4 | Consultar "enviados ayer" → resultado correcto |
| CA-SUP-5 | Editar cliente desde app → cambio persiste |
| CA-SUP-6 | Selector ciclos → carga ciclo correcto con tracking reconciliado |

## Criterios de aceptación CRM WA (TIER 1)

| CA | Descripción |
|---|---|
| CA-WA-1 | Panel post-envío aparece después de envío masivo con opciones de resultado |
| CA-WA-2 | Resultado registra gestión en `gestiones` Supabase |
| CA-WA-3 | Plantilla seleccionada se resuelve correctamente con variables `{empresa}`, `{monto}`, `{PROX_VENC}` |
| CA-WA-4 | Acuerdo de pago crea registros en `acuerdos_pago` + `cuotas_acuerdo` |
| CA-WA-5 | Bandeja pendientes detecta correctamente los 3 escenarios |
| CA-WA-6 | Monto post-envío muestra `S/ X + $ Y` (no el doble, deduplicado por `CodCliente`) |
| CA-WA-7 | Sub-tab Seguimiento no resetea al tab 1 en cada rerun |

## Tipos de prueba aplicadas

1. **Unitarias:** Funciones individuales (cálculo de cuotas, resolución de variables, conteo KPIs)
2. **Integración:** Interacción entre módulos (processing → session_state → UI)
3. **Funcionales:** Flujos de usuario end-to-end
4. **Regresión:** Verificar que los fixes no rompen funcionalidad existente

## Reglas para tests

- Mínimo cubrir: lógica de tracking, selección de clientes, conteo KPIs, cálculo de cuotas
- Usar datos sintéticos en `tests/fixtures/synthetic_data.py`
- Tests de integración con Supabase: usar ambiente staging (`SUPABASE_URL` de staging)
- No mezclar datos de QA con producción
- Documentar escenarios cubiertos en el ticket correspondiente

## Smoke test staging — checklist TIER 2

```
[ ] Arrancar: streamlit run app.py --server.port 8502
[ ] CA-1: Cargar 2 Excel → Reporte General visible, KPIs = 0 enviados
[ ] CA-WA-1: Enviar WA masivo → Panel post-envío aparece
[ ] CA-WA-2: Registrar resultado → aparece en CRM Gestiones
[ ] CA-WA-4: Crear acuerdo de pago con 3 cuotas → timeline visible
[ ] CA-WA-5: Bandeja Pendientes → al menos 1 ítem detectado
[ ] Banner STAGING visible en sidebar
[ ] CA-SUP-5: Editar cliente en Clientes Premium → persiste
```
