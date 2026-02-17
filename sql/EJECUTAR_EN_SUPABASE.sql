-- ============================================
-- SCRIPT CONSOLIDADO PARA SUPABASE
-- Sistema de Cobranzas Antay
-- Fecha: 2026-02-05
-- ============================================
--
-- INSTRUCCIONES:
-- 1. Ir a https://gnsetbdjxbtaqchdhgpi.supabase.co
-- 2. SQL Editor > New Query
-- 3. Copiar TODO este archivo
-- 4. Pegar y ejecutar (Run)
-- 5. Verificar que las 4 tablas se crearon
--
-- ============================================

-- ====================
-- FUNCIÓN HELPER (se usa en todos los triggers)
-- ====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ====================
-- TABLA 1: clientes
-- ====================
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    email TEXT,
    telefono TEXT,
    ruc TEXT,
    direccion TEXT,
    estado TEXT DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO', 'MOROSO')),
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clientes_cliente_id ON clientes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_clientes_estado ON clientes(estado);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);

CREATE TRIGGER update_clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE clientes IS 'Información de clientes para sistema de cobranzas Antay';
COMMENT ON COLUMN clientes.cliente_id IS 'ID único del cliente en el sistema de negocio';
COMMENT ON COLUMN clientes.estado IS 'Estado del cliente: ACTIVO, INACTIVO, MOROSO';

-- ====================
-- TABLA 2: documentos
-- ====================
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

CREATE INDEX IF NOT EXISTS idx_documentos_documento_id ON documentos(documento_id);
CREATE INDEX IF NOT EXISTS idx_documentos_cliente_id ON documentos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_documentos_estado ON documentos(estado);
CREATE INDEX IF NOT EXISTS idx_documentos_fecha_vencimiento ON documentos(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON documentos(tipo_documento);

CREATE TRIGGER update_documentos_updated_at
    BEFORE UPDATE ON documentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE documentos IS 'Facturas y documentos de cobranza del sistema Antay';
COMMENT ON COLUMN documentos.documento_id IS 'ID único del documento en el sistema de negocio';
COMMENT ON COLUMN documentos.monto_pendiente IS 'Monto pendiente de pago (puede ser menor que monto_total si hay pagos parciales)';

-- ====================
-- TABLA 3: cobranzas
-- ====================
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

CREATE INDEX IF NOT EXISTS idx_cobranzas_documento_id ON cobranzas(documento_id);
CREATE INDEX IF NOT EXISTS idx_cobranzas_cliente_id ON cobranzas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cobranzas_tipo_gestion ON cobranzas(tipo_gestion);
CREATE INDEX IF NOT EXISTS idx_cobranzas_estado_gestion ON cobranzas(estado_gestion);
CREATE INDEX IF NOT EXISTS idx_cobranzas_fecha_gestion ON cobranzas(fecha_gestion);

CREATE TRIGGER update_cobranzas_updated_at
    BEFORE UPDATE ON cobranzas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE cobranzas IS 'Historial de gestiones de cobranza realizadas';
COMMENT ON COLUMN cobranzas.tipo_gestion IS 'Tipo de gestión: EMAIL, WHATSAPP, LLAMADA, VISITA, CARTA';
COMMENT ON COLUMN cobranzas.metadata IS 'Datos adicionales en formato JSON (IDs de mensajes, respuestas, etc)';

-- ====================
-- TABLA 4: notificaciones
-- ====================
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

CREATE INDEX IF NOT EXISTS idx_notificaciones_tipo ON notificaciones(tipo_notificacion);
CREATE INDEX IF NOT EXISTS idx_notificaciones_prioridad ON notificaciones(prioridad);
CREATE INDEX IF NOT EXISTS idx_notificaciones_estado ON notificaciones(estado);
CREATE INDEX IF NOT EXISTS idx_notificaciones_destinatario ON notificaciones(destinatario);
CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha_envio ON notificaciones(fecha_envio);
CREATE INDEX IF NOT EXISTS idx_notificaciones_cliente_id ON notificaciones(cliente_id);

CREATE TRIGGER update_notificaciones_updated_at
    BEFORE UPDATE ON notificaciones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE notificaciones IS 'Sistema de notificaciones y alertas del sistema Antay';
COMMENT ON COLUMN notificaciones.tipo_notificacion IS 'Tipo de notificación: VENCIMIENTO, PAGO_RECIBIDO, GESTION_FALLIDA, ALERTA, INFO';
COMMENT ON COLUMN notificaciones.metadata IS 'Datos adicionales en formato JSON';

-- ====================
-- VERIFICACIÓN FINAL
-- ====================
-- Ejecutar para verificar que todas las tablas existen:
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('clientes', 'documentos', 'cobranzas', 'notificaciones')
ORDER BY table_name;

-- ====================
-- FIN DEL SCRIPT
-- ====================
-- Si ves 4 filas en el resultado, las tablas se crearon correctamente
