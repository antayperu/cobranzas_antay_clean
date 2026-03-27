# Flujo de Control de Versiones - ReporteCobranzas

**Basado en:** Estándares de Branching GitFlow - Antay (Metodología Vigente)  
**Documento oficial:** https://notion.so/Estandares-de-Branching-GitFlow-Antay  
**Última actualización:** 2026-03-12

---

## 1. Estructura de Ramas (PERMANENTES)

### 1.1 `main` (Producción)
- **Propósito:** Código en producción que usan los clientes
- **Quién puede hacer merge:** Solo mediante Pull Request desde `dev`
- **Protecciones GitHub:**
  - ❌ No permitir push directo
  - ❌ No permitir force push
  - ❌ No permitir eliminación
  - ✅ Requerir status checks (tests deben pasar)
- **Deploy automático:** Streamlit Cloud lee esta rama y despliega automáticamente

### 1.2 `dev` (Desarrollo/Integración)
- **Propósito:** Rama de integración donde se juntan todas las nuevas funcionalidades
- **Quién puede hacer merge:** Pull Requests desde `feature/*` y `fix/*`
- **Protecciones GitHub:**
  - ❌ No permitir force push
  - ❌ No permitir eliminación
  - ✅ Permitir push directo (para desarrollo rápido)
- **Ciclo:** Se prueba exhaustivamente aquí antes de merge a `main`

---

## 2. Ramas Temporales (SE CREAN Y ELIMINAN)

```
├── feature/[nombre-ticket]    → Nueva funcionalidad (ej: feature/FEATURE-001-Analytics)
├── fix/[nombre-bug]           → Bug no crítico (ej: fix/RC-BUG-023-Reset-SSOT)
└── hotfix/[nombre-urgente]    → Bug CRÍTCO en producción (ej: hotfix/RC-URGENT-Email-Down)
```

**Reglas:**
- Siempre crear desde `dev` (excepto `hotfix` que sale de `main`)
- Nombrar siguiendo el patrón
- Eliminar rama después del merge
- Nunca hacer push directo a `main` desde feature/fix

---

## 3. Flujo de Desarrollo - Paso a Paso

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW RECOMENDADO                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Crear rama feature/fix desde dev:                          │
│     $ git checkout -b feature/TICKET-001-Description dev       │
│                                                                 │
│  2. Desarrollar y commitear con convención Antay:              │
│     $ git commit -m "feat: Descripcion del cambio"             │
│                                                                 │
│  3. Hacer pull request a dev con descripción de cambios        │
│     Esperar: Code Review + Tests pasen + QA valide            │
│                                                                 │
│  4. Merge a dev (merge commit):                                │
│     Resumen: Qué funcionalidad se agregó                       │
│     Description: Link al ticket, cambios principales           │
│                                                                 │
│  5. Local: actualizar dev y eliminar branch:                   │
│     $ git checkout dev                                         │
│     $ git pull origin dev                                      │
│     $ git branch -d feature/TICKET-001-Description            │
│                                                                 │
│  6. Cuando dev esté LISTO PARA PRODUCCIÓN:                    │
│     - Crear release notes documentando cambios                │
│     - Hacer PR de dev --> main                                │
│     - Merge a main (merge commit)                             │
│     - AUTOMÁTICO: Streamlit despliega a producción            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Commits - Convención Antay

```
feat:     Nueva funcionalidad
fix:      Corrección de bug
hotfix:   Corrección urgente en producción
docs:     Cambios en documentación
style:    Cambios de formato (sin afectar funcionalidad)
refactor: Reescritura de código (sin cambiar funcionalidad)
test:     Agregar o modificar tests
chore:    Tareas de mantenimiento
```

**Ejemplo válido:**
```
feat(whatsapp): migrar de Selenium a Playwright para eliminar dependencia de Chrome

- Reemplazar async Selenium con Playwright
- Auto-descargar Chromium en función _ensure_playwright_browser()
- Mantener _SELENIUM_OK alias para compatibilidad retroactiva con módulos UI
- Actualizar requirements.txt (remover selenium y webdriver-manager)
```

---

## 5. SEGURIDAD: Commits de Rollback y Reversión

### 5.1 Estado Actual (2026-03-12)

**Gran cambio realizado: Migración Selenium → Playwright**

| Rama | Commit | Mensaje | Estado |
|------|--------|---------|--------|
| **main** | `2e93afd` | fix(whatsapp): migrate to Playwright | ✅ VIGENTE |
| **main** | `8b52a08` | docs: Guía de instalación Chrome | ⚠️ ANTERIOR |
| **dev** | `471b405` | fix(config_tab): Eliminar recargas | ⚠️ SIN CAMBIOS PLAYWRIGHT |

### 5.2 Cómo Hacer Rollback Seguro

**Si necesitas revertir la migración Playwright en main:**

```bash
# Opción 1: Revert (crear commit inverso - RECOMENDADO)
git checkout main
git pull origin main
git revert 2e93afd
git push origin main
# Streamlit se redeploy automáticamente con Selenium

# Opción 2: Reset (borrar commits - SOLO SI NO ESTÁ EN PRODUCCIÓN)
git checkout main
git reset --hard 8b52a08
git push -f origin main  # ⚠️ CUIDADO: force push
```

**Commit "seguro" anterior (Selenium):**
```
8b52a08 - docs: Guía de instalación de Chrome en servidor QA
```

**Archivo con cambio crítico:**
```
utils/whatsapp_sender.py
  - Contiene: imports de Playwright, _PLAYWRIGHT_OK flag, _SELENIUM_OK alias
  - Cambios: -494 líneas, +364 líneas (refactoring importante)
  - Impactados: Todos los módulos que usan WhatsApp (envío, PDF, imágenes)
```

---

## 6. SINCRONIZACIÓN ACTUAL: dev vs main

### problema IDENTIFICADO ⚠️

```
main (HEAD)
└─ 2e93afd fix(whatsapp): migrate to Playwright  ← VIGENTE
   └─ 8b52a08 docs: Guía de instalación Chrome
      └─ ... (historia compartida)

dev
└─ 471b405 fix(config_tab): Eliminar recargas   ← SIN CAMBIOS PLAYWRIGHT
   └─ (commits anteriores al Playwright)
```

**Status:** `dev` está ATRÁS de `main` por 2 commits (incluyendo Playwright)

### Solución: Sincronizar dev WITH main

```bash
# Opción 1: Merge main en dev (RECOMENDADO para GitFlow)
git checkout dev
git pull origin dev
git merge main  # O: git merge -m "merge: Sync main changes to dev" main
git push origin dev

# Opción 2: Rebase dev sobre main (historial más limpio)
git checkout dev
git pull origin dev
git rebase main
git push origin dev --force-with-lease

# Verificar que ambas ramas tienen los mismos commits:
git log --oneline dev
git log --oneline main
# Deberían mostrar los mismos últimos commits
```

---

## 7. Quality Gates (Validaciones antes de Merge)

**ANTES de hacer PR a main desde dev:**

- [ ] Tests pasen localmente: `pytest tests/ -v`
- [ ] Lint check: `pylint app.py modules/ utils/`
- [ ] Changelog actualizado: `CHANGELOG_v*.md`
- [ ] Requirements.txt sincronizado: `pip freeze | grep -E "playwright|pyperclip|notion"`
- [ ] Validación en QA: Se deployó a `\\QA\antay-cobranza` y se probó

**DESPUÉS de merge a main:**

- Streamlit Cloud se redeploy automáticamente (5-10 minutos)
- Validar en producción: https://[URL-STREAMLIT-PRODUCTION]
- Crear GitHub Release con notas

---

## 8. Errores Comunes (Y Cómo Evitarlos)

| Error | Cómo Ocurre | Cómo Evitar |
|-------|-------------|-----------|
| **Commits a main directamente** | `git push origin main` desde feature | Proteger main en GitHub (no permitir push directo) |
| **Desincronización dev/main** | Merge a main sin sincronizar dev | Después de cada merge a main, hacer merge main→dev |
| **Force push en main** | `git push -f origin main` | Nunca; usar revert en su lugar |
| **Branch olvidada** | No eliminar feature branch | Script pre-push que liste ramas locales viejas |
| **Merge sin testing** | Mergear cambios sin validar | Requerir status checks en GitHub |

---

## 9. Preguntas Frecuentes

### P: "¿Dónde se deployea la app?"
**R:** 
- `dev` branch → Se prueba localmente (`streamlit run app.py`)
- `main` branch → Streamlit Cloud lee esta rama y deployea automáticamente a producción
- Usuarios ven siempre lo que está en `main`

### P: "¿Qué pasa si merge a main y hay un error?"
**R:**
```bash
# Opción segura: Revert (crear commit inverso)
git revert COMMIT_ID
git push origin main
# Streamlit se redeploy con la versión anterior

# Opción rápida: Reset (si no está en producción 1+ hora)
git reset --hard COMMIT_ANTERIOR
git push -f origin main
```

### P: "¿Puedo commitear directamente a main si es un cambio pequeño?"
**R:** **NO. NUNCA.** Incluso cambios pequeños deben:
1. Pasar por feature/fix branch
2. Code review
3. Tests validados
4. Merge a dev primero si corresponde

This ensures trazabilidad y rollback seguro.

---

## 10. Referencias

- [Estándares de Branching GitFlow - Antay (Notion)](https://notion.so/2ff7544a-512b-81ce-b9a7-d27c4b43714a)
- [Convenciones de Commits - Conventional Commits](https://www.conventionalcommits.org/)
- [GitFlow Original - Nvie](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow - Documentación](https://docs.github.com/en/get-started/quickstart/github-flow)

---

**Documento oficial del proyecto. Mantener sincronizado con Notion.**
