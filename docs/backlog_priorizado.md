# Backlog Priorizado - ReporteCobranzas Antay

Ultima actualizacion: 2026-03-14
Version actual: v1.7.2 (post-TIER1 hotfixes + staging)
Estado migracion Supabase: Completada. Todas las fases MIG-000 a MIG-009 + SUPABASE-002 + CONFIG-001 cerradas.
Iniciativa CRM WhatsApp: TIER 1 completado 2026-03-13 (141/141 tests). Ambiente staging configurado. TIER 2 pendiente.

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

### Pendiente — TIER 2 (Próximo Sprint)
- RC-FEAT-026: Panel de envío WA de prueba en Tab Configuración (smoke test sin datos reales)
  - Smoke test completo del panel post-envío (RC-FEAT-019) en staging
  - Testing de acuerdos de pago (RC-FEAT-021) en staging

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
