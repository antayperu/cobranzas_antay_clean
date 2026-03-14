-- =====================================================
-- 13_alter_gestiones_add_cycle_id.sql
-- Agrega columna cycle_id a la tabla gestiones
-- Ejecutado manualmente en Supabase PROD (documentado aqui para consistencia del schema)
-- =====================================================

ALTER TABLE gestiones ADD COLUMN IF NOT EXISTS cycle_id TEXT;

CREATE INDEX IF NOT EXISTS idx_gestiones_cycle_id ON gestiones(cycle_id);

COMMENT ON COLUMN gestiones.cycle_id IS 'ID del ciclo de cobranza al que pertenece esta gestion (ej: CIC-20260311-1124)';
