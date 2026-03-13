-- =============================================================================
-- RC-FEAT-021: Módulo Acuerdos de Pago con Cuotas
-- Tablas: acuerdos_pago + cuotas_acuerdo
-- =============================================================================

-- 1. Tabla principal de acuerdos
CREATE TABLE IF NOT EXISTS acuerdos_pago (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id      TEXT        NOT NULL,
    ciclo_id        TEXT,                       -- ciclo desde el que se creó (opcional)
    monto_total     NUMERIC(14,2) NOT NULL,
    numero_cuotas   INT         NOT NULL DEFAULT 1 CHECK (numero_cuotas >= 1),
    fecha_acuerdo   DATE        NOT NULL,
    gestor          TEXT,
    estado          TEXT        NOT NULL DEFAULT 'ACTIVO'
                        CHECK (estado IN ('ACTIVO','CUMPLIDO','INCUMPLIDO','CANCELADO')),
    notas           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Tabla de cuotas vinculadas a cada acuerdo
CREATE TABLE IF NOT EXISTS cuotas_acuerdo (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    acuerdo_id          UUID        NOT NULL REFERENCES acuerdos_pago(id) ON DELETE CASCADE,
    numero_cuota        INT         NOT NULL CHECK (numero_cuota >= 1),
    monto_cuota         NUMERIC(14,2) NOT NULL,
    fecha_vencimiento   DATE        NOT NULL,
    fecha_pago          DATE,
    estado              TEXT        NOT NULL DEFAULT 'PENDIENTE'
                            CHECK (estado IN ('PENDIENTE','PAGADO','VENCIDO','REPACTADO')),
    notas               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (acuerdo_id, numero_cuota)
);

-- 3. Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_acuerdos_cliente    ON acuerdos_pago (cliente_id);
CREATE INDEX IF NOT EXISTS idx_acuerdos_estado     ON acuerdos_pago (estado);
CREATE INDEX IF NOT EXISTS idx_cuotas_acuerdo_id   ON cuotas_acuerdo (acuerdo_id);
CREATE INDEX IF NOT EXISTS idx_cuotas_estado       ON cuotas_acuerdo (estado);
CREATE INDEX IF NOT EXISTS idx_cuotas_vencimiento  ON cuotas_acuerdo (fecha_vencimiento);

-- 4. Row Level Security (habilitar pero permiso total para service_role)
ALTER TABLE acuerdos_pago   ENABLE ROW LEVEL SECURITY;
ALTER TABLE cuotas_acuerdo  ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='acuerdos_pago' AND policyname='service_role_full_acuerdos') THEN
    CREATE POLICY "service_role_full_acuerdos"
        ON acuerdos_pago FOR ALL TO service_role USING (true) WITH CHECK (true);
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='cuotas_acuerdo' AND policyname='service_role_full_cuotas') THEN
    CREATE POLICY "service_role_full_cuotas"
        ON cuotas_acuerdo FOR ALL TO service_role USING (true) WITH CHECK (true);
  END IF;
END $$;
