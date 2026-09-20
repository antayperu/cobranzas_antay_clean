# Metodología Antay Fábrica de Software
# Última sincronización: corte - [LIVE NOTION FETCH]

[BLOCK: callout]
  ## ⚙️ Antay Fábrica de Software
  Metodología oficial para diseñar, construir, probar, versionar y operar software en Antay bajo estándares enterprise.
[BLOCK: table_of_contents]
[BLOCK: divider]
### 🧭 Accesos rápidos
[BLOCK: column_list]
  [BLOCK: column]
    [BLOCK: callout]
    [BLOCK: callout]
    [BLOCK: callout]
  [BLOCK: column]
    [BLOCK: callout]
    [BLOCK: callout]
  [BLOCK: column]
    [BLOCK: callout]
    [BLOCK: callout]
[BLOCK: divider]
### 📌 Índice (subpáginas)
-     Documentación Oficial (SSOT)
- Base de Documentación Profesional
- Proyectos (Hub)
- Glosario Técnico Oficial — Metodología Antay v2.0
- Estándares de Branching GitFlow - Antay
- Guías y manuales de desarrollo
- Playbook de Marketing - Antay
[BLOCK: divider]
### 🔗 Navegación
- Consultoría Antay
### [    Documentación Oficial (SSOT)]
  📜 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [BLOCK: quote]
  [BLOCK: divider]
  [BLOCK: table_of_contents]
  [BLOCK: divider]
  ## 📚 Partes del estándar
  [BLOCK: toggle]
    Parte I - Principios y Estándares Enterprise
  [BLOCK: toggle]
    Untitled
  [BLOCK: toggle]
    Untitled
  [BLOCK: toggle]
    Parte IV - Quality Gates – Estándar Antay
  [BLOCK: toggle]
    Untitled
  [BLOCK: toggle]
    Untitled
  [BLOCK: toggle]
    Untitled
  [BLOCK: toggle]
    Parte VIII - Continuidad, Trazabilidad y Control de versiones (Notion + Github)
  [BLOCK: toggle]
    Untitled
  [BLOCK: toggle]
    Untitled
  [BLOCK: toggle]
    Parte XI - DOCOPS-NOTION — Estándar de Cierre
  [BLOCK: toggle]
    - Untitled
  [BLOCK: divider]
  ## 🔗 Navegación
  ← 
  ### [🚀 Estándares de Despliegue - Metodología Antay]
    # Estándares de Despliegue - Metodología Antay
    Basado en:
    Uso:
    [BLOCK: divider]
    ## 🎯 Objetivo
    Implementar un flujo de despliegue (deploy) profesional que minimice errores en producción y mantenga la estabilidad del sistema.
    [BLOCK: divider]
    ## 🌍 GitFlow Simplificado (Estándar Internacional)
    ### Estructura de Ramas Obligatoria
    [BLOCK: code]
    ### Definiciones
    [BLOCK: heading_4]
    - ✅ Código 100% probado y estable
    - ✅ SIEMPRE desplegable (deployable)
    - ✅ Solo recibe merges desde 
    - ✅ Streamlit Cloud / Producción lee de AQUÍ
    - ❌ NUNCA se trabaja directamente en esta rama
    - ❌ NUNCA se hace commit directo
    Analogía:
    [BLOCK: heading_4]
    - ✅ Código integrado y probado
    - ✅ Recibe merges desde 
    - ✅ Base para crear nuevas features
    - ✅ Debe pasar Quality Gates antes de merge a 
    - ❌ Puede tener bugs menores (se arreglan antes de merge a main)
    Analogía:
    [BLOCK: heading_4]
    - ✅ Una rama por ticket/funcionalidad
    - ✅ Nombrado: 
    - ✅ Se crea desde 
    - ✅ Se mergea de vuelta a 
    - ✅ Se elimina después del merge exitoso
    Analogía:
    [BLOCK: divider]
    ## 🔄 Flujo Completo de Trabajo
    ### PASO 1: Crear Feature Branch
    [BLOCK: code]
    Explicación:
    - checkout dev
    - pull origin dev
    - checkout -b feature/...
    [BLOCK: divider]
    ### PASO 2: Desarrollo en Feature
    [BLOCK: code]
    Buenas Prácticas:
    - ✅ Commits pequeños y frecuentes
    - ✅ Mensajes descriptivos
    - ✅ Usar conventional commits: 
    [BLOCK: divider]
    ### PASO 3: Testing en Feature
    Quality Gates Obligatorios:
    [BLOCK: code]
    ✅ 
    [BLOCK: divider]
    ### PASO 4: Merge Feature → Dev
    [BLOCK: code]
    ¿Por qué eliminar la rama feature?
    - Ya su trabajo está integrado en 
    - Mantener repo limpio
    - Evitar confusión
    [BLOCK: divider]
    ### PASO 5: Testing en Dev (Pre-Release)
    ANTES de mergear a 
    1. ✅ Todas las funcionalidades existentes siguen funcionando
    1. ✅ Nueva funcionalidad funciona correctamente
    1. ✅ Tests pasando (Gate 0, 1, 2, 3)
    1. ✅ Sin regresiones (bugs nuevos)
    1. ✅ README actualizado
    1. ✅ Documentación en Notion actualizada
    Opcional pero Recomendado:
    - Configurar Streamlit Cloud para desplegar 
    - Ejemplo: 
    - Probar en ambiente similar a producción
    [BLOCK: divider]
    ### PASO 6: Release (Merge Dev → Main)
    SOLO cuando 
    [BLOCK: code]
    ¿Qué pasa automáticamente?
    1. GitHub detecta cambio en 
    1. Streamlit Cloud detecta cambio en 
    1. Streamlit Cloud descarga código nuevo
    1. Streamlit Cloud instala dependencias
    1. Streamlit Cloud reinicia la app
    1. ✅ Usuarios ven nueva versión en ~2-5 minutos
    [BLOCK: divider]
    ### PASO 7: Verificación Post-Deploy
    Inmediatamente después del deploy:
    [BLOCK: code]
    Si algo falla:
    - Opción A: Rollback (volver a versión anterior)
    - Opción B: Hotfix (arreglo rápido en main)
    [BLOCK: divider]
    ## ⚠️ Reglas Críticas de Seguridad
    ### ANTES de cualquier Push a GitHub:
    [BLOCK: code]
    ### .gitignore Obligatorio:
    [BLOCK: code]
    [BLOCK: divider]
    ## 🚨 Manejo de Emergencias
    ### Rollback (Volver a Versión Anterior)
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
  ### [Parte VIII - Continuidad, Trazabilidad y Control de versiones (Notion + Github)]
    # 1) Continuidad del Proyecto (Notion como SSOT)
    Regla:
    Objetivo:
    Debe existir SIEMPRE (obligatorio) dentro de cada proyecto en Notion:
    1. FRD
      - Documento oficial del “qué debe hacer la app” + criterios de aceptación 
    1. Estado Actual
      Debe incluir:
      - Versión/tag estable actual (ej: 
      - DONE / IN PROGRESS / BLOCKED 
      - Riesgos conocidos
      - Próximo paso exacto
    1. Log del Proyecto
      Cada sesión de trabajo debe registrar en 5 líneas:
      - Fecha/hora
      - Qué se cambió
      - Resultado Gate 3 (PASS/FAIL)
      - Bugs abiertos (IDs)
      - Próximo paso
    1. Gate 3 Checklist E2E
      - Casos CA-1, CA-2… con pasos + resultado esperado
      - Evidencia (capturas o video)
      - Resultado por versión/tag
    Regla de aceptación:
    [BLOCK: quote]
    # 2) Control de Versiones y Respaldo (GitHub)
    Rol de GitHub en Antay Fábrica de Software (3 roles):
    1. Codebase
    1. Versioning/Rollback
    1. Evidencia técnica
    Reglas obligatorias de trabajo en GitHub:
    1. Trabajar por ramas (Branch = línea de trabajo separada)
      - Toda mejora se hace en una rama, NO directo en 
      - Nombre estándar: 
    1. Commit discipline (commit = registro de cambio)
      - Commits pequeños, descriptivos y relacionados a un objetivo.
      - Cada commit debe permitir entender: “qué se cambió y por qué”.
    1. Tag estable antes de cambios grandes
      - Crear un 
        Ejemplo: 
      - Este tag es el punto seguro para volver atrás.
    1. Rollback (volver atrás) si falla Gate 3
      - Si Gate 3 FAIL, se revierte a último tag estable y se corrige desde ahí.
    1. Push obligatorio + sincronización
      - Todo cambio relevante debe quedar en remoto (GitHub).
      - Prohibido dejar cambios solo en local.
    Definición clave (para evitar confusión):
    [BLOCK: quote]
    # C) Regla específica para IA (Antigravity)
    Política para agentes IA (Antigravity):
    - Antes de codificar, debe leer el 
    - Debe confirmar entendimiento y NO inventar flujos.
    - Debe ejecutar Quality Gates:
      - Gate 0
      - Gate 1
      - Gate 3
    - Al finalizar, debe actualizar:
      - Notion: Estado Actual + Log + resultado Gate 3
      - GitHub: rama + commits + tag si corresponde
    # D) Protocolo de Trabajo con IA (Antigravity / Agentes)
    “Regla de comunicación”
    [BLOCK: quote]
    Ejemplo:
    - “branch (rama: copia paralela del código para trabajar sin afectar lo estable)”
    - “commit (registro: guardado de cambios en GitHub)”
    - “rollback (volver atrás: regresar a una versión estable)”
    - “E2E (fin a fin: prueba completa como lo usa un usuario)”
  ### [Parte XI - DOCOPS-NOTION — Estándar de Cierre]
    [BLOCK: divider]
    # 1) Objetivo
    Garantizar trazabilidad (registro verificable) y continuidad entre sesiones (sin pérdida de contexto), evitando duplicidades y contradicciones en Notion.
    ## 2) Principio “Handoff Único” (OBLIGATORIO)
    Para evitar información repetida y contradictoria:
    El único bloque “vivo” (que se actualiza en cada sesión) es:
    Datos que viven SOLO ahí (no se repiten en otras secciones):
    - Versión estable actual (tag = etiqueta)
    - Commit relevante (hash = código corto)
    - Gates (compuertas de calidad)
    - Bugs abiertos
    - Próximo paso exacto (siempre desde Backlog en columna Ready)
    Regla anti-duplicidad (OBLIGATORIO):
    Se escribe una sola línea: 
    ## 3) DOCOPS DONE = 3 páginas + verificación (OBLIGATORIO)
    Antigravity solo puede declarar 
    ### A) Backlog (tablero Kanban = tablero por columnas)
    - Identificar la tarjeta activa (ID).
    - Moverla al estado correcto (por ejemplo: Ready → In Progress → Done / Blocked).
    - La “siguiente tarea” se toma SOLO de la columna 
    ### B) Log del Proyecto (bitácora)
    - Agregar una entrada con formato oficial:
      - Fecha/hora
      - Objetivo
      - Cambio aplicado
      - Gate 0 (PASS/FAIL)
      - Gate 3 (PASS/FAIL) + evidencia (capturas/video/artefactos)
      - Bugs abiertos
      - Próximo paso
    ### C) Estado Actual (página del proyecto)
    - NO duplicar datos operativos.
    - Confirmar que la página quedó con:
      - Handoff arriba (bloque vivo)
      - Scope (alcance = qué incluye)
      - Riesgos (qué no romper)
      - Referencia a este estándar (Parte XI)
    ### D) Verificación (Readback = re-lectura obligatoria)
    Antigravity debe re-abrir Notion y pegar en el chat:
    1. Texto final del 
    1. La última entrada del 
    1. La tarjeta que queda en 
    Sin esta verificación, 
    ## 4) Prompt estándar (referencia)
    El prompt de arranque y cierre vive en “Parte X — Prompt estándar para Antigravity”.
Este estándar (Parte XI) tiene prioridad sobre cualquier instrucción suelta en chats.
### [Glosario Técnico Oficial — Metodología Antay v2.0]
  Glosario Técnico Oficial — Metodología Antay v2.0
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [BLOCK: quote]
  [BLOCK: divider]
  [BLOCK: callout]
    - Referencia oficial única de terminología técnica para todos los proyectos de Antay Fábrica de Software.
  [BLOCK: divider]
  [BLOCK: table_of_contents]
  [BLOCK: divider]
  ## Metadatos
  - Versión:
  - Última actualización:
  - Mantenido por:
  - Estado:
  - Nota:
  [BLOCK: divider]
  ## Propósito, audiencia y alcance
  - Propósito:
  - Audiencia:
  - Alcance:
  [BLOCK: divider]
  ## Cómo usar este glosario
  - Regla 1:
  - Regla 2:
  - Regla 3:
  [BLOCK: divider]
  # Glosario por categoría
  [BLOCK: quote]
  [BLOCK: quote]
  [BLOCK: quote]
  [BLOCK: quote]
  [BLOCK: divider]
  ## 1) Control de Versiones (Git)
  Herramientas y conceptos para gestionar versiones del código fuente.
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Repository
  🗣️ 
  📖 
  💡 
  ✅ 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Branch
  🗣️ 
  📖 
  💡 
  ✅ 
  🔍 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Commit
  🗣️ 
  📖 
  💡 
  ✅ 
  🔍 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Push / Pull
  🗣️ 
  📖 
  💡 
  ✅ 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Merge
  🗣️ 
  📖 
  💡 
  ✅ 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Clone / Fork
  🗣️ 
  📖 
  💡 
  ✅ 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Conflict
  🗣️ 
  📖 
  💡 
  ✅ 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Rollback / Tag
  🗣️ 
  📖 
  💡 
  ✅ 
  🔍 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ### 📘 Git / GitHub
  🗣️ 
  📖 
  💡 
  ✅ 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [BLOCK: divider]
### [Base de Documentación Profesional]
  🏭 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [BLOCK: quote]
  [BLOCK: divider]
  [BLOCK: table_of_contents]
  [BLOCK: divider]
  ## 📋 Descripción General
  Esta plantilla de Notion está diseñada para servir como base documental para una fábrica de software moderna, basada en estándares internacionales y mejores prácticas de la industria.
  ## 🎯 Objetivo
  Proporcionar una estructura organizacional completa y profesional que permita gestionar todos los aspectos de desarrollo de software de manera eficiente y estandarizada.
  ## 📁 Estructura de la Plantilla
  La plantilla contiene 
  [BLOCK: divider]
  ## 📚 Índice de Subpáginas
  ### [00_ResumenGeneral]
    ## 🎯 Propósito General
    Antay Fábrica de Software es una iniciativa que busca construir soluciones digitales profesionales, accesibles y personalizables para emprendedores y pequeñas empresas, utilizando agentes de inteligencia artificial como fuerza de desarrollo y operación. Esta fábrica opera bajo estándares internacionales de calidad, flujos de trabajo ágiles y herramientas digitales modernas.
    ## 🧱 Objetivos
    - Establecer una 
    - Facilitar el desarrollo y mantenimiento de 
    - Documentar y estandarizar todo el proceso con miras a 
    ## 📌 Proyecto Matriz (Proyecto Base)
    Este documento y su contexto en ChatGPT representan el 
    [BLOCK: quote]
    Aquí se definirán las reglas, flujos, agentes IA, tipos de pruebas, metodologías y decisiones clave que regirán todos los desarrollos futuros.
    ## 🛠️ Primer Proyecto Registrado
    - Nombre:
    - Objetivo:
    - Stack:
    ## 👤 Perfil del Líder del Proyecto
    Camilo Ortega F.R. lidera la iniciativa, guiado por principios de organización profesional, documentación clara y enfoque en eficiencia. La fábrica trabaja con agentes IA altamente especializados, sin necesidad de programadores humanos, pero con supervisión humana rigurosa.
    ## 🔍 Herramientas Utilizadas
    - ChatGPT
    - Notion
    - GitHub
    - Streamlit
    - Google Sheets / Excel
    ## 📦 Qué se Documentará Aquí
    - El 
    - El 
    - La 
    - Las 
    - La 
    ## 🔁 Ciclo de Vida de un Proyecto
    Cada nuevo proyecto (como CatalogPro) seguirá el siguiente ciclo:
    1. Registro en ChatGPT como nuevo proyecto hijo
    1. Definición funcional/documental
    1. Generación con agentes IA
    1. Control de calidad y pruebas
    1. Publicación como Web App
    1. Revisión post-lanzamiento y ajustes
    ## 📌 Nota Final
    Esta documentación es 
    [BLOCK: divider]
    [BLOCK: quote]
  ### [02_Manual de calidad y pruebas]
    Este documento establece las normas, criterios y tipos de pruebas que regirán la calidad de todos los desarrollos dentro de la fábrica de software. Se basa en estándares internacionales y busca garantizar productos funcionales, usables, estables y escalables.
    [BLOCK: divider]
    ## 🎯 Objetivos de la Calidad
    - Garantizar que cada solución funcione según lo especificado.
    - Asegurar que la experiencia del usuario sea óptima y fluida.
    - Prevenir errores críticos antes de que lleguen al usuario final.
    - Fomentar la mejora continua y evolución del software entregado.
    [BLOCK: divider]
    ## 🔍 Tipos de Pruebas Aplicadas
    ### 1. 🧪 Pruebas Unitarias (Unit Testing)
    - Validan el correcto funcionamiento de funciones o componentes individuales.
    - Automatizadas o manuales, según complejidad.
    ### 2. 🔗 Pruebas de Integración
    - Verifican cómo interactúan los diferentes módulos del sistema.
    - Aseguran que no haya ruptura en el flujo de datos entre componentes.
    ### 3. 🧭 Pruebas Funcionales
    - Evalúan que las funcionalidades declaradas se ejecuten según lo esperado.
    - Basadas en los requerimientos funcionales del proyecto.
    ### 4. 👨‍💻 Pruebas de Usabilidad
    - Evalúan la facilidad de uso y navegación.
    - Enfocadas en la experiencia del usuario final.
    - Se valida en dispositivos móviles y PC.
    ### 5. 🤖 Pruebas Automatizadas
    - Se aplican cuando existe lógica repetitiva y flujos estables.
    - Uso de frameworks ligeros compatibles con Python + Streamlit.
    ### 6. 🙋‍♂️ Pruebas de Aceptación de Usuario (UAT)
    - Ejecutadas por el líder del proyecto o el usuario final.
    - Validan si el sistema cumple con las necesidades prácticas.
    - Son la última validación antes de la publicación.
    [BLOCK: divider]
    ## 🧩 Estándares Adicionales de Calidad
    - Código limpio, comentado y versionado.
    - Interfaces responsivas y accesibles.
    - Control de errores y validación de datos de entrada.
    - Flujo de navegación coherente.
    - Exportación funcional de catálogos (en PDF/HTML).
    - Agilidad para interacción con WhatsApp/Email.
    [BLOCK: divider]
    ## 🗂️ Documentación de Pruebas
    - Toda ejecución de pruebas debe:
      - Registrar escenarios cubiertos.
      - Anotar errores detectados y soluciones aplicadas.
      - Documentarse en Notion bajo el proyecto correspondiente.
      - Ser actualizada con cada versión publicada.
  ### [03_EstructuraAgentesIA]
    Este documento define los roles, funciones, reglas de actuación y delimitaciones de los agentes de inteligencia artificial que participan en los proyectos de Antay Fábrica de Software. Cada agente cumple un propósito especializado y se integra en distintas fases del ciclo de desarrollo.
    [BLOCK: divider]
    ## 🧭 Propósito del Modelo Multi-Agente
    - Distribuir las responsabilidades de desarrollo, pruebas, documentación y diseño entre agentes IA especializados.
    - Acelerar la producción sin sacrificar calidad.
    - Documentar de manera estructurada las interacciones, decisiones y entregables de cada agente.
    [BLOCK: divider]
    ## 👥 Agentes y sus Roles
    ### 1. 
    - Interpreta requerimientos del líder del proyecto o usuario.
    - Genera especificaciones funcionales claras.
    - Identifica entradas, salidas y reglas del negocio.
    ### 2. 
    - Propone interfaces limpias, accesibles y modernas.
    - Define jerarquía visual, espaciado, colores, estilo.
    - Adapta la vista para dispositivos móviles y PC.
    ### 3. 
    - Genera el código fuente siguiendo las especificaciones.
    - Se adapta al stack definido (ej. Python + Streamlit).
    - Usa buenas prácticas, modularidad y comentarios útiles.
    ### 4. 
    - Sugiere y ejecuta casos de prueba.
    - Reporta errores, comportamientos inesperados y mejoras.
    - Trabaja con las fases de pruebas definidas (unitarias, integración, UAT, etc.)
    ### 5. 
    - Resume decisiones clave del proyecto.
    - Genera la documentación interna de cada fase.
    - Registra versiones, notas de actualización, archivos exportables.
    ### 6. 
    - Define cuándo crear versiones y ramas.
    - Coordina el uso de GitHub para control de versiones.
    - Sugiere buenas prácticas de actualización y merge.
    [BLOCK: divider]
    ## 🔄 Interacción entre Agentes
    - Todos los agentes siguen instrucciones del líder del proyecto.
    - No actúan por cuenta propia sin contexto o reglas dadas.
    - Cada uno entrega su parte de forma ordenada y documentada.
    [BLOCK: divider]
    ## 🔐 Reglas para su Operación
    - Cada agente debe:
      - Usar lenguaje técnico, claro y profesional.
      - Indicar sus límites si una tarea supera su especialización.
      - Evitar asumir funcionalidades sin validación del analista o líder.
    [BLOCK: divider]
    ## 🧠 Notas Finales
    - Cada agente puede ser ejecutado en sesiones separadas o en conversaciones específicas.
    - La trazabilidad y resultados deben mantenerse organizados en Notion.
    - Si se desea migrar esta arquitectura a otra plataforma IA (Claude, Perplexity, etc.), se debe respetar esta misma estructura base.
  ### [04_Normas de documentación de proyectos]
     
    Este documento establece los lineamientos para estructurar, redactar, almacenar y mantener la documentación interna de todos los proyectos desarrollados dentro de la fábrica de software. Su propósito es garantizar trazabilidad, comprensión y reutilización del conocimiento generado.
    [BLOCK: divider]
    ## 📁 Estructura Base por Proyecto en Notion
    Cada proyecto activo debe contener los siguientes apartados documentados:
    1. Resumen Ejecutivo del Proyecto
      - Objetivo
      - Público objetivo
      - Solución propuesta
    1. Requerimientos Funcionales y Técnicos
      - Entradas esperadas
      - Resultados esperados
      - Reglas de negocio
    1. Diseño UI/UX (Borradores o imágenes)
      - Prototipos (opcionalmente en Canva o Figma)
      - Guías de colores, fuentes y espaciado
    1. Planificación del Desarrollo
      - Fases del proyecto
      - Entregables por fase
      - Responsable (agente o humano)
    1. Código Fuente y Estructura de Carpetas
      - Enlace a repositorio GitHub (rama por fase o versión)
      - Descripción de carpetas y archivos
    1. Ejecución de Pruebas QA
      - Casos de prueba ejecutados
      - Errores detectados y corregidos
      - Validación UAT final
    1. Versiones Publicadas y Cambios
      - Registro de cada versión con fecha
      - Funcionalidades agregadas o modificadas
    1. Notas Técnicas o de Soporte
      - Dependencias, librerías usadas
      - Errores recurrentes y soluciones aplicadas
      - Consideraciones de compatibilidad
    [BLOCK: divider]
    ## ✍️ Estilo de Redacción
    - Lenguaje técnico, claro y directo.
    - Sin adornos comerciales ni palabras vacías.
    - Uso de viñetas o listas para mejorar la legibilidad.
    - Fechas claramente indicadas.
    - Cada entrada debe tener responsable, fecha y estado (borrador / validado).
    [BLOCK: divider]
    ## 🛠️ Herramientas de Soporte
    - Notion:
    - GitHub:
    - Canva/Figma (opcional):
    - ChatGPT / Claude / otros:
    [BLOCK: divider]
    ## 🔁 Revisión y Actualización
    - La documentación debe actualizarse al menos al final de cada fase.
    - Los documentos deben estar alineados al avance del desarrollo real.
    - En caso de cambios importantes, debe actualizarse la fecha de última edición.
  ### [06_Gestion de proyectos Notion]
    Este documento define la estructura de trabajo, plantillas y seguimiento de proyectos que se utilizará en Notion como sistema central de gestión y documentación interna.
    [BLOCK: divider]
    ## 🎯 Objetivos
    - Centralizar la información, avances, decisiones y documentación de cada proyecto.
    - Asegurar trazabilidad y seguimiento transparente.
    - Integrar contenido generado por agentes IA, flujos técnicos y documentación QA.
    [BLOCK: divider]
    ## 🧱 Estructura Base de Notion
    ### 🗂️ 1. 
    - Acceso directo a todos los proyectos activos, archivados y en validación.
    - Vista por fases: Planeación, Desarrollo, QA, Lanzamiento, Soporte.
    ### 📁 2. 
    Cada proyecto tiene una ficha que contiene:
    - Nombre del proyecto
    - Enlace al repositorio GitHub
    - Documentación viva (vínculos internos)
    - Estado actual y responsables
    - Historial de cambios
    ### 🧩 3. 
    Cada ficha de proyecto incluye:
    - Documentos: Resumen, Flujo de Desarrollo, Manual QA, etc.
    - Lista de tareas (Kanban)
    - Calendario de entregas
    - Registro de pruebas (manuales y automáticas)
    - Bitácora de decisiones
    [BLOCK: divider]
    ## 🛠️ Reglas de Uso
    - Toda documentación generada en ChatGPT se exporta a Notion.
    - Solo se puede editar por usuarios con permisos explícitos.
    - Se debe actualizar con cada nuevo avance, commit o entrega QA.
    - Los agentes IA pueden consultar y actualizar contenido bajo reglas específicas.
    [BLOCK: divider]
    ## 🔗 Integración con GitHub y ChatGPT
    - Cada proyecto en Notion debe enlazar al repositorio GitHub.
    - Cada entrada documentada debe tener contexto y estar sincronizada con lo conversado en ChatGPT.
    - Se crea una tabla de sincronización entre documentos clave (README, manual QA, changelog).
  ### [09_Control de accesos y roles]
    Este documento establece los roles definidos dentro de la fábrica, así como los niveles de acceso permitidos en cada herramienta colaborativa (ChatGPT, Notion, GitHub). El objetivo es garantizar la seguridad, trazabilidad y responsabilidad compartida en todos los proyectos.
    [BLOCK: divider]
    ## 👤 Roles Oficiales
    ### 1. 🧠 Líder de Proyecto (Humano)
    - Define objetivos, aproba versiones, y supervisa la calidad final.
    - Interactúa directamente con los agentes IA y toma decisiones finales.
    ### 2. 🤖 Agentes de IA Especializados
    - Arquitecto IA
    - Desarrollador Frontend IA
    - Desarrollador Backend IA
    - QA IA
    - Documentador IA
    ### 3. 👩‍💻 Colaboradores Técnicos (opcional)
    - En caso se incorporen humanos técnicos en el futuro (devs, testers, diseñadores).
    [BLOCK: divider]
    ## 🛠️ Acceso por Herramienta
    [BLOCK: table]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
    [BLOCK: divider]
    ## 🔄 Procedimientos de Seguridad y Control
    - Toda modificación en código/documentos debe ser registrada.
    - No se comparten accesos sensibles directamente con agentes IA.
    - Todo acceso nuevo debe ser aprobado por el líder.
    - Se mantendrá un log de actividades en Notion.
  ### [10_Gestion de versiones publicaciones]
    Este documento define el esquema oficial para el versionamiento de soluciones desarrolladas, así como las condiciones para considerar una versión lista para su publicación (release). Está alineado con buenas prácticas de la industria y se aplica a todo el ciclo de desarrollo.
    [BLOCK: divider]
    ## 🔢 Esquema de Versionado – SemVer
    Se utiliza el esquema Semantic Versioning (SemVer):
    [BLOCK: code]
    - MAJOR
    - MINOR
    - PATCH
    [BLOCK: quote]
    [BLOCK: divider]
    ## 🚦 Criterios para Publicar una Versión
    Una versión es considerada 
    1. ✅ Todas las funcionalidades planificadas están completas.
    1. ✅ Pasó por pruebas unitarias, funcionales, automatizadas (si aplica) y UAT.
    1. ✅ Documentación técnica y de usuario está actualizada.
    1. ✅ Revisión de código superada y cambios versionados en GitHub.
    1. ✅ Aprobación explícita del Líder del Proyecto.
    [BLOCK: divider]
    ## 🗃️ Publicación y Entrega
    - Entorno de producción
    - Nombre de release
    - Backup
    - Histórico
    [BLOCK: divider]
    ## 🔄 Ciclo de Actualizaciones
    - El equipo puede lanzar parches sin necesidad de pasar por UAT si son urgencias críticas.
    - Cada cambio debe quedar trazado en GitHub con mensajes de commit descriptivos.
    - No se acepta push directo a rama principal sin revisión.
  ### [11_Gestión de incidencias y feedback]
    Este documento establece el procedimiento oficial para registrar, clasificar, priorizar y resolver incidencias técnicas o feedback de usuarios en los proyectos desarrollados por la fábrica de software.
    [BLOCK: divider]
    ## 🧾 Registro de Incidencias
    Todas las incidencias deben ser registradas en Notion bajo la sección "Incidencias del Proyecto". Cada entrada debe incluir:
    - 🆔 ID único
    - 📝 Descripción clara y detallada del problema
    - 📷 Evidencia (imagen/video/logs si aplica)
    - 🔢 Versión en la que ocurrió
    - 👤 Reportado por
    - 📅 Fecha de reporte
    - ⏱️ Estado: Reportado / En análisis / En solución / Solucionado / Descartado
    [BLOCK: divider]
    ## 🧭 Clasificación y Priorización
    - Críticas (Alta prioridad)
    - Altas
    - Medias
    - Bajas
    [BLOCK: quote]
    [BLOCK: divider]
    ## 🔄 Flujo de Resolución
    1. El desarrollador o agente IA analiza el caso y propone solución.
    1. Se valida por QA o Líder del Proyecto.
    1. Se actualiza el estado en Notion.
    1. Se registra el cambio en GitHub (si aplica).
    1. Se incluye en el changelog de la siguiente versión.
    [BLOCK: divider]
    ## 💬 Feedback de Usuario
    - Se registrará en la misma sección con la etiqueta 
    - Será evaluado y clasificado como:
      - Mejora menor (UI, accesibilidad, contenido)
      - Sugerencia futura
      - Requiere análisis previo
    [BLOCK: divider]
    ## 📊 Métricas de Seguimiento
    Cada proyecto debe medir:
    - % de incidencias resueltas por versión
    - Tiempo promedio de resolución
    - Tipos de incidencias más frecuentes
    Estas métricas serán revisadas en reuniones mensuales internas.
  ### [12_Estándares de calidad de código ]
    Este documento define las buenas prácticas y lineamientos que deben seguirse para garantizar un código limpio, mantenible, legible y de alta calidad en todos los proyectos de la fábrica de software.
    [BLOCK: divider]
    ## 📋 Convenciones Generales
    - Seguir las convenciones de estilo del lenguaje utilizado (PEP8 en Python, Airbnb Style Guide en JavaScript/React, etc.).
    - Nombrar variables, funciones y archivos de forma clara, semántica y consistente.
    - Usar comentarios solo donde sean necesarios para clarificar lógica compleja.
    - Separar responsabilidades (principio de responsabilidad única).
    - Evitar código duplicado.
    - Utilizar control de versiones con commits descriptivos y atómicos.
    [BLOCK: divider]
    ## 🧼 Buenas Prácticas
    - Escribir funciones puras y pequeñas.
    - Aplicar principios SOLID y DRY.
    - Usar linters y formateadores automáticos (black, prettier, eslint).
    - Documentar funciones y módulos críticos con docstrings o JSDoc.
    - Validar entradas del usuario y manejar errores de forma controlada.
    [BLOCK: divider]
    ## ✅ Revisión de Código (Code Review)
    Todo código debe pasar por una revisión antes de ser fusionado a la rama principal:
    - Pull request obligatorio en GitHub.
    - Mínimo 1 aprobación externa (otro agente IA o humano).
    - Validación de pruebas superadas (unitarias, automatizadas si aplica).
    - Verificación de que se sigan las convenciones y buenas prácticas.
    [BLOCK: quote]
    [BLOCK: divider]
    ## 🧪 Pruebas y Calidad
    - Incluir pruebas unitarias obligatorias para funciones críticas.
    - Cobertura mínima recomendada: 80%.
    - Ejecutar pruebas automáticamente en CI/CD (GitHub Actions).
    - QA validará funcionalidades claves en entorno staging.
    [BLOCK: divider]
    ## 📁 Estructura de Proyecto
    Cada proyecto debe mantener:
    - Estructura modular clara.
    - Separación de código de backend y frontend (si aplica).
    - Directorios bien nombrados y organizados por función.
    - README técnico actualizado y útil.
    [BLOCK: divider]
    ## 🚨 Control de Calidad Automatizado
    - Integrar herramientas como SonarQube o CodeQL en el pipeline.
    - Configurar GitHub Actions para verificar calidad y seguridad del código.
  ### [13_Plan de pruebas y estrategias de Testing]
    Este documento formaliza los tipos de pruebas, sus objetivos, responsables y la estrategia de calidad aplicada a todos los proyectos desarrollados por Antay Fábrica de Software.
    [BLOCK: divider]
    ## 🎯 Objetivo General
    Garantizar que las soluciones desarrolladas cumplan con los requisitos funcionales, no funcionales, de usabilidad, rendimiento, accesibilidad y seguridad definidos, bajo un enfoque profesional y estructurado.
    [BLOCK: divider]
    ## 🧩 Tipos de Pruebas Aplicadas
    [BLOCK: table]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
    [BLOCK: divider]
    ## 🔄 Estrategia de Ejecución
    1. Entorno de testing:
    1. Herramientas usadas:
      - Pruebas manuales: Checklist Notion
      - Automatizadas: Pytest, Selenium, CI/CD GitHub Actions
      - UAT: Formularios Notion con checklist por módulo
    1. Criterios de aceptación:
      - Todas las pruebas funcionales deben pasar al 100%
      - No deben existir errores críticos o bloqueantes
      - Pruebas UAT aprobadas por el cliente
    [BLOCK: divider]
    ## 📦 Evidencias y Reporte
    - Todas las pruebas se documentan en Notion
    - Se adjuntan capturas, logs, videos o resultados automáticos
    - Se vinculan a la versión de despliegue respectiva en GitHub
    [BLOCK: divider]
    ## 🧮 Métricas de Calidad
    - % de cobertura de pruebas unitarias
    - Tasa de defectos encontrados post-UAT
    - Tiempo promedio de resolución de bugs
  ### [14_Control de versiones y GitHub]
    Este documento define la política de control de versiones, uso de ramas y buenas prácticas para el uso de GitHub como sistema de gestión de código fuente para todos los proyectos desarrollados por la fábrica.
    [BLOCK: divider]
    ## 🎯 Objetivo
    Asegurar trazabilidad, orden, colaboración efectiva y control sobre el ciclo de vida del código fuente de todos los desarrollos.
    [BLOCK: divider]
    ## 🧱 Estructura de Ramas
    [BLOCK: table]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
    [BLOCK: divider]
    ## 🔄 Flujo de Trabajo (Git Flow Simplificado)
    1. Clonar desde 
    1. Crear rama 
    1. Subir cambios con commits atómicos y descriptivos
    1. Realizar 
    1. Revisión por otro agente / QA
    1. Merge con validación de CI/CD y pruebas
    1. Cuando 
    1. Etiquetar versión (
    [BLOCK: divider]
    ## 🧪 Validaciones Obligatorias
    - Toda rama debe tener nombre claro y formato estandarizado
    - Pull Requests requieren:
      - Revisión cruzada por otro miembro o agente IA
      - Pruebas pasadas (unitarias / automatizadas)
      - Verificación de cobertura y formato de código
    [BLOCK: divider]
    ## 📦 Versionado Semántico
    Usamos 
    - MAJOR
    - MINOR
    - PATCH
    [BLOCK: divider]
    ## 📁 Organización de Repositorios
    - Un repositorio por proyecto
    - README técnico obligatorio
    - Incluir changelog y documentación básica
    - Licencia clara (MIT, GPL, etc.)
  ### [15_Checklist de liberación de versiones]
    Este documento establece la lista mínima de verificación que debe cumplirse antes de liberar oficialmente una nueva versión de cualquier proyecto de software desarrollado por la fábrica.
    [BLOCK: divider]
    ## 📋 Lista de Verificación de Publicación
    [BLOCK: table]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
  ### [16_Seguridad, datos y privacidad]
    Este documento establece las políticas y prácticas de seguridad digital, privacidad y protección de datos que deben cumplirse en todos los proyectos desarrollados por la fábrica.
    [BLOCK: divider]
    ## 🔒 Principios Generales
    - Confidencialidad
    - Integridad
    - Disponibilidad
    - Privacidad
    [BLOCK: divider]
    ## 🧱 Prácticas de Seguridad en el Desarrollo
    - Uso de entornos separados para desarrollo, testing y producción.
    - Variables sensibles (API Keys, tokens) gestionadas en 
    - Autenticación segura y control de roles en interfaces de administración.
    - Revisión automática de vulnerabilidades (ej. dependabot, análisis de dependencias).
    [BLOCK: divider]
    ## 🗂️ Gestión de Datos de Usuarios
    - Formularios deben tener consentimiento explícito cuando recojan datos personales.
    - Los datos serán almacenados solo el tiempo necesario y podrán ser eliminados a solicitud.
    - Toda exportación o descarga de datos estará auditada.
    - Si se usan herramientas de terceros (ej. Google Sheets), deben cumplir con términos de privacidad adecuados.
    [BLOCK: divider]
    ## 🔍 Auditoría y Respuesta ante Incidentes
    - Toda actividad relevante será registrada en logs.
    - En caso de incidente, se activará un plan de contención, notificación y resolución.
    - Los incidentes serán documentados y revisados en la reunión mensual.
  ### [17_Buenas Prácticas UX/UI]
    Este documento establece los lineamientos visuales y de experiencia de usuario que deben aplicarse en todos los desarrollos de software de la fábrica, garantizando interfaces modernas, accesibles y coherentes.
    [BLOCK: divider]
    ## 🎯 Principios UX Fundamentales
    - Claridad
    - Jerarquía visual
    - Consistencia
    - Feedback inmediato
    - Accesibilidad
    [BLOCK: divider]
    ## 🧩 Guías UI por Defecto
    - Colores
    - Tipografía
    - Espaciado
    - Botones
    - Iconografía
    [BLOCK: divider]
    ## 🧪 Pruebas de Experiencia de Usuario
    - Prototipos deben validarse con al menos 3 usuarios antes del desarrollo final.
    - Se deben realizar pruebas de navegación, entendimiento y tarea (ej. ¿puede encontrar este botón?).
    - Recoger sugerencias y registrar observaciones en la sección UX de Notion.
    [BLOCK: divider]
    ## 📱 Diseño Responsive
    - Toda interfaz debe adaptarse fluidamente a diferentes tamaños de pantalla (móvil, tablet, desktop).
    - Prioridad a mobile-first cuando el público objetivo lo justifique.
    - Evitar scrolls innecesarios o interfaces rotas en resoluciones pequeñas.
    [BLOCK: divider]
    [BLOCK: quote]
  ### [18_Política de uso de inteligencia artificial]
    Este documento regula el uso ético, estratégico y responsable de herramientas de inteligencia artificial (IA) dentro del ciclo de desarrollo de software de la fábrica.
    [BLOCK: divider]
    ## 🎯 Objetivo
    Maximizar la productividad del equipo y la calidad del software mediante el uso de agentes y asistentes de IA, sin comprometer la ética, la supervisión humana ni la calidad final.
    [BLOCK: divider]
    ## 🧠 Ámbitos de Uso de la IA
    ### 1. Generación de Código y Arquitectura
    - Uso de IA para generación de boilerplate, estructuras iniciales, funciones repetitivas.
    - Propuesta de estructuras de carpetas, diseño de endpoints o lógica base de componentes.
    ### 2. Redacción Técnica
    - Uso de IA para elaborar documentación técnica, manuales de usuario, mensajes de error.
    - Corrección ortográfica y gramática profesional.
    ### 3. Diseño UX/UI Asistido
    - Generación de propuestas visuales o prototipos a partir de prompts.
    - Revisión de buenas prácticas visuales.
    ### 4. QA y Pruebas
    - Generación automática de casos de prueba.
    - Soporte en validación de cobertura y detección de rutas críticas.
    ### 5. Automatización y Productividad
    - Asistencia con scripts de automatización, CI/CD, monitoreo de logs o configuraciones repetitivas.
    [BLOCK: divider]
    ## 🛑 Límites y Reglas
    - Revisión humana obligatoria
    - Transparencia
    - No uso indebido
    - Privacidad
    [BLOCK: divider]
    ## 📌 Registro y Control
    - Cada agente IA tendrá una función definida dentro del proyecto y su output será evaluado.
    - Se asignará a un humano revisor responsable por cada IA involucrada.
    - En Notion se mantendrá un listado de prompts y outputs validados por fase.
  ### [20_Plan de mejora continua]
    Este documento define la estrategia y metodología de mejora continua para garantizar que la fábrica de software evolucione, se adapte a nuevas tecnologías y mantenga altos estándares de calidad y eficiencia.
    [BLOCK: divider]
    ## 🎯 Objetivos del Plan
    - Identificar oportunidades de mejora en procesos, herramientas y resultados.
    - Aumentar la eficiencia, la calidad y la satisfacción del cliente.
    - Fomentar la innovación constante con ayuda de IA.
    - Alinear la evolución interna con estándares internacionales.
    [BLOCK: divider]
    ## 🔁 Ciclo de Mejora Continua (PDCA)
    1. Planificar (Plan):
      - Revisión mensual de procesos, herramientas y feedback de usuarios.
      - Definición de objetivos de mejora.
    1. Ejecutar (Do):
      - Implementación de mejoras en pequeños sprints controlados.
      - Pruebas internas y monitoreo del cambio.
    1. Verificar (Check):
      - Evaluación de resultados post-implementación.
      - Comparación con métricas anteriores.
    1. Actuar (Act):
      - Documentación de aprendizajes.
      - Ajustes finales o retroceso si es necesario.
    [BLOCK: divider]
    ## 🧰 Herramientas de Soporte
    - Notion:
    - GitHub Issues:
    - Encuestas y Retroalimentación:
    - Revisión de Prompts IA:
    [BLOCK: divider]
    ## 📊 Métricas a Monitorear
    - Tiempo promedio de desarrollo por módulo.
    - Porcentaje de cobertura de pruebas.
    - Número de incidencias detectadas post-producción.
    - Tiempo de respuesta ante bugs críticos.
    - Nivel de satisfacción del usuario final (NPS).
    [BLOCK: divider]
    ## 🧭 Gobernanza del Plan
    - El 
    - Los cambios aprobados deben ser implementados por el equipo responsable y documentados en Notion.
    - Las métricas se presentan trimestralmente en formato visual para análisis estratégico.
  ### [21_Estándares tecnológicos]
    Este documento define las tecnologías base, convenciones y buenas prácticas que guían el desarrollo técnico dentro de la fábrica de software. Establece un marco común para asegurar compatibilidad, mantenibilidad y escalabilidad.
    [BLOCK: divider]
    ## ⚙️ Lenguajes y Entornos Preferidos
    - Frontend Web:
      - Framework principal: 
      - Alternativo: 
    - Backend y lógica de negocio:
      - Python
      - Librerías comunes: 
    - Automatización e Integración de IA:
      - OpenAI
    - Base de Datos:
      - PostgreSQL
    [BLOCK: divider]
    ## 🧱 Infraestructura y DevOps
    - Repositorio de código:
    - Control de versiones:
    - CI/CD:
    - Despliegue:
    [BLOCK: divider]
    ## 🧾 Convenciones de Código
    - Python:
      - Estilo PEP8 obligatorio.
      - Nombrado de funciones: 
      - Comentarios doctrinales 
    - JavaScript/React:
      - Nombrado en 
      - Componentes funcionales, preferencia por hooks.
    - Uso de Prompts IA:
      - Documentar en Notion prompts usados para generación de código.
      - Todo código generado por IA debe ser validado por un humano.
    [BLOCK: divider]
    ## 🧪 Buenas prácticas de desarrollo
    - Validar inputs del usuario.
    - Capturar y loguear errores.
    - Modularizar el código y evitar duplicación.
    - Mantener estructura limpia del proyecto (carpetas bien definidas).
  ### [22_Métricas y Seguimiento]
    Este documento define los indicadores clave (KPIs) y mecanismos de seguimiento que utilizamos para evaluar el desempeño de los proyectos, la productividad de los agentes y la calidad de las entregas dentro de nuestra fábrica de software.
    [BLOCK: divider]
    ## 📌 Categorías de Métricas
    ### 1. 
    - % de tareas completadas vs planificadas
    - Tiempo medio por entrega funcional
    - Retrasos acumulados vs cronograma
    ### 2. 
    - % de revisiones con observaciones críticas
    - % de código generado por IA vs ajustado por humanos
    - % de cumplimiento con estándares de codificación
    ### 3. 
    - % de cobertura con pruebas unitarias y funcionales
    - % de pruebas automatizadas vs manuales
    - Número de bugs detectados en UAT
    ### 4. 
    - Feedback NPS (Net Promoter Score)
    - Encuestas de usabilidad (escala 1-5)
    - Tasa de adopción de la funcionalidad entregada
    ### 5. 
    - Número de sugerencias/retrospectivas implementadas
    - Frecuencia de actualización del backlog
    - % de cumplimiento de iniciativas de mejora
    [BLOCK: divider]
    ## 📍 Herramientas de Seguimiento
    - Trello o Notion
    - GitHub Insights
    - Streamlit Dashboard (opcional):
    [BLOCK: divider]
    ## 🔁 Frecuencia de Evaluación
    - Semanal:
    - Quincenal:
    - Mensual:
  ### [23_Modelos de negocio base]
    Este documento describe el modelo de negocio general de la Fábrica de Software Antay, incluyendo su propuesta de valor, segmentos de clientes, estructura operativa y fuentes de ingresos.
    [BLOCK: divider]
    ## 💎 Propuesta de Valor
    - Desarrollo de soluciones web rápidas, funcionales y profesionales utilizando IA.
    - Productos pensados para pequeños emprendedores con necesidades claras y tiempos limitados.
    - Bajo costo de desarrollo gracias a la automatización con agentes IA.
    [BLOCK: divider]
    ## 👥 Segmentos de Clientes
    - Emprendedores sin conocimientos técnicos que necesitan herramientas digitales listas para usar.
    - PYMEs que requieren soluciones personalizadas con bajo costo.
    - Consultores que buscan productos digitalizados para terceros.
    [BLOCK: divider]
    ## 🧱 Estructura de Oferta
    - Soluciones tipo 
    - Apps web exportables en formato HTML, PDF o compartibles por WhatsApp/email.
    - Capacitación mínima: interfaces intuitivas, sin necesidad de instalación.
    [BLOCK: divider]
    ## 🔁 Proceso Productivo
    1. Captación del cliente (web, referidos, redes).
    1. Relevamiento rápido del requerimiento.
    1. Generación del prototipo y UI con IA.
    1. Desarrollo con supervisión humana.
    1. Validación y pruebas (incluye UAT).
    1. Entrega del producto y capacitación exprés.
    [BLOCK: divider]
    ## 💸 Modelo de Ingresos
    - Venta directa de productos listos.
    - Personalización sobre demanda (servicio adicional).
    - Planes de soporte técnico y mejoras.
    [BLOCK: divider]
    ## 📈 Escalabilidad
    - Plantillas reutilizables con ajustes por vertical.
    - Repositorio central de proyectos y módulos reutilizables (GitHub).
    - Producción descentralizada con agentes IA escalables.
  ### [24_Casos de Uso y Plantillas Base ]
    Este documento recopila y estandariza los casos de uso más frecuentes desarrollados por la Fábrica de Software Antay, así como las plantillas de solución que se reutilizarán como punto de partida en nuevos proyectos.
    [BLOCK: divider]
    ## 🧰 Plantillas Base Reutilizables
    ### 1. 
    - Input: Hoja con nombre, descripción, imagen, precio, categoría.
    - Output: Interfaz web visual con botones para compartir vía WhatsApp o email.
    - Opciones: Exportación a HTML, PDF.
    ### 2. 
    - Input: Prompts descriptivos, logos, identidad de marca.
    - Output: Landing page responsive con diseño profesional, formularios de contacto.
    ### 3. 
    - Input: Hoja de cálculo con datos de clientes y pedidos.
    - Output: Aplicación simple para filtrar, visualizar, actualizar y exportar pedidos.
    [BLOCK: divider]
    ## 🧩 Casos de Uso Tipo
    ### A. Emprendedor sin web ni catálogo
    [BLOCK: quote]
    - Solución: Catálogo + exportación PDF + botón de contacto WhatsApp.
    ### B. Negocio con presencia digital débil
    [BLOCK: quote]
    - Solución: Landing Page + catálogo básico + capacitación de uso.
    ### C. Comercializador o distribuidor con clientes frecuentes
    [BLOCK: quote]
    - Solución: Filtros dinámicos + selección múltiple + envío directo.
    ### D. Agencia o consultor digital
    [BLOCK: quote]
    - Solución: Kit de plantillas personalizables + manual de uso.
    [BLOCK: divider]
    ## 🔄 Mantenimiento de Plantillas
    - Toda plantilla debe estar documentada en Notion y versionada en GitHub.
    - Las versiones estables se etiquetan y se conectan a flujos de trabajo automatizados.
  ### [25_Plan de soporte y mantenimiento]
    Este documento establece el protocolo de soporte post-entrega y las directrices para el mantenimiento evolutivo y correctivo de las soluciones entregadas.
    [BLOCK: divider]
    ## 🧭 Alcance del Soporte
    ### Soporte Básico Incluido (30 días desde la entrega)
    - Corrección de errores funcionales menores.
    - Asistencia en el uso correcto de la interfaz.
    - Reenvío de enlaces o archivos si el cliente los extravía.
    ### Soporte Extendido (Planes pagos)
    - Ampliación de funcionalidades.
    - Personalización de interfaz, colores, o estructura.
    - Soporte técnico recurrente y mejoras.
    [BLOCK: divider]
    ## 🔁 Tipos de Mantenimiento
    ### 1. Mantenimiento Correctivo
    - Corrección de errores detectados luego de la entrega.
    - Ajustes de compatibilidad por cambios en navegadores o plataformas.
    ### 2. Mantenimiento Evolutivo
    - Incorporación de nuevas funciones solicitadas por el cliente.
    - Integración con nuevas fuentes de datos, canales de exportación u otros sistemas.
    [BLOCK: divider]
    ## 🕒 Tiempo de Respuesta y Prioridades
    [BLOCK: table]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
      [BLOCK: table_row]
    [BLOCK: divider]
    ## 📦 Entorno de Entrega y Backup
    - Cada solución final se entrega comprimida (ZIP) con carpeta de código fuente, HTML/PDF generado y guía básica.
    - Se recomienda al cliente hacer backup tras cada mejora o descarga.
    [BLOCK: divider]
    ## 📑 Registro de Incidencias
    - Cada cliente tendrá una hoja de seguimiento compartida donde se registran incidencias y acciones tomadas.
    - Los cambios mayores deben registrarse también en el historial del repositorio GitHub.
  ### [26_Política de Seguridad y Privacidad]
    Este documento establece los principios, prácticas y estándares que guían el tratamiento seguro y responsable de los datos e información en todos los desarrollos realizados por la Fábrica de Software Antay.
    [BLOCK: divider]
    ## 🛡️ Principios Rectores
    - Confidencialidad:
    - Integridad:
    - Disponibilidad:
    [BLOCK: divider]
    ## 🔍 Recolección y Uso de Datos
    - Solo se recolectan datos necesarios para el funcionamiento de la aplicación.
    - Ningún dato es compartido con terceros sin consentimiento del cliente.
    - En el caso de soluciones basadas en Google Sheets o Excel, los archivos permanecen bajo control del cliente.
    [BLOCK: divider]
    ## 🔒 Mecanismos de Seguridad Aplicados
    - Accesos con autenticación básica o API Key cuando aplique.
    - Despliegue en servidores seguros (ej. Vercel con HTTPS).
    - Revisión periódica de código en búsqueda de vulnerabilidades básicas.
    [BLOCK: divider]
    ## 🧯 Protección ante Fallos
    - Copias de seguridad locales durante el proceso de desarrollo.
    - Exportación del producto final en formatos estándar (ZIP, HTML, PDF).
    [BLOCK: divider]
    ## 👥 Privacidad del Usuario Final
    - Las soluciones no recolectan datos sensibles de usuarios finales.
    - Las funcionalidades como envío por WhatsApp o email no almacenan ni procesan los datos del receptor.
    [BLOCK: divider]
    ## 📌 Compromiso Institucional
    Antay Fábrica de Software se compromete a:
    - No vender, alquilar ni divulgar datos de clientes.
    - Asesorar al cliente en buenas prácticas de protección de información.
    - Adoptar progresivamente estándares de seguridad más avanzados conforme la fábrica evolucione.
  ### [27_Estándares de desarrollo]
    Este documento define las convenciones, prácticas y normas de codificación aplicadas a todos los proyectos desarrollados dentro de la Fábrica de Software Antay. Garantiza consistencia, legibilidad y calidad a lo largo del ciclo de vida del software.
    [BLOCK: divider]
    ## 🎯 Objetivos
    - Promover código limpio, legible y mantenible.
    - Establecer una arquitectura modular y reutilizable.
    - Facilitar colaboración entre agentes humanos e IA.
    - Reducir errores y facilitar el testing y debugging.
    [BLOCK: divider]
    ## 🧱 Estructura y Organización del Código
    - Separación clara entre frontend, backend, lógica y recursos.
    - Nombrado coherente de archivos, carpetas y variables (snake_case o camelCase según lenguaje).
    - Documentación embebida con comentarios precisos y actualizados.
    - Uso de archivos 
    [BLOCK: divider]
    ## 🧑‍💻 Lenguajes y Herramientas Permitidos
    - Python + Streamlit
    - HTML/CSS + JS
    - Selenium / Playwright
    - GitHub
    [BLOCK: divider]
    ## ✨ Buenas Prácticas
    - Aplicación de principios SOLID donde sea posible.
    - Modularización del código en funciones reutilizables.
    - Validación de entradas antes de procesarlas.
    - Logs simples para trazabilidad.
    - Uso de IA (CodeGen) solo en entornos controlados y con validación manual.
    [BLOCK: divider]
    ## 🔁 Control de Versiones y CI/CD
    - Commits descriptivos y frecuentes.
    - Ramas organizadas por feature / fix / release.
    - Integración con GitHub Actions para pruebas automáticas o despliegues.
    [BLOCK: divider]
    ## 📄 Estilo y Formato
    - Convenciones de estilo alineadas al lenguaje (ej. PEP8 en Python).
    - Linter y autoformato (ej. black, prettier).
    - Revisión cruzada antes de mergear código generado por IA.
    [BLOCK: divider]
    ## 📘 Documentación y Readme
    - Todo proyecto debe incluir un 
      - Descripción del proyecto.
      - Requisitos de instalación.
      - Ejemplo de uso.
      - Autor(es) y licencias.
  ### [28_Plantilla de entrega de proyecto]
    Esta plantilla define los elementos mínimos que debe incluir toda entrega final de proyecto al cliente, garantizando trazabilidad, facilidad de uso y claridad técnica.
    [BLOCK: divider]
    ## 📁 Estructura de la Entrega
    [BLOCK: code]
    [BLOCK: divider]
    ## 📋 Contenido Obligatorio
    - README.txt
    - Manual de Usuario:
    - Manual Técnico:
    - Resumen Funcional:
    - Acceso a código fuente:
    - Instrucciones de instalación o acceso web.
    - Datos de ejemplo o demo funcional.
    [BLOCK: divider]
    ## 📝 Recomendaciones
    - Usar lenguaje claro, evitar jerga técnica innecesaria.
    - Incluir capturas de pantalla y ejemplos en los manuales.
    - Validar que todo enlace esté funcional y todo archivo sea accesible.
  ### [29_Plantilla de Registro de Proyecto]
    Este documento debe completarse al inicio de cada nuevo proyecto dentro de la fábrica. Permite establecer los datos clave, responsables, alcance y plan de trabajo.
    [BLOCK: divider]
    ## 🗂 Información General
    - Nombre del Proyecto:
    - Cliente o Unidad Interna:
    - Fecha de Inicio:
    - Fecha Estimada de Cierre:
    - Responsable Principal (humano):
    - Agentes IA involucrados:
    - Repositorio GitHub:
    - URL de Notion asociada:
    [BLOCK: divider]
    ## 🎯 Objetivo General
    [BLOCK: quote]
    [BLOCK: divider]
    ## 🔍 Alcance Inicial
    - Funcionalidades principales esperadas.
    - Restricciones tecnológicas (si las hubiera).
    - Público objetivo.
    [BLOCK: divider]
    ## 🧩 Recursos y Estructura
    - Herramientas a utilizar (Streamlit, Python, GitHub, etc.).
    - Requerimientos de datos o acceso a fuentes externas.
    - Integraciones previstas.
    [BLOCK: divider]
    ## 📅 Fases Tentativas
    1. Definición de requerimientos
    1. Diseño inicial y estructura
    1. Desarrollo asistido por IA
    1. Testing (manual + automático)
    1. Ajustes finales
    1. Documentación
    1. Entrega al cliente
  ### [30_Control de versiones]
    Este documento define las reglas, herramientas y convenciones para gestionar el control de versiones en todos los proyectos de la fábrica.
    [BLOCK: divider]
    ## ⚙️ Herramientas Utilizadas
    - Git
    - GitHub
    - Convenciones de ramas:
      - main
      - develop
      - feature/nombre
      - bugfix/nombre
      - hotfix/nombre
    [BLOCK: divider]
    ## 📌 Reglas Generales
    - Toda funcionalidad nueva se desarrolla en una rama 
    - Todo cambio requiere 
    - Todo commit debe tener mensaje claro y significativo.
    - Se usan etiquetas para marcar versiones (
    - Se documenta en el 
    [BLOCK: divider]
    ## 🔄 Flujo Simplificado
    [BLOCK: code]
    [BLOCK: divider]
    ## ✅ Buenas Prácticas
    - Realizar commits frecuentes.
    - Usar títulos y descripciones claras en los PRs.
    - Incluir capturas o referencias a tickets si aplica.
    - Mantener ramas actualizadas con 
  ### [31_Modelo financiero]
    Este documento establece la estructura comercial, pricing, análisis de costos y indicadores financieros que rigen la operación comercial de Antay Fábrica de Software. Define criterios de rentabilidad, métodos de cotización y control financiero de proyectos.
    [BLOCK: divider]
    ## 💰 Estructura de Pricing por Tipo de Proyecto
    ### 📱 
    - MVP Básico:
      - Hasta 50 productos
      - Diseño estándar responsive
      - Exportación PDF/HTML
      - Envío WhatsApp integrado
    - Catálogo Avanzado:
      - Hasta 200 productos
      - Diseño personalizado
      - Filtros avanzados por categoría
      - Panel admin básico
    - Solución Enterprise:
      - Productos ilimitados
      - Multi-usuario
      - Analytics integrado
      - API personalizada
    ### 🏢 
    - Consultoría y análisis:
    - Desarrollo custom:
    - Integración con APIs externas:
    - Diseño UX/UI personalizado:
    ### 🔧 
    - Soporte post-entrega:
    - Mantenimiento y actualizaciones:
    - Capacitación usuario final:
    - Migración de datos:
    [BLOCK: divider]
    ## 📊 Estructura de Costos y Márgenes
    ### 💡 
    - Herramientas IA (ChatGPT, etc.):
    - Hosting y dominio:
    - Herramientas dev (GitHub, Notion):
    - Tiempo líder proyecto:
    - Total costos directos:
    ### 🎯 
    - Margen bruto objetivo:
    - ROI mínimo por proyecto:
    - Utilidad neta objetivo:
    - Tiempo de recuperación:
    [BLOCK: divider]
    ## 📈 KPIs Financieros Clave
    ### 💼 
    - Average Deal Size (ADS):
    - Customer Acquisition Cost (CAC):
    - Sales Cycle Length:
    - Quote-to-Close Rate:
    ### 🔄 
    - Customer Lifetime Value (LTV):
    - LTV/CAC Ratio:
    - Monthly Recurring Revenue (MRR):
    - Churn Rate:
    ### ⚡ 
    - Time to Value:
    - Project Delivery Time:
    - Utilization Rate:
    - Gross Margin per Project:
    [BLOCK: divider]
    ## 🧮 Calculadora de Cotización
    ### 📋 
    1. Complejidad Funcional (1-5)
      - 1: Catálogo básico
      - 3: Funcionalidades medium
      - 5: Desarrollo completamente custom
    1. Diseño y UX (1-3)
      - 1: Templates estándar
      - 2: Personalización media
      - 3: Diseño único desde cero
    1. Integraciones (0-3)
      - 0: Sin integraciones
      - 1: WhatsApp/Email básico
      - 2: APIs externas simples
      - 3: Múltiples integraciones complejas
    ### 🔢 
    [BLOCK: code]
    [BLOCK: divider]
    ## 💳 Proceso de Facturación
    ### 🔄 
    - Proyecto <$1,500:
    - Proyecto >$1,500:
    - Servicios mensuales:
    - Consultoría:
    ### 📅 
    - Tiempo de pago:
    - Métodos aceptados:
    - Moneda base:
    - Política de reembolso:
    [BLOCK: divider]
    ## 📊 Dashboard Financiero
    ### 🎯 
    - Revenue generado
    - Proyectos cerrados
    - Pipeline value
    - Cash flow actual
    ### 📈 
    - MRR y crecimiento
    - Margen bruto acumulado
    - CAC y LTV
    - Proyección siguiente mes
    ### 🔍 
    - Análisis de rentabilidad por tipo proyecto
    - Review de pricing y ajustes
    - Forecast siguiente trimestre
    - Benchmarking competencia
    [BLOCK: divider]
    ## 🎯 Objetivos Financieros 2025
    ### 💰 
    - Q1:
    - Q2:
    - Q3:
    - Q4:
    ### 📊 
    - Revenue total:
    - Proyectos completados:
    - MRR al final del año:
    - Team size:
    [BLOCK: divider]
    Última actualización:
    Responsable:
    Revisión:
  [BLOCK: paragraph]
  [BLOCK: paragraph]
### [Proyectos (Hub)]
  🗂️ 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [BLOCK: quote]
  [BLOCK: divider]
  [BLOCK: table_of_contents]
  [BLOCK: divider]
  ## 📌 Proyectos
  [BLOCK: column_list]
    [BLOCK: column]
      [BLOCK: callout]
      [BLOCK: callout]
      [BLOCK: paragraph]
    [BLOCK: column]
      [BLOCK: callout]
      [BLOCK: callout]
    [BLOCK: column]
      [BLOCK: callout]
      [BLOCK: paragraph]
  [BLOCK: divider]
  ## 🔗 Navegación
  ← 
  ### [ReporteCobranzas]
    ### [FRD v0.2 — ReporteCobranzas (Antay)]
      # FRD (Functional Requirements Document: Documento de Requisitos Funcionales)
      Proyecto:
      Repositorio (código):
      Tag estable (freeze):
      Fecha: 2026-02-15 (America/Lima)
      Dueño del producto (Product Owner: dueño del requerimiento):
      Objetivo:
      [BLOCK: divider]
      ## 0) Glosario mínimo (para operar sin confusión)
      - SSOT (Single Source of Truth: “fuente única de la verdad”)
      - Vista filtrada
      - Tracking (trazabilidad)
      - Fresh Load (ciclo nuevo)
      - Gate (Quality Gate: “puerta de calidad”)
      - E2E (End-to-End: “de punta a punta”)
      - Rollback (reversión)
      [BLOCK: divider]
      ## 1) Problema a resolver (definición)
      Necesitamos 
      2) Cobranzas
      3) Cartera de clientes
      La app debe:
- Generar el Reporte General (cliente + documentos por pagar).
- Permitir enviar notificaciones.
- Mantener trazabilidad de envíos (qué cliente ya fue notificado y cuándo).
- Permitir reiniciar el ciclo o reiniciar solo la trazabilidad (sin recargar excels).
      [BLOCK: divider]
      ## 2) Alcance (Scope) v0.2
      ### 2.1 Incluye (IN)
      - Carga de 3 Excel y generación de Reporte General.
      - Tab “Notificaciones Email”: selección de clientes con correo, vista previa HTML, envío y reporte post-envío.
      - Trazabilidad de envío en Reporte General:
        - Estado Notificación (Email)
        - Último Envío (fecha/hora)
      - Persistencia de sesión (al día siguiente se ve lo mismo).
      - “Nuevo Ciclo” (cargar nuevos excels con advertencia) y “Nuevo Ciclo de Envíos” (reset de tracking).
      ### 2.2 No incluye (OUT)
      - Rediseñar lógica financiera de deuda/detracción.
      - Cambiar nombres de columnas clave (prohibido).
      - Cambiar motor de PDF / exportación (si existe).
      - Rehacer el envío WhatsApp desde cero (ya existe; solo documentar/estabilizar).
      [BLOCK: divider]
      ## 3) Reglas NO negociables (Anti-regresión)
      1. NO romper el flujo funcional existente.
      1. NO inventar nuevos procesos
      1. NO renombrar columnas clave
        - COD CLIENTE, EMPRESA, SALDO REAL, CORREO, MATCH_KEY (se mantienen tal cual).
      1. Mejoras AU/UX solamente
      1. Todo cambio debe pasar Gates
      [BLOCK: divider]
      ## 4) Modelo de datos (mínimo)
      ### 4.1 Entradas (Excel)
      - Archivo A: Cuentas por Cobrar
      - Archivo B: Cobranzas
      - Archivo C: Cartera de clientes
      ### 4.2 SSOT (datos maestros)
      - SSOT:
      - Vista filtrada:
      ### 4.3 Columnas de envío
      - CORREO
      - EMAIL_FINAL
        - La app trabaja por 
        - Pero 
          - 1 email por cliente
          - múltiples emails por cliente (ej: contabilidad@…, tesoreria@…)
          - un email compartido por varios clientes (ej: cortega28@hotmail.com)
      [BLOCK: quote]
      [BLOCK: divider]
      ## 5) Tracking (técnico) — trazabilidad de envíos (Email)
      Estas columnas NO vienen del Excel: se crean en la app.
      ### 5.1 Columnas tracking (2 obligatorias + 1 legacy opcional)
      - ESTADO_EMAIL (estado técnico)
        - Valores: PENDIENTE | ENVIADO | ERROR | SIN_CORREO
        - Inicial al cargar excels: PENDIENTE (si hay email) o SIN_CORREO (si no hay).
      - FECHA_ULTIMO_ENVIO (timestamp: fecha/hora real)
        - Inicial: vacío
        - Se llena solo si envío confirmado.
      - ESTADO_ENVIO_TEXTO (legacy opcional para compatibilidad; no se inicializa en Fresh Load)
        - Inicial: PENDIENTE
        - Después: “ENVIADO (HH:MM)” o “ERROR (…)”
      ### 5.2 Regla crítica: conteos por CLIENTE (no por email)
      - “Enviados Hoy” y “Pendientes” se miden por 
      - Motivo: un mismo EMAIL_FINAL puede representar varios clientes.
      [BLOCK: divider]
      ## 6) Flujo correcto del usuario (User Flow) — Email
      ### 6.1 Ciclo completo
      1. Usuario carga 3 Excel (Fresh Load = ciclo nuevo).
      1. Se genera Reporte General.
      1. Tracking inicial:
        - Estado Notificación = PENDIENTE (si aplica)
        - Último Envío = vacío
      1. Usuario va a “Notificaciones Email”, selecciona cliente(s), revisa vista previa HTML, envía.
      1. Si envío exitoso:
        - Se actualiza tracking en SSOT (
        - “Enviados Hoy” incrementa.
        - Se muestra “Reporte Post-Envío (obligatorio)”.
      1. La sesión se persiste (al día siguiente se ve igual).
      ### 6.2 Nuevo ciclo (reemplaza todo)
      - Botón: “📂 Cargar Nuevos Archivos”
      - Confirmación 2 pasos (no sorpresas).
      - Al confirmar:
        - Se elimina Reporte General anterior.
        - Tracking vuelve a estado inicial (nuevo ciclo).
      ### 6.3 Nuevo Ciclo de Envíos (solo reset tracking)
      - Ubicado en Configuración.
      - Botón (nombre recomendado): “Reiniciar Registro de Envíos”
(no “Reiniciar Sesión” para no confundir).
      - Acción:
        - ESTADO_EMAIL = PENDIENTE (si hay email)
        - FECHA_ULTIMO_ENVIO = vacío
        - ESTADO_ENVIO_TEXTO = PENDIENTE
      [BLOCK: divider]
      ## 7) UI/UX (solo lo necesario y sin inventar)
      ### 7.1 Reporte General
      - Vista Ejecutiva / Vista Completa.
      - Pantalla completa real (misma pestaña para preservar sesión).
        KPIs Ejecutivos (Dashboard Financiero)
        El Reporte General debe mostrar 4 KPIs principales en la parte superior:
        1. Total Saldo
          - Soles (S/)
          - Dólares ($)
          - Formato: S/ X,XXX.XX | $ X,XXX.XX
        1. Total Detracción
          - Formato: S/ X,XXX.XX
          - Nota: Las detracciones siempre se miden en Soles
        1. Total Saldo Real
          - Soles (S/)
          - Dólares ($)
          - Formato: S/ X,XXX.XX | $ X,XXX.XX
        1. Documentos
          - Cantidad en Soles
          - Cantidad en Dólares
          - Formato: XX (S/) | XX ($)
        Regla de cálculo:
      - NO agregar KPIs nuevos en Reporte General (si no están en FRD).
      - Maximizar tabla: experiencia fluida, sin romper filtros.
      ### 7.2 Tab “Notificaciones Email”
      KPIs (deben estar aquí, no en Reporte General):
      UIX-03: Reporte Post-Envío (OBLIGATORIO)
      Contenido mínimo del Reporte Post-Envío:
- Tabla con: cliente(s), email destino(s), cantidad docs, resultado (enviado/error/bloqueado TTL).
- Resumen con métricas: enviados, fallidos, bloqueados.
      [BLOCK: divider]
      ## 8) WhatsApp (documentar estado actual)
      - Estado: Implementado (según repositorio actual).
      - Nota: Enlace/imagen puede estar condicionado; mejora futura (no bloqueante v0.2).
      - Regla: WhatsApp usa la misma lógica de filtros compartidos (Reporte General → WhatsApp).
      [BLOCK: divider]
      ## 9) Criterios de aceptación (Acceptance Criteria)
    ### [Estado Actual — ReporteCobranzas]
      [BLOCK: divider]
      DOCOPS_ANCHOR_HANDOFF
      ## 1) Handoff Automático — ReporteCobranzas (para IA) — Único BLOQUE "VIVO"
      Uso:
      - SSOT (fuente única de verdad): Notion → FRD v0.2 + Estado Actual + Log del Proyecto + Backlog (tablero).
        - Versión Estable: v1.5.6 | Commit: 5f69e68 | Fecha: 2026-02-04 | Total Commits: 97
        - Próxima versión: v1.6.0-supabase-persistence (En desarrollo)
        - Estado: Producción Estable | Gates: Gate 0 PASS, Gate 3 PASS
        - Branch de trabajo: feature/supabase-integration
        - Último commit feature: 6c2cd11 (wip: SUPABASE-002 setup scripts parcial)
      - Repo (repositorio = donde vive el código): 
      - Versión estable actual (tag = etiqueta de versión segura): v1.5.6
      - Commit relevante (hash = código corto del cambio): 5f69e68
      - Gates (compuertas de calidad): Gate 0 PASS, Gate 3 Light PASS
        - Gate 0 (arranque/sintaxis = que corre sin error): ✅ PASS
        - Gate 3 (E2E = fin-a-fin): ✅ PASS (incluye reinicio de sesión)
      - Bugs abiertos (errores pendientes): 0
      - Trabajo completado reciente: 
        - SUPABASE-001 ✅ COMPLETADO (2026-02-05) - 4 tablas SQL creadas, cliente singleton
        - SUPABASE-002 🚧 EN PROGRESO (2026-02-05) - Scripts SQL listos, pendiente ejecución
      - Próximo paso exacto (tomado del Backlog en columna "Ready"): SUPABASE-002 — Migración inicial de datos
        🎯 ACCIÓN INMEDIATA: Ejecutar sql/EJECUTAR_EN_SUPABASE.sql en Supabase Dashboard
        📍 ESTADO: Scripts creados, pendiente ejecución manual en dashboard
        📁 ARCHIVOS LISTOS:
          - sql/EJECUTAR_EN_SUPABASE.sql (script consolidado para copiar/pegar)
          - scripts/setup_supabase_
        📋 DESPUÉS DE EJECUTAR SQL: Crear scripts de migración de datos desde Excel
      - Reglas NO negociables:
        - EMAIL_FINAL (correo normalizado) puede repetirse entre clientes.
        - Un cliente puede tener múltiples correos destino.
        - No cambiar columnas: COD CLIENTE, EMPRESA, SALDO REAL, CORREO, MATCH_KEY.
        - KPIs de email (indicadores) solo en la pestaña “Notificaciones Email”.
        - Todo término técnico debe incluir explicación (entre paréntesis).
        - No se cierra sesión sin DOCOPS-NOTION (actualizar Notion): 
      [BLOCK: divider]
      ## 2) Prompt fijo para Antigravity (OBLIGATORIO)
      ### Prompt de arranque (OBLIGATORIO)
      Antigravity: SSOT (fuente única) está en Notion. Abre esta página "Estado Actual — ReporteCobranzas" y lee la sección "Handoff Automático — para IA". [Ver: v1.5.6 | Commit: 5f69e68]
      Commit relevante (hash = código corto del cambio): 5f69e68
      No avances sin checklist Gate 3 (fin-a-fin) cuando aplique.
      ### Prompt de cierre (OBLIGATORIO)
      Antigravity: ejecuta DOCOPS-NOTION (actualización automática).
      Actualiza 
      Luego ejecuta SSOT READBACK (relectura de SSOT = releer Notion) y pega aquí el texto final del Handoff (tag/commit/gates/bugs/próximo paso).
      [BLOCK: divider]
      ## 3) Estado Actual — ReporteCobranzas (PARA HUMANOS)
      Nota:
      ### Estado general
      ✅ Tracking (trazabilidad = estado/fecha/conteo) y KPIs (indicadores) corregidos y validados.
      El trabajo se controla por Backlog (tablero Kanban = tablero por columnas).
      ### Calidad (Quality Gates = compuertas de calidad)
      - Gate 0 (arranque/sintaxis): ver Handoff (arriba)
      - Gate 1 (unit tests = pruebas unitarias): PENDIENTE/NA
      - Gate 3 (E2E = fin-a-fin + regresión): ver Handoff (arriba) + evidencia en Log del Proyecto (bitácora)
        - [2026-02-04] — RELEASE-v1.5.6 — Versión Estable (5f69e68) | Tag: v1.5.6 | Gate 3 PASS
        - [2026-01-06] — HOTFIX-HTML-001 — Fix HTML Preview (8785ab7) | Tag: v1.5.3-stable-html-preview-hotfix | Gate 3 Light PASS
      ### Alcance actual (Scope = lo que incluye esta versión)
      - ✅ Envío Email operativo
      - ✅ KPI “📧 Enviados Hoy” incrementa correctamente (persistente al reiniciar sesión)
      - ✅ KPI “⏳ Pendientes de Envío” resta correctamente (según enviados hoy)
      - ✅ Filtro “Ocultar ya enviados hoy” funciona tras cerrar y reabrir sesión
      - ✅ Trazabilidad en Reporte General: Estado Notificación (Email) + Último Envío
      - ✅ Tracking persistente al alternar vistas (Ejecutiva/Completa)
      - ✅ Reporte post-envío visible (UIX-03 = requisito de interfaz)
      - ✅ Pantalla completa del Reporte General
      - ✅ Reglas de ciclo nuevo / “no sorpresas”
      - ⏳ WhatsApp: documentar estado actual (implementado/parcial)
      - 🛠️ EN DESARROLLO: Persistencia con Supabase (v1.6.0)
        - Tablas: clientes, documentos, cobranzas, notificaciones
        - Historial permanente de notificaciones
        - Mantenimiento de clientes desde app
        - Reportes históricos
      ### Riesgos / puntos sensibles
      - Emails compartidos entre clientes (EMAIL_FINAL repetible) debe seguir funcionando.
      - No modificar nombres de columnas: COD CLIENTE, EMPRESA, SALDO REAL, CORREO, MATCH_KEY.
      - No inventar flujos: seguir FRD v0.2 (documento de requisitos).
      ### Control del siguiente paso
      El siguiente paso 
      Regla:
      [BLOCK: divider]
      ## 4) Estándar de cierre (OBLIGATORIO)
      El estándar DOCOPS-NOTION (Documentación Operativa en Notion = actualización automática) vive en:
      Documentación Oficial (SSOT) → Parte XI — DOCOPS-NOTION — Estándar de Cierre
      Aquí solo se aplica, no se duplica.
      - [2026-01-04 | 17:09] — Fix DOCOPS Recovery — v1.5.2-stable-email-kpi-fix — 0757108 — Gate 0 PASS, Gate 3 PASS (E2E)
      [BLOCK: divider]
      🟢 
      ### ROADMAP v5.0 (Prioridad Técnica)
      [BLOCK: to_do]
    ### [DATABASE: Backlog / Bugs — reporte_cobranzas]
    ### [Log del Proyecto — ReporteCobranzas]
      ### Log del Proyecto — ReporteCobranzas (Bitácora)
      Formato de registro (usar siempre):
      [Fecha AAAA-MM-DD | Hora] — Título corto del cambio
      - Objetivo (qué se buscaba)
      - Cambio aplicado (archivo/rama/tag si aplica)
      - Gate 0: PASS/FAIL
      - Gate 3: PASS/FAIL + evidencia (link/video)
      - Bugs abiertos (IDs o lista)
      - Próximo paso
      [BLOCK: divider]
      ## Ejemplo (plantilla)
      [2026-01-03 | 10:30] — Limpieza UI Tab Reporte General
      - Objetivo:
      - Cambio aplicado:
      - Gate 0:
      - Gate 3:
      - Bugs abiertos:
      - Próximo paso:
      [BLOCK: divider]
      ## Registros
      [2026-01-03 | 17:25] — Gate 3 E2E (End-to-End / Fin-a-Fin) — EJECUCIÓN COMPLETA
      - Objetivo:
      - Cambio aplicado:
      - Servidor (app corriendo local):
      - Gate 0 (compilación/arranque):
      - Gate 3 (E2E):
        - CA-1 (Fresh Load):
        - CA-2 (Persistencia entre tabs):
        - CA-3 (Cliente deuda 0):
        - CA-4 (Email compartido):
        - CA-5 (Post-envío):
      - Evidencia:
      - Bugs abiertos:
      - Próximo paso:
      [BLOCK: divider]
      [2026-01-03 | 22:35] — BUG-TRACKING-001 Fix Tracking + Gate 3 Regresión + Release v1.5.1
      - Objetivo:
      - Cambio aplicado:
        - Evitar overwrite de 
        - Refresh controlado post-envío + persistencia visual del “Resumen del Proceso”.
      - Gate 0:
      - Gate 3 (E2E + Regresión):
        - AC1/AC2/AC6 validados:
        - Regresión adicional con múltiples clientes:
      - Evidencia:
      - Bugs abiertos:
      - Release:
        - Commit:
        - Tag:
      - Próximo paso:
      [BLOCK: divider]
      [2026-01-03 | 22:45] — Cierre de sesión (servidor + artifacts)
      - Objetivo:
      - Acción:
      - Entregables:
      - Próximo paso:
      🤖 [Antigravity Auto-Test] Write permission verification.
      [BLOCK: divider]
      - [2026-01-04 | 14:46] — Fix BUG-EMAIL-COUNTERS-001 — Commit: 0757108 — Tag: v1.5.2-stable-email-kpi-fix — Gate 0 PASS — Gate 3 PASS (E2E)
      [BLOCK: paragraph]
      - [2026-01-05 | 08:01] — Automación DocOps — v1.5.2-stable-docops-final3 — f430cb7 — Gate 0 PASS, Gate 3 PASS (E2E) — Bugs: 0 — Next: QA-WA-TXT-001 WA-TXT-001 — Pruebas funcionales WhatsApp: envío de texto
      - [2026-01-05 | 08:13] — Automación DocOps — v1.5.2-stable-docops-final2 — f430cb7 — Gate 0 PASS, Gate 3 PASS (E2E) — Bugs: 0 — Next: QA-WA-TXT-001 WA-TXT-001 — Pruebas funcionales WhatsApp: envío de texto
      - [2026-01-05 | 08:43] — Automación DocOps — v1.5.2-stable-docops-debug02 — 038e452 — Gate 0 PASS, Gate 3 PASS (E2E) — Bugs: 0 — Next: QA-WA-TXT-001 WA-TXT-001 — Pruebas funcionales WhatsApp: envío de texto
      - [2026-01-05 | 09:06] — Automación DocOps — v1.5.2-stable-docops-debug03 — 12bc204 — Gate 0 PASS, Gate 3 PASS (E2E) — Bugs: 0 — Next: QA-E2E-001 — QA-E2E-001 — Pruebas E2E completas antes de publicar
      - [2026-01-05 | 09:14] — Automación DocOps — v1.5.2-stable-docops-debug04 — c30a39a — Gate 0 PASS, Gate 3 PASS (E2E) — Bugs: 0 — Next: QA-E2E-001 — QA-E2E-001 — Pruebas E2E completas antes de publicar
      - [2026-01-05 | 04:32] — Cierre de sesión + limpieza aplicada — fix(docops): update anchor id to target section header
      - [2026-01-06] - HOTFIX-HTML-001 -Fix HTML Preview 
      - [2026-01-06 | 20:54] — Automación DocOps — v1.6.0-antay-bridge-fix — b0cde19 — Gate 0 PASS, Gate 3 PASS (E2E) — Bugs: 0 — Next: QA-WA-TXT-001 WA-TXT-001 — Pruebas funcionales WhatsApp: envío de texto
      [BLOCK: divider]
      [2026-02-01] — RELEASE v1.5.6 — Tracking Integrity + Email Persistence
      - Objetivo:
      - Cambio aplicado:
        - Commit principal:
        - Último commit:
        - Tag:
        - Total commits en rama:
      - Características implementadas:
        - ✅ 
        - ✅ 
        - ✅ 
        - ✅ 
        - ✅ 
        - ✅ 
      - Gate 0 (compilación/arranque):
      - Gate 3 (E2E):
        - Email persistence validado post-restart
        - Tracking integrity confirmado
        - No regresiones detectadas
      - Bugs abiertos:
      - Commits relacionados:
        - 5f69e68
        - bd1cc47
        - df516da
        - 64a9978
        - b49bf8a
      - Estado:
      - Próximo paso:
      - Sincronización Notion:
      [BLOCK: divider]
      [2026-02-05] — ARQUITECTURA v1.6.0 — Migración a Supabase Persistence
      - Objetivo:
      - Problema resuelto:
        - Sin Supabase: Tracking solo en session_state (se pierde al recargar)
        - Con Supabase: Historial permanente de notificaciones y mantenimiento de clientes desde app
      - Cambios en arquitectura:
        - 4 tablas nuevas: 
        - FRD actualizado: Sección 13 - Persistencia con Supabase
        - Backlog actualizado: 7 tickets nuevos (SUPABASE-001 a SUPABASE-007)
      - Estado:
      - Gate 0:
      - Gate 3:
      - Tickets creados:
        - SUPABASE-001: Setup proyecto Supabase (Ready)
        - SUPABASE-002: Migración inicial de datos (Backlog)
        - SUPABASE-003: Integrar Supabase en 
        - SUPABASE-004: Persistir notificaciones (Backlog)
        - SUPABASE-005: Consulta de pendientes (Backlog)
        - SUPABASE-006: CRUD de clientes desde app (Backlog)
        - SUPABASE-007: Reportes históricos (Backlog)
      - Próximo paso:
      - Documentación:
      [BLOCK: divider]
      [2026-02-05] — SUPABASE-001 COMPLETADO — Setup proyecto Supabase
      - Objetivo:
      - Cambio aplicado:
        - Branch:
        - Commits:
          - 894afe2
          - d0e8fc6
        - Tag backup:
      - Archivos creados:
        - sql/01_create_clientes.sql
        - sql/02_create_documentos.sql
        - sql/03_create_cobranzas.sql
        - sql/04_create_notificaciones.sql
        - sql/00_setup_all.sql
        - utils/supabase_
        - .env.example
        - README_
        - requirements.txt
      - Arquitectura implementada:
        - 4 tablas SQL con índices y triggers
        - Cliente Singleton con lazy initialization
        - Fallback automático a session_state si Supabase no disponible
        - Modo híbrido: CLOUD (Supabase) o LOCAL (SQLite)
      - Gate 0 (compilación/arranque):
        - Import de SupabaseClient: OK
        - Import de funciones helper: OK
        - db_
      - Gate 3 (E2E):
      - Criterios de aceptación:
        - ✅ 4 tablas SQL creadas (clientes, documentos, cobranzas, notificaciones)
        - ✅ Código compila sin errores (Gate 0 PASS)
        - ✅ Fallback a session_state implementado
        - ✅ No se modificaron archivos existentes
      - Total líneas de código nuevo:
      - Bugs abiertos:
      - Estado:
      - Próximo paso:
      - Evidencia:
      ### [2026-02-08 | 00:55] — Fix Licencias (CP-BUG-022) + Sync Metodología
      - Objetivo: Corregir prioridad de licencias (Fecha > Cantidad) y sincronizar metodología Antay.
      - Cambio aplicado: auth.py (check_quota), main.py (get_user_plan_status), autay_sync_pro.py
      - Gate 0: PASS | Gate 1: PASS (9 tests) | Gate 3: PASS (Unitary Verification)
      - Próximo paso: Merge a dev y main.
    ### [Gate 3 Checklist E2E — ReporteCobranzas]
      ### Gate 3 — Checklist E2E (End-to-End = fin a fin)
      Versión evaluada (tag):
      Fecha de ejecución:
      Ejecutado por:
      ### CA-1: Nuevo ciclo (Fresh Load = carga nueva)
      - Pasos: cargar 3 excels
      - Esperado: tracking inicia en PENDIENTE / vacío; “Enviados Hoy” = 0
      - Resultado: PASS/FAIL
      - Evidencia: __
      ### CA-2: Filtros compartidos (Reporte General ↔ Notificaciones Email)
      - Pasos: filtrar Reporte General; ir a Notificaciones Email
      - Esperado: lista + preview respetan filtro
      - Resultado: PASS/FAIL
      - Evidencia: __
      ### CA-3: Cliente con deuda 0
      - Pasos: cliente con SALDO REAL=0
      - Esperado: no aparece para envío (salvo detracción pendiente)
      - Resultado: PASS/FAIL
      - Evidencia: __
      ### CA-4: Email compartido entre múltiples clientes
      - Pasos: varios clientes con mismo EMAIL_FINAL
      - Esperado: no se rompe selección; no queda “No options to select” indebidamente
      - Resultado: PASS/FAIL
      - Evidencia: __
      ### CA-5: Post-envío
      - Pasos: enviar email a cliente
      - Esperado:
        - Reporte post-envío visible en Tab Notificaciones Email
        - Se actualiza “Enviados Hoy / Pendientes” en Tab Notificaciones Email
        - Se actualiza trazabilidad en Reporte General (Estado + Último Envío)
      - Resultado: PASS/FAIL
      - Evidencia: __
      [BLOCK: paragraph]
    ### [🏛️ Arquitectura Técnica - Supabase v1.6]
      # Arquitectura Técnica - Persistencia Supabase v1.6.0
      Proyecto:
      Versión:
      Fecha:
      Owner:
      [BLOCK: divider]
      ## 1) Visión General
      ### Problema Actual (v1.5.6)
      [BLOCK: code]
      ### Solución con Supabase (v1.6.0)
      [BLOCK: code]
      [BLOCK: divider]
      ## 2) Modelo de Datos
      ### Diagrama ER
      [BLOCK: code]
      ### Tabla 1: clientes
      Tipo:
      Campos:
      - cod_cliente
      - empresa
      - email
      - telefono
      - responsable
      - activo
      - fecha_creacion
      - fecha_actualizacion
      Origen:
      Operaciones:
      - INSERT: Solo carga inicial o nuevo cliente desde app
      - UPDATE: Desde app (editar email, teléfono, etc.)
      - DELETE: NO (solo marcar activo=false)
      ### Tabla 2: documentos
      Tipo:
      Campos:
      - id
      - cod_cliente
      - nro_documento
      - tipo_documento
      - fecha_emision
      - fecha_vencimiento
      - monto_original
      - moneda
      - fecha_carga
      - UNIQUE(nro_documento, fecha_carga)
      Origen:
      Lógica:
      - Cada carga de Excel crea NUEVOS registros
      - Mismo documento puede tener múltiples entradas (histórico)
      - Para saldo actual: MAX(fecha_carga)
      ### Tabla 3: cobranzas
      Tipo:
      Campos:
      - id
      - nro_documento
      - tipo_aplicacion
      - monto_aplicado
      - fecha_aplicacion
      - fecha_carga
      - observaciones
      Origen:
      Cálculo Saldo Real:
      [BLOCK: code]
      ### Tabla 4: notificaciones
      Tipo:
      Campos:
      - id
      - cod_cliente
      - tipo
      - email_destino
      - telefono_destino
      - fecha_envio
      - estado
      - error_mensaje
      - documentos_incluidos
      - monto_total
      - usuario
      - metadata
      Origen:
      Consultas clave:
      1. ¿Ya notifiqué HOY a este cliente?
      [BLOCK: code]
      1. Pendientes de notificar HOY
      [BLOCK: code]
      [BLOCK: divider]
      ## 3) Arquitectura de la App
      ### Estructura de archivos (propuesta)
      [BLOCK: code]
      ### Módulo: utils/supabase_
      [BLOCK: code]
      ### Módulo: utils/db_
      [BLOCK: code]
      [BLOCK: divider]
      ## 4) Flujo de Operación
      ### Flujo 1: Carga Inicial (Setup)
      [BLOCK: code]
      ### Flujo 2: Operación Diaria
      [BLOCK: code]
      ### Flujo 3: Mantenimiento de Cliente
      [BLOCK: code]
      [BLOCK: divider]
  ### [Sistema de Punto de Venta - POS]
    # Antecedentes:
  ### [Antay Reports System]
    [BLOCK: paragraph]
    ### [FRD - Antay Report System]
      ## 📋 Resumen Ejecutivo
      Proyecto:
      Objetivo:
      Usuario Target:
      Tecnología:
      ## 🎯 Objetivos del Sistema
      ### Objetivos Primarios
      - Democratizar el acceso a datos de bd_antay
      - Eliminar dependencia de conocimientos SQL
      - Generar reportes ejecutivos en formatos estándar (Excel, PDF)
      - Interfaz intuitiva para usuarios no técnicos
      ### Objetivos Secundarios
      - Sistema offline/standalone
      - Sin dependencias de servicios externos
      - Instalación simple en cualquier PC de la red
      - Escalabilidad para futuras funcionalidades
      ## 📊 Especificaciones Funcionales
      ### Módulo de Autenticación
      - Login con credenciales de bd_antay
      - Validación contra SQL Server
      - Manejo seguro de credenciales
      - Timeout de sesión
      ### Módulo de Reportes de Ventas
      - Ventas diarias/semanales/mensuales
      - Comparativos temporales (año vs año)
      - Top productos por rotación
      - Análisis por categorías jerárquicas
      ### Módulo de Rentabilidad
      - Productos con margen bajo/negativo
      - Análisis de márgenes por proveedor
      - Rentabilidad por línea de productos
      - Identificación de loss leaders vs profit drivers
      ### Módulo de Exportación
      - Export a Excel con formato profesional
      - Generación de PDFs ejecutivos
      - Guardado automático con timestamp
      - Configuración de rutas de guardado
      ## 🛠️ Arquitectura Técnica
      ### Stack Tecnológico
      - Backend:
      - GUI Framework:
      - Base de Datos:
      - Análisis de Datos:
      - Visualización:
      - Export:
      ### Estructura del Proyecto
      [BLOCK: code]
      ## 📋 Metodología de Desarrollo
      ### Metodología Ágil - Scrum Adaptado
      - Sprints de 4 horas
      - MVP (Minimum Viable Product)
      - Iteraciones incrementales
      - Testing continuo
      ### Buenas Prácticas de Código
      - PEP 8
      - Docstrings
      - Type hints
      - Logging
      - Error handling
      - Validación de inputs
      ## 🔒 Consideraciones de Seguridad
      ### Manejo de Credenciales
      - No almacenamiento de contraseñas en texto plano
      - Hashing de credenciales en memoria
      - Timeout automático de sesiones
      - Validación de permisos contra bd_antay
      ### Acceso a Datos
      - Conexiones SQL con parámetros seguros
      - Prevención de SQL injection
      - Logs de auditoría de acceso
      - Manejo seguro de excepciones
      ## 📈 Plan de Sprints
      ### Sprint 1 (4 horas) - MVP
      - ✅ Setup del proyecto y estructura
      - ✅ Módulo de conexión a bd_antay
      - ✅ Interfaz de login básica
      - ✅ Reporte simple de ventas
      - ✅ Export básico a Excel
      ### Sprint 2 (4 horas) - Core Features
      - ✅ Interfaz principal completa
      - ✅ Módulo de reportes de rentabilidad
      - ✅ Visualizaciones básicas
      - ✅ Manejo de errores
      ### Sprint 3 (4 horas) - Advanced Features
      - ✅ Dashboards interactivos
      - ✅ Reportes comparativos
      - ✅ Export a PDF
      - ✅ Configuraciones de usuario
      ### Sprint 4 (2 horas) - Polish & Deploy
      - ✅ Interfaz profesional final
      - ✅ Testing completo
      - ✅ Documentación de usuario
      - ✅ Instalador/distribuible
      ## 🎨 Diseño de Interface
      ### Principios de UX/UI
      - Simplicidad:
      - Intuitividad:
      - Consistencia:
      - Feedback:
      - Accesibilidad:
    ### [Backlog/Bugs_Antay Report System]
    [BLOCK: paragraph]
    [BLOCK: paragraph]
  ### [Sistema de Pricing Inteligente con Claude MCP]
    ## 📋 INFORMACIÓN DEL PROYECTO
    Nombre:
    Objetivo:
    Fecha Inicio:
    Estado:
    Responsables:
    [BLOCK: divider]
    ## 🎯 RESUMEN EJECUTIVO
    Situación Actual:
    - Tienda Antay percibida como "cara" vs competencia
    - Productos exclusivos + commodities
    - Oportunidad: Fiestas patronales Julio 2025
    Estrategia:
    - Pricing híbrido: commodities competitivos + premium margen alto
    - Automatización con Claude + MCP
    - Interfaces simples para el equipo
    Resultados Esperados:
    - Margen total +25-35% en temporada alta
    - Cambio percepción "precios altos"
    - Optimización automática continua
    [BLOCK: divider]
    ## 📊 MÉTRICAS OBJETIVO
    - Margen Julio 2025:
    - Ticket Promedio:
    - Tráfico:
    - Quejas precio:
    [BLOCK: divider]
    ## 🔗 PÁGINAS DEL PROYECTO
    📍 
    - 🎯 Estrategias de Pricing
    - ⚙️ Configuración Técnica
    - 📋 Plan de Implementación
    - 📊 Seguimiento y Métricas
    - 🗓️ Log de Progreso
    [BLOCK: divider]
    ## 🚀 COMENZAR CONFIGURACIÓN
    ESTADO:
    PRÓXIMO PASO:
    ### [🎯 Estrategias de Pricing]
      ## 1. ESTRATEGIA "MARGEN POR CANASTA"
      ### Concepto Base:
      - Loss Leaders:
      - Profit Drivers:
      - Cross-selling forzado:
      ### Productos Loss Leaders (Sacrificio):
      - Agua Cielo: Precio agresivo para percepción
      - Coca-Cola familiar: 5% más barato que competencia
      - Cerveza Pilsen: Igualar competencia exacto
      - Galletas básicas: Precio competitivo
      ### Productos Profit Drivers (Compensación):
      - Licores premium: +15-20% margen
      - Snacks gourmet: +15% precio
      - Energizantes: +10% en fiestas
      - Cigarrillos: +10% margen
      - Preservativos: +25% (demanda inelástica)
      [BLOCK: divider]
      ## 2. ESTRATEGIA FIESTAS PATRONALES JULIO 2025
      ### Productos "Imagen" (30% inventario):
      [BLOCK: code]
      ### Productos "Margen" (70% inventario):
      [BLOCK: code]
      ### Calendario de Ejecución:
      - Semana 1:
      - Semana 2-3:
      - Semana 4:
      [BLOCK: divider]
      ## 3. ESTRATEGIAS PROACTIVAS
      ### Calendar-Based Pricing:
      - Enero:
      - Febrero:
      - Marzo:
      ### Competitive Intelligence:
      - Lunes 6 AM:
      - Ajustes dinámicos:
      - Pricing elasticidad:
      ### Técnicas Anti-Cherry Picking:
      - Límites cantidad:
      - Bundling forzado:
      - Ubicación estratégica:
    ### [⚙️ Configuración Técnica MCP]
      ## 🔌 REQUISITOS BASE DE DATOS
      ### Conexión SQL Server:
      [BLOCK: code]
      ### Tablas Críticas:
      [BLOCK: code]
      ### Campos Obligatorios:
      [BLOCK: code]
      [BLOCK: divider]
      ## 🎛️ REGLAS DE NEGOCIO ANTAY
      [BLOCK: code]
      [BLOCK: divider]
      ## 🏪 DATOS COMPETENCIA
      ### Competidores Principales:
      [BLOCK: code]
      ### Estructura Datos Competencia:
      [BLOCK: code]
      [BLOCK: divider]
      ## 🔒 CONFIGURACIÓN SEGURIDAD
      ### Permisos MCP:
      [BLOCK: code]
      ### Plan Backup:
      [BLOCK: code]
      [BLOCK: divider]
      ## 📡 ARQUITECTURA SISTEMA
      [BLOCK: code]
    ### [📋 Plan de Implementación]
      ## 🚀 CRONOGRAMA GENERAL
      ### FASE 1: CONFIGURACIÓN TÉCNICA (Días 1-3)
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      ### FASE 2: CONFIGURACIÓN NEGOCIO (Días 4-7)
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      ### FASE 3: DESARROLLO INTERFACES (Días 8-14)
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      ### FASE 4: TESTING (Días 15-17)
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      ### FASE 5: EJECUCIÓN JULIO (Días 18+)
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: divider]
      ## 📱 INTERFACES DE USUARIO
      ### ROL EMPLEADO:
      [BLOCK: code]
      ### ROL SUPERVISOR:
      [BLOCK: code]
      ### ROL GERENTE:
      [BLOCK: code]
      [BLOCK: divider]
      ## 🔄 FLUJOS OPERATIVOS
      ### FLUJO REACTIVO (Queja Cliente):
      1. Empleado
      1. Sistema
      1. Claude
      1. WhatsApp
      1. Supervisor
      1. Sistema
      1. Equipo
      ### FLUJO PROACTIVO (Lunes 6 AM):
      1. Claude
      1. Sistema
      1. Claude
      1. Sistema
      1. Gerencia
      [BLOCK: divider]
      ## ⚠️ PLAN DE CONTINGENCIA
      ### ROLLBACK AUTOMÁTICO:
      [BLOCK: code]
      ### VALIDACIONES CRÍTICAS:
      - Margen nunca < 15%
      - Cambio precio nunca > 30%
      - Máximo 200 productos por lote
      - Backup antes de cambios masivos
      ### CONTACTOS EMERGENCIA:
      - Técnico:
      - Negocio:
      - Sistema:
    ### [📊 Seguimiento y Métricas]
      # 📊 SEGUIMIENTO Y MÉTRICAS
      ## 🎯 KPIs PRINCIPALES
      ### MÉTRICAS NEGOCIO:
      [BLOCK: code]
      ### MÉTRICAS OPERATIVAS:
      [BLOCK: code]
      [BLOCK: divider]
      ## 📋 DASHBOARD EJECUTIVO
      ### RESUMEN DIARIO:
      [BLOCK: code]
      ### ALERTAS AUTOMÁTICAS:
      [BLOCK: code]
      [BLOCK: divider]
      ## 📊 REPORTES SEMANALES
      ### REPORTE COMPETENCIA:
      [BLOCK: code]
      ### REPORTE ELASTICIDAD:
      [BLOCK: code]
      [BLOCK: divider]
      ## 📅 SEGUIMIENTO TEMPORAL
      ### TRACKING FIESTAS PATRONALES:
      [BLOCK: code]
      ### COMPARATIVO ANUAL:
      [BLOCK: code]
      [BLOCK: divider]
      ## 🔄 OPTIMIZACIÓN CONTINUA
      ### AJUSTES AUTOMÁTICOS:
      [BLOCK: code]
      ### MACHINE LEARNING:
      [BLOCK: code]
    ### [🗓️ Log de Progreso]
      ## 🟡 ESTADO ACTUAL: CONFIGURACIÓN INICIAL
      Fecha Inicio:
      Última Actualización:
      Progreso General:
      [BLOCK: divider]
      ## ✅ TAREAS COMPLETADAS
      ### 📋 PLANIFICACIÓN Y DISEÑO:
      - ✅ 
      - ✅ 
      - ✅ 
      - ✅ 
      - ✅ 
      - ✅ 
      - ✅ 
      ### 🎨 DOCUMENTACIÓN:
      - ✅ 
      - ✅ 
      - ✅ 
      - ✅ 
      [BLOCK: divider]
      ## ⏳ PRÓXIMAS TAREAS (Esta Semana)
      ### FASE 1: CONFIGURACIÓN TÉCNICA
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      ### FASE 2: CONFIGURACIÓN NEGOCIO
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: to_do]
      [BLOCK: divider]
      ## 📝 DECISIONES TOMADAS
      ### ESTRATEGIA PRINCIPAL:
      - Enfoque:
      - Productos imagen:
      - Productos premium:
      - Automatización:
      ### ARQUITECTURA TÉCNICA:
      - Backend:
      - Empleados:
      - Supervisor:
      - Gerente:
      ### CRONOGRAMA:
      - Configuración:
      - Desarrollo:
      - Testing:
      - Ejecución:
      [BLOCK: divider]
      ## 💬 CONVERSACIONES IMPORTANTES
      ### JULI0 25, 2025 - SESIÓN INICIAL:
      - Tema:
      - Decisiones:
      - Próximo paso:
      - Pendiente:
      [BLOCK: divider]
      ## ⚠️ RIESGOS Y MITIGACIONES
      ### RIESGOS IDENTIFICADOS:
      - Técnico:
      - Negocio:
      - Operativo:
      - Temporal:
      ### PLAN CONTINGENCIA:
      - Rollback automático
      - Validaciones críticas
      - Soporte técnico
      - Plan B manual
      [BLOCK: divider]
      ## 🎯 OBJETIVOS INMEDIATOS
      ### ESTA SEMANA:
      1. Completar configuración
      1. Mapear productos
      1. Definir precios
      1. Preparar plan
      ### PRÓXIMAS 2 SEMANAS:
      1. Desarrollar interfaces
      1. Testing completo
      1. Capacitar equipo
      1. Ejecutar plan
      [BLOCK: divider]
      ## 📞 CONTACTOS Y RECURSOS
      ### EQUIPO PROYECTO:
      - Responsable Técnico:
      - Responsable Negocio:
      - Usuario Final:
      - Stakeholder:
      ### RECURSOS NECESARIOS:
      - Acceso BD:
      - Datos competencia:
      - Hardware:
      - Tiempo:
      [BLOCK: divider]
      PRÓXIMA ACTUALIZACIÓN:
      ESTADO:
### [Estándares de Branching GitFlow - Antay]
  ##  Estándares de Branching (Ramas) - GitFlow
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [BLOCK: quote]
  [BLOCK: divider]
  [BLOCK: table_of_contents]
  [BLOCK: divider]
  ## 🎯 Regla permanente de la metodología Antay
  [BLOCK: callout]
    NO SE PREGUNTA
  [BLOCK: divider]
  ## 🏭 Metodología adoptada: GitFlow simplificado
  [BLOCK: callout]
    Usado por:
  [BLOCK: divider]
  ## 📊 Estructura de ramas (Branches)
  ### 🔵 Ramas permanentes (siempre existen)
  [BLOCK: heading_4]
  - Propósito:
  - Características:
    - ✅ SIEMPRE funcional y estable
    - ✅ Cada commit es una versión publicable
    - ✅ Protegida contra push directo
    - ✅ Solo recibe merges desde 
    - ✅ Cada merge = nuevo release/versión
  - Analogía:
  - Reglas:
    - ❌ NUNCA hacer commit directamente a 
    - ❌ NUNCA hacer push --force a 
    - ✅ Solo merge desde 
    - ✅ Tag cada merge con versión (v1.5.0, v1.5.1, etc.)
  [BLOCK: toggle]
    [BLOCK: code]
  [BLOCK: divider]
  [BLOCK: heading_4]
  - Propósito:
  - Características:
    - ✅ Integra trabajo de múltiples features
    - ✅ Debe ser estable pero permite bugs menores
    - ✅ Base para crear features nuevas
    - ✅ Testing continuo aquí
  - Analogía:
  - Reglas:
    - ✅ Aceptable hacer commits directos para ajustes pequeños
    - ✅ Features se mergean aquí primero
    - ✅ Cuando está estable y lista → merge a 
    - ❌ No debe tener bugs críticos
  [BLOCK: toggle]
    [BLOCK: code]
  [BLOCK: divider]
  ### 🟢 Ramas temporales (se crean y eliminan)
  [BLOCK: heading_4]
  - Propósito:
  [BLOCK: toggle]
    [BLOCK: code]
  [BLOCK: toggle]
    [BLOCK: code]
  - Reglas:
    - ✅ Siempre crear desde 
    - ✅ Nombre descriptivo con ticket ID
    - ✅ Una feature = una funcionalidad
    - ✅ Mergear a 
    - ✅ Eliminar después del merge
  [BLOCK: divider]
  [BLOCK: heading_4]
  - Propósito:
  [BLOCK: toggle]
    [BLOCK: code]
  - Ciclo:
  [BLOCK: divider]
  [BLOCK: heading_4]
  - Propósito:
  - Diferencia con fix:
  [BLOCK: toggle]
    [BLOCK: code]
  [BLOCK: toggle]
    [BLOCK: code]
  - Reglas:
    - ✅ Solo para emergencias (app rota, fuga de datos, etc.)
    - ✅ Testing mínimo pero suficiente
    - ✅ Mergear a 
    - ✅ Incrementa versión patch (v1.5.0 → v1.5.1)
  [BLOCK: divider]
  ## 📊 Diagrama de flujo GitFlow
  [BLOCK: toggle]
    [BLOCK: code]
  [BLOCK: divider]
  ## 🛡️ Protección de ramas
  ### Configuración en GitHub
  Para 
  - ✅ Require pull request reviews (opcional pero recomendado)
  - ✅ Require status checks (tests deben pasar)
  - ✅ Prohibir push directo
  - ✅ Prohibir force push
  - ✅ Prohibir eliminación
  Para 
  - ✅ Prohibir force push
  - ✅ Prohibir eliminación
  [BLOCK: divider]
  ## 📝 Convenciones de commits
  [BLOCK: callout]
  [BLOCK: toggle]
    [BLOCK: code]
  ### Tipos
  - feat:
  - fix:
  - hotfix:
  - docs:
  - style:
  - refactor:
  - test:
  - chore:
  [BLOCK: toggle]
    [BLOCK: code]
  [BLOCK: divider]
  ## 🔄 Respuesta a tu pregunta 3
  Pregunta:
  [BLOCK: callout]
    ### Respuesta: SÍ, correcto
  [BLOCK: toggle]
    [BLOCK: code]
  Conclusión:
  1. ✅ En local tienes 
  1. ✅ Ambas se suben (push) a GitHub
  1. ✅ Streamlit Cloud está configurado para leer solo 
  1. ✅ Cuando haces merge de 
  [BLOCK: divider]
  ## 🎯 Proceso completo de deploy (publicación)
  [BLOCK: toggle]
    [BLOCK: code]
  [BLOCK: divider]
  ## ⚠️ Errores comunes (y cómo evitarlos)
  ### Error 1: commits directos a main
  [BLOCK: toggle]
    [BLOCK: code]
  ### Error 2: olvidar eliminar feature branches
  [BLOCK: toggle]
    [BLOCK: code]
  ### Error 3: mergear sin testing
  [BLOCK: toggle]
    [BLOCK: code]
  [BLOCK: divider]
  ## 📚 Referencias internacionales
  - GitFlow Original: 
  - GitHub Flow: 
### [Guías y manuales de desarrollo]
  📕 
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [BLOCK: quote]
  [BLOCK: divider]
  [BLOCK: table_of_contents]
  [BLOCK: divider]
  ## 🔗 Recursos (bookmarks)
  [BLOCK: toggle]
    [BLOCK: bookmark]
    [BLOCK: bookmark]
    [BLOCK: bookmark]
    [BLOCK: bookmark]
    [BLOCK: bookmark]
  [BLOCK: divider]
  ## 🔗 Navegación
  ← 
### [Playbook de Marketing - Antay]
  [BLOCK: callout]
  [BLOCK: divider]
  [BLOCK: table_of_contents]
  [BLOCK: divider]
  # 1. Narrativa de Marca
  [BLOCK: callout]
  ## 1.1 Nuestro WHY (Simon Sinek)
  [BLOCK: quote]
  ## 1.2 Framework StoryBrand (Donald Miller)
  Aplicamos el SB7 Framework para posicionar nuestra comunicacion:
  ### El Heroe: El comerciante peruano
  No somos nosotros los protagonistas. El heroe de la historia es el dueno de bodega, la emprendedora de Instagram, el distribuidor mayorista. Ellos tienen productos increibles pero herramientas limitadas para mostrarlos al mundo.
  ### El Problema
  - Externo: 
  - Interno: 
  - Filosofico: 
  ### El Guia: Antay
  Antay se posiciona como el guia que entiende el dolor del emprendedor y tiene las herramientas para resolverlo. Mostramos empatia y autoridad.
  - Empatia: 
  - Autoridad: 
  ### El Plan (3 pasos simples)
  1. Sube tu lista de productos (Excel o Google Sheets)
  1. Personaliza tu catalogo (logo, colores, productos)
  1. Descarga tu PDF profesional y compartelo con tus clientes
  ### El Llamado a la Accion (CTA)
  - CTA Directo: 
  - CTA Transicional: 
  ### El Exito
  Pintar la transformacion del heroe:
  - "De enviar fotos borrosas por WhatsApp a compartir un catalogo PDF profesional con tu marca."
  - "Tus clientes te ven como un negocio serio y organizado."
  - "Vendes mas porque tus productos se ven como merecen."
  ### El Fracaso (lo que pasa si NO actua)
  - Sigue enviando listas de precios en texto plano que nadie lee.
  - Sus competidores con mejor presentacion le ganan clientes.
  - Pierde oportunidades de venta por no verse profesional.
  [BLOCK: divider]
  ## 1.3 Propuesta Unica de Valor (UVP)
  [BLOCK: callout]
  ### UVP de Antay (Marca Madre)
  [BLOCK: quote]
  ### UVP de CatalogPro (Producto)
  [BLOCK: quote]
  ### Stack de Valor Hormozi ($100M Offers)
  Para que la oferta sea irresistible, el valor percibido debe ser >> precio:
  - Dream Outcome: 
  - Perceived Likelihood: 
  - Time Delay: 
  - Effort & Sacrifice: 
  [BLOCK: divider]
  # 2. Segmento de Mercado y Buyer Personas
  [BLOCK: callout]
  ## 2.1 Analisis de Mercado
  ### Oceano Rojo (competencia actual)
  - Canva: Herramienta generalista de diseno (no especializada en catalogos comerciales)
  - Disenadores freelance: Caros (S/ 200-500 por catalogo), lentos (3-7 dias)
  - Catalogo manual: El comerciante arma su propia lista en Word/Excel (poco profesional)
  - WhatsApp Business Catalogo: Limitado, no exporta PDF, no maneja inventario
  ### Oceano Azul (nuestra oportunidad)
  Segun Blue Ocean Strategy, nuestra diferenciacion es:
  - Eliminar: 
  - Reducir: 
  - Incrementar: 
  - Crear: 
  ## 2.2 Segmentacion
  - Mercado Total (TAM): 
  - Mercado Alcanzable (SAM): 
  - Mercado Objetivo (SOM): 
  - Nicho Inicial: 
  ## 2.3 Buyer Personas
  ### Persona 1: "Don Carlos" — El Bodeguero Tradicional
  - Edad: 
  - Negocio: 
  - Ubicacion: 
  - Tecnologia: 
  - Dolor principal: 
  - Motivacion: 
  - Objecion: 
  - Frase que lo define: 
  - Canal de captacion: 
  - Trigger de compra: 
  ### Persona 2: "Maria Emprendedora" — La Vendedora Digital
  - Edad: 
  - Negocio: 
  - Ubicacion: 
  - Tecnologia: 
  - Dolor principal: 
  - Motivacion: 
  - Objecion: 
  - Frase que la define: 
  - Canal de captacion: 
  - Trigger de compra: 
  ### Persona 3: "Ingeniero Luis" — El Distribuidor
  - Edad: 
  - Negocio: 
  - Ubicacion: 
  - Tecnologia: 
  - Dolor principal: 
  - Motivacion: 
  - Objecion: 
### Pol?tica Global de Ejecuci?n (Aplicable a todos los proyectos)
Vigente desde 2026-02-15 18:53. Esta pol?tica es obligatoria para todos los equipos y agentes de Antay.
### 1) Modelo de desarrollo: ramas paralelas multi-agente
1. Main protegido. Solo se integra por Pull Request con quality gates obligatorios.
1. 1 ticket = 1 rama de integraci?n. Cada agente trabaja en su subrama especializada (UI, DB, QA, DocOps, etc.).
1. Integraci?n por lotes en rama del ticket y merge final a main solo con evidencia de pruebas y no regresi?n.
1. Todo cambio debe mantener trazabilidad: Ticket ID, rama, commit, evidencias y estado de gates.
### 2) Autonom?a operativa del agente de c?digo (default)
1. El agente ejecuta de forma aut?noma el an?lisis, implementaci?n, pruebas y documentaci?n t?cnica sin pedir confirmaciones innecesarias.
1. Solo se solicita confirmaci?n cuando exista ambig?edad real de regla de negocio, alcance o impacto no definido por el FRD/SSOT.
1. Si la regla de negocio est? clara, el agente debe proceder end-to-end y entregar resultado verificable.
1. Este est?ndar prioriza velocidad, calidad y responsabilidad t?cnica de clase mundial.
