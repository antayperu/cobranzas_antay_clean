-- Tabla: notificaciones
-- Descripción: Sistema de notificaciones y alertas
-- Autor: Antay Consultoria
-- Fecha: 2026-02-05

CREATE TABLE IF NOT EXISTS notificaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_notificacion TEXT NOT NULL CHECK (tipo_notificacion IN ('VENCIMIENTO', 'PAGO_RECIBIDO', 'GESTION_FALLIDA', 'ALERTA', 'INFO')),
    prioridad TEXT DEFAULT 'NORMAL' CHECK (prioridad IN ('BAJA', 'NORMAL', 'ALTA', 'URGENTE')),
    destinatario TEXT NOT NULL,
    asunto TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    estado TEXT DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'ENVIADO', 'LEIDO', 'ARCHIVADO')),
    fecha_envio TIMESTAMP WITH TIME ZONE,
    fecha_lectura TIMESTAMP WITH TIME ZONE,
    cliente_id TEXT REFERENCES clientes(cliente_id) ON DELETE SET NULL,
    documento_id TEXT REFERENCES documentos(documento_id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_notificaciones_tipo ON notificaciones(tipo_notificacion);
CREATE INDEX IF NOT EXISTS idx_notificaciones_prioridad ON notificaciones(prioridad);
CREATE INDEX IF NOT EXISTS idx_notificaciones_estado ON notificaciones(estado);
CREATE INDEX IF NOT EXISTS idx_notificaciones_destinatario ON notificaciones(destinatario);
CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha_envio ON notificaciones(fecha_envio);
CREATE INDEX IF NOT EXISTS idx_notificaciones_cliente_id ON notificaciones(cliente_id);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_notificaciones_updated_at
    BEFORE UPDATE ON notificaciones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios de documentación
COMMENT ON TABLE notificaciones IS 'Sistema de notificaciones y alertas del sistema Antay';
COMMENT ON COLUMN notificaciones.tipo_notificacion IS 'Tipo de notificación: VENCIMIENTO, PAGO_RECIBIDO, GESTION_FALLIDA, ALERTA, INFO';
COMMENT ON COLUMN notificaciones.prioridad IS 'Prioridad de la notificación: BAJA, NORMAL, ALTA, URGENTE';
COMMENT ON COLUMN notificaciones.metadata IS 'Datos adicionales en formato JSON';
