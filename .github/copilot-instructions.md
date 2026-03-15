# ReporteCobranzas — Antay Perú
# Instrucciones para GitHub Copilot (contexto global del proyecto)

## Identidad del proyecto

- **Nombre:** ReporteCobranzas
- **Empresa:** Antay Fábrica de Software
- **Product Owner:** Camilo Ortega F.R.
- **Agente de desarrollo:** Antigravity (GitHub Copilot / Claude Sonnet en VS Code)
- **Versión actual:** v1.7.3
- **Rama activa:** `dev`
- **Tag producción:** `v1.6.0` (TIER 1 — 141/141 tests)
- **FRD:** `docs/FRD_REPORTECOBRANZAS_v2.0.md`

## Stack tecnológico

- **Lenguaje:** Python 3.11
- **UI:** Streamlit
- **BD:** Supabase (PostgreSQL cloud) — cloud-only, sin fallback local
- **Email:** SMTP (smtplib)
- **WhatsApp:** `whatsapp_sender.py` con `send_whatsapp_messages_direct()`
- **Excel:** openpyxl / pandas
- **Persistencia sesión:** `st.session_state` + Supabase

## Arquitectura de datos

- `df_final` — SSOT (Single Source of Truth), dataset maestro en memoria. NUNCA se modifica directamente excepto por la lógica de tracking oficial.
- `df_filtered` — vista derivada según filtros activos del Reporte General. Se usa en Email/WA/Preview. **No es el SSOT.**
- Cartera de clientes: solo en Supabase tabla `clientes`. NO se recarga desde Excel en cada ciclo.
- Ciclo identificado por `cycle_id` formato `CIC-YYYYMMDD-HHMM`.

## Columnas prohibidas (nunca renombrar)

`CodCliente`, `Empresa`, `SaldoReal`, `Correo`, `MATCH_KEY`, `ESTADO_EMAIL`, `FECHA_ULTIMO_ENVIO`, `ESTADO_WHATSAPP`

## Ambientes

| Ambiente | Puerto | Supabase URL (parcial) |
|---|---|---|
| PROD | 8501 | (proyecto PROD) |
| STAGING | 8502 | `hrnqngndnohkkegtzgjg.supabase.co` |

Detección automática: si `os.getenv("SUPABASE_URL")` contiene la URL de staging → mostrar banner via `st.warning()`.

## Gitflow Antay (obligatorio)

```
1. git checkout dev
2. git checkout -b feature/nombre-feature
3. [desarrollar + commits]
4. git checkout dev && git merge feature/nombre --no-ff
5. [smoke test en staging localhost:8502]
6. git checkout main && git merge dev --no-ff
7. git push origin main && git push origin dev
8. git branch -d feature/nombre
```

- Ramas permitidas: `main`, `dev`, `feature/*`, `hotfix/*`
- `main` es producción — solo recibe merges desde `dev` con staging verde
- Commits: `tipo(scope): descripción` — ej: `fix(whatsapp): RC-BUG-030 persistir subtab por índice`

## Quality Gates (siempre antes de "done")

| Gate | Descripción |
|---|---|
| Gate 0 | `py_compile` sin errores |
| Gate 1 | `pytest tests/` — mínimo funciones críticas de tracking y selección |
| Gate 2 | Config/QA mode correcto; no enviar a reales en QA |
| Gate 3 | Smoke manual en staging con evidencia (CA-1 a CA-5) |
| Gate 4 | Actualizar FRD + backlog + notas de release |

## Reglas no negociables

1. NO romper el flujo funcional existente.
2. NO inventar procesos sin actualizar el FRD.
3. NO declarar "fix completado" sin evidencia E2E.
4. NO hacer cambios de código sin Gate 3 PASS.
5. SSOT (`df_final`) y vista filtrada (`df_filtered`) son entidades separadas — nunca mezclar.
6. Toda mejora UI/UX: solo si el FRD no exige lógica nueva.
7. Supabase cloud-only: no implementar fallback SQLite/local.
8. Siempre usar `load_css()` en app.py para inyectar design tokens Antay.

## Estructura de directorios clave

```
app.py                          ← entry point Streamlit
utils/
  ui/
    styles.py                   ← design tokens COLORS + load_css()
    sidebar.py                  ← sidebar con cargas, ciclos, banner
    tabs/
      whatsapp.py               ← Tab WhatsApp + CRM post-envío
      email_notifications.py   ← Tab Email
      crm_gestiones.py         ← CRM: gestiones, acuerdos, pendientes
      clientes_premium.py      ← CRUD clientes Supabase
      config_tab.py            ← configuración + plantillas WA
  db_manager.py                ← todas las operaciones Supabase
  supabase_client.py           ← cliente singleton Supabase
  processing.py                ← lógica de procesamiento Excel → df_final
  session.py                   ← gestión session_state
docs/
  FRD_REPORTECOBRANZAS_v2.0.md ← FRD maestro
  backlog_priorizado.md        ← backlog y sprint activo
  TICKETS_ANTAY.md             ← catálogo de tickets
sql/                           ← scripts DDL Supabase
tests/                         ← pytest

```

## Estado actual (2026-03-15)

- TIER 1 CRM WhatsApp: COMPLETADO ✅ (v1.6.0 → v1.7.3)
- Próximo: TIER 2 smoke test en staging + RC-FEAT-026
- Merge `dev → main` pendiente hasta staging verde

## Política de autonomía del agente

El agente ejecuta autónomamente análisis, implementación, pruebas y documentación sin pedir confirmaciones innecesarias. Solo se solicita confirmación ante:
- Ambigüedad real de regla de negocio no definida en el FRD
- Operaciones destructivas (DROP TABLE, borrar ramas, push force)
- Cambios que afecten `main` directamente
