# TICKET FEATURE-002 - Clientes Premium + Home 2 Archivos

Fecha: 2026-02-19  
Estado: In Progress  
Prioridad: Alta  
Referencia FRD: `docs/FRD_CLIENTES_PREMIUM_v1.0.md`

## Objetivo

Completar la separacion operativa:

1. Home principal solo procesa con `CtasxCobrar + Cobranza`.
2. Clientes se gestionan en TAB independiente `Clientes Premium`.
3. UI principal adopta un patron corporativo premium alineado a Antay.

## Subtickets generados

1. `FEATURE-004`: Home operativo estricto de 2 archivos.
2. `FEATURE-005`: Rediseno UX corporativo premium (sidebar + bienvenida).

## Alcance tecnico

1. `app.py`
   - Eliminar dependencia de uploader de cartera en el flujo principal.
   - Consumir cartera maestra desde Supabase por defecto.
2. `utils/ui/sidebar.py`
   - Mantener solo 2 uploaders.
   - Mensajeria operativa clara hacia `Clientes Premium`.
3. `utils/session.py`
   - Alinear estado de `uploaded_files` al nuevo flujo.
4. `utils/ui/styles.py`
   - Upgrade visual premium para sidebar, acciones y bienvenida.
5. Documentacion
   - FRD + backlog + tickets sincronizados con el nuevo proceso.

## Criterios de aceptacion

1. No existe uploader de cartera en Home.
2. El ciclo corre con 2 archivos y cartera maestra Supabase.
3. Si no hay cartera maestra, la app bloquea y guia al tab correcto.
4. La UI principal comunica visualmente el flujo corporativo de forma clara.
5. `Clientes Premium` sigue siendo la unica via de mantenimiento/migracion de clientes.

## Evidencia esperada

1. `docs/FRD_CLIENTES_PREMIUM_v1.0.md`
2. `docs/backlog_priorizado.md`
3. `app.py`
4. `utils/ui/sidebar.py`
5. `utils/ui/styles.py`
