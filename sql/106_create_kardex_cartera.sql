-- =============================================================================
-- MIGRATION 106 — kardex_cartera: Ledger de Saldos por Ciclo
-- RC-FEAT-042
-- =============================================================================
-- Crea la tabla kardex_cartera que actúa como libro contable de la cartera.
-- Una fila por ciclo. El saldo_final del ciclo N es el saldo_inicial del ciclo N+1.
--
-- Fórmula garantizada en cada fila:
--   saldo_inicial + cartera_nueva − cobrado = saldo_final
--
-- Ejecutar en: Supabase producción y staging.
-- =============================================================================

CREATE TABLE IF NOT EXISTS kardex_cartera (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id                  TEXT UNIQUE NOT NULL,
    cycle_id_anterior         TEXT,
    fecha_ciclo               DATE NOT NULL,

    -- Cartera general (todos los clientes del ciclo)
    saldo_inicial_sol         NUMERIC(14,2) DEFAULT 0,
    cartera_nueva_sol         NUMERIC(14,2) DEFAULT 0,
    cobrado_sol               NUMERIC(14,2) DEFAULT 0,
    saldo_final_sol           NUMERIC(14,2) DEFAULT 0,

    saldo_inicial_usd         NUMERIC(14,2) DEFAULT 0,
    cartera_nueva_usd         NUMERIC(14,2) DEFAULT 0,
    cobrado_usd               NUMERIC(14,2) DEFAULT 0,
    saldo_final_usd           NUMERIC(14,2) DEFAULT 0,

    -- Cartera activa (solo clientes notificables: enviar_email = 'SI')
    saldo_inicial_sol_activa  NUMERIC(14,2) DEFAULT 0,
    cartera_nueva_sol_activa  NUMERIC(14,2) DEFAULT 0,
    cobrado_sol_activa        NUMERIC(14,2) DEFAULT 0,
    saldo_final_sol_activa    NUMERIC(14,2) DEFAULT 0,

    saldo_inicial_usd_activa  NUMERIC(14,2) DEFAULT 0,
    cartera_nueva_usd_activa  NUMERIC(14,2) DEFAULT 0,
    cobrado_usd_activa        NUMERIC(14,2) DEFAULT 0,
    saldo_final_usd_activa    NUMERIC(14,2) DEFAULT 0,

    created_at                TIMESTAMPTZ DEFAULT now(),
    updated_at                TIMESTAMPTZ DEFAULT now()
);

-- Índice para búsqueda rápida por ciclo anterior (trazabilidad de cadena)
CREATE INDEX IF NOT EXISTS idx_kardex_cycle_id_anterior
    ON kardex_cartera (cycle_id_anterior);

-- Verificación post-migration
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'kardex_cartera'
ORDER BY ordinal_position;
