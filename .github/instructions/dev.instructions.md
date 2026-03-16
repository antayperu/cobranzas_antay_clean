---
applyTo: "modules/**,utils/**,app.py"
---

# IA_Programador — ReporteCobranzas

Eres el agente de desarrollo (IA_Programador) del proyecto ReporteCobranzas.
Aplica estas reglas en todos los archivos de módulos, utilidades y la entrada principal de la app.

## Stack obligatorio

- Python 3.11
- Streamlit (UI)
- pandas / openpyxl (Excel)
- Supabase Python client (BD)
- smtplib (Email)
- pytest (tests)

## Reglas de implementación

### SSOT vs Vista filtrada
- `df_final` es el SSOT — NUNCA modificar directamente excepto por lógica de tracking oficial
- `df_filtered` es la vista derivada para pantalla — úsala en Email/WA/Preview
- Nunca mezclar ambas ni asumir que son equivalentes

### Supabase
- Cloud-only. NO implementar fallback SQLite ni session_state como BD
- Toda operación BD pasa por `utils/db_manager.py`
- Cliente singleton en `utils/supabase_client.py`
- Si Supabase no responde → bloqueo controlado con mensaje de error claro

### Session state
- Toda persistencia de UI en `st.session_state`
- Keys con nombres descriptivos: `wa_subtab_idx`, `wa_plantilla_seleccionada`, etc.
- Persistir por valor (índice entero, no label dinámico) cuando el label puede cambiar con emoji o contador
- Flag `skip_auto_restore` para evitar que auto-restore sobreescriba elección manual

### Ciclos de procesamiento
- `cycle_id` formato: `CIC-YYYYMMDD-HHMM`
- Al restaurar ciclo X: reconciliar `df_final` con `notificaciones WHERE cycle_id = X`
- `attempt_auto_restore()` en `app.py` al arrancar

### Conteo y deduplicación
- KPIs de Enviados/Pendientes: siempre por `CodCliente` único, no por EMAIL_FINAL
- Si un cliente tiene fila Envío WA + fila Gestión → deduplicar por `CodCliente`
- Monto multimoneda: guardar `DeudaS` / `DeudaD` explícitos, no `SaldoReal` plano

### Columnas prohibidas (nunca renombrar)
`CodCliente`, `Empresa`, `SaldoReal`, `Correo`, `MATCH_KEY`,
`ESTADO_EMAIL`, `FECHA_ULTIMO_ENVIO`, `ESTADO_WHATSAPP`

### Columnas de tracking
- `ESTADO_EMAIL`: `PENDIENTE` / `ENVIADO` / `ERROR` / `SIN_CORREO`
- `ESTADO_WHATSAPP`: `PENDIENTE` / `ENVIADO` / `ERROR` / `SIN_TELEFONO`
- Al cargar Excel nuevo: inicializar con `fillna('PENDIENTE')` en `_docs_to_df()`

## Estructura de módulos

```
utils/
  db_manager.py          ← TODAS las operaciones Supabase
  supabase_client.py     ← cliente singleton
  processing.py          ← Excel → df_final
  session.py             ← gestión session_state
  ui/
    styles.py            ← COLORS + load_css()
    sidebar.py           ← sidebar, banner, carga de archivos
    tabs/
      whatsapp.py        ← Tab WA + post-envío
      email_notifications.py
      crm_gestiones.py   ← gestiones, acuerdos, pendientes
      clientes_premium.py
      config_tab.py
```

## Convenciones de código

- Funciones con responsabilidad única
- Sin lógica de negocio en archivos de UI (tabs)
- Comentarios solo donde la lógica no es evidente
- No añadir manejo de errores para escenarios que no pueden ocurrir
- Imports ordenados: stdlib → third-party → local
