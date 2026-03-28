-- =============================================================================
-- MIGRACIÓN 102: resumen_ciclo — columnas de recuperación Cartera Activa
-- =============================================================================
-- Ticket  : RC-BUG-069
-- Propósito: Agregar columnas para almacenar la recuperación calculada
--            exclusivamente sobre clientes con enviar_email = 'SI'
--            (Cartera Activa), separada de la Cartera General.
--
-- Ejecutar UNA SOLA VEZ en Supabase (staging y producción).
-- Es seguro re-ejecutar: usa IF NOT EXISTS.
-- =============================================================================

ALTER TABLE resumen_ciclo
    ADD COLUMN IF NOT EXISTS monto_recuperado_sol_activa NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_recuperado_usd_activa NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS docs_recuperados_activa     INTEGER       DEFAULT 0,
    ADD COLUMN IF NOT EXISTS tasa_recuperacion_activa    NUMERIC(6,2)  DEFAULT 0;

-- Verificar columnas agregadas
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'resumen_ciclo'
  AND column_name LIKE '%activa%'
ORDER BY column_name;
