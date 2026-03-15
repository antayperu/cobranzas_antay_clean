-- ============================================================================
-- 92_verify_schema_contract.sql
-- Verificador de contrato de schema. Debe pasar 100% antes de usar la app.
-- ============================================================================

-- 1) Verificar tablas requeridas
DO $$
DECLARE
    _missing TEXT;
BEGIN
    SELECT string_agg(t.name, ', ' ORDER BY t.name)
    INTO _missing
    FROM (
        VALUES
            ('clientes'),
            ('documentos'),
            ('cobranzas'),
            ('notificaciones'),
            ('ledger_last_send'),
            ('send_attempts'),
            ('app_config'),
            ('ciclos_procesamiento'),
            ('documentos_ciclo'),
            ('gestiones'),
            ('acuerdos_pago'),
            ('cuotas_acuerdo'),
            ('resumen_cliente_ciclo'),
            ('resumen_ciclo')
    ) AS t(name)
    WHERE to_regclass('public.' || t.name) IS NULL;

    IF _missing IS NOT NULL THEN
        RAISE EXCEPTION 'Faltan tablas requeridas: %', _missing;
    END IF;
END
$$;

-- 2) Verificar FK documentos_ciclo -> ciclos_procesamiento(cycle_id)
DO $$
DECLARE
    _fk_count INT;
BEGIN
    SELECT COUNT(*)
    INTO _fk_count
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
     AND ccu.table_schema = tc.table_schema
    WHERE tc.table_schema = 'public'
      AND tc.table_name = 'documentos_ciclo'
      AND tc.constraint_type = 'FOREIGN KEY'
      AND kcu.column_name = 'cycle_id'
      AND ccu.table_name = 'ciclos_procesamiento'
      AND ccu.column_name = 'cycle_id';

    IF _fk_count = 0 THEN
        RAISE EXCEPTION 'Falta FK: documentos_ciclo.cycle_id -> ciclos_procesamiento.cycle_id';
    END IF;
END
$$;

-- 3) Verificar columnas minimas criticas para persistencia de ciclo
DO $$
DECLARE
    _missing_cols TEXT;
BEGIN
    SELECT string_agg(c.col, ', ' ORDER BY c.col)
    INTO _missing_cols
    FROM (
        VALUES
            ('cycle_id'),
            ('cliente_id'),
            ('cod_cliente'),
            ('match_key'),
            ('estado_email'),
            ('estado_whatsapp'),
            ('saldo_real'),
            ('saldo_original')
    ) AS c(col)
    WHERE NOT EXISTS (
        SELECT 1
        FROM information_schema.columns ic
        WHERE ic.table_schema = 'public'
          AND ic.table_name = 'documentos_ciclo'
          AND ic.column_name = c.col
    );

    IF _missing_cols IS NOT NULL THEN
        RAISE EXCEPTION 'Faltan columnas criticas en documentos_ciclo: %', _missing_cols;
    END IF;
END
$$;

-- 4) Verificar que df_final_json NO sea obligatorio (compatibilidad cloud-only detalle)
DO $$
DECLARE
    _is_nullable TEXT;
BEGIN
    SELECT is_nullable
    INTO _is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'ciclos_procesamiento'
      AND column_name = 'df_final_json';

    IF _is_nullable IS DISTINCT FROM 'YES' THEN
        RAISE EXCEPTION 'df_final_json sigue obligatorio (NOT NULL). Debe permitir NULL.';
    END IF;
END
$$;

-- 5) Reporte final de conteos (diagnostico)
SELECT 'clientes' AS tabla, COUNT(*) AS total FROM public.clientes
UNION ALL SELECT 'documentos', COUNT(*) FROM public.documentos
UNION ALL SELECT 'cobranzas', COUNT(*) FROM public.cobranzas
UNION ALL SELECT 'notificaciones', COUNT(*) FROM public.notificaciones
UNION ALL SELECT 'gestiones', COUNT(*) FROM public.gestiones
UNION ALL SELECT 'ciclos_procesamiento', COUNT(*) FROM public.ciclos_procesamiento
UNION ALL SELECT 'documentos_ciclo', COUNT(*) FROM public.documentos_ciclo
UNION ALL SELECT 'acuerdos_pago', COUNT(*) FROM public.acuerdos_pago
UNION ALL SELECT 'cuotas_acuerdo', COUNT(*) FROM public.cuotas_acuerdo
UNION ALL SELECT 'resumen_cliente_ciclo', COUNT(*) FROM public.resumen_cliente_ciclo
UNION ALL SELECT 'resumen_ciclo', COUNT(*) FROM public.resumen_ciclo
UNION ALL SELECT 'ledger_last_send', COUNT(*) FROM public.ledger_last_send
UNION ALL SELECT 'send_attempts', COUNT(*) FROM public.send_attempts
UNION ALL SELECT 'app_config', COUNT(*) FROM public.app_config
ORDER BY tabla;

SELECT 'SCHEMA_CONTRACT_OK' AS status;
