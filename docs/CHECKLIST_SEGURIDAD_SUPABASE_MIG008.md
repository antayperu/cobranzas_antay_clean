# Checklist Seguridad Supabase - SUPABASE-MIG-008

Fecha: 2026-02-17  
Objetivo: validar RLS, politicas y uso de llaves por entorno.

---

## 1) Matriz de llaves por entorno

1. Desarrollo (backend local):
   - `SUPABASE_URL`: requerido
   - `SUPABASE_SERVICE_ROLE_KEY`: permitido en `.env` local no versionado
2. Staging:
   - `SUPABASE_SERVICE_ROLE_KEY`: en secretos del entorno (CI/CD/hosting), nunca en repositorio
3. Produccion:
   - `SUPABASE_SERVICE_ROLE_KEY`: solo backend trusted
   - `ANON KEY`: solo frontend/clientes (si aplica), nunca procesos batch

---

## 2) RLS y politicas

1. Script aplicado:
   - `sql/06_enable_rls_policies.sql`
2. Confirmar que RLS esta activo:

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
      'clientes', 'documentos', 'cobranzas', 'notificaciones', 'ledger_last_send', 'send_attempts'
  )
ORDER BY tablename;
```

3. Confirmar politicas service_role:

```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
      'clientes', 'documentos', 'cobranzas', 'notificaciones', 'ledger_last_send', 'send_attempts'
  )
ORDER BY tablename, policyname;
```

---

## 3) Operacion segura

1. `SUPABASE_SERVICE_ROLE_KEY` no aparece en:
   - repositorio
   - logs
   - frontend
2. `.env` esta en `.gitignore` y validado en PR.
3. Rotacion de llave service role documentada en incidente/seguridad.

---

## 4) Gate de cierre

1. RLS activo en 6 tablas operativas.
2. Politicas service_role creadas en 6 tablas.
3. Matriz de llaves revisada y comunicada al equipo.

Estado esperado: `PASS`.
