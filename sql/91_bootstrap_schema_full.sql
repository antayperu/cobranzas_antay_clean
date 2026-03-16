-- ============================================================================
-- 91_bootstrap_schema_full.sql
-- Bootstrap completo de schema para ReporteCobranzas (cloud-only).
-- Crea TODAS las tablas usadas por la app con relaciones e indices base.
-- ============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- --------------------------------------------------------------------------
-- 1) clientes
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.clientes (
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
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clientes_cliente_id ON public.clientes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_clientes_estado ON public.clientes(estado);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON public.clientes(email);

DROP TRIGGER IF EXISTS update_clientes_updated_at ON public.clientes;
CREATE TRIGGER update_clientes_updated_at
    BEFORE UPDATE ON public.clientes
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- --------------------------------------------------------------------------
-- 2) documentos
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id TEXT UNIQUE NOT NULL,
    cliente_id TEXT NOT NULL REFERENCES public.clientes(cliente_id) ON DELETE CASCADE,
    tipo_documento TEXT NOT NULL CHECK (tipo_documento IN ('FACTURA', 'BOLETA', 'NOTA_CREDITO', 'NOTA_DEBITO', 'RECIBO')),
    numero_documento TEXT NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    monto_total NUMERIC(12,2) NOT NULL,
    monto_pendiente NUMERIC(12,2) NOT NULL,
    moneda TEXT DEFAULT 'PEN' CHECK (moneda IN ('PEN', 'USD', 'EUR')),
    estado TEXT DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PAGADO', 'VENCIDO', 'CANCELADO')),
    descripcion TEXT,
    archivo_url TEXT,
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documentos_documento_id ON public.documentos(documento_id);
CREATE INDEX IF NOT EXISTS idx_documentos_cliente_id ON public.documentos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_documentos_estado ON public.documentos(estado);
CREATE INDEX IF NOT EXISTS idx_documentos_fecha_vencimiento ON public.documentos(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON public.documentos(tipo_documento);

DROP TRIGGER IF EXISTS update_documentos_updated_at ON public.documentos;
CREATE TRIGGER update_documentos_updated_at
    BEFORE UPDATE ON public.documentos
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- --------------------------------------------------------------------------
-- 3) cobranzas
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.cobranzas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id TEXT NOT NULL REFERENCES public.documentos(documento_id) ON DELETE CASCADE,
    cliente_id TEXT NOT NULL REFERENCES public.clientes(cliente_id) ON DELETE CASCADE,
    tipo_gestion TEXT NOT NULL CHECK (tipo_gestion IN ('EMAIL', 'WHATSAPP', 'LLAMADA', 'VISITA', 'CARTA')),
    estado_gestion TEXT NOT NULL CHECK (estado_gestion IN ('ENVIADO', 'ENTREGADO', 'LEIDO', 'RESPONDIDO', 'FALLIDO', 'BLOQUEADO')),
    fecha_gestion TIMESTAMPTZ DEFAULT now(),
    responsable TEXT,
    monto_gestionado NUMERIC(12,2),
    resultado TEXT,
    notas TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cobranzas_documento_id ON public.cobranzas(documento_id);
CREATE INDEX IF NOT EXISTS idx_cobranzas_cliente_id ON public.cobranzas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cobranzas_tipo_gestion ON public.cobranzas(tipo_gestion);
CREATE INDEX IF NOT EXISTS idx_cobranzas_estado_gestion ON public.cobranzas(estado_gestion);
CREATE INDEX IF NOT EXISTS idx_cobranzas_fecha_gestion ON public.cobranzas(fecha_gestion);

DROP TRIGGER IF EXISTS update_cobranzas_updated_at ON public.cobranzas;
CREATE TRIGGER update_cobranzas_updated_at
    BEFORE UPDATE ON public.cobranzas
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- --------------------------------------------------------------------------
-- 4) notificaciones
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.notificaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_notificacion TEXT NOT NULL CHECK (tipo_notificacion IN ('VENCIMIENTO', 'PAGO_RECIBIDO', 'GESTION_FALLIDA', 'ALERTA', 'INFO')),
    prioridad TEXT DEFAULT 'NORMAL' CHECK (prioridad IN ('BAJA', 'NORMAL', 'ALTA', 'URGENTE')),
    destinatario TEXT NOT NULL,
    asunto TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    estado TEXT DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'ENVIADO', 'LEIDO', 'ARCHIVADO')),
    fecha_envio TIMESTAMPTZ,
    fecha_lectura TIMESTAMPTZ,
    cliente_id TEXT REFERENCES public.clientes(cliente_id) ON DELETE SET NULL,
    documento_id TEXT REFERENCES public.documentos(documento_id) ON DELETE SET NULL,
    cycle_id TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notificaciones_tipo ON public.notificaciones(tipo_notificacion);
CREATE INDEX IF NOT EXISTS idx_notificaciones_prioridad ON public.notificaciones(prioridad);
CREATE INDEX IF NOT EXISTS idx_notificaciones_estado ON public.notificaciones(estado);
CREATE INDEX IF NOT EXISTS idx_notificaciones_destinatario ON public.notificaciones(destinatario);
CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha_envio ON public.notificaciones(fecha_envio);
CREATE INDEX IF NOT EXISTS idx_notificaciones_cliente_id ON public.notificaciones(cliente_id);
CREATE INDEX IF NOT EXISTS idx_notificaciones_cycle_id ON public.notificaciones(cycle_id);
CREATE INDEX IF NOT EXISTS idx_notificaciones_cycle_cliente ON public.notificaciones(cycle_id, cliente_id);

DROP TRIGGER IF EXISTS update_notificaciones_updated_at ON public.notificaciones;
CREATE TRIGGER update_notificaciones_updated_at
    BEFORE UPDATE ON public.notificaciones
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- --------------------------------------------------------------------------
-- 5) tracking operativo
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ledger_last_send (
    ledger_key TEXT PRIMARY KEY,
    last_sent_at TIMESTAMPTZ,
    last_msg_id TEXT,
    send_count INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ledger_last_send_last_sent_at ON public.ledger_last_send(last_sent_at);

DROP TRIGGER IF EXISTS update_ledger_last_send_updated_at ON public.ledger_last_send;
CREATE TRIGGER update_ledger_last_send_updated_at
    BEFORE UPDATE ON public.ledger_last_send
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

CREATE TABLE IF NOT EXISTS public.send_attempts (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    ledger_key TEXT,
    recipient TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    timestamp TIMESTAMPTZ DEFAULT now(),
    run_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_send_attempts_ledger_key ON public.send_attempts(ledger_key);
CREATE INDEX IF NOT EXISTS idx_send_attempts_recipient ON public.send_attempts(recipient);
CREATE INDEX IF NOT EXISTS idx_send_attempts_status ON public.send_attempts(status);
CREATE INDEX IF NOT EXISTS idx_send_attempts_timestamp ON public.send_attempts(timestamp);

-- --------------------------------------------------------------------------
-- 6) app_config
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.app_config (
    config_key TEXT PRIMARY KEY,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_app_config_updated_at ON public.app_config(updated_at);

DROP TRIGGER IF EXISTS update_app_config_updated_at ON public.app_config;
CREATE TRIGGER update_app_config_updated_at
    BEFORE UPDATE ON public.app_config
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

INSERT INTO public.app_config(config_key, payload)
VALUES ('global', '{}'::jsonb)
ON CONFLICT (config_key) DO NOTHING;

-- --------------------------------------------------------------------------
-- 7) ciclos + detalle (modelo cabecera/detalle)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ciclos_procesamiento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id TEXT UNIQUE NOT NULL,
    df_final_json JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    row_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + INTERVAL '30 days')
);

-- Alinear entornos legacy: permitir null en df_final_json.
ALTER TABLE public.ciclos_procesamiento
    ALTER COLUMN df_final_json DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ciclos_created_at ON public.ciclos_procesamiento(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ciclos_cycle_id ON public.ciclos_procesamiento(cycle_id);

CREATE TABLE IF NOT EXISTS public.documentos_ciclo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id TEXT NOT NULL REFERENCES public.ciclos_procesamiento(cycle_id) ON DELETE CASCADE,
    cliente_id TEXT,
    cod_cliente TEXT,
    empresa TEXT,
    enviar_email TEXT,
    nota TEXT,
    correo TEXT,
    telefono TEXT,
    tipo_pedido TEXT,
    comprobante TEXT,
    fech_emis TEXT,
    fech_venc TEXT,
    dias_mora TEXT,
    estado_deuda TEXT,
    moneda TEXT,
    tipo_cambio NUMERIC(14,4),
    mont_emit NUMERIC(14,2),
    mont_emit_display TEXT,
    saldo_real NUMERIC(14,2),
    saldo_real_display TEXT,
    saldo NUMERIC(14,2),
    saldo_original NUMERIC(14,2),
    saldo_display TEXT,
    detraccion NUMERIC(14,2),
    detraccion_display TEXT,
    estado_detraccion TEXT,
    amortizaciones TEXT,
    match_key TEXT,
    email_final TEXT,
    estado_email TEXT DEFAULT 'PENDIENTE',
    fecha_ultimo_envio TEXT,
    estado_whatsapp TEXT DEFAULT 'PENDIENTE',
    fecha_ultimo_wa TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE FUNCTION public.sync_documentos_ciclo_keys()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.cliente_id IS NULL OR btrim(NEW.cliente_id) = '' THEN
        NEW.cliente_id := NEW.cod_cliente;
    END IF;
    IF NEW.cod_cliente IS NULL OR btrim(NEW.cod_cliente) = '' THEN
        NEW.cod_cliente := NEW.cliente_id;
    END IF;
    IF NEW.saldo_original IS NULL THEN
        NEW.saldo_original := COALESCE(NEW.saldo, NEW.saldo_real, 0);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_documentos_ciclo_keys ON public.documentos_ciclo;
CREATE TRIGGER trg_sync_documentos_ciclo_keys
    BEFORE INSERT OR UPDATE ON public.documentos_ciclo
    FOR EACH ROW
    EXECUTE FUNCTION public.sync_documentos_ciclo_keys();

CREATE INDEX IF NOT EXISTS idx_documentos_ciclo_cycle_id ON public.documentos_ciclo(cycle_id);
CREATE INDEX IF NOT EXISTS idx_documentos_ciclo_cliente_id ON public.documentos_ciclo(cliente_id);
CREATE INDEX IF NOT EXISTS idx_documentos_ciclo_cod_cliente ON public.documentos_ciclo(cod_cliente);
CREATE INDEX IF NOT EXISTS idx_documentos_ciclo_match_key ON public.documentos_ciclo(match_key);
CREATE INDEX IF NOT EXISTS idx_documentos_ciclo_estado_email ON public.documentos_ciclo(estado_email);
CREATE INDEX IF NOT EXISTS idx_documentos_ciclo_estado_whatsapp ON public.documentos_ciclo(estado_whatsapp);

-- --------------------------------------------------------------------------
-- 8) gestiones
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.gestiones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id TEXT REFERENCES public.clientes(cliente_id) ON DELETE SET NULL,
    cycle_id TEXT,
    tipo_gestion TEXT NOT NULL CHECK (tipo_gestion IN ('EMAIL', 'WHATSAPP', 'LLAMADA', 'VISITA', 'NOTA', 'OTRO')),
    canal TEXT NOT NULL DEFAULT 'EMAIL',
    fecha TIMESTAMPTZ DEFAULT now(),
    resultado TEXT CHECK (resultado IN ('EXITOSO', 'FALLIDO', 'PENDIENTE', 'SIN_RESPUESTA', 'REPROGRAMADO')),
    notas TEXT,
    usuario TEXT,
    duracion_minutos INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gestiones_cliente_id ON public.gestiones(cliente_id);
CREATE INDEX IF NOT EXISTS idx_gestiones_tipo ON public.gestiones(tipo_gestion);
CREATE INDEX IF NOT EXISTS idx_gestiones_fecha ON public.gestiones(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_gestiones_resultado ON public.gestiones(resultado);
CREATE INDEX IF NOT EXISTS idx_gestiones_canal ON public.gestiones(canal);
CREATE INDEX IF NOT EXISTS idx_gestiones_cycle_id ON public.gestiones(cycle_id);

DROP TRIGGER IF EXISTS update_gestiones_updated_at ON public.gestiones;
CREATE TRIGGER update_gestiones_updated_at
    BEFORE UPDATE ON public.gestiones
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- --------------------------------------------------------------------------
-- 9) acuerdos y cuotas
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.acuerdos_pago (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id TEXT NOT NULL,
    ciclo_id TEXT,
    monto_total NUMERIC(14,2) NOT NULL,
    numero_cuotas INT NOT NULL DEFAULT 1 CHECK (numero_cuotas >= 1),
    fecha_acuerdo DATE NOT NULL,
    gestor TEXT,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO','CUMPLIDO','INCUMPLIDO','CANCELADO')),
    notas TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.cuotas_acuerdo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    acuerdo_id UUID NOT NULL REFERENCES public.acuerdos_pago(id) ON DELETE CASCADE,
    numero_cuota INT NOT NULL CHECK (numero_cuota >= 1),
    monto_cuota NUMERIC(14,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    fecha_pago DATE,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE','PAGADO','VENCIDO','REPACTADO')),
    notas TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (acuerdo_id, numero_cuota)
);

CREATE INDEX IF NOT EXISTS idx_acuerdos_cliente ON public.acuerdos_pago(cliente_id);
CREATE INDEX IF NOT EXISTS idx_acuerdos_estado ON public.acuerdos_pago(estado);
CREATE INDEX IF NOT EXISTS idx_cuotas_acuerdo_id ON public.cuotas_acuerdo(acuerdo_id);
CREATE INDEX IF NOT EXISTS idx_cuotas_estado ON public.cuotas_acuerdo(estado);
CREATE INDEX IF NOT EXISTS idx_cuotas_vencimiento ON public.cuotas_acuerdo(fecha_vencimiento);

DROP TRIGGER IF EXISTS update_acuerdos_pago_updated_at ON public.acuerdos_pago;
CREATE TRIGGER update_acuerdos_pago_updated_at
    BEFORE UPDATE ON public.acuerdos_pago
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_cuotas_acuerdo_updated_at ON public.cuotas_acuerdo;
CREATE TRIGGER update_cuotas_acuerdo_updated_at
    BEFORE UPDATE ON public.cuotas_acuerdo
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- --------------------------------------------------------------------------
-- 10) resumenes de trazabilidad
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.resumen_cliente_ciclo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id TEXT NOT NULL,
    cycle_id TEXT NOT NULL,
    docs_total INT NOT NULL DEFAULT 0,
    monto_total NUMERIC(14,2) NOT NULL DEFAULT 0,
    docs_recuperados INT NOT NULL DEFAULT 0,
    monto_recuperado NUMERIC(14,2) NOT NULL DEFAULT 0,
    gestiones_count INT NOT NULL DEFAULT 0,
    tiene_acuerdo_pago BOOLEAN NOT NULL DEFAULT FALSE,
    ultima_gestion TIMESTAMPTZ,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE','PARCIAL','RECUPERADO','SIN_ACTIVIDAD')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (cliente_id, cycle_id)
);

CREATE TABLE IF NOT EXISTS public.resumen_ciclo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id TEXT NOT NULL UNIQUE,
    cycle_id_anterior TEXT,
    clientes_total INT NOT NULL DEFAULT 0,
    docs_total INT NOT NULL DEFAULT 0,
    monto_total NUMERIC(14,2) NOT NULL DEFAULT 0,
    clientes_recuperados INT NOT NULL DEFAULT 0,
    docs_recuperados INT NOT NULL DEFAULT 0,
    monto_recuperado NUMERIC(14,2) NOT NULL DEFAULT 0,
    tasa_recuperacion NUMERIC(5,2) NOT NULL DEFAULT 0,
    gestiones_total INT NOT NULL DEFAULT 0,
    acuerdos_total INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_res_cli_ciclo_cliente ON public.resumen_cliente_ciclo(cliente_id);
CREATE INDEX IF NOT EXISTS idx_res_cli_ciclo_cycle ON public.resumen_cliente_ciclo(cycle_id);
CREATE INDEX IF NOT EXISTS idx_res_cli_ciclo_estado ON public.resumen_cliente_ciclo(estado);
CREATE INDEX IF NOT EXISTS idx_resumen_ciclo_id ON public.resumen_ciclo(cycle_id);

DROP TRIGGER IF EXISTS update_resumen_cliente_ciclo_updated_at ON public.resumen_cliente_ciclo;
CREATE TRIGGER update_resumen_cliente_ciclo_updated_at
    BEFORE UPDATE ON public.resumen_cliente_ciclo
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_resumen_ciclo_updated_at ON public.resumen_ciclo;
CREATE TRIGGER update_resumen_ciclo_updated_at
    BEFORE UPDATE ON public.resumen_ciclo
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

COMMIT;

SELECT 'BOOTSTRAP_SCHEMA_OK' AS status;
