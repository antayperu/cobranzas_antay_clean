-- =============================================================================
-- DATA RECONCILIATION — Informe Gerencial para Comité de Directorio (RC-FEAT-039)
-- =============================================================================
-- Propósito : Validar que los números del PDF "Informe Gerencial" coincidan
--             exactamente con la base de datos (Supabase).
-- Uso       : Ejecutar en Supabase SQL Editor (staging o producción).
--
-- PASO 1: Reemplazar 'CIC-YYYYMMDD-HHMM' con el ciclo analizado.
-- PASO 2: Elegir el SCOPE según la vista del informe:
--           • Cartera Activa  → descomentar:   AND enviar_email = 'SI'
--           • Cartera General → dejar comentado: AND enviar_email = 'SI'
--
-- Lógica de la app:
--   - Aging    : por CLIENTE ÚNICO (mora máxima), no por documento.
--   - Saldos   : SUM(saldo_real) por moneda, excluye tipo_pedido IN ('DSP','PAV').
--   - Gestiones: filtradas por cycle_id + scope (solo_notificable).
--   - Acuerdos : tabla acuerdos_pago usa ciclo_id (NO cycle_id) — trampa crítica.
--   - Cuotas   : cuotas_acuerdo JOIN acuerdos_pago WHERE ciclo_id = X AND estado='PAGADA'.
-- =============================================================================


-- ===========================================================================
-- SECCIÓN 0 — DIAGNÓSTICO PREVIO: ¿qué ciclos y scopes hay disponibles?
-- ===========================================================================

-- 0a. Ciclos disponibles
SELECT cycle_id, row_count, created_at
FROM ciclos_procesamiento
ORDER BY created_at DESC;

-- 0b. ¿Cuántos clientes notificables vs. total en el ciclo?
SELECT
    COUNT(DISTINCT cod_cliente)                                   AS total_clientes,
    COUNT(DISTINCT cod_cliente) FILTER (WHERE enviar_email = 'SI') AS cartera_activa,
    COUNT(DISTINCT cod_cliente) FILTER (WHERE enviar_email != 'SI'
        OR enviar_email IS NULL)                                   AS cartera_especiales
FROM documentos_ciclo
WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'
  AND tipo_pedido NOT IN ('DSP','PAV');
-- Cartera Activa  = clientes con enviar_email = 'SI'
-- Cartera General = total_clientes

-- 0c. Estado de resumen_ciclo (fuente del "Recuperado en el Período")
SELECT
    cycle_id, cycle_id_anterior,
    clientes_total, docs_recuperados,
    monto_recuperado_sol, monto_recuperado_usd,
    tasa_recuperacion, updated_at
FROM resumen_ciclo
WHERE cycle_id = 'CIC-YYYYMMDD-HHMM';
-- Si vacío → el lazy reconciliation se ejecutará al generar el PDF por primera vez.


-- ===========================================================================
-- SECCIÓN A — Semáforo Ejecutivo (4 tarjetas)
-- ===========================================================================

-- ① TARJETA 1: CARTERA VENCIDA TOTAL
--    Cartera Activa  → agregar: AND enviar_email = 'SI'
--    Cartera General → sin filtro adicional
SELECT
    SUM(saldo_real) FILTER (WHERE moneda NOT IN ('USD','US$','$','DOLARES','DÓLARES'))
                                    AS cartera_vencida_sol,
    SUM(saldo_real) FILTER (WHERE moneda IN ('USD','US$','$','DOLARES','DÓLARES'))
                                    AS cartera_vencida_usd,
    COUNT(DISTINCT cod_cliente)     AS clientes_activos
FROM documentos_ciclo
WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'
  AND tipo_pedido NOT IN ('DSP','PAV')
  -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
;
-- PDF muestra: "S/ X,XXX" (sol) y "N clientes activos" ó "US$ X,XXX" si existe deuda USD


-- ② TARJETA 2: RECUPERADO EN EL PERÍODO
--    Fuente: resumen_ciclo (comparación CxC entre ciclos, nivel de ciclo completo).
--    Este valor es el mismo para Cartera Activa y Cartera General.
SELECT
    monto_recuperado_sol,
    monto_recuperado_usd,
    docs_recuperados,
    tasa_recuperacion,
    cycle_id_anterior
FROM resumen_ciclo
WHERE cycle_id = 'CIC-YYYYMMDD-HHMM';
-- Si no hay fila → lazy reconciliation pendiente (generar el PDF una vez para activarlo)
-- PDF muestra: "S/ X,XXX / US$ X,XXX" con "N docs · Tasa: X.X% · Meta: 55%"


-- ③ TARJETA 3: SALDO PENDIENTE
--    = cartera_vencida_sol − recuperado_sol (calculado por la app, no hay query directa)
-- Sub-métrica: clientes derivados a legal (misma lógica de scope que gestiones)
WITH clientes_scope AS (
    SELECT DISTINCT cod_cliente
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'
    -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
)
SELECT COUNT(DISTINCT g.cliente_id) AS derivados_a_legal
FROM gestiones g
INNER JOIN clientes_scope cs ON cs.cod_cliente = g.cliente_id
WHERE g.cycle_id  = 'CIC-YYYYMMDD-HHMM'
  AND g.resultado = 'ESCALAR_LEGAL';


-- ④ TARJETA 4: EN ACUERDOS DE PAGO
--    Cartera Activa  → filtra acuerdos de clientes con enviar_email = 'SI'
--    Cartera General → todos los acuerdos del ciclo
WITH clientes_scope AS (
    SELECT DISTINCT cod_cliente
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'
    -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
)
SELECT
    COUNT(ap.id)                                                  AS acuerdos_totales_ciclo,
    COUNT(ap.id) FILTER (WHERE ap.estado = 'ACTIVO')              AS acuerdos_activos,
    ROUND(COALESCE(SUM(ap.monto_total), 0)::NUMERIC, 2)           AS monto_comprometido_sol
FROM acuerdos_pago ap
INNER JOIN clientes_scope cs ON cs.cod_cliente = ap.cliente_id
WHERE ap.ciclo_id = 'CIC-YYYYMMDD-HHMM';  -- ← OJO: ciclo_id, NO cycle_id
-- PDF muestra: "S/ X,XXX" (monto_comprometido) y "N acuerdo(s) activo(s)"


-- ===========================================================================
-- SECCIÓN B — Distribución de Cartera por Antigüedad de Deuda (Aging)
-- ===========================================================================
-- La app agrupa por CLIENTE ÚNICO usando la mora MÁXIMA de sus documentos.
-- Buckets: 0-14 (BAJO), 15-30 (MEDIO), 31-60 (ALTO), 61+ (CRÍTICO).

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
      -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
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

-- ⑥ Top clientes con mora > 60 días
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
  -- AND dc.enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
GROUP BY dc.cod_cliente
ORDER BY saldo_sol DESC NULLS LAST
LIMIT 8;
-- PDF muestra: # · Cliente · Días mora · Saldo S/ · Saldo US$ · Gestiones · Recomendación


-- ===========================================================================
-- SECCIÓN D — Resumen de Gestiones del Período
-- ===========================================================================

-- ⑦ Conteo por canal y tipo de registro
--    Cartera Activa  → solo gestiones de clientes con enviar_email = 'SI'
--    Cartera General → todas las gestiones del ciclo
WITH clientes_scope AS (
    SELECT DISTINCT cod_cliente
    FROM documentos_ciclo
    WHERE cycle_id = 'CIC-YYYYMMDD-HHMM'
    -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
)
SELECT
    g.tipo_registro,
    g.tipo_gestion,
    COUNT(*) AS registros
FROM gestiones g
INNER JOIN clientes_scope cs ON cs.cod_cliente = g.cliente_id
WHERE g.cycle_id = 'CIC-YYYYMMDD-HHMM'
GROUP BY g.tipo_registro, g.tipo_gestion
ORDER BY g.tipo_registro, g.tipo_gestion;
-- PDF mapea:
--   ENVIO  / WHATSAPP → "WA enviados (masivo)"
--   ENVIO  / EMAIL    → "Emails enviados"
--   GESTION/ LLAMADA  → "Llamadas registradas"
--   GESTION/ VISITA   → "Visitas presenciales"
--   GESTION/ NOTA     → "Notas y observaciones"

-- ⑧ Resultados de gestión (derivados a legal y exitosos)
WITH clientes_scope AS (
    SELECT DISTINCT cod_cliente
    FROM documentos_ciclo
    WHERE cycle_id = 'CIC-YYYYMMDD-HHMM'
    -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
)
SELECT
    g.resultado,
    COUNT(*) AS cantidad
FROM gestiones g
INNER JOIN clientes_scope cs ON cs.cod_cliente = g.cliente_id
WHERE g.cycle_id  = 'CIC-YYYYMMDD-HHMM'
  AND g.resultado IN ('ESCALAR_LEGAL','EXITOSO','PROMESA_PAGO')
GROUP BY g.resultado;
-- PDF: legal = ESCALAR_LEGAL, exitosos = EXITOSO + PROMESA_PAGO

-- ⑨ Acuerdos de pago del ciclo
WITH clientes_scope AS (
    SELECT DISTINCT cod_cliente
    FROM documentos_ciclo
    WHERE cycle_id = 'CIC-YYYYMMDD-HHMM'
    -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
)
SELECT
    COUNT(ap.id)                                              AS acuerdos_firmados,
    COUNT(ap.id) FILTER (WHERE ap.estado = 'ACTIVO')          AS acuerdos_activos,
    ROUND(COALESCE(SUM(ap.monto_total), 0)::NUMERIC, 2)       AS monto_comprometido_sol
FROM acuerdos_pago ap
INNER JOIN clientes_scope cs ON cs.cod_cliente = ap.cliente_id
WHERE ap.ciclo_id = 'CIC-YYYYMMDD-HHMM';   -- ← OJO: ciclo_id, NO cycle_id

-- ⑩ Cuotas cobradas de esos acuerdos
WITH clientes_scope AS (
    SELECT DISTINCT cod_cliente
    FROM documentos_ciclo
    WHERE cycle_id = 'CIC-YYYYMMDD-HHMM'
    -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
)
SELECT
    ROUND(COALESCE(SUM(ca.monto_cuota), 0)::NUMERIC, 2)  AS cuotas_pagadas_sol,
    COUNT(*)                                               AS cuotas_pagadas_count
FROM cuotas_acuerdo ca
INNER JOIN acuerdos_pago ap ON ca.acuerdo_id = ap.id
INNER JOIN clientes_scope cs ON cs.cod_cliente = ap.cliente_id
WHERE ap.ciclo_id = 'CIC-YYYYMMDD-HHMM'
  AND ca.estado   = 'PAGADA';


-- ===========================================================================
-- DIAGNÓSTICO: tabla acuerdos_pago — verificar campo ciclo_id vs cycle_id
-- ===========================================================================
SELECT ciclo_id, estado, COUNT(*) AS cantidad, SUM(monto_total) AS monto_total
FROM acuerdos_pago
GROUP BY ciclo_id, estado
ORDER BY ciclo_id DESC;
