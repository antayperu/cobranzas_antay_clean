# Estado del Proyecto: ReporteCobranzas — Antay Fábrica de Software

**Fecha de Inicio:** 2025-12-16
**Última Actualización:** 2026-03-23
**Versión Actual:** v1.9.0 (dev) — Dashboard RC-FEAT-060 completo · 162/162 tests
**Estado General:** 🟡 EN QA — pendiente Gate 3 smoke en staging antes de merge a main
**Repositorio:** [antayperu/cobranzas_antay_clean](https://github.com/antayperu/cobranzas_antay_clean)
**Rama activa:** `dev` | **Tag producción:** `v1.6.0`

---

## 🎯 Objetivo del Producto

**ReporteCobranzas** es una plataforma de gestión de cobranza B2B para DACTA S.A.C. — consolida cartera, envía notificaciones (WA + Email), registra gestiones CRM y reporta efectividad a distintos niveles jerárquicos.

Ver FRD maestro: `docs/FRD_REPORTECOBRANZAS_v4.0.md`

---

## ✅ Módulos Completados (Producción)

| Módulo | Versión | Estado |
|---|---|---|
| Reporte General (Excel → cartera visual) | v1.6.0 | ✅ PROD |
| Notificaciones Email (HTML premium + tracking) | v1.6.0 | ✅ PROD |
| WhatsApp Masivo (Selenium + 8 plantillas) | v1.8.3 | ✅ PROD |
| CRM Centro de Gestiones (multicanal) | v1.8.3 | ✅ PROD |
| Acuerdos de Pago con Cuotas | v1.8.3 | ✅ PROD |
| Bandeja de Pendientes del Día | v1.8.3 | ✅ PROD |
| Clientes Premium (CRUD Supabase) | v1.7.1 | ✅ PROD |
| Dashboard de Efectividad (RC-FEAT-038) | v1.9.0 | 🟡 QA |

---

## 🔄 Sprint Actual — v1.9.0 (RC-FEAT-060)

### Cambios incluidos en dev (pendientes de merge a main)

**RC-BUG-059** — Fix tasa de recuperación: denominador = clientes únicos del funnel, no conteo de filas KPIs período.

**RC-FEAT-060** — Dashboard: Cobertura, Intensidad y Resultados por cliente:
- `get_funnel_cobranza()`: 9 nuevas claves de intensidad y último resultado por cliente
- Funnel jerárquico con sub-filas auditables (Llamada/Visita/Nota/Otros suman al padre)
- "¿Qué respondieron?": muestra **último resultado por cliente único** (no filas de gestión)
- Top Clientes: `@st.fragment` para cambio instantáneo entre vistas, columna **Nivel mora** (Crítica/Alta/Media/Normal), métrica **Gestionados: X de N**, columnas Docs S/ y Docs US$ recuperadas, UX corporativa

**Tests:** 162/162 PASS (Gate 0 ✅ · Gate 1 ✅)

---

## 📋 Checklist Gate 3 — Smoke en staging (localhost:8502)

Antes de hacer merge a main, el PO valida visualmente:

```
[ ] CA-1  — Abrir Dashboard, ciclo CIC-20260322-1256 cargado correctamente
[ ] CA-2  — Tabla "Proceso de Cobranza": sub-filas Llamada/Visita/Nota/Otros suman al padre
[ ] CA-3  — Columna "Cantidad": sub-filas de directa muestran números (no vacíos)
[ ] CA-4  — "¿Qué respondieron?": cada empresa aparece 1 sola vez (no repite por gestión)
[ ] CA-5  — Top Clientes: Vista operativa es el default al entrar al Dashboard
[ ] CA-6  — Top Clientes: cambiar entre Vista financiera/operativa es instantáneo (sin spinner)
[ ] CA-7  — Top Clientes: KPIs (Gestionados, Saldo, Mora) cambian correctamente al cambiar vista
[ ] CA-8  — Top Clientes: columna "Nivel mora" visible — filas con >90 días muestran "Crítica"
[ ] CA-9  — Banner "AMBIENTE DE PRUEBAS (STAGING)" visible en sidebar
[ ] CA-10 — Versión "v1.9.0" visible en el sidebar
```

---

## 🗺️ Roadmap — Próximas Funcionalidades

Según orden de prioridad del FRD v4.0 (sección 11):

| # | Ticket | Descripción | Prioridad | Depende de |
|---|---|---|---|---|
| 1 | **RC-FEAT-061** | Gestión de Email — CRM seguimiento post-envío email | P1 Alto | — |
| 2 | **RC-FEAT-039** | Informe Gerencial PDF para comités de directorio | P1 Alto | RC-FEAT-038 ✅ |
| 3 | **RC-SEC-001** | Seguridad: credenciales SMTP fuera de config.json | P0 Urgente | — |
| 4 | **RC-UX-001** | Feedback visual en tiempo real durante envío WA masivo | P1 Alto | — |
| 5 | **RC-FEAT-027** | Plantilla WA sugerida por aging del cliente | P1 Alto | — |
| 6 | **RC-FEAT-028** | KPIs operativos del ciclo en Tab WA y CRM | P2 Medio | — |

---

## 🔧 Instrucciones para retomar sesión

1. Leer este archivo: `ESTADO_PROYECTO.md`
2. Leer FRD: `docs/FRD_REPORTECOBRANZAS_v4.0.md`
3. Verificar rama activa: `git status` → debe estar en `dev`
4. Ambientes: STAGING en localhost:8502 con `.env.staging`

---

## 📦 Historial de Versiones

| Versión | Fecha | Descripción |
|---|---|---|
| v1.6.0 | 2026-03-13 | TIER 1 CRM WhatsApp completo — 141/141 tests |
| v1.7.1 | 2026-03-13 | Módulo Clientes Premium + Home 2 archivos |
| v1.7.2 | 2026-03-14 | CRM flow + auto-restore + banner STAGING |
| v1.8.0 | 2026-03-16 | TIER 2: panel prueba WA + 9 mejoras UX post-envío |
| v1.8.3 | 2026-03-16 | Trazabilidad individual + persistencia en tiempo real |
| **v1.9.0** | **2026-03-23** | **RC-FEAT-060: Dashboard completo — funnel jerárquico, resultados por cliente único, Top Clientes 7 mejoras UX + @st.fragment** |
