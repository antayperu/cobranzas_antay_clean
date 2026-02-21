# Evidencia Seguridad Operacional - SUPABASE-MIG-008

Fecha: 2026-02-17  
Ticket: SUPABASE-MIG-008  
Objetivo: definir RLS/politicas, revisar llaves por entorno y documentar checklist.

---

## 1) Politicas RLS definidas

Archivo:

- `sql/06_enable_rls_policies.sql`

Incluye:

1. `ENABLE ROW LEVEL SECURITY` para:
   - `clientes`
   - `documentos`
   - `cobranzas`
   - `notificaciones`
   - `ledger_last_send`
   - `send_attempts`
2. Politicas `FOR ALL TO service_role` por tabla.
3. Query de verificacion `pg_tables` (rowssecurity).

---

## 2) Uso de llaves por entorno revisado

Actualizado:

- `.env.example`

Lineamientos:

1. Arquitectura cloud-only (Supabase obligatorio).
2. `SUPABASE_SERVICE_ROLE_KEY` solo backend trusted.
3. `anon key` solo frontend (si aplica), nunca para procesos batch.

---

## 3) Checklist documentado

Documento:

- `docs/CHECKLIST_SEGURIDAD_SUPABASE_MIG008.md`

Incluye:

1. Matriz de llaves por entorno (dev/stg/prod).
2. Verificaciones SQL de RLS y politicas.
3. Reglas operativas de manejo seguro de secretos.

---

## 4) Integracion en runbook

Actualizado:

- `docs/PLAN_MIGRACION_SUPABASE_PREMIUM_v1.0.md` (seccion 12.3)
- `sql/00_setup_all.sql` (incluye paso 7)
- `sql/EJECUTAR_EN_SUPABASE.sql` (seccion RLS + politicas)
- `scripts/setup_supabase_tables.py` y `scripts/setup_tables_postgres.py` (incluyen `sql/06_enable_rls_policies.sql`)

---

Estado del ticket: `COMPLETADO`.
