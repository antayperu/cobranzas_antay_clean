# FRD - Clientes Premium (Cartera Maestra)

Fecha: 2026-02-17  
Proyecto: ReporteCobranzas (Antay)  
Version: v1.0

---

## 1. Contexto

La operacion debe priorizar carga de 2 archivos (`CtasxCobrar` y `Cobranza`) usando una cartera maestra persistida en Supabase.  
La gestion de clientes no debe mezclarse con configuracion general: se requiere una TAB dedicada, con capacidad de edicion completa y migracion masiva.

---

## 2. Objetivo

Habilitar una experiencia premium de mantenimiento de clientes con:

1. TAB independiente para cartera maestra.
2. Edicion de cualquier registro y cualquier campo de negocio.
3. Migracion de cartera desde Excel hacia Supabase.
4. Flujo principal de carga basado en 2 archivos, tomando clientes desde Supabase.

---

## 3. Alcance Funcional

### IN

1. Nueva TAB `Clientes Premium` con editor maestro de `clientes`.
2. Campos editables: `cliente_id`, `nombre`, `email`, `telefono`, `ruc`, `direccion`, `estado`, `notas`.
3. Guardado masivo via upsert por `cliente_id`.
4. Eliminacion controlada de clientes removidos del editor (opt-in).
5. Migracion de cartera desde Excel con validacion y resumen de errores.
6. Sidebar prioriza modo 2 archivos, usando cartera maestra Supabase por defecto.

### OUT

1. Cambios de modelo relacional fuera de `clientes`.
2. Reglas comerciales nuevas sobre documentos/cobranzas.
3. Automatizaciones de aprobacion de cambios (workflow externo).

---

## 4. Requerimientos Funcionales

1. RF-CP-01: El mantenimiento de clientes se ejecuta solo en la TAB `Clientes Premium`.
2. RF-CP-02: El usuario puede editar/insertar clientes con todos los campos operativos.
3. RF-CP-03: El sistema permite migrar cartera desde Excel y aplicar upsert.
4. RF-CP-04: El flujo de carga principal opera con 2 archivos en modo recomendado.
5. RF-CP-05: Si no existe cartera maestra en Supabase, el sistema bloquea y muestra instruccion operativa.
6. RF-CP-06: Debe mantenerse opcion de carga manual de cartera para soporte excepcional.

---

## 5. Criterios de Aceptacion

1. CA-CP-01: Se visualiza la TAB `Clientes Premium` separada de `Configuracion`.
2. CA-CP-02: Se pueden actualizar en lote los campos del cliente y persisten en Supabase.
3. CA-CP-03: La migracion de cartera desde Excel inserta/actualiza clientes validos.
4. CA-CP-04: Se reportan errores de validacion de cartera en la migracion.
5. CA-CP-05: Sidebar permite procesar ciclo con solo `CtasxCobrar` y `Cobranza`.
6. CA-CP-06: La app informa claramente cuando falta cartera maestra en Supabase.

---

## 6. Entregables Tecnicos

1. `utils/ui/tabs/clientes_premium.py`
2. `utils/db_manager.py` (CRUD ampliado + migracion cartera)
3. `utils/ui/sidebar.py` (modo principal 2 archivos por defecto)
4. `app.py` (nueva TAB y flujo asociado)
5. `tests/test_db_manager_clients.py`

---

## 7. Validacion

1. Tests unitarios de `db_manager` para listado, update full payload, upsert, delete y migracion.
2. Prueba manual E2E:
   - Migrar cartera en TAB `Clientes Premium`.
   - Procesar ciclo subiendo solo 2 archivos.
   - Confirmar uso de cartera maestra y persistencia correcta.
