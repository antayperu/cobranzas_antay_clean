# ReporteCobranzas — Instrucciones para Claude Code

## Comportamiento de inicio
- NO explorar el proyecto automáticamente al iniciar sesión
- NO acceder a rutas de red (\\QA\antay-cobranza) sin instrucción explícita
- Responder inmediatamente al saludo antes de cualquier exploración
- Extended thinking: DESACTIVADO por defecto

---

**Proyecto:** ReporteCobranzas v1.7.3 | Antay Fábrica de Software
**Product Owner:** Camilo Ortega F.R.
**Rama activa:** `dev` | **Tag producción:** `v2.1.0` (162/162 tests)
**FRD maestro:** `docs/FRD_REPORTECOBRANZAS_v2.0.md`

---

## Política de comunicación (NO NEGOCIABLE)

El Product Owner **no es programador**. Toda comunicación se rige por estas reglas:

1. **Idioma:** Siempre en español, claro y directo. Sin tecnicismos innecesarios.
2. **Términos de industria en inglés** (bug, feature, fix, deploy, merge, etc.): incluir siempre la pronunciación aproximada en español entre paréntesis y su significado. Ejemplo:
   - *bug* (pronunciado: "bag") — error en el código
   - *feature* (pronunciado: "fícher") — nueva funcionalidad
   - *fix* (pronunciado: "fics") — corrección de un error
   - *deploy* (pronunciado: "diplói") — publicar/instalar la app
   - *merge* (pronunciado: "mersh") — unir ramas de código
   - *commit* (pronunciado: "comit") — guardar cambios en el historial
3. **Tono:** Como un profesor que explica a su alumno — contexto primero, luego la acción. Priorizar por qué importa antes de explicar qué se hizo.
4. **Mantener esta guía** hasta que el PO indique explícitamente que ya no la necesita.

---

## Estándar de calidad — Antay Class Worldwide (NO NEGOCIABLE)

En Antay Fábrica de Software desarrollamos aplicaciones de **clase mundial**, al mismo nivel de productos como Google Workspace, Netflix, Stripe, Linear y Notion. Esto no es aspiracional — es la política de trabajo.

Esto significa:

1. **Experiencia de usuario premium:** Cada pantalla, botón y mensaje debe sentirse como un producto de Fortune 500. Sin interfaces descuidadas, sin textos de error técnicos, sin layouts improvisados.
2. **Accesibilidad obligatoria (WCAG AA):** Contraste mínimo 4.5:1, botones con touch target de 44px, nunca información transmitida solo por color.
3. **Performance primero:** Spinners en toda operación >300ms, paginación en tablas grandes, cache para datos que no cambian.
4. **Arquitectura escalable:** Código limpio, responsabilidades únicas por función, sin lógica de negocio en archivos de UI.
5. **Cero tolerancia a deuda técnica visible:** Tracebacks crudos al usuario = inaceptable. Errores sin mensaje descriptivo = inaceptable. Datos sin contexto de moneda/unidad = inaceptable.
6. **Design System como ley:** La paleta Antay, la tipografía Manrope + IBM Plex Sans y los componentes definidos en `utils/ui/styles.py` son el estándar. No se improvisan estilos fuera del sistema.
7. **Cada entrega es una demo al cliente:** Antes de declarar cualquier cambio "done", debe verse y comportarse como si lo fuera a ver el CEO de la empresa.

---

## Stack

- Python 3.11 + Streamlit + Supabase (PostgreSQL cloud) + pandas/openpyxl
- WhatsApp Web: `whatsapp_sender.py` con Selenium + ChromeDriver
- Email: smtplib | Tests: pytest | Env vars: `.env` / `.env.staging`

---
## Skills activos — SIEMPRE aplicar

Estos skills están instalados globalmente y deben usarse en cada tarea
según el contexto. No es necesario invocarlos manualmente — Claude los
activa automáticamente, pero se listan aquí como política obligatoria.

### 🎨 frontend-design
**Cuándo:** En TODO componente visual, pantalla, sidebar, tabla o UI
**Regla:** Antes de codificar cualquier elemento visual, definir
dirección estética. Respetar siempre el Design System Antay:
paleta COLORS de `utils/ui/styles.py`, tipografía Manrope + IBM Plex Sans.
Nunca romper el sistema de diseño por decisiones del skill.

### 🏗️ feature-dev
**Cuándo:** En TODA feature nueva o cambio de arquitectura significativo
**Regla:** Seguir las 7 fases obligatorias: requerimientos → exploración
→ arquitectura → implementación → testing → revisión → documentación.
Nunca saltar directo a codificar sin explorar el código existente primero.

### ✅ code-review
**Cuándo:** Al terminar CADA tarea antes de declararla "done"
**Regla:** Revisar calidad, legibilidad y principios SOLID.
Complementa los Quality Gates existentes (Gate 0 y Gate 1).
Invocar explícitamente con: `usa code-review para revisar los cambios`

### 🔒 security-guidance
**Cuándo:** Antes de escribir código que maneje archivos, datos del
usuario, conexiones a Supabase o cualquier input externo
**Regla:** Validar archivos Excel subidos por el usuario, sanitizar
inputs, no exponer credenciales en logs. Especialmente crítico en
`utils/db_manager.py` y `utils/processing.py`.

### 📄 document-skills
**Cuándo:** Para generar informes gerenciales en PDF (RC-FEAT-039)
y cualquier documento formal del sistema
**Regla:** Formato A4 profesional, márgenes correctos, logo
"Cobranzas Antay", número de página y fecha en pie de página.
Tipografía ejecutiva. Tablas financieras correctamente alineadas.
Los valores monetarios siempre con símbolo de moneda (S/ o $).

## Reglas no negociables

1. **Supabase cloud-only.** NUNCA implementar fallback SQLite ni session_state como BD.
2. **SSOT sagrado.** `df_final` solo se modifica por lógica de tracking oficial. `df_filtered` es la vista derivada para UI.
3. **No mezclar** `df_final` y `df_filtered` — son entidades separadas.
4. **Columnas prohibidas** (nunca renombrar): `CodCliente`, `Empresa`, `SaldoReal`, `Correo`, `MATCH_KEY`, `ESTADO_EMAIL`, `FECHA_ULTIMO_ENVIO`, `ESTADO_WHATSAPP`
5. **No declarar "done"** sin evidencia E2E de Gate 3 (smoke manual en staging).
6. **No push a main** sin staging verde y aprobación explícita del PO.
7. **No enviar mensajes reales** en ambiente QA/staging.
8. Toda mejora UI/UX: usar `load_css()` desde `utils/ui/styles.py`. NUNCA inyectar CSS en otro lugar.

---

## Arquitectura de datos

```
df_final       → SSOT en memoria. NUNCA modificar desde UI.
df_filtered    → Vista derivada según filtros activos.
cycle_id       → Formato: CIC-YYYYMMDD-HHMM
ESTADO_EMAIL   → PENDIENTE / ENVIADO / ERROR / SIN_CORREO
ESTADO_WHATSAPP→ PENDIENTE / ENVIADO / ERROR / SIN_TELEFONO
```

KPIs de Enviados/Pendientes: siempre por `CodCliente` único, nunca por EMAIL_FINAL.

---

## Estructura de archivos clave

```
app.py                          ← entry point (load_css + enforce_cloud_only)
utils/
  db_manager.py                 ← TODAS las operaciones Supabase
  supabase_client.py            ← cliente singleton
  processing.py                 ← Excel → df_final
  session.py                    ← session_state + enforce_cloud_only_policy()
  whatsapp_sender.py            ← Selenium WA Web
  ui/
    styles.py                   ← COLORS dict + load_css()
    sidebar.py                  ← sidebar, banner ambiente, uploader, ciclos
    tabs/
      whatsapp.py               ← Tab WhatsApp + CRM post-envío
      email_notifications.py   ← Tab Email
      crm_gestiones.py         ← gestiones, acuerdos, bandeja pendientes
      clientes_premium.py      ← CRUD clientes Supabase
      config_tab.py            ← configuración + plantillas WA
docs/
  FRD_REPORTECOBRANZAS_v2.0.md ← FRD maestro
  backlog_priorizado.md        ← sprint activo
  TICKETS_ANTAY.md             ← catálogo tickets
tests/                         ← pytest (141 tests críticos)
sql/                           ← scripts DDL Supabase
```

---

## Gitflow Antay (obligatorio)

```bash
# Feature
git checkout dev && git pull origin dev
git checkout -b feature/RC-FEAT-XXX-nombre
# [desarrollar + commits atómicos]
git checkout dev && git merge feature/RC-FEAT-XXX-nombre --no-ff
# [Gate 3 staging] → si verde:
git checkout main && git merge dev --no-ff
git push origin main && git push origin dev
git branch -d feature/RC-FEAT-XXX-nombre

# Hotfix (desde main, merge a main Y dev)
git checkout main && git checkout -b hotfix/RC-BUG-XXX-nombre
```

**Convención commits:** `tipo(scope): descripción — ID ticket`
Tipos: `feat` `fix` `docs` `refactor` `test` `chore`

---

## Quality Gates (antes de cualquier "done")

| Gate | Acción | Criterio |
|---|---|---|
| 0 | `python -m py_compile app.py utils/**/*.py` | Sin errores de sintaxis |
| 1 | `pytest tests/ -v` | 100% PASS |
| 2 | Verificar QA mode | No enviar emails/WA reales en staging |
| 3 | Smoke manual `localhost:8502` | CA-1 a CA-5 PASS con evidencia |
| 4 | Actualizar FRD + backlog + TICKETS_ANTAY | Docs al día |

---

## Ambientes

| Ambiente | Puerto | Cómo arrancar |
|---|---|---|
| PROD (local) | 8501 | `./start_prod.ps1` |
| STAGING | 8502 | `./start_staging.ps1` o `$env:SUPABASE_URL=<staging> streamlit run app.py --server.port 8502` |
| QA servidor | — | Ejecutar `5_COMBINADO_APP_Y_TUNEL.bat` en \\QA\antay-cobranza |

Banner staging: visible automáticamente si `SUPABASE_URL` contiene `hrnqngndnohkkegtzgjg.supabase.co`.

---

## Sistema de diseño Antay (resumen)

```python
# Paleta principal — NUNCA hardcodear fuera de utils/ui/styles.py
COLORS = {
    "primary":     "#0D3B66",  # azul corporativo
    "accent":      "#0B7285",  # teal activo
    "success":     "#2B8A3E",  # verde
    "warning":     "#E67700",  # naranja
    "danger":      "#C92A2A",  # rojo
    "background":  "#F1F5FB",
    "surface":     "#FFFFFF",
    "text_main":   "#102A43",
    "text_muted":  "#486581",
    "border":      "#D9E2EC",
}
```

- Tipografía: Manrope (headings) + IBM Plex Sans (body)
- Tabs: persistir siempre por **índice entero** en `session_state`, nunca por string label
- Botones: `min-height: 44px` (WCAG), confirm dialog antes de acciones destructivas
- Contraste mínimo WCAG AA: 4.5:1

---

## Checklist pre-entrega UI

```
[ ] Colores desde COLORS / CSS vars — sin hardcode
[ ] Spinner para ops >300ms
[ ] Empty states con mensaje + acción sugerida
[ ] Errores descriptivos (no tracebacks crudos)
[ ] Acciones destructivas con confirmación
[ ] Tab index por entero en session_state
[ ] df_final no modificado desde UI
[ ] Banner staging visible si IS_STAGING
[ ] load_css() llamado en app.py
```

---

## Slash commands disponibles

| Comando | Propósito |
|---|---|
| `/nuevo-ciclo` | Flujo completo Gitflow para nuevo feature |
| `/hotfix` | Flujo hotfix urgente con rollback disponible |
| `/smoke-test` | Checklist TIER 2 smoke test en staging |
| `/gate-check` | Verificar quality gates Gate 0 + Gate 1 |
| `/deploy-qa` | Pasos para copiar cambios al servidor QA |
| `/ui-ux` | Guía completa diseño Antay — paleta, componentes, checklist pre-entrega |

---

## Autonomía del agente

Ejecutar autónomamente: análisis, implementación, tests, documentación.
Pedir confirmación solo ante:
- Ambigüedad real de regla de negocio no definida en FRD
- Operaciones destructivas (DROP TABLE, push --force, borrar ramas)
- Cambios que afecten `main` directamente
- Deploy a QA o push a remoto

Comunicación siempre en **español claro y directo**.

---

## Dashboard RC-FEAT-038 — Contexto y casuística aprendida

> Sección crítica para el desarrollo del **Informe Gerencial (RC-FEAT-039)**.
> Todo lo aprendido aquí debe aplicarse al diseño de ese informe.

### Esquema de tablas del Dashboard (Supabase staging)

```
documentos_ciclo   → cod_cliente (NO cliente_id), cycle_id, tipo_pedido, enviar_email, saldo_real
gestiones          → cliente_id (= cod_cliente en valor), tipo_registro, tipo_gestion, cycle_id, resultado
notificaciones     → cliente_id, tipo_notificacion, estado, cycle_id
clientes           → id (UUID), cliente_id (código como "000001"), nombre
acuerdos_pago      → ciclo_id (no cycle_id), estado, cliente_id
```

**TRAMPA CRÍTICA:** `documentos_ciclo` usa `cod_cliente`, pero `gestiones` y `notificaciones` usan `cliente_id`. Ambos contienen el mismo valor (ej: "000211"). NUNCA hacer `select("cliente_id")` en `documentos_ciclo` — falla en producción.

### Regla DSP/PAV (tipo_pedido)

- `tipo_pedido IN ('DSP','PAV')` = registros de crédito/descuento, no de deuda real.
- **Solo se excluyen los REGISTROS**, nunca el cliente completo.
- Un cliente con FAC + DSP → sigue en cartera (por el FAC), su saldo es menor.
- Un cliente con SOLO DSP → no tiene deuda real → queda fuera de cartera operativa. Correcto.
- El flag `enviar_email` es propiedad del **cliente**, no del registro. Leer de `_todos_docs` para determinar notificabilidad.
- Implementación correcta en `get_funnel_cobranza()`:
  ```python
  _set_en_cartera = {cod from _filas_validas}   # no-DSP/PAV
  _set_con_flag   = {cod from _todos_docs where enviar_email='SI'}
  set_notificable = _set_en_cartera & _set_con_flag  # intersección
  ```

### Arquitectura del funnel — "Pirámide de Cobertura"

```
cartera_total   = todos los clientes únicos del ciclo (incluyendo especiales)
cartera         = notificables (enviar_email='SI' Y tienen deuda real)
especiales      = cartera_total - cartera (trato directo, no notificar)

set_wa          = clientes con ENVIO WHATSAPP en el ciclo
set_email       = clientes con notificacion EMAIL ENVIADO en el ciclo
set_directo     = clientes con GESTION tipo LLAMADA/VISITA/NOTA/OTRO en el ciclo
                  ∩ set_notificable

set_notif       = set_wa | set_email
set_alcanz      = set_notif | set_directo
alcanzados      = len(set_alcanz)
sin_contactar   = cartera - alcanzados   ← ALERTA CRÍTICA para el gerente
con_respuesta   = clientes únicos en set_notificable con GESTION registrada
pendientes_seg  = alcanzados - con_respuesta
```

**Invariante matemática garantizada:** `con_respuesta ≤ alcanzados ≤ cartera`

### Tipos de gestión (tabla gestiones)

| tipo_registro | tipo_gestion | Significado |
|---|---|---|
| ENVIO | WHATSAPP | Envío masivo automático del sistema |
| ENVIO | EMAIL | Envío email automático del sistema |
| GESTION | WHATSAPP | Gestor registró resultado del WA enviado |
| GESTION | LLAMADA | Gestor llamó directamente al cliente |
| GESTION | VISITA | Gestor visitó presencialmente al cliente |
| GESTION | NOTA | Gestor dejó una nota/observación |
| GESTION | OTRO | Otro tipo de contacto directo |

### Valores de resultado (gestiones)

```
EXITOSO        → acordó pagar (cuenta como "recuperado")
PROMESA_PAGO   → legado de EXITOSO, mismo significado
EN_NEGOCIACION → en proceso de acuerdo
SOLICITO_PLAZO → pidió más tiempo
SIN_RESPUESTA  → no contestó
ESCALAR_LEGAL  → derivar a legal
DISPUTA        → cuestiona la deuda
```

### Coherencia de KPIs — lección aprendida

**Error que NO repetir:** Los KPIs del "Resumen Ejecutivo" usaban `get_kpis_periodo()` (filtro fecha) mientras el funnel usaba `get_funnel_cobranza()` (filtro cycle_id). Esto producía "Gestionados: 35" vs "Con resultado: 32" en el mismo Dashboard, y "Tasa de gestión: 109.4%" (imposible).

**Regla fija:** Todos los KPIs del Dashboard deben derivar del funnel (cycle_id). Nunca mezclar período y ciclo en la misma vista.

```python
# CORRECTO — todo del funnel
contactados = funnel.get("alcanzados", 0)
gestionados = funnel.get("con_respuesta", 0)
tasa_gestion = gestionados / contactados * 100  # siempre ≤ 100%
```

### Casuística de datos reales (staging CIC-20260322-1256)

- **cartera notificable:** 32 clientes con FAC/deuda real y enviar_email='SI'
- **especiales:** 20 clientes con trato directo (enviar_email='NO' o sin deuda real)
- **cliente 000005:** tiene solo 1 documento DSP en el ciclo → fuera de cartera operativa. El gestor le registró una LLAMADA, pero esa gestión NO cuenta en el funnel (correcto: no tiene deuda).
- **KORESUR S.A.C. (000087):** registró gestiones con cycle_id=NULL (bug anterior). Las gestiones existen en BD pero son históricas y no se vinculan a ningún ciclo. No eliminar — son historia real.
- **Ciclos en staging:** solo existe `CIC-20260322-1256`. Los HIST_* tienen cycle_id=NULL en gestiones (datos anteriores al fix).

### Funnel adaptativo — reglas de visibilidad

| Fila | Mostrar |
|---|---|
| 🏢 Toda la cartera | Solo si especiales > 0 |
| ↳ ⭐ Especiales (trato directo · no notificar) | Solo si especiales > 0 |
| 📋 Cartera activa | Siempre |
| 📱 Notificados WA | Solo si notif_wa > 0 |
| 📧 Notificados Email | Solo si notif_email > 0 |
| 📞 Con gestión directa (X llamadas · Y visitas) | Solo si contacto_dir > 0 |
| 🎯 Total alcanzados | Siempre |
| ✅/❌ Sin contacto | Siempre (✅ cuando 0, ❌ ALERTA cuando > 0) |
| 💬 Con resultado registrado | Siempre |
| ⏳ Pendientes de seguimiento | Solo si > 0 |
| ↳ ✅ Comprometidos | Solo si > 0 |
| 🤝 Con acuerdo activo | Solo si > 0 |

### Para el Informe Gerencial (RC-FEAT-039) — pendiente

El informe debe mostrar estas métricas clave con su contexto narrativo:

1. **Cobertura de cartera:** alcanzados/cartera (nunca supera 100%)
2. **Intensidad de gestión:** total registros GESTION (puede superar cartera — es esfuerzo del equipo)
3. **Efectividad:** con_respuesta/alcanzados
4. **Tasa de recuperación:** EXITOSO/con_respuesta
5. **Clientes críticos:** mayor saldo sin gestión = riesgo
6. **Desglose por canal:** WA masivo vs Email vs Gestión directa (llamada/visita)
7. **Evolución temporal:** comparar ciclos (requiere múltiples cycle_ids)

**Métricas financieras disponibles:** `saldo_real`, `moneda`, `dias_mora` en `documentos_ciclo`.
Agregar por cliente con `SUM(saldo_real) WHERE tipo_pedido NOT IN ('DSP','PAV')`.

### Ambiente de trabajo

- **SIEMPRE validar contra staging:** `https://hrnqngndnohkkegtzgjg.supabase.co`
- Cargar con: `load_dotenv('.env.staging')` + `os.environ['SUPABASE_URL'] = 'https://hrnqngndnohkkegtzgjg.supabase.co'`
- Producción (`gnsetbdjxbtaqchdhgpi.supabase.co`) solo accesible desde PC QA — nunca desde laptop del PO.
- El script `CLEAN_SUPABASE_TABLES_FOR_TESTING.sql` limpia TODAS las tablas operativas en staging (destructivo — usar con cuidado).
