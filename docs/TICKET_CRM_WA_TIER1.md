# TICKET TIER 1 — CRM WhatsApp Completo

**ID:** CRM-WA-TIER1  
**Proyecto:** ReporteCobranzas — Antay Perú  
**Referencia FRD:** `docs/FRD_REPORTECOBRANZAS_v2.0.md` secciones 9 y 10  
**Estado:** COMPLETADO ✅  
**Tag:** `v1.6.0`  
**Tests:** 141/141 PASS  
**Commit cierre TIER 1:** (merge dev → main, 2026-03-13)  
**Commit fix final:** `58ca367` (RC-BUG-030/031, 2026-03-15)  
**Responsable:** Antigravity (GitHub Copilot / Claude Sonnet)  
**Supervisor:** Camilo Ortega F.R.

---

## Resumen Ejecutivo

Implementación completa del módulo CRM WhatsApp: panel de seguimiento post-envío, biblioteca de plantillas, acuerdos de pago con cuotas, bandeja de pendientes, trazabilidad completa y todas las mejoras de flujo necesarias para operar el ciclo de cobranza desde la app.

---

## Features implementados

### RC-FEAT-019 — Panel Resultado Post-Envío WA
- **Archivo:** `utils/ui/tabs/whatsapp.py`
- Panel de seguimiento post-lote
- Opciones de resultado: `EXITOSO` / `PROMETIO_PAGAR` / `SIN_RESPUESTA` / `ESCALAR`
- Llama a `insert_gestion()` con `tipo_gestion=WHATSAPP`
- Persiste en `gestiones.resultado` en Supabase
- Criterios aceptación:
  - [x] Panel aparece después de envío masivo
  - [x] Cada resultado registra gestión en Supabase
  - [x] Resumen de resultados visible

### RC-FEAT-020 — Biblioteca 7 Plantillas WhatsApp
- **Archivos:** `utils/ui/tabs/whatsapp.py`, `utils/ui/tabs/config_tab.py`
- Selector visual antes del envío
- 7 plantillas: primer aviso, recordatorio, aviso firme, acuerdo, pre-legal, felicitación, solicitud datos
- Variables: `{empresa}`, `{monto}`, `{fecha_venc}`, `{gestor}`, `{PROX_VENC}`
- Editables desde Tab Configuración, guardadas en `app_config` Supabase
- Criterios aceptación:
  - [x] Selector visible antes de enviar
  - [x] 7 plantillas predefinidas con variables
  - [x] Plantilla seleccionada grabada en `gestiones.metadata.template`
  - [x] Variables resueltas correctamente en preview

### RC-FEAT-021 — Módulo Acuerdos de Pago con Cuotas
- **Archivo:** `utils/ui/tabs/crm_gestiones.py`
- Tablas nuevas: `acuerdos_pago` + `cuotas_acuerdo`
- Formulario: cliente, monto total, nro cuotas, fecha inicio
- Cálculo automático de fechas por cuota
- Timeline visual: `PENDIENTE` / `PAGADA` / `VENCIDA`
- WA automático al crear acuerdo
- Criterios aceptación:
  - [x] Tablas creadas en Supabase
  - [x] Formulario funcional
  - [x] Cálculo automático de cuotas correcto
  - [x] Timeline visual operativo

### RC-FEAT-022 — Bandeja de Pendientes del Día
- **Archivo:** `utils/ui/tabs/crm_gestiones.py`
- Prioridades: `URGENTE` / `ALTO` / `MEDIO`
- Detecta: WA sin respuesta +48h, cuotas venciendo ≤3 días, mora +30 días sin gestión
- Botón de acción directa por ítem
- Criterios aceptación:
  - [x] Lista priorizada generada automáticamente
  - [x] Lógica de detección correcta para los 3 escenarios
  - [x] Acciones directas operativas

### RC-FEAT-023 — Trazabilidad Completa
- **Archivo:** `utils/db_manager.py`
- Tablas: `resumen_cliente_ciclo` + `resumen_ciclo`
- `reconcile_ciclo_recovery()` para documentos recuperados
- Criterios aceptación:
  - [x] Tablas creadas y pobladas al cierre de ciclo
  - [x] Documentos desaparecidos → estado `RECUPERADO` + metadata

### RC-FEAT-024 — Tabs CRM Persistentes
- **Archivo:** `utils/ui/sidebar.py`, `app.py`
- Sidebar no limpia `df_final` al confirmar reemplazar archivos
- CRM visible durante transición de ciclo

### RC-FEAT-025 — Auto-restore Último Ciclo
- **Archivo:** `app.py`
- `attempt_auto_restore()` al abrir la app
- Flag `skip_auto_restore` evita sobreescritura por elección manual

---

## Hotfixes asociados

| ID | Descripción | Archivo afectado |
|---|---|---|
| RC-BUG-024 | `CREATE POLICY IF NOT EXISTS` incompatible con PostgreSQL | `sql/11_*.sql`, `sql/12_*.sql` |
| RC-BUG-025 | `insert_acuerdo_pago` error `.select()` encadenado | `utils/db_manager.py` |
| RC-BUG-026 | ESTADO_* en blanco al restaurar ciclo | `utils/processing.py` |
| RC-BUG-027 | Selectbox plantilla WA se resetea en rerun | `utils/ui/tabs/whatsapp.py` |
| RC-BUG-028 | Variable `{PROX_VENC}` faltante en plantillas | `utils/ui/tabs/whatsapp.py` |
| RC-BUG-029 | Auto-restore sobreescribe elección manual de ciclo | `app.py` |
| RC-BUG-030 | Sub-tab Seguimiento reseteaba al tab 1 en cada rerun | `utils/ui/tabs/whatsapp.py` |
| RC-BUG-031 | Monto WA mostraba solo S/ y con doble conteo | `utils/ui/tabs/whatsapp.py` |
| RC-UX-013 | Banner STAGING/PROD en sidebar | `utils/ui/sidebar.py` |
| RC-OPS-006 | Ambiente staging configurado | `.env.staging`, `.gitignore` |
| RC-OPS-007 | Rama `master` remota eliminada, 5 feature branches limpiadas | git |

---

## Evidencias de calidad

- Gate 0 (compilación): ✅ PASS
- Gate 1 (pytest): ✅ 141/141 tests PASS
- Gate 3 (smoke TIER 1): ✅ PASS en staging
- Gate 4 (documentación): ✅ FRD v2.0 + backlog + tickets actualizados

---

## Pendiente TIER 2

Ver `docs/FRD_REPORTECOBRANZAS_v2.0.md` sección 15.  
Próximo ticket: `RC-FEAT-026` — Panel envío WA de prueba en Tab Configuración.
