-- ============================================
-- SCRIPT CONSOLIDADO PARA SUPABASE
-- Sistema de Cobranzas Antay
-- Fecha: 2026-02-15
-- ============================================
--
-- INSTRUCCIONES:
-- 1. Ir a tu proyecto de Supabase
-- 2. SQL Editor > New Query
-- 3. Copiar TODO este archivo
-- 4. Pegar y ejecutar (Run)
-- 5. Verificar que las 6 tablas se crearon
--
-- ============================================

-- ====================
-- FUNCION HELPER (se usa en triggers de tablas con updated_at)
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

CREATE INDEX IF NOT EXISTS idx_clientes_cliente_id ON clientes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_clientes_estado ON clientes(estado);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);

DROP TRIGGER IF EXISTS update_clientes_updated_at ON clientes;
CREATE TRIGGER update_clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE clientes IS 'Informacion de clientes para sistema de cobranzas Antay';
COMMENT ON COLUMN clientes.cliente_id IS 'ID unico del cliente en el sistema de negocio';
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

DROP TRIGGER IF EXISTS update_documentos_updated_at ON documentos;
CREATE TRIGGER update_documentos_updated_at
    BEFORE UPDATE ON documentos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE documentos IS 'Facturas y documentos de cobranza del sistema Antay';
COMMENT ON COLUMN documentos.documento_id IS 'ID unico del documento en el sistema de negocio';
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

DROP TRIGGER IF EXISTS update_cobranzas_updated_at ON cobranzas;
CREATE TRIGGER update_cobranzas_updated_at
    BEFORE UPDATE ON cobranzas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE cobranzas IS 'Historial de gestiones de cobranza realizadas';
COMMENT ON COLUMN cobranzas.tipo_gestion IS 'Tipo de gestion: EMAIL, WHATSAPP, LLAMADA, VISITA, CARTA';
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

DROP TRIGGER IF EXISTS update_notificaciones_updated_at ON notificaciones;
CREATE TRIGGER update_notificaciones_updated_at
    BEFORE UPDATE ON notificaciones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE notificaciones IS 'Sistema de notificaciones y alertas del sistema Antay';
COMMENT ON COLUMN notificaciones.tipo_notificacion IS 'Tipo de notificacion: VENCIMIENTO, PAGO_RECIBIDO, GESTION_FALLIDA, ALERTA, INFO';
COMMENT ON COLUMN notificaciones.metadata IS 'Datos adicionales en formato JSON';

-- ====================
-- TABLA 5: ledger_last_send (tracking de reenvio)
-- ====================
CREATE TABLE IF NOT EXISTS ledger_last_send (
    ledger_key TEXT PRIMARY KEY,
    last_sent_at TIMESTAMP WITH TIME ZONE,
    last_msg_id TEXT,
    send_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ledger_last_send_last_sent_at ON ledger_last_send(last_sent_at);

DROP TRIGGER IF EXISTS update_ledger_last_send_updated_at ON ledger_last_send;
CREATE TRIGGER update_ledger_last_send_updated_at
    BEFORE UPDATE ON ledger_last_send
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE ledger_last_send IS 'Control de ultimo envio por ledger_key para TTL/rate-limit';
COMMENT ON COLUMN ledger_last_send.ledger_key IS 'Clave unica para evitar reenvios no deseados';
COMMENT ON COLUMN ledger_last_send.last_sent_at IS 'Timestamp del ultimo envio';

-- ====================
-- TABLA 6: send_attempts (historial de intentos)
-- ====================
CREATE TABLE IF NOT EXISTS send_attempts (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    ledger_key TEXT,
    recipient TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    run_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_send_attempts_ledger_key ON send_attempts(ledger_key);
CREATE INDEX IF NOT EXISTS idx_send_attempts_recipient ON send_attempts(recipient);
CREATE INDEX IF NOT EXISTS idx_send_attempts_status ON send_attempts(status);
CREATE INDEX IF NOT EXISTS idx_send_attempts_timestamp ON send_attempts(timestamp);

COMMENT ON TABLE send_attempts IS 'Historial de intentos de envio de email/whatsapp';
COMMENT ON COLUMN send_attempts.recipient IS 'Destinatario del intento de envio';
COMMENT ON COLUMN send_attempts.status IS 'Estado del intento (SENT, FAILED, BLOCKED, etc)';
COMMENT ON COLUMN send_attempts.timestamp IS 'Timestamp del intento';

-- ====================
-- SEGURIDAD: RLS + POLITICAS SERVICE ROLE
-- ====================
ALTER TABLE IF EXISTS clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS cobranzas ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS notificaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ledger_last_send ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS send_attempts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS clientes_service_role_all ON clientes;
DROP POLICY IF EXISTS documentos_service_role_all ON documentos;
DROP POLICY IF EXISTS cobranzas_service_role_all ON cobranzas;
DROP POLICY IF EXISTS notificaciones_service_role_all ON notificaciones;
DROP POLICY IF EXISTS ledger_last_send_service_role_all ON ledger_last_send;
DROP POLICY IF EXISTS send_attempts_service_role_all ON send_attempts;

CREATE POLICY clientes_service_role_all
    ON clientes
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY documentos_service_role_all
    ON documentos
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY cobranzas_service_role_all
    ON cobranzas
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY notificaciones_service_role_all
    ON notificaciones
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY ledger_last_send_service_role_all
    ON ledger_last_send
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY send_attempts_service_role_all
    ON send_attempts
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ====================
-- VERIFICACION FINAL
-- ====================
-- Ejecutar para verificar que todas las tablas existen:
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'clientes',
      'documentos',
      'cobranzas',
      'notificaciones',
      'ledger_last_send',
      'send_attempts'
  )
ORDER BY table_name;

-- ====================
-- FIN DEL SCRIPT
-- ====================
-- Si ves 6 filas en el resultado, las tablas se crearon correctamente
