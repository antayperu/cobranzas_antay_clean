# Texto Listo para Notion (FRD Update)

Fecha de actualizacion sugerida: 2026-02-15

---

## Bloque 1: Estado de Implementacion (pegar en seccion 14)

### 14.x Estado real de migracion a Supabase

- Esquema Supabase operativo con 6 tablas:
  - `clientes`
  - `documentos`
  - `cobranzas`
  - `notificaciones`
  - `ledger_last_send`
  - `send_attempts`
- Migracion desde 3 Excel implementada y validada:
  - `clientes`: 199
  - `documentos`: 231
  - `cobranzas`: 165
- Regla de integridad aplicada:
  - No se insertan cobranzas huerfanas (sin documento asociado).
- Script operativo:
  - `scripts/migrate_excel_to_supabase.py`
- Comandos:
  - `python scripts/migrate_excel_to_supabase.py`
  - `python scripts/migrate_excel_to_supabase.py --apply`

---

## Bloque 2: Regla de Integridad (pegar en seccion 13.2 o 13.3)

### Regla de carga de cobranzas (obligatoria)

Solo se inserta en `cobranzas` una fila que tenga match con `documentos` por clave documental.

Justificacion:
- Evitar registros huerfanos.
- Proteger consistencia de reportes y KPIs.
- Mantener integridad referencial para trazabilidad premium.

---

## Bloque 3: Plan de cierre (pegar en seccion 13.5/13.6)

### Plan de cierre de migracion (pendiente)

1. Integrar runtime app para leer/escribir en Supabase en modo cloud.
2. Mantener misma UI de carga de 3 Excel (sin cambios para usuario).
3. Mantener paridad del Excel de salida (mismos campos y calculos).
4. Persistir notificaciones de correo por `cliente_id` en tabla `notificaciones`.
5. Exponer reporte por cliente desde Supabase en UI.
6. Definir y validar RLS/politicas de seguridad.
7. Definir politica cloud-only (sin fallback local) con bloqueo controlado.
8. Ejecutar Quality Gates E2E (datos, UX, seguridad, no-regresion).

---

## Bloque 4: Criterios de aceptacion (pegar en seccion 13.6)

### Criterios de aceptacion de migracion completa

- CA-MIG-1: Flujo de 3 Excel persiste en Supabase sin romper logica funcional.
- CA-MIG-2: UI de carga se mantiene igual para usuario final.
- CA-MIG-3: Excel de salida mantiene campos, orden y calculos.
- CA-MIG-4: `clientes/documentos/cobranzas` se actualizan por ciclo con upsert idempotente.
- CA-MIG-5: No existen cobranzas huerfanas.
- CA-MIG-6: Cada envio de correo se registra en `notificaciones` con `cliente_id`.
- CA-MIG-7: Reporte de notificaciones por cliente disponible en UI.
- CA-MIG-8: Politica cloud-only validada (sin fallback local).
- CA-MIG-9: En caida de Supabase, bloqueo controlado + mensaje operativo + observabilidad.

---

## Bloque 5: Operacion diaria (pegar en anexo operativo)

### Runbook rapido

1. Cargar 3 Excel.
2. Ejecutar dry-run.
3. Revisar resumen de validos/errores.
4. Ejecutar apply.
5. Validar conteos en Supabase.

SQL:

```sql
select count(*) as clientes from clientes;
select count(*) as documentos from documentos;
select count(*) as cobranzas from cobranzas;
select count(*) as notificaciones from notificaciones;
```
