# Metodología Antay Fábrica de Software
# Última sincronización: corte - [LIVE NOTION FETCH]

### [    Documentación Oficial (SSOT)]
  Esta documentación define la metodología oficial para diseñar, construir, probar, versionar y operar software en Antay bajo estándares enterprise.
  [BLOCK: paragraph]
  ### [Parte I - Principios y Estándares Enterprise]
    ## 1. Filosofía Antay (No negociable)
    - Trabajamos bajo estándares enterprise internacionales.
    - El código debe escalar a millones de registros (performance y memoria como requisito, no como extra).
    - Optimización es estándar base, no opcional.
    - Diseño premium y altos estándares AU/UX al nivel de empresas top mundiales.
    - No sorpresas: cambios puntuales, controlados y con evidencia de no-regresión.
    ## 2. Roles y responsabilidades (modelo mínimo)
    - Owner: prioriza negocio, aprueba planes, valida entregas.
    - Tech Lead (IA/Dev Senior): diseña solución, implementa sin romper, entrega pruebas y evidencia.
    - QA Lead: define smoke/regresión, valida escenarios críticos, audita logs.
    - UX Lead: define flujos, textos, estados y coherencia (habilitar/inhabilitar, staging, previews).
    - Release Manager: versionado, tags, backups, changelog, rollback.
    ## 3. Ciclo de vida estándar (de idea a producción)
    1. Intake: requerimiento claro + criterios de aceptación + no-go (lo que NO se debe tocar).
    1. Diseño: plan técnico + impacto + riesgos + test plan (smoke y regresión).
    1. Build: cambio mínimo viable, modular, con logging y feature flags cuando aplique.
    1. QA: pruebas automatizables + smoke manual reproducible + evidencias (screens/logs).
    1. Release: backup/tag, bump versión, changelog, despliegue controlado.
    1. Operate: monitoreo, gestión de incidencias, mejoras iterativas.
    ## 4. Quality Gates (obligatorio antes de decir 'terminado')
    - Compilación / arranque: python -m py_compile PASS + streamlit run PASS.
    - No-regresión: smoke tests claves ejecutados y documentados.
    - Logs limpios: sin NameError/AttributeError, sin variables no definidas.
    - UX coherente: botones deshabilitados hasta cambios; staging + guardar; feedback visual.
    - Seguridad: credenciales fuera de código (env/secret), no hardcode.
    - Versionado: commit claro, tag, backup previo si el cambio es sensible.
    ## 5. Estándares AU/UX (reglas operativas)
    - Un cambio de configuración debe ser explícito: staging → Guardar/Aplicar → feedback.
    - Botones de guardado deshabilitados por defecto; se habilitan solo si hay cambios.
    - Vista previa siempre debe mostrar 'qué se enviará realmente' (To/CC/BCC + modo QA/Prod).
    - Mensajes y etiquetas consistentes y sin ambigüedad.
  ### [Parte II - Manual Operativo Oficial (MODO ENTERPRISE)]
    Este documento manda. Si algo contradice prácticas anteriores, prevalece este manual.
    # 1) Reglas de Oro (No Sorpresas)
    1. **No-regresión**: no se rompe nada existente.
    1. **Cambios acotados**: solo tocar lo solicitado + lo mínimo indispensable para que compile y pase gates.
    1. **Sin supuestos**: si falta un dato, se implementa de forma segura con default reversible.
    1. **Observabilidad**: logs legibles para negocio + logs técnicos en modo “Avanzado”.
    1. **Rollback siempre posible**: tag/branch de backup antes de cambios.
    # 2) Flujo Estándar End-to-End
    ## 2.1 Intake
    - Ticket con: objetivo, alcance, NO-alcance, criterios de aceptación, riesgos, dependencias.
    ## 2.2 Plan
    - Propuesta de plan en 5-10 bullets:
    - Archivos a tocar
    - Funciones/paths exactos
    - Tests a crear/actualizar
    - Riesgos de regresión
    - Estrategia de rollback
    - **Se aprueba el plan** y luego se ejecuta sin pedir permiso paso a paso.
    ## 2.3 Implementación (con Quality Gates)
    - Gate 0: `python -m py_compile` (o equivalente)
    - Gate 1: unit tests / tests críticos
    - Gate 2: smoke test manual guiado (pasos + evidencia)
    - Gate 3: revisión de UX (consistencia, claridad, estados, feedback)
    - Gate 4: documentación mínima actualizada (tickets + estado + smoke)
    ## 2.4 Release
    - Commit con mensaje estándar.
    - Tag versionado semántico + notas de release.
    - Checklist de producción.
    # 3) Estándar de Configuración (UX)
    - Toda configuración sensible debe ser:
    - **Staging** (cambios pendientes) + botón **Guardar/Aplicar** + **Cancelar**
    - Botón “Guardar” **deshabilitado** hasta que detecte cambios
    - Vista previa clara del resultado final (“Así se verá en producción”)
    # 4) Estándar de Correo Masivo (Seguridad)
    - Modo Producción y Modo Marcha Blanca (QA) deben ser **mutuamente excluyentes**.
    - En QA:
    - To/CC/BCC se redirigen a listas QA explícitas (separadas).
    - Asunto y banner deben marcar PRUEBA, solo cuando QA esté ON.
    - Nunca se debe inyectar “Marcha Blanca” si el toggle está OFF.
    # 5) Definición de Done (DoD)
    ✅ Compila | ✅ Gates pasan | ✅ No rompe UI | ✅ Logs claros | ✅ Docs actualizadas | ✅ Rollback disponible
  ### [ Parte III - Protocolo de Trabajo con IA (Antigravity / Agentes)]
    # Objetivo
    Asegurar entregables estables y sin regresiones, evitando “errores junior” (indentación, variables no definidas, APIs inexistentes, etc.).
    # Reglas
    - No introducir APIs inventadas (ej. `st.permissions` si no existe).
    - No dejar variables sin definir (`supervisor_copy_target`, `supervisor_log_info`).
    - No romper imports (ej. `components`).
    - No usar `st.rerun()` en loops sin guardas (hash, session_state, flags).
    # Formato de entrega obligatorio
    1. **Plan** (bullets + archivos + funciones).
    1. **Diff mental**: “Qué cambia” / “Qué NO cambia”.
    1. **Gates ejecutados** (comandos + PASS).
    1. **Smoke test** (pasos numerados).
    1. **Notas de riesgo** + rollback.
    # Prompt estándar (plantilla)
    - “Solo modificar lo solicitado, sin refactors adicionales”.
    - “Crear tag backup antes del cambio”.
    - “No pedir permiso por cada micro paso: presentar plan → ejecutar”.
  ### [Parte IV - Quality Gates – Estándar Antay]
    # Gate 0 – Compilación
    - `python -m py_compile app.py` (o paquete completo)
    - Falla = no se continúa.
    # Gate 1 – Tests Automatizados
    - Unit tests / tests de integración ligeros
    - Tests de no-regresión: rutas críticas del negocio
    # Gate 2 – Preflight (antes de enviar a clientes)
    - Validar configuración activa (Producción vs QA)
    - Validar destinatarios (To/CC/BCC)
    - Vista previa HTML
    # Gate 3 – Smoke Manual (evidencia)
    - Caso feliz
    - Caso sin logo / sin config
    - Caso QA ON
    - Caso QA OFF
    - Caso CC/BCC con múltiples emails
    # Gate 4 – Documentación
    - Ticket actualizado
    - md actualizado
    - SMOKE_TEST actualizado con nuevos casos
  ### [Parte V - Estándares AU/UX (Streamlit / Apps internas)]
    # Claridad
    - Estados visibles: ON/OFF, activo/inactivo.
    - Textos explicativos cortos.
    - “Vista previa” de lo que saldrá en producción.
    # Prevención de errores
    - Botones deshabilitados hasta que existan cambios.
    - Confirmaciones (“Guardado con éxito”, “Cambios pendientes”).
    - Staging + Guardar/Cancelar para operaciones críticas.
    # Consistencia
    - Terminología única (ej. CC/CCO, QA/Marcha Blanca).
    - Evitar duplicar conceptos (“Supervisor” si ya migró a “Copias Internas”).
    # Accesibilidad y estética
    - Tipografías y jerarquía
    - Espaciado y alineación
    - Mensajes de error accionables (qué hacer, dónde, cómo)
  ### [Parte VI - Caso de Estudio – ReporteCobranzas (Logo + Email + QA)]
    # Lecciones capturadas (para no repetir)
    1. **Cambios sin staging** provocan loops/”parpadeos” y desconfianza del usuario.
    1. **Variables no definidas** aparecen cuando se hace hotfix sin volver a correr gates.
    1. **QA debe controlar To/CC/BCC completos**; no mezclar “copias de producción” dentro de QA.
    1. El banner/asunto de QA solo debe aparecer cuando el toggle QA está ON.
    # Reglas derivadas
    - QA tiene sus propias listas: `qa_to_list`, `qa_cc_list`, `qa_bcc_list`.
    - Producción tiene sus listas: `prod_cc_list`, `prod_bcc_list`.
    - Al enviar:
    - Si QA ON → usar SOLO listas QA (To/CC/BCC) + marcadores QA.
    - Si QA OFF → usar clientes reales en To + copias internas de producción.
    # Checklist QA (antes de producción)
    - Enviar a 3 clientes “ficticios” → llegan a QA To.
    - CC QA llega a CC QA.
    - BCC QA llega a BCC QA.
    - Ningún correo sale a clientes reales.
  [BLOCK: paragraph]
  [BLOCK: paragraph]
[BLOCK: paragraph]
