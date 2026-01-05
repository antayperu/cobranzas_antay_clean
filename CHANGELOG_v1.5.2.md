# CHANGELOG v1.5.2 - Fullscreen UX + Tracking Fix

**Fecha:** 2025-12-31  
**Versión:** v1.5.2-fullscreen-tracking-fix  
**Tipo:** UX Enhancement + Bug Fixes

---

## Resumen Ejecutivo

Esta versión implementa mejoras de UX (vista fullscreen para tabla) y corrige bugs críticos en el sistema de tracking de notificaciones. **NO se modificó lógica de procesamiento, envío de emails, ni persistencia core.**

---

## Cambios por Archivo

### 1. `app.py`

#### Líneas 6-55: Detección de Vista Fullscreen
- **Propósito:** UI - Detectar query parameter `?view=full_table` para modo fullscreen
- **Cambio:** Agregada lógica para configurar página sin sidebar cuando `is_fullscreen_view=True`
- **Impacto:** Solo UI, no afecta lógica de negocio

#### Líneas 238-260: Auto-Restauración de Sesión
- **Propósito:** UX - Restaurar sesión automáticamente al volver de fullscreen
- **Cambio:** Agregado bloque que auto-carga `df_final` desde persistencia si `data_ready=False` y existe sesión válida
- **Condición:** NO auto-restaura si `loading_new_files=True` (usuario cargando archivos nuevos)
- **Impacto:** Mejora UX, no modifica lógica de procesamiento

#### Líneas 366-369: Reseteo de Flag `loading_new_files`
- **Propósito:** Bug Fix - Prevenir bloqueo de uploaders
- **Cambio:** Agregado `st.session_state['loading_new_files'] = False` después de procesar archivos exitosamente
- **Impacto:** Solo control de flujo UI

#### Líneas 664-670: Eliminación de Reseteo Prematuro de `fresh_load`
- **Propósito:** Bug Fix - Prevenir actualización desde DB con datos del ciclo anterior
- **Cambio:** Eliminada línea `st.session_state['fresh_load'] = False` que causaba contaminación de tracking
- **Impacto:** Corrige bug de "Enviados Hoy = 1" en ciclo nuevo

#### Líneas 1284-1302: Tab Email - Uso de Vista Filtrada
- **Propósito:** Bug Fix - Restaurar regla histórica de filtros compartidos
- **Cambio:** Cambiado de `df_final` (dataset completo) a `df_filtered` (vista filtrada) para construir destinatarios
- **Impacto:** Tab Email ahora respeta filtros del Reporte General

#### Líneas 1307-1320: Tab Email - Contadores sin Contaminación
- **Propósito:** Bug Fix - Prevenir contaminación de contadores con datos del ciclo anterior
- **Cambio:** Agregada condición `if not is_fresh_load` antes de consultar DB para "Enviados Hoy"
- **Impacto:** En ciclo nuevo, "Enviados Hoy" = 0 correctamente

#### Línea 1464: Vista Previa HTML - Uso de Vista Filtrada
- **Propósito:** Bug Fix - Asegurar consistencia entre Reporte General y Preview HTML
- **Cambio:** Cambiado de `df_final` a `df_email_view` para generar documentos del preview
- **Impacto:** Preview HTML muestra solo documentos de la vista filtrada actual

---

### 2. `utils/ui/report_view.py`

#### Líneas 99-117: Botón Fullscreen
- **Propósito:** UI - Agregar botón para abrir vista fullscreen
- **Cambio:** Agregado link HTML con `target="_self"` (NO `_blank` para preservar session_state)
- **Impacto:** Solo UI, no afecta lógica de negocio

#### Líneas 160-203: Función `render_report_fullscreen`
- **Propósito:** UI - Renderizar tabla en modo fullscreen
- **Cambio:** Nueva función que renderiza tabla ocupando ~100% del viewport
- **Impacto:** Solo UI, no afecta lógica de negocio

---

### 3. `utils/ui/sidebar.py`

#### Líneas 50-52: Flag `loading_new_files`
- **Propósito:** Bug Fix - Prevenir auto-restauración durante carga de archivos nuevos
- **Cambio:** Agregado `st.session_state['loading_new_files'] = True` al confirmar "Reemplazar"
- **Impacto:** Solo control de flujo UI

---

### 4. `utils/processing.py`

#### Líneas 454-458: Inicialización de Tracking (SIN CAMBIOS RECIENTES)
- **Estado:** Inicializa solo 2 columnas: `ESTADO_EMAIL` (default "PENDIENTE") y `FECHA_ULTIMO_ENVIO` (default "")
- **Confirmación:** NO se modificó en esta versión

---

## Confirmaciones de NO Modificación

✅ **NO se modificó:**
- `utils/processing.py` - Lógica de procesamiento de datos
- `utils/email_sender.py` - Lógica de envío de emails
- `utils/state_manager.py` - Lógica de persistencia
- `utils/db_manager.py` - Lógica de base de datos
- Reglas de negocio core (cálculo de saldos, detracciones, etc.)

✅ **Solo se modificó:**
- UI/UX (fullscreen, botones, navegación)
- Control de flujo (flags de estado, auto-restauración)
- Corrección de bugs (filtros compartidos, contadores, tracking)

---

## Bugs Corregidos

### Bug 1: Pérdida de Sesión al Volver de Fullscreen
- **Síntoma:** Al cerrar vista fullscreen, usuario veía pantalla "Bienvenido"
- **Causa:** Navegación con query params reinicializaba `session_state`
- **Fix:** Auto-restauración de sesión desde persistencia

### Bug 2: Uploaders Bloqueados
- **Síntoma:** Al confirmar "Cargar Nuevos Archivos", uploaders no aparecían
- **Causa:** Auto-restauración se ejecutaba antes del sidebar y bloqueaba modo carga
- **Fix:** Flag `loading_new_files` previene auto-restauración durante carga

### Bug 3: "Enviados Hoy" Contaminado
- **Síntoma:** En ciclo nuevo, "Enviados Hoy" mostraba 1 en lugar de 0
- **Causa:** Tab Email consultaba DB con datos del ciclo anterior
- **Fix:** NO consultar DB si `fresh_load=True`

### Bug 4: Filtros No Compartidos
- **Síntoma:** Filtros del Reporte General no se reflejaban en tab Email
- **Causa:** Tab Email usaba `df_final` (dataset completo) en lugar de `df_filtered`
- **Fix:** Cambio a `df_filtered` para destinatarios y preview HTML

---

## Comandos Git para Rollback

```bash
# Crear tag de rollback ANTES de estos cambios
git tag v1.5.0-stable HEAD~10
git push origin v1.5.0-stable

# Si necesitas revertir a estado estable
git checkout v1.5.0-stable
git checkout -b rollback-to-stable
git push origin rollback-to-stable
```

---

## Próximos Pasos

1. **Ejecutar Gate 3 manual** (checklist en `GATE3_CHECKLIST_v1.5.2.md`)
2. **Ejecutar pytest** (`pytest tests/test_business_rules.py -v`)
3. **Validar CI/CD** (GitHub Actions debe pasar)
4. **Solo después de PASS:** Merge a main y tag `v1.5.2`
