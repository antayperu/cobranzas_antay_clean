-- ============================================
-- 07_create_app_config.sql
-- Configuracion global de la app en Supabase (CONFIG-001)
-- ============================================

-- Helper trigger function (idempotente)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS app_config (
    config_key TEXT PRIMARY KEY,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_app_config_updated_at ON app_config(updated_at);

DROP TRIGGER IF EXISTS update_app_config_updated_at ON app_config;
CREATE TRIGGER update_app_config_updated_at
    BEFORE UPDATE ON app_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE app_config IS 'Configuracion global de la aplicacion (cloud-only)';
COMMENT ON COLUMN app_config.config_key IS 'Clave de configuracion. Se usa global.';
COMMENT ON COLUMN app_config.payload IS 'JSONB con configuracion completa de UI y canales.';

-- Bootstrap row por defecto (idempotente)
INSERT INTO app_config(config_key, payload)
VALUES ('global', '{}'::jsonb)
ON CONFLICT (config_key) DO NOTHING;
