# Gate 3 Checklist - Manual E2E Testing v1.5.2

**Versión:** v1.5.2-fullscreen-tracking-fix  
**Fecha:** 2025-12-31  
**Ejecutor:** [TU NOMBRE]  
**Resultado:** [ ] PASS / [ ] FAIL

---

## Instrucciones Generales

1. Ejecutar cada test en orden
2. Marcar ✅ PASS o ❌ FAIL para cada criterio
3. Si FAIL, anotar detalles en sección "Notas"
4. Capturar screenshots de cada test (opcional pero recomendado)
5. **NO declarar PASS general hasta que TODOS los criterios sean ✅**

---

## CA-1: Nuevo Ciclo (Fresh Load)

### Objetivo
Validar que al cargar nuevos archivos, el tracking se inicializa correctamente y no hay contaminación del ciclo anterior.

### Pasos
1. Iniciar app limpia (`streamlit run app.py`)
2. Cargar 3 archivos Excel:
   - CtasxCobrar.xlsx
   - Cobranza.xlsx
   - Cartera.xlsx
3. Click "🚀 Procesar y Validar"
4. Esperar a que se genere el Reporte General
5. Ir al tab "Notificaciones Email"

### Criterios de Aceptación
- [ ] **CA-1.1:** "Enviados Hoy" = **0**
- [ ] **CA-1.2:** "Pendientes de Envío" = **> 0** (si hay correos en los datos)
- [ ] **CA-1.3:** Dropdown "Seleccione Clientes con Correo" muestra opciones disponibles
- [ ] **CA-1.4:** NO aparece mensaje "No options to select"

### Resultado CA-1
- [ ] ✅ PASS
- [ ] ❌ FAIL

**Notas:**
```
[Anotar observaciones aquí]
```

---

## CA-2: Filtros Compartidos (Regla Histórica)

### Objetivo
Validar que los filtros aplicados en "Reporte General" se reflejan automáticamente en "Notificaciones Email".

### Pasos
1. Con datos cargados, ir a "Reporte General"
2. Aplicar filtro de empresa (seleccionar UNA empresa específica)
3. Aplicar filtro "Solo con Correo" (checkbox)
4. Ir al tab "Notificaciones Email"
5. Revisar lista de destinatarios

### Criterios de Aceptación
- [ ] **CA-2.1:** Lista de destinatarios muestra SOLO clientes de la empresa filtrada
- [ ] **CA-2.2:** NO aparecen clientes de otras empresas
- [ ] **CA-2.3:** Contador "Pendientes de Envío" refleja solo el subconjunto filtrado
- [ ] **CA-2.4:** Al seleccionar un cliente y ver "Vista Previa (HTML)", los documentos mostrados corresponden SOLO a la empresa filtrada

### Resultado CA-2
- [ ] ✅ PASS
- [ ] ❌ FAIL

**Notas:**
```
[Anotar observaciones aquí]
```

---

## CA-3: Cliente con Deuda 0

### Objetivo
Validar que clientes con saldo 0 NO aparecen en "Notificaciones Email", salvo que tengan detracción pendiente.

### Pasos
1. En "Reporte General", identificar un cliente con:
   - SALDO REAL = 0 (o muy cercano a 0)
   - ESTADO DETRACCION ≠ "PENDIENTE" (o DETRACCIÓN = 0)
2. Ir al tab "Notificaciones Email"
3. Buscar ese cliente en la lista de destinatarios

### Criterios de Aceptación
- [ ] **CA-3.1:** Cliente con SALDO REAL = 0 y sin detracción pendiente NO aparece en lista
- [ ] **CA-3.2:** Si existe un cliente con SALDO REAL = 0 pero DETRACCIÓN PENDIENTE > 0, SÍ aparece en lista

### Resultado CA-3
- [ ] ✅ PASS
- [ ] ❌ FAIL

**Notas:**
```
[Anotar observaciones aquí]
```

---

## CA-4: Emails Duplicados (Caso Real)

### Objetivo
Validar que múltiples clientes compartiendo el mismo email NO causan problemas de filtrado, contadores o selección.

### Pasos
1. Usar datos de prueba donde múltiples clientes tienen el mismo email
2. Cargar archivos y generar reporte
3. Ir a "Notificaciones Email"
4. Revisar lista de destinatarios y contadores

### Criterios de Aceptación
- [ ] **CA-4.1:** Todos los clientes con email válido aparecen en la lista (no se ocultan por compartir email)
- [ ] **CA-4.2:** Contador "Pendientes de Envío" refleja cantidad correcta de registros/clientes
- [ ] **CA-4.3:** Al seleccionar un cliente, la Vista Previa HTML muestra documentos del cliente correcto (no mezcla con otros que comparten email)
- [ ] **CA-4.4:** Puedo seleccionar y enviar sin errores

### Resultado CA-4
- [ ] ✅ PASS
- [ ] ❌ FAIL

**Notas:**
```
[Anotar observaciones aquí]
```

---

## CA-5: Pantalla Completa + Retorno sin Romper Sesión

### Objetivo
Validar que la funcionalidad de "Pantalla Completa" no rompe la sesión ni obliga a recargar archivos.

### Pasos
1. Con datos cargados, ir a "Reporte General"
2. Cambiar a "Vista Completa"
3. Click en botón "🖥️ Ver en Pantalla Completa"
4. Verificar que se abre vista fullscreen
5. Click en botón "✖ Cerrar"
6. Verificar que regresa a la app
7. Click en "📂 Cargar Nuevos Archivos" (sidebar)
8. Click "✅ Sí, reemplazar"

### Criterios de Aceptación
- [ ] **CA-5.1:** Vista fullscreen se abre correctamente (tabla visible, sin sidebar)
- [ ] **CA-5.2:** Botón "✖ Cerrar" funciona y regresa a la app sin error
- [ ] **CA-5.3:** Al regresar, la sesión sigue activa (se ve "⚡ Sesión Activa desde HH:MM")
- [ ] **CA-5.4:** NO obliga a recargar archivos
- [ ] **CA-5.5:** Botón "Cargar Nuevos Archivos" funciona y muestra los 3 uploaders al confirmar

### Resultado CA-5
- [ ] ✅ PASS
- [ ] ❌ FAIL

**Notas:**
```
[Anotar observaciones aquí]
```

---

## Resumen Final

### Resultados por Criterio
- CA-1 (Nuevo Ciclo): [ ] PASS / [ ] FAIL
- CA-2 (Filtros Compartidos): [ ] PASS / [ ] FAIL
- CA-3 (Deuda 0): [ ] PASS / [ ] FAIL
- CA-4 (Emails Duplicados): [ ] PASS / [ ] FAIL
- CA-5 (Fullscreen): [ ] PASS / [ ] FAIL

### Resultado General
- [ ] ✅ **GATE 3 PASS** - Todos los criterios pasaron
- [ ] ❌ **GATE 3 FAIL** - Al menos un criterio falló

### Acciones Requeridas
- Si PASS: Proceder con merge y tag `v1.5.2`
- Si FAIL: Revertir cambios y corregir antes de merge

### Firma
**Ejecutor:** ___________________  
**Fecha:** ___________________  
**Hora:** ___________________
