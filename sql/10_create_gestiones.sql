-- =====================================================
-- 10_create_gestiones.sql
-- Registro CRM de todas las interacciones con clientes
-- =====================================================

CREATE TABLE IF NOT EXISTS gestiones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id TEXT REFERENCES clientes(cliente_id) ON DELETE SET NULL,
    tipo_gestion TEXT NOT NULL CHECK (tipo_gestion IN ('EMAIL', 'WHATSAPP', 'LLAMADA', 'VISITA', 'NOTA', 'OTRO')),
    canal TEXT NOT NULL DEFAULT 'EMAIL',
    fecha TIMESTAMP WITH TIME ZONE DEFAULT now(),
    resultado TEXT CHECK (resultado IN ('EXITOSO', 'FALLIDO', 'PENDIENTE', 'SIN_RESPUESTA', 'REPROGRAMADO')),
    notas TEXT,
    usuario TEXT,
    duracion_minutos INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gestiones_cliente_id ON gestiones(cliente_id);
CREATE INDEX IF NOT EXISTS idx_gestiones_tipo ON gestiones(tipo_gestion);
CREATE INDEX IF NOT EXISTS idx_gestiones_fecha ON gestiones(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_gestiones_resultado ON gestiones(resultado);
CREATE INDEX IF NOT EXISTS idx_gestiones_canal ON gestiones(canal);

-- Trigger para auto-update de updated_at (reutiliza funcion existente)
CREATE TRIGGER update_gestiones_updated_at
    BEFORE UPDATE ON gestiones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE gestiones IS 'Registro CRM de todas las interacciones con clientes: emails, llamadas, visitas, WhatsApp';
