-- Patch incremental para entornos existentes.
-- Agrega columnas requeridas por Clientes Premium sin recrear tabla.

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS dni TEXT,
    ADD COLUMN IF NOT EXISTS enviar_email TEXT DEFAULT 'SIN CONFIGURAR',
    ADD COLUMN IF NOT EXISTS extra_fields JSONB DEFAULT '{}'::jsonb;
