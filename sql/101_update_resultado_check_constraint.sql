-- =============================================================================
-- MIGRACIÓN: Actualizar CHECK constraint de columna `resultado` en gestiones
-- Ticket: RC-BUG-057
-- =============================================================================
-- Problema:
--   La tabla gestiones tiene un CHECK constraint antiguo que solo permite:
--   'EXITOSO', 'FALLIDO', 'PENDIENTE', 'SIN_RESPUESTA', 'REPROGRAMADO'
--
--   Los nuevos códigos de resultado ('PROMESA_PAGO', 'SOLICITO_PLAZO',
--   'EN_NEGOCIACION', 'ESCALAR_LEGAL', 'DISPUTA') son rechazados por Supabase
--   con error de violación de constraint, causando "No se pudo guardar".
--
-- Solución:
--   Eliminar el constraint antiguo y crear uno nuevo con todos los valores válidos.
--
-- Uso: Ejecutar en Supabase SQL Editor (staging primero, luego producción).
-- =============================================================================


-- ---------------------------------------------------------------------------
-- PASO 0 — Diagnóstico: ver el constraint actual
-- ---------------------------------------------------------------------------
SELECT
    conname   AS constraint_name,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'gestiones'::regclass
  AND contype  = 'c';
-- Buscar la línea con "resultado IN (...)" — ese es el que vamos a reemplazar.


-- ---------------------------------------------------------------------------
-- PASO 1 — Eliminar el constraint antiguo
-- ---------------------------------------------------------------------------

-- ⚠️ PRIMERO: identificar el nombre exacto del constraint en el resultado del PASO 0
-- Normalmente se llama "gestiones_resultado_check" — ajustar si es diferente.
ALTER TABLE gestiones
DROP CONSTRAINT IF EXISTS gestiones_resultado_check;


-- ---------------------------------------------------------------------------
-- PASO 2 — Crear el nuevo constraint con todos los valores válidos
-- ---------------------------------------------------------------------------

ALTER TABLE gestiones
ADD CONSTRAINT gestiones_resultado_check
CHECK (resultado IN (
    -- Valores actuales (estándar 2026)
    'EXITOSO',          -- Acordó pagar — compromiso firme
    'PROMESA_PAGO',     -- Prometió pagar — promesa verbal, requiere seguimiento
    'SOLICITO_PLAZO',   -- Solicitó más plazo
    'EN_NEGOCIACION',   -- En negociación — conversación activa
    'SIN_RESPUESTA',    -- Sin respuesta — no contestó
    'ESCALAR_LEGAL',    -- Derivar a Legal
    'DISPUTA',          -- Disputó la deuda
    -- Valores legado (historial antiguo, NO usar en inserciones nuevas)
    'FALLIDO',
    'PENDIENTE',
    'REPROGRAMADO'
));


-- ---------------------------------------------------------------------------
-- PASO 3 — Verificación
-- ---------------------------------------------------------------------------

-- Ver el nuevo constraint:
SELECT
    conname   AS constraint_name,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'gestiones'::regclass
  AND contype  = 'c'
  AND conname  = 'gestiones_resultado_check';

-- Prueba: insertar un registro de prueba con PROMESA_PAGO (luego se puede borrar)
-- INSERT INTO gestiones (cliente_id, tipo_gestion, canal, resultado, notas, tipo_registro)
-- VALUES ('TEST', 'LLAMADA', 'LLAMADA', 'PROMESA_PAGO', 'Prueba constraint', 'GESTION');
-- Si no da error → el constraint está correcto.
-- Borrar el registro de prueba:
-- DELETE FROM gestiones WHERE cliente_id = 'TEST' AND notas = 'Prueba constraint';
