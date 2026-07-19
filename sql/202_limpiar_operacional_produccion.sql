-- ============================================================
-- 202_limpiar_operacional_produccion.sql
-- Limpieza SEGURA de tablas transaccionales para producción.
--
-- QUÉ LIMPIA:  Todo lo operativo (ciclos, documentos, notificaciones,
--              gestiones, ledger, resúmenes, acuerdos).
-- QUÉ CONSERVA: clientes, app_config, catalogo_resultados
--               (configuración y maestros — NO son datos operativos).
--
-- USO:
--   Supabase Dashboard → SQL Editor → New Query → pegar y ejecutar.
--
-- PROPÓSITO:
--   Arrancar limpio desde el 01-Abr-2026.
--   Los ciclos históricos se recargan luego como HIST_* vía
--   migrate_historical.py.
--
-- ADVERTENCIA: OPERACIÓN IRREVERSIBLE sobre producción.
--   Tomar screenshot del conteo de tablas antes de ejecutar.
-- ============================================================

BEGIN;

-- Orden respetando FK: primero hijos, luego padres
TRUNCATE TABLE
    public.resumen_cliente_ciclo,
    public.resumen_ciclo,
    public.cuotas_acuerdo,
    public.acuerdos_pago,
    public.documentos_ciclo,
    public.ciclos_procesamiento,
    public.gestiones,
    public.notificaciones,
    public.ledger_last_send,
    public.send_attempts
RESTART IDENTITY CASCADE;

COMMIT;

-- ============================================================
-- Verificación posterior (todos deben quedar en 0)
-- ============================================================
SELECT 'ciclos_procesamiento'  AS tabla, COUNT(*) AS total FROM public.ciclos_procesamiento
UNION ALL
SELECT 'documentos_ciclo'      AS tabla, COUNT(*) AS total FROM public.documentos_ciclo
UNION ALL
SELECT 'notificaciones'        AS tabla, COUNT(*) AS total FROM public.notificaciones
UNION ALL
SELECT 'gestiones'             AS tabla, COUNT(*) AS total FROM public.gestiones
UNION ALL
SELECT 'ledger_last_send'      AS tabla, COUNT(*) AS total FROM public.ledger_last_send
UNION ALL
SELECT 'send_attempts'         AS tabla, COUNT(*) AS total FROM public.send_attempts
UNION ALL
SELECT 'acuerdos_pago'         AS tabla, COUNT(*) AS total FROM public.acuerdos_pago
UNION ALL
SELECT 'cuotas_acuerdo'        AS tabla, COUNT(*) AS total FROM public.cuotas_acuerdo
UNION ALL
SELECT 'resumen_ciclo'         AS tabla, COUNT(*) AS total FROM public.resumen_ciclo
UNION ALL
SELECT 'resumen_cliente_ciclo' AS tabla, COUNT(*) AS total FROM public.resumen_cliente_ciclo
UNION ALL
-- Estas deben conservar sus datos:
SELECT '--- clientes (NO tocar) ---' AS tabla, COUNT(*) AS total FROM public.clientes
UNION ALL
SELECT '--- app_config (NO tocar) ---' AS tabla, COUNT(*) AS total FROM public.app_config
UNION ALL
SELECT '--- catalogo_resultados (NO tocar) ---' AS tabla, COUNT(*) AS total FROM public.catalogo_resultados
ORDER BY tabla;
