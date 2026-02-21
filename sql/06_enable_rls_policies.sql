-- =====================================================
-- RLS Y POLITICAS DE SEGURIDAD OPERACIONAL
-- Ticket: SUPABASE-MIG-008
-- =====================================================
-- En esta arquitectura cloud-only, la app backend usa SERVICE ROLE KEY.
-- Estas politicas permiten operacion backend y dejan lista la base para hardening adicional.

-- 1) Habilitar RLS en tablas operativas
ALTER TABLE IF EXISTS clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS cobranzas ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS notificaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS ledger_last_send ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS send_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS app_config ENABLE ROW LEVEL SECURITY;

-- 2) Limpiar politicas previas (idempotente)
DROP POLICY IF EXISTS clientes_service_role_all ON clientes;
DROP POLICY IF EXISTS documentos_service_role_all ON documentos;
DROP POLICY IF EXISTS cobranzas_service_role_all ON cobranzas;
DROP POLICY IF EXISTS notificaciones_service_role_all ON notificaciones;
DROP POLICY IF EXISTS ledger_last_send_service_role_all ON ledger_last_send;
DROP POLICY IF EXISTS send_attempts_service_role_all ON send_attempts;
DROP POLICY IF EXISTS app_config_service_role_all ON app_config;

-- 3) Politicas para service_role (backend trusted)
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

CREATE POLICY app_config_service_role_all
    ON app_config
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 4) Verificacion de estado RLS
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
      'clientes',
      'documentos',
      'cobranzas',
      'notificaciones',
      'ledger_last_send',
      'send_attempts',
      'app_config'
  )
ORDER BY tablename;
