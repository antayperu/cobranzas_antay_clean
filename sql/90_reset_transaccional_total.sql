-- ============================================================================
-- 90_reset_transaccional_total.sql
-- Reinicio TOTAL de tablas operativas para STAGING/QA.
-- Uso recomendado: ambiente de pruebas/certificacion.
-- ============================================================================

BEGIN;

DROP TABLE IF EXISTS public.resumen_ciclo CASCADE;
DROP TABLE IF EXISTS public.resumen_cliente_ciclo CASCADE;
DROP TABLE IF EXISTS public.cuotas_acuerdo CASCADE;
DROP TABLE IF EXISTS public.acuerdos_pago CASCADE;
DROP TABLE IF EXISTS public.documentos_ciclo CASCADE;
DROP TABLE IF EXISTS public.ciclos_procesamiento CASCADE;
DROP TABLE IF EXISTS public.gestiones CASCADE;
DROP TABLE IF EXISTS public.send_attempts CASCADE;
DROP TABLE IF EXISTS public.ledger_last_send CASCADE;
DROP TABLE IF EXISTS public.notificaciones CASCADE;
DROP TABLE IF EXISTS public.cobranzas CASCADE;
DROP TABLE IF EXISTS public.documentos CASCADE;
DROP TABLE IF EXISTS public.clientes CASCADE;
DROP TABLE IF EXISTS public.app_config CASCADE;

COMMIT;

SELECT 'RESET_TOTAL_OK' AS status;
