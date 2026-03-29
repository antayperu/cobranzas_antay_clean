-- ============================================================================
-- 201_homologar_produccion_v2.1.0_fixed.sql
-- Script CORREGIDO basado en schema real de producción
-- ReporteCobranzas — Antay Fábrica de Software
-- Fecha: 2026-03-28
-- ============================================================================
-- INSTRUCCIONES:
--   1. Ir a supabase.com → proyecto Antay-Cobranzas (PRODUCTION)
--   2. SQL Editor → New Query
--   3. Pegar TODO este script y ejecutar (Run)
--   4. Verificar que la última línea diga: HOMOLOGACION_v2.1.0_OK
--
-- Es IDEMPOTENTE: puede ejecutarse varias veces sin daño.
-- NO borra datos existentes.
-- ============================================================================

BEGIN;

-- ============================================================================
-- PASO 1 — Función helper
-- ============================================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PASO 2 — Tablas que NO existen en producción (crear si faltan)
-- ============================================================================

-- ledger_last_send
CREATE TABLE IF NOT EXISTS public.ledger_last_send (
    ledger_key   TEXT PRIMARY KEY,
    last_sent_at TIMESTAMPTZ NOT NULL,
    recipient    TEXT,
    cycle_id     TEXT,
    created_at   TIMESTAMPTZ DEFAULT now(),
    updated_at   TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ledger_last_send_last_sent_at ON public.ledger_last_send(last_sent_at);
DROP TRIGGER IF EXISTS update_ledger_last_send_updated_at ON public.ledger_last_send;
CREATE TRIGGER update_ledger_last_send_updated_at
    BEFORE UPDATE ON public.ledger_last_send
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- send_attempts
CREATE TABLE IF NOT EXISTS public.send_attempts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ledger_key TEXT NOT NULL,
    recipient  TEXT,
    status     TEXT,
    error_msg  TEXT,
    channel    TEXT,
    cycle_id   TEXT,
    timestamp  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_send_attempts_ledger_key ON public.send_attempts(ledger_key);
CREATE INDEX IF NOT EXISTS idx_send_attempts_status     ON public.send_attempts(status);

-- cuotas_acuerdo
CREATE TABLE IF NOT EXISTS public.cuotas_acuerdo (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    acuerdo_id        UUID NOT NULL REFERENCES public.acuerdos_pago(id) ON DELETE CASCADE,
    numero_cuota      INTEGER NOT NULL,
    monto             NUMERIC(14,2),
    fecha_vencimiento DATE,
    estado            TEXT DEFAULT 'PENDIENTE'
                      CHECK (estado IN ('PENDIENTE','PAGADA','VENCIDA')),
    fecha_pago        DATE,
    created_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cuotas_acuerdo_id ON public.cuotas_acuerdo(acuerdo_id);

-- catalogo_resultados (nuevo en v2.1.0)
CREATE TABLE IF NOT EXISTS public.catalogo_resultados (
    codigo       TEXT PRIMARY KEY,
    etiqueta     TEXT NOT NULL,
    icono        TEXT NOT NULL DEFAULT '',
    color_scheme TEXT NOT NULL DEFAULT 'neutral'
                 CHECK (color_scheme IN ('success','info','warning','danger','neutral')),
    activo       BOOLEAN NOT NULL DEFAULT TRUE,
    es_legado    BOOLEAN NOT NULL DEFAULT FALSE,
    orden        INTEGER NOT NULL DEFAULT 99,
    created_at   TIMESTAMPTZ DEFAULT now()
);

INSERT INTO public.catalogo_resultados
    (codigo, etiqueta, icono, color_scheme, activo, es_legado, orden)
VALUES
    ('EXITOSO',        'Acordó pagar',       '✅', 'success', TRUE, FALSE,  1),
    ('PROMESA_PAGO',   'Prometió pagar',     '🤝', 'info',    TRUE, TRUE,  93),
    ('SOLICITO_PLAZO', 'Solicitó más plazo', '⏳', 'warning', TRUE, FALSE,  3),
    ('EN_NEGOCIACION', 'En negociación',     '💬', 'info',    TRUE, FALSE,  4),
    ('SIN_RESPUESTA',  'Sin respuesta',      '📵', 'neutral', TRUE, FALSE,  5),
    ('ESCALAR_LEGAL',  'Derivar a Legal',    '⚖️', 'danger',  TRUE, FALSE,  6),
    ('DISPUTA',        'Disputó la deuda',   '❓', 'warning', TRUE, FALSE,  7),
    ('FALLIDO',        'Falló',              '❌', 'danger',  TRUE, TRUE,  90),
    ('PENDIENTE',      'Prometió pagar',     '🤝', 'warning', TRUE, TRUE,  91),
    ('REPROGRAMADO',   'Derivar a Legal',    '⚖️', 'neutral', TRUE, TRUE,  92)
ON CONFLICT (codigo) DO UPDATE SET
    etiqueta     = EXCLUDED.etiqueta,
    icono        = EXCLUDED.icono,
    color_scheme = EXCLUDED.color_scheme,
    activo       = EXCLUDED.activo,
    es_legado    = EXCLUDED.es_legado,
    orden        = EXCLUDED.orden;

-- ============================================================================
-- PASO 3 — Columnas faltantes en tablas existentes
-- ============================================================================

-- 3.1 documentos_ciclo
ALTER TABLE public.documentos_ciclo
    ADD COLUMN IF NOT EXISTS saldo_original NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS extra_data     JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS updated_at     TIMESTAMPTZ DEFAULT now();

-- 3.2 resumen_ciclo — dual moneda + cartera activa + amortizaciones
ALTER TABLE public.resumen_ciclo
    ADD COLUMN IF NOT EXISTS monto_total_sol              NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_total_usd              NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_recuperado_sol         NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_recuperado_usd         NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_recuperado_sol_activa  NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_recuperado_usd_activa  NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS docs_recuperados_activa      INTEGER       DEFAULT 0,
    ADD COLUMN IF NOT EXISTS tasa_recuperacion_activa     NUMERIC(6,2)  DEFAULT 0,
    ADD COLUMN IF NOT EXISTS docs_amortizados             INTEGER       DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_amortizado_sol         NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_amortizado_usd         NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS docs_amortizados_activa      INTEGER       DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_amortizado_sol_activa  NUMERIC(14,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_amortizado_usd_activa  NUMERIC(14,2) DEFAULT 0;

-- 3.3 acuerdos_pago — moneda faltante
ALTER TABLE public.acuerdos_pago
    ADD COLUMN IF NOT EXISTS moneda TEXT DEFAULT 'PEN';

-- 3.4 notificaciones — canal faltante
ALTER TABLE public.notificaciones
    ADD COLUMN IF NOT EXISTS canal TEXT;

-- 3.5 gestiones — remover constraint rígido (la app valida por catálogo)
ALTER TABLE public.gestiones
    DROP CONSTRAINT IF EXISTS gestiones_resultado_check;

-- ============================================================================
-- PASO 4 — Backfill: copiar valores existentes a nuevas columnas
-- ============================================================================
UPDATE public.resumen_ciclo
   SET monto_total_sol       = COALESCE(monto_total, 0),
       monto_total_usd       = 0,
       monto_recuperado_sol  = COALESCE(monto_recuperado, 0),
       monto_recuperado_usd  = 0
 WHERE monto_total_sol = 0 AND COALESCE(monto_total, 0) > 0;

-- ============================================================================
-- PASO 5 — Verificación final
-- ============================================================================
DO $$
DECLARE _missing TEXT;
BEGIN
    SELECT string_agg(t.name, ', ' ORDER BY t.name) INTO _missing
    FROM (VALUES
        ('clientes'),('documentos'),('cobranzas'),('notificaciones'),
        ('ledger_last_send'),('send_attempts'),('app_config'),
        ('ciclos_procesamiento'),('documentos_ciclo'),('gestiones'),
        ('acuerdos_pago'),('cuotas_acuerdo'),('resumen_cliente_ciclo'),
        ('resumen_ciclo'),('catalogo_resultados')
    ) AS t(name)
    WHERE to_regclass('public.' || t.name) IS NULL;

    IF _missing IS NOT NULL THEN
        RAISE EXCEPTION 'Faltan tablas: %', _missing;
    END IF;
END $$;

-- Reporte de conteos
SELECT tabla, total FROM (
    SELECT 'clientes'              AS tabla, COUNT(*)::INT AS total FROM public.clientes
    UNION ALL SELECT 'documentos_ciclo',     COUNT(*) FROM public.documentos_ciclo
    UNION ALL SELECT 'gestiones',            COUNT(*) FROM public.gestiones
    UNION ALL SELECT 'notificaciones',       COUNT(*) FROM public.notificaciones
    UNION ALL SELECT 'acuerdos_pago',        COUNT(*) FROM public.acuerdos_pago
    UNION ALL SELECT 'cuotas_acuerdo',       COUNT(*) FROM public.cuotas_acuerdo
    UNION ALL SELECT 'ciclos_procesamiento', COUNT(*) FROM public.ciclos_procesamiento
    UNION ALL SELECT 'resumen_ciclo',        COUNT(*) FROM public.resumen_ciclo
    UNION ALL SELECT 'catalogo_resultados',  COUNT(*) FROM public.catalogo_resultados
    UNION ALL SELECT 'app_config',           COUNT(*) FROM public.app_config
) sub ORDER BY tabla;

SELECT 'HOMOLOGACION_v2.1.0_OK' AS status;

COMMIT;
