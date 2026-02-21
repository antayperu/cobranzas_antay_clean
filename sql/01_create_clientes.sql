-- Tabla: clientes
-- Descripción: Almacena información de clientes para cobranzas
-- Autor: Antay Consultoria
-- Fecha: 2026-02-05

CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    email TEXT,
    dni TEXT,
    telefono TEXT,
    ruc TEXT,
    direccion TEXT,
    enviar_email TEXT DEFAULT 'SIN CONFIGURAR',
    estado TEXT DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO', 'MOROSO')),
    notas TEXT,
    extra_fields JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_clientes_cliente_id ON clientes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_clientes_estado ON clientes(estado);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios de documentación
COMMENT ON TABLE clientes IS 'Información de clientes para sistema de cobranzas Antay';
COMMENT ON COLUMN clientes.cliente_id IS 'ID único del cliente en el sistema de negocio';
COMMENT ON COLUMN clientes.estado IS 'Estado del cliente: ACTIVO, INACTIVO, MOROSO';
