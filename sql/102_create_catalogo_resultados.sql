-- =============================================================================
-- MIGRACIÓN: Tabla catalogo_resultados (RC-FEAT-041)
-- =============================================================================
-- Propósito:
--   Centralizar en base de datos los valores válidos de resultado de gestión.
--   Elimina hardcodes dispersos en Python y hace el catálogo configurable
--   sin necesidad de hacer deploy (publicar nueva versión de la app).
--
-- Uso: Ejecutar en Supabase SQL Editor (staging primero, luego producción).
-- =============================================================================


-- ---------------------------------------------------------------------------
-- PASO 1 — Crear la tabla
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS catalogo_resultados (
    codigo          TEXT PRIMARY KEY,
    etiqueta        TEXT NOT NULL,
    icono           TEXT NOT NULL DEFAULT '',
    color_scheme    TEXT NOT NULL DEFAULT 'neutral'
                    CHECK (color_scheme IN ('success','info','warning','danger','neutral')),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    es_legado       BOOLEAN NOT NULL DEFAULT FALSE,
    orden           INTEGER NOT NULL DEFAULT 99,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE catalogo_resultados IS
    'Catálogo de resultados válidos para gestiones CRM. Fuente única de verdad — '
    'elimina hardcodes en Python y permite agregar nuevos resultados sin deploy.';

COMMENT ON COLUMN catalogo_resultados.codigo IS
    'Código interno usado en DB y código Python (ej: PROMESA_PAGO)';
COMMENT ON COLUMN catalogo_resultados.etiqueta IS
    'Texto visible al usuario en la UI (ej: Prometió pagar)';
COMMENT ON COLUMN catalogo_resultados.icono IS
    'Emoji o prefijo visual para la UI (ej: 🤝)';
COMMENT ON COLUMN catalogo_resultados.color_scheme IS
    'Esquema de color: success | info | warning | danger | neutral';
COMMENT ON COLUMN catalogo_resultados.activo IS
    'FALSE oculta el resultado de la UI (sin borrarlo de la BD)';
COMMENT ON COLUMN catalogo_resultados.es_legado IS
    'TRUE = valor antiguo, solo para mostrar historial. No aparece en nuevas gestiones.';
COMMENT ON COLUMN catalogo_resultados.orden IS
    'Orden de aparición en dropdowns de la UI';


-- ---------------------------------------------------------------------------
-- PASO 2 — Cargar datos iniciales
-- ---------------------------------------------------------------------------

INSERT INTO catalogo_resultados
    (codigo, etiqueta, icono, color_scheme, activo, es_legado, orden)
VALUES
    -- Valores actuales (estándar 2026)
    ('EXITOSO',        'Acordó pagar',        '✅', 'success', TRUE,  FALSE, 1),
    ('PROMESA_PAGO',   'Prometió pagar',      '🤝', 'info',    TRUE,  TRUE,  93),  -- legado: mismo significado que EXITOSO
    ('SOLICITO_PLAZO', 'Solicitó más plazo',  '⏳', 'warning', TRUE,  FALSE, 3),
    ('EN_NEGOCIACION', 'En negociación',      '💬', 'info',    TRUE,  FALSE, 4),
    ('SIN_RESPUESTA',  'Sin respuesta',       '📵', 'neutral', TRUE,  FALSE, 5),
    ('ESCALAR_LEGAL',  'Derivar a Legal',     '⚖️', 'danger',  TRUE,  FALSE, 6),
    ('DISPUTA',        'Disputó la deuda',    '❓', 'warning', TRUE,  FALSE, 7),
    -- Valores legado (historial antiguo, no aparecen en nuevas gestiones)
    ('FALLIDO',        'Falló',               '❌', 'danger',  TRUE,  TRUE,  90),
    ('PENDIENTE',      'Prometió pagar',      '🤝', 'warning', TRUE,  TRUE,  91),
    ('REPROGRAMADO',   'Derivar a Legal',     '⚖️', 'neutral', TRUE,  TRUE,  92)
ON CONFLICT (codigo) DO UPDATE SET
    etiqueta     = EXCLUDED.etiqueta,
    icono        = EXCLUDED.icono,
    color_scheme = EXCLUDED.color_scheme,
    activo       = EXCLUDED.activo,
    es_legado    = EXCLUDED.es_legado,
    orden        = EXCLUDED.orden;


-- ---------------------------------------------------------------------------
-- PASO 3 — Reemplazar CHECK constraint rígido por validación flexible
-- ---------------------------------------------------------------------------
-- El constraint en gestiones.resultado ya no necesita listar valores explícitos
-- porque la validación ocurre en la app (db_manager.py) consultando esta tabla.
-- Lo dejamos sin CHECK para que la BD no bloquee inserciones al agregar nuevos
-- resultados sin ejecutar ALTER TABLE.

ALTER TABLE gestiones
DROP CONSTRAINT IF EXISTS gestiones_resultado_check;

-- Nota: la integridad la garantiza la app. Si en el futuro se quiere FK:
-- ALTER TABLE gestiones
--     ADD CONSTRAINT gestiones_resultado_fk
--     FOREIGN KEY (resultado) REFERENCES catalogo_resultados(codigo);
-- (requiere que todos los valores existentes estén en el catálogo)


-- ---------------------------------------------------------------------------
-- PASO 4 — Verificación
-- ---------------------------------------------------------------------------

SELECT
    codigo, etiqueta, icono, color_scheme, activo, es_legado, orden
FROM catalogo_resultados
ORDER BY es_legado, orden;
-- Debe mostrar 10 filas: 7 activos + 3 legado
