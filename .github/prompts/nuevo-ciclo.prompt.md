---
mode: agent
description: Inicia un nuevo feature siguiendo el Gitflow Antay completo
---

# Nuevo Ciclo de Feature — ReporteCobranzas

Sigue el flujo completo para implementar un nuevo feature.

## Variables del feature (completar antes de ejecutar)

- **ID Ticket:** RC-FEAT-XXX
- **Nombre rama:** feature/nombre-descriptivo
- **Descripción:** ¿Qué hace este feature?
- **Archivo(s) principal(es):** utils/ui/tabs/XXX.py

## Paso 1 — Preparar el branch

```bash
git checkout dev
git pull origin dev
git checkout -b feature/nombre-descriptivo
```

## Paso 2 — Desarrollar

Verificar antes de escribir código:
- [ ] ¿El FRD define claramente este feature? (`docs/FRD_REPORTECOBRANZAS_v2.0.md`)
- [ ] ¿Hay columnas prohibidas involucradas?
- [ ] ¿Afecta `df_final` (SSOT) o solo `df_filtered`?

Al terminar:
```bash
git add -p   # staging selectivo
git commit -m "feat(scope): RC-FEAT-XXX descripción"
```

## Paso 3 — Gate 0 + Gate 1

```powershell
python -m py_compile app.py
pytest tests/ -v
```

Ambos deben pasar antes de continuar.

## Paso 4 — Merge a dev

```bash
git checkout dev
git merge feature/nombre-descriptivo --no-ff -m "feat: merge RC-FEAT-XXX"
```

## Paso 5 — Gate 3 en staging

```powershell
$env:SUPABASE_URL="https://hrnqngndnohkkegtzgjg.supabase.co"
streamlit run app.py --server.port 8502
```

Ejecutar los CA relevantes. Documentar evidencia (screenshots).

## Paso 6 — Merge a main (solo si staging verde)

```bash
git checkout main
git merge dev --no-ff -m "release: RC-FEAT-XXX a producción"
git push origin main
git push origin dev
```

## Paso 7 — Limpieza + Gate 4

```bash
git branch -d feature/nombre-descriptivo
```

Actualizar:
- [ ] `docs/FRD_REPORTECOBRANZAS_v2.0.md` — sección del feature
- [ ] `docs/backlog_priorizado.md` — estado Done
- [ ] `docs/TICKETS_ANTAY.md` — estado Done
- [ ] Versión en `utils/ui/sidebar.py` si aplica
