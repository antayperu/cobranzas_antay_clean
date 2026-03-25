# Sistema de Tickets Antay (TICKETS_ANTAY)

> **Fuente de Verdad** para trazabilidad, calidad y control de deuda técnica.
> Metodología: Antay Fábrica de Software.

## 1. Catálogo de Tipos y Correlativos

| Código | Tipo | Descripción | Último ID |
| :--- | :--- | :--- | :--- |
| **RC-FEAT** | Funcionalidad | Nueva característica visible para el usuario. | 062 |
| **RC-BUG** | Corrección | Error reportado o encontrado en QA. | 062 |
| **RC-UX** | UI/UX | Mejoras visuales, flujos, feedback. | 002 |
| **RC-PERF** | Performance | Optimización de tiempo, memoria o recursos. | 001 |
| **RC-ARCH** | Arquitectura | Refactor de código, estructura o deuda técnica. | 001 |
| **RC-TECH** | Deuda técnica | Estandarización de esquema, nomenclatura, contratos internos. | 001 |
| **RC-SEC** | Seguridad | Manejo de datos sensibles, credenciales. | 000 |
| **RC-QA** | Calidad | Pruebas, validaciones, checklists. | 002 |
| **RC-DOC** | Documentación | Guías, manuales, actualización de estados. | 001 |
| **RC-OPS** | Operación | Configuración, despliegue, limpieza. | 007 |

## 2. Flujo de Estados

`Backlog` → `Ready` (Definido) → `In Progress` → `QA` (Verificación) → `Done` (Cerrado)

## 3. Registro de Tickets ACTIVOS (Roadmap v5.0)

| ID | Título | Prioridad | Estado | Asignado | Fecha Inicio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RC-FEAT-039** | Informe Gerencial PDF para Comité de Directorio | **P1** (Alto) | Done ✅ | Claude | 2026-03-24 |
| **RC-FIX-062** | Recuperado real dual moneda desde resumen_ciclo | **P1** (Alto) | Done ✅ | Claude | 2026-03-24 |
| **RC-UX-001** | Sidebar progressive disclosure + feedback visual archivos | **P2** (Medio) | Done ✅ | Claude | 2026-03-24 |
| **RC-UX-002** | Informe Gerencial — tipografía Manrope/IBM Plex Sans + visual premium | **P2** (Medio) | Done ✅ | Claude | 2026-03-24 |
| **RC-QA-001** | Validar Envío PDF (Estrategia Force-Click + Loop) | **P0** (Critico) | Ready | Antigravity | 2025-12-22 |
| **RC-FEAT-001** | Selector Tri-modal (Texto / Imagen / +PDF) | **P1** (Alto) | Backlog | - | - |
| **RC-ARCH-001** | Estandarización Selectores DOM WhatsApp Web | **P2** (Medio) | Backlog | - | - |
| **RC-PERF-001** | Optimización Generación Imágenes (Caché por Hash) | **P2** (Medio) | Backlog | - | - |
| **RC-OPS-001** | Hotfix Release: Deshabilitar WhatsApp Imagen+Texto | **P0** (Critico) | In Progress | Antigravity | 2025-12-22 |
| **RC-BUG-001** | Fix SyntaxError ST-07 (Hexcept typo) | **P0** (Critico) | Done | Antigravity | 2025-12-22 |
| **RC-QA-001** | Smoke Test v1.0 — Cierre de entrega | **P0** (Critico) | Ready | Antigravity | 2025-12-22 |
| **RC-BUG-002** | Export Excel: Detracción siempre S/ + montos numéricos | **P0** (Critico) | Done | Antigravity | 2025-12-22 |
| **RC-UX-001** | Export: nombre de archivo por empresa + timestamp | **P1** (Alto) | Done | Antigravity | 2025-12-22 |
| **RC-BUG-003** | Consistencia Vista vs Excel (Amortizaciones = 0.00 fix) | **P0** (Critico) | Done | Antigravity | 2025-12-22 |
| **RC-BUG-004** | Regresión export: montos numéricos restaurados | **P0** (Critico) | Done | Antigravity | 2025-12-22 |
| **RC-UX-002** | Plantillas Email Premium (PC + Móvil) + Total Detracción | **P1** (Alto) | Done | Antigravity | 2025-12-22 |
| **RC-UX-003** | Refinamiento Email Premium (Formalidad, Layout, Medios de Pago) | **P1** (Alto) | **Done** | Antigravity | 2025-12-23 |
| **RC-DOC-001** | Reglas comunicación DACTA vs SUNAT (Detracción) | **P2** (Medio) | In Progress | Antigravity | 2025-12-22 |
| **RC-QA-002** | Smoke Test Email (SMTP) v4.6.1 | **P1** (Alto) | **Done** | Antigravity | 2025-12-23 |
| **RC-SEC-001** | Seguridad Configuración JSON (Plain Text Risk) | **P1** (Alto) | Backlog | Antigravity | 2025-12-22 |
| **RC-BUG-006** | Email Duplicado (Doble Envío / Rerun Issue) | **P0** (Critico) | Done | Antigravity | 2025-12-22 |
| **RC-BUG-007** | Email Duplicado (Protección Triple Capa) | **P0** (Critico) | In Progress | Antigravity | 2025-12-22 |
| **RC-BUG-008** | Investigación Forense Duplicados (Logs + Headers) | **P0** (Critico) | Done | Antigravity | 2025-12-23 |
| **RC-BUG-009** | SMTP Duplicado (Explicit Envelope) | **P0** (Critico) | Done | Antigravity | 2025-12-23 |
| **RC-BUG-010** | Duplicado Persistente (Forensic Trace + UI Lock) | **P0** (Critico) | Done | Antigravity | 2025-12-23 |
| **RC-BUG-012** | Restaurar Botón Envío (Regresión UI) | **P0** (Critico) | Done | Antigravity | 2025-12-23 |
| **RC-BUG-013** | Solución Definitiva Duplicados (Fix Doble Ejecución) | **P0** (Critico) | **Done** | Antigravity | 2025-12-23 |
| RC-BUG-017 | Supervisor Conf No Persiste (UI/Save) | **P0** (Critico) | **Done** | Antigravity | 2025-12-23 |
| **RC-BUG-014** | Business Ledger (SQLite) Persistente | **P0** (Critico) | **Done** | Antigravity | 2025-12-23 |
| **RC-BUG-015** | Smart Ledger (TTL 10m + Reenvío Explícito) | **P1** (Alto) | **Done** | Antigravity | 2025-12-23 |
| **RC-BUG-016** | Soporte Multi-Cliente Mismo Email (Dedup por Notif) | **P1** (Alto) | **Done** | Antigravity | 2025-12-23 |
| **RC-UX-002** | Panel de Envío Profesional (Resumen + Detalle) | **P1** (Alto) | **Done** | Antigravity | 2025-12-23 |
| **RC-FEAT-011** | Supervisor Email Copy (BCC/CC Automatico) | **P1** (Alto) | **Done** | Antigravity | 2025-12-23 |
| **RC-FEAT-012** | **QA Mode (Marcha Blanca) Safe Testing** | **P0** (Critico) | **Done** | Antigravity | 2025-12-23 |
| **RC-FEAT-013** | **Internal Copies (CC/BCC Enterprise)** | **P1** (Alto) | **Done** | Antigravity | 2025-12-24 |
| **RC-BUG-018** | **Fix Invalid st.permissions Attribute** | **P0** (Critico) | **Done** | Antigravity | 2025-12-23 |
| **RC-BUG-019** | **Fix NameError supervisor_copy_target (Residual)** | **P0** (Critico) | **Done** | Antigravity | 2025-12-23 |
| **RC-BUG-020** | **Stabilize QA Mode & Remove Supervisor Residue** | **P0** (Critico) | **Done** | Antigravity | 2025-12-23 |
| **RC-FEAT-014** | **QA Mode CC/BCC Support (Full Control)** | **P1** (Alto) | **Done** | Antigravity | 2025-12-23 |
| **RC-BUG-021** | **Strict QA/Prod Separation (No Prod Copies in QA)** | **P0** (Critico) | **Done** | Antigravity | 2025-12-23 |
| **RC-BUG-022** | **Fix CCO (BCC) Not Sending in Production** | **P0** (Critico) | **Done** | Antigravity | 2025-12-24 |
| **RC-UX-008** | **Enterprise Config UX (Dirty State & Preview)** | **P1** (Alto) | **Done** | Antigravity | 2025-12-24 |
| **RC-FEAT-015** | **Multi-Client Email Support** (Comma/Semicolon) | **P0** (Critico) | **Done** | Antigravity | 2025-12-30 |
| **RC-UX-009** | **Email List Visual Truncation** | **P1** (Alto) | **Done** | Antigravity | 2025-12-30 |
| **RC-FEAT-016** | **New 'CORREO' Column in Report & Export** | **P1** (Alto) | **Done** | Antigravity | 2025-12-30 |
| **RC-FEAT-017** | **Home Operativo Estricto (2 Archivos)** | **P0** (Critico) | **In Progress** | Antigravity | 2026-02-19 |
| **RC-UX-010** | **Home Corporativo Premium (Sidebar + Bienvenida)** | **P1** (Alto) | **In Progress** | Antigravity | 2026-02-19 |
| **RC-BUG-023** | **Fix Encoding Corrupto email_notifications.py (Mojibake CP1252→UTF-8)** | **P0** (Critico) | **Done** | Antigravity | 2026-02-20 |
| **RC-FEAT-018** | **CRM Centro de Gestiones: Timeline fix + WA tracking + Historial rediseño** | **P1** (Alto) | **Done** | Antigravity | 2026-02-20 |
| **RC-UX-011** | **CRM Gestiones — Buscar cliente con searchable selectbox** | **P1** (Alto) | **Done** | Antigravity | 2026-02-21 |
| **RC-UX-012** | **Clientes Premium — Layout mejorado (separador KPIs + filtros + botones)** | **P1** (Alto) | **Done** | Antigravity | 2026-02-21 |
| **RC-OPS-003** | **Deploy en servidor QA antay-cobranza (puerto 8503, autostart, cloudflare)** | **P0** (Critico) | **Done** | Antigravity | 2026-02-21 |
| **RC-OPS-004** | **Ciclos Persistentes con Tracking Reconciliado (cycle_id + selector + reconcile)** | **P0** (Critico) | **Done** | Antigravity | 2026-02-22 |
| **RC-FEAT-019** | **CRM: Resultado Post-Envío WhatsApp (Panel de seguimiento post-lote)** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-FEAT-020** | **CRM: Biblioteca de 7 Plantillas WhatsApp con variables** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-FEAT-021** | **CRM: Módulo de Acuerdos de Pago con Cuotas (2 tablas Supabase)** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-FEAT-022** | **CRM: Bandeja de Pendientes del Día (alertas automáticas)** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-FEAT-023** | **CRM: Trazabilidad Completa (reconcile + resumen_cliente_ciclo + resumen_ciclo)** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-BUG-024** | **Fix CREATE POLICY IF NOT EXISTS — compatibilidad PostgreSQL (sql/11, sql/12)** | **P0** (Critico) | **Done** | Antigravity | 2026-03-13 |
| **RC-BUG-025** | **Fix insert_acuerdo_pago error .select() encadenado — supabase-py sync client** | **P0** (Critico) | **Done** | Antigravity | 2026-03-13 |
| **RC-BUG-026** | **Fix ESTADO_EMAIL/WA en blanco al restaurar ciclo → fillna PENDIENTE** | **P0** (Critico) | **Done** | Antigravity | 2026-03-13 |
| **RC-BUG-027** | **Fix selectbox plantilla WA se resetea en rerun → key=wa_plantilla_seleccionada** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-BUG-028** | **Fix variable {PROX_VENC} no disponible en plantillas WA** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-FEAT-024** | **CRM: Tabs persisten al preparar nuevo ciclo (no limpiar df_final)** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-FEAT-025** | **Auto-restore último ciclo al abrir la app** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-BUG-029** | **Fix Cambiar ciclo sobreescrito por auto-restore → flag skip_auto_restore** | **P0** (Critico) | **Done** | Antigravity | 2026-03-13 |
| **RC-OPS-005** | **Documentar ALTER gestiones cycle_id en SQL (sql/13)** | **P2** (Medio) | **Done** | Antigravity | 2026-03-13 |
| **RC-OPS-006** | **Setup ambiente staging — Supabase staging + .env.staging + gitignore** | **P1** (Alto) | **Done** | Antigravity | 2026-03-14 |
| **RC-OPS-007** | **Limpieza repo — eliminar rama master remota + 5 feature branches mergeadas** | **P2** (Medio) | **Done** | Antigravity | 2026-03-13 |
| **RC-UX-013** | **Banner indicador de ambiente STAGING/PROD en sidebar** | **P1** (Alto) | **Done** | Antigravity | 2026-03-14 |
| **RC-DOC-001** | **Formalizar gitflow Antay: feature→dev→staging→main→PROD** | **P1** (Alto) | **Done** | Antigravity | 2026-03-13 |
| **RC-FEAT-026** | **Panel envío WA de prueba en Tab Configuración (smoke test sin datos reales)** | **P1** (Alto) | **Done** | Antigravity | 2026-03-16 |
| **RC-BUG-032** | **Fix notas vacías en historial post-rerun — columna `notas` faltaba en SELECT Supabase** | **P1** (Alto) | **Done** | Antigravity | 2026-03-16 |
| **RC-BUG-033** | **Fix saldo sin prefijo de moneda en tablas historial y pendientes — usar DeudaS/DeudaD** | **P1** (Alto) | **Done** | Antigravity | 2026-03-16 |
| **RC-FEAT-034** | **9 mejoras UX panel Seguimiento Post-Envío WA (orden saldo, link wa.me, % efectividad, etc.)** | **P1** (Alto) | **Done** | Antigravity | 2026-03-16 |
| **RC-FEAT-035** | **Link historial CRM completo del cliente desde panel WA Seguimiento Post-Envío** | **P3** (Bajo) | **Backlog** | - | - |
| **RC-FEAT-036** | **Tabla separada `wa_mensajes_enviados` para auditoría de mensajes (sacar de JSON metadata)** | **P1** (Alto) | **Backlog** | - | - |
| **RC-FEAT-037** | **Catálogo editable de resultados de gestión WA (`catalogo_resultado_gestion`)** | **P1** (Alto) | **Backlog** | - | - |
| **RC-BUG-050** | **Join mensaje WA a fila gestión en historial (depende de RC-FEAT-036)** | **P2** (Medio) | **Backlog** | - | - |
| **RC-BUG-053** | **Fix duplicados en historial al navegar entre sub-tabs WA — deduplicar por (CodCliente, Tipo)** | **P0** (Crítico) | **Done** | Antigravity | 2026-03-16 |
| **RC-BUG-059** | **Fix tasa de recuperación Dashboard — denominador clientes únicos del funnel, no KPIs período** | **P0** (Crítico) | **Done** | Antigravity | 2026-03-23 |
| **RC-FEAT-060** | **Dashboard: Cobertura/Intensidad/Resultados — funnel jerárquico, último resultado por cliente, Top Clientes 7 mejoras UX** | **P1** (Alto) | **Done** | Antigravity | 2026-03-23 |

---

## 4. Detalle de Tickets (Últimos 5 activos)

### [RC-FEAT-060] Dashboard: Cobertura, Intensidad y Resultados por cliente
- **Contexto**: El Dashboard mostraba métricas mezcladas — contaba filas de gestión en lugar de clientes únicos, lo que producía tasas de gestión imposibles (>100%) y confusión gerencial.
- **Rama**: `dev` (commits directos)
- **Archivos modificados**: `utils/db_manager.py`, `utils/ui/tabs/dashboard.py`, `tests/test_dashboard.py`
- **Cambios principales**:
  - `get_funnel_cobranza()`: +9 nuevas claves — `by_resultado_ultimo`, `total_envios_wa`, `total_gestion_wa`, `con_gestion_wa`, `total_gestiones_directas`, `llamadas_total`, `visitas_total`, `notas_total`, `otros_total`
  - Funnel jerárquico: fila "Con gestión directa" con sub-filas Llamada / Visita / Nota / Otros (auditabilidad: las sub-filas suman el total del padre)
  - "¿Qué respondieron?": usa `by_resultado_ultimo` → último resultado por cliente único (ya no cuenta filas)
  - Top Clientes: `@st.fragment` (cambio de vista instantáneo), vista operativa como default, columna "Nivel mora" (Crítica/Alta/Media/Normal), métrica "Gestionados: X de N", columnas Docs S/ y Docs US$ recuperadas, UX corporativa sin exceso de emojis
- **Tests**: 162/162 PASS
- **Estado**: ✅ Done — Gate 0, Gate 1 PASS · pendiente Gate 3 smoke en staging

---

### [RC-FEAT-019] CRM: Resultado Post-Envío WhatsApp
- **Contexto**: Hoy después de un envío masivo el gestor no tiene forma de registrar qué pasó con cada cliente. El campo `gestiones.resultado` existe en Supabase pero nunca se actualiza post-envío WA.
- **Rama**: `dev`
- **Archivos a modificar**: `utils/ui/tabs/whatsapp.py`, `utils/db_manager.py`
- **Alcance IN**:
  - Panel de resultados post-lote en Tab WhatsApp
  - Opciones por cliente: EXITOSO / PROMETIO_PAGAR / SIN_RESPUESTA / ESCALAR
  - Llama a `insert_gestion()` con tipo_gestion='WHATSAPP' y resultado seleccionado
  - Resumen visual de resultados registrados del lote
- **Alcance OUT**: No modifica el flujo de envío existente, no toca email
- **Criterios de Aceptación**:
  - [ ] Panel aparece solo después de un envío exitoso con al menos 1 contacto
  - [ ] Cada resultado persiste en Supabase tabla `gestiones`
  - [ ] El resultado queda vinculado al `cycle_id` del ciclo actual
  - [ ] Tests: `test_whatsapp_resultado_post_envio` pasa
- **Esfuerzo**: 1–2 horas | **Tier**: 1 | **Dependencias**: ninguna

---

### [RC-FEAT-020] CRM: Biblioteca de 7 Plantillas WhatsApp
- **Contexto**: Hoy todos los WA se envían con el mismo mensaje hardcodeado. No hay forma de elegir tono según el estado del cliente (preventivo vs. pre-legal).
- **Rama**: `dev`
- **Archivos a modificar**: `utils/ui/tabs/whatsapp.py`, `utils/ui/tabs/config_tab.py`, `utils/db_manager.py`
- **Alcance IN**:
  - Selector de plantilla visible antes del envío masivo
  - 7 plantillas predefinidas: Primer Aviso, Recordatorio, Aviso Firme, Acuerdo Confirmado, Pre-Legal, Felicitación Pago, Solicitud Datos de Contacto
  - Variables soportadas: `{empresa}`, `{monto}`, `{moneda}`, `{fecha_venc}`, `{dias_mora}`, `{gestor}`
  - Editables desde Tab Configuración y guardadas en tabla Supabase `app_config`
  - Plantilla utilizada se graba en `gestiones.metadata.template`
- **Alcance OUT**: No modifica envío de email, no cambia estructura de `gestiones`
- **Criterios de Aceptación**:
  - [ ] Selector de plantilla visible y funcional antes del envío
  - [ ] Variables se resuelven correctamente con datos del cliente
  - [ ] Plantillas persisten en Supabase entre sesiones
  - [ ] Tests: `test_wa_plantilla_resolucion_variables` pasa
- **Esfuerzo**: 3–4 horas | **Tier**: 1 | **Dependencias**: ninguna

---

### [RC-FEAT-021] CRM: Módulo de Acuerdos de Pago con Cuotas
- **Contexto**: No existe forma de formalizar en el sistema un acuerdo de pago. Los acuerdos se hacen verbalmente o en papel y nunca quedan trazados.
- **Rama**: `dev`
- **Archivos a modificar**: `utils/ui/tabs/crm_gestiones.py`, `utils/db_manager.py`
- **SQL nuevo**:
  ```sql
  CREATE TABLE acuerdos_pago (id, cliente_id, cycle_id, monto_total, num_cuotas,
    fecha_inicio, estado, notas, usuario, created_at, updated_at)
  CREATE TABLE cuotas_acuerdo (id, acuerdo_id, numero_cuota, monto, fecha_vencimiento,
    fecha_pago, estado, notas, created_at)
  ```
- **Alcance IN**:
  - Nueva sección "Acuerdos" en Tab Centro de Gestiones
  - Formulario: cliente, monto total, número de cuotas, fecha de inicio
  - Cálculo automático de fechas de vencimiento por cuota
  - Timeline visual: cuotas PENDIENTE / PAGADA / VENCIDA
  - WA automático de confirmación al crear acuerdo (usa RC-FEAT-020 si disponible)
- **Alcance OUT**: No modifica flujo de carga de Excel, no toca tab WhatsApp directamente
- **Criterios de Aceptación**:
  - [ ] Tablas `acuerdos_pago` y `cuotas_acuerdo` creadas en Supabase
  - [ ] Formulario funcional crea acuerdo con cuotas calculadas
  - [ ] Timeline visual muestra estado actualizable de cada cuota
  - [ ] Tests: `test_acuerdo_calculo_cuotas` pasa
- **Esfuerzo**: 4–6 horas | **Tier**: 1 | **Dependencias**: RC-FEAT-019 recomendado

---

### [RC-FEAT-022] CRM: Bandeja de Pendientes del Día
- **Contexto**: El gestor entra cada mañana sin saber exactamente qué hacer primero. No hay priorización automática de tareas de cobranza.
- **Rama**: `dev`
- **Archivos a modificar**: `utils/ui/tabs/crm_gestiones.py`, `utils/db_manager.py`
- **Alcance IN**:
  - Nueva pestaña "Pendientes Hoy" en Centro de Gestiones
  - Reglas de detección automática:
    - WA enviado hace +48h sin resultado registrado → prioridad URGENTE
    - Cuota de acuerdo venciendo en ≤3 días → prioridad ALTO
    - Cliente con mora >30 días sin ninguna gestión en el ciclo → prioridad ALTO
    - Cliente en estado PRE-LEGAL sin gestión esta semana → prioridad URGENTE
  - Botones de acción directa por ítem (Registrar resultado / Enviar WA / Ver acuerdo)
- **Alcance OUT**: No genera acciones automáticas sin intervención del gestor
- **Criterios de Aceptación**:
  - [ ] Lista priorizada carga al abrir la pestaña
  - [ ] Reglas de detección funcionan con datos reales de Supabase
  - [ ] Tests: `test_pendientes_deteccion_reglas` pasa
- **Esfuerzo**: 2–3 horas | **Tier**: 1 | **Dependencias**: RC-FEAT-021 (tabla cuotas_acuerdo)

---

### [RC-FEAT-023] CRM: Trazabilidad Completa (reconcile + 2 tablas resumen)
- **Contexto**: Los datos de pago del ERP Integrens ya están en Supabase (`cobranzas`) pero nunca se cruzan con `documentos_ciclo` para marcar documentos como RECUPERADOS con fecha y forma de pago exacta. Tampoco existen tablas de resumen por cliente ni por ciclo para el informe gerencial.
- **Rama**: `dev`
- **Archivos a modificar**: `utils/db_manager.py`, `app.py`
- **SQL nuevo**:
  ```sql
  CREATE TABLE resumen_cliente_ciclo (cycle_id, cod_cliente, empresa,
    total_deuda, docs_vencidos, dias_mora_max, tendencia, created_at)
  CREATE TABLE resumen_ciclo (cycle_id, fecha_corte, cartera_total,
    cartera_vencida, cartera_prelegal, recuperado_vs_anterior, tasa_recuperacion,
    created_at)
  ```
- **Alcance IN**:
  - Función `reconcile_ciclo_recovery(cycle_id_anterior, cycle_id_nuevo)` en `db_manager.py`
  - Documentos que desaparecen del Excel → busca en `cobranzas` → marca estado RECUPERADO + fecha_pago + forma_pago + banco
  - Al cierre de ciclo: graba 1 fila en `resumen_cliente_ciclo` por cada cliente
  - Al cierre de ciclo: graba 1 fila en `resumen_ciclo` con totales de toda la cartera
  - `app.py` llama a reconcile después de `persist_cycle_to_supabase()`
- **Alcance OUT**: No modifica el flujo de carga ni la UX existente
- **Criterios de Aceptación**:
  - [ ] Tablas `resumen_cliente_ciclo` y `resumen_ciclo` creadas en Supabase
  - [ ] `reconcile_ciclo_recovery()` detecta documentos RECUPERADOS correctamente
  - [ ] Al cargar ciclo nuevo, ambas tablas resumen se actualizan automáticamente
  - [ ] Tests: `test_reconcile_recovery_deteccion` pasa
- **Esfuerzo**: 4–5 horas | **Tier**: 1 | **Dependencias**: ninguna

---

### [RC-OPS-004] Ciclos Persistentes con Tracking Reconciliado
- **Descripcion**: Al restaurar un ciclo anterior, ESTADO_EMAIL aparecia en blanco aunque los correos ya habian sido enviados. El tracking solo vivia en memoria y nunca se reconciliaba con la tabla notificaciones.
- **Alcance IN**: SQL ALTER TABLE notificaciones ADD COLUMN cycle_id. Funcion reconcile en db_manager. Selector de ciclos en sidebar (tabla con ID, archivo, filas, enviados). state_manager lista y carga ciclos por ID. email y whatsapp pasan cycle_id al persistir.
- **Criterios de Aceptacion**:
    - [ ] cycle_id columna existe en notificaciones.
    - [ ] Al restaurar ciclo X, ESTADO_EMAIL se reconstruye desde notificaciones WHERE cycle_id = X.
    - [ ] Sidebar muestra lista de todos los ciclos disponibles con info clave.
    - [ ] Ciclos no se borran al iniciar nuevo procesamiento.
    - [ ] Excel export refleja tracking correcto tras restaurar.

| **RC-FEAT-017** | **Home Operativo Estricto (2 Archivos)** — **Done** ✅
- **Descripcion**: Ajustar la UI principal para procesar exclusivamente CtasxCobrar + Cobranza, tomando cartera desde Supabase.
- **Alcance IN**: Sidebar sin uploader de cartera, validacion de 2 archivos, bloqueo operativo si falta cartera maestra.
- **Criterios de Aceptacion**:
    - [x] Sidebar muestra solo 2 uploaders.
    - [x] Proceso usa cartera maestra Supabase por defecto.
    - [x] Mensaje de bloqueo dirige al tab Clientes Premium.

### [RC-UX-010] Home Corporativo Premium (Sidebar + Bienvenida)
- **Descripcion**: Renovar el punto de entrada con lenguaje y visual corporativo alineado a metodologia Antay.
- **Alcance IN**: Cabecera premium en sidebar, tarjeta de bienvenida con guia operativa, consistencia visual de controles clave.
- **Criterios de Aceptacion**:
    - [x] Sidebar con identidad visual corporativa.
    - [x] Bienvenida principal actualizada al flujo de 2 archivos.
    - [x] Responsive funcional en desktop/mobile.

### [RC-FEAT-012] QA Mode (Marcha Blanca) Safe Testing
- **Descripción**: Implementar un modo de "Marcha Blanca" que permita realizar pruebas end-to-end de envío de correos masivos sin riesgo de contactar clientes reales.
- **Alcance IN**: Toggle QA Mode, Lista de QA Recipient, Override de destinatarios, Subject/Body injection.
- **Criterios de Aceptación**:
    - [ ] **Safe Override**: Si QA ON, ignorar emails reales y usar lista QA.
    - [ ] **Injection**: Subject `[QA - MARCHA BLANCA]`, Body Banner `PRUEBA INTERNA`.
    - [ ] **Traceability**: UI muestra Email Original vs Email QA enviado.
    - [x] **Traceability**: UI muestra Email Original vs Email QA enviado.
    - [x] **No-Regression**: Ledger, TTL y Multi-cliente siguen funcionando igual.

### [RC-FEAT-013] Internal Copies (CC/BCC Enterprise)
- **Descripción**: Reemplazar lógica simple de "Supervisor" por listas de distribución interna (CC Visible y CCO Oculto).
- **Alcance**: UI para gestionar listas, normalización, headers SMTP y reglas QA (ignorar copias en QA).
- **Criterios de Aceptación**:
    - [ ] **UI**: Campos CC y CCO separados, validación de emails.
    - [ ] **SMTP Prod**: Header `Cc` correcto, `Bcc` oculto, Envelope contiene todos.
    - [ ] **SMTP QA**: Ignora copias internas (solo envía a QA List).

### [RC-QA-001] Validar Envío PDF (Estrategia Force-Click + Loop)
- **Descripción**: El envío de PDF en WhatsApp Web es crítico para v5.0. Se debe validar la robustez de la estrategia actual (reintentos x3, selectores estrictos y manejo de modales).
- **Alcance IN**: Validación manual y automatizada del flujo de adjuntos. Verificación de selectores.
- **Alcance OUT**: Rediseño del PDF en sí mismo.
- **Criterios de Aceptación**:
    - [ ] El script detecta correctamente el botón "Adjuntar".
    - [ ] El input file recibe el path absoluto sin error.
    - [ ] Se verifica visualmente (o por DOM) que el modal de carga aparece.
    - [ ] El envío se confirma solo tras la subida completa.
    - [ ] Manejo de error si el archivo no existe.

### [RC-UX-001] Feedback Visual Envío WhatsApp
- **Descripción**: El usuario necesita saber qué está pasando durante el envío masivo. Logs de texto plano no son suficientes para una experiencia "Premium".
- **Criterios de Aceptación**:
    - [ ] Barra de progreso visual en Streamlit.
    - [ ] Indicador de estado por cliente (Pendiente -> Enviando -> Éxito/Fallen).
    - [ ] Resumen final con estadísticas.

### [RC-FEAT-001] Selector Tri-modal de Envío
- **Descripción**: Permitir al usuario elegir explícitamente entre: 1) Solo Texto, 2) Tarjeta (Imagen), 3) Tarjeta + PDF.
- **Criterios de Aceptación**:
    - [ ] Radio button o Selectbox en UI.
    - [ ] La lógica de envío respeta la selección estrictamente.
    - [ ] UI se adapta (muestra/oculta opciones de PDF) según selección.

### [RC-UX-011] CRM Gestiones — Buscar cliente con searchable selectbox
- **Descripcion**: Reemplazar el flujo de 2 pasos (text_input + selectbox condicional) por un único `st.selectbox` preloaded con todos los clientes de Supabase + ciclo activo.
- **Commit**: `596001b` — release v1.7.1
- **Criterios de Aceptacion**:
    - [x] Selectbox preloaded con clientes Supabase + ciclo activo combinados.
    - [x] Busqueda nativa por codigo o nombre.
    - [x] Sin selectbox condicional ni text_input previo.

### [RC-UX-012] Clientes Premium — Layout mejorado
- **Descripcion**: Mejorar distribución visual del TAB Clientes Premium: separador post-KPIs, filtros con labels visibles, botones Agregar/Importar/Eliminar en misma fila que filtros.
- **Commit**: `596001b` — release v1.7.1
- **Criterios de Aceptacion**:
    - [x] Separador `---` entre KPIs y zona de filtros.
    - [x] Labels visibles en filtros Estado y Enviar Email.
    - [x] Botones de accion alineados horizontalmente con los filtros.

### [RC-OPS-003] Deploy en servidor QA antay-cobranza
- **Descripcion**: Instalar y configurar la app en `\\QA\antay-cobranza` (C:\antay-cobranza) para operacion permanente en servidor siempre encendido con acceso remoto via Cloudflare Tunnel.
- **Commit**: `596001b` — release v1.7.1
- **Criterios de Aceptacion**:
    - [x] Repo clonado desde GitHub (antayperu/cobranzas_antay_clean).
    - [x] venv_prod con supabase>=2.27.3 y websockets>=13,<16.
    - [x] cloudflared.exe + url_notifier.py envia URL al correo al arrancar.
    - [x] Puerto 8503 (8501/8502 ocupados por otras apps).
    - [x] Tarea Windows `CobranzasAntayAutoStart` registrada (onlogon).
    - [x] App accesible via URL Cloudflare desde cualquier red.

### [RC-FEAT-026] Panel WA de Prueba en Tab Configuración
- **Contexto**: Para hacer smoke test del envío WA el gestor necesitaba tener datos reales cargados. No había forma de validar la conexión WA sin un ciclo activo.
- **Rama**: `dev`
- **Archivo**: `utils/ui/tabs/config_tab.py` — SECCIÓN 8 (entre WA dispositivo y Opciones Avanzadas)
- **Alcance IN**:
  - Input teléfono con valor por defecto `+51921566036`
  - Textarea para mensaje libre
  - Botón "Enviar WA de prueba" — llama a `send_whatsapp_messages_direct()` con contacto ficticio
  - Toast verde en éxito / mensaje claro en error
  - NO requiere ciclo cargado ni `df_final` activo
- **Commit**: `d8a342a` (2026-03-16)
- **Estado**: Done ✅

---

### [RC-BUG-032] Notas vacías en historial post-rerun
- **Contexto**: Al hacer rerun de Streamlit después de guardar una gestión, el campo "Notas" aparecía vacío en la tabla de historial aunque el dato existía en Supabase.
- **Causa raíz**: La columna `notas` faltaba en el `.select()` de `get_wa_gestiones_by_cycle` en `db_manager.py`.
- **Fix 1**: Persistir nota en `session_state['last_wa_send_results']['details']` antes del `st.rerun()`.
- **Fix 2 (raíz)**: Agregar `notas` al `.select()` en `db_manager.py`.
- **Commits**: `bd9f264` + `4cd9cac` (2026-03-16)
- **Estado**: Done ✅

---

### [RC-BUG-033] Saldo sin prefijo de moneda en tablas historial y pendientes
- **Contexto**: En las tablas de historial de gestiones y bandeja de pendientes, la columna "Saldo" mostraba un número sin indicar si era S/ o $.
- **Causa**: Se usaba `_det.get('Deuda', '')` (número raw sin prefijo de moneda).
- **Fix**: Usar `DeudaS` + `DeudaD` ya formateados (`S/ X.XX` / `$ X.XX`) con fallback.
- **Archivo**: `utils/ui/tabs/whatsapp.py`
- **Commits**: `1f69034` + `da4b6b3` (2026-03-16)
- **Estado**: Done ✅

---

### [RC-FEAT-034] 9 mejoras UX panel Seguimiento Post-Envío WA
- **Contexto**: El panel de seguimiento post-envío era funcional pero carecía de información de valor para el gestor (efectividad, priorización por saldo, accesos directos).
- **Rama**: `dev`
- **Archivo**: `utils/ui/tabs/whatsapp.py`
- **Mejoras implementadas**:
  1. Orden por saldo descendente (`_parse_saldo_sort()`)
  2. Teléfono como link `wa.me/{número}` con ícono 💬
  3. KPI % efectividad (`_con_gestion / _total_env * 100`)
  4. Tipo de gestión como ícono (📋 Gestión / 📤 Envío WA) con tooltip
  5. Tooltip notas largas truncadas (`max-width:200px`)
  6. Barra de progreso del ciclo (`_pct_ciclo`)
  7. Color semántico del saldo (rojo ≥S/5000, naranja ≥S/1000, gris <S/1000)
  8. Badge ↩ Reintentar si resultado = SIN_RESPUESTA
  9. Tooltip descriptivo en botón "Guardar todos"
- **Mejora #10** (link historial CRM): diferida a TIER 3 como RC-FEAT-035
- **Commits**: `cb4c9b6` + `6e65376` (2026-03-16)
- **Estado**: Done ✅

---

### [RC-FEAT-035] Link Historial CRM Completo del Cliente desde Panel WA
- **Contexto**: Desde el historial de gestiones WA, el gestor no puede navegar directamente al historial CRM completo del cliente. Debe cambiar de tab manualmente y filtrar.
- **Rama**: pendiente
- **Archivos**: `utils/ui/tabs/whatsapp.py` (columna nueva en historial), `utils/ui/tabs/crm_gestiones.py` (recibir filtro por `cliente_id`)
- **Alcance IN**:
  - Botón/link "Ver CRM" en cada fila del historial de gestiones WA
  - Clic navega automáticamente a Tab CRM Gestiones via `session_state`
  - Tab CRM pre-filtra por el cliente seleccionado
  - Filtro se limpia al cambiar contexto manualmente
- **Alcance OUT**: Sin afectar SSOT ni `df_final`
- **Dependencias**: RC-FEAT-034 (mejoras UX WA) — COMPLETADO
- **Esfuerzo**: 2 puntos (~2 horas) | **Tier**: 3
- **Estado**: Backlog 📋

---

### [RC-FEAT-036] Tabla separada `wa_mensajes_enviados`
- **Contexto**: Los mensajes enviados por WA viven dentro del campo JSONB `metadata` de la tabla `gestiones`. Datos críticos de auditoría en JSON violan estándares de arquitectura: no se pueden indexar, buscar ni reportar eficientemente.
- **Rama**: pendiente
- **Archivos**: `utils/db_manager.py`, SQL nuevo
- **SQL propuesto**:
  ```sql
  CREATE TABLE wa_mensajes_enviados (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      gestion_id UUID REFERENCES gestiones(id),
      cliente_id TEXT REFERENCES clientes(CodCliente),
      template_label TEXT,
      template_texto TEXT,
      mensaje_exacto_enviado TEXT,
      telefono_destino TEXT,
      batch_id TEXT,
      send_mode TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```
- **Beneficios**: Auditoría sin parseo JSON, búsquedas por índice, escalable
- **Esfuerzo**: 5 puntos (1–2 días) | **Tier**: 3
- **Estado**: Backlog 📋

---

### [RC-FEAT-037] Catálogo editable de resultados de gestión WA
- **Contexto**: Los resultados de gestión (EXITOSO, PROMETIO_PAGAR, SIN_RESPUESTA, ESCALAR) están hardcodeados en Python. Agregar un nuevo resultado requiere redeploy completo. No es escalable para un producto en producción.
- **Rama**: pendiente
- **Archivos**: `utils/ui/tabs/config_tab.py`, `utils/db_manager.py`, SQL nuevo
- **SQL propuesto**:
  ```sql
  CREATE TABLE catalogo_resultado_gestion (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      codigo_resultado TEXT UNIQUE NOT NULL,
      label_ui TEXT NOT NULL,
      descripcion TEXT,
      color_badge TEXT,
      activo BOOLEAN DEFAULT TRUE,
      orden INTEGER,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```
- **Panel en Configuración**: CRUD (crear/editar/borrar) resultados desde UI
- **Esfuerzo**: 3 puntos (1–2 días) | **Tier**: 3
- **Estado**: Backlog 📋

---

### [RC-BUG-050] Join mensaje WA a fila gestión en historial
- **Contexto**: En la tabla de historial de gestiones, la columna "Mensaje WA" solo se llena si la fila es de tipo Envío. Si hay una gestión manual posterior registrada para el mismo cliente, el mensaje original no se muestra en esa fila.
- **Causa**: No existe JOIN entre `gestiones` y los mensajes enviados (hoy en JSON metadata).
- **Fix requerido**: JOIN `gestiones ← wa_mensajes_enviados` para recuperar el mensaje exacto por `cliente_id` + `batch_id`.
- **Dependencia crítica**: RC-FEAT-036 (tabla `wa_mensajes_enviados`) debe estar en producción primero.
- **Esfuerzo**: 2 puntos (2–3 horas) | **Tier**: 3
- **Estado**: Pendiente / Diferido 📋

---

### [RC-TECH-001] Estandarizar `documentos_ciclo.cod_cliente` → `cliente_id`
- **Contexto**: La columna `documentos_ciclo.cod_cliente` usa una nomenclatura distinta al resto del esquema, donde la misma referencia se llama `cliente_id` (en `gestiones`, `acuerdos_pago`, etc.). Esta inconsistencia ya causó un bug silencioso en `get_funnel_cobranza()`: el código buscaba `cliente_id` en `documentos_ciclo` y retornaba diccionario vacío sin levantar error, haciendo que el Dashboard mostrara todos los KPIs en cero.
- **Categoría**: Deuda técnica — nomenclatura inconsistente en el esquema
- **Impacto detectado**: Bug RC-BUG en producción — Dashboard mostraba KPIs en cero (detectado en sesión 2026-03-22)
- **Política**: Antay Fábrica de Software de Talla Mundial — contratos de datos explícitos, sin trampas de nomenclatura.
- **Rama**: pendiente (antes de v2.0)
- **Archivos afectados**:
  - `utils/db_manager.py` → `get_funnel_cobranza()`: actualizar select y referencias
  - Cualquier otra función que haga select en `documentos_ciclo`
- **SQL de migración**:
  ```sql
  -- Ejecutar en staging primero, luego en producción
  ALTER TABLE documentos_ciclo RENAME COLUMN cod_cliente TO cliente_id;
  ```
- **Precaución**: Verificar que ninguna vista (VIEW) o función PostgreSQL referencia `cod_cliente` antes de ejecutar. Correr `pytest tests/ -v` después del cambio.
- **Esfuerzo**: 1 punto (2–3 horas) | **Tier**: 2
- **Prioridad**: P2 (Medio) — no bloquea operación, pero elimina trampa activa
- **Estado**: Backlog 📋

---
*Fin del documento.*
