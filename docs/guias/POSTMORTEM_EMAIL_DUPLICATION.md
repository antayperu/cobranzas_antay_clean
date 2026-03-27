# Post-Mortem: Email Duplication Incident (RC-BUG-006 to RC-BUG-013)

## 📅 Fecha
23 de Diciembre de 2025

## 🚨 Incidente
Usuarios reportaron recepción duplicada de correos de Estado de Cuenta.

## 🕵️‍♂️ Análisis de Causa Raíz (RCA)

### Hipótesis Iniciales Descartadas
1.  **Gmail/SMPT**: Se pensó que Gmail duplicaba al recibir. Descartado por Message-IDs distintos.
2.  **Rerun de Streamlit**: Se pensó que el script se reejecutaba entero. Descartado parcialmente (button guard ayudó, pero no resolvió todo).
3.  **Concurrencia**: Se pensó en clicks rápidos o tabs abiertos. Ledger ayudó pero no era la causa principal.

### **Causa Raíz Confirmada: Duplicación de Código (Code Smell)**
El archivo `app.py` contenía un bloque de código **copiado y pegado** al final de la lógica del botón de envío.
- **Bloque 1**: Líneas ~1225. Llamaba a `send_email_batch`.
- **Bloque 2**: Líneas ~1259. Re-inicializaba config y llamaba a `send_email_batch` **DE NUEVO**.

Esto provocaba que **CADA CLICK** generara **DOS ENVÍOS** secuenciales inevitables.

## 🛠️ Solución Implementada

### 1. Fix Definitivo (Core)
- **Eliminación de Código Muerto/Duplicado**: Se borró el segundo bloque de llamada en `app.py`.
- **Garantía Exactly-Once**: Ahora solo existe una única llamada a `send_email_batch`.

### 2. Capas de Protección Adicional (Defense in Depth)
Dado que el error humano es posible, se implementaron controles robustos:
- **Business Ledger (SQLite)**: Base de datos local que registra cada envío exitoso.
- **TTL (Time-To-Live)**: Bloquea intentos de reenviar la misma notificación (misma llave de negocio) en < 10 minutos.
- **Notification Key**: `Hash(Cliente + Docs + Fecha)` asegura que si el contenido cambia, el envío se permite.

### 3. UX Enterprise
- **Panel de Resultados**: Se reemplazó el log de texto por métricas visuales y tabla de detalle.
- **Descarga de Reporte**: CSV para auditoría del usuario.

## 🎓 Lecciones Aprendidas (Senior Standard)
1.  **Código Limpio**: Nunca dejar bloques de código comentados o "legacy" activos cerca de la lógica principal. Un vistazo rápido al archivo habría revelado la doble llamada.
2.  **Logs Forenses**: La implementación de `RunID` y `Stack Trace` fue clave para confirmar que eran dos llamadas distintas y no un comportamiento extraño de la librería.
3.  **No Confiar en "Magic Fixes"**: Intentar arreglar duplicados con deduplicación en listas no funciona si la función se llama dos veces desde fuera. Siempre auditar el **Caller**.

## ✅ Estado Final
- **Bug**: Erradicado.
- **Robustez**: Alta (Ledger + TTL).
- **UX**: Mejorada significativamente.
