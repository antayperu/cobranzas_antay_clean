-- Setup completo de base de datos Supabase
-- Sistema de Cobranzas Antay
-- Fecha: 2026-02-05
--
-- INSTRUCCIONES:
-- 1. Conectarse a Supabase Dashboard
-- 2. Ir a SQL Editor
-- 3. Ejecutar este script completo
-- 4. Verificar que las 4 tablas se crearon correctamente
--
-- ORDEN DE EJECUCIÓN:
-- - Función helper (update_updated_at_column)
-- - Tablas en orden: clientes -> documentos -> cobranzas -> notificaciones
-- - Índices y triggers para cada tabla

-- =====================================================
-- PASO 1: Crear función helper para triggers
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
-- VERIFICACIÓN FINAL
-- =====================================================
-- Ejecutar para verificar que todas las tablas existen:
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('clientes', 'documentos', 'cobranzas', 'notificaciones')
ORDER BY table_name;

-- Mostrar resumen de registros (debería estar todo en 0 inicialmente)
SELECT
    'clientes' as tabla, COUNT(*) as registros FROM clientes
UNION ALL
SELECT 'documentos', COUNT(*) FROM documentos
UNION ALL
SELECT 'cobranzas', COUNT(*) FROM cobranzas
UNION ALL
SELECT 'notificaciones', COUNT(*) FROM notificaciones;
