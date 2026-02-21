# Evidencia Mantenimiento de Clientes - SUPABASE-MIG-005

Fecha: 2026-02-17  
Ticket: SUPABASE-MIG-005  
Objetivo: editar telefono/email/estado de cliente desde la app sin recargar Excel.

---

## 1) Implementacion

1. Capa de datos (`db_manager`):
   - `list_clientes_for_admin(search, limit)`
   - `update_cliente_fields(cliente_id, email, telefono, estado)`
2. UI en Configuracion:
   - Nueva seccion `Mantenimiento de Clientes (Supabase)` con:
     - busqueda por codigo/nombre/correo
     - seleccion de cliente
     - edicion de correo, telefono y estado
     - guardado directo en Supabase
3. Refresco en sesion:
   - al guardar, se actualizan columnas de `df_final` en memoria (`CORREO`, `EMAIL_FINAL`, `TELÉFONO`) cuando existe dataset cargado.

---

## 2) Persistencia y auditoria minima

1. Update persistente en `public.clientes` por `cliente_id`.
2. Auditoria minima:
   - columna `updated_at` en tabla `clientes`.
   - trigger `update_clientes_updated_at` (definido en SQL base) actualiza timestamp en cada cambio.

---

## 3) Validacion automatizada

Comandos:

```powershell
pytest tests/test_db_manager_clients.py -q -p no:cacheprovider
pytest tests/test_db_manager_clients.py tests/test_migration_integrity.py tests/test_db_manager_notifications.py tests/test_export_parity.py tests/test_processing_calculation_parity.py tests/test_supabase_cycle_service.py tests/test_ui_init.py -q -p no:cacheprovider
```

Resultados:

1. `tests/test_db_manager_clients.py` -> 3 passed
2. Suite consolidada objetivo -> 26 passed

---

Estado del ticket: `COMPLETADO`.
