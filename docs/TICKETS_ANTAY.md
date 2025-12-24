# Sistema de Tickets Antay (TICKETS_ANTAY)

> **Fuente de Verdad** para trazabilidad, calidad y control de deuda técnica.
> Metodología: Antay Fábrica de Software.

## 1. Catálogo de Tipos y Correlativos

| Código | Tipo | Descripción | Último ID |
| :--- | :--- | :--- | :--- |
| **RC-FEAT** | Funcionalidad | Nueva característica visible para el usuario. | 001 |
| **RC-BUG** | Corrección | Error reportado o encontrado en QA. | 000 |
| **RC-UX** | UI/UX | Mejoras visuales, flujos, feedback. | 002 |
| **RC-PERF** | Performance | Optimización de tiempo, memoria o recursos. | 001 |
| **RC-ARCH** | Arquitectura | Refactor de código, estructura o deuda técnica. | 001 |
| **RC-SEC** | Seguridad | Manejo de datos sensibles, credenciales. | 000 |
| **RC-QA** | Calidad | Pruebas, validaciones, checklists. | 002 |
| **RC-DOC** | Documentación | Guías, manuales, actualización de estados. | 000 |
| **RC-OPS** | Operación | Configuración, despliegue, limpieza. | 001 |

## 2. Flujo de Estados

`Backlog` → `Ready` (Definido) → `In Progress` → `QA` (Verificación) → `Done` (Cerrado)

## 3. Registro de Tickets ACTIVOS (Roadmap v5.0)

| ID | Título | Prioridad | Estado | Asignado | Fecha Inicio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RC-QA-001** | Validar Envío PDF (Estrategia Force-Click + Loop) | **P0** (Critico) | Ready | Antigravity | 2025-12-22 |
| **RC-UX-001** | Feedback Visual Envío WhatsApp (Logs y Progreso) | **P1** (Alto) | Backlog | - | - |
| **RC-FEAT-001** | Selector Tri-modal (Texto / Imagen / +PDF) | **P1** (Alto) | Backlog | - | - |
| **RC-UX-002** | Rediseño Tarjeta Ejecutiva (Match Email UI) | **P1** (Alto) | Backlog | - | - |
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
| **RC-FEAT-013** | **Internal Copies (CC/BCC Enterprise)** | **P1** (Alto) | **In Progress** | Antigravity | 2025-12-23 |

---

## 4. Detalle de Tickets (Últimos 5 activos)

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

---
*Fin del documento.*
