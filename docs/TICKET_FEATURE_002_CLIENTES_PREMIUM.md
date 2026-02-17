# TICKET FEATURE-002 - Clientes Premium

Fecha: 2026-02-17  
Estado: In Progress  
Prioridad: Alta

## Objetivo

Separar el mantenimiento de clientes en una TAB dedicada con experiencia premium, permitiendo:

1. Edicion total de registros/campos en `clientes`.
2. Migracion de cartera desde Excel.
3. Operacion principal con 2 archivos usando cartera maestra Supabase.

## Alcance Tecnico

1. Nueva TAB `6. Clientes Premium`.
2. Backend `db_manager` con:
   - listado full
   - update extendido
   - upsert masivo
   - delete controlado
   - migracion de cartera
3. Sidebar en modo recomendado de 2 archivos por defecto.

## Criterios de Aceptacion

1. Usuario puede editar cualquier campo en grilla y persistir cambios.
2. Usuario puede migrar cartera con feedback de errores.
3. Carga principal procesa con `CtasxCobrar + Cobranza` si existe cartera maestra.
4. Configuracion ya no duplica mantenimiento de clientes.

## Evidencia Esperada

1. `docs/FRD_CLIENTES_PREMIUM_v1.0.md`
2. `utils/ui/tabs/clientes_premium.py`
3. `tests/test_db_manager_clients.py`
