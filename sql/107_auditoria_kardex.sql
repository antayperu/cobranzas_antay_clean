-- =============================================================================
-- AUDITORIA KARDEX -- RC-FEAT-042
-- Ejecutar en Supabase SQL Editor (producción o staging)
--
-- ANTES DE EJECUTAR: ajusta los dos ciclos en la sección "PASO 2"
--   :CIC_ANTERIOR  → el ciclo del período previo  (ej: HIST_20260219_2127)
--   :CIC_NUEVO     → el ciclo que quieres auditar (ej: HIST_20260311_1353)
--
-- Puedes encontrar los cycle_id en: SELECT cycle_id FROM kardex_cartera ORDER BY cycle_id;
-- =============================================================================


-- ============================================================
-- PASO 1 — Vista general del kardex con verificación de cadena
-- ============================================================
-- Muestra todos los ciclos y verifica la fórmula:
--   Ini + Nueva − Cobrado = Final  (diferencia debe ser ≈ 0)
-- Si "Diferencia S/" > 1 en algún ciclo, ese ciclo tiene inconsistencia.

SELECT
    k.cycle_id                                                   AS "Ciclo",
    k.fecha_ciclo                                                AS "Fecha",
    k.cycle_id_anterior                                          AS "Ciclo Anterior",
    -- Cartera Activa (notificables)
    k.saldo_inicial_sol_activa                                   AS "Ini S/ Act",
    k.cartera_nueva_sol_activa                                   AS "Nueva S/ Act",
    k.cobrado_sol_activa                                         AS "Cobrado S/ Act",
    k.saldo_final_sol_activa                                     AS "Fin S/ Act",
    ROUND(
        ABS( k.saldo_inicial_sol_activa
           + k.cartera_nueva_sol_activa
           - k.cobrado_sol_activa
           - k.saldo_final_sol_activa ), 2
    )                                                            AS "Dif S/ Act",
    -- Encadenamiento: ini del ciclo actual debe = fin del anterior
    LAG(k.saldo_final_sol_activa) OVER (ORDER BY k.cycle_id)    AS "Fin Ant (cadena)",
    ROUND(
        ABS( k.saldo_inicial_sol_activa
           - COALESCE(LAG(k.saldo_final_sol_activa) OVER (ORDER BY k.cycle_id), k.saldo_inicial_sol_activa)
        ), 2
    )                                                            AS "Error Cadena S/"
FROM kardex_cartera k
ORDER BY k.cycle_id;


-- ============================================================
-- PASO 2 — Detalle del movimiento entre dos ciclos consecutivos
-- ============================================================
-- AJUSTA AQUI los dos ciclos a comparar:

DO $$ BEGIN
    RAISE NOTICE '=== SUSTITUYE LOS VALORES DE cycle_id ABAJO ===';
END $$;

-- Cambia estos valores:
WITH
cic_ant AS (SELECT 'HIST_20260219_2127' AS id),   -- <<< CICLO ANTERIOR
cic_nue AS (SELECT 'HIST_20260311_1353' AS id),   -- <<< CICLO NUEVO

-- Documentos del ciclo anterior (excluyendo DSP/PAV)
docs_ant AS (
    SELECT
        d.match_key,
        d.cod_cliente,
        d.empresa,
        ROUND(d.saldo_real::numeric, 2)  AS saldo_real,
        d.moneda,
        d.tipo_pedido,
        d.enviar_email
    FROM documentos_ciclo d, cic_ant c
    WHERE d.cycle_id = c.id
      AND d.tipo_pedido NOT IN ('DSP', 'PAV')
),

-- Documentos del ciclo nuevo (excluyendo DSP/PAV)
docs_nue AS (
    SELECT
        d.match_key,
        d.cod_cliente,
        d.empresa,
        ROUND(d.saldo_real::numeric, 2)  AS saldo_real,
        d.moneda,
        d.tipo_pedido,
        d.enviar_email
    FROM documentos_ciclo d, cic_nue c
    WHERE d.cycle_id = c.id
      AND d.tipo_pedido NOT IN ('DSP', 'PAV')
),

-- Clasificación de cada documento
clasificados AS (

    -- A) Documentos NUEVOS (aparecen en nuevo, no estaban en anterior)
    SELECT
        'NUEVO'             AS categoria,
        n.moneda,
        n.enviar_email,
        n.cod_cliente,
        n.empresa,
        n.match_key,
        n.tipo_pedido,
        NULL::numeric       AS saldo_anterior,
        n.saldo_real        AS saldo_nuevo,
        n.saldo_real        AS monto_movimiento
    FROM docs_nue n
    LEFT JOIN docs_ant a ON a.match_key = n.match_key
    WHERE a.match_key IS NULL

    UNION ALL

    -- B) Documentos COBRADOS AL 100% (estaban en anterior, ya no están en nuevo)
    SELECT
        'COBRADO_100%'      AS categoria,
        a.moneda,
        a.enviar_email,
        a.cod_cliente,
        a.empresa,
        a.match_key,
        a.tipo_pedido,
        a.saldo_real        AS saldo_anterior,
        NULL::numeric       AS saldo_nuevo,
        a.saldo_real        AS monto_movimiento
    FROM docs_ant a
    LEFT JOIN docs_nue n ON n.match_key = a.match_key
    WHERE n.match_key IS NULL

    UNION ALL

    -- C) Documentos AMORTIZADOS PARCIALMENTE (persisten pero con saldo menor)
    SELECT
        'AMORTIZACION'      AS categoria,
        a.moneda,
        a.enviar_email,
        a.cod_cliente,
        a.empresa,
        a.match_key,
        a.tipo_pedido,
        a.saldo_real        AS saldo_anterior,
        n.saldo_real        AS saldo_nuevo,
        ROUND(a.saldo_real - n.saldo_real, 2) AS monto_movimiento
    FROM docs_ant a
    JOIN docs_nue n ON n.match_key = a.match_key
    WHERE a.saldo_real - n.saldo_real > 0.01

    UNION ALL

    -- D) Documentos SIN CAMBIO (persisten con mismo saldo — referencia)
    SELECT
        'SIN_CAMBIO'        AS categoria,
        a.moneda,
        a.enviar_email,
        a.cod_cliente,
        a.empresa,
        a.match_key,
        a.tipo_pedido,
        a.saldo_real        AS saldo_anterior,
        n.saldo_real        AS saldo_nuevo,
        0                   AS monto_movimiento
    FROM docs_ant a
    JOIN docs_nue n ON n.match_key = a.match_key
    WHERE ABS(a.saldo_real - n.saldo_real) <= 0.01
)

-- Resultado detallado
SELECT
    categoria                   AS "Categoría",
    moneda                      AS "Mon.",
    CASE WHEN enviar_email = 'SI' THEN 'Activa' ELSE 'Especial' END AS "Cartera",
    cod_cliente                 AS "Código",
    empresa                     AS "Cliente",
    match_key                   AS "Documento (match_key)",
    tipo_pedido                 AS "Tipo Doc",
    saldo_anterior              AS "Saldo Anterior",
    saldo_nuevo                 AS "Saldo Nuevo",
    monto_movimiento            AS "Monto Movimiento"
FROM clasificados
ORDER BY
    CASE categoria
        WHEN 'COBRADO_100%'  THEN 1
        WHEN 'AMORTIZACION'  THEN 2
        WHEN 'NUEVO'         THEN 3
        WHEN 'SIN_CAMBIO'    THEN 4
    END,
    moneda,
    monto_movimiento DESC;


-- ============================================================
-- PASO 3 — Resumen totalizador por categoría y moneda
-- ============================================================
-- Compara contra lo que tiene el kardex_cartera para verificar coincidencia.

WITH
cic_ant AS (SELECT 'HIST_20260219_2127' AS id),   -- <<< mismo ciclo anterior
cic_nue AS (SELECT 'HIST_20260311_1353' AS id),   -- <<< mismo ciclo nuevo

docs_ant AS (
    SELECT match_key, ROUND(saldo_real::numeric,2) saldo_real, moneda, enviar_email
    FROM documentos_ciclo d, cic_ant c
    WHERE d.cycle_id = c.id AND tipo_pedido NOT IN ('DSP','PAV')
),
docs_nue AS (
    SELECT match_key, ROUND(saldo_real::numeric,2) saldo_real, moneda, enviar_email
    FROM documentos_ciclo d, cic_nue c
    WHERE d.cycle_id = c.id AND tipo_pedido NOT IN ('DSP','PAV')
),

movimientos AS (
    -- Cobrados 100%
    SELECT 'COBRADO_100%' cat, a.moneda, a.enviar_email, a.saldo_real monto
    FROM docs_ant a LEFT JOIN docs_nue n ON n.match_key = a.match_key WHERE n.match_key IS NULL
    UNION ALL
    -- Amortizaciones
    SELECT 'AMORTIZACION', a.moneda, a.enviar_email, ROUND(a.saldo_real - n.saldo_real, 2)
    FROM docs_ant a JOIN docs_nue n ON n.match_key = a.match_key WHERE a.saldo_real - n.saldo_real > 0.01
    UNION ALL
    -- Nuevos
    SELECT 'NUEVO', n.moneda, n.enviar_email, n.saldo_real
    FROM docs_nue n LEFT JOIN docs_ant a ON a.match_key = n.match_key WHERE a.match_key IS NULL
    UNION ALL
    -- Saldo final actual
    SELECT 'SALDO_FINAL', n.moneda, n.enviar_email, n.saldo_real
    FROM docs_nue n
)

SELECT
    cat                                                     AS "Categoría",
    moneda                                                  AS "Moneda",
    CASE WHEN enviar_email = 'SI' THEN 'Activa' ELSE 'Especial' END AS "Cartera",
    COUNT(*)                                                AS "N° Docs",
    ROUND(SUM(monto), 2)                                    AS "Total Calculado"
FROM movimientos
GROUP BY cat, moneda, enviar_email
ORDER BY
    CASE cat WHEN 'COBRADO_100%' THEN 1 WHEN 'AMORTIZACION' THEN 2
             WHEN 'NUEVO' THEN 3 WHEN 'SALDO_FINAL' THEN 4 END,
    moneda, enviar_email;

-- =============================================================================
-- INTERPRETACION:
--   "COBRADO_100%" + "AMORTIZACION" (Activa, PEN) debe coincidir con
--     kardex_cartera.cobrado_sol_activa para ese cycle_id
--
--   "NUEVO" (Activa, PEN) debe coincidir con
--     kardex_cartera.cartera_nueva_sol_activa
--
--   "SALDO_FINAL" (Activa, PEN) debe coincidir con
--     kardex_cartera.saldo_final_sol_activa
-- =============================================================================
