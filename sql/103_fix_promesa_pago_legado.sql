-- =============================================================================
-- CORRECCIÓN: PROMESA_PAGO → es_legado = TRUE
-- =============================================================================
-- Problema: PROMESA_PAGO fue insertado con es_legado=FALSE, por lo que aparece
-- en los selectores de nueva gestión junto a EXITOSO ("Acordó pagar"), generando
-- ambigüedad. En la práctica toda promesa de pago incluye una fecha acordada,
-- por lo que ambos códigos significan lo mismo. PROMESA_PAGO es legado.
--
-- Uso: Ejecutar en Supabase SQL Editor (staging primero, luego producción).
-- =============================================================================

UPDATE catalogo_resultados
SET
    es_legado = TRUE,
    orden     = 93
WHERE codigo = 'PROMESA_PAGO';

-- Verificación — PROMESA_PAGO debe aparecer con es_legado=TRUE
SELECT codigo, etiqueta, activo, es_legado, orden
FROM catalogo_resultados
ORDER BY es_legado, orden;
-- Resultado esperado: 7 filas con es_legado=FALSE, 3 con es_legado=TRUE
-- PROMESA_PAGO debe estar en el grupo es_legado=TRUE con orden=93
