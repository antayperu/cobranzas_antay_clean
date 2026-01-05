# SMOKE TEST PACK - v1.0 Release (Hotfix)

> **Ticket**: RC-QA-001 | **Fecha**: 22/12/2025 | **Versión**: v4.6.1-hotfix

Este documento define las pruebas rápidas "de humo" para validar la estabilidad de la aplicación antes de la entrega urgente. El objetivo es confirmar que el **Happy Path (Solo Texto)** funciona y que no hay regresiones críticas.

## 1. Datos de Prueba (Mínimos Recomendados)
Para ejecutar estas pruebas, utiliza el dataset estándar de prueba o crea uno pequeño:
*   **CtasxCobrar.xlsx**: Al menos 2 empresas, 5 documentos (soles y dólares).
*   **Cobranza.xlsx**: Vacío o con 1 registro.
*   **cartera_clientes.xlsx**: Mapeo básico de teléfonos para esas 2 empresas.

## 2. Checklist de Pruebas (End-to-End)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **ST-01** | **Carga de Archivos** | 1. Subir los 3 Excels.<br>2. Click en "Procesar Archivos". | Aparece mensaje "Actualizado" y se cargan los datos en tabla. Sin errores rojos. | [ ] |
| **ST-02** | **Tabla Principal** | Visualizar la tabla de "Reporte General". | Las columnas clave (Empresa, Saldo Real, Vencimiento) tienen datos correctos. Índices empiezan en 1. | [ ] |
| **ST-03** | **Filtros Básicos** | 1. Filtrar por una "Empresa X".<br>2. Filtrar por Moneda "Soles". | La tabla se reduce correctamente. Los KPIs (Tarjetas superiores) se recalculan. | [ ] |
| **ST-04** | **Excel No-Regresión** | Descargar Excel y abrir. | **Validar 3 Puntos:**<br>1. `SUMA(SALDO)` y otros montos funciona.<br>2. `DETRACCIÓN` siempre es S/.<br>3. `AMORTIZACIONES` coincide texto con UI (Match Key). | [ ] |
| **ST-05** | **Pestaña WhatsApp** | Ir a tab "Marketing WhatsApp". | Se muestran opciones de plantilla y selector de clientes. | [ ] |
| **ST-06** | **UI Hotfix (Bloqueo)** | Verificar selector "Modo de Envío". | Deben verse las opciones "Tarjeta" y "PDF" con etiqueta **(MANTENIMIENTO)** o similar. | [ ] |
| **ST-07** | **Envío Solo Texto** | 1. Seleccionar Modo "Solo Texto".<br>2. Seleccionar 1 cliente.<br>3. Click "Enviar Mensajes". | Se abre navegador. Se escribe y envía el texto. **NO se intenta adjuntar nada.**<br>*(Fix: RC-BUG-001 Applied)* | [x] |
| **ST-08** | **Email Premium (Preview)** | 1. Ir a tab Email.<br>2. Seleccionar 1 cliente.<br>3. Ver Preview HTML. | - **Logo Visible** (PC/Móvil).<br>- **Tabla** en PC / **Tarjetas** en Móvil (Simular).<br>- **3 KPIs** Header (S/, $, Detr S/).<br>- **Cuentas DACTA vs BN** separados. | [ ] |
| **ST-08** | **Protección Backend** | (Opcional) Intentar seleccionar modo Imagen (si la UI dejara) o verificar Log. | El sistema debe forzar "Solo Texto" automáticamente y no romper. | [ ] |
| **ST-09** | **Limpieza** | Verificar carpeta de descargas o temporales. | No quedan archivos huerfanos críticos bloqueando (aunque limpieza es P2, verificar no saturación). | [ ] |

## 3. Criterio de Aceptación (Go/No-Go)
*   [ ] **ST-01** a **ST-07** deben pasar OBLIGATORIAMENTE (Pass).
*   Si falla ST-04 (Excel) o ST-07 (Envío Texto), es **NO-GO** (Detener entrega).
*   Cualquier error en Modo Imagen es ACEPTABLE (pues está deshabilitado).

---

## 4. CHECKLIST DE ENTREGA (Release v4.6.1-hotfix)

Antes de marcar como "Done" el ticket RC-QA-001, verifica estos 5 puntos finales:

1.  **Versión Confirmada**: v4.6.1-hotfix (Etiquetado en `ESTADO_PROYECTO.md`).
2.  **Comando de Ejecución**: `streamlit run app.py` (debe correr sin errores de importación).
3.  **Archivos Requeridos**:
    *   `CtasxCobrar.xlsx` (Headers: COD CLIENTE, EMPRESA, SALDO, etc.)
    *   `Cobranza.xlsx` (Headers: COMPROBANTE, IMPORTE)
    *   `cartera_clientes.xlsx` (Headers: COD CLIENTE, TELÉFONO)
4.  **Funciones Deshabilitadas**:
    *   El modo "Imagen Ejecutiva" NO debe intentar generar imágenes.
    *   El modo "PDF" NO debe intentar adjuntar archivos.
    *   *Comportamiento esperado*: Si se seleccionan, el sistema los convierte a "Solo Texto" y avisa en consola.
5.  **Evidencia Mínima a Capturar**:
    *   Screenshot de la Tabla cargada (ST-02).
    *   Screenshot del mensaje enviado en WhatsApp Web (Solo texto) (ST-07).
    *   Log de consola mostrando la advertencia de Hotfix si se intenta usar modos bloqueados (ST-08).

**Resultado Final**: [ ] APROBADO (Release v1.0) / [ ] RECHAZADO
