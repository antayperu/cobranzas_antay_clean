-- =============================================================================
-- DATA RECONCILIATION — Informe Gerencial para Comité de Directorio (RC-FEAT-039)
-- =============================================================================
-- Propósito : Validar que los números del PDF "Informe Gerencial" coincidan
--             exactamente con la base de datos (Supabase).
-- Uso       : Ejecutar en Supabase SQL Editor (staging o producción).
--             Reemplazar 'CIC-YYYYMMDD-HHMM' con el ciclo analizado.
--
-- Lógica de la app:
--   - Aging    : por CLIENTE ÚNICO (mora máxima), no por documento.
--   - Saldos   : SUM(saldo_real) por moneda, excluye tipo_pedido IN ('DSP','PAV').
--   - Gestiones: filtradas por cycle_id.
--   - Acuerdos : tabla acuerdos_pago usa ciclo_id (NO cycle_id) — trampa crítica.
--   - Cuotas   : cuotas_acuerdo JOIN acuerdos_pago WHERE ciclo_id = X AND estado='PAGADA'.
-- =============================================================================


-- ===========================================================================
-- SECCIÓN A — Semáforo Ejecutivo (4 tarjetas)
-- ===========================================================================

-- ① TARJETA 1: CARTERA VENCIDA TOTAL
--    = SUM(saldo_real) por moneda de documentos válidos del ciclo.
--    La app suma saldo_sol y saldo_usd del resultado de get_aging_distribution().
SELECT
    SUM(saldo_real) FILTER (WHERE moneda NOT IN ('USD','US$','$','DOLARES','DÓLARES'))
                                    AS cartera_vencida_sol,
    SUM(saldo_real) FILTER (WHERE moneda IN ('USD','US$','$','DOLARES','DÓLARES'))
                                    AS cartera_vencida_usd,
    COUNT(DISTINCT cod_cliente)     AS clientes_activos
FROM documentos_ciclo
WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'
  AND tipo_pedido NOT IN ('DSP','PAV');
-- PDF muestra: "S/ X,XXX" (sol) y "N clientes activos" ó "US$ X,XXX" si existe deuda USD


-- ② TARJETA 2: RECUPERADO EN EL PERÍODO
--    = monto_recuperado_sol / monto_recuperado_usd de resumen_ciclo.
--    Representa documentos que estaban en el CxC anterior y desaparecieron
--    en el CxC actual → fueron cobrados en el ERP y reflejados en Cobranza.xlsx.
--    NOTA: requiere que exista un ciclo anterior (cycle_id_anterior no nulo).
SELECT
    monto_recuperado_sol,
    monto_recuperado_usd,
    docs_recuperados,
    tasa_recuperacion,
    cycle_id_anterior
FROM resumen_ciclo
WHERE cycle_id = 'CIC-YYYYMMDD-HHMM';
-- Si no hay fila o cycle_id_anterior es NULL → primer ciclo → recuperado = 0 (correcto)
-- PDF muestra: "S/ X,XXX / US$ X,XXX" con "N docs · Tasa: X.X% · Meta: 55%"
-- La tasa = docs_recuperados / docs_total_ciclo_anterior * 100


-- ③ TARJETA 3: SALDO PENDIENTE
--    = cartera_vencida_sol  −  recuperado_sol
--    Se deriva de las tarjetas 1 y 2 — no hay query directa; es cálculo de la app.
-- Fórmula: saldo_pendiente = MAX(cartera_vencida_sol - recuperado_sol, 0)
-- También se muestra: clientes activos + cuántos están en Legal (ESCALAR_LEGAL)
SELECT COUNT(DISTINCT cliente_id) AS derivados_a_legal
FROM gestiones
WHERE cycle_id  = 'CIC-YYYYMMDD-HHMM'
  AND resultado = 'ESCALAR_LEGAL';


-- ④ TARJETA 4: EN ACUERDOS DE PAGO
SELECT
    COUNT(*)              AS acuerdos_totales_ciclo,
    COUNT(*) FILTER (WHERE estado = 'ACTIVO')   AS acuerdos_activos,
    SUM(monto_total)      AS monto_comprometido_sol
FROM acuerdos_pago
WHERE ciclo_id = 'CIC-YYYYMMDD-HHMM';   -- ← OJO: ciclo_id, NO cycle_id
-- PDF muestra: "S/ X,XXX" (monto_comprometido) y "N acuerdo(s) activo(s)"


-- ===========================================================================
-- SECCIÓN B — Distribución de Cartera por Antigüedad de Deuda (Aging)
-- ===========================================================================
-- La app agrupa por CLIENTE ÚNICO usando la mora MÁXIMA de sus documentos.
-- Los buckets son: 0-14 (BAJO), 15-30 (MEDIO), 31-60 (ALTO), 61+ (CRÍTICO).

-- ⑤ Aging por cliente único — mora máxima y saldo acumulado
WITH cliente_mora AS (
    SELECT
        cod_cliente,
        MAX(CAST(NULLIF(dias_mora, '') AS INTEGER))   AS mora_max,
        SUM(saldo_real) FILTER (
            WHERE moneda NOT IN ('USD','US$','$','DOLARES','DÓLARES')
        )                                              AS saldo_sol,
        SUM(saldo_real) FILTER (
            WHERE moneda IN ('USD','US$','$','DOLARES','DÓLARES')
        )                                              AS saldo_usd
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'
      AND tipo_pedido NOT IN ('DSP','PAV')
    GROUP BY cod_cliente
),
total AS (
    SELECT SUM(saldo_sol) AS total_sol FROM cliente_mora
)
SELECT
    CASE
        WHEN mora_max BETWEEN 0  AND 14  THEN '🟢 0 – 14 días'
        WHEN mora_max BETWEEN 15 AND 30  THEN '🟡 15 – 30 días'
        WHEN mora_max BETWEEN 31 AND 60  THEN '🟠 31 – 60 días'
        ELSE                                  '🔴 Más de 60 días'
    END                                                     AS segmento,
    CASE
        WHEN mora_max BETWEEN 0  AND 14  THEN 'BAJO'
        WHEN mora_max BETWEEN 15 AND 30  THEN 'MEDIO'
        WHEN mora_max BETWEEN 31 AND 60  THEN 'ALTO'
        ELSE                                  'CRÍTICO'
    END                                                     AS riesgo,
    COUNT(*)                                                AS clientes,
    ROUND(COALESCE(SUM(saldo_sol), 0)::NUMERIC, 2)         AS saldo_sol,
    ROUND(COALESCE(SUM(saldo_usd), 0)::NUMERIC, 2)         AS saldo_usd,
    ROUND(COALESCE(SUM(saldo_sol), 0) / NULLIF(MAX(t.total_sol), 0) * 100, 1)
                                                            AS pct_sol
FROM cliente_mora, total t
GROUP BY segmento, riesgo
ORDER BY MIN(mora_max);
-- PDF muestra esta misma tabla con colores por riesgo.


-- ===========================================================================
-- SECCIÓN C — Clientes Críticos (mora > 60 días)
-- ===========================================================================

-- ⑥ Top clientes con mora > 60 días (misma lógica que get_top_clientes_criticos)
SELECT
    dc.cod_cliente                                          AS cliente_id,
    MAX(dc.empresa)                                         AS nombre,
    MAX(CAST(NULLIF(dc.dias_mora, '') AS INTEGER))          AS dias_mora_max,
    ROUND(COALESCE(SUM(dc.saldo_real) FILTER (
        WHERE dc.moneda NOT IN ('USD','US$','$','DOLARES','DÓLARES')
    ), 0)::NUMERIC, 2)                                      AS saldo_sol,
    ROUND(COALESCE(SUM(dc.saldo_real) FILTER (
        WHERE dc.moneda IN ('USD','US$','$','DOLARES','DÓLARES')
    ), 0)::NUMERIC, 2)                                      AS saldo_usd,
    COUNT(DISTINCT g.id)                                    AS gestiones_count
FROM documentos_ciclo dc
LEFT JOIN gestiones g
       ON g.cliente_id = dc.cod_cliente
      AND g.cycle_id   = dc.cycle_id
WHERE dc.cycle_id   = 'CIC-YYYYMMDD-HHMM'
  AND dc.tipo_pedido NOT IN ('DSP','PAV')
  AND CAST(NULLIF(dc.dias_mora, '') AS INTEGER) > 60
GROUP BY dc.cod_cliente
ORDER BY saldo_sol DESC NULLS LAST
LIMIT 8;
-- PDF muestra: # · Cliente · Días mora · Saldo S/ · Saldo US$ · Gestiones · Recomendación


-- ===========================================================================
-- SECCIÓN D — Resumen de Gestiones del Período
-- ===========================================================================

-- ⑦ Conteo por canal y tipo de registro
SELECT
    tipo_registro,
    tipo_gestion,
    COUNT(*)  AS registros
FROM gestiones
WHERE cycle_id = 'CIC-YYYYMMDD-HHMM'
GROUP BY tipo_registro, tipo_gestion
ORDER BY tipo_registro, tipo_gestion;
-- PDF mapea:
--   ENVIO  / WHATSAPP → "WA enviados (masivo)"
--   ENVIO  / EMAIL    → "Emails enviados"
--   GESTION/ LLAMADA  → "Llamadas registradas"
--   GESTION/ VISITA   → "Visitas presenciales"
--   GESTION/ NOTA     → "Notas y observaciones"
--   GESTION/ OTRO     → incluido en "otros" (no mostrado por separado en PDF)

-- ⑧ Resultados de gestión (derivados a legal y exitosos)
SELECT
    resultado,
    COUNT(*) AS cantidad
FROM gestiones
WHERE cycle_id = 'CIC-YYYYMMDD-HHMM'
  AND resultado IN ('ESCALAR_LEGAL','EXITOSO','PROMESA_PAGO')
GROUP BY resultado;
-- PDF: legal = ESCALAR_LEGAL, exitosos = EXITOSO + PROMESA_PAGO

-- ⑨ Acuerdos de pago del ciclo (sección "Acuerdos de Pago" columna derecha)
SELECT
    COUNT(*)                                          AS acuerdos_firmados,
    COUNT(*) FILTER (WHERE estado = 'ACTIVO')         AS acuerdos_activos,
    ROUND(COALESCE(SUM(monto_total), 0)::NUMERIC, 2) AS monto_comprometido_sol
FROM acuerdos_pago
WHERE ciclo_id = 'CIC-YYYYMMDD-HHMM';   -- ← OJO: ciclo_id, NO cycle_id

-- ⑩ Cuotas cobradas de esos acuerdos
SELECT
    ROUND(COALESCE(SUM(ca.monto_cuota), 0)::NUMERIC, 2)  AS cuotas_pagadas_sol,
    COUNT(*)                                               AS cuotas_pagadas_count
FROM cuotas_acuerdo ca
INNER JOIN acuerdos_pago ap ON ca.acuerdo_id = ap.id
WHERE ap.ciclo_id = 'CIC-YYYYMMDD-HHMM'
  AND ca.estado   = 'PAGADA';


-- ===========================================================================
-- RESUMEN EJECUTIVO — Todos los indicadores del informe en una sola vista
-- ===========================================================================

WITH
-- Base aging
docs_validos AS (
    SELECT cod_cliente, saldo_real, moneda,
           CAST(NULLIF(dias_mora, '') AS INTEGER) AS dias_mora
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'
      AND tipo_pedido NOT IN ('DSP','PAV')
),
cliente_mora AS (
    SELECT cod_cliente,
           MAX(dias_mora)                            AS mora_max,
           SUM(saldo_real) FILTER (WHERE moneda NOT IN ('USD','US$','$','DOLARES','DÓLARES')) AS saldo_sol,
           SUM(saldo_real) FILTER (WHERE moneda IN    ('USD','US$','$','DOLARES','DÓLARES'))  AS saldo_usd
    FROM docs_validos
    GROUP BY cod_cliente
),
-- Acuerdos
acuerdos AS (
    SELECT ap.id, ap.monto_total, ap.estado
    FROM acuerdos_pago ap
    WHERE ap.ciclo_id = 'CIC-YYYYMMDD-HHMM'
),
-- Cuotas cobradas
cuotas AS (
    SELECT COALESCE(SUM(ca.monto_cuota), 0) AS total_cobrado
    FROM cuotas_acuerdo ca
    INNER JOIN acuerdos a ON ca.acuerdo_id = a.id
    WHERE ca.estado = 'PAGADA'
),
-- Gestiones
gest AS (
    SELECT tipo_registro, tipo_gestion, resultado
    FROM gestiones
    WHERE cycle_id = 'CIC-YYYYMMDD-HHMM'
)
SELECT
    -- === Sección A ===
    ROUND(COALESCE(SUM(cm.saldo_sol), 0)::NUMERIC, 2)               AS "A1_cartera_total_sol",
    ROUND(COALESCE(SUM(cm.saldo_usd), 0)::NUMERIC, 2)               AS "A1_cartera_total_usd",
    COUNT(DISTINCT cm.cod_cliente)                                   AS "A1_clientes_activos",
    ROUND((SELECT total_cobrado FROM cuotas)::NUMERIC, 2)            AS "A2_recuperado_sol",
    ROUND(
        GREATEST(
            COALESCE(SUM(cm.saldo_sol), 0)
            - (SELECT total_cobrado FROM cuotas), 0
        )::NUMERIC, 2
    )                                                                AS "A3_saldo_pendiente_sol",
    (SELECT COUNT(*) FROM acuerdos WHERE estado = 'ACTIVO')          AS "A4_acuerdos_activos",
    ROUND(COALESCE((SELECT SUM(monto_total) FROM acuerdos), 0)::NUMERIC, 2)
                                                                     AS "A4_monto_acuerdos_sol",
    -- === Sección D — Canales ===
    COUNT(*) FILTER (
        WHERE g.tipo_registro = 'ENVIO' AND g.tipo_gestion = 'WHATSAPP'
    ) OVER ()                                                        AS "D_wa_envios",
    COUNT(*) FILTER (
        WHERE g.tipo_registro = 'ENVIO' AND g.tipo_gestion = 'EMAIL'
    ) OVER ()                                                        AS "D_email_envios",
    COUNT(*) FILTER (
        WHERE g.tipo_gestion = 'LLAMADA'
    ) OVER ()                                                        AS "D_llamadas",
    COUNT(*) FILTER (
        WHERE g.tipo_gestion = 'VISITA'
    ) OVER ()                                                        AS "D_visitas",
    COUNT(*) FILTER (
        WHERE g.resultado = 'ESCALAR_LEGAL'
    ) OVER ()                                                        AS "D_legal",
    COUNT(*) FILTER (
        WHERE g.resultado IN ('EXITOSO','PROMESA_PAGO')
    ) OVER ()                                                        AS "D_exitosos"
FROM cliente_mora cm, gest g
GROUP BY g.tipo_registro, g.tipo_gestion, g.resultado
LIMIT 1;
-- Si la consulta anterior falla por el CROSS JOIN, usar las queries individuales (① al ⑩).
-- Las queries individuales son más claras para validar valor a valor.


-- ===========================================================================
-- DIAGNÓSTICO: tabla acuerdos_pago — verificar campo ciclo_id vs cycle_id
-- ===========================================================================
-- TRAMPA CRÍTICA: la tabla acuerdos_pago usa 'ciclo_id' (NO 'cycle_id').
-- Si el ciclo no aparece aquí, verifica que el ciclo_id coincida exactamente.
SELECT ciclo_id, estado, COUNT(*) AS cantidad, SUM(monto_total) AS monto_total
FROM acuerdos_pago
GROUP BY ciclo_id, estado
ORDER BY ciclo_id DESC;
