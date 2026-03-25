-- =============================================================================
-- MIGRATION: resumen_ciclo — columnas dual moneda para recuperacion real
-- RC-FIX-062
-- =============================================================================
-- Ejecutar en Supabase SQL Editor (staging primero, luego produccion).
-- Es idempotente: IF NOT EXISTS evita errores si ya existen las columnas.
-- =============================================================================

ALTER TABLE resumen_ciclo
  ADD COLUMN IF NOT EXISTS monto_recuperado_sol  NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS monto_recuperado_usd  NUMERIC(14,2) DEFAULT 0;

-- Backfill: para ciclos existentes, asignar todo el monto_recuperado a soles
-- (no hay forma de saber la division de moneda de ciclos anteriores).
UPDATE resumen_ciclo
   SET monto_recuperado_sol = COALESCE(monto_recuperado, 0),
       monto_recuperado_usd = 0
 WHERE monto_recuperado_sol IS NULL
    OR (monto_recuperado_sol = 0 AND monto_recuperado_usd = 0 AND monto_recuperado > 0);

-- Verificar resultado:
-- SELECT cycle_id, monto_recuperado, monto_recuperado_sol, monto_recuperado_usd
-- FROM resumen_ciclo ORDER BY cycle_id DESC LIMIT 10;
