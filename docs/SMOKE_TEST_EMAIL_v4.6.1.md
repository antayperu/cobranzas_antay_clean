# SMOKE TEST CHECKLIST - v4.6.3 (Corporate Template)

> **Ticket**: RC-QA-002 | **Fecha**: 2025-12-23 | **Versión**: v4.6.1-stable-email

## Objetivo
Validar que el módulo de correos es robusto, no duplica envíos y maneja correctamente múltiples clientes con el mismo correo, cumpliendo con el estándar Enterprise de Antay.

## 1. Criterios de Aceptación (DoD)
El Smoke Test se considera **APROBADO (PASSED)** si y solo si:
1.  **Un click = Un envío**: Cero (0) duplicados en bandeja de entrada bajo condiciones normales.
2.  **Multi-cliente (Mismo Email)**: Si un correo tiene 3 clientes asociados, recibe **3 correos distintos** (uno por cada notificación/cliente) y NO se colapsan ni bloquean.
3.  **Reenvío Intencional**: Funciona correctamente (Override del Ledger) cuando el usuario lo solicita explícitamente y queda auditado en log.
4.  **No-Bloqueo**: El Ledger/TTL no impide escenarios válidos de negocio (ej. re-enviar a los 11 minutos o forzar envío).
5.  **UI Feedback**: La interfaz muestra claramente Resultados (Enviados/Fallidos/Omitidos) y el Log Técnico está oculto en la sección "Avanzado".
6.  **Supervisor Copy**: El supervisor configurado recibe copia (BCC/CC) de todos los envíos.

## 2. Checklist de Pruebas (Email Focus)

| ID | Caso de Prueba | Detalle | Resultado Esperado | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **ET-01** | **Envío Simple** | Enviar correo a 1 cliente nuevo. | Recibe **1 solo correo**. Log muestra "Enviado". | [ ] |
| **ET-02** | **Envío Duplicado (Prevención)** | Sin recargar, intentar enviar de nuevo al mismo cliente (mismo monto/fecha) antes de 10 min. | UI muestra "Omitido (Ledger)". **NO se envía correo**. | [ ] |
| **ET-03** | **Multi-Cliente (Mismo Email)** | Configurar `cliente1@test.com` para Empresa A y Empresa B (mismo Excel). Enviar masivo. | Recibe **2 correos** (uno por Empresa A, uno por Empresa B). Log muestra 2 envíos exitosos. | [ ] |
| **ET-04** | **Force Send (Reenvío)** | Activar check "Forzar reenvío" y enviar al cliente de ET-01. | Se envía correo nuevamente. Log indica envío forzado. | [ ] |
| **ET-05** | **UI/UX Clean** | Revisar panel de resultados tras envío masivo. | Resumen claro (ej. "3 Enviados"). Logs técnicos ("DEBUG: ...") **no visibles** por defecto. Panel "Avanzado" funciona. | [ ] |
| **ET-06** | **Supervisor Copy (BCC)** | Configurar `enable_supervisor_copy=ON`. Enviar. | Cliente recibe 1. Supervisor recibe 1. Log indica envío con copia. | [ ] |
| **ET-07** | **Config Persistence (RC-BUG-017)** | Cambiar email supervisor -> Guardar (Botón Nuevo) -> Recargar F5. | Valor persiste. Pestaña Email muestra "Copia de Supervisión ACTIVADA". | [ ] |
| **ET-08** | **UX Validation (Toggle & Modes)** | Probar Toggle OFF (inputs grises) y ON (habilitados). Verificar textos "Recomendado". | UI responde correctamente. Inputs se bloquean. Mapeo BCC/CC es correcto en backend. | [ ] |
| **QC-LOGO-01** | **Sin Logo** | Configurar sin logo. Enviar correo. | Header texto centrado. **Sin espacio blanco** por imagen rota. | [ ] |
| **QC-LOGO-02** | **Con Logo** | Cargar logo PNG con aire. Verificar "Trim + Resize". Enviar. | Header muestra logo grande y cortado (360px). | [ ] |
| **QC-LOGO-03** | **UX Logo Delete** | Usar botón "Eliminar Logo". | Estado cambia a "No hay logo". Archivo se borra (o desvincula). | [ ] |
| **LOGO-STAGE-01** | **Staging Flow** | Subir logo SIN guardar. | Muestra preview "Pendiente". NO afecta config ni email real. | [ ] |
| **LOGO-SAVE-02** | **Commit Flow** | Click en "Guardar y Aplicar". | Se limpia uploader. Mensaje "Guardado". Email real hora usa nuevo logo. | [ ] |
| **LOGO-LOOP-03** | **Anti-Loop** | Subir logo y no tocar nada. | La app queda estable (sin "running man"). No se recarga infinitamente. | [ ] |

## 3. Evidencia de Ejecución

### Resumen de Resultados
- **Fecha Ejecución**: 2025-12-23
- **Ejecutado por**: Antigravity / User
- **Resultado Final**: [ ] PASSED / [ ] FAILED

### Logs Clave (Ejemplo)
```text
[INFO] Iniciando envío masivo...
[INFO] Procesando Cliente A (cliente@test.com)...
[SUCCESS] Correo enviado a cliente@test.com (ID: XXXX)
[INFO] Procesando Cliente B (cliente@test.com)...
[SUCCESS] Correo enviado a cliente@test.com (ID: YYYY)
[WARNING] Cliente A detectado en Ledger (TTL activo). Omitiendo.
```
