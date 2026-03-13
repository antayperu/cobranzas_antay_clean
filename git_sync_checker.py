#!/usr/bin/env python3
"""
Script de validación de sincronización Git - ReporteCobranzas
Verifica que dev y main estén sincronizadas según metodología Antay.

Uso:
    python git_sync_checker.py
    python git_sync_checker.py --fix    (auto-sincronizar si hay diferencia)
    python git_sync_checker.py --status (solo mostrar status sin acciones)
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

class GitSyncChecker:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.status = {
            "main_commit": None,
            "dev_commit": None,
            "synchronized": False,
            "issues": []
        }
    
    def run_git(self, cmd: str) -> str:
        """Ejecutar comando git y retornar output."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path)] + cmd.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0 and result.stderr:
                raise RuntimeError(result.stderr)
            return result.stdout.strip()
        except Exception as e:
            print(f"ERROR ejecutando git: {e}")
            sys.exit(1)
    
    def get_current_branch(self) -> str:
        """Obtener rama actual."""
        return self.run_git("rev-parse --abbrev-ref HEAD")
    
    def get_commit_hash(self, branch: str) -> str:
        """Obtener hash del commit actual de una rama."""
        try:
            return self.run_git(f"rev-parse {branch}")[:7]  # Short hash
        except:
            return "UNKNOWN"
    
    def check_synchronization(self) -> bool:
        """Verificar si main y dev están sincronizadas."""
        main_commit = self.get_commit_hash("main")
        dev_commit = self.get_commit_hash("dev")
        
        self.status["main_commit"] = main_commit
        self.status["dev_commit"] = dev_commit
        self.status["synchronized"] = (main_commit == dev_commit)
        
        return self.status["synchronized"]
    
    def check_uncommitted_changes(self) -> bool:
        """Verificar si hay cambios no committeados."""
        status = self.run_git("status --porcelain")
        if status:
            self.status["issues"].append("WARN: Cambios no committeados locales")
            return True
        return False
    
    def check_branch_protection(self) -> bool:
        """Verificar que no hay force-push permitido."""
        # Este check sería mejor en GitHub API, aquí solo validamos local
        try:
            config = self.run_git("config --get-all branch.main.pushRemote")
            if not config:
                self.status["issues"].append("WARN: Configuración de push en main no clara")
                return False
            return True
        except:
            return True  # No es bloqueante
    
    def check_rollback_commit(self) -> bool:
        """Verificar que el commit de rollback está documentado."""
        try:
            log = self.run_git("log --oneline -30")
            if "2e93afd" in log:  # Commit de Playwright
                return True
            else:
                self.status["issues"].append("WARN: No encontrado commit 2e93afd (Playwright)")
                return False
        except:
            return False
    
    def display_status(self):
        """Mostrar status en formato legible."""
        print("\n" + "="*70)
        print("GIT SYNC STATUS - ReporteCobranzas")
        print("="*70)
        
        # Status principal
        sync_symbol = "✅" if self.status["synchronized"] else "❌"
        print(f"\n[{sync_symbol}] SINCRONIZACION: ", end="")
        if self.status["synchronized"]:
            print(f"OK (main={self.status['main_commit']}, dev={self.status['dev_commit']})")
        else:
            print(f"DESINCRONIZADA")
            print(f"    main: {self.status['main_commit']}")
            print(f"    dev:  {self.status['dev_commit']}")
        
        # Rama actual
        current = self.get_current_branch()
        print(f"\n[INFO] Rama actual: {current}")
        
        # Issues
        if self.status["issues"]:
            print("\n[⚠️  ] WARNINGS/ISSUES:")
            for issue in self.status["issues"]:
                print(f"    * {issue}")
        else:
            print("\n[✅] Sin issues detectados")
        
        # Documentación
        print("\n[📄] Documentación:")
        files_to_check = [
            "GIT_WORKFLOW_ANTAY_OFFICIAL.md",
            "GIT_SYNC_STATUS_VERIFICADO.md"
        ]
        for f in files_to_check:
            exists = (self.repo_path / f).exists()
            symbol = "✅" if exists else "❌"
            print(f"    {symbol} {f}")
        
        print("\n" + "="*70)
    
    def sync_dev_with_main(self) -> bool:
        """Auto-sincronizar dev con main."""
        try:
            current = self.get_current_branch()
            
            print("\n[SYNC] Iniciando sincronización dev con main...")
            
            # 1. Ir a dev
            print("  1. Cambiando a rama dev...")
            self.run_git("checkout dev")
            
            # 2. Merge main en dev
            print("  2. Haciendo merge de main en dev...")
            merge_msg = """merge(sync): Sincronizar dev con cambios de main [Auto]

SYNC AUTOMÁTICO: main fue integrado en dev.
Verificar que todos los archivos están correctos."""
            
            self.run_git(f"merge main -m '{merge_msg}'")
            
            # 3. Validar
            self.check_synchronization()
            if self.status["synchronized"]:
                print("  ✅ Sincronización exitosa!")
                print(f"  Ambas ramas en commit: {self.status['main_commit']}")
                return True
            else:
                print("  ❌ Sincronización falló!")
                return False
                
        except Exception as e:
            print(f"  ❌ Error durante sincronización: {e}")
            return False
    
    def run_all_checks(self) -> int:
        """Ejecutar todos los checks y retornar código de salida."""
        checks = [
            ("Sincronización dev/main", self.check_synchronization),
            ("Cambios sin commitear", lambda: not self.check_uncommitted_changes()),
            ("Commit Playwright documentado", self.check_rollback_commit),
        ]
        
        all_ok = True
        for check_name, check_fn in checks:
            try:
                result = check_fn()
                symbol = "✅" if result else "⚠️ "
                # print(f"  {symbol} {check_name}")
                if not result:
                    all_ok = False
            except Exception as e:
                print(f"  ❌ {check_name}: {e}")
                all_ok = False
        
        return 0 if all_ok else 1

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validador de sincronización Git - ReporteCobranzas"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-sincronizar dev con main si está desincronizada"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Solo mostrar status (no hacer cambios)"
    )
    
    args = parser.parse_args()
    
    checker = GitSyncChecker()
    
    # Ejecutar checks
    checker.run_all_checks()
    
    # Mostrar status
    checker.display_status()
    
    # Auto-fix si se solicita
    if args.fix and not checker.status["synchronized"]:
        print("\n[AUTO-FIX] Intentando sincronizar...")
        if checker.sync_dev_with_main():
            checker.display_status()
            print("\n✅ Sincronización completada exitosamente")
            return 0
        else:
            print("\n❌ Error durante sincronización automática")
            return 1
    
    # Retornar código de salida
    return 0 if checker.status["synchronized"] else 1

if __name__ == "__main__":
    sys.exit(main())
