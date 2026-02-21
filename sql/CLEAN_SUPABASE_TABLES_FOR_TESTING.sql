-- ============================================
-- CLEAN_SUPABASE_TABLES_FOR_TESTING.sql
-- Uso: limpiar datos operativos para pruebas manuales/E2E
-- Fecha: 2026-02-17
-- ============================================
--
-- ADVERTENCIA:
-- - Script destructivo: elimina TODOS los datos de las tablas operativas.
-- - No elimina estructura (tablas, indices, triggers, policies).
--
-- Instrucciones:
-- 1. Supabase -> SQL Editor -> New Query
-- 2. Pegar y ejecutar este script completo
-- 3. Validar que todos los conteos queden en 0

BEGIN;

TRUNCATE TABLE
    public.send_attempts,
    public.ledger_last_send,
    public.cobranzas,
    public.notificaciones,
    public.documentos,
    public.clientes
RESTART IDENTITY
CASCADE;

COMMIT;

-- Verificacion posterior
SELECT 'clientes' AS tabla, COUNT(*) AS total FROM public.clientes
UNION ALL
SELECT 'documentos' AS tabla, COUNT(*) AS total FROM public.documentos
UNION ALL
SELECT 'cobranzas' AS tabla, COUNT(*) AS total FROM public.cobranzas
UNION ALL
SELECT 'notificaciones' AS tabla, COUNT(*) AS total FROM public.notificaciones
UNION ALL
SELECT 'ledger_last_send' AS tabla, COUNT(*) AS total FROM public.ledger_last_send
UNION ALL
SELECT 'send_attempts' AS tabla, COUNT(*) AS total FROM public.send_attempts
ORDER BY tabla;
