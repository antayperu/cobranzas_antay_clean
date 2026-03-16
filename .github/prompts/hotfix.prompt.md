---
mode: agent
description: Flujo de hotfix urgente con rollback disponible
---

# Hotfix — ReporteCobranzas

Flujo para corregir un bug crítico en producción.

## Variables del hotfix (completar antes de ejecutar)

- **ID Ticket:** RC-BUG-XXX
- **Bug:** descripción del problema
- **Rama:** hotfix/descripcion-corta
- **Tag estable de rollback:** v1.X.X (verificar con `git tag`)

## Paso 0 — Verificar tag de rollback disponible

```bash
git tag --list "v*" --sort=-version:refname | head -5
```

Anotar el tag estable antes de tocar nada.

## Paso 1 — Crear hotfix branch desde main

```bash
git checkout main
git pull origin main
git checkout -b hotfix/descripcion-corta
```

## Paso 2 — Aplicar el fix

Verificar:
- [ ] ¿El fix toca columnas prohibidas? Si sí, DETENER y consultar FRD
- [ ] ¿El fix afecta SSOT (`df_final`)? Revisar lógica de tracking
- [ ] ¿El fix es mínimo y no introduce cambios de scope?

```bash
git commit -m "fix(scope): RC-BUG-XXX descripción del fix"
```

## Paso 3 — Gate 0 + Gate 1

```powershell
python -m py_compile app.py
pytest tests/ -v
```

Si falla → NO continuar. Revisar el fix.

## Paso 4 — Gate 3 en staging

```powershell
$env:SUPABASE_URL="https://hrnqngndnohkkegtzgjg.supabase.co"
streamlit run app.py --server.port 8502
```

Verificar: el bug ya no ocurre. No hay regresiones visibles.

## Paso 5 — Merge a main Y dev

```bash
# Merge a main (producción)
git checkout main
git merge hotfix/descripcion-corta --no-ff -m "fix: RC-BUG-XXX hotfix a producción"
git push origin main

# Merge a dev (para mantener sincronía)
git checkout dev
git merge hotfix/descripcion-corta --no-ff
git push origin dev

# Limpieza
git branch -d hotfix/descripcion-corta
```

## Rollback (si el hotfix falla en producción)

```bash
git checkout main
git reset --hard vX.X.X   # tag estable anotado en Paso 0
git push origin main --force
```

⚠️ `--force` en main requiere confirmación explícita del Product Owner.

## Gate 4 — Documentación

- [ ] `docs/backlog_priorizado.md` — sección hotfixes, estado Done
- [ ] `docs/TICKETS_ANTAY.md` — estado Done
- [ ] `docs/FRD_REPORTECOBRANZAS_v2.0.md` — si el fix cambia comportamiento documentado
