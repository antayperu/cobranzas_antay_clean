# SMOKE TEST PACK - EMAIL (SMTP)

> **Ticket**: RC-QA-002 | **Fecha**: 22/12/2025 | **Módulo**: Notificaciones Email

Este documento define las pruebas de aceptación para el módulo de envío de correos, asegurando que la configuración SMTP y el renderizado HTML funcionan correctamente sin bloquear la aplicación.

## 1. Prerrequisitos
*   Cuenta de envío válida (idealmente Gmail).
*   **Contraseña de Aplicación** generada (si usa 2FA).
*   Archivo `config.json` (o configuración manual en UI).
*   Conexión a Internet estable (SMTP requiere salida por puerto 587).

## 2. Checklist de Pruebas (Email)

| ID | Caso de Prueba | Pasos | Resultado Esperado | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **ET-01** | **Configuración SMTP** | 1. Ir a tab "Configuración".<br>2. Ingresar Server `smtp.gmail.com`, Port `587`.<br>3. Ingresar User/Pass y Guardar. | Mensaje "Configuración guardada". No debe crashear. | [ ] |
| **ET-02** | **Prueba Unitaria (Dry Run)** | *No disponible botón "Test" aislado actualmente. Se valida con envío real a 1 destinatario.* | - | N/A |
| **ET-03** | **Preview Premium (UX)** | 1. Cargar Data.<br>2. Ir a Tab "Marketing Email".<br>3. Seleccionar 1 cliente en tabla.<br>4. Expandir vista. | - **Logo + Header Compacto**.<br>- **3 KPIs** (S/, US$, DetrS/ sin abreviaturas).<br>- "Medios de Pago" **AL FINAL**.<br>- Cuenta BN **NO repetida** (solo en bloque Detracción). | [ ] |
| **ET-04** | **Validación Móvil (Simul)** | Reducir ancho navegador en Preview. | Tabla cambia a **Tarjetas**. Tarjetas muestran "Saldo a DACTA" y "Detracción SUNAT". | [ ] |
| **ET-05** | **Manejo de Errores** | Intentar enviar con contraseña incorrecta (o vacío). | Barra de progreso muestra error rojo. Log expandible muestra error "535" o "Authentication failed". App NO se cierra. | [ ] |
| **ET-06** | **Envío Real (1 Destinatario)** | 1. Filtrar tabla para dejar solo 1 cliente (el de prueba).<br>2. Click "Enviar Correos Masivos". | Progreso llega al 100%. Mensaje "✅ Enviados: 1". Log muestra "Enviado a...". | [ ] |
| **ET-07** | **Deliverability (Manual)** | Revisar inbox del destinatario. | Correo recibido. Asunto correcto. Imágenes visibles (o botón "ver imágenes"). No en Spam (idealmente). | [ ] |
| **ET-08** | **Seguridad** | Revisar Log en pantalla. | **LA CONTRASEÑA NO DEBE APARECER EN NINGÚN LOG.** | [ ] |

### ET-08: Validación Visual (Premium Content)
- [ ] **Desktop Check**:
    - [ ] Layout de Tabla (Header, Body, Footer) correcto.
    - [ ] Logo visible (~90px).
    - [ ] Título "ESTADO DE CUENTA" centrado.
- [ ] **Mobile Check** (Reducir ventana a <600px):
    - [ ] Tabla desaparece.
    - [ ] Aparecen Tarjetas (Cards) individuales por documento.
    - [ ] Card con borde y saldo DACTA destacado.
- [ ] **Detracción**:
    - [ ] Si `Saldo Dacta` < 0.1 y `Detraccion` > 0 => Mostrar "Solo falta Detracción".
    - [ ] Bloque "Importante - Detracción" en gris suave con borde rojo.

### ET-09: Robustez y Anti-Duplicados (RC-BUG-006)
- [ ] **Prueba de Unicidad**:
    - [ ] Seleccionar 1 cliente.
    - [ ] Clic en "Enviar".
    - [ ] Confirmar que **SOLO llega 1 correo**.
    - [ ] Intentar hacer clic de nuevo inmediatamente (debe mostrar advertencia de "Ya enviado").
- [ ] **Prueba Log**:
    - [ ] Verificar en consola/log que diga: "X solicitudes -> X únicos".

## 3. Riesgos y Mitigaciones
*   **Riesgo**: `config.json` guarda la contraseña en texto plano.
*   **Mitigación**: Asegurar que `config.json` está en `.gitignore`.
*   **Fallback**: Si falla SMTP, el sistema atrapa la excepción y permite continuar (no bloquea el resto de la app).

---
**Resultado Final**: [ ] APROBADO / [ ] REQUIERE AJUSTES
