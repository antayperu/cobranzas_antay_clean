-- =============================================================================
-- MIGRACIÓN 104: resumen_ciclo — columnas de amortizaciones parciales
-- =============================================================================
-- Ticket    : RC-BUG-070
-- Propósito : Registrar por separado los documentos que redujeron su saldo
--             entre ciclos (pago parcial = amortización) vs. los que
--             desaparecieron completamente (recuperación total).
--
-- Impacto en monto_recuperado_sol/_usd:
--   Esos campos pasan a ser COMBINADOS:
--       monto_recuperado_sol = full_recovery_sol + amortizados_sol
--   No se crean columnas nuevas para el total — se reutilizan las existentes.
--
-- Las columnas monto_amortizado_* sirven para auditoría/validación (queries
-- ⑬ y ⑭ del archivo 100_informe_gerencial_reconciliation.sql).
--
-- Ejecutar UNA SOLA VEZ en staging, verificar, luego producción.
-- Es seguro re-ejecutar: usa ADD COLUMN IF NOT EXISTS.
-- =============================================================================

ALTER TABLE resumen_ciclo
    ADD COLUMN IF NOT EXISTS docs_amortizados             INTEGER        DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_amortizado_sol         NUMERIC(14,2)  DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_amortizado_usd         NUMERIC(14,2)  DEFAULT 0,
    ADD COLUMN IF NOT EXISTS docs_amortizados_activa      INTEGER        DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_amortizado_sol_activa  NUMERIC(14,2)  DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_amortizado_usd_activa  NUMERIC(14,2)  DEFAULT 0;

-- Verificar columnas agregadas:
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'resumen_ciclo'
  AND column_name LIKE '%amortiz%'
ORDER BY column_name;
