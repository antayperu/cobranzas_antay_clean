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
    clientes_total,
    -- Full recoveries (docs que desaparecieron)
    docs_recuperados,
    monto_recuperado_sol, monto_recuperado_usd,
    tasa_recuperacion,
    -- Amortizaciones parciales (RC-BUG-070)
    docs_amortizados,
    monto_amortizado_sol, monto_amortizado_usd,
    -- Cartera Activa
    docs_recuperados_activa,
    monto_recuperado_sol_activa,
    docs_amortizados_activa,
    monto_amortizado_sol_activa,
    updated_at
FROM resumen_ciclo
WHERE cycle_id = 'CIC-YYYYMMDD-HHMM';
-- Si vacío → el lazy reconciliation se ejecutará al generar el PDF por primera vez.
-- Si docs_amortizados = NULL → migración 104 no ejecutada aún en este ambiente.


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
--    Fuente: resumen_ciclo — diferencia CxC entre ciclo anterior y ciclo actual.
--    Cartera Activa  → columnas *_activa  (solo clientes con enviar_email = 'SI')
--    Cartera General → columnas sin sufijo (todos los clientes)
SELECT
    -- Cartera General (combinado: full recovery + amortizaciones)
    monto_recuperado_sol                AS recuperado_sol_general,
    monto_recuperado_usd                AS recuperado_usd_general,
    docs_recuperados                    AS docs_completos_general,
    docs_amortizados                    AS docs_amortizados_general,
    tasa_recuperacion                   AS tasa_general,
    -- Cartera Activa (solo enviar_email = 'SI')
    monto_recuperado_sol_activa         AS recuperado_sol_activa,
    monto_recuperado_usd_activa         AS recuperado_usd_activa,
    docs_recuperados_activa             AS docs_completos_activa,
    docs_amortizados_activa             AS docs_amortizados_activa,
    tasa_recuperacion_activa            AS tasa_activa,
    -- Detalle amortizaciones (auditoría RC-BUG-070)
    monto_amortizado_sol                AS amortizado_sol_general,
    monto_amortizado_usd                AS amortizado_usd_general,
    monto_amortizado_sol_activa         AS amortizado_sol_activa,
    monto_amortizado_usd_activa         AS amortizado_usd_activa,
    -- Referencia
    cycle_id_anterior
FROM resumen_ciclo
WHERE cycle_id = 'CIC-YYYYMMDD-HHMM';
-- Si no hay fila       → ejecutar primero: DELETE FROM resumen_ciclo WHERE cycle_id = '...'
--                        y luego generar el PDF (lazy reconciliation re-calcula).
-- Si activa = 0 y general > 0 → fila antigua sin columnas activa: repetir DELETE + PDF.
-- PDF Cartera Activa  muestra: recuperado_sol_activa / recuperado_usd_activa
-- PDF Cartera General muestra: recuperado_sol_general / recuperado_usd_general
--
-- VALIDACIÓN RC-BUG-070 (amortizaciones):
--   recuperado_sol_general = total_recuperado_sol (⑫) + total_amortizado_sol (⑭)
--   docs_completos_general + docs_amortizados_general = total de documentos con cobro parcial o total


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
-- SECCIÓN E — DETALLE DE DOCUMENTOS RECUPERADOS (validación Tarjeta 2)
-- ===========================================================================
-- Propósito: Listar uno a uno los documentos considerados "recuperados",
--            es decir, los que estaban en el ciclo ANTERIOR y ya NO aparecen
--            en el ciclo ACTUAL (el cliente los pagó en el ERP).
--            La suma de estos montos debe coincidir exactamente con
--            "RECUPERADO EN EL PERÍODO" del PDF.
--
-- Reemplazar también 'CIC-ANTERIOR-HHMM' con el cycle_id del ciclo previo
-- (ver columna cycle_id_anterior en la query ②).
-- ===========================================================================

-- ⑪ Documentos recuperados — detalle por documento
--    Cartera Activa  → descomentar: AND anterior.enviar_email = 'SI'
--    Cartera General → dejar comentado
WITH docs_anterior AS (
    SELECT match_key, cod_cliente, empresa, saldo_real, moneda, enviar_email
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-ANTERIOR-HHMM'       -- ← ciclo ANTERIOR
      AND tipo_pedido NOT IN ('DSP','PAV')
      -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
),
docs_actual AS (
    SELECT match_key
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'       -- ← ciclo ACTUAL
      AND tipo_pedido NOT IN ('DSP','PAV')
)
SELECT
    ant.cod_cliente                                         AS cliente_id,
    ant.empresa                                             AS nombre,
    ant.match_key,
    ant.moneda,
    ROUND(ant.saldo_real::NUMERIC, 2)                       AS monto_recuperado,
    ant.enviar_email
FROM docs_anterior ant
LEFT JOIN docs_actual act ON act.match_key = ant.match_key
WHERE act.match_key IS NULL          -- estaba antes, ya no está ahora = recuperado
ORDER BY ant.moneda, ant.saldo_real DESC;
-- Cada fila = un documento cobrado entre el ciclo anterior y el actual.
-- La suma de monto_recuperado (por moneda) debe igualar Tarjeta 2 del PDF.


-- ⑫ Totales de documentos recuperados — debe coincidir con resumen_ciclo
--    Cartera Activa  → descomentar: AND anterior.enviar_email = 'SI'
--    Cartera General → dejar comentado
WITH docs_anterior AS (
    SELECT match_key, saldo_real, moneda, enviar_email
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-ANTERIOR-HHMM'       -- ← ciclo ANTERIOR
      AND tipo_pedido NOT IN ('DSP','PAV')
      -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
),
docs_actual AS (
    SELECT match_key
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'       -- ← ciclo ACTUAL
      AND tipo_pedido NOT IN ('DSP','PAV')
)
SELECT
    COUNT(*)                                                             AS docs_recuperados,
    ROUND(COALESCE(SUM(ant.saldo_real) FILTER (
        WHERE ant.moneda NOT IN ('USD','US$','$','DOLARES','DÓLARES')
    ), 0)::NUMERIC, 2)                                                   AS total_recuperado_sol,
    ROUND(COALESCE(SUM(ant.saldo_real) FILTER (
        WHERE ant.moneda IN ('USD','US$','$','DOLARES','DÓLARES')
    ), 0)::NUMERIC, 2)                                                   AS total_recuperado_usd
FROM docs_anterior ant
LEFT JOIN docs_actual act ON act.match_key = ant.match_key
WHERE act.match_key IS NULL;
-- ✅ total_recuperado_sol debe igualar recuperado_sol_activa (o _general) de la query ②
-- ✅ total_recuperado_usd debe igualar recuperado_usd_activa (o _general) de la query ②
-- ✅ docs_recuperados    debe igualar docs_recuperados_activa (o _general) de la query ②


-- ===========================================================================
-- SECCIÓN F — DETALLE DE AMORTIZACIONES PARCIALES (RC-BUG-070)
-- ===========================================================================
-- Propósito: Listar los documentos que PERMANECEN entre ciclos pero con
--            saldo_real reducido (el cliente pagó parcialmente).
--            La suma de monto_amortizado + total_recuperado (⑫) debe igualar
--            el total de la Tarjeta 2 del PDF para el scope correspondiente.
--
-- NOTA: el umbral de 0.01 evita ruido de redondeo (igual al usado en Python).
-- ===========================================================================

-- ⑬ Amortizaciones parciales — detalle por documento
--    Cartera Activa  → descomentar: AND anterior.enviar_email = 'SI'
--    Cartera General → dejar comentado
WITH docs_anterior AS (
    SELECT match_key, cod_cliente, empresa, saldo_real, moneda, enviar_email
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-ANTERIOR-HHMM'       -- ← ciclo ANTERIOR
      AND tipo_pedido NOT IN ('DSP','PAV')
      -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
),
docs_actual AS (
    SELECT match_key, saldo_real
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'       -- ← ciclo ACTUAL
      AND tipo_pedido NOT IN ('DSP','PAV')
)
SELECT
    ant.cod_cliente                                               AS cliente_id,
    ant.empresa                                                   AS nombre,
    ant.match_key,
    ant.moneda,
    ROUND(ant.saldo_real::NUMERIC, 2)                            AS saldo_anterior,
    ROUND(act.saldo_real::NUMERIC, 2)                            AS saldo_actual,
    ROUND((ant.saldo_real - act.saldo_real)::NUMERIC, 2)         AS monto_amortizado,
    ant.enviar_email
FROM docs_anterior ant
INNER JOIN docs_actual act ON act.match_key = ant.match_key
WHERE ant.saldo_real IS NOT NULL
  AND act.saldo_real IS NOT NULL
  AND (ant.saldo_real - act.saldo_real) > 0.01
ORDER BY ant.moneda, (ant.saldo_real - act.saldo_real) DESC;
-- Cada fila = un documento con pago parcial entre el ciclo anterior y el actual.


-- ⑭ Totales de amortizaciones — para validar con resumen_ciclo y Tarjeta 2
--    Cartera Activa  → descomentar: AND anterior.enviar_email = 'SI'
--    Cartera General → dejar comentado
WITH docs_anterior AS (
    SELECT match_key, saldo_real, moneda, enviar_email
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-ANTERIOR-HHMM'       -- ← ciclo ANTERIOR
      AND tipo_pedido NOT IN ('DSP','PAV')
      -- AND enviar_email = 'SI'   ← DESCOMENTAR para Cartera Activa
),
docs_actual AS (
    SELECT match_key, saldo_real
    FROM documentos_ciclo
    WHERE cycle_id   = 'CIC-YYYYMMDD-HHMM'       -- ← ciclo ACTUAL
      AND tipo_pedido NOT IN ('DSP','PAV')
)
SELECT
    COUNT(*)                                                              AS docs_amortizados,
    ROUND(COALESCE(SUM(ant.saldo_real - act.saldo_real) FILTER (
        WHERE ant.moneda NOT IN ('USD','US$','$','DOLARES','DÓLARES')
    ), 0)::NUMERIC, 2)                                                    AS total_amortizado_sol,
    ROUND(COALESCE(SUM(ant.saldo_real - act.saldo_real) FILTER (
        WHERE ant.moneda IN ('USD','US$','$','DOLARES','DÓLARES')
    ), 0)::NUMERIC, 2)                                                    AS total_amortizado_usd
FROM docs_anterior ant
INNER JOIN docs_actual act ON act.match_key = ant.match_key
WHERE ant.saldo_real IS NOT NULL
  AND act.saldo_real IS NOT NULL
  AND (ant.saldo_real - act.saldo_real) > 0.01;
-- ✅ total_amortizado_sol + recuperado total_recuperado_sol (⑫) = monto_recuperado_sol de ②
-- ✅ total_amortizado_usd + total_recuperado_usd (⑫)           = monto_recuperado_usd de ②
-- ✅ docs_amortizados debe igualar docs_amortizados en resumen_ciclo (columnas de migración 104)


-- ===========================================================================
-- DIAGNÓSTICO: tabla acuerdos_pago — verificar campo ciclo_id vs cycle_id
-- ===========================================================================
SELECT ciclo_id, estado, COUNT(*) AS cantidad, SUM(monto_total) AS monto_total
FROM acuerdos_pago
GROUP BY ciclo_id, estado
ORDER BY ciclo_id DESC;
