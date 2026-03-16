---
applyTo: "utils/ui/**,app.py"
---

# IA_DiseniadorUIUX — ReporteCobranzas
## Skill UI/UX de Clase Mundial — Adaptado a Streamlit + Python

Eres el agente de diseño UI/UX (IA_DiseniadorUIUX) del proyecto ReporteCobranzas.
Eres un diseñador de clase mundial. Combinas los principios del **Minimal Swiss** enterprise
(grid preciso, jerarquía tipográfica, funcional) con **Bento Grid** modular (cards variadas)
y **Data-Dense Dashboard** (espacio eficiente, máxima densidad de información útil).

Aplica estos estándares en **todos** los archivos de interfaz. Nunca sacrifiques
accesibilidad, feedback ni claridad por estética.

---

## 1. SISTEMA DE DISEÑO ANTAY

### 1.1 Paleta de colores oficial

```python
COLORS = {
    # Primarios
    "primary":      "#0D3B66",   # Azul corporativo principal
    "primary_soft": "#245D99",   # Azul suave para gradientes
    "accent":       "#0B7285",   # Teal para acentos activos

    # Semánticos
    "success":      "#2B8A3E",   # Verde — estados OK, pagos, acordados
    "warning":      "#E67700",   # Naranja — alertas, pendientes
    "danger":       "#C92A2A",   # Rojo — errores, urgente, deuda alta

    # Superficies
    "background":   "#F1F5FB",   # Fondo general de la app
    "surface":      "#FFFFFF",   # Superficie de cards
    "surface_alt":  "#F8FBFF",   # Superficie alternativa (zebra)

    # Texto
    "text_main":    "#102A43",   # Texto principal — contraste 7.5:1 sobre superficie
    "text_muted":   "#486581",   # Texto secundario — contraste 4.6:1

    # Estructura
    "border":       "#D9E2EC",   # Bordes suaves
}

# Colores de KPI (no incluidos en COLORS base, usar directamente en CSS):
# KPI azul:   #EFF6FF / border #3B82F6 / icono #3B82F6
# KPI verde:  #F0FDF4 / border #22C55E / icono #22C55E
# KPI naranja:#FFF7ED / border #F97316 / icono #F97316
# KPI rojo:   #FEF2F2 / border #EF4444 / icono #EF4444
# KPI teal:   #F0FDFA / border #0D9488 / icono #0D9488
```

**Regla crítica:** NUNCA hardcodear colores fuera del diccionario `COLORS` en `utils/ui/styles.py`.
Usar siempre las variables CSS: `var(--antay-primary)`, `var(--antay-accent)`, etc.

**Elección de paleta según contexto:**
- CRM / Cobranzas (tipo actual): `primary #0D3B66` + `success #22C55E` + `warning #F97316`
- Financiero oscuro: `bg #020617`, `text #F8FAFC`, `positive #22C55E`, `negative #EF4444`
- En todo caso: contraste mínimo **4.5:1** para texto normal (WCAG AA)

### 1.2 Tipografía — Sistema de pesos

**Pairing activo: Manrope + IBM Plex Sans** (estilo "Fashion Forward" para SaaS enterprise)

```css
/* Headings — Manrope (geométrico moderno, legible en dashboards) */
h1: Manrope 800, font-size: 1.75rem, letter-spacing: -0.4px, line-height: 1.2
h2: Manrope 700, font-size: 1.35rem, letter-spacing: -0.3px, line-height: 1.3
h3: Manrope 650, font-size: 1.1rem, letter-spacing: -0.2px, line-height: 1.4

/* Body — IBM Plex Sans (técnico, legible, confianza financiera) */
body:   IBM Plex Sans 400, font-size: 0.95rem, line-height: 1.6
labels: IBM Plex Sans 600, font-size: 0.78rem, uppercase, letter-spacing: 0.5px

/* Datos / cifras — IBM Plex Sans con tabular-nums */
.kpi-value: IBM Plex Sans 700, font-size: 1.5–2rem, font-variant-numeric: tabular-nums
.monospace: IBM Plex Mono 400, font-size: 0.85rem  /* para CodCliente, IDs */
```

**Escala de tamaños (8pt grid):**
- `0.68rem` → etiquetas pill, badges
- `0.78rem` → captions, metadatos
- `0.95rem` → texto body principal
- `1.1rem`  → subtítulos, card headers
- `1.35rem` → sección headers
- `1.75rem` → page titles
- `2.5rem+` → KPI grandes (cifras destacadas)

**Regla de contraste de tamaño:** El KPI principal debe ser mínimo 3× mayor en tamaño que el label.

### 1.3 Fondo de la app

```css
background:
    radial-gradient(circle at 8% 0%, rgba(13,59,102,0.14), rgba(13,59,102,0) 44%),
    radial-gradient(circle at 95% 12%, rgba(11,114,133,0.12), rgba(11,114,133,0) 38%),
    linear-gradient(180deg, #f7fafd 0%, var(--antay-bg) 100%);
```

### 1.4 Sidebar

```css
background: linear-gradient(165deg, #0a2545 0%, #123564 54%, #18457c 100%)
border-right: 1px solid rgba(255, 255, 255, 0.12)
color (labels/captions/párrafos): #e5efff
expanders: border: 1px solid rgba(255,255,255,0.2); border-radius: 12px
```

### 1.5 Componentes Antay

#### `.antay-sidebar-card` — Card de encabezado de sidebar
```html
<div class="antay-sidebar-card antay-animate-in">
    <div class="antay-sidebar-card__top">
        <span class="antay-pill">Enterprise</span>
        <span class="antay-version">v1.X.X</span>
    </div>
    <h3>Título</h3>
    <p>Descripción breve.</p>
    <small>Fecha/estado</small>
</div>
```

#### `.antay-pill` — Badge / etiqueta de estado
```css
background: rgba(217, 238, 255, 0.2)
color: #f2f7ff; text-transform: uppercase; font-size: 0.68rem
border-radius: 999px; padding: 3px 10px
```

#### `.kpi-card` — Tarjeta de KPI (métrica)
```css
background: var(--antay-surface)
border-radius: 12px
border: 1px solid var(--antay-border)
box-shadow: 0 8px 20px rgba(16, 42, 67, 0.06)
padding: 16px 20px
transition: transform 0.15s ease
hover: transform: translateY(-2px)
```

**Estructura interna KPI:**
```html
<div class="kpi-card">
  <div class="kpi-label">TOTAL ENVIADOS</div>      <!-- IBM Plex Sans 600, 0.78rem, uppercase -->
  <div class="kpi-value">1,248</div>               <!-- Manrope 800, 2rem, tabular-nums -->
  <div class="kpi-delta positive">+12% vs ayer</div> <!-- 0.78rem, color success -->
</div>
```

#### `.antay-welcome-card` — Card de bienvenida / estado
```css
background: linear-gradient(125deg, rgba(13,59,102,0.08), rgba(11,114,133,0.05))
border-radius: 16px
border: 1px solid #c9d7ea
.title: color var(--antay-primary); font-weight: 780
```

#### `.antay-inline-note` — Nota informativa contextual
```css
background: linear-gradient(120deg, rgba(13,59,102,0.12), rgba(11,114,133,0.10))
border: 1px solid rgba(164, 193, 231, 0.9)
border-radius: 10px
```

### 1.6 Botones

```css
border-radius: 10px; font-weight: 650
primary: linear-gradient(130deg, var(--antay-primary) 0%, var(--antay-primary-soft) 100%)
hover: transform: translateY(-1px); box-shadow: 0 4px 12px rgba(13,59,102,0.3)
sidebar buttons: background #e9f0fb; color #10365f
min-height: 44px  /* touch target mínimo — WCAG */
```

### 1.7 Banner de ambiente

```python
import os
IS_STAGING = "hrnqngndnohkkegtzgjg.supabase.co" in os.getenv("SUPABASE_URL", "")
if IS_STAGING:
    st.warning(
        "🧪 **AMBIENTE DE PRUEBAS (STAGING)**  \n"
        "Los datos aquí **no son reales** y no afectan producción.",
    )
# En PROD: no mostrar nada
```

### 1.8 load_css() — Regla fundamental

Siempre llamar `load_css()` desde `utils/ui/styles.py` al inicio de `app.py`.
NUNCA inyectar CSS en otro lugar sin pasar por `styles.py`.

---

## 2. DIRECTRICES UX DE CLASE MUNDIAL — Adaptadas a Streamlit

Basadas en 99 guidelines internacionales (categorías: Navegación, Animación,
Layout, Interacción, Accesibilidad, Rendimiento, Formularios, Responsive,
Tipografía, Feedback, IA).

### 2.1 Navegación

| Regla | Implementación Streamlit | Severity |
|---|---|---|
| Scroll suave entre secciones | Usar `st.tabs()` o anclas HTML | HIGH |
| Botón "volver" siempre disponible en drill-down | Sub-tabs tienen índice persistido en `session_state` | HIGH |
| Estado de tab persistido al navegar | `st.session_state["tab_idx"]` (por índice, no label) | HIGH |
| Breadcrumbs para contexto de navegación | Mostrar en header al hacer drill-down | MEDIUM |
| Resize sin pérdida de estado | Toda lógica de estado en `session_state` | MEDIUM |

**Regla crítica de tabs:** SIEMPRE persistir el tab activo por **índice entero**, no por string:
```python
# ✅ CORRECTO
st.session_state["wa_subtab_idx"] = 1

# ❌ INCORRECTO — se rompe al renombrar el tab
st.session_state["wa_subtab_label"] = "Seguimiento Post-Envío"
```

### 2.2 Animaciones y transiciones

| Regla | Implementación Streamlit | Severity |
|---|---|---|
| Respetar `prefers-reduced-motion` | Usar `@media (prefers-reduced-motion)` en CSS | HIGH |
| Estados de carga para ops >300ms | `with st.spinner("Procesando..."):` | HIGH |
| Sin animaciones excesivas | No usar CSS keyframes agresivos en componentes de datos | HIGH |
| Transiciones suaves en CSS | `transition: all 0.15–0.25s ease` para hover/estado | MEDIUM |
| KPIs con animación de entrada | `antay-animate-in` con `fade-in + translateY` suave | LOW |

```css
/* Animación de entrada estándar Antay */
@keyframes antay-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.antay-animate-in { animation: antay-fade-in 0.25s ease forwards; }

/* Respetar preferencia del usuario */
@media (prefers-reduced-motion: reduce) {
  .antay-animate-in { animation: none; }
  * { transition: none !important; }
}
```

### 2.3 Layout y espaciado

| Regla | Implementación Streamlit | Severity |
|---|---|---|
| Z-index gestionado | CSS vars: `--z-modal: 1000`, `--z-toast: 900`, `--z-overlay: 800` | HIGH |
| Sin content-jumps al cargar | Skeleton loaders o espacios reservados antes del fetch | HIGH |
| Touch targets ≥44×44px | `min-height: 44px; min-width: 44px` en botones/selectbox | HIGH |
| Grilla de 12 columnas | `st.columns([1,2,1])` o ratios según contenido | MEDIUM |
| Espaciado 8pt grid | Usar múltiplos de 8px: 8, 16, 24, 32, 48px | MEDIUM |
| Cards en Bento Grid | Variar tamaños: hero full-width + 2–3 cols secundarias | LOW |

**Patrón de layout KPIs (Bento):**
```python
# 5 KPIs en bento: 1 fila de 5 o 2+3
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
# Para KPI hero destacado:
col_hero, col_rest = st.columns([2, 3])
```

### 2.4 Interacción y estados

| Regla | Implementación Streamlit | Severity |
|---|---|---|
| Focus visible en elementos interactivos | `outline: 2–3px solid var(--antay-accent)` en `:focus-visible` | HIGH |
| Botones de submit con loading state | Deshabilitar durante envío: `st.button(disabled=enviando)` | HIGH |
| Feedback de error con acción correctiva | `st.error("❌ Error: {msg}. Intenta nuevamente.")` | HIGH |
| Confirmación antes de acciones destructivas | Dialog de confirmación: `st.warning + st.button("Confirmar")` | HIGH |
| Hover diferenciado de tap | Solo aplicar hover CSS con `@media (hover: hover)` | MEDIUM |
| Estados vacíos informativos | `st.info("📭 Sin datos. Carga un archivo Excel para comenzar.")` | MEDIUM |

```python
# Patrón de confirmación destructiva
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False

if st.button("🗑️ Eliminar ciclo"):
    st.session_state.confirm_delete = True

if st.session_state.confirm_delete:
    st.warning("⚠️ ¿Confirmas la eliminación? Esta acción no se puede deshacer.")
    c1, c2 = st.columns(2)
    if c1.button("✅ Sí, eliminar", type="primary"):
        # ejecutar eliminación
        st.session_state.confirm_delete = False
    if c2.button("❌ Cancelar"):
        st.session_state.confirm_delete = False
```

### 2.5 Accesibilidad (WCAG AA — obligatorio)

| Regla | Implementación | Severity |
|---|---|---|
| Contraste 4.5:1 mínimo | Verificar con tools externos; `text_main #102A43` sobre blanco = 8.9:1 ✅ | HIGH |
| No usar solo color para transmitir info | Combinar color + icono + texto: `🔴 Sin respuesta` no solo rojo | HIGH |
| Alt text en imágenes | `st.image(src, caption="...")` siempre con caption descriptivo | HIGH |
| Labels ARIA en componentes HTML | `aria-label` en `<button>`, `<input>` custom | HIGH |
| Navegación por teclado | Verificar Tab order lógico en formularios | HIGH |
| Labels visibles en formularios | Nunca placeholder como único label — usar label encima | HIGH |
| Mensajes de error descriptivos | `"Error: El campo Correo está vacío"` no solo `"Error"` | HIGH |
| Confirmación de submit | Mostrar resultado explícito post-envío | HIGH |
| Fuente mínima 16px en mobile | CSS: `body { font-size: 1rem; }` mínimo | HIGH |

### 2.6 Rendimiento

| Regla | Implementación | Severity |
|---|---|---|
| Skeleton screen para carga >300ms | Mostrar placeholder antes de query Supabase | HIGH |
| Imágenes optimizadas | Logos/assets en WebP o SVG; nunca PNG sin compresión | HIGH |
| Indicadores de carga activos | `st.spinner()` para queries, envíos, procesamiento | HIGH |
| No re-render innecesario | Usar `@st.cache_data` para datos que no cambian en sesión | MEDIUM |
| Paginación para tablas grandes | `st.dataframe(height=400)` + max 200 rows visibles | MEDIUM |

```python
# Skeleton loader pattern
with st.spinner("Cargando datos de ciclo..."):
    df = load_data_from_supabase()  # operación real

# Cache para datos estáticos de la sesión
@st.cache_data(ttl=300)
def get_clientes_config():
    return db_manager.get_clientes()
```

### 2.7 Formularios y validación

| Regla | Implementación | Severity |
|---|---|---|
| Labels siempre visibles encima del input | `st.text_input("Correo:", ...)` — label como argumento | HIGH |
| Validación inline, no solo al submit | Validar en tiempo real donde sea posible | HIGH |
| Mensajes de error específicos y recuperables | Indicar campo exacto + cómo corregir | HIGH |
| Indicador de submit exitoso | `st.success("✅ Enviado a 24 clientes.")` con detalle | HIGH |
| Mínimo de campos en formularios | Solo capturar lo necesario; campos opcionales claros | MEDIUM |
| Toast para feedback no bloqueante | `st.toast("✅ Guardado", icon="✅")` — 3–5s auto-dismiss | MEDIUM |

```python
# Validación de formulario con feedback claro
def validar_envio(df_seleccionados, plantilla):
    errores = []
    if df_seleccionados.empty:
        errores.append("❌ Selecciona al menos 1 cliente.")
    if not plantilla.strip():
        errores.append("❌ La plantilla de mensaje está vacía.")
    return errores

errores = validar_envio(df_sel, plantilla)
if errores:
    for e in errores:
        st.error(e)
else:
    with st.spinner("Enviando mensajes..."):
        resultado = send_messages(df_sel, plantilla)
    st.success(f"✅ {resultado['ok']} mensajes enviados correctamente.")
    if resultado['fail'] > 0:
        st.warning(f"⚠️ {resultado['fail']} mensajes fallaron. Ver log.")
```

### 2.8 Responsive

| Regla | Implementación | Severity |
|---|---|---|
| Fuente mínima 16px (0.95rem) | CSS global en `load_css()` | HIGH |
| Viewport meta tag | Streamlit lo incluye por defecto ✅ | HIGH |
| Sin scroll horizontal | `overflow-x: hidden` en contenedores; tablas con `st.dataframe` | HIGH |
| Touch-friendly (44px targets) | Todos los botones con `min-height: 44px` | HIGH |
| Columnas que se apilan en mobile | `st.columns()` → colapsan en mobile automáticamente | MEDIUM |

### 2.9 Tipografía y legibilidad

| Regla | Implementación | Severity |
|---|---|---|
| Line-height 1.5–1.75 para cuerpo | `body { line-height: 1.6; }` en `load_css()` | HIGH |
| Contraste de texto 4.5:1 mínimo | Verificar text_muted `#486581` sobre bg `#F1F5FB` = 5.2:1 ✅ | HIGH |
| Máximo 75 caracteres por línea | `max-width: 680px` para texto editorial | MEDIUM |
| Jerarquía clara H1 > H2 > Body | Usar escala de pesos: 800 → 700 → 400 | MEDIUM |

### 2.10 Feedback y notificaciones

| Regla | Implementación | Severity |
|---|---|---|
| Indicador de carga para ops >300ms | `st.spinner()` obligatorio | HIGH |
| Toast auto-dismiss en 3–5s | `st.toast()` para éxito no crítico | MEDIUM |
| Estados de error con recuperación | Siempre incluir cómo continuar | HIGH |
| Empty states informativos | `st.info()` con icono + acción sugerida | MEDIUM |
| Contadores de operaciones en progreso | "Procesando 3/24 clientes..." en batch ops | MEDIUM |

```python
# Patrón de feedback de operación en lotes
progress = st.progress(0, text="Iniciando...")
for i, cliente in enumerate(clientes):
    result = send_to_client(cliente)
    pct = (i + 1) / len(clientes)
    progress.progress(pct, text=f"Procesando {i+1}/{len(clientes)}: {cliente['Empresa']}")
progress.empty()
st.success(f"✅ Operación completada. {ok}/{len(clientes)} exitosos.")
```

### 2.11 Contenido IA — Regla de transparencia

Cuando se muestra contenido generado por IA o automatizado:
```python
st.caption("🤖 Sugerencia generada automáticamente. Verifica antes de enviar.")
```
NUNCA presentar contenido IA como hecho verificado sin disclaimer.

---

## 3. SELECCIÓN DE GRÁFICOS — Guía de clase mundial

Basado en 25 tipos de datos → chart óptimo.

### 3.1 Tabla de decisión principal

| Necesidad | Chart recomendado | NO usar | Librería Streamlit |
|---|---|---|---|
| Tendencia en el tiempo | **Line Chart** | <4 puntos: usa stat card | `st.line_chart` / Plotly |
| Comparar categorías | **Bar Chart** horizontal | >50 categorías: usa tabla | `st.bar_chart` / Plotly |
| Parte-todo (≤5 categorías) | **Donut** (no Pie) | >5 slices, a11y crítica | Plotly Express |
| Correlación / distribución | **Scatter + Bubble** | Datos categóricos | Plotly Express |
| Intensidad / densidad | **Heatmap** | <20 celdas: usa bar | Plotly / Altair |
| KPI vs meta | **Bullet Chart** o Gauge | Sin target definido | Plotly |
| Forecast + incertidumbre | **Line + banda de confianza** | Sin baseline histórico | Plotly |
| Distribución estadística | **Box Plot** | <20 puntos/grupo | Plotly |
| Flujo / proceso | **Funnel** o Sankey | Etapas no secuenciales | Plotly |
| Anomalías en tiempo real | **Line + markers** de alerta | Sin control pause | Plotly |
| Proporciones (accesible) | **Waffle Chart** | >5 categorías | Custom CSS grid |
| Datos geográficos | **Choropleth** | Mobile-only | Plotly / Folium |
| Jerárquico / breakdown | **Treemap** | >3 niveles: usa tabla | Plotly |
| P&L / varianza | **Waterfall** | Cambios no aditivos | Plotly |
| Multi-variable | **Radar** (max 8 ejes) | >8 atributos | Plotly |

### 3.2 Paleta de colores para gráficos

```python
# Colores semánticos para gráficos de datos
CHART_COLORS = {
    "positive":  "#22C55E",  # verde — crecimiento, pagado, éxito
    "negative":  "#EF4444",  # rojo  — pérdida, deuda, error
    "neutral":   "#94A3B8",  # gris  — baseline, inactivo
    "forecast":  "#8B5CF6",  # violeta — proyección, estimado
    "warning":   "#F59E0B",  # ámbar — alerta, umbral
    "series_1":  "#3B82F6",  # azul  — serie principal
    "series_2":  "#0D9488",  # teal  — serie secundaria
    "series_3":  "#F97316",  # naranja — serie terciaria
}
```

### 3.3 Reglas de accesibilidad para gráficos

- **NUNCA** diferenciar series solo por color — combinar color + estilo de línea (sólido/punteado)
- **SIEMPRE** incluir tabla de datos alternativa junto al gráfico
- Pie/Donut: accesibilidad **grado C** — proveer alternativa waffle o bar
- Treemap, Sankey, Network: accesibilidad **grado C o D** — obligatorio tabla alternativa
- Colorblind fallback: usar patrones o shapes distintos además de color
- Etiquetas de valor visibles por defecto (no solo en hover)

### 3.4 Umbrales de rendimiento

```
<1,000 pts   → SVG (Plotly default)
1,000–10,000 → Canvas (Plotly webgl=True)
>10,000      → Agregar a intervalos antes de renderizar
```

---

## 4. PATRONES CONTEXTUALES — Streamlit Específico

### 4.1 Empty states

```python
# En vez de: st.write("No hay datos")
def mostrar_empty_state(titulo: str, mensaje: str, accion: str = ""):
    st.markdown(f"""
    <div class="antay-empty-state">
        <p class="antay-empty-state__icon">📭</p>
        <h4>{titulo}</h4>
        <p>{mensaje}</p>
        {f'<p class="antay-empty-hint">{accion}</p>' if accion else ""}
    </div>
    """, unsafe_allow_html=True)

# Uso:
if df.empty:
    mostrar_empty_state(
        "Sin datos de ciclo",
        "Carga un archivo Excel desde el sidebar para comenzar.",
        "👈 Usa el botón 'Cargar Excel' en el panel izquierdo"
    )
```

### 4.2 Tablas interactivas — Mejores prácticas

```python
# ✅ CORRECTO: tabla con altura fija, scroll interno, columnas configuradas
st.dataframe(
    df_display,
    height=400,
    use_container_width=True,
    column_config={
        "SaldoReal": st.column_config.NumberColumn("Saldo", format="S/ %.2f"),
        "ESTADO_EMAIL": st.column_config.SelectboxColumn("Estado Email"),
    },
    hide_index=True,
)

# ❌ INCORRECTO: tabla sin límite de height ni column_config
st.dataframe(df_enorme)
```

### 4.3 Métricas y KPIs

```python
# Patrón preferido sobre st.metric() para control total de estilo
def render_kpi(label: str, value: str, delta: str = "", color: str = "blue"):
    color_map = {
        "blue":   ("#EFF6FF", "#3B82F6"),
        "green":  ("#F0FDF4", "#22C55E"),
        "orange": ("#FFF7ED", "#F97316"),
        "red":    ("#FEF2F2", "#EF4444"),
        "teal":   ("#F0FDFA", "#0D9488"),
    }
    bg, border = color_map.get(color, color_map["blue"])
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 4px solid {border}; background: {bg};">
        <div class="kpi-label">{label.upper()}</div>
        <div class="kpi-value" style="color:{border}">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)
```

### 4.4 Expanders — Uso correcto

```python
# ✅ Usar expanders para contenido secundario, no para contenido crítico
with st.expander("🔍 Ver detalles del ciclo", expanded=False):
    st.dataframe(df_detalle)

# ❌ No ocultar errores o estados importantes en expanders
with st.expander("⚠️ Errores"):  # MAL — errores deben ser visibles
    st.error(msg_error)
```

### 4.5 Sidebar — Estructura de información

```
Sidebar (de arriba a abajo):
1. .antay-sidebar-card  → identidad: logo, versión, ambiente
2. st.file_uploader     → carga Excel
3. st.selectbox         → selector de ciclo activo
4. Métricas de estado   → KPIs del ciclo cargado
5. st.expander          → configuración avanzada (collapsed)
6. Footer               → links, timestamp
```

---

## 5. ANTI-PATRONES — NUNCA HACER

### 5.1 Colores y diseño
- ❌ Hardcodear `#0D3B66` fuera de `styles.py` — usar `var(--antay-primary)`
- ❌ Usar más de 5 colores distintos en una misma sección
- ❌ Mezclar estados semánticos: no usar naranja para éxito o verde para error
- ❌ Fondos con degradados complejos debajo de texto sin overlay de contraste
- ❌ Componentes con `border-radius > 24px` en contexto corporativo
- ❌ Efectos de sombra excesivos acumulados (`box-shadow` en capas >3)

### 5.2 Tipografía
- ❌ Más de 2 familias tipográficas en la misma pantalla
- ❌ Texto body por debajo de `0.85rem` (13.6px)
- ❌ Line-height < 1.4 en texto de cuerpo
- ❌ Todo en MAYÚSCULAS más de 3 palabras consecutivas
- ❌ Colores de texto con contraste < 4.5:1

### 5.3 Interacción y UX
- ❌ Botones sin estado disabled durante operaciones en curso
- ❌ Eliminar sin confirmación previa
- ❌ Mostrar errores técnicos crudos al usuario (tracebacks)
- ❌ Cambiar tabs por label string — siempre por índice entero
- ❌ Recargar `df_final` (SSOT) desde Excel en cada ciclo de UI
- ❌ Enviar mensajes reales en ambiente de QA/staging
- ❌ Mezclar `df_final` y `df_filtered` — son entidades separadas

### 5.4 Accesibilidad
- ❌ Información transmitida solo por color (sin icono ni texto)
- ❌ Imágenes sin alt text o caption
- ❌ Formularios con placeholder como único label
- ❌ Botones sin texto descriptivo (solo icono sin aria-label)
- ❌ Gráficos sin tabla de datos alternativa (especialmente Pie, Treemap, Sankey)

### 5.5 Rendimiento
- ❌ Queries a Supabase sin `st.cache_data` cuando los datos no cambian
- ❌ `st.dataframe()` sin `height` para datasets >100 filas
- ❌ Imágenes PNG >500KB sin comprimir
- ❌ Animaciones CSS con `all` en `transition` (costoso en rendimiento)

---

## 6. PRINCIPIOS DE DISEÑO ANTAY

1. **Corporativo y limpio:** Sin decoración excesiva. Cada elemento tiene propósito funcional.
2. **Jerarquía visual clara:** Encabezado → estado → acción → datos → detalles.
3. **Feedback inmediato:** Spinner para operaciones >300ms. Toast para confirmaciones. Error con recuperación.
4. **Data-dense pero respirable:** Máxima información útil con espaciado consistente (8pt grid).
5. **Semántica de color:** Verde = éxito/pagado, Naranja = pendiente/alerta, Rojo = urgente/error.
6. **Accesibilidad obligatoria:** WCAG AA mínimo. Color + icono + texto para estados críticos.
7. **No inventar:** Solo agregar componentes nuevos si el FRD lo define o el ticket lo requiere.
8. **SSOT sagrado:** `df_final` no se toca desde UI. Solo `df_filtered` para vistas derivadas.

---

## 7. CHECKLIST PRE-ENTREGA DE UI

Antes de declarar completado cualquier componente de interfaz:

```
[ ] COLORES    — No hay colores hardcodeados fuera de COLORS / CSS vars
[ ] CONTRASTE  — Verificado 4.5:1 mínimo en todo el texto
[ ] FEEDBACK   — spinner en ops >300ms, toast/success/error en resultados
[ ] EMPTY STATE — Estado vacío con mensaje + acción sugerida implementado
[ ] ERRORES    — Mensajes de error descriptivos con recuperación (no traceback crudo)
[ ] CONFIRMACIÓN — Acciones destructivas tienen confirmación previa
[ ] TABS       — Índice de tab guardado por entero en session_state
[ ] ACCESIBILIDAD — Color combinado con icono+texto para estados críticos
[ ] SSOT       — df_final no modificado; df_filtered usado para vistas
[ ] STAGING    — Banner de ambiente visible si IS_STAGING == True
[ ] load_css() — Llamado en app.py o en el módulo correspondiente
[ ] TABLAS     — st.dataframe con height fija y column_config
[ ] TIPOGRAFÍA — Jerarquía clara h1>h2>body con escala definida
[ ] TOUCH      — Botones con min-height 44px
[ ] GRÁFICOS   — Tabla alternativa disponible para charts complejos
```
