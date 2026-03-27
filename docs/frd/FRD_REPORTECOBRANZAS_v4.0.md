# FRD v4.0 — ReporteCobranzas (Antay)

**Proyecto:** ReporteCobranzas — Plataforma de Gestión de Cobranza B2B
**Product Owner:** Camilo Ortega F.R.
**Versión FRD:** 4.1
**Fecha:** 2026-03-17
**Versión app actual:** v1.8.3
**Estado Supabase:** Migración completa (MIG-000 a MIG-009)
**Estado CRM WA:** TIER 1 ✅ + TIER 2 ✅ completados

---

## Tabla de Contenidos

1. [Glosario mínimo](#1-glosario-mínimo)
2. [Visión del producto](#2-visión-del-producto)
3. [Problema a resolver](#3-problema-a-resolver)
4. [Alcance](#4-alcance)
5. [Reglas NO negociables](#5-reglas-no-negociables)
6. [Modelo de datos](#6-modelo-de-datos)
7. [Flujo del usuario](#7-flujo-del-usuario)
8. [Reglas de conteo](#8-reglas-de-conteo)
9. [Módulos actuales — Lo que ya funciona](#9-módulos-actuales--lo-que-ya-funciona)
10. [Backlog — Funcionalidades pendientes con diseños](#10-backlog--funcionalidades-pendientes-con-diseños)
11. [Matriz de priorización](#11-matriz-de-priorización)
12. [Quality Gates](#12-quality-gates)
13. [Criterios de aceptación globales](#13-criterios-de-aceptación-globales)
14. [Ambientes](#14-ambientes)
15. [Changelog](#15-changelog)

---

## 1. Glosario mínimo

| Término | Definición |
|---|---|
| **SSOT** | Fuente única de verdad — el dataset maestro en memoria (`df_final`) |
| **Vista filtrada** | Dataset para la pantalla según filtros activos (`df_filtered`) |
| **Ciclo** | Unidad de procesamiento identificada con un código único (`CIC-YYYYMMDD-HHMM`) |
| **Fresh Load** | Carga nueva de los 2 archivos Excel que inicia un ciclo nuevo |
| **Gate** | Punto de control de calidad obligatorio antes de declarar un cambio "listo" |
| **E2E** | End-to-End — prueba completa del flujo real del usuario de inicio a fin |
| **Cloud-only** | Sin respaldo local; si Supabase no responde → bloqueo controlado con mensaje claro |
| **Aging** | Días de mora de un documento (desde la fecha de vencimiento hasta hoy) |
| **Lote** | Grupo de clientes enviados en un mismo envío WA masivo |
| **Gestión** | Registro de contacto/resultado en tabla `gestiones` (tipo: WHATSAPP, EMAIL, LLAMADA) |
| **DSO** | Days Sales Outstanding — días promedio desde que se emite una factura hasta que se cobra |
| **B2B** | Business to Business — empresa que vende a otras empresas (no a consumidores finales) |
| **Funnel** | Embudo de conversión — cuántos clientes pasan de cada etapa a la siguiente |
| **KPI** | Key Performance Indicator — indicador clave de desempeño |

---

## 2. Visión del producto

### 2.1 Qué es esta aplicación

**ReporteCobranzas** es una **plataforma de gestión de cobranza B2B** para empresas de servicios que necesitan administrar, comunicar y reportar su cartera de cuentas por cobrar de forma profesional.

No es simplemente una herramienta de envío de mensajes. Es el sistema central desde donde el área de cobranzas:

- **Opera** — gestiona la cartera, envía notificaciones, registra acuerdos
- **Controla** — monitorea la efectividad de cada canal y cada gestión
- **Reporta** — genera evidencia para el directorio y el CEO

### 2.2 Los tres niveles de usuario

La aplicación sirve simultáneamente a tres niveles de la organización:

```
┌──────────────────────────────────────────────────────────────┐
│  NIVEL 3 — DIRECTORIO / CEO                                  │
│  ¿Cuánto se cobró? ¿Cuánto está en riesgo? ¿Qué hacemos?    │
│  → Informe Gerencial mensual exportable en PDF               │
├──────────────────────────────────────────────────────────────┤
│  NIVEL 2 — JEFE / SUPERVISOR DE COBRANZAS                    │
│  ¿Qué tan efectiva es la gestión? ¿Qué canal funciona más?  │
│  → Dashboard de Efectividad con KPIs en tiempo real         │
├──────────────────────────────────────────────────────────────┤
│  NIVEL 1 — GESTOR DE COBRANZAS (operativo)                   │
│  ¿A quién contacto hoy? ¿Qué le digo? ¿Qué respondió?       │
│  → Reporte General + Tabs Email/WA/CRM + Acuerdos           │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Canales de gestión soportados

La plataforma registra y trazabiliza todos los canales de contacto propios de una cobranza B2B:

| Canal | Estado actual |
|---|---|
| Email masivo con HTML premium | ✅ Implementado |
| WhatsApp Web (texto + imagen + PDF) | ✅ Implementado |
| Llamada telefónica (registro manual) | ✅ Registro en CRM |
| Visita presencial (registro manual) | ✅ Registro en CRM |
| Carta / comunicación formal | 🔲 Pendiente |
| Acuerdos de pago con cuotas | ✅ Implementado |

---

## 3. Problema a resolver

La empresa DACTA S.A.C. (y cualquier empresa de servicios B2B) enfrenta estos desafíos de cobranza:

1. **Cartera dispersa** — los documentos por cobrar están en Excel y no se cruzan fácilmente con los datos de contacto de cada cliente.
2. **Sin trazabilidad** — no queda registro claro de cuándo se contactó a cada cliente, por qué canal, qué respondió, qué acordó.
3. **Gestión reactiva** — sin indicadores, no se sabe cuáles clientes están en riesgo hasta que la deuda es muy alta.
4. **Reportes manuales** — el jefe de cobranzas prepara el informe para directorio a mano, en Excel, cada mes.
5. **Sin evidencia** — en caso de disputa legal, no hay registro ordenado de las gestiones realizadas.

**ReporteCobranzas resuelve todo esto** desde una sola plataforma web.

---

## 4. Alcance

### 4.1 Incluye (IN)

- Carga de 2 archivos Excel y generación del Reporte General
- Cartera maestra de clientes mantenida en Supabase (CRUD desde la app)
- Notificaciones Email: selección, vista previa HTML, envío masivo, reporte post-envío
- WhatsApp: envío masivo, 7 plantillas configurables, seguimiento resultado por cliente
- CRM Centro de Gestiones: registro de gestiones multicanal, acuerdos de pago, bandeja de pendientes
- Trazabilidad completa de todos los envíos y gestiones (ciclos históricos recuperables)
- **Dashboard de Efectividad** con funnel de cobranza y KPIs financieros _(pendiente de implementar)_
- **Informe Gerencial** mensual exportable en PDF para comités de directorio _(pendiente de implementar)_
- Módulo Clientes Premium (CRUD completo desde la app)
- Ambientes PROD/STAGING con detección automática y banner visible
- Panel de prueba WA en Tab Configuración

### 4.2 No incluye (OUT)

- Rediseñar la lógica financiera de deuda o detracción
- Cambiar los nombres de las columnas clave del sistema
- Cambiar el motor de exportación a Excel/PDF
- Base de datos local (SQLite) — solo Supabase cloud
- Envío automático de mensajes sin intervención del gestor
- Integración directa con sistemas contables (SAP, CONCAR, etc.)

---

## 5. Reglas NO negociables

1. **NO romper el flujo funcional existente.** Cualquier cambio debe ser aditivo.
2. **NO inventar procesos sin actualizar este FRD.**
3. **NO renombrar columnas clave:**
   - `CodCliente`, `Empresa`, `SaldoReal`, `Correo`, `MATCH_KEY`
   - `ESTADO_EMAIL`, `FECHA_ULTIMO_ENVIO`, `ESTADO_WHATSAPP`
4. **Mejoras UI/UX** solo usando `load_css()` desde `utils/ui/styles.py`. Nunca inyectar CSS en otro lugar.
5. **Todo cambio debe pasar todos los Quality Gates** antes de declararse "listo".
6. **Timestamps en Supabase siempre en UTC real** (`datetime.now(timezone.utc)`). Nunca hora local como UTC.
7. **Gestiones graban la hora real del clic**, no la hora del envío WA original.
8. **`df_final` es SSOT sagrado** — solo la lógica de tracking oficial lo modifica. La UI usa `df_filtered`.

---

## 6. Modelo de datos

### 6.1 Entradas del sistema (archivos Excel)

- **Archivo A:** Cuentas por Cobrar (documentos pendientes)
- **Archivo B:** Cobranzas (aplicaciones: detracciones, amortizaciones, pagos)

> La cartera maestra de clientes **NO** se carga desde Excel en cada ciclo. Se mantiene en Supabase y se edita desde la app.

### 6.2 Dataset en memoria

| Dataset | Rol |
|---|---|
| `df_final` | SSOT — dataset maestro. Solo se modifica por lógica de tracking oficial |
| `df_filtered` | Vista derivada según filtros activos. Es lo que ve la pantalla |

### 6.3 Columnas de tracking (obligatorias)

| Columna | Valores posibles | Notas |
|---|---|---|
| `ESTADO_EMAIL` | `PENDIENTE` / `ENVIADO` / `ERROR` / `SIN_CORREO` | Se inicializa en Fresh Load |
| `FECHA_ULTIMO_ENVIO` | timestamp ISO | Vacío hasta confirmación de envío |
| `ESTADO_WHATSAPP` | `PENDIENTE` / `ENVIADO` / `ERROR` / `SIN_TELEFONO` | Ídem |

### 6.4 Tablas Supabase

| Tabla | Tipo | Descripción |
|---|---|---|
| `clientes` | MAESTRA | Lista oficial de clientes. Se edita desde la app, no se recarga por Excel |
| `documentos` | TRANSACCIONAL | Facturas/boletas por cobrar. Se recarga en cada ciclo |
| `cobranzas` | TRANSACCIONAL | Aplicaciones de pago (detracciones, amortizaciones) |
| `notificaciones` | TRANSACCIONAL CRÍTICA | Registro permanente de cada envío. **NUNCA se borra** |
| `gestiones` | TRANSACCIONAL | Gestiones CRM: contacto, resultado, notas, metadata |
| `acuerdos_pago` | TRANSACCIONAL | Acuerdos de pago registrados con cliente |
| `cuotas_acuerdo` | TRANSACCIONAL | Cuotas por acuerdo con estado y fechas |
| `ciclos_procesamiento` | TRANSACCIONAL | Metadata de cada ciclo cargado (historial recuperable) |
| `resumen_cliente_ciclo` | ANALÍTICA | 1 fila por cliente por ciclo (para dashboard) |
| `resumen_ciclo` | ANALÍTICA | 1 fila por ciclo con totales (para informes) |
| `app_config` | CONFIGURACIÓN | Plantillas WA, config SMTP, parámetros de la app |

**Reglas críticas:**
- `clientes`: no se recarga en cada ciclo
- `notificaciones`: nunca se borra, se acumula historial indefinidamente
- `ciclos_procesamiento`: se acumula; cada ciclo es identificable y recuperable
- `cycle_id` formato: `CIC-YYYYMMDD-HHMM`
- Timestamps: siempre UTC (`datetime.now(timezone.utc).isoformat()`)

---

## 7. Flujo del usuario

### 7.1 Flujo principal (ciclo de gestión)

```
1. Cargar 2 Excel
   └─→ Se genera el Reporte General
   └─→ Se crea un cycle_id nuevo
   └─→ Tracking inicial: ESTADO_EMAIL = PENDIENTE, ESTADO_WHATSAPP = PENDIENTE

2. Revisar Reporte General
   └─→ Filtrar por empresa, rango de saldo, estado de envío
   └─→ Vista Ejecutiva (resumen) o Vista Completa (detalle)

3. Notificaciones Email (Tab Email)
   └─→ Seleccionar clientes a notificar
   └─→ Vista previa del email HTML personalizado
   └─→ Enviar → tracking actualizado automáticamente

4. Notificaciones WhatsApp (Tab WhatsApp)
   └─→ Seleccionar plantilla (o dejar que la app sugiera por aging)
   └─→ Envío masivo → cada cliente se registra en Supabase al instante
   └─→ Registrar resultado post-envío por cliente

5. Gestión CRM (Tab CRM)
   └─→ Registrar llamadas, visitas, notas por cliente
   └─→ Crear acuerdos de pago con cuotas
   └─→ Revisar bandeja de pendientes del día

6. Reportar (Dashboard + Informe Gerencial) [PENDIENTE]
   └─→ Ver KPIs de efectividad del ciclo
   └─→ Generar PDF del informe gerencial para el directorio
```

### 7.2 Ciclo nuevo (reemplaza el ciclo actual)

- Botón "Cargar nuevos archivos" → confirmación en 2 pasos
- Al confirmar: el reporte anterior desaparece, el tracking vuelve a estado inicial
- El ciclo anterior queda guardado en Supabase, recuperable por selector de ciclos históricos

### 7.3 Auto-restore

- Al abrir la app: se carga automáticamente el último ciclo activo
- El gestor puede cambiar de ciclo sin recargar archivos
- Flag `skip_auto_restore` evita que el auto-restore sobreescriba una elección manual

---

## 8. Reglas de conteo

- **"Enviados"** y **"Pendientes"** se miden por `CodCliente` único — nunca por email
- Un cliente con fila de Envío WA + fila de Gestión se cuenta **una sola vez**
- Montos multimoneda: guardar `DeudaS` (soles) y `DeudaD` (dólares) por separado
- Historial de gestiones: deduplicar por clave única `(CodCliente, Tipo, Timestamp)`, no por cliente
- % Efectividad WA = (EXITOSO + PROMESA_PAGO) / total WA enviados en el ciclo

---

## 9. Módulos actuales — Lo que ya funciona

Esta sección documenta lo que está **completamente implementado y funcionando** en producción (v1.8.3).

---

### 9.1 Módulo: Reporte General

**Qué hace:** Procesa los 2 archivos Excel y genera la vista de toda la cartera por cobrar.

```
┌─────────────────────────────────────────────────────────────────────┐
│  ReporteCobranzas  ·  Ciclo: CIC-20260317-0930  ·  48 clientes     │
├──────────┬──────────┬──────────┬──────────────────────────────────  │
│ S/141,200│ $24,800  │    48    │    31 pendientes de notificar      │
│Total S/  │ Total $  │ Clientes │                                    │
├──────────┴──────────┴──────────┴──────────────────────────────────  │
│  🔍 Filtrar por empresa... │ Estado: [Todos ▼] │ [Vista Ejecutiva]  │
├─────────────────────────────────────────────────────────────────────┤
│  Empresa          │ Saldo S/ │ Saldo $ │ Email     │ WhatsApp       │
│  ─────────────────┼──────────┼─────────┼───────────┼──────────────  │
│  EMPRESA A SAC    │  2,333   │    -    │ ✅ Enviado │ ✅ Enviado     │
│  EMPRESA B EIRL   │    -     │  4,734  │ ⏳ Pendiente│ ⏳ Pendiente  │
│  EMPRESA C SAC    │  18,390  │    -    │ ✅ Enviado │ ⚠️ Error       │
│  EMPRESA D SAC    │    -     │  3,087  │ ⏳ Pendiente│ ⏳ Pendiente  │
│  ...              │  ...     │  ...    │ ...       │ ...            │
└─────────────────────────────────────────────────────────────────────┘
```

**Características:**
- Vista Ejecutiva (resumen compacto) y Vista Completa (todos los campos)
- KPIs en parte superior: Total Saldo S/ y $, Total Clientes, Pendientes
- Filtros por empresa, estado de envío, rango de saldo
- Pantalla completa para máxima productividad

---

### 9.2 Módulo: Notificaciones Email

**Qué hace:** Envía emails HTML personalizados a cada cliente con el detalle de sus documentos pendientes.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Tab: Notificaciones Email                                          │
├────────────────────┬────────────────────────────────────────────────┤
│  📊 KPIs           │  31 pendientes · 17 enviados hoy               │
├────────────────────┴────────────────────────────────────────────────┤
│  Seleccionar clientes:  ☑ Todos pendientes  /  ○ Selección manual  │
│                                                                     │
│  ☑ EMPRESA A SAC     S/ 2,333    📧 contacto@empresaa.com          │
│  ☑ EMPRESA B EIRL    $ 4,734     📧 admin@empresab.com             │
│  ☑ EMPRESA D SAC     $ 3,087     📧 finanzas@empresad.com          │
│                                                                     │
│  [👁️ Vista previa email]           [ 📧 Enviar (3 clientes) ]       │
├─────────────────────────────────────────────────────────────────────┤
│  ✅ REPORTE POST-ENVÍO                                              │
│  3 enviados · 0 errores · 0 sin correo                              │
│  EMPRESA A SAC → ✅ | EMPRESA B EIRL → ✅ | EMPRESA D SAC → ✅     │
└─────────────────────────────────────────────────────────────────────┘
```

**Características:**
- Vista previa HTML del email antes de enviar
- Tracking automático por `CodCliente` en Supabase
- Reporte post-envío que persiste entre pestañas
- Protección anti-duplicados (no reenvía si ya fue enviado en el ciclo)
- QA Mode: en ambiente de prueba no envía emails reales

---

### 9.3 Módulo: WhatsApp

**Qué hace:** Envía mensajes masivos por WhatsApp Web y registra el resultado de cada gestión.

#### Sub-módulo A: Envío Masivo

```
┌─────────────────────────────────────────────────────────────────────┐
│  Tab: WhatsApp > Enviar Mensajes                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Plantilla:  [ 📋 Cobranza Estándar                  ▼ ]           │
│                                                                     │
│  Clientes seleccionados (31):                                       │
│  ☑ EMPRESA A SAC    S/ 2,333   📱 +51 999 111 222                  │
│  ☑ EMPRESA B EIRL   $ 4,734    📱 +51 999 333 444                  │
│  ☑ EMPRESA D SAC    $ 3,087    📱 +51 999 555 666                  │
│  ...                                                               │
│                                                                     │
│              [ 📲 Enviar WA masivo (31 clientes) ]                  │
└─────────────────────────────────────────────────────────────────────┘
```

#### Sub-módulo B: Seguimiento Post-Envío (CRM WhatsApp)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Tab: WhatsApp > Seguimiento                                        │
├───────────────────────────┬──────────────────────────────────────── │
│  📊 Este ciclo             │  31 enviados · 12 con resultado (38.7%)│
├───────────────────────────┴──────────────────────────────────────── │
│  #  │ Cliente          │ Saldo    │ Resultado          │ Acción     │
│  ───┼──────────────────┼──────────┼────────────────────┼─────────── │
│  1  │ EMPRESA A SAC    │ S/ 2,333 │ [✅ Acordó pagar ▼]│ [Guardar] │
│  2  │ EMPRESA B EIRL   │ $ 4,734  │ [📵 Sin respuesta▼]│ ↩ Reinten │
│  3  │ EMPRESA C SAC    │ S/ 138   │ [🤝 Prometió pagar▼│ [Guardar] │
│  4  │ EMPRESA D SAC    │ $ 3,087  │ [Seleccionar...  ▼]│ [Guardar] │
│                                                                     │
│         [ 💾 Guardar todos ]                                        │
└─────────────────────────────────────────────────────────────────────┘
```

**8 Plantillas configurables** (nombres reales en la app + uso recomendado por aging):

| Plantilla | Uso recomendado | Días de mora |
|---|---|---|
| 📋 Cobranza Estándar | Primer contacto, deuda reciente | 0 – 14 días |
| 🔔 Primer Recordatorio | Primera insistencia | 15 – 30 días |
| ⚠️ Segundo Recordatorio | Segunda insistencia, tono más firme | 31 – 45 días |
| 🔴 Urgente / Pre-Legal | Aviso formal, riesgo de escalar | 46 – 60 días |
| 🤝 Confirmación de Acuerdo | Tras firmar un acuerdo de pago | Cualquiera |
| ✅ Reconocimiento de Pago | Tras confirmación de pago recibido | Cualquiera |
| 💰 Solo Total | Clientes que prefieren mensaje breve | Cualquiera |
| ✏️ Personalizada | Casos especiales, redactado libre | Cualquiera |

**Resultados de gestión WA** (estándar de industria cobranza B2B, aprobado 2026-03-17):

| Etiqueta en la app | Código interno Supabase | Significado operativo |
|---|---|---|
| ✅ Acordó pagar | `EXITOSO` | Compromiso firme con fecha y/o comprobante |
| 🤝 Prometió pagar | `PROMESA_PAGO` | Promesa verbal sin fecha exacta — requiere seguimiento |
| ⏳ Solicitó más plazo | `SOLICITO_PLAZO` | Pidió extensión — registrar nueva fecha de contacto |
| 💬 En negociación | `EN_NEGOCIACION` | Conversación activa, pendiente de acuerdo |
| 📵 Sin respuesta | `SIN_RESPUESTA` | No contestó ningún canal |
| ⚖️ Derivar a Legal | `ESCALAR_LEGAL` | Agotados los canales amistosos — requiere acción legal |
| ❓ Disputó la deuda | `DISPUTA` | Cliente no reconoce la deuda — requiere revisión comercial |

---

### 9.4 Módulo: CRM Centro de Gestiones

**Qué hace:** Registro centralizado de todas las interacciones con cada cliente, acuerdos de pago y bandeja de pendientes prioritarios.

#### Sub-módulo A: Historial de Gestiones

```
┌─────────────────────────────────────────────────────────────────────┐
│  CRM > Historial de Gestiones                                       │
│  Filtrar por cliente: [ EMPRESA C SAC          ▼ ]                 │
├─────────────────────────────────────────────────────────────────────┤
│  Fecha         │ Tipo       │ Resultado       │ Notas               │
│  ─────────────┼────────────┼─────────────────┼─────────────────── │
│  17/03 10:30  │ 📲 WA      │ 🤝 Prometió     │ "Paga el viernes"  │
│  15/03 09:15  │ 📤 Email   │ ✅ Enviado       │ Primer aviso        │
│  10/03 14:00  │ 📞 Llamada  │ 📵 Sin respuesta │ Número correcto     │
├─────────────────────────────────────────────────────────────────────┤
│  [ + Registrar nueva gestión ]                                      │
│  Tipo: [Llamada ▼]  Resultado: [...]  Notas: [________________]    │
└─────────────────────────────────────────────────────────────────────┘
```

#### Sub-módulo B: Acuerdos de Pago

```
┌─────────────────────────────────────────────────────────────────────┐
│  CRM > Acuerdos de Pago                                             │
├─────────────────────────────────────────────────────────────────────┤
│  Cliente: [ EMPRESA C SAC ▼ ]   Monto total: S/ 18,390             │
│  Cuotas: [ 3 ▼ ]    Fecha inicio: [ 20/03/2026 ]                   │
│                                                                     │
│  Cuota 1 — S/ 6,130 — 20/03/2026  🟢 PENDIENTE                    │
│  Cuota 2 — S/ 6,130 — 20/04/2026  ⬜ PENDIENTE                    │
│  Cuota 3 — S/ 6,130 — 20/05/2026  ⬜ PENDIENTE                    │
│                                                                     │
│              [ 💾 Registrar acuerdo ]                               │
└─────────────────────────────────────────────────────────────────────┘
```

#### Sub-módulo C: Bandeja de Pendientes del Día

```
┌─────────────────────────────────────────────────────────────────────┐
│  CRM > Pendientes del Día                     3 acciones urgentes  │
├─────────────────────────────────────────────────────────────────────┤
│  🚨 URGENTE                                                         │
│  DISTRIBUIDORA SUR — $ 3,200 — 68 días sin pago                    │
│  3 WA enviados sin respuesta — ¿Derivar a legal?                   │
│  [ 📲 Enviar WA ]  [ 📞 Registrar llamada ]  [ ⚖️ Derivar legal ]  │
├─────────────────────────────────────────────────────────────────────┤
│  ⚠️ ATENCIÓN                                                         │
│  COMERCIAL LIMA — Cuota 1 de acuerdo vence en 3 días (20/03)       │
│  S/ 6,130 — ¿Enviar recordatorio?                                  │
│  [ 📲 Enviar recordatorio WA ]  [ ✅ Marcar como pagada ]           │
├─────────────────────────────────────────────────────────────────────┤
│  ℹ️ SEGUIMIENTO                                                      │
│  GRUPO NORTE SAC — Sin gestión en 7 días — S/ 21,400               │
│  [ 📲 Enviar WA ]  [ 📧 Enviar email ]  [ 📞 Registrar llamada ]   │
└─────────────────────────────────────────────────────────────────────┘
```

**Lógica de prioridad automática:**
- `URGENTE` — WA sin respuesta +48h, o mora +60 días sin acción
- `ATENCIÓN` — cuotas de acuerdo venciendo en ≤3 días
- `SEGUIMIENTO` — clientes +30 días mora sin ninguna gestión

---

### 9.5 Módulo: Clientes Premium

**Qué hace:** Mantenimiento de la cartera maestra de clientes en Supabase. Es la única pantalla autorizada para agregar, editar o desactivar clientes.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Clientes Premium — Cartera Maestra                 48 clientes    │
├─────────────────────────────────────────────────────────────────────┤
│  [ + Agregar cliente ]     🔍 Buscar...                             │
├─────────────────────────────────────────────────────────────────────┤
│  Código  │ Empresa          │ Email            │ Teléfono │ Estado  │
│  ────────┼──────────────────┼──────────────────┼──────────┼─────── │
│  000165  │ EMPRESA A SAC    │ contacto@...     │ +51 999  │ ✅ Activo│
│  000234  │ EMPRESA B EIRL   │ admin@...        │ +51 998  │ ✅ Activo│
│  000089  │ EMPRESA C SAC    │ —                │ +51 997  │ ✅ Activo│
│                                                                     │
│  [ Editar ] [ Desactivar ]                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 9.6 Módulo: Configuración

**Qué hace:** Administración de plantillas WA, configuración SMTP, y herramientas de diagnóstico.

- Edición de las 7 plantillas de WhatsApp (texto, variables disponibles)
- Panel de prueba de WhatsApp (enviar un mensaje de prueba sin datos reales)
- Configuración de email (servidor SMTP, remitente, copia al supervisor)
- Reiniciar registro de envíos del ciclo actual
- Selector de ciclos históricos

---

## 10. Backlog — Funcionalidades Pendientes con Diseños

Esta sección describe **todo lo que falta implementar**, con diseños detallados de pantalla, criterios de aceptación y esfuerzo estimado. Sirve como base para la priorización.

---

### 10.1 RC-FEAT-027 — Selección automática de plantilla WA por Aging

**Para quién:** El gestor de cobranzas.

**El problema hoy:** El gestor debe recordar qué plantilla usar según cuántos días lleva la deuda. Si usa un tono agresivo con un cliente que recién vence, o uno suave con uno que ya tiene 60 días, está cometiendo un error de estrategia.

**La solución:** La app sugiere automáticamente la plantilla correcta según los días de mora de cada cliente en el lote.

```
┌─────────────────────────────────────────────────────────────────────┐
│  WhatsApp > Enviar Mensajes                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Plantilla: [🟡 Recordatorio (sugerida por antigüedad de deuda) ▼] │
│  ℹ️ Sugerencia basada en el segmento de mora del lote seleccionado  │
│                                                                     │
│  #  │ Cliente          │ Saldo    │ Días mora │ Segmento           │
│  ───┼──────────────────┼──────────┼───────────┼─────────────────── │
│  1  │ EMPRESA A SAC    │ S/ 2,333 │  22 días  │ 🟡 Recordatorio   │
│  2  │ EMPRESA B EIRL   │ $ 4,734  │   8 días  │ 🟢 Primer Aviso   │
│  3  │ EMPRESA C SAC    │ S/ 138   │  45 días  │ 🔴 Aviso Firme    │
│  4  │ EMPRESA D SAC    │ $ 3,087  │  70 días  │ ⛔ Pre-Legal      │
│                                                                     │
│  ⚠️ Atención: 1 cliente en Pre-Legal. Revisar antes de enviar.     │
│                                                                     │
│              [ 📲 Enviar WA masivo (4 clientes) ]                   │
└─────────────────────────────────────────────────────────────────────┘
```

**Regla de negocio — Segmentos de mora:**

| Días de mora | Segmento | Plantilla sugerida | Color |
|---|---|---|---|
| 0 – 14 días | Deuda reciente | 📋 Cobranza Estándar | 🟢 Verde |
| 15 – 30 días | Sin respuesta inicial | 🔔 Primer Recordatorio | 🟡 Amarillo |
| 31 – 45 días | Mora significativa | ⚠️ Segundo Recordatorio | 🟠 Naranja |
| 46 – 60 días | Mora alta | 🔴 Urgente / Pre-Legal | 🔴 Rojo |
| 61+ días | Mora crítica | Derivar a Legal (sin WA) | ⛔ Crítico |

**Criterios de aceptación:**
- [ ] Columna "Días mora" y "Segmento" visibles en la tabla de selección de clientes WA
- [ ] La plantilla se pre-selecciona según el segmento más frecuente del lote
- [ ] El gestor puede cambiar la plantilla manualmente antes de enviar
- [ ] Alerta visible si hay clientes en Pre-Legal en el lote seleccionado
- [ ] El envío automático nunca ocurre — siempre requiere clic explícito del gestor

**Esfuerzo estimado:** 2 horas | **Prioridad:** Media | **Archivos:** `whatsapp.py`

---

### 10.2 RC-FEAT-028 — KPIs Operativos del Ciclo Actual

**Para quién:** El supervisor inmediato del área de cobranzas.

**El problema hoy:** Se sabe cuántos mensajes se enviaron, pero no se sabe qué tan efectiva está siendo la gestión del día. No hay forma de ver en tiempo real si los esfuerzos están funcionando.

**La solución:** Panel de KPIs operativos visible en el Tab WhatsApp y en el CRM, actualizado en tiempo real.

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 Efectividad del Ciclo Actual — CIC-20260317-0930               │
├──────────┬──────────┬──────────┬──────────┬──────────────────────── │
│    31    │    12    │    8     │    3     │      S/ 156,420        │
│  WA      │  Con     │  Sin     │ Acuerdos │  Monto en Gestión      │
│  Enviados│ Resultado│ Respuesta│ Activos  │                        │
│          │  38.7% ✅│          │          │                        │
├──────────┴──────────┴──────────┴──────────┴──────────────────────── │
│  ⏰ Cuotas venciendo en ≤3 días: 2  │  💰 Monto con acuerdo: S/48,200│
│  🏆 Plantilla más efectiva: Recordatorio → 5 con resultado EXITOSO  │
└─────────────────────────────────────────────────────────────────────┘
```

**Criterios de aceptación:**
- [ ] KPIs calculados desde Supabase (tablas `gestiones`, `acuerdos_pago`, `cuotas_acuerdo`)
- [ ] Visibles en Tab WhatsApp (subtab Seguimiento) y en CRM Centro de Gestiones
- [ ] % efectividad = (EXITOSO + PROMESA_PAGO) / total WA enviados en el ciclo
- [ ] No modifica `df_final` ni `df_filtered` — cálculo independiente
- [ ] Se actualiza al refrescar la pantalla sin necesidad de recargar el ciclo

**Esfuerzo estimado:** 3 horas | **Prioridad:** Media | **Archivos:** `whatsapp.py`, `crm_gestiones.py`, `db_manager.py`

---

### 10.3 RC-UX-001 — Feedback visual durante el envío WA masivo

**Para quién:** El gestor de cobranzas.

**El problema hoy:** Durante el envío masivo la pantalla queda sin información. El gestor no sabe si el proceso avanza, quién ya recibió su mensaje y quién falló. Es una experiencia de usuario deficiente para un proceso tan crítico.

**La solución:** Panel de progreso en tiempo real durante el envío.

```
┌─────────────────────────────────────────────────────────────────────┐
│  📲 Enviando mensajes WhatsApp...                                   │
│                                                                     │
│  ████████████████░░░░░░░░░░░░░░  18 / 31  (58%)                    │
│  Cliente actual: ALMACENES CHUPACA S.A.C.                          │
│                                                                     │
│  ✅  GOLOSINAS SEMINARIO E.I.R.L.      S/ 2,333   → Enviado        │
│  ✅  DISTRIBUIDORA DISUMP S.A.C.       S/ 138     → Enviado        │
│  ✅  LA GRAN RES SAC                   $ 3,087    → Enviado        │
│  ⏳  ALMACENES CHUPACA S.A.C.          S/ 18,390  → Enviando...    │
│  ⬜  EMPRESA E SAC                     S/ 892     → Pendiente      │
│  ❌  EMPRESA F EIRL                    $ 445      → Sin teléfono   │
│  ⬜  EMPRESA G SAC                     S/ 3,100   → Pendiente      │
│                                                                     │
│  Enviados: 3  │  Con error: 1  │  Pendientes: 13                   │
└─────────────────────────────────────────────────────────────────────┘
```

**Criterios de aceptación:**
- [ ] Barra de progreso con contador `N / Total` y porcentaje
- [ ] Nombre del cliente actual visible mientras se procesa
- [ ] Lista en tiempo real con iconos de estado por cliente
- [ ] Contador de enviados / errores / pendientes al pie
- [ ] No bloquea la interfaz durante el proceso

**Nota técnica:** El `progress_callback` ya existe en `send_whatsapp_messages_direct()`. Solo se necesita mejorar la UI que lo consume.

**Esfuerzo estimado:** 3 horas | **Prioridad:** Alta | **Archivos:** `whatsapp.py`, `whatsapp_sender.py`

---

### 10.4 RC-FEAT-001 — Selector tri-modal: Texto / Imagen / Imagen+PDF

**Para quién:** El gestor de cobranzas.

**El problema hoy:** El modo de envío (solo texto, imagen de resumen, o imagen+PDF detallado) no es configurable fácilmente antes de cada envío. Se presta a errores.

**La solución:** Selector explícito del modo de envío con vista previa.

```
┌─────────────────────────────────────────────────────────────────────┐
│  WhatsApp > Modo de envío:                                          │
│                                                                     │
│  ○ 📝 Solo Texto    ● 🖼️ Tarjeta (Imagen)    ○ 📎 Imagen + PDF    │
│                                                                     │
│  ┌── Vista previa ───────────────────────────────────────────────┐  │
│  │  [Logo empresa]                                               │  │
│  │                                                               │  │
│  │  Estimado EMPRESA A SAC,                                      │  │
│  │  Le informamos que tiene documentos pendientes de pago        │  │
│  │  por un total de S/ 2,333.00                                  │  │
│  │                                                               │  │
│  │  [Imagen resumen de la deuda]                                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ⚠️ Modo PDF requiere sesión de WhatsApp Web activa                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Criterios de aceptación:**
- [ ] Selector tri-modal visible antes del envío
- [ ] La UI muestra/oculta la vista previa según la selección
- [ ] La lógica de envío respeta estrictamente el modo seleccionado
- [ ] Advertencia si selecciona PDF y no hay sesión WA activa
- [ ] La selección se guarda y no se resetea al refrescar la pantalla

**Esfuerzo estimado:** 4 horas | **Prioridad:** Media | **Archivos:** `whatsapp.py`, `whatsapp_sender.py`

---

### 10.5 RC-SEC-001 — Seguridad: credenciales en texto plano

**Para quién:** El administrador del sistema.

**El problema hoy:** Las contraseñas del servidor de email (SMTP) y las claves de Supabase están guardadas en archivos de texto (`config.json`) en el servidor. Cualquier persona con acceso al servidor puede verlas.

**La solución:** Mover todas las credenciales sensibles a variables de entorno (un archivo especial que no se puede leer desde el exterior).

**Antes (inseguro):**
```
config.json → contiene SMTP password, API keys en texto visible
              cualquier persona con acceso al servidor puede leerlo
```

**Después (seguro):**
```
.env → variables de entorno (protegido, no incluido en backups de código)
       SMTP_PASSWORD=xxxxx
       SUPABASE_KEY=xxxxx

config.json → solo configuración NO sensible
              (nombre empresa, teléfonos, opciones de pantalla)
```

**Criterios de aceptación:**
- [ ] Ninguna contraseña ni clave API en `config.json` ni en el código fuente
- [ ] Variables sensibles cargadas desde `.env` con la librería `python-dotenv`
- [ ] `.env` incluido en la lista de archivos ignorados por git (ya existe)
- [ ] Documento `.env.example` con las variables requeridas (sin valores reales)
- [ ] Sin romper la configuración existente en el servidor QA

**Esfuerzo estimado:** 3 horas | **Prioridad:** Alta (riesgo de seguridad real) | **Archivos:** `settings_manager.py`, `email_sender.py`

---

### 10.6 RC-FEAT-035 — Link "Ver CRM" desde el historial WA

**Para quién:** El gestor de cobranzas.

**El problema hoy:** Desde el historial de WhatsApp el gestor debe ir manualmente al tab de CRM y buscar al cliente para ver su historial completo. Son muchos clics innecesarios.

**La solución:** Un botón "Ver CRM →" en cada fila del historial que lleva directo al CRM filtrado por ese cliente.

```
│  #  │ Cliente          │ Saldo    │ Resultado    │ Acción           │
│  ───┼──────────────────┼──────────┼──────────────┼───────────────── │
│  1  │ EMPRESA A SAC    │ S/ 2,333 │ ✅ Acordó    │ [Ver CRM →]     │
│  2  │ EMPRESA B EIRL   │ $ 4,734  │ 📵 Sin resp. │ [Ver CRM →]     │
```

**Criterios de aceptación:**
- [ ] Botón "Ver CRM →" por fila en el historial de gestiones WA
- [ ] Al hacer clic: cambia automáticamente al Tab CRM con el cliente pre-filtrado
- [ ] El filtro se limpia al navegar manualmente en CRM

**Esfuerzo estimado:** 2 horas | **Prioridad:** Baja | **Archivos:** `whatsapp.py`, `crm_gestiones.py`

---

### 10.7 RC-FEAT-036 — Tabla separada para mensajes WA enviados

**Para quién:** El equipo técnico y auditores.

**El problema hoy:** El texto exacto de cada mensaje WA enviado a cada cliente está enterrado dentro de un campo JSON en la base de datos. No se puede buscar ni consultar directamente.

**La solución:** Una tabla dedicada `wa_mensajes_enviados` en Supabase que guarda cada mensaje como texto plano, con referencias al cliente, la plantilla usada y el envío original.

**Criterios de aceptación:**
- [ ] Tabla `wa_mensajes_enviados` creada en Supabase con script SQL versionado
- [ ] El callback `on_client_sent` inserta también en esta nueva tabla
- [ ] La consulta `SELECT * FROM wa_mensajes_enviados WHERE cliente_id = 'X'` devuelve el historial completo
- [ ] Sin cambios visibles en la interfaz de usuario

**Esfuerzo estimado:** 5 horas | **Prioridad:** Baja (arquitectura interna) | **Archivos:** `db_manager.py`

---

### 10.8 RC-FEAT-037 — Catálogo editable de resultados de gestión WA

**Para quién:** El administrador del sistema.

**El problema hoy:** Los resultados de gestión disponibles (7 resultados del estándar: `EXITOSO`, `PROMESA_PAGO`, `SOLICITO_PLAZO`, `EN_NEGOCIACION`, `SIN_RESPUESTA`, `ESCALAR_LEGAL`, `DISPUTA`) están fijos en el código. Agregar uno nuevo requiere modificar el código y hacer un nuevo despliegue de la app.

**La solución:** Un catálogo editable desde la pantalla de Configuración, guardado en Supabase.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Configuración > Resultados de Gestión WA                          │
├─────────────────────────────────────────────────────────────────────┤
│  Orden │ Código           │ Etiqueta UI      │ Activo │ Acciones   │
│  ──────┼──────────────────┼──────────────────┼────────┼──────────  │
│    1   │ EXITOSO          │ ✅ Acordó pagar      │  ✅   │ [Editar]  │
│    2   │ PROMESA_PAGO     │ 🤝 Prometió pagar    │  ✅   │ [Editar]  │
│    3   │ SOLICITO_PLAZO   │ ⏳ Solicitó más plazo│  ✅   │ [Editar]  │
│    4   │ EN_NEGOCIACION   │ 💬 En negociación    │  ✅   │ [Editar]  │
│    5   │ SIN_RESPUESTA    │ 📵 Sin respuesta      │  ✅   │ [Editar]  │
│    6   │ ESCALAR_LEGAL    │ ⚖️ Derivar a Legal    │  ✅   │ [Editar]  │
│    7   │ DISPUTA          │ ❓ Disputó la deuda   │  ✅   │ [Editar]  │
│                                                                     │
│  [ + Agregar resultado ]                                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Criterios de aceptación:**
- [ ] Panel CRUD (crear, editar, desactivar) en Tab Configuración
- [ ] Los resultados se cargan dinámicamente desde Supabase en el panel de seguimiento WA
- [ ] Desactivar un resultado lo oculta de la UI pero no borra datos históricos
- [ ] El orden es configurable

**Esfuerzo estimado:** 4 horas | **Prioridad:** Media | **Archivos:** `config_tab.py`, `whatsapp.py`, `db_manager.py`

---

### 10.9 RC-FEAT-038 — Dashboard de Efectividad de Cobranza (Visión Completa)

**Para quién:** El jefe / supervisor de cobranzas.

**El problema hoy:** No existe ninguna pantalla que muestre la efectividad real de la gestión de cobranza. Se sabe cuántos mensajes se enviaron, pero no cuántos resultaron en un pago, cuánto tiempo tardó el cobro, qué canal funciona mejor, ni cuáles clientes son crónicamente difíciles.

**La solución:** Un tab dedicado "Dashboard de Efectividad" con 5 bloques de información.

---

#### Bloque 1 — Funnel de Cobranza (el flujo completo)

Muestra cuántos clientes pasan de cada etapa a la siguiente. Identifica en qué punto se "cae" la gestión.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Dashboard Efectividad > Funnel del Ciclo  CIC-20260317-0930       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐  ▶  ┌──────────┐  ▶  ┌──────────┐  ▶  ┌──────────┐  ▶  ┌──────────┐│
│  │    48    │     │    38    │     │    22    │     │    11    │     │    7     ││
│  │ TOTAL    │     │ WA       │     │RESPONDIER│     │ ACUERDO  │     │  PAGO   ││
│  │ CARTERA  │     │ENVIADOS  │     │ ON O     │     │ FIRMADO  │     │RECIBIDO ││
│  │ CON DEUDA│     │ con tel. │     │PROMETIERO│     │          │     │CONFIRMAD││
│  │  100%    │     │  79%     │     │  58%     │     │  29%     │     │  18%    ││
│  └──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘│
│                                                                     │
│  ⚡ Tasa de conversión global: 18% (7 de 48 clientes pagaron)      │
│  📉 Mayor caída: "Respondieron → Acuerdo" — oportunidad de mejora  │
└─────────────────────────────────────────────────────────────────────┘
```

---

#### Bloque 2 — KPIs Financieros de Efectividad

```
┌─────────────────────────────────────────────────────────────────────┐
│  KPIs Financieros                                                   │
├──────────────────────┬──────────────────────┬──────────────────────┤
│  DSO — Días prom.   │  Tasa de Recuperación│  Efectividad WA      │
│  de cobro           │  Mensual             │                      │
│                     │                      │                      │
│        34           │         62%          │         58%          │
│     días            │  de cartera cobrada  │  de WA respondidos   │
│                     │                      │                      │
│  ⚠️ Meta: 25 días   │  ✅ Meta: 55%        │  ✅ Meta: 40%        │
│  +9 días sobre meta │  +7% sobre meta      │  +18% sobre meta     │
│  Tendencia: ↗ +3d   │  Tendencia: ↗ +5%   │  Tendencia: → igual  │
├──────────────────────┼──────────────────────┼──────────────────────┤
│  Monto Recuperado   │  Acuerdos:           │  Tiempo respuesta WA │
│  (período actual)   │  Cumplimiento        │                      │
│                     │                      │                      │
│    S/ 87,400        │         73%          │        4.2h          │
│  (de S/ 141,200)    │  cuotas en fecha     │  desde envío a resp. │
│                     │                      │                      │
│  ✅ Meta: S/ 70,000 │  ⚠️ Meta: 80%        │  ✅ Meta: < 8h       │
│  + S/ 12,800 (USD)  │  11 acuerdos activos │  Pico: 10-12am       │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

---

#### Bloque 3 — Efectividad por Plantilla WA

Qué plantilla convierte más en acuerdos y pagos reales.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Efectividad por Plantilla WA                                       │
├──────────────────┬──────────┬──────────┬──────────┬────────────────┤
│  Plantilla       │ Enviados │Respuesta │ Acuerdo  │  Pago efectivo │
├──────────────────┼──────────┼──────────┼──────────┼────────────────┤
│  📋 Primer Aviso │    18    │   72%  ✅│   33%    │      22%       │
│  ⏰ Recordatorio │    12    │   67%  ✅│   42%    │  33%  🏆 mejor  │
│  🔴 Aviso Firme  │     6    │   50%  ⚠️│   17%    │      17%       │
│  ⚖️ Pre-Legal    │     2    │    0%  ❌│    0%    │       0%       │
├──────────────────┴──────────┴──────────┴──────────┴────────────────┤
│  🏆 RECORDATORIO tiene la mayor tasa de conversión a pago (33%)    │
└─────────────────────────────────────────────────────────────────────┘
```

---

#### Bloque 4 — Top 5 Clientes Críticos

Los clientes que más atención gerencial requieren.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Top Clientes Críticos                                              │
├──────────────────────┬──────────┬──────────┬──────────┬────────────┤
│  Cliente             │ Días mora│  Saldo   │Gestiones │  Estado    │
├──────────────────────┼──────────┼──────────┼──────────┼────────────┤
│  DISTRIBUIDORA SUR   │  68 días │  $ 3,200 │   3 WA   │⛔ Pre-Legal│
│  GRUPO NORTE SAC     │  55 días │ S/21,400 │   2 WA   │❌ Sin ctto │
│  COMERCIAL LIMA SAC  │  47 días │ S/12,400 │2WA+acuerd│✅ Acuerdo  │
│  IMP. ANDINA         │  38 días │  S/9,800 │    1 WA  │🤝 Prometió │
│  TRÁFICO LISTO       │  31 días │  $ 1,900 │    1 WA  │📵 Sin resp.│
└──────────────────────┴──────────┴──────────┴──────────┴────────────┘
```

---

#### Bloque 5 — Fuente de datos del Dashboard

| Métrica | Tabla Supabase | Se actualiza cuando... |
|---|---|---|
| Funnel (etapas de conversión) | `gestiones` + `acuerdos_pago` + `cuotas_acuerdo` | El gestor registra resultado o marca pago |
| DSO (días prom. de cobro) | `documentos.fecha_vencimiento` + `cuotas_acuerdo.fecha_pago` | Al marcar cuota pagada |
| Tasa de recuperación | `documentos.monto_pendiente` vs `monto_total` | Al registrar pagos recibidos |
| Efectividad por plantilla | `gestiones.metadata.template` + `gestiones.resultado` | Al registrar resultado del WA |
| Cumplimiento de acuerdos | `cuotas_acuerdo.estado` | Al marcar cuota pagada o vencida |
| Tiempo de respuesta WA | `gestiones.fecha` (envío) vs `gestiones.updated_at` (resultado) | Al guardar resultado post-envío |

**Criterios de aceptación:**
- [ ] Nuevo tab "Dashboard" visible en la navegación principal
- [ ] Funnel muestra los 5 pasos con % de conversión en cada etapa
- [ ] Los 6 KPIs financieros calculados desde Supabase
- [ ] Tabla de efectividad por plantilla actualizada con datos reales
- [ ] Top clientes críticos ordenados por días de mora descendente
- [ ] Selector de período (ciclo actual / últimos 3 ciclos / mes calendario)
- [ ] No modifica `df_final` ni `df_filtered`

**Esfuerzo estimado:** 8 horas | **Prioridad:** Alta | **Archivos:** nuevo `dashboard.py`, `db_manager.py`

---

### 10.10 RC-FEAT-039 — Informe Gerencial para Comités de Directorio

**Para quién:** El jefe de cobranzas que reporta al CEO o directorio de la empresa.

**El problema hoy:** El informe mensual para el directorio se prepara manualmente, en Excel o Word, cada mes. Toma horas, puede tener errores, y no hay una presentación visual consistente. Si el directorio hace preguntas difíciles, el jefe no tiene datos rápidos para responder.

**La solución:** Un botón que genera automáticamente el informe ejecutivo completo en PDF, listo para imprimir o enviar por email al directorio.

**Filosofía del informe:** El directorio necesita 3 respuestas en 30 segundos:
1. ¿Cuánto nos deben?
2. ¿Cuánto recuperamos este mes?
3. ¿Qué riesgo hay y qué decidimos?

---

#### Sección A — Semáforo Ejecutivo (resumen en 4 tarjetas)

```
┌─────────────────────────────────────────────────────────────────────┐
│  INFORME EJECUTIVO DE GESTIÓN DE COBRANZA — DACTA S.A.C.           │
│  Cartera Cuentas por Cobrar · Período: Febrero 2026                │
│  Generado: 17/03/2026 · Área de Cobranzas · CONFIDENCIAL          │
├────────────────┬───────────────┬───────────────┬────────────────────┤
│ CARTERA        │ RECUPERADO    │ SALDO         │ EN ACUERDOS        │
│ VENCIDA TOTAL  │ EN EL PERÍODO │ PENDIENTE     │ DE PAGO            │
│                │               │               │                    │
│ S/ 141,200     │  S/ 87,400    │  S/ 53,800    │   S/ 31,200        │
│ + $ 24,800     │ Tasa: 62%     │ 28 clientes   │ 11 acuerdos        │
│                │               │               │                    │
│ ↗ +8% vs enero │ ✅ Meta: 55%  │ ⚠️ 3 en legal │ 73% cuotas al día │
└────────────────┴───────────────┴───────────────┴────────────────────┘
```

---

#### Sección B — Distribución de Cartera por Antigüedad de Deuda

```
┌─────────────────────────────────────────────────────────────────────┐
│  DISTRIBUCIÓN POR ANTIGÜEDAD DE DEUDA (AGING)                      │
├───────────────────────┬────────┬──────────┬────────┬───────────────┤
│  Segmento             │Clientes│ Saldo S/ │% Carter│  Riesgo       │
├───────────────────────┼────────┼──────────┼────────┼───────────────┤
│🟢 0 – 14 días         │   12   │  28,400  │  20%   │ BAJO          │
│🟡 15 – 30 días        │   16   │  51,200  │  36%   │ MEDIO         │
│🟠 31 – 60 días        │    9   │  41,800  │  30%   │ ALTO          │
│🔴 Más de 60 días      │    5   │  19,800  │  14%   │ CRÍTICO ⚠️    │
├───────────────────────┼────────┼──────────┼────────┼───────────────┤
│  TOTAL                │   42   │ 141,200  │ 100%   │               │
└───────────────────────┴────────┴──────────┴────────┴───────────────┘

Acción recomendada por segmento:
  🟢 0-14 días:  Primer aviso preventivo por WA o email
  🟡 15-30 días: Recordatorio + llamada si no responde en 48h
  🟠 31-60 días: Aviso firme + oferta de acuerdo de pago
  🔴 +60 días:   Derivar a Legal de forma inmediata
```

---

#### Sección C — Clientes Críticos (para decisión del directorio)

```
┌─────────────────────────────────────────────────────────────────────┐
│  🚨 CLIENTES QUE REQUIEREN DECISIÓN DEL DIRECTORIO                 │
├─────────────────────┬──────────┬──────────┬──────────┬─────────────┤
│  Cliente            │Días mora │  Saldo   │Gestiones │Recomendación│
├─────────────────────┼──────────┼──────────┼──────────┼─────────────┤
│  DISTRIBUIDORA SUR  │  68 días │  $ 3,200 │  3 WA    │Carta notarial│
│  GRUPO NORTE SAC    │  55 días │ S/21,400 │  2 WA    │Visita urgente│
│  COMERCIAL LIMA SAC │  47 días │ S/12,400 │2WA+acuerd│Monit. cuota1 │
└─────────────────────┴──────────┴──────────┴──────────┴─────────────┘
```

---

#### Sección D — Resumen de Gestiones del Período

```
┌───────────────────────────────┬────────────────────────────────────┐
│  GESTIONES REALIZADAS         │  COMPARATIVO VS MES ANTERIOR       │
├───────────────────────────────┼────────────────────────────────────┤
│  WhatsApp enviados:      38   │  Recuperación S/:  ↗ +S/ 11,200   │
│  Emails enviados:        42   │  Tasa recuperación:↗ +5% (57%→62%)│
│  Llamadas registradas:    8   │  DSO (días prom.): ↗ +3d (31→34)  │
│  Acuerdos firmados:      11 ✅│  Efectividad WA:   → igual (58%)  │
│  Derivados a Legal:       2 ⚠️│  Acuerdos activos: ↗ +4 acuerdos  │
└───────────────────────────────┴────────────────────────────────────┘
```

---

#### Sección E — Recomendaciones automáticas para el directorio

```
┌─────────────────────────────────────────────────────────────────────┐
│  💡 RECOMENDACIONES                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  🚨 ACCIÓN INMEDIATA:                                               │
│  Autorizar inicio de proceso legal para DISTRIBUIDORA SUR E.I.R.L. │
│  ($ 3,200 · 68 días). Ya se enviaron 3 comunicaciones sin respuesta.│
├─────────────────────────────────────────────────────────────────────┤
│  ⚠️ ATENCIÓN PRIORITARIA:                                           │
│  GRUPO NORTE S.A.C. (S/ 21,400 · 55 días) no ha respondido ningún  │
│  canal. Se recomienda visita presencial del Jefe de Ventas.        │
├─────────────────────────────────────────────────────────────────────┤
│  📊 OPORTUNIDAD DE MEJORA:                                          │
│  El DSO subió 3 días vs. enero. Implementar el seguimiento          │
│  automático de cuotas proyecta reducirlo en 5-8 días en 60 días.  │
├─────────────────────────────────────────────────────────────────────┤
│  ✅ LOGRO DESTACADO:                                                │
│  Tasa de recuperación 62% supera la meta de 55%. Canal WhatsApp    │
│  con 58% de tasa de respuesta, muy superior al benchmark de email. │
└─────────────────────────────────────────────────────────────────────┘
```

---

#### Panel de generación del informe (desde la app)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Dashboard > Generar Informe para Comité                           │
├─────────────────────────────────────────────────────────────────────┤
│  Período:        [ Febrero 2026          ▼ ]                        │
│  Tipo de informe:[ Mensual — Comité de Directorio ▼ ]               │
│                                                                     │
│  Incluir en el informe:                                            │
│  ☑ Resumen ejecutivo y semáforos                                   │
│  ☑ Distribución por antigüedad (aging)                             │
│  ☑ Clientes críticos y recomendaciones                             │
│  ☑ Gestiones del período (multicanal)                              │
│  ☑ Comparativo vs. período anterior                                │
│  ☑ Recomendaciones automáticas                                     │
│  ☐ Detalle de acuerdos de pago                                     │
│                                                                     │
│  [ 📥 Generar PDF Gerencial ]  [ 📧 Enviar por email al Directorio ]│
└─────────────────────────────────────────────────────────────────────┘
```

**Preguntas del directorio que este informe responde:**

| Pregunta | Fuente en la app |
|---|---|
| ¿Cuánto nos deben en total? | `documentos` (monto pendiente total) |
| ¿Cuánto cobramos este mes? | `cuotas_acuerdo.estado=PAGADA` + pagos directos |
| ¿Cuánto está en riesgo de no cobrarse? | Clientes +60 días sin acuerdo ni pago |
| ¿A quántos clientes contactamos? | `gestiones` por tipo y período |
| ¿Qué canal funciona mejor? | % efectividad por tipo de gestión |
| ¿Cuántos acuerdos están activos? | `acuerdos_pago.estado=ACTIVO` |
| ¿Cuántos clientes derivamos a legal? | `gestiones.resultado=ESCALAR_LEGAL` |

**Criterios de aceptación:**
- [ ] Nuevo panel en Tab Dashboard con selector de período y tipo de informe
- [ ] El PDF generado incluye las 5 secciones con datos reales de Supabase
- [ ] Botón "Enviar por email al directorio" usa los emails configurados en Config
- [ ] El informe se puede generar para cualquier ciclo histórico, no solo el actual
- [ ] Los datos provienen exclusivamente de lo que el gestor ya registró (sin preparación manual)
- [ ] Diseño visual de nivel ejecutivo (no un Excel volcado a PDF)

**Esfuerzo estimado:** 12 horas | **Prioridad:** Alta | **Archivos:** nuevo `dashboard.py`, `db_manager.py`, nuevo `report_generator.py`

---

## 11. Matriz de priorización

Esta tabla es la base para decidir qué se construye primero. Los criterios son: valor para el negocio, esfuerzo de implementación, y si hay dependencias que bloqueen otros tickets.

| # | Ticket | Descripción | Valor negocio | Esfuerzo | Riesgo | Dependencias |
|---|---|---|---|---|---|---|
| 1 | **RC-SEC-001** | Seguridad credenciales | 🔴 Urgente — riesgo real de exposición | 3h | Medio | Ninguna |
| 2 | **RC-UX-001** | Feedback visual envío WA | 🟠 Alto — el gestor lo nota cada vez | 3h | Bajo | Ninguna |
| 3 | **RC-FEAT-027** | Plantilla por Aging | 🟠 Alto — previene errores de tono | 2h | Bajo | Ninguna |
| 4 | **RC-FEAT-038** | Dashboard de Efectividad | 🟠 Alto — visibilidad para supervisor | 8h | Medio | Ninguna |
| 5 | **RC-FEAT-039** | Informe Gerencial PDF | 🟠 Alto — herramienta para directorio | 12h | Medio | RC-FEAT-038 |
| 6 | **RC-FEAT-028** | KPIs operativos del ciclo | 🟡 Medio — complementa el Dashboard | 3h | Bajo | Ninguna |
| 7 | **RC-FEAT-001** | Selector tri-modal WA | 🟡 Medio — el modo imagen ya funciona | 4h | Medio | Ninguna |
| 8 | **RC-FEAT-037** | Catálogo resultados | 🟡 Medio — flexibilidad sin redeploy | 4h | Bajo | Ninguna |
| 9 | **RC-FEAT-036** | Tabla wa_mensajes | ⚪ Bajo — arquitectura interna | 5h | Bajo | Ninguna |
| 10 | **RC-BUG-050** | Join mensaje WA | ⚪ Bajo — mejora historial | 2h | Bajo | RC-FEAT-036 |
| 11 | **RC-FEAT-035** | Link "Ver CRM" | ⚪ Bajo — comodidad UX | 2h | Bajo | Ninguna |

### Propuesta de orden de sprints

> ⚠️ **Esta propuesta es un punto de partida para la conversación con el PO.** Las prioridades se confirman en la sesión de revisión del FRD.

**Sprint 1 — Seguridad y Quick Wins operativos:**
1. RC-SEC-001 — seguridad (no tiene fecha pero el riesgo es constante)
2. RC-UX-001 — feedback visual WA (impacto inmediato en experiencia del gestor)
3. RC-FEAT-027 — plantilla por aging (2 horas, alto valor)

**Sprint 2 — Visibilidad para el supervisor:**
4. RC-FEAT-028 — KPIs operativos del ciclo
5. RC-FEAT-038 — Dashboard de Efectividad (el más importante del backlog)

**Sprint 3 — Reportes para directorio:**
6. RC-FEAT-039 — Informe Gerencial exportable

**Sprint 4 — Mejoras y deuda técnica:**
7. RC-FEAT-001 — selector tri-modal WA
8. RC-FEAT-037 — catálogo de resultados
9. RC-FEAT-036 + RC-BUG-050 — arquitectura mensajes WA
10. RC-FEAT-035 — link "Ver CRM"

---

## 12. Quality Gates

Todo cambio debe pasar **todos los gates** antes de declararse "listo". No hay excepciones.

| Gate | Acción | Criterio mínimo |
|---|---|---|
| **Gate 0** | Compilación | `python -m py_compile app.py utils/**/*.py` sin errores |
| **Gate 1** | Tests automáticos | `pytest tests/ -v` → 100% PASS |
| **Gate 2** | Modo QA verificado | No enviar emails ni WA reales en ambiente de prueba |
| **Gate 3** | Smoke manual | Screenshots de CA-1 a CA-5 en staging (localhost:8502) |
| **Gate 4** | Documentación | FRD + changelog + TICKETS_ANTAY actualizados |

---

## 13. Criterios de aceptación globales

Estos criterios aplican a **cualquier entrega**, sin importar qué feature o fix se esté implementando.

| ID | Descripción |
|---|---|
| CA-1 | Fresh Load → KPIs Email: Enviados=0, Pendientes>0. Tracking inicial PENDIENTE |
| CA-2 | Filtrar Reporte → Tab Email refleja exactamente el mismo subconjunto |
| CA-3 | Clientes con deuda 0 no aparecen para notificar (salvo detracción pendiente) |
| CA-4 | Emails compartidos: no bloquea selección; KPIs contados por CodCliente, no por email |
| CA-5 | Post-envío: tracking actualizado, KPIs actualizados, Reporte Post-Envío persiste |
| CA-6 | WA masivo: cada cliente se graba en Supabase inmediatamente, no al final del lote |
| CA-7 | WA masivo: resultado en Supabase es individual por cliente (no todos iguales) |
| CA-8 | Timestamps en Supabase siempre en UTC real (sin desfase de 5 horas) |
| CA-9 | Banner STAGING visible en sidebar cuando se usa el ambiente de prueba |

---

## 14. Ambientes

| Ambiente | Puerto | Base de datos | Cómo arrancar |
|---|---|---|---|
| **PROD** (servidor QA) | 8501 | Supabase PROD | Ejecutar `5_COMBINADO_APP_Y_TUNEL.bat` en `\\QA\antay-cobranza` |
| **STAGING** (local) | 8502 | Supabase STAGING | `streamlit run app.py --server.port 8502` con `.env.staging` |

**Detección automática de ambiente:** Si `SUPABASE_URL` contiene la URL del proyecto de staging → banner naranja visible en el sidebar.

**Flujo de despliegue (deploy):**
```
1. Desarrollar + probar en STAGING (localhost:8502)
2. Gate 0 + Gate 1 (compilación + tests)
3. Gate 3 (smoke manual en STAGING con screenshots)
4. Aprobación explícita del PO
5. Copiar archivos a \\QA\antay-cobranza\ (deploy al servidor)
6. Smoke test en servidor QA
7. Commit + push + merge dev → main
```

> **Regla absoluta:** Nunca hacer deploy ni push a main sin aprobación explícita del PO.

---

## 15. Changelog

| Versión | Fecha | Descripción del cambio |
|---|---|---|
| v0.1 | 2025-12-22 | Versión inicial — Email + tracking básico |
| v0.2 | 2026-01-15 | Estabilización ciclo Email + tracking + UX mínima |
| v0.3 | 2026-02-15 | Integración Supabase cloud-only, ciclos persistentes |
| v1.6.0 | 2026-03-13 | TIER 1 CRM WhatsApp completo — 141/141 tests |
| v1.7.1 | 2026-03-13 | Módulo Clientes Premium + Home 2 archivos + hotfixes SQL |
| v1.7.2 | 2026-03-14 | Mejoras CRM flow + auto-restore + banner STAGING |
| v1.7.3 | 2026-03-15 | Fix sub-tab seguimiento WA (RC-BUG-030/031) |
| v1.8.0 | 2026-03-16 | TIER 2: panel prueba WA + 9 mejoras UX post-envío |
| v1.8.1 | 2026-03-16 | RC-BUG-043 a RC-BUG-053: serie fixes WA seguimiento |
| v1.8.2 | 2026-03-16 | RC-BUG-054/055/056: timestamps UTC, metadata, cycle_id |
| v1.8.3 | 2026-03-16 | Trazabilidad individual + persistencia en tiempo real |
| v4.0 FRD | 2026-03-17 | Reposicionamiento como plataforma B2B · Incorporación Dashboard de Efectividad (RC-FEAT-038) e Informe Gerencial (RC-FEAT-039) con diseños completos · Reorganización y priorización del backlog completo |
| **v4.1 FRD** | **2026-03-17** | **Homologación con datos reales de la app: 8 plantillas WA reales, 7 resultados de gestión con estándar de industria cobranza B2B (PROMESA_PAGO, SOLICITO_PLAZO, EN_NEGOCIACION, ESCALAR_LEGAL, DISPUTA), corrección aging por plantilla** |
| **v1.9.0 app** | **2026-03-23** | **RC-FEAT-060: Dashboard — funnel jerárquico con sub-filas auditables, último resultado por cliente único en "¿Qué respondieron?", Top Clientes con @st.fragment + Nivel mora + Gestionados + Docs S$/US$ · 162/162 tests** |

---

*Documento preparado por Antay Fábrica de Software para DACTA S.A.C.*
*Nivel de confidencialidad: USO INTERNO*
