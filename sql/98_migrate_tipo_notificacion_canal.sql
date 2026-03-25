-- =============================================================================
-- MIGRACIÓN: tipo_notificacion → estandarizar por CANAL (RC-FIX-tipo_notif)
-- =============================================================================
-- Propósito : El campo tipo_notificacion almacenaba el nivel de prioridad
--             (INFO / ALERTA / GESTION_FALLIDA) en vez del CANAL de envío
--             (EMAIL / WHATSAPP). Este script corrige los datos históricos.
--
-- Regla de negocio:
--   - Toda notificación del canal email → tipo_notificacion = 'EMAIL'
--   - Toda notificación del canal WA    → tipo_notificacion = 'WHATSAPP'
--     (Las WA ya usaban el valor correcto — incluido por completitud)
--
-- Uso : Ejecutar en Supabase SQL Editor (staging primero, luego producción).
--       REVISAR los COUNT antes de ejecutar los UPDATE.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- PASO 1 — Diagnóstico previo (ejecutar primero para entender el volumen)
-- ---------------------------------------------------------------------------

SELECT
    tipo_notificacion,
    COUNT(*) AS total,
    MIN(created_at) AS primera,
    MAX(created_at) AS ultima
FROM notificaciones
GROUP BY tipo_notificacion
ORDER BY total DESC;


-- ---------------------------------------------------------------------------
-- PASO 2 — Vista previa de las filas afectadas
-- ---------------------------------------------------------------------------

-- Notificaciones que tenían INFO o ALERTA y tienen canal EMAIL en metadata
SELECT
    id,
    tipo_notificacion,
    estado,
    cliente_id,
    created_at,
    metadata->>'channel' AS canal_metadata
FROM notificaciones
WHERE tipo_notificacion IN ('INFO', 'ALERTA', 'GESTION_FALLIDA')
  AND (metadata->>'channel' = 'EMAIL' OR metadata IS NULL)
ORDER BY created_at DESC
LIMIT 20;


-- ---------------------------------------------------------------------------
-- PASO 3A — Actualizar el CHECK CONSTRAINT para aceptar los valores nuevos
-- (obligatorio antes del UPDATE — el constraint actual solo acepta INFO/ALERTA/GESTION_FALLIDA)
-- ---------------------------------------------------------------------------

-- ⚠️  EJECUTAR ESTE BLOQUE PRIMERO
ALTER TABLE notificaciones
    DROP CONSTRAINT IF EXISTS notificaciones_tipo_notificacion_check;

ALTER TABLE notificaciones
    ADD CONSTRAINT notificaciones_tipo_notificacion_check
    CHECK (tipo_notificacion IN ('EMAIL', 'WHATSAPP', 'SMS', 'INFO', 'ALERTA', 'GESTION_FALLIDA'));
-- Los valores viejos quedan en el CHECK durante la transición.
-- Una vez migrados todos los datos, se puede volver a ajustar si se desea.


-- ---------------------------------------------------------------------------
-- PASO 3B — UPDATE: INFO / ALERTA / GESTION_FALLIDA → EMAIL
-- (solo cuando el canal en metadata es EMAIL o no hay metadata)
-- ---------------------------------------------------------------------------

-- ⚠️  EJECUTAR DESPUÉS DEL PASO 3A
UPDATE notificaciones
SET tipo_notificacion = 'EMAIL'
WHERE tipo_notificacion IN ('INFO', 'ALERTA', 'GESTION_FALLIDA')
  AND (
      metadata->>'channel' = 'EMAIL'
      OR metadata IS NULL
      OR NOT (metadata ? 'channel')
  );

-- Resultado esperado: X filas actualizadas (el número del COUNT en PASO 1)


-- ---------------------------------------------------------------------------
-- PASO 3C — (Opcional) Ajustar el CHECK CONSTRAINT a solo valores modernos
-- Ejecutar solo si ya no quedan filas con INFO/ALERTA/GESTION_FALLIDA
-- ---------------------------------------------------------------------------

-- Verificar primero que no queden valores viejos:
-- SELECT COUNT(*) FROM notificaciones WHERE tipo_notificacion IN ('INFO','ALERTA','GESTION_FALLIDA');

-- Si el resultado es 0, puedes limpiar el constraint:
-- ALTER TABLE notificaciones DROP CONSTRAINT IF EXISTS notificaciones_tipo_notificacion_check;
-- ALTER TABLE notificaciones ADD CONSTRAINT notificaciones_tipo_notificacion_check
--     CHECK (tipo_notificacion IN ('EMAIL', 'WHATSAPP', 'SMS'));


-- ---------------------------------------------------------------------------
-- PASO 4 — Verificación post-migración
-- ---------------------------------------------------------------------------

SELECT
    tipo_notificacion,
    COUNT(*) AS total
FROM notificaciones
GROUP BY tipo_notificacion
ORDER BY total DESC;

-- Resultado esperado:
--   EMAIL     → N filas (todas las email)
--   WHATSAPP  → N filas (WA ya tenían el valor correcto)
--   (no debe aparecer INFO, ALERTA ni GESTION_FALLIDA)


-- ---------------------------------------------------------------------------
-- PASO 5 — Validación de integridad Dashboard (reconciliación rápida)
-- ---------------------------------------------------------------------------

-- Verificar que el Dashboard ahora cuenta emails correctamente
SELECT
    tipo_notificacion,
    estado,
    COUNT(*) AS cantidad
FROM notificaciones
GROUP BY tipo_notificacion, estado
ORDER BY tipo_notificacion, estado;
