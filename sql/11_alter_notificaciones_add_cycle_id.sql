-- RC-OPS-004: Agregar cycle_id a tabla notificaciones
-- Permite vincular cada notificacion con su ciclo de procesamiento origen
-- y reconciliar el tracking al restaurar un ciclo.
--
-- EJECUTAR EN SUPABASE SQL EDITOR:

ALTER TABLE notificaciones
ADD COLUMN IF NOT EXISTS cycle_id TEXT DEFAULT NULL;

-- Indice para consultas de reconciliacion (WHERE cycle_id = X)
CREATE INDEX IF NOT EXISTS idx_notificaciones_cycle_id
ON notificaciones (cycle_id);

-- Indice compuesto para consultas por ciclo + cliente
CREATE INDEX IF NOT EXISTS idx_notificaciones_cycle_cliente
ON notificaciones (cycle_id, cliente_id);
