# FULLSCREEN_NAV_FIX - Root Cause Analysis

**Fecha:** 2025-12-31 21:03  
**Versión:** v1.5.2-fullscreen-nav-fix  
**Problema:** Pérdida de session_state al cerrar vista fullscreen

---

## Problema Reportado

Al hacer clic en "✖ Cerrar" desde la vista fullscreen (`/?view=full_table`), el usuario volvía a la vista principal pero **perdía el estado de la sesión** (datos cargados, filtros, etc.), sintiendo como si fuera un "fresh start".

---

## Root Cause Analysis (RCA)

### Causa Raíz

El botón "🖥️ Ver en Pantalla Completa" estaba configurado con `target="_blank"`, lo que abría la vista fullscreen en una **nueva pestaña del navegador**.

### Por qué causaba pérdida de sesión

En Streamlit, cada **pestaña del navegador** tiene su **propio WebSocket y session_state independiente**:

1. **Pestaña Original**: Tiene `st.session_state['df_final']` con datos cargados
2. **Nueva Pestaña** (fullscreen con `target="_blank"`): Crea **nuevo session_state vacío**
3. Al cerrar y volver a `/`, el usuario quedaba en la **nueva pestaña** (sin datos), no en la original

### Evidencia Técnica

```html
<!-- ANTES (❌ INCORRECTO) -->
<a href="?view=full_table" target="_blank">
    🖥️ Ver en Pantalla Completa
</a>
<!-- Abre NUEVA pestaña → NUEVO session_state → pérdida de datos -->

<!-- DESPUÉS (✅ CORRECTO) -->
<a href="?view=full_table" target="_self">
    🖥️ Ver en Pantalla Completa
</a>
<!-- Navega en MISMA pestaña → MISMO session_state → datos preservados -->
```

---

## Solución Implementada

### Cambio Mínimo

**Archivo:** `utils/ui/report_view.py`  
**Línea:** 106  
**Cambio:** `target="_blank"` → `target="_self"`

### Flujo Corregido

1. Usuario en vista normal con datos cargados (`st.session_state['df_final']` poblado)
2. Click "🖥️ Ver en Pantalla Completa" → navega a `/?view=full_table` en **misma pestaña**
3. Vista fullscreen usa **mismo session_state** (datos disponibles)
4. Click "✖ Cerrar" → navega a `/` en **misma pestaña**
5. Usuario vuelve a vista normal con **mismo session_state** (datos preservados)

---

## Validación (Gate 3)

### Caso 1: Sesión Activa
- ✅ Cargar excels → generar reporte
- ✅ Click "Ver en Pantalla Completa"
- ✅ Click "✖ Cerrar"
- ✅ **Resultado:** Vuelve al home con sesión activa (datos preservados)

### Caso 2: Sin Datos
- ✅ Ir directo a `/?view=full_table`
- ✅ Click "Volver/Cerrar"
- ✅ **Resultado:** Vuelve a `/` sin error

### Caso 3: No Pestañas Nuevas
- ✅ **Confirmado:** No se abren pestañas adicionales
- ✅ **Confirmado:** Navegación en misma pestaña preserva estado

---

## Lecciones Aprendidas

1. **Streamlit session_state es por pestaña**: Cada pestaña del navegador tiene su propio estado
2. **`target="_blank"` rompe continuidad**: Siempre usar `target="_self"` para navegación interna
3. **Validar flujo completo**: No solo que "funcione", sino que preserve estado

---

## Archivos Modificados

| Archivo | Línea | Cambio |
|---------|-------|--------|
| `utils/ui/report_view.py` | 106 | `target="_blank"` → `target="_self"` |

---

## Compliance

✅ **No se tocó lógica de negocio**  
✅ **No se modificó SSOT**  
✅ **Fix mínimo** (1 palabra cambiada)  
✅ **Gate 0 PASS** (sintaxis correcta)  
✅ **Preserva estado** (session_state intacto)
