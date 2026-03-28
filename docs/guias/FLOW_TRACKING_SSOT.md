# FLOW TRACKING SSOT - Sistema de Seguimiento de Notificaciones Email

**Versión:** 1.5.2-tracking-fix  
**Fecha:** 2025-12-31  
**Principio:** SSOT (Single Source of Truth) - `df_final` es la única fuente de verdad

---

## Resumen Ejecutivo

El sistema de tracking de notificaciones por email utiliza **SOLO 2 columnas** en el DataFrame principal (`df_final`) para rastrear el estado de envío de correos electrónicos a clientes.

### Columnas de Tracking (ÚNICAS)

1. **`ESTADO_EMAIL`**: Estado de la notificación
   - Valores posibles: `"PENDIENTE"` | `"ENVIADO"` | `"FALLIDO"`
   - Valor por defecto: `"PENDIENTE"`

2. **`FECHA_ULTIMO_ENVIO`**: Fecha y hora del último envío
   - Tipo: String (timestamp formateado)
   - Valor por defecto: `""` (vacío)
   - Formato después de envío: `"YYYY-MM-DD HH:MM:SS"`

---

## Flujo de Datos

### 1. Inicialización (Carga de Archivos Excel)

**Archivo:** `utils/processing.py` (líneas 454-457)

```python
# Al procesar los 3 archivos Excel, se inicializan las columnas de tracking
df_merged['ESTADO_EMAIL'] = "PENDIENTE"  # Todos los registros inician como pendientes
df_merged['FECHA_ULTIMO_ENVIO'] = ""     # Fecha vacía (no se ha enviado nada)
```

**Comportamiento:**
- Se ejecuta al cargar los 3 archivos Excel (Cuentas por Cobrar, Cobranza, Cartera)
- **TODOS** los registros inician con `ESTADO_EMAIL = "PENDIENTE"` y `FECHA_ULTIMO_ENVIO = ""`
- Estas columnas NO existen en los archivos Excel originales (se crean en memoria)

---

### 2. Visualización en Reporte General

**Archivo:** `utils/ui/report_view.py`

**Vista Ejecutiva** (modo por defecto):
- **NO muestra** las columnas de tracking
- Enfoque en datos de negocio: Cliente, Deuda, Email, Teléfono, Saldo Real, etc.

**Vista Completa** (modo avanzado):
- **SÍ muestra** las 2 columnas de tracking con labels claros:
  - `ESTADO_EMAIL` → "Estado Notificación (Email)"
  - `FECHA_ULTIMO_ENVIO` → "Último Envío"

**Configuración de Columnas:**
```python
COLUMN_CONFIG = {
    "ESTADO_EMAIL": st.column_config.TextColumn(
        "Estado Notificación (Email)", 
        help="PENDIENTE: no enviado | ENVIADO: confirmado | FALLIDO: error en envío"
    ),
    "FECHA_ULTIMO_ENVIO": st.column_config.TextColumn(
        "Último Envío", 
        help="Fecha y hora del último envío exitoso (vacío si no se ha enviado)"
    ),
}
```

---

### 3. Actualización Post-Envío

**Archivo:** `app.py` (tab "5. Notificaciones Email")

**Trigger:** Después de envío exitoso de email

**Lógica:**
```python
# Solo se actualizan los registros que fueron enviados exitosamente
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Actualizar SOLO las 2 columnas de tracking
st.session_state.df_final.loc[mask_enviados, 'ESTADO_EMAIL'] = 'ENVIADO'
st.session_state.df_final.loc[mask_enviados, 'FECHA_ULTIMO_ENVIO'] = timestamp
```

**Comportamiento:**
- Solo se actualizan los registros con `Estado == 'Enviado'` (confirmación SMTP exitosa)
- Los registros NO enviados mantienen `ESTADO_EMAIL = "PENDIENTE"` y `FECHA_ULTIMO_ENVIO = ""`
- La actualización es **selectiva** (solo afecta a los clientes enviados en esa operación)

---

### 4. Reset de Tracking

**Archivo:** `app.py` (botón "Reiniciar tracking de notificaciones")

**Trigger:** Usuario hace clic en botón de reset (con confirmación)

**Lógica:**
```python
# Volver TODOS los registros a estado inicial
df_final['ESTADO_EMAIL'] = "PENDIENTE"
df_final['FECHA_ULTIMO_ENVIO'] = ""
```

**Comportamiento:**
- **TODOS** los registros vuelven a `PENDIENTE` con fecha vacía
- NO afecta otros datos (deudas, emails, teléfonos, etc.)
- Útil para iniciar un nuevo ciclo de notificaciones sin recargar archivos

---

### 5. Nueva Carga de Archivos

**Trigger:** Usuario carga nuevos archivos Excel (con confirmación "No Sorpresas")

**Comportamiento:**
- Se reemplaza completamente `df_final` con los nuevos datos procesados
- Las columnas de tracking se inicializan desde cero (todos `PENDIENTE` + fecha vacía)
- Se pierde el historial de envíos del ciclo anterior (comportamiento esperado)

---

## Reglas de Negocio

### ✅ PERMITIDO

1. **Actualizar tracking solo después de envío confirmado** (SMTP success)
2. **Resetear tracking** para nuevo ciclo de envíos (sin recargar archivos)
3. **Filtrar por estado** en el Reporte General (ej: mostrar solo pendientes)
4. **Exportar a Excel** con las columnas de tracking incluidas

### 🚫 PROHIBIDO

1. **NO agregar más columnas de tracking** (solo estas 2)
2. **NO crear columnas derivadas/computadas** (ej: `ESTADO_NOTIF_EMAIL`, `EMAIL_DISPLAY`)
3. **NO modificar tracking manualmente** (solo por flujo automatizado)
4. **NO actualizar tracking sin confirmación de envío exitoso**

---

## Persistencia de Sesión

**Archivo:** `utils/state_manager.py`

**Comportamiento:**
- Al guardar sesión, se guarda `df_final` completo (incluyendo columnas de tracking)
- Al restaurar sesión, las columnas de tracking mantienen su estado anterior
- Permite continuar trabajo al día siguiente sin perder historial de envíos

**Ejemplo:**
- Día 1: Envío emails a 10 clientes → `ESTADO_EMAIL = "ENVIADO"` para esos 10
- Día 2: Restauro sesión → Los 10 clientes siguen mostrando `"ENVIADO"`
- Día 2: Envío a 5 clientes más → Solo esos 5 se actualizan a `"ENVIADO"`

---

## Debugging y QA

**Archivo:** `app.py` (expander "🔧 Debug: Tracking Stats")

**Métricas disponibles:**
- Total Registros
- ✅ Enviados (count donde `ESTADO_EMAIL == "ENVIADO"`)
- ⏳ Pendientes (count donde `ESTADO_EMAIL == "PENDIENTE"`)
- Última actualización (timestamp y cantidad de registros actualizados)

---

## Archivos Modificados (Resumen)

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `utils/processing.py` | Inicialización de 2 columnas tracking | 454-457, 460-476 |
| `utils/ui/report_view.py` | Reescritura completa (eliminadas columnas derivadas) | 1-133 |
| `app.py` | Eliminadas referencias a `ESTADO_ENVIO_TEXTO` | 488-493, 552-553 |

---

## Compliance con STOP THE LINE

✅ **Solo 2 columnas de tracking** (como se solicitó originalmente)  
✅ **No se modificó lógica de negocio** (cálculos, merge, filtros, SMTP)  
✅ **No se cambiaron nombres de funciones críticas**  
✅ **No se agregaron "nuevos modos" ni "nuevos flujos"**  
✅ **SSOT mantenido** (`df_final` sigue siendo la única fuente de verdad)  

---

## Próximos Pasos (Gate 3)

**Pendiente:** Validación manual del usuario

**Checklist:**
1. Cargar 3 archivos Excel → Verificar tracking vacío (`PENDIENTE` + fecha vacía)
2. Tab Email lista clientes → Verificar métricas correctas
3. Enviar a 1 cliente → Verificar tracking actualiza solo ese cliente
4. Reset tracking → Verificar todos vuelven a `PENDIENTE`
5. Nueva carga → Verificar tracking limpio

**Evidencia requerida:** Screenshots de cada test
