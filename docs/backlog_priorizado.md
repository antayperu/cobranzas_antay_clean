# Backlog Priorizado - ReporteCobranzas Antay

Ultima actualizacion: 2026-03-28
Version actual: v2.0.0 (TIER 2 completado — RC-FEAT-039 + RC-BUG-063→071 + RC-UX-001/002/003 · pendiente Gate 3 QA)
Estado migracion Supabase: Completada. Todas las fases MIG-000 a MIG-009 + SUPABASE-002 + CONFIG-001 cerradas.
Iniciativa CRM WhatsApp: TIER 1 completado 2026-03-13 (141/141 tests). TIER 2 completado 2026-03-16. TIER 3 pendiente.
Informe Gerencial PDF: TIER 2 completado 2026-03-28 (162/162 tests). Gate 3 QA pendiente en PC servidor.

---

## 0. Sprint CRM WhatsApp — TIER 1 ✅ COMPLETADO (2026-03-13, tag v1.6.0)

### CRM-001: Resultado Post-Envío WhatsApp (RC-FEAT-019)
- Estado: Done ✅
- Esfuerzo: 2 puntos (1–2 horas)
- Prioridad: P1 Alto
- Dependencias: ninguna
- Descripcion: Panel de seguimiento post-lote en Tab WhatsApp. El gestor registra con 1 click si el cliente acordó, prometió, no contestó o escalar. Persiste en `gestiones.resultado` en Supabase.
- Criterios de Aceptacion:
  - [x] Aparece panel de resultados después de envío masivo
  - [x] Opciones: EXITOSO / PROMETIO_PAGAR / SIN_RESPUESTA / ESCALAR
  - [x] Cada resultado llama a `insert_gestion()` con tipo_gestion=WHATSAPP
  - [x] Se muestra resumen de resultados registrados
  - [x] Tests unitarios actualizados

---

### CRM-002: Biblioteca de 7 Plantillas WhatsApp (RC-FEAT-020)
- Estado: Done ✅
- Esfuerzo: 3 puntos (3–4 horas)
- Prioridad: P1 Alto
- Dependencias: ninguna (puede ir en paralelo con CRM-001)
- Descripcion: Selector visual de plantilla antes del envío masivo. 7 plantillas por escenario (primer aviso, recordatorio, aviso firme, acuerdo, pre-legal, felicitación, solicitud datos). Editables desde Configuración. Guardadas en Supabase `app_config`.
- Criterios de Aceptacion:
  - [x] Selector desplegable de plantilla visible antes de enviar
  - [x] 7 plantillas predefinidas con variables: {empresa}, {monto}, {fecha_venc}, {gestor}
  - [x] Plantillas editables en Tab Configuración
  - [x] Plantilla seleccionada se graba en `gestiones.metadata.template`
  - [x] Tests unitarios para resolución de variables

---

### CRM-003: Módulo de Acuerdos de Pago con Cuotas (RC-FEAT-021)
- Estado: Done ✅
- Esfuerzo: 5 puntos (4–6 horas)
- Prioridad: P1 Alto
- Dependencias: CRM-001 recomendado (para registrar gestión asociada)
- Descripcion: Nueva sección en Centro de Gestiones. Formulario para registrar acuerdos de pago, cálculo automático de cuotas, timeline visual de estado, WA de confirmación automático. Requiere 2 nuevas tablas en Supabase.
- Criterios de Aceptacion:
  - [x] CREATE TABLE acuerdos_pago en Supabase
  - [x] CREATE TABLE cuotas_acuerdo en Supabase
  - [x] Formulario: cliente, monto total, cuotas, fecha inicio
  - [x] Cálculo automático de fechas de vencimiento por cuota
  - [x] Timeline visual: cuotas PENDIENTE / PAGADA / VENCIDA
  - [x] WA automático de confirmación al crear acuerdo
  - [x] Tests unitarios para cálculo de cuotas

---

### CRM-004: Bandeja de Pendientes del Día (RC-FEAT-022)
- Estado: Done ✅
- Esfuerzo: 2 puntos (2–3 horas)
- Prioridad: P1 Alto
- Dependencias: CRM-003 (requiere tabla cuotas_acuerdo)
- Descripcion: Nueva pestaña en Centro de Gestiones con lista priorizada de acciones diarias generada automáticamente. Detecta: WA sin respuesta +48h, cuotas venciendo hoy/en 3 días, clientes con mora crítica sin contacto. Cada ítem con botones de acción directa.
- Criterios de Aceptacion:
  - [x] Lista de pendientes por prioridad (URGENTE / ALTO / MEDIO)
  - [x] Detecta WA enviado hace +48h sin resultado registrado
  - [x] Detecta cuotas venciendo en ≤3 días
  - [x] Detecta clientes +30 días mora sin ninguna gestión
  - [x] Botón acción directa por ítem (Registrar resultado / Enviar WA / Ver acuerdo)
  - [x] Tests unitarios para lógica de detección

---

### CRM-009: Trazabilidad Completa — Cruce documentos + 2 tablas resumen (RC-FEAT-023)
- Estado: Done ✅
- Esfuerzo: 4 puntos (4–5 horas)
- Prioridad: P1 Alto
- Dependencias: ninguna (trabaja sobre tablas existentes)
- Descripcion: Al cargar ciclo nuevo, cruzar documentos_ciclo anterior con cobranzas de Integrens para marcar documentos RECUPERADOS con fecha, forma de pago y banco. Crear tablas resumen_cliente_ciclo y resumen_ciclo para alimentar dashboard e informe gerencial.
- Criterios de Aceptacion:
  - [x] CREATE TABLE resumen_cliente_ciclo en Supabase
  - [x] CREATE TABLE resumen_ciclo en Supabase
  - [x] Función reconcile_ciclo_recovery() en db_manager.py
  - [x] Al cargar ciclo: documentos desaparecidos → estado RECUPERADO + fecha + forma_pago + banco
  - [x] Al cierre de ciclo: 1 fila en resumen_cliente_ciclo por cliente
  - [x] Al cierre de ciclo: 1 fila en resumen_ciclo con totales de cartera
  - [x] Tests unitarios para reconciliación

---

## 0.1. Post-TIER 1 — Hotfixes & Mejoras CRM (2026-03-13/14)

### Hotfixes SQL Supabase
- Estado: Done ✅
- RC-BUG-024: Fix `CREATE POLICY IF NOT EXISTS` incompatible con PostgreSQL (sql/11, sql/12) → bloque `DO $$`
- RC-BUG-025: Fix `insert_acuerdo_pago` error `.select()` encadenado — supabase-py sync client no lo soporta

### Bugs Smoke Test WA (3 bugs)
- Estado: Done ✅
- RC-BUG-026: Campos ESTADO_EMAIL / ESTADO_WHATSAPP en blanco al restaurar ciclo → `fillna('PENDIENTE')` en `_docs_to_df()`
- RC-BUG-027: Selectbox plantilla WA se resetea en cada rerun → `key="wa_plantilla_seleccionada"`
- RC-BUG-028: Variable `{PROX_VENC}` no disponible en plantillas → agregada a `contact_data` y preview

### Mejoras CRM Flow
- Estado: Done ✅
- RC-FEAT-024: Tabs CRM permanecen visibles al preparar nuevo ciclo — sidebar ya no limpia `df_final` al confirmar reemplazar
- RC-FEAT-025: Auto-restore automático del último ciclo al abrir la app (`attempt_auto_restore()` en `app.py`)
- RC-BUG-029: Botón "Cambiar ciclo" ya no es sobreescrito por auto-restore → flag `skip_auto_restore`

### Infraestructura & Documentación
- Estado: Done ✅
- RC-OPS-005: `sql/13_alter_gestiones_add_cycle_id.sql` — documenta ALTER ya ejecutado en PROD (cycle_id en gestiones)
- RC-OPS-006: Ambiente de staging configurado — Supabase staging + `.env.staging` + `.gitignore` actualizado
- RC-UX-013: Banner de ambiente STAGING/PROD en sidebar — detección automática via `SUPABASE_URL`
  - Gitflow completo: `feature/env-indicator-banner` → `dev` → `main` → push PROD

### Limpieza de Repositorio
- Estado: Done ✅
- RC-OPS-007: Rama `master` remota eliminada (redundante, todos los commits ya en `main`)
- 5 feature branches mergeadas eliminadas localmente (RC-FEAT-019 a RC-FEAT-023)
- Gitflow Antay formalizado: `feature/* → dev → staging test → main → PROD`

### Bugs Sub-tab Seguimiento Post-Envío WA (2026-03-15)
- Estado: Done ✅ — commit `58ca367`
- RC-BUG-030: Tab "Seguimiento Post-Envío" reseteaba al tab 1 en cada rerun de widget
  - Causa: `st.tabs` y luego `st.radio+key` con label dinámico (emoji 🔴 rompía el match de string)
  - Fix: persistir por índice entero `wa_subtab_idx` en session_state
- RC-BUG-031: Monto mostraba solo S/ (sin $) y doble conteo
  - Causa: `wa_details` no guardaba montos por moneda; fallback Supabase usaba `SALDO REAL` plano
  - Fix: guardar `DeudaS`/`DeudaD` explícitos al enviar y recalcular desde `df_filtered` en fallback
  - Fix: deduplicar `CodCliente` en cálculo (un cliente tiene fila Envío + fila Gestión)
- Criterios de aceptación definidos y documentados en `RETOMAR_SESION.md`

### Completados — TIER 2 (Sprint 2026-03-24/28) ✅ → v2.0.0 · Gate 3 pendiente
- RC-FEAT-039: Informe Gerencial PDF para Comité de Directorio — Secciones A-F ✅
- RC-FIX-062: Recuperado real dual moneda (S/ + US$) desde resumen_ciclo — diferencia CxC ✅
- RC-UX-001: Sidebar progressive disclosure + slots duales con feedback visual por archivo ✅
- RC-UX-002: PDF Informe Gerencial — tipografía Manrope + IBM Plex Sans, visual premium ✅
- RC-UX-003: Filtro Cartera Activa / General en panel PDF ✅
- RC-BUG-063: SMTP leía session_state incorrecto — ahora usa config['smtp_config'] ✅
- RC-BUG-064: Footer/portada del PDF usaban empresa hardcodeada ✅
- RC-BUG-065: Credenciales SMTP se perdían en cada refresco ✅
- RC-BUG-066: prev_cycle_id leído desde Supabase (no session_state) ✅
- RC-BUG-067: Lazy reconciliation en get_recovery_stats() ✅
- RC-BUG-068: Gestiones y acuerdos del Informe filtrados por scope ✅
- RC-BUG-069: Recovery y título del PDF respetan scope activa/general ✅
- RC-BUG-071: Rediseño Semáforo Ejecutivo — AR Roll Forward (corrige doble sustracción) ✅

### Completados — TIER 2 (Sprint 2026-03-16) ✅
- RC-FEAT-026: Panel de envío WA de prueba en Config Tab — `config_tab.py` SECCIÓN 8 ✅
- RC-BUG-032: Notas vacías en historial post-rerun (causa raíz: `notas` faltaba en SELECT Supabase) ✅
- RC-BUG-033: Saldo sin moneda en tablas historial y pendientes (usa `DeudaS`/`DeudaD`) ✅
- RC-FEAT-034: 9 mejoras UX panel Seguimiento Post-Envío WA ✅
  - Orden por saldo desc, link wa.me, % efectividad, ícono tipo, tooltip notas
  - Barra progreso ciclo, color semántico saldo, badge ↩ Reintentar, tooltip guardar todos
- RC-DOCS-001: Context engineering — copilot-instructions.md, 5 skills, FRD v2.0 PDF ✅

### Pendiente — TIER 2 (sin iniciar)
- RC-FEAT-027: Selección automática de plantilla por Aging
- RC-FEAT-028: KPIs Expandidos de Efectividad de Cobranza

### Pendiente — TIER 3 (Features futuras)
- RC-FEAT-029: Registro de Pagos en Tiempo Real (sin esperar ERP)
- RC-FEAT-030: Dashboard de Efectividad de Cobranza (analytics 7/15/30 días)
- RC-FEAT-035: Link historial CRM completo del cliente desde panel WA Seguimiento Post-Envío

### Pendiente — TIER 3 (Mejoras arquitectónicas — Filosofía Class Worldwide)

#### RC-FEAT-036: Tabla separada `wa_mensajes_enviados` para auditoría de mensajes
- Estado: Pendiente
- Prioridad: P1 Alto (Arquitectura)
- Esfuerzo: 5 puntos (1-2 días)
- Descripción: Extraer mensajes del campo JSON metadata → tabla independiente. Violación de estándar: datos críticos de auditoría NO deben vivir en JSON. Afecta escalabilidad (búsquedas, índices, reportes).
- Beneficios: Auditoría sin parseo JSON, búsquedas rápidas, escalable Fortune 500
- Tabla propuesta:
  ```sql
  CREATE TABLE wa_mensajes_enviados (
    id UUID PK, gestion_id UUID FK, cliente_id TEXT FK, 
    template_label, template_texto, mensaje_exacto_enviado,
    telefono_destino, batch_id, send_mode, created_at
  );
  ```

#### RC-FEAT-037: Catálogo editable de resultados gestión WA
- Estado: Pendiente
- Prioridad: P1 Alto (Flexibilidad de producto)
- Esfuerzo: 3 puntos (1-2 días)
- Descripción: Mover resultados hardcodeados (EXITOSO, PENDIENTE, SIN_RESPUESTA, REPROGRAMADO) a tabla `catalogo_resultado_gestion` editable. Hoy es imposible agregar nuevos resultado sin cambiar código Python.
- Beneficios: Flexible sin redeploy, auditable (quién/cuándo cambió), multiidioma, escalable
- Panel en Configuración: CRUD (crear/editar/borrar) resultados desde UI
- Tabla propuesta:
  ```sql
  CREATE TABLE catalogo_resultado_gestion (
    id UUID PK, codigo_resultado TEXT UNIQUE, label_ui, descripción,
    color_badge, activo, orden, created_at
  );
  ```

#### RC-BUG-050: Join mensaje a fila gestión en historial
- Estado: Pendiente / Diferido
- Prioridad: P2 Medio
- Esfuerzo: 2 puntos (2-3 horas)
- Dependencia: RC-FEAT-036 (requiere tabla wa_mensajes_enviados)
- Descripción: Columna "Mensaje WA" solo se llena si fila es Envío. Si hay gestión manual posterior, mensaje no se muestra. Requiere JOIN: gestiones ← wa_mensajes_enviados.

---

## 1. Prioridad Critica (Sprint Actual)

### SUPABASE-MIG-000: Bootstrap Inicial de Datos (Excel -> Supabase)
- Estado: Completado
- Esfuerzo: 5 puntos
- Resultado:
  - clientes: 199
  - documentos: 231
  - cobranzas: 165
- Entregables:
  - Script `scripts/migrate_excel_to_supabase.py`
  - Regla de integridad: no insertar cobranzas huerfanas

---

### SUPABASE-MIG-001: Integracion de Carga desde UI (3 Excel)
- Estado: Completado
- Esfuerzo: 8 puntos (2-3 dias)
- Dependencias: SUPABASE-MIG-000
- Descripcion: Conectar la carga desde la interfaz actual (sidebar) para persistir automaticamente en Supabase sin cambiar UX.
- Criterios de Aceptacion:
  - [x] Se mantienen los mismos uploaders actuales.
  - [x] Flujo de usuario no cambia (cargar -> revisar -> exportar -> enviar).
  - [x] Al cargar 3 archivos se ejecuta persistencia en `clientes`, `documentos`, `cobranzas`.
  - [x] En fallo de Supabase, app aplica bloqueo controlado (sin fallback local).

---

### SUPABASE-MIG-002: Paridad Funcional del Excel de Salida (No Regresion)
- Estado: Completado
- Esfuerzo: 5 puntos (1-2 dias)
- Dependencias: SUPABASE-MIG-001
- Descripcion: Garantizar que el export Excel mantenga campos, orden y calculos actuales.
- Evidencia:
  - `docs/EVIDENCIA_PARIDAD_EXPORT_SUPABASE_MIG002.md`
- Criterios de Aceptacion:
  - [x] Mismas columnas que baseline.
  - [x] Mismo orden de columnas.
  - [x] Mismos calculos de deuda/detraccion/saldo.
  - [x] Mismo comportamiento con filtros.
  - [x] Evidencia de comparacion pre/post migracion.

---

### SUPABASE-MIG-003: Persistencia de Notificaciones por Cliente
- Estado: Completado
- Esfuerzo: 8 puntos (2-3 dias)
- Dependencias: SUPABASE-MIG-001
- Descripcion: Registrar cada envio en `notificaciones` con `cliente_id` y contexto de envio.
- Criterios de Aceptacion:
  - [x] Cada envio Email crea registro en `notificaciones`.
  - [x] Se persiste `cliente_id`, `destinatario`, `estado`, `fecha_envio`, metadata.
  - [x] Cuando aplique, se vincula `documento_id`.
  - [x] Se puede consultar historial por cliente.

---

### SUPABASE-MIG-004: Integridad de Datos y Reporte de No-Match
- Estado: Completado
- Esfuerzo: 3 puntos (1 dia)
- Dependencias: SUPABASE-MIG-001
- Descripcion: Formalizar reporte de cobranzas no matcheadas y chequeos de integridad.
- Evidencia:
  - `docs/EVIDENCIA_INTEGRIDAD_NO_MATCH_SUPABASE_MIG004.md`
- Criterios de Aceptacion:
  - [x] Query de control de huerfanos retorna cero.
  - [x] Se genera reporte de filas de cobranza sin documento asociado.
  - [x] Runbook operativo documentado en `docs/PLAN_MIGRACION_SUPABASE_PREMIUM_v1.0.md`.

---

## 2. Prioridad Alta (Siguiente Sprint)

### SUPABASE-MIG-005: Mantenimiento de Clientes desde App
- Estado: Completado
- Esfuerzo: 5 puntos (1-2 dias)
- Dependencias: SUPABASE-MIG-001
- Descripcion: Permitir editar telefono/email/estado de cliente sin recargar excels.
- Evidencia:
  - `docs/EVIDENCIA_MANTENIMIENTO_CLIENTES_SUPABASE_MIG005.md`
- Criterios de Aceptacion:
  - [x] UI para editar cliente.
  - [x] Update persistente en tabla `clientes`.
  - [x] Auditoria minima de cambios.

---

### SUPABASE-MIG-006: Reporte Premium de Notificaciones
- Estado: Completado
- Esfuerzo: 5 puntos (1-2 dias)
- Dependencias: SUPABASE-MIG-003
- Descripcion: Dashboard operativo por cliente para envios, estados y fechas.
- Evidencia:
  - `docs/EVIDENCIA_REPORTE_PREMIUM_NOTIFICACIONES_SUPABASE_MIG006.md`
- Criterios de Aceptacion:
  - [x] Reporte por cliente.
  - [x] Filtros por fecha/estado/canal.
  - [x] KPIs de enviados, fallidos y pendientes.

---

### SUPABASE-MIG-007: Quality Gates Automatizados de Migracion
- Estado: Completado
- Esfuerzo: 8 puntos (2-3 dias)
- Dependencias: SUPABASE-MIG-001, SUPABASE-MIG-002, SUPABASE-MIG-003
- Descripcion: Crear pruebas automatizadas para paridad, integridad y resiliencia.
- Evidencia:
  - `docs/EVIDENCIA_QUALITY_GATES_SUPABASE_MIG007.md`
- Criterios de Aceptacion:
  - [x] Test de paridad de export.
  - [x] Test de integridad FK.
  - [x] Test de idempotencia de cargas.
  - [x] Test de politica cloud-only (retry y bloqueo controlado).

---

## 3. Prioridad Media

### SUPABASE-MIG-008: Seguridad Operacional (RLS + Politicas)
- Estado: Completado
- Esfuerzo: 5 puntos
- Dependencias: SUPABASE-MIG-001
- Evidencia:
  - `docs/EVIDENCIA_SEGURIDAD_SUPABASE_MIG008.md`
- Criterios de Aceptacion:
  - [x] Politicas RLS definidas para tablas operativas.
  - [x] Uso de llaves revisado por entorno.
  - [x] Checklist de seguridad documentado.

---

### SUPABASE-MIG-009: Backups y Recuperacion
- Estado: Completado
- Esfuerzo: 3 puntos
- Dependencias: SUPABASE-MIG-008
- Evidencia:
  - `docs/EVIDENCIA_BACKUP_RESTORE_SUPABASE_MIG009.md`
- Criterios de Aceptacion:
  - [x] Procedimiento de backup.
  - [x] Procedimiento de restore validado.
  - [x] Evidencia de prueba de recuperacion.

---

## 4. Iniciativas Relacionadas (No bloqueantes de migracion)

### SUPABASE-002: Storage de Archivos e Imagenes
- Estado: Completado
- Dependencias: SUPABASE-MIG-001
- Evidencia:
  - `docs/EVIDENCIA_STORAGE_SUPABASE_002.md`
  - `docs/EVIDENCIA_MERGE_GITFLOW_SUPABASE_002.md`
- Entregables:
  - `utils/storage_manager.py`
  - `scripts/setup_supabase_storage.py`
- Criterios de Aceptacion:
  - [x] Buckets `logos`, `exports`, `whatsapp-images` creados.
  - [x] Logo sincronizable en Storage desde UI de Configuracion.
  - [x] Export Excel guarda copia en bucket `exports`.
  - [x] Quality gate de Storage agregado y en PASS.

### CONFIG-001: Configuracion en Supabase
- Estado: Completado (pendiente ejecucion SQL `sql/07_create_app_config.sql` en entorno)
- Dependencias: SUPABASE-MIG-001
- Entregables:
  - `sql/07_create_app_config.sql`
  - `utils/settings_manager.py` (cloud-first: `app_config`)
  - `tests/test_settings_manager.py`

### FEATURE-001: Dashboard de Analytics
- Estado: Pendiente

### FEATURE-002: Clientes Premium (Cartera Maestra + TAB Independiente)
- Estado: Completado
- Dependencias: SUPABASE-MIG-001, SUPABASE-MIG-005
- Referencia FRD:
  - `docs/FRD_CLIENTES_PREMIUM_v1.0.md`
  - `docs/TICKET_FEATURE_002_CLIENTES_PREMIUM.md`
- Descripcion:
  - Crear TAB dedicada para mantenimiento de clientes con edicion total y migracion de cartera.
  - Operacion principal orientada a carga de 2 archivos (CtasxCobrar + Cobranza) usando cartera maestra en Supabase.
- Criterios de Aceptacion:
  - [x] TAB independiente de clientes habilitada.
  - [x] Edicion de cualquier campo operativo en `clientes`.
  - [x] Migracion de cartera desde Excel con reporte de errores.
  - [x] Flujo principal 2 archivos operativo con cartera maestra.

### FEATURE-004: Home Operativo Estricto (2 Archivos)
- Estado: Completado
- Dependencias: FEATURE-002
- Referencia FRD:
  - `docs/FRD_CLIENTES_PREMIUM_v1.0.md`
  - `docs/TICKET_FEATURE_002_CLIENTES_PREMIUM.md`
  - `docs/TICKET_FEATURE_004_HOME_2_ARCHIVOS.md`
- Descripcion:
  - Eliminar carga de cartera en sidebar principal.
  - Procesar solo `CtasxCobrar + Cobranza` con cartera maestra de Supabase.
- Criterios de Aceptacion:
  - [x] Sidebar muestra solo uploaders de `CtasxCobrar` y `Cobranza`.
  - [x] Boton de procesamiento se habilita solo con esos 2 archivos.
  - [x] Si no hay cartera maestra, se bloquea ciclo con mensaje operativo.

### FEATURE-005: UX Corporativo Premium del Home
- Estado: Completado
- Dependencias: FEATURE-004
- Referencia FRD:
  - `docs/FRD_CLIENTES_PREMIUM_v1.0.md`
  - `docs/TICKET_FEATURE_005_UX_HOME_PREMIUM.md`
- Descripcion:
  - Renovar visual de sidebar y bienvenida para reflejar flujo empresarial de 2 archivos.
  - Estandarizar guias de operacion y feedback visual en el punto de entrada.
- Criterios de Aceptacion:
  - [x] Cabecera de sidebar con identidad corporativa premium.
  - [x] Tarjeta de bienvenida principal actualizada a 2 archivos.
  - [x] Mensajeria clara de derivacion a TAB `Clientes Premium`.

### FEATURE-003: Modo Multi-Tenant
- Estado: Pendiente

---

## 5. Roadmap de Ejecucion

### Fase A (Cierre migracion funcional)
1. SUPABASE-MIG-001
2. SUPABASE-MIG-002
3. SUPABASE-MIG-003
4. SUPABASE-MIG-004

### Fase B (Operacion premium)
1. SUPABASE-MIG-005
2. SUPABASE-MIG-006
3. SUPABASE-MIG-007

### Fase C (Gobierno y seguridad)
1. SUPABASE-MIG-008
2. SUPABASE-MIG-009

---

## 6. Definicion de Cierre de Migracion

La migracion se considera cerrada cuando:

1. El flujo de 2 Excel opera desde UI sin regresiones.
2. El Excel de salida conserva funcionalidad y campos.
3. Notificaciones se registran por cliente en Supabase.
4. Existen reportes operativos por cliente.
5. Gates de calidad pasan en E2E.
6. Backups y restore operativos validados.

---

## 7. Sprint TIER 2 — CRM WhatsApp Avanzado (Pendiente v1.8.x / v1.9.x)

### CRM-010: Panel WA de Prueba en Tab Configuración (RC-FEAT-026)
- Estado: Done ✅ — commit `d8a342a` (2026-03-16)
- Esfuerzo: 1 punto (~1 hora)
- Prioridad: P1
- Dependencias: Smoke Test TIER 2 en staging
- Descripción: Panel en Tab Configuración para enviar un WA de prueba sin necesitar datos reales. Input de teléfono (default +51921566036), textarea de mensaje, botón "Enviar prueba". Llama a `send_whatsapp_messages_direct()` con contacto ficticio.
- Archivo: `utils/ui/tabs/config_tab.py` — SECCIÓN 8 (entre WA dispositivo y Opciones Avanzadas)
- Criterios de Aceptación:
  - [x] Input teléfono con valor por defecto configurable
  - [x] Textarea para mensaje libre
  - [x] Botón "Enviar WA de prueba"
  - [x] Toast verde en éxito / mensaje claro en error
  - [x] NO requiere ciclo cargado ni df_final activo

---

### CRM-011: Selección Automática de Plantilla por Aging (RC-FEAT-027)
- Estado: Pendiente ⏳
- Esfuerzo: 2 puntos (~2 horas)
- Prioridad: P2
- Dependencias: RC-FEAT-020 (Biblioteca plantillas) — COMPLETADO
- Descripción: Al abrir Tab WhatsApp, el sistema sugiere automáticamente la plantilla correcta por cliente según sus días de mora. El gestor puede sobreescribir antes de enviar.
- Regla de negocio (segmentos):
  - 0–14 días → Primer Aviso
  - 15–30 días → Recordatorio
  - 31–60 días → Aviso Firme
  - 60+ días → Pre-Legal
- Archivo: `utils/ui/tabs/whatsapp.py`
- Criterios de Aceptación:
  - [ ] Columna "Segmento" visible en tabla de selección de clientes
  - [ ] Plantilla pre-seleccionada según segmento al cargar la vista
  - [ ] Gestor puede cambiar plantilla por cliente antes de enviar
  - [ ] Sin envío automático — siempre requiere acción explícita del gestor
  - [ ] Tests unitarios para lógica de segmentación por días

---

### CRM-012: KPIs Expandidos de Efectividad de Cobranza (RC-FEAT-028)
- Estado: Pendiente ⏳
- Esfuerzo: 2 puntos (~2 horas)
- Prioridad: P2
- Dependencias: RC-FEAT-019, RC-FEAT-021, RC-FEAT-023 — todos COMPLETADOS
- Descripción: Panel de métricas cruzadas en Tab WA y Centro de Gestiones. Indicadores de efectividad calculados en tiempo real desde Supabase.
- Métricas:
  - WA enviados hoy / esta semana
  - Con respuesta (EXITOSO + PROMETIO_PAGAR) vs Sin respuesta
  - Acuerdos de pago activos
  - Cuotas venciendo en ≤3 días
  - Monto total gestionado (S/ + $) vs monto con acuerdo formal
- Archivos: `utils/ui/tabs/whatsapp.py`, `utils/ui/tabs/crm_gestiones.py`, `utils/db_manager.py`
- Criterios de Aceptación:
  - [ ] KPIs calculados desde Supabase (gestiones + acuerdos_pago + cuotas_acuerdo)
  - [ ] Sin afectar df_final ni df_filtered (solo lectura Supabase)
  - [ ] Visible en Tab WA y en Centro de Gestiones
  - [ ] Actualización al recargar la sección (no tiempo real)

---

## 7.1. Sprint TIER 2 — Bugs y UX (2026-03-16) ✅ COMPLETADO

### RC-BUG-032: Notas vacías en historial post-rerun
- Estado: Done ✅ — commits `bd9f264` + `4cd9cac`
- Causa raíz: columna `notas` faltaba en SELECT de `get_wa_gestiones_by_cycle` en `db_manager.py`
- Fix 1: persistir nota en `session_state['last_wa_send_results']['details']` antes del `st.rerun()`
- Fix 2 (raíz): agregar `notas` al `.select()` en `db_manager.py`

### RC-BUG-033: Saldo sin moneda en tablas
- Estado: Done ✅ — commits `1f69034` + `da4b6b3`
- Causa: Se usaba `_det.get('Deuda', '')` (número raw sin prefijo de moneda)
- Fix: Usar `DeudaS` + `DeudaD` ya formateados (`S/ X.XX` / `$ X.XX`) con fallback
- Afectado: tabla historial y tabla pendientes en `whatsapp.py`

### RC-FEAT-034: 9 mejoras UX panel Seguimiento Post-Envío WA
- Estado: Done ✅ — commits `cb4c9b6` + `6e65376`
- Archivo: `utils/ui/tabs/whatsapp.py`
- Mejoras implementadas:
  1. Orden por saldo descendente en tabla pendientes (`_parse_saldo_sort()`)
  2. Teléfono como link `wa.me/{número}` con ícono 💬
  3. KPI % efectividad (`_con_gestion / _total_env * 100`) en panel de métricas
  4. Tipo de gestión como ícono (📋 Gestión / 📤 Envío WA) con tooltip
  5. Tooltip notas largas truncadas (`max-width:200px;overflow:hidden;text-overflow:ellipsis`)
  6. Barra de progreso del ciclo (`_pct_ciclo = len(_rows_saved)/total * 100`)
  7. Color semántico del saldo en pendientes (rojo ≥5000, naranja ≥1000, gris <1000)
  8. Badge ↩ Reintentar si resultado = 'Sin respuesta'
  9. Tooltip descriptivo mejorado en botón "Guardar todos"
- Mejora #10 (link historial CRM) → diferida a TIER 3 como RC-FEAT-035

---

## 8. Sprint TIER 3 — Analytics y Cierre de Ciclo (Features futuras v2.x)

> Origen: Propuesta CRM WhatsApp v1.0 (2025). Documento de propuesta ahora obsoleto — estas features
> fueron aprobadas y se documentan aquí como roadmap. Prerequisito: TIER 2 completado.

### CRM-015: Link Historial CRM Completo del Cliente desde Panel WA (RC-FEAT-035)
- Estado: Backlog futuro 📋
- Esfuerzo: 2 puntos (~2 horas)
- Prioridad: P3
- Dependencias: RC-FEAT-019 (Panel post-envío) — COMPLETADO; RC-FEAT-034 (mejoras UX WA) — COMPLETADO
- Descripción: Desde la tabla de historial de gestiones WA, agregar un link/botón por fila que navegue al historial CRM completo del cliente. Requiere deep-link vía `st.session_state` del `cliente_id` hacia Tab CRM Gestiones filtrado por ese cliente.
- Archivo: `utils/ui/tabs/whatsapp.py` (columna nueva en tabla historial), `utils/ui/tabs/crm_gestiones.py` (recibir filtro por cliente_id desde session_state)
- Criterios de Aceptación:
  - [ ] Botón/link "Ver CRM" visible en cada fila del historial de gestiones WA
  - [ ] Clic navega automáticamente a Tab CRM Gestiones
  - [ ] Tab CRM Gestiones pre-filtra por el cliente seleccionado
  - [ ] Filtro se limpia al cambiar de contexto manualmente
  - [ ] Sin afectar SSOT ni df_final

---

### CRM-013: Registro de Pagos en Tiempo Real (RC-FEAT-029)
- Estado: Backlog futuro 📋
- Esfuerzo: 3 puntos (~4 horas)
- Prioridad: P3
- Dependencias: RC-FEAT-021 (Acuerdos de pago) — COMPLETADO
- Descripción: Formulario en CRM para que el gestor registre un pago recibido directamente en la app, sin esperar sincronización del ERP. El registro es provisional hasta que el próximo ciclo Excel lo confirme.
- Campos: cliente, monto, moneda, fecha, forma de pago, banco, referencia, nota
- Efecto:
  - Actualiza `documentos.monto_pendiente` con flag `provisional=true`
  - Marca cuota del acuerdo como `PAGADA` si corresponde
  - Genera WA de agradecimiento (plantilla Felicitación)
  - El próximo ciclo Excel reconcilia y confirma o revierte el registro provisional
- Riesgo documentado: posible desincronización con ERP si el Excel no llega o llega tarde
- Archivos: `utils/ui/tabs/crm_gestiones.py`, `utils/db_manager.py`
- Criterios de Aceptación:
  - [ ] Formulario de registro de pago en pestaña CRM
  - [ ] Flag `provisional` visible en la UI con advertencia
  - [ ] Cuota correspondiente marcada como PAGADA
  - [ ] WA de agradecimiento generado automáticamente
  - [ ] Al cargar siguiente ciclo: reconciliación automática provisional vs. Excel

---

### CRM-014: Dashboard de Efectividad de Cobranza (RC-FEAT-030)
- Estado: Backlog futuro 📋
- Esfuerzo: 5 puntos (~6 horas)
- Prioridad: P3
- Dependencias: RC-FEAT-023 (Trazabilidad) — COMPLETADO; requiere ≥2 ciclos en producción para tener datos suficientes
- Descripción: Nuevo Tab "Analytics" con reportes para el supervisor/dirección sobre efectividad de gestión de cobranza.
- Métricas objetivo:
  - % de WA que resultan en pago (ventanas 7 / 15 / 30 días)
  - Ranking de clientes por dificultad de cobranza
  - Saldo total gestionado (S/ + $) vs saldo recuperado — por ciclo y acumulado
  - Evolución mensual de recuperación
  - Acuerdos cumplidos vs incumplidos
  - Tasa de respuesta por plantilla WA (qué plantilla convierte más)
- Fuente: `resumen_cliente_ciclo`, `resumen_ciclo`, `gestiones`, `acuerdos_pago`, `cuotas_acuerdo`
- Archivo: Nuevo `utils/ui/tabs/analytics.py`
- Criterios de Aceptación:
  - [ ] Nuevo tab "Analytics" visible en la app
  - [ ] Gráficos de evolución mensual
  - [ ] Tabla ranking de clientes por dificultad
  - [ ] KPI: % conversión por plantilla WA
  - [ ] Exportable a Excel/CSV
  - [ ] Sin impacto en flujo operativo principal
