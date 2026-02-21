# FRD - Clientes Premium y Home Operativo (2 archivos)

Fecha: 2026-02-19  
Proyecto: ReporteCobranzas (Antay)  
Version: v1.1

---

## 1. Contexto

La operacion principal cambia de forma oficial a un flujo de 2 archivos:

1. `CtasxCobrar`
2. `Cobranza`

La cartera de clientes ya no se carga en el Home.  
La cartera maestra se administra solo en la TAB `Clientes Premium` y se consume desde Supabase en cada ciclo.

---

## 2. Objetivo

Consolidar una experiencia corporativa premium y sin ambiguedades:

1. Home operacional simple y rapido (2 archivos).
2. Gestion de clientes completamente separada en `Clientes Premium`.
3. Mensajeria UI consistente con metodologia Antay (flujo claro, sin pasos redundantes).

---

## 3. Alcance Funcional

### IN

1. Sidebar/Home con uploaders unicamente para `CtasxCobrar` y `Cobranza`.
2. Eliminacion del uploader de `Cartera` en la UI principal.
3. Procesamiento del ciclo usando cartera maestra desde Supabase.
4. Bloqueo operativo con instruccion clara si no existe cartera maestra.
5. Refuerzo visual corporativo premium en sidebar y estado de bienvenida.
6. TAB `Clientes Premium` como unica superficie de mantenimiento/migracion de clientes.

### OUT

1. Cambios de modelo relacional fuera de `clientes`.
2. Nuevas reglas comerciales para documentos/cobranzas.
3. Automatizaciones externas de aprobacion (workflows fuera de app).

---

## 4. Requerimientos Funcionales

1. RF-CP-01: El Home solo acepta `CtasxCobrar` y `Cobranza`.
2. RF-CP-02: La app obtiene cartera desde Supabase en cada procesamiento.
3. RF-CP-03: Si no hay cartera maestra, el ciclo se bloquea y muestra accion correctiva hacia `Clientes Premium`.
4. RF-CP-04: La gestion de clientes (edicion total + migracion Excel) ocurre solo en `Clientes Premium`.
5. RF-CP-05: El sidebar comunica el flujo oficial con mensajes operativos corporativos.
6. RF-CP-06: El estado inicial muestra guia de 3 pasos alineada a flujo 2 archivos.

---

## 5. Requerimientos UX/UI

1. UX-CP-01: Cabecera de sidebar con jerarquia visual corporativa.
2. UX-CP-02: Tarjeta de bienvenida premium con pasos de operacion.
3. UX-CP-03: Controles de carga y acciones primarias con consistencia visual.
4. UX-CP-04: Responsive correcto en desktop y mobile dentro de Streamlit.

---

## 6. Criterios de Aceptacion

1. CA-CP-01: En sidebar se visualizan solo 2 uploaders (`CtasxCobrar`, `Cobranza`).
2. CA-CP-02: El boton `Procesar y validar` se habilita solo cuando ambos archivos existen.
3. CA-CP-03: El sistema procesa con cartera Supabase sin solicitar Excel de clientes en Home.
4. CA-CP-04: Si la cartera maestra no existe, se muestra mensaje de bloqueo con instruccion a `Clientes Premium`.
5. CA-CP-05: `Clientes Premium` mantiene edicion/migracion de cartera sin regresiones.
6. CA-CP-06: La UI principal refleja look corporativo premium y comunica el nuevo flujo sin ambiguedad.

---

## 7. Entregables Tecnicos

1. `app.py` (flujo estricto de 2 archivos).
2. `utils/ui/sidebar.py` (wizard operativo sin uploader de cartera).
3. `utils/session.py` (estado de carga alineado a 2 archivos).
4. `utils/ui/styles.py` (upgrade visual corporativo premium).
5. `docs/backlog_priorizado.md` (tickets y criterios actualizados).
6. `docs/TICKET_FEATURE_002_CLIENTES_PREMIUM.md` (alcance actualizado).

---

## 8. Validacion

1. Smoke manual:
   - Cargar `CtasxCobrar` + `Cobranza`.
   - Procesar ciclo.
   - Validar que usa cartera Supabase.
2. Caso de control:
   - Simular ausencia de cartera maestra.
   - Confirmar bloqueo y mensaje operativo.
3. Validacion UX:
   - Confirmar nueva cabecera sidebar.
   - Confirmar tarjeta de bienvenida premium.
