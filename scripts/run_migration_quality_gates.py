"""
Runner de Quality Gates de migracion Supabase.

Ejecuta suites enfocadas en:
- Paridad export
- Integridad FK / no-match
- Idempotencia de cargas
- Politica cloud-only (bloqueo controlado)
"""

from __future__ import annotations

import subprocess
import sys
from typing import List, Tuple


GATES: List[Tuple[str, List[str]]] = [
    (
        "GATE-PARIDAD",
        [
            "tests/test_export_parity.py",
            "tests/test_processing_calculation_parity.py",
        ],
    ),
    (
        "GATE-INTEGRIDAD",
        [
            "tests/test_migration_integrity.py",
        ],
    ),
    (
        "GATE-IDEMPOTENCIA-CLOUD",
        [
            "tests/test_migration_quality_gates.py",
            "tests/test_supabase_cycle_service.py::test_persist_cycle_fails_when_supabase_unavailable",
        ],
    ),
    (
        "GATE-BACKUP-RESTORE",
        [
            "tests/test_backup_restore_supabase.py",
        ],
    ),
    (
        "GATE-STORAGE",
        [
            "tests/test_storage_manager.py",
        ],
    ),
]


def run_gate(gate_name: str, tests: List[str]) -> int:
    print(f"\n{'=' * 72}")
    print(f"{gate_name}")
    print(f"{'=' * 72}")
    cmd = [sys.executable, "-m", "pytest", *tests, "-q", "-p", "no:cacheprovider"]
    print("Comando:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode


def main() -> int:
    failed = []
    for gate_name, tests in GATES:
        rc = run_gate(gate_name, tests)
        if rc != 0:
            failed.append(gate_name)

    print(f"\n{'=' * 72}")
    if failed:
        print("RESULTADO: FAIL")
        print("Gates fallidos:", ", ".join(failed))
        return 1
    print("RESULTADO: PASS")
    print("Todos los quality gates de migracion pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
