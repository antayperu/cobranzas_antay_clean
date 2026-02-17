-- Tabla: documentos
-- Descripción: Almacena facturas y documentos de cobranza
-- Autor: Antay Consultoria
-- Fecha: 2026-02-05

CREATE TABLE IF NOT EXISTS documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id TEXT UNIQUE NOT NULL,
    cliente_id TEXT NOT NULL REFERENCES clientes(cliente_id) ON DELETE CASCADE,
    tipo_documento TEXT NOT NULL CHECK (tipo_documento IN ('FACTURA', 'BOLETA', 'NOTA_CREDITO', 'NOTA_DEBITO', 'RECIBO')),
    numero_documento TEXT NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    monto_total DECIMAL(12, 2) NOT NULL,
    monto_pendiente DECIMAL(12, 2) NOT NULL,
    moneda TEXT DEFAULT 'PEN' CHECK (moneda IN ('PEN', 'USD', 'EUR')),
    estado TEXT DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PAGADO', 'VENCIDO', 'CANCELADO')),
    descripcion TEXT,
    archivo_url TEXT,
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_documentos_documento_id ON documentos(documento_id);
CREATE INDEX IF NOT EXISTS idx_documentos_cliente_id ON documentos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_documentos_estado ON documentos(estado);
CREATE INDEX IF NOT EXISTS idx_documentos_fecha_vencimiento ON documentos(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON documentos(tipo_documento);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_documentos_updated_at
    BEFORE UPDATE ON documentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios de documentación
COMMENT ON TABLE documentos IS 'Facturas y documentos de cobranza del sistema Antay';
COMMENT ON COLUMN documentos.documento_id IS 'ID único del documento en el sistema de negocio';
COMMENT ON COLUMN documentos.monto_pendiente IS 'Monto pendiente de pago (puede ser menor que monto_total si hay pagos parciales)';
COMMENT ON COLUMN documentos.estado IS 'Estado del documento: PENDIENTE, PAGADO, VENCIDO, CANCELADO';
