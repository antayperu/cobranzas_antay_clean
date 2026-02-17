# Backlog Priorizado - ReporteCobranzas Antay

Ultima actualizacion: 2026-02-17  
Version actual: v1.5.6  
Estado migracion Supabase: Base de datos + bootstrap + integracion runtime + paridad de export + notificaciones por cliente + integridad/no-match + mantenimiento de clientes + reporte premium + quality gates + seguridad operacional + backup/restore completados. Iniciativa de Storage (SUPABASE-002) completada.

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
- Estado: Pendiente
- Dependencias: SUPABASE-MIG-001

### FEATURE-001: Dashboard de Analytics
- Estado: Pendiente

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

1. El flujo de 3 Excel opera desde UI sin regresiones.
2. El Excel de salida conserva funcionalidad y campos.
3. Notificaciones se registran por cliente en Supabase.
4. Existen reportes operativos por cliente.
5. Gates de calidad pasan en E2E.
6. Backups y restore operativos validados.
