-- =============================================================================
-- RC-FEAT-023: Trazabilidad Completa — Nivel 2 (por cliente/ciclo) y Nivel 3 (por ciclo)
-- Tablas: resumen_cliente_ciclo + resumen_ciclo
-- =============================================================================

-- 1. Resumen por cliente por ciclo (Nivel 2 de trazabilidad)
CREATE TABLE IF NOT EXISTS resumen_cliente_ciclo (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id          TEXT        NOT NULL,
    cycle_id            TEXT        NOT NULL,

    -- Situacion en este ciclo
    docs_total          INT         NOT NULL DEFAULT 0,
    monto_total         NUMERIC(14,2) NOT NULL DEFAULT 0,

    -- Recuperaciones detectadas (docs en ciclo anterior ausentes en este)
    docs_recuperados    INT         NOT NULL DEFAULT 0,
    monto_recuperado    NUMERIC(14,2) NOT NULL DEFAULT 0,

    -- Actividad de gestión
    gestiones_count     INT         NOT NULL DEFAULT 0,
    tiene_acuerdo_pago  BOOLEAN     NOT NULL DEFAULT FALSE,
    ultima_gestion      TIMESTAMPTZ,

    -- Estado de recuperación calculado
    estado              TEXT        NOT NULL DEFAULT 'PENDIENTE'
                            CHECK (estado IN ('PENDIENTE','PARCIAL','RECUPERADO','SIN_ACTIVIDAD')),

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (cliente_id, cycle_id)
);

-- 2. Resumen por ciclo total (Nivel 3 de trazabilidad)
CREATE TABLE IF NOT EXISTS resumen_ciclo (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id                TEXT        NOT NULL UNIQUE,
    cycle_id_anterior       TEXT,               -- ciclo previo que se comparó

    -- Totales del ciclo
    clientes_total          INT         NOT NULL DEFAULT 0,
    docs_total              INT         NOT NULL DEFAULT 0,
    monto_total             NUMERIC(14,2) NOT NULL DEFAULT 0,

    -- Recuperaciones vs ciclo anterior
    clientes_recuperados    INT         NOT NULL DEFAULT 0,
    docs_recuperados        INT         NOT NULL DEFAULT 0,
    monto_recuperado        NUMERIC(14,2) NOT NULL DEFAULT 0,
    tasa_recuperacion       NUMERIC(5,2) NOT NULL DEFAULT 0,   -- porcentaje 0-100

    -- Actividad
    gestiones_total         INT         NOT NULL DEFAULT 0,
    acuerdos_total          INT         NOT NULL DEFAULT 0,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Índices
CREATE INDEX IF NOT EXISTS idx_res_cli_ciclo_cliente  ON resumen_cliente_ciclo (cliente_id);
CREATE INDEX IF NOT EXISTS idx_res_cli_ciclo_cycle    ON resumen_cliente_ciclo (cycle_id);
CREATE INDEX IF NOT EXISTS idx_res_cli_ciclo_estado   ON resumen_cliente_ciclo (estado);
CREATE INDEX IF NOT EXISTS idx_resumen_ciclo_id       ON resumen_ciclo (cycle_id);

-- 4. RLS
ALTER TABLE resumen_cliente_ciclo   ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumen_ciclo           ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='resumen_cliente_ciclo' AND policyname='service_role_full_resumen_cliente') THEN
    CREATE POLICY "service_role_full_resumen_cliente"
        ON resumen_cliente_ciclo FOR ALL TO service_role USING (true) WITH CHECK (true);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='resumen_ciclo' AND policyname='service_role_full_resumen_ciclo') THEN
    CREATE POLICY "service_role_full_resumen_ciclo"
        ON resumen_ciclo FOR ALL TO service_role USING (true) WITH CHECK (true);
  END IF;
END $$;
