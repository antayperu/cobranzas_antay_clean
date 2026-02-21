-- =====================================================
-- 09_create_ciclos_procesamiento.sql
-- Persistencia de sesion de procesamiento en Supabase
-- =====================================================

CREATE TABLE IF NOT EXISTS ciclos_procesamiento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id TEXT UNIQUE NOT NULL,
    df_final_json JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    row_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (now() + INTERVAL '30 days')
);

CREATE INDEX IF NOT EXISTS idx_ciclos_created_at ON ciclos_procesamiento(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ciclos_cycle_id ON ciclos_procesamiento(cycle_id);

COMMENT ON TABLE ciclos_procesamiento IS 'Almacena snapshots del ultimo ciclo de procesamiento para restaurar sesion';
COMMENT ON COLUMN ciclos_procesamiento.df_final_json IS 'DataFrame serializado como array de records JSON';
COMMENT ON COLUMN ciclos_procesamiento.metadata IS 'file_names, fecha_corte, row_count, columns, cycle_timestamp';
COMMENT ON COLUMN ciclos_procesamiento.expires_at IS 'TTL para limpieza automatica de ciclos antiguos';
