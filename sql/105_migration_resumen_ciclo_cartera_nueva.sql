-- =============================================================================
-- MIGRATION 105 — resumen_ciclo: Roll Forward "Movimiento de Cartera"
-- RC-FEAT-042
-- =============================================================================
-- Agrega columnas para calcular y mostrar el Roll Forward completo en el
-- Informe Gerencial:
--
--   Saldo anterior  +  Cartera nueva  −  Recuperado  =  Cartera actual
--
-- Esto permite al Directorio verificar el cuadre matemático de la cartera
-- sin discrepancias con la base de datos operativa.
--
-- Ejecutar en: Supabase producción y staging.
-- Idempotente: usa IF NOT EXISTS en cada columna.
-- =============================================================================

ALTER TABLE resumen_ciclo
  -- Saldo directo del ciclo anterior (suma saldo_real, excluyendo DSP/PAV)
  ADD COLUMN IF NOT EXISTS saldo_anterior_sol        NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS saldo_anterior_usd        NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS saldo_anterior_sol_activa NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS saldo_anterior_usd_activa NUMERIC(14,2) DEFAULT 0,

  -- Cartera nueva: docs en el ciclo actual que NO estaban en el anterior
  ADD COLUMN IF NOT EXISTS cartera_nueva_sol         NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS cartera_nueva_usd         NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS cartera_nueva_sol_activa  NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS cartera_nueva_usd_activa  NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS docs_nuevos               INT           DEFAULT 0,
  ADD COLUMN IF NOT EXISTS docs_nuevos_activa        INT           DEFAULT 0,

  -- Saldo directo del ciclo actual (suma saldo_real, excluyendo DSP/PAV)
  ADD COLUMN IF NOT EXISTS saldo_actual_sol          NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS saldo_actual_usd          NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS saldo_actual_sol_activa   NUMERIC(14,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS saldo_actual_usd_activa   NUMERIC(14,2) DEFAULT 0;

-- Verificación post-migration
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'resumen_ciclo'
  AND column_name IN (
    'saldo_anterior_sol', 'saldo_anterior_usd',
    'cartera_nueva_sol',  'cartera_nueva_usd',
    'docs_nuevos',
    'saldo_actual_sol',   'saldo_actual_usd'
  )
ORDER BY column_name;
