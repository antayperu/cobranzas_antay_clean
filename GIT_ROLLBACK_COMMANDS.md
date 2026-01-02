# Comandos Git para Rollback y Tagging

## 1. Crear Tag de Rollback (ANTES de merge)

```bash
# Crear tag en el commit actual (estado estable antes de v1.5.2)
git tag -a v1.5.0-stable -m "Estado estable antes de cambios fullscreen/tracking"

# Push del tag al remoto
git push origin v1.5.0-stable
```

## 2. Verificar Estado Actual

```bash
# Ver commits recientes
git log --oneline -10

# Ver tags existentes
git tag -l

# Ver diff desde tag estable
git diff v1.5.0-stable..HEAD
```

## 3. Rollback Completo (si Gate 3 FAIL)

### Opción A: Rollback Suave (Crear Branch de Rollback)
```bash
# Checkout al tag estable
git checkout v1.5.0-stable

# Crear branch de rollback
git checkout -b rollback-to-stable

# Push del branch
git push origin rollback-to-stable

# Crear PR para merge a main
# (Hacer PR manual en GitHub)
```

### Opción B: Rollback Duro (Revertir Commits)
```bash
# Ver commits a revertir
git log --oneline

# Revertir commits uno por uno (más seguro)
git revert <commit-hash>
git revert <commit-hash>
# ... repetir para cada commit

# O revertir rango completo
git revert HEAD~5..HEAD

# Push de los reverts
git push origin main
```

### Opción C: Reset Duro (PELIGROSO - Solo en emergencia)
```bash
# ADVERTENCIA: Esto borra cambios permanentemente
git reset --hard v1.5.0-stable

# Force push (requiere permisos)
git push origin main --force
```

## 4. Crear Tag de Release (si Gate 3 PASS)

```bash
# Después de validar Gate 3 exitosamente
git tag -a v1.5.2 -m "Release v1.5.2: Fullscreen UX + Tracking Fixes"

# Push del tag
git push origin v1.5.2

# Crear release en GitHub
# (Hacer release manual en GitHub con changelog)
```

## 5. Comandos de Verificación Post-Rollback

```bash
# Verificar que estamos en el tag correcto
git describe --tags

# Verificar archivos modificados
git status

# Verificar que la app funciona
streamlit run app.py
pytest tests/test_business_rules.py -v
```

## 6. Workflow Recomendado

1. **ANTES de merge:** `git tag v1.5.0-stable`
2. **Hacer cambios** en feature branch
3. **Ejecutar Gate 0:** `python -m py_compile app.py`
4. **Ejecutar Gate 1:** `pytest tests/test_business_rules.py -v`
5. **Ejecutar Gate 3:** Validación manual con `GATE3_CHECKLIST_v1.5.2.md`
6. **Si PASS:** `git tag v1.5.2` y merge a main
7. **Si FAIL:** `git checkout v1.5.0-stable` y rollback

## 7. Protección de Branches (Configurar en GitHub)

```yaml
# Settings > Branches > Branch protection rules
# Para branch: main

Required status checks:
  - quality-gates (GitHub Actions)
  - pytest-business-rules

Require pull request reviews: 1

Require status checks to pass before merging: ✅
```

## 8. Comandos de Emergencia

```bash
# Ver qué cambió en un archivo específico
git diff v1.5.0-stable..HEAD -- app.py

# Restaurar un archivo específico del tag estable
git checkout v1.5.0-stable -- app.py

# Ver quién modificó una línea específica
git blame app.py -L 1284,1302
```
