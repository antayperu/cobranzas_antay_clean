# ARQUITECTURA BD — DECISIONES Y CONTRATOS DE TABLAS
**Versión:** 1.0
**Fecha:** 2026-02-25
**Estado:** VIGENTE — Refactorización en curso

---

## 1. REGLA MAESTRA DE ROUTING DE CANALES

Esta es la regla más importante del sistema. Toda IA que continúe este trabajo debe respetarla sin excepción:

| Canal | Tabla de escritura | Tabla PROHIBIDA |
|-------|-------------------|-----------------|
| **EMAIL** | `notificaciones` | ~~gestiones~~ |
| **WHATSAPP** | `gestiones` | ~~notificaciones~~ |
| **LLAMADA / VISITA / NOTA / OTRO** | `gestiones` | ~~notificaciones~~ |

### Por qué esta regla existe
La tabla `notificaciones` fue diseñada exclusivamente para tracking de envíos de email (integración SendGrid/Resend). La tabla `gestiones` es el CRM general de interacciones.

Antes de 2026-02-25, el código cometía el error de escribir también en `notificaciones` al enviar WhatsApp (comentario RC-OPS-004), lo cual creaba registros duplicados y contaminaba los KPIs de email. **Ese bug fue corregido.**

---

## 2. CORRECCIÓN APLICADA — BUG RC-OPS-004

### Síntoma
Al enviar WhatsApp, aparecían 2 registros en el CRM:
1. ✅ Correcto: `gestiones` → Canal=WHATSAPP, Resultado=EXITOSO
2. ❌ Incorrecto: `notificaciones` → Canal=EMAIL (hardcodeado), Asunto="WhatsApp Estado de Cuenta"

### Causa raíz
`utils/ui/tabs/whatsapp.py` llamaba a `dbm.persist_notification_event()` con `metadata_extra={"channel": "WHATSAPP"}` para "cycle tracking reconciliation". Eso escribía en `notificaciones`.

### Corrección aplicada
**Archivo:** `utils/ui/tabs/whatsapp.py`
- Eliminado: bloque `dbm.persist_notification_event()` completo
- Modificado: `dbm.insert_gestion()` ahora recibe `metadata_extra={"cycle_id": current_cycle_id}`

**Archivo:** `utils/db_manager.py`
- Agregada: función `get_wa_gestiones_by_cycle(cycle_id)` — consulta `gestiones` donde `tipo_gestion='WHATSAPP'` y filtra por `metadata.cycle_id` en Python
- Modificada: `reconcile_tracking_from_notifications()` — ahora EMAIL viene de `notificaciones` y WHATSAPP viene de `gestiones`

**Archivo:** `utils/ui/tabs/crm_gestiones.py`
- Corregido: en `_render_client_drilldown()`, el canal de las notificaciones ya no está hardcodeado como "Email" — se lee desde `metadata.channel`

---

## 3. REFACTORIZACIÓN PENDIENTE — CICLOS PROCESAMIENTO

### Estado actual (anti-patrón — a refactorizar)
La tabla `ciclos_procesamiento` tiene una columna `df_final_json` que almacena todo el DataFrame del ciclo como un JSON blob en un solo campo. Esto es un anti-patrón "fat column" que impide hacer queries sobre los documentos históricos.

### Diseño objetivo (cabecera + detalle)

**Tabla cabecera:** `ciclos_procesamiento` (mantener, solo eliminar `df_final_json`)
```sql
cycle_id     TEXT PRIMARY KEY
fecha        TIMESTAMP
row_count    INTEGER
estado       TEXT
metadata     JSONB   -- archivo origen, fecha corte, etc. (NO datos de documentos)
created_at   TIMESTAMP
expires_at   TIMESTAMP
```

**Tabla detalle:** `documentos_ciclo` (NUEVA — crear en Supabase)
```sql
id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
cycle_id         TEXT REFERENCES ciclos_procesamiento(cycle_id) ON DELETE CASCADE
cliente_id       TEXT
empresa          TEXT
comprobante      TEXT
fech_emis        DATE
fech_venc        DATE
moneda           TEXT
mont_emit        NUMERIC
saldo            NUMERIC
saldo_real       NUMERIC
detraccion       NUMERIC
estado_detraccion TEXT
correo           TEXT
telefono         TEXT
estado_email     TEXT   -- PENDIENTE | ENVIADO | FALLIDO
estado_whatsapp  TEXT   -- PENDIENTE | ENVIADO | FALLIDO
fecha_ultimo_envio TEXT
fecha_ultimo_wa  TEXT
created_at       TIMESTAMP DEFAULT now()
```

### Archivos a modificar
1. `utils/state_manager.py` — 3 funciones afectadas:
   - `save_session_cloud()`: en lugar de JSON blob → upsert cabecera + insert filas en `documentos_ciclo`
   - `load_session_cloud()`: en lugar de leer blob → query `documentos_ciclo` WHERE cycle_id = último
   - `load_session_by_id()`: igual pero para cycle_id específico
   - `clear_session_cloud()`: agregar DELETE en `documentos_ciclo` también

2. `migrate_historical.py` — reescribir `insert_ciclo()`:
   - Solo insertar metadatos en `ciclos_procesamiento` (sin `df_final_json`)
   - Insertar cada fila del Excel en `documentos_ciclo`

### Estado de la base de datos al 2026-02-25
Las siguientes tablas fueron **limpiadas completamente** para iniciar la refactorización sin data basura:
- `ciclos_procesamiento` → VACÍA ✅
- `gestiones` → VACÍA ✅
- `notificaciones` → VACÍA ✅
- `clientes` → **INTACTA** (no tocar) ✅

La tabla `documentos_ciclo` **aún no existe** en Supabase — debe crearse.

---

## 4. SCRIPT migrate_historical.py — AJUSTES PENDIENTES

El script `migrate_historical.py` (raíz del proyecto) necesita los siguientes cambios antes de ejecutarse:

1. **Desactivar upsert de clientes** — La tabla `clientes` ya tiene data correcta en Supabase. El upsert sobreescribiría data actual con datos viejos de Excel.

2. **Cambiar escritura de ciclo** — En lugar de guardar `df_final_json`, insertar filas en `documentos_ciclo`.

3. **Eliminar escritura a gestiones** — El script actualmente escribe en AMBAS tablas (`gestiones` + `notificaciones`) para emails históricos. Solo debe escribir en `notificaciones` (regla maestra de routing).

4. **Archivos a migrar** (en `data/historical_cycles/`):
   - `DACTA_S.A.C._ReporteCobranzas_20251230_1453.xlsx` → `HIST_20251230_1453`
   - `DACTA_S.A.C._ReporteCobranzas_20260105_1340.xlsx` → `HIST_20260105_1340`
   - `DACTA_S.A.C._ReporteCobranzas_20260114_1800.xlsx` → `HIST_20260114_1800`
   - `DACTA_S.A.C._ReporteCobranzas_20260204_1812.xlsx` → `HIST_20260204_1812`
   - `DACTA_S.A.C._ReporteCobranzas_20260219_2127.xlsx` → `HIST_20260219_2127`

---

## 5. FLUJO COMPLETO DE ESCRITURA POR ACCIÓN

### Al enviar Email masivo
```
email_notifications.py
  └─► dbm.persist_notification_event(metadata_extra={"channel": "EMAIL"})
        └─► INSERT notificaciones (channel=EMAIL, cycle_id=X)
```

### Al enviar WhatsApp masivo
```
whatsapp.py
  └─► dbm.insert_gestion(tipo_gestion='WHATSAPP', metadata_extra={"cycle_id": X})
        └─► INSERT gestiones (tipo=WHATSAPP, cycle_id en metadata)
```

### Al guardar un ciclo nuevo (objetivo tras refactorización)
```
state_manager.save_session_cloud(df, cycle_id)
  ├─► UPSERT ciclos_procesamiento (solo metadatos)
  └─► INSERT documentos_ciclo (una fila por documento del Excel)
```

### Al cargar un ciclo (objetivo tras refactorización)
```
state_manager.load_session_by_id(cycle_id)
  └─► SELECT documentos_ciclo WHERE cycle_id = X
        └─► pd.DataFrame(rows)  → reconstruye df_final
```

---

## 6. PRÓXIMOS PASOS EN ORDEN

1. **Crear tabla `documentos_ciclo`** en Supabase (SQL en sección 3)
2. **Reescribir `state_manager.py`** — funciones save/load
3. **Reescribir `migrate_historical.py`** — con los 3 ajustes de sección 4
4. **Ejecutar migración** en modo `--dry-run` primero, luego real
5. **Verificar** que el selector de ciclos y auto-restore funcionen
