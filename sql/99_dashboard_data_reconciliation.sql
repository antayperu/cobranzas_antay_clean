-- =============================================================================
-- DATA RECONCILIATION — Dashboard de Efectividad de Cobranza (RC-FEAT-038)
-- =============================================================================
-- Propósito : Validar que los números del TAB "Dashboard" coincidan
--             exactamente con la base de datos (Supabase).
-- Uso       : Ejecutar en Supabase SQL Editor (cobranzas-staging o producción).
-- Ciclo ref.: Reemplazar 'CIC-YYYYMMDD-HHMM' con el ciclo activo.
-- Período   : Ajustar las fechas según el selector de período que usaste en el Dashboard.
--
-- Última actualización:
--   - Funnel usa COUNT(DISTINCT cliente_id) — igual que la app
--   - Top Clientes excluye tipo_pedido IN ('DSP','PAV') — datos basura
--   - Top Clientes separa saldo y docs por moneda (SOL vs USD)
--   - tipo_notificacion = 'EMAIL' (ya no 'INFO'/'ALERTA')
--   - WA mensajes en gestiones (tipo_gestion='WHATSAPP'), no en notificaciones
--   - Fechas con sufijo -05:00 (Lima UTC-5) para comparar correctamente contra UTC almacenado
-- =============================================================================


-- ---------------------------------------------------------------------------
-- PASO 0 — Verificar ciclo activo y cartera
-- ---------------------------------------------------------------------------

-- ¿Qué ciclos existen?
SELECT cycle_id, created_at
FROM ciclos_procesamiento
ORDER BY created_at DESC
LIMIT 5;

-- ¿Cuántos documentos tiene el ciclo activo? (con y sin datos basura)
SELECT
    cycle_id,
    COUNT(*)                                                    AS total_documentos,
    COUNT(*) FILTER (WHERE tipo_pedido NOT IN ('DSP','PAV'))    AS docs_validos,
    COUNT(*) FILTER (WHERE tipo_pedido IN ('DSP','PAV'))        AS docs_basura,
    COUNT(DISTINCT cliente_id)
        FILTER (WHERE tipo_pedido NOT IN ('DSP','PAV'))         AS clientes_unicos_validos
FROM documentos_ciclo
GROUP BY cycle_id
ORDER BY cycle_id DESC;
-- Dashboard usa: clientes_unicos_validos en el Funnel
-- Dashboard usa: docs_validos para el Top Clientes


-- ---------------------------------------------------------------------------
-- PASO 1 — KPIs del Período
-- Corresponde al bloque "📊 KPIs del Período" del Dashboard.
-- Ajustar las fechas según el período seleccionado.
-- ---------------------------------------------------------------------------

-- ① Gestiones por resultado (últimos 7 días — ajustar fecha_desde)
--    IMPORTANTE: filtrar tipo_registro='GESTION' (solo acciones manuales del gestor).
--    Los envíos automáticos del sistema (tipo_registro='ENVIO') se cuentan en ②, no aquí.
SELECT
    resultado,
    COUNT(*)                              AS cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS porcentaje
FROM gestiones
WHERE tipo_registro = 'GESTION'
  AND fecha >= '2026-03-10T00:00:00-05:00'
  AND fecha <= '2026-03-17T23:59:59-05:00'
GROUP BY resultado
ORDER BY cantidad DESC;
-- Dashboard muestra: Gestiones totales = SUM, Acordaron pagar = EXITOSO,
-- Tasa de éxito = EXITOSO/total, Promesas = PROMESA_PAGO, Sin respuesta = SIN_RESPUESTA

-- ② Notificaciones — valores exactos de los KPIs del Período
--    tipo_notificacion ahora es el CANAL: 'EMAIL' o 'WHATSAPP' (ya no 'INFO'/'ALERTA')
--
--    CÓMO FUNCIONA LA APP:
--    - Filtra por fecha_envio dentro del período (los no enviados tienen fecha_envio=NULL → quedan fuera)
--    - NO filtra por estado='ENVIADO' explícitamente — el filtro de fecha lo hace implícito
--    - Cuenta filas (no clientes únicos) por tipo_notificacion

-- "📱 WA enviados"
--    Los WA se graban en gestiones (tipo_gestion='WHATSAPP', tipo_registro='ENVIO').
--    Los seguimientos manuales del gestor tienen tipo_registro='GESTION' y NO se cuentan aquí.
SELECT COUNT(*) AS wa_enviados
FROM gestiones
WHERE tipo_gestion  = 'WHATSAPP'
  AND tipo_registro = 'ENVIO'
  AND fecha >= '2026-03-10T00:00:00-05:00'
  AND fecha <= '2026-03-17T23:59:59-05:00';

-- "📧 Emails enviados"
SELECT COUNT(*) AS email_enviados
FROM notificaciones
WHERE tipo_notificacion = 'EMAIL'
  AND fecha_envio >= '2026-03-10T00:00:00-05:00'
  AND fecha_envio <= '2026-03-17T23:59:59-05:00';

-- "Tasa notif. exitosa" = ENVIADO / total notificaciones con fecha_envio en período
SELECT
    COUNT(*)                                                        AS total_con_fecha,
    COUNT(*) FILTER (WHERE estado = 'ENVIADO')                      AS enviadas,
    ROUND(COUNT(*) FILTER (WHERE estado = 'ENVIADO') * 100.0
          / NULLIF(COUNT(*), 0), 1)                                 AS tasa_pct
FROM notificaciones
WHERE fecha_envio >= '2026-03-10T00:00:00-05:00'
  AND fecha_envio <= '2026-03-17T23:59:59-05:00';

-- Vista consolidada de los 3 valores anteriores (diagnóstico rápido)
SELECT tipo_notificacion, estado, COUNT(*) AS cantidad
FROM notificaciones
WHERE fecha_envio >= '2026-03-10T00:00:00-05:00'
  AND fecha_envio <= '2026-03-17T23:59:59-05:00'
GROUP BY tipo_notificacion, estado
ORDER BY tipo_notificacion, estado;

-- ③ Acuerdos de pago activos (sin filtro de fecha — estado actual)
SELECT estado, COUNT(*) AS cantidad
FROM acuerdos_pago
GROUP BY estado;
-- Dashboard muestra: Acuerdos activos = estado = 'ACTIVO'


-- ---------------------------------------------------------------------------
-- PASO 2 — Funnel de Cobranza
-- Corresponde al bloque "🔽 Funnel de Cobranza" del Dashboard.
-- IMPORTANTE: el Dashboard cuenta CLIENTES ÚNICOS, no documentos ni filas.
-- ---------------------------------------------------------------------------

-- ④ Cartera total del ciclo (clientes únicos — excluye DSP y PAV)
SELECT
    COUNT(DISTINCT cliente_id) AS clientes_unicos,
    COUNT(*)                   AS documentos_total,
    COUNT(*) FILTER (WHERE tipo_pedido NOT IN ('DSP','PAV')) AS docs_validos
FROM documentos_ciclo
WHERE cycle_id = 'CIC-20260317-1547';
-- Dashboard muestra: Cartera total = clientes_unicos (excluye tipo_pedido DSP y PAV)

-- ⑤ Notificados WA en el ciclo (clientes únicos)
--    Los mensajes WA se graban en gestiones (tipo_gestion='WHATSAPP'), NO en notificaciones.
SELECT COUNT(DISTINCT cliente_id) AS notificados_wa_clientes_unicos
FROM gestiones
WHERE tipo_gestion = 'WHATSAPP'
  AND cycle_id = 'CIC-20260317-1547';

-- ⑥ Notificados Email en el ciclo (clientes únicos)
SELECT COUNT(DISTINCT cliente_id) AS notificados_email_clientes_unicos
FROM notificaciones
WHERE tipo_notificacion = 'EMAIL'
  AND estado = 'ENVIADO'
  AND cycle_id = 'CIC-20260317-1547';

-- ⑦ Con respuesta (clientes únicos con gestión positiva en el ciclo)
SELECT COUNT(DISTINCT cliente_id) AS con_respuesta_clientes_unicos
FROM gestiones
WHERE resultado IN ('EXITOSO', 'PROMESA_PAGO', 'SOLICITO_PLAZO', 'EN_NEGOCIACION')
  AND cycle_id = 'CIC-20260317-1547';

-- ⑧ Con acuerdo de pago en el ciclo
SELECT COUNT(*) AS con_acuerdo
FROM acuerdos_pago
WHERE estado = 'ACTIVO'
  AND ciclo_id = 'CIC-20260317-1547';

-- ⑨ Recuperados (clientes únicos con resultado EXITOSO en el ciclo — solo gestiones manuales)
SELECT COUNT(DISTINCT cliente_id) AS recuperados_clientes_unicos
FROM gestiones
WHERE resultado     = 'EXITOSO'
  AND tipo_registro = 'GESTION'
  AND cycle_id      = 'CIC-20260317-1547';


-- ---------------------------------------------------------------------------
-- PASO 3 — Distribución de Resultados
-- Corresponde al bloque "📈 Distribución de Resultados" del Dashboard.
-- ---------------------------------------------------------------------------

-- ⑩ Distribución completa de resultados (últimos 7 días — solo gestiones manuales)
SELECT
    resultado,
    COUNT(*)                              AS cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_del_total
FROM gestiones
WHERE tipo_registro = 'GESTION'
  AND fecha >= '2026-03-10T00:00:00-05:00'
  AND fecha <= '2026-03-17T23:59:59-05:00'
GROUP BY resultado
ORDER BY cantidad DESC;


-- ---------------------------------------------------------------------------
-- PASO 4 — Efectividad por Plantilla WhatsApp
-- Corresponde al bloque "📋 Efectividad por Plantilla WhatsApp" del Dashboard.
-- Requiere que metadata JSONB tenga el campo "template" o "plantilla".
-- ---------------------------------------------------------------------------

-- ⑪ Ver qué tiene el campo metadata en notificaciones WA
SELECT
    metadata->>'template'  AS plantilla_template,
    metadata->>'plantilla' AS plantilla_alt,
    estado,
    COUNT(*) AS cantidad
FROM notificaciones
WHERE tipo_notificacion = 'WHATSAPP'
  AND cycle_id = 'CIC-20260317-1547'
GROUP BY plantilla_template, plantilla_alt, estado
ORDER BY cantidad DESC;


-- ---------------------------------------------------------------------------
-- PASO 5 — Top Clientes por Saldo Pendiente
-- Corresponde al bloque "🔴 Top Clientes por Saldo Pendiente" del Dashboard.
-- REGLAS:
--   - Excluir tipo_pedido IN ('DSP','PAV') — son datos basura
--   - Separar saldo y docs por moneda (SOL vs USD)
--   - Ordenar por saldo en Soles (referencia principal)
-- ---------------------------------------------------------------------------

-- ⑫ Top 15 clientes — desglose por moneda (excluye DSP y PAV)
SELECT
    cliente_id,
    empresa                                                           AS nombre_cliente,
    SUM(saldo_real) FILTER (WHERE moneda LIKE 'S%')                  AS saldo_sol,
    COUNT(*)        FILTER (WHERE moneda LIKE 'S%')                  AS docs_sol,
    SUM(saldo_real) FILTER (WHERE moneda NOT LIKE 'S%')              AS saldo_usd,
    COUNT(*)        FILTER (WHERE moneda NOT LIKE 'S%')              AS docs_usd,
    MAX(CAST(NULLIF(dias_mora, '') AS INTEGER))                       AS dias_mora_max
FROM documentos_ciclo
WHERE cycle_id = 'CIC-20260317-1547'
  AND tipo_pedido NOT IN ('DSP', 'PAV')
GROUP BY cliente_id, empresa
ORDER BY saldo_sol DESC NULLS LAST
LIMIT 15;

-- ⑬ Último resultado y fecha de gestión por cliente
SELECT
    g.cliente_id,
    g.resultado,
    g.fecha                                                           AS fecha_ultimo_contacto
FROM gestiones g
INNER JOIN (
    SELECT cliente_id, MAX(fecha) AS ultima_fecha
    FROM gestiones
    WHERE cycle_id = 'CIC-20260317-1547'
    GROUP BY cliente_id
) ult ON g.cliente_id = ult.cliente_id AND g.fecha = ult.ultima_fecha
ORDER BY g.fecha DESC
LIMIT 15;

-- ⑭ Diagnóstico: ¿Cuántos documentos son basura en el ciclo?
SELECT
    tipo_pedido,
    COUNT(*)        AS documentos,
    SUM(saldo_real) AS saldo_total
FROM documentos_ciclo
WHERE cycle_id = 'CIC-20260317-1547'
GROUP BY tipo_pedido
ORDER BY documentos DESC;
-- Verifica que DSP y PAV aparezcan y estén excluidos del Top Clientes


-- ---------------------------------------------------------------------------
-- PASO 6 — Resumen de reconciliación (ejecutar todo junto para vista rápida)
-- ---------------------------------------------------------------------------

-- tipo_registro='GESTION' = acciones manuales del gestor (base de los KPIs de efectividad)
-- tipo_registro='ENVIO'   = envíos automáticos del sistema (base del KPI "WA enviados")
SELECT
    'gestiones_total'         AS indicador,
    COUNT(*)::TEXT            AS valor
FROM gestiones
WHERE tipo_registro = 'GESTION'
  AND fecha >= '2026-03-10T00:00:00-05:00' AND fecha <= '2026-03-17T23:59:59-05:00'

UNION ALL

SELECT 'exitosos', COUNT(*)::TEXT
FROM gestiones
WHERE resultado     = 'EXITOSO'
  AND tipo_registro = 'GESTION'
  AND fecha >= '2026-03-10T00:00:00-05:00' AND fecha <= '2026-03-17T23:59:59-05:00'

UNION ALL

SELECT 'sin_respuesta', COUNT(*)::TEXT
FROM gestiones
WHERE resultado     = 'SIN_RESPUESTA'
  AND tipo_registro = 'GESTION'
  AND fecha >= '2026-03-10T00:00:00-05:00' AND fecha <= '2026-03-17T23:59:59-05:00'

UNION ALL

-- WA enviados = envíos automáticos del sistema (tipo_registro='ENVIO')
-- Los seguimientos manuales del gestor son tipo_registro='GESTION' y van en gestiones_total
SELECT 'notif_wa_enviadas', COUNT(*)::TEXT
FROM gestiones
WHERE tipo_gestion  = 'WHATSAPP'
  AND tipo_registro = 'ENVIO'
  AND fecha >= '2026-03-10T00:00:00-05:00' AND fecha <= '2026-03-17T23:59:59-05:00'

UNION ALL

SELECT 'notif_email_enviadas', COUNT(*)::TEXT
FROM notificaciones
WHERE tipo_notificacion = 'EMAIL' AND estado = 'ENVIADO'
  AND fecha_envio >= '2026-03-10T00:00:00-05:00' AND fecha_envio <= '2026-03-17T23:59:59-05:00'

UNION ALL

SELECT 'acuerdos_activos', COUNT(*)::TEXT
FROM acuerdos_pago
WHERE estado = 'ACTIVO'

UNION ALL

-- Cartera: clientes únicos válidos (sin DSP ni PAV)
SELECT 'cartera_ciclo_clientes_unicos', COUNT(DISTINCT cliente_id)::TEXT
FROM documentos_ciclo
WHERE cycle_id = 'CIC-20260317-1547'
  AND tipo_pedido NOT IN ('DSP', 'PAV')

UNION ALL

SELECT 'top_clientes_saldo_sol', ROUND(SUM(saldo_real))::TEXT
FROM documentos_ciclo
WHERE cycle_id = 'CIC-20260317-1547'
  AND tipo_pedido NOT IN ('DSP', 'PAV')
  AND moneda LIKE 'S%'

UNION ALL

SELECT 'top_clientes_saldo_usd', ROUND(SUM(saldo_real))::TEXT
FROM documentos_ciclo
WHERE cycle_id = 'CIC-20260317-1547'
  AND tipo_pedido NOT IN ('DSP', 'PAV')
  AND moneda NOT LIKE 'S%';
