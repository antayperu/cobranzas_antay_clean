"""
Setup buckets for Supabase Storage.

Buckets:
- logos
- exports
- whatsapp-images
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import utils.storage_manager as storage_mgr


def main() -> int:
    print("=" * 72)
    print("SUPABASE STORAGE SETUP")
    print("=" * 72)
    try:
        results = storage_mgr.ensure_default_buckets()
    except Exception as exc:
        print(f"ERROR: No se pudo configurar buckets: {exc}")
        return 1

    for bucket_name, info in results.items():
        status = "CREATED" if info.get("created") else "OK"
        print(f"- {bucket_name}: {status}")

    print("=" * 72)
    print("Storage setup completado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

