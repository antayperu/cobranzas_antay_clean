# Evidencia Backups y Recuperacion - SUPABASE-MIG-009

Fecha: 2026-02-17  
Ticket: SUPABASE-MIG-009  
Objetivo: implementar y validar procedimiento operativo de backup y restore en Supabase.

---

## 1) Implementacion

1. Script operativo:
   - `scripts/backup_restore_supabase.py`
   - Subcomandos: `backup`, `restore`
2. Cobertura automatizada:
   - `tests/test_backup_restore_supabase.py` (5 tests)
3. Integracion en quality gates:
   - `scripts/run_migration_quality_gates.py` ahora incluye `GATE-BACKUP-RESTORE`.

---

## 2) Comandos ejecutados y resultado

1. Pruebas unitarias del modulo de backup/restore:

```powershell
pytest tests/test_backup_restore_supabase.py -q -p no:cacheprovider
```

Resultado: `5 passed`.

2. Validacion CLI:

```powershell
python scripts/backup_restore_supabase.py --help
```

Resultado: CLI disponible con comandos `backup` y `restore`.

3. Backup real de Supabase:

```powershell
python scripts/backup_restore_supabase.py backup --output-dir reports
```

Resultado:
- clientes: 199
- documentos: 231
- cobranzas: 165
- notificaciones: 0
- ledger_last_send: 33
- send_attempts: 35
- total_rows: 663
- backup generado en: `reports/supabase_backup_20260217_000304`

4. Restore en modo seguro (dry-run):

```powershell
python scripts/backup_restore_supabase.py restore --backup-dir C:\dev\ReporteCobranzas\reports\supabase_backup_20260217_000304 --truncate
```

Resultado:
- Plan de truncado y restauracion generado correctamente.
- Sin cambios aplicados (dry-run).

5. Restore validado contra Supabase (apply sin truncate, con integridad):

```powershell
python scripts/backup_restore_supabase.py restore --backup-dir C:\dev\ReporteCobranzas\reports\supabase_backup_20260217_000304 --apply --integrity-check
```

Resultado:
- Restore aplicado exitosamente.
- Integridad post-restore:
  - `orphan_count: 0`
- Ajuste defensivo activo:
  - `ledger_last_send` uso fallback `insert_missing` por trigger inconsistente de `updated_at`.
  - `send_attempts` se restaura como append-only (`insert_missing`) para evitar updates sobre historial.

6. Runner consolidado de quality gates:

```powershell
python scripts/run_migration_quality_gates.py
```

Resultado: `RESULTADO: PASS`.

---

## 3) Entregables

1. `scripts/backup_restore_supabase.py`
2. `tests/test_backup_restore_supabase.py`
3. `docs/EVIDENCIA_BACKUP_RESTORE_SUPABASE_MIG009.md`
4. Actualizacion de backlog en `docs/backlog_priorizado.md`

---

Estado del ticket: `COMPLETADO`.
