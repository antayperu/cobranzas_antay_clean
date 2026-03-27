# TICKET FEATURE-004 - Home Operativo Estricto (2 Archivos)

Fecha: 2026-02-19  
Estado: In Progress  
Prioridad: Critica  
Owner: Antigravity

## Objetivo

Formalizar y ejecutar el flujo principal con solo 2 archivos:

1. `CtasxCobrar`
2. `Cobranza`

La cartera debe tomarse exclusivamente desde Supabase en el ciclo principal.

## Alcance

1. Eliminar uploader de cartera en sidebar principal.
2. Mantener validacion de procesamiento basada solo en 2 archivos.
3. Bloquear proceso cuando no exista cartera maestra.
4. Mostrar instruccion clara hacia TAB `Clientes Premium`.

## Criterios de aceptacion

1. No hay uploader de `Cartera` en Home.
2. `Procesar y validar` solo requiere `CtasxCobrar` y `Cobranza`.
3. El procesamiento usa cartera maestra de Supabase en todos los casos.
4. Si falta cartera maestra, se informa error operativo accionable.

## Entregables

1. `app.py`
2. `utils/ui/sidebar.py`
3. `utils/session.py`
