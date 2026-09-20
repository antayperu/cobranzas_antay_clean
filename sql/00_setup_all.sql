-- Setup completo de base de datos Supabase
-- Sistema de Cobranzas Antay
-- Fecha: 2026-02-15
--
-- INSTRUCCIONES:
-- 1. Conectarse a Supabase Dashboard
-- 2. Ir a SQL Editor
-- 3. Ejecutar este script completo
-- 4. Verificar que las 6 tablas se crearon correctamente
--
-- ORDEN DE EJECUCION:
-- - Funcion helper (update_updated_at_column)
-- - Tablas dominio: clientes -> documentos -> cobranzas -> notificaciones
-- - Tablas tracking: ledger_last_send -> send_attempts
-- - Indices y triggers para cada tabla

-- =====================================================
-- PASO 1: Crear funcion helper para triggers
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PASO 2: Crear tabla CLIENTES
-- =====================================================
\i 01_create_clientes.sql

-- =====================================================
-- PASO 3: Crear tabla DOCUMENTOS
-- =====================================================
\i 02_create_documentos.sql

-- =====================================================
-- PASO 4: Crear tabla COBRANZAS
-- =====================================================
\i 03_create_cobranzas.sql

-- =====================================================
-- PASO 5: Crear tabla NOTIFICACIONES
-- =====================================================
\i 04_create_notificaciones.sql

-- =====================================================
-- PASO 6: Crear tablas TRACKING (ledger/send_attempts)
-- =====================================================
\i 05_create_tracking_tables.sql

-- =====================================================
-- PASO 7: Seguridad operacional (RLS + politicas)
-- =====================================================
\i 06_enable_rls_policies.sql

-- =====================================================
-- VERIFICACION FINAL
-- =====================================================
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

-- Mostrar resumen de registros (deberia estar todo en 0 inicialmente)
SELECT
    'clientes' AS tabla, COUNT(*) AS registros FROM clientes
UNION ALL
SELECT 'documentos', COUNT(*) FROM documentos
UNION ALL
SELECT 'cobranzas', COUNT(*) FROM cobranzas
UNION ALL
SELECT 'notificaciones', COUNT(*) FROM notificaciones
UNION ALL
SELECT 'ledger_last_send', COUNT(*) FROM ledger_last_send
UNION ALL
SELECT 'send_attempts', COUNT(*) FROM send_attempts;
