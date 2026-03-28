-- =============================================================================
-- MIGRACIÓN: Columna tipo_registro en gestiones (RC-FEAT-040)
-- =============================================================================
-- Propósito : Distinguir formalmente entre registros automáticos del sistema
--             (envíos WA masivos) y gestiones manuales del gestor.
--
-- Problema previo:
--   La tabla `gestiones` mezclaba dos tipos de registros distintos:
--   - Envíos automáticos (wa_envio_masivo): creados por el sistema al enviar
--   - Gestiones manuales: creadas por el gestor al registrar un resultado
--   El código los distinguía leyendo metadata->>'origen' — un artificio.
--
-- Solución:
--   Columna tipo_registro con dos valores explícitos:
--   - 'ENVIO'   → registro automático del sistema (WA masivo enviado)
--   - 'GESTION' → acción manual del gestor (seguimiento, notas, llamadas)
--
-- Uso: Ejecutar en Supabase SQL Editor (staging primero, luego producción).
--      Ejecutar los pasos en orden: diagnóstico → DDL → backfill → constraint.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- PASO 0 — Diagnóstico previo
-- ---------------------------------------------------------------------------

-- ¿Qué registros hay en gestiones?
SELECT
    metadata->>'origen'   AS origen,
    metadata->>'source'   AS source,
    tipo_gestion,
    COUNT(*)              AS total
FROM gestiones
GROUP BY origen, source, tipo_gestion
ORDER BY total DESC;
-- Resultado esperado:
--   origen='wa_envio_masivo' → son ENVIOS (automáticos)
--   source='seguimiento_post_envio' → son GESTIONES (manuales)
--   Sin metadata / otros → son GESTIONES (manuales)


-- ---------------------------------------------------------------------------
-- PASO 1 — Agregar columna (nullable primero, sin romper datos existentes)
-- ---------------------------------------------------------------------------

-- ⚠️ EJECUTAR ESTE BLOQUE PRIMERO
ALTER TABLE gestiones
ADD COLUMN IF NOT EXISTS tipo_registro TEXT
CHECK (tipo_registro IN ('ENVIO', 'GESTION'));

-- Verificar que la columna se agregó:
-- SELECT column_name, data_type, is_nullable FROM information_schema.columns
-- WHERE table_name = 'gestiones' AND column_name = 'tipo_registro';


-- ---------------------------------------------------------------------------
-- PASO 2A — Backfill: marcar envíos automáticos
-- ---------------------------------------------------------------------------

-- ⚠️ EJECUTAR DESPUÉS DEL PASO 1
UPDATE gestiones
SET tipo_registro = 'ENVIO'
WHERE (metadata->>'origen' = 'wa_envio_masivo'
   OR  metadata->>'source'  = 'wa_envio_masivo')
  AND tipo_registro IS NULL;

-- Ver cuántas filas se marcaron como ENVIO:
-- SELECT COUNT(*) FROM gestiones WHERE tipo_registro = 'ENVIO';


-- ---------------------------------------------------------------------------
-- PASO 2B — Backfill: marcar gestiones manuales (todo lo que no es ENVIO)
-- ---------------------------------------------------------------------------

UPDATE gestiones
SET tipo_registro = 'GESTION'
WHERE tipo_registro IS NULL;

-- Ver distribución final:
SELECT tipo_registro, COUNT(*) AS total
FROM gestiones
GROUP BY tipo_registro;
-- Resultado esperado:
--   ENVIO   → N (todos los wa_envio_masivo)
--   GESTION → N (todos los seguimientos manuales y gestiones CRM)


-- ---------------------------------------------------------------------------
-- PASO 3 — Hacer la columna NOT NULL con default 'GESTION'
-- (ejecutar solo si PASO 2A y 2B dejaron 0 filas con NULL)
-- ---------------------------------------------------------------------------

-- Verificar primero que no quedan NULLs:
-- SELECT COUNT(*) FROM gestiones WHERE tipo_registro IS NULL;

-- Si el resultado es 0, proceder:
ALTER TABLE gestiones
ALTER COLUMN tipo_registro SET NOT NULL,
ALTER COLUMN tipo_registro SET DEFAULT 'GESTION';

-- Resultado: el default 'GESTION' protege contra futuros INSERT sin tipo_registro


-- ---------------------------------------------------------------------------
-- PASO 4 — Verificación post-migración
-- ---------------------------------------------------------------------------

SELECT
    tipo_registro,
    tipo_gestion,
    COUNT(*) AS total
FROM gestiones
GROUP BY tipo_registro, tipo_gestion
ORDER BY tipo_registro, tipo_gestion;

-- Resultado esperado:
--   ENVIO   / WHATSAPP → N (mensajes WA masivo enviados)
--   GESTION / WHATSAPP → N (seguimientos manuales post-envío WA)
--   GESTION / LLAMADA  → N (si existen)
--   GESTION / VISITA   → N (si existen)
--   GESTION / NOTA     → N (si existen)


-- ---------------------------------------------------------------------------
-- PASO 5 — Queries de reconciliación con el Dashboard (post-migración)
-- ---------------------------------------------------------------------------

-- "WA enviados" en el Dashboard (KPIs del Período)
SELECT COUNT(*) AS wa_enviados
FROM gestiones
WHERE tipo_gestion    = 'WHATSAPP'
  AND tipo_registro   = 'ENVIO'
  AND fecha >= '2026-03-10T00:00:00-05:00'
  AND fecha <= '2026-03-17T23:59:59-05:00';

-- "Gestiones totales" en el Dashboard
SELECT COUNT(*) AS gestiones_total
FROM gestiones
WHERE tipo_registro = 'GESTION'
  AND fecha >= '2026-03-10T00:00:00-05:00'
  AND fecha <= '2026-03-17T23:59:59-05:00';

-- "Acordaron pagar" en el Dashboard
SELECT COUNT(*) AS acordaron_pagar
FROM gestiones
WHERE resultado     = 'EXITOSO'
  AND tipo_registro = 'GESTION'
  AND fecha >= '2026-03-10T00:00:00-05:00'
  AND fecha <= '2026-03-17T23:59:59-05:00';

-- "Tasa de éxito" en el Dashboard
SELECT
    COUNT(*) FILTER (WHERE resultado = 'EXITOSO') AS exitosos,
    COUNT(*) AS total_gestiones,
    ROUND(
        COUNT(*) FILTER (WHERE resultado = 'EXITOSO') * 100.0
        / NULLIF(COUNT(*), 0), 1
    ) AS tasa_exito_pct
FROM gestiones
WHERE tipo_registro = 'GESTION'
  AND fecha >= '2026-03-10T00:00:00-05:00'
  AND fecha <= '2026-03-17T23:59:59-05:00';
