## STATUS VIGENTE — Refactorización BD + Fix WhatsApp (2026-02-25)

- Fecha/Hora: 2026-02-25
- Rama activa: `main`
- Estado global técnico: Refactorización de `ciclos_procesamiento` EN CURSO

---

### Trabajo completado en esta sesión

#### 1. Fix bug RC-OPS-004 — Registro duplicado WhatsApp
**Problema:** Al enviar WhatsApp se creaban 2 registros: uno correcto en `gestiones` y uno incorrecto en `notificaciones` (con canal hardcodeado como EMAIL).
**Archivos modificados:**
- `utils/ui/tabs/whatsapp.py` — Eliminado `persist_notification_event()`, agregado `cycle_id` en metadata de `insert_gestion()`
- `utils/db_manager.py` — Nueva función `get_wa_gestiones_by_cycle()`, actualizada `reconcile_tracking_from_notifications()` para leer WA desde `gestiones`
- `utils/ui/tabs/crm_gestiones.py` — Corregido canal hardcodeado "Email" en drill-down CRM

#### 2. Limpieza de base de datos
Las siguientes tablas fueron vaciadas para iniciar refactorización limpia:
- `ciclos_procesamiento` → VACÍA
- `gestiones` → VACÍA
- `notificaciones` → VACÍA
- `clientes` → **INTACTA** (no se tocó)

---

### Trabajo PENDIENTE — Refactorización ciclos_procesamiento

**Problema identificado:** La tabla `ciclos_procesamiento` guarda todo el DataFrame como JSON blob en un campo `df_final_json`. Esto es un anti-patrón que impide queries sobre documentos históricos.

**Solución acordada:** Modelo cabecera/detalle
- `ciclos_procesamiento` — solo metadatos (sin `df_final_json`)
- `documentos_ciclo` — **NUEVA tabla**, una fila por documento (aún no existe en Supabase)

**Documentación completa:** Ver `docs/ARQUITECTURA_BD_DECISIONES_v1.0.md`

**Próximos pasos en orden:**
1. Crear tabla `documentos_ciclo` en Supabase (SQL en doc de arquitectura)
2. Reescribir `utils/state_manager.py` — funciones `save_session_cloud()`, `load_session_cloud()`, `load_session_by_id()`, `clear_session_cloud()`
3. Reescribir `migrate_historical.py` — desactivar upsert clientes, usar `documentos_ciclo`, solo escribir email en `notificaciones`
4. Ejecutar migración `--dry-run` → luego real
5. Verificar selector de ciclos y auto-restore en app

---

### Regla maestra de routing (NO VIOLAR)

| Canal | Tabla | Prohibido |
|-------|-------|-----------|
| EMAIL | `notificaciones` | ~~gestiones~~ |
| WHATSAPP | `gestiones` | ~~notificaciones~~ |
| LLAMADA/VISITA/NOTA | `gestiones` | ~~notificaciones~~ |

---

### Archivos desplegados en QA (\\QA\antay-cobranza)

- `utils/ui/tabs/whatsapp.py` ✅
- `utils/db_manager.py` ✅
- `utils/ui/tabs/crm_gestiones.py` ✅

---

### Referencia anterior
Estado previo: SUPABASE-002 completado (2026-02-17) — ver historial en git.
