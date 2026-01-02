# FULLSCREEN_SESSION_FLOW - Auto-Restore Implementation

**Fecha:** 2025-12-31 22:00  
**Versión:** v1.5.2-session-auto-restore  
**Problema:** Pérdida de sesión al volver de vista fullscreen

---

## Problema Reportado

**Flujo incorrecto:**
1. Usuario tiene sesión activa (datos cargados)
2. Click "Ver en Pantalla Completa" → navega a `/?view=full_table`
3. Click "✖ Cerrar" → vuelve a `/`
4. **BUG:** App muestra pantalla "Bienvenido" pidiendo cargar excels o click en "Continuar Trabajo Anterior"
5. Usuario pierde continuidad del flujo

**Flujo correcto esperado:**
1. Usuario tiene sesión activa
2. Click "Ver en Pantalla Completa"
3. Click "✖ Cerrar"
4. **ESPERADO:** Vuelve al Reporte General con misma sesión activa, sin interrupciones

---

## Root Cause Analysis (RCA)

### Causa Raíz

La navegación con `target="_self"` + query params en Streamlit causa **reload completo del script**, lo que:

1. Reinicializa `st.session_state` (nuevo WebSocket)
2. `data_ready` vuelve a `False`
3. `df_final` se pierde
4. App detecta "no hay datos" y muestra pantalla de carga

### Por qué ocurre

Streamlit no mantiene `session_state` entre navegaciones con query params diferentes. Cada URL con query params distintos es tratada como una "nueva sesión" en términos de estado en memoria.

**Evidencia:**
- URL original: `http://localhost:8501/` → session_state A
- URL fullscreen: `http://localhost:8501/?view=full_table` → session_state B (nuevo)
- Volver a `/`: session_state C (nuevo otra vez)

---

## Solución Implementada: Plan B (Auto-Restauración)

### Estrategia

En lugar de intentar prevenir el reload (imposible sin refactor masivo), **auto-restaurar la sesión silenciosamente** desde persistencia cuando se detecta que no hay datos pero sí existe sesión guardada.

### Implementación

**Archivo:** `app.py`  
**Líneas:** 238-258 (antes del sidebar)

```python
# --- AUTO-RESTORE SESSION (PLAN B: Fullscreen Navigation Fix) ---
# Si no hay datos en session_state pero existe sesión persistida válida,
# auto-restaurar silenciosamente para preservar continuidad al volver de fullscreen
if not st.session_state.get('data_ready', False):
    has_session, session_info = state_mgr.has_valid_session()
    if has_session:
        try:
            df_loaded, meta_loaded, cache_ts_loaded = state_mgr.load_session()
            if df_loaded is not None and not df_loaded.empty:
                # Auto-restaurar sesión sin requerir click del usuario
                st.session_state['df_final'] = df_loaded
                st.session_state['data_ready'] = True
                st.session_state['session_start_ts'] = cache_ts_loaded
                st.session_state['uploaded_files'] = meta_loaded.get('uploaded_files', [])
                st.session_state['fresh_load'] = False
                # Silencioso: no mostrar mensaje, solo restaurar estado
        except Exception as e:
            # Si falla la auto-restauración, continuar normalmente
            # El usuario verá la pantalla de carga normal
            pass
```

### Flujo Corregido

1. Usuario carga excels → sesión activa → datos guardados en persistencia
2. Click "Ver en Pantalla Completa" → navega a `/?view=full_table`
   - Reload de script → `session_state` nuevo
   - **Auto-restauración:** Detecta sesión persistida → carga `df_final` automáticamente
   - Usuario ve tabla en fullscreen sin interrupciones
3. Click "✖ Cerrar" → vuelve a `/`
   - Reload de script → `session_state` nuevo
   - **Auto-restauración:** Detecta sesión persistida → carga `df_final` automáticamente
   - Usuario ve Reporte General con mismos datos, sin "Bienvenido"

---

## Cambios Realizados

### Archivos Modificados

| Archivo | Líneas | Cambio |
|---------|--------|--------|
| `app.py` | 238-258 | Agregado bloque de auto-restauración antes del sidebar |
| `app.py` | 250-275 | Modificado: botón "Continuar Trabajo Anterior" ahora es opcional (no bloquea flujo) |

### Comportamiento Actualizado

**Antes:**
- Volver de fullscreen → pantalla "Bienvenido" → usuario debe click "Continuar Trabajo Anterior"

**Después:**
- Volver de fullscreen → **auto-restauración silenciosa** → usuario ve Reporte General directamente

**Botón "Continuar Trabajo Anterior":**
- Sigue disponible como opción manual
- Ya no es obligatorio para continuar el flujo
- Solo se muestra si la auto-restauración no se ejecutó (caso edge)

---

## Validación (Gate 3)

### Caso 1: Sesión Activa → Fullscreen → Cerrar
**Pasos:**
1. Cargar 3 excels → generar Reporte General
2. Click "🖥️ Ver en Pantalla Completa"
3. Click "✖ Cerrar"

**Resultado esperado:**
- ✅ Vuelve al Reporte General
- ✅ Mismos datos visibles
- ✅ Tracking intacto (enviados/pendientes)
- ✅ Sin pantalla "Bienvenido"
- ✅ Sin pedir cargar excels

### Caso 2: Fullscreen sin Datos
**Pasos:**
1. Ir directo a `http://localhost:8501/?view=full_table` (sin cargar excels antes)
2. Click "🔙 Volver"

**Resultado esperado:**
- ✅ Vuelve a `/`
- ✅ Muestra pantalla de carga normal
- ✅ Sin errores

### Caso 3: Tracking Intacto
**Pasos:**
1. Enviar emails a 5 clientes → tracking actualizado
2. Click "Ver en Pantalla Completa"
3. Click "Cerrar"
4. Verificar columnas `ESTADO_EMAIL` y `FECHA_ULTIMO_ENVIO`

**Resultado esperado:**
- ✅ Tracking preservado (5 enviados, resto pendientes)
- ✅ Fechas de envío intactas

---

## Compliance

✅ **No se tocó lógica de negocio** (procesamiento, envío, tracking)  
✅ **No se modificó SSOT** (solo restauración de estado)  
✅ **Fix mínimo** (20 líneas agregadas)  
✅ **Gate 0 PASS** (sintaxis correcta)  
✅ **Preserva flujo operativo** (usuario no ve interrupciones)  

---

## Lecciones Aprendidas

1. **Streamlit session_state no persiste entre query params**: Cada URL con query params distintos reinicializa el estado
2. **Persistencia es clave**: Sin `state_mgr.save_session()`, la auto-restauración no sería posible
3. **UX silenciosa**: Auto-restaurar sin mensajes mejora la experiencia vs. requerir clicks manuales

---

## Próximos Pasos (Gate 3 Manual)

**Usuario debe validar:**
- [ ] Caso 1: Sesión activa → fullscreen → cerrar (sin pérdida de datos)
- [ ] Caso 2: Fullscreen sin datos (sin errores)
- [ ] Caso 3: Tracking intacto después de fullscreen

**Evidencia requerida:** Screenshots de cada caso
