-- Tabla: cobranzas
-- Descripción: Registra intentos y gestiones de cobranza
-- Autor: Antay Consultoria
-- Fecha: 2026-02-05

CREATE TABLE IF NOT EXISTS cobranzas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id TEXT NOT NULL REFERENCES documentos(documento_id) ON DELETE CASCADE,
    cliente_id TEXT NOT NULL REFERENCES clientes(cliente_id) ON DELETE CASCADE,
    tipo_gestion TEXT NOT NULL CHECK (tipo_gestion IN ('EMAIL', 'WHATSAPP', 'LLAMADA', 'VISITA', 'CARTA')),
    estado_gestion TEXT NOT NULL CHECK (estado_gestion IN ('ENVIADO', 'ENTREGADO', 'LEIDO', 'RESPONDIDO', 'FALLIDO', 'BLOQUEADO')),
    fecha_gestion TIMESTAMP WITH TIME ZONE DEFAULT now(),
    responsable TEXT,
    monto_gestionado DECIMAL(12, 2),
    resultado TEXT,
    notas TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_cobranzas_documento_id ON cobranzas(documento_id);
CREATE INDEX IF NOT EXISTS idx_cobranzas_cliente_id ON cobranzas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cobranzas_tipo_gestion ON cobranzas(tipo_gestion);
CREATE INDEX IF NOT EXISTS idx_cobranzas_estado_gestion ON cobranzas(estado_gestion);
CREATE INDEX IF NOT EXISTS idx_cobranzas_fecha_gestion ON cobranzas(fecha_gestion);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_cobranzas_updated_at
    BEFORE UPDATE ON cobranzas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios de documentación
COMMENT ON TABLE cobranzas IS 'Historial de gestiones de cobranza realizadas';
COMMENT ON COLUMN cobranzas.tipo_gestion IS 'Tipo de gestión: EMAIL, WHATSAPP, LLAMADA, VISITA, CARTA';
COMMENT ON COLUMN cobranzas.estado_gestion IS 'Estado de la gestión: ENVIADO, ENTREGADO, LEIDO, RESPONDIDO, FALLIDO, BLOQUEADO';
COMMENT ON COLUMN cobranzas.metadata IS 'Datos adicionales en formato JSON (IDs de mensajes, respuestas, etc)';
