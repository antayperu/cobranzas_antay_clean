"""
Backup and restore utilities for Supabase operational tables.

Scope:
- clientes
- documentos
- cobranzas
- notificaciones
- ledger_last_send
- send_attempts

Usage examples:
    python scripts/backup_restore_supabase.py backup --output-dir backups
    python scripts/backup_restore_supabase.py restore --backup-dir backups/supabase_backup_20260217_120000
    python scripts/backup_restore_supabase.py restore --backup-dir backups/supabase_backup_20260217_120000 --apply --truncate
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple
from uuid import UUID

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.supabase_client import SupabaseClient

try:
    from postgrest.exceptions import APIError
except Exception:  # pragma: no cover - defensive import
    APIError = Exception


@dataclass(frozen=True)
class TableSpec:
    name: str
    conflict_key: str
    restore_order: int
    truncate_order: int
    restore_mode: str = "upsert"


TABLE_SPECS: List[TableSpec] = [
    TableSpec(name="clientes", conflict_key="cliente_id", restore_order=10, truncate_order=60),
    TableSpec(name="documentos", conflict_key="documento_id", restore_order=20, truncate_order=50),
    TableSpec(name="cobranzas", conflict_key="id", restore_order=30, truncate_order=40),
    TableSpec(name="notificaciones", conflict_key="id", restore_order=40, truncate_order=30),
    TableSpec(name="ledger_last_send", conflict_key="ledger_key", restore_order=50, truncate_order=20),
    # send_attempts is append-only by design; restore avoids updates on existing rows.
    TableSpec(name="send_attempts", conflict_key="id", restore_order=60, truncate_order=10, restore_mode="insert_missing"),
]


def chunked(items: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def normalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): normalize_for_hash(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [normalize_for_hash(v) for v in value]
    if isinstance(value, tuple):
        return [normalize_for_hash(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def stable_rows_hash(rows: Sequence[Dict[str, Any]], key_name: str) -> str:
    normalized_rows = [normalize_for_hash(row) for row in rows]
    ordered_rows = sorted(
        normalized_rows,
        key=lambda row: str(row.get(key_name, json.dumps(row, sort_keys=True, ensure_ascii=False))),
    )
    payload = json.dumps(ordered_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def find_spec(table_name: str) -> TableSpec:
    for spec in TABLE_SPECS:
        if spec.name == table_name:
            return spec
    raise ValueError(f"Unknown table: {table_name}")


def select_specs(tables_filter: str) -> List[TableSpec]:
    if not tables_filter:
        return list(TABLE_SPECS)
    wanted = {item.strip() for item in tables_filter.split(",") if item.strip()}
    selected = [spec for spec in TABLE_SPECS if spec.name in wanted]
    missing = wanted - {spec.name for spec in selected}
    if missing:
        raise ValueError(f"Unknown table names in --tables: {', '.join(sorted(missing))}")
    return selected


def fetch_table_rows(supabase, table_name: str, page_size: int = 1000) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    start = 0
    while True:
        end = start + page_size - 1
        res = supabase.table(table_name).select("*").range(start, end).execute()
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return rows


def fetch_primary_keys(supabase, spec: TableSpec, page_size: int = 1000) -> List[Any]:
    values: List[Any] = []
    start = 0
    while True:
        end = start + page_size - 1
        res = supabase.table(spec.name).select(spec.conflict_key).range(start, end).execute()
        batch = res.data or []
        for row in batch:
            value = row.get(spec.conflict_key)
            if value is not None:
                values.append(value)
        if len(batch) < page_size:
            break
        start += page_size
    return values


def delete_table_rows(supabase, spec: TableSpec, page_size: int = 1000, delete_batch_size: int = 500) -> int:
    deleted = 0
    while True:
        keys = fetch_primary_keys(supabase, spec=spec, page_size=page_size)
        if not keys:
            break
        for key_chunk in chunked(keys, delete_batch_size):
            supabase.table(spec.name).delete().in_(spec.conflict_key, list(key_chunk)).execute()
            deleted += len(key_chunk)
    return deleted


def upsert_rows(supabase, spec: TableSpec, rows: Sequence[Dict[str, Any]], batch_size: int = 200) -> int:
    total = 0
    for batch in chunked(list(rows), batch_size):
        supabase.table(spec.name).upsert(list(batch), on_conflict=spec.conflict_key).execute()
        total += len(batch)
    return total


def insert_missing_rows(
    supabase,
    spec: TableSpec,
    rows: Sequence[Dict[str, Any]],
    page_size: int = 1000,
    batch_size: int = 200,
) -> Tuple[int, int]:
    existing = set(fetch_primary_keys(supabase=supabase, spec=spec, page_size=page_size))
    pending: List[Dict[str, Any]] = []
    skipped = 0
    for row in rows:
        key_value = row.get(spec.conflict_key)
        if key_value in existing:
            skipped += 1
            continue
        pending.append(row)

    inserted = 0
    for batch in chunked(pending, batch_size):
        supabase.table(spec.name).insert(list(batch)).execute()
        inserted += len(batch)
    return inserted, skipped


def build_backup_manifest(
    table_rows: Dict[str, List[Dict[str, Any]]],
    table_specs: Sequence[TableSpec],
    started_at: str,
    finished_at: str,
) -> Dict[str, Any]:
    manifest_tables: Dict[str, Any] = {}
    total_rows = 0
    for spec in table_specs:
        rows = table_rows.get(spec.name, [])
        row_count = len(rows)
        total_rows += row_count
        manifest_tables[spec.name] = {
            "row_count": row_count,
            "conflict_key": spec.conflict_key,
            "sha256": stable_rows_hash(rows, spec.conflict_key),
            "file": f"{spec.name}.json",
        }
    return {
        "version": "1.0",
        "started_at": started_at,
        "finished_at": finished_at,
        "total_rows": total_rows,
        "tables": manifest_tables,
    }


def write_backup_bundle(
    output_root: Path,
    table_rows: Dict[str, List[Dict[str, Any]]],
    manifest: Dict[str, Any],
) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = output_root / f"supabase_backup_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    for table_name, rows in table_rows.items():
        table_file = backup_dir / f"{table_name}.json"
        table_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")

    manifest_file = backup_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return backup_dir


def load_backup_bundle(backup_dir: Path, table_specs: Sequence[TableSpec]) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    manifest_file = backup_dir / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"manifest.json not found in {backup_dir}")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    table_rows: Dict[str, List[Dict[str, Any]]] = {}
    for spec in table_specs:
        table_file = backup_dir / f"{spec.name}.json"
        if not table_file.exists():
            raise FileNotFoundError(f"{table_file.name} not found in {backup_dir}")
        rows = json.loads(table_file.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError(f"{table_file.name} must contain a JSON array")
        table_rows[spec.name] = rows

    return manifest, table_rows


def verify_backup_bundle(
    manifest: Dict[str, Any],
    table_rows: Dict[str, List[Dict[str, Any]]],
    table_specs: Sequence[TableSpec],
) -> List[str]:
    errors: List[str] = []
    manifest_tables = manifest.get("tables", {})
    for spec in table_specs:
        entry = manifest_tables.get(spec.name)
        if not entry:
            errors.append(f"manifest missing table: {spec.name}")
            continue
        rows = table_rows.get(spec.name, [])
        expected_count = int(entry.get("row_count", -1))
        current_count = len(rows)
        if expected_count != current_count:
            errors.append(f"{spec.name}: row_count mismatch manifest={expected_count} current={current_count}")

        expected_hash = str(entry.get("sha256", ""))
        current_hash = stable_rows_hash(rows, spec.conflict_key)
        if expected_hash != current_hash:
            errors.append(f"{spec.name}: sha256 mismatch")
    return errors


def build_restore_plan(
    table_rows: Dict[str, List[Dict[str, Any]]],
    truncate: bool,
    table_specs: Sequence[TableSpec] | None = None,
) -> List[Dict[str, Any]]:
    specs = list(table_specs or TABLE_SPECS)
    plan: List[Dict[str, Any]] = []
    if truncate:
        for spec in sorted(specs, key=lambda item: item.truncate_order):
            plan.append(
                {
                    "phase": "truncate",
                    "table": spec.name,
                    "rows": len(table_rows.get(spec.name, [])),
                }
            )
    for spec in sorted(specs, key=lambda item: item.restore_order):
        plan.append(
            {
                "phase": "restore",
                "table": spec.name,
                "rows": len(table_rows.get(spec.name, [])),
            }
        )
    return plan


def compute_orphan_document_ids(documento_ids: Sequence[str], cobranzas_documento_ids: Sequence[str]) -> List[str]:
    docs = {str(x).strip() for x in documento_ids if str(x).strip()}
    cobs = {str(x).strip() for x in cobranzas_documento_ids if str(x).strip()}
    return sorted(cobs - docs)


def run_integrity_check(supabase, page_size: int) -> Dict[str, Any]:
    doc_spec = find_spec("documentos")
    cob_spec = find_spec("cobranzas")
    documento_ids = fetch_primary_keys(supabase, spec=doc_spec, page_size=page_size)
    cobranza_documento_ids = fetch_primary_keys(supabase, spec=TableSpec("cobranzas", "documento_id", 0, 0), page_size=page_size)
    orphan_ids = compute_orphan_document_ids(documento_ids, cobranza_documento_ids)
    return {
        "documentos_distinct": len(set(documento_ids)),
        "cobranzas_distinct_documentos": len(set(cobranza_documento_ids)),
        "orphan_count": len(orphan_ids),
        "orphan_sample": orphan_ids[:10],
    }


def print_counts(title: str, table_rows: Dict[str, List[Dict[str, Any]]], table_specs: Sequence[TableSpec]) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
    total = 0
    for spec in table_specs:
        count = len(table_rows.get(spec.name, []))
        total += count
        print(f"- {spec.name}: {count}")
    print(f"- total_rows: {total}")


def get_supabase_client():
    wrapper = SupabaseClient.get_instance()
    if not wrapper.is_available():
        raise RuntimeError("Supabase no disponible. Verifica SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY.")
    return wrapper.get_client()


def run_backup(args: argparse.Namespace) -> int:
    table_specs = select_specs(args.tables)
    started_at = datetime.now().isoformat()
    supabase = get_supabase_client()

    table_rows: Dict[str, List[Dict[str, Any]]] = {}
    for spec in table_specs:
        rows = fetch_table_rows(supabase, table_name=spec.name, page_size=args.page_size)
        table_rows[spec.name] = rows

    finished_at = datetime.now().isoformat()
    manifest = build_backup_manifest(table_rows=table_rows, table_specs=table_specs, started_at=started_at, finished_at=finished_at)
    backup_dir = write_backup_bundle(output_root=Path(args.output_dir), table_rows=table_rows, manifest=manifest)

    print_counts("BACKUP SUMMARY", table_rows, table_specs)
    print(f"\nBackup directory: {backup_dir}")
    print("Manifest file:", backup_dir / "manifest.json")
    return 0


def run_restore(args: argparse.Namespace) -> int:
    table_specs = select_specs(args.tables)
    backup_dir = Path(args.backup_dir)
    if not backup_dir.exists():
        print(f"ERROR: backup directory not found: {backup_dir}")
        return 1

    manifest, table_rows = load_backup_bundle(backup_dir=backup_dir, table_specs=table_specs)
    verify_errors = verify_backup_bundle(manifest=manifest, table_rows=table_rows, table_specs=table_specs)
    if verify_errors:
        print("ERROR: backup verification failed:")
        for error in verify_errors:
            print(f"- {error}")
        return 1

    print_counts("RESTORE INPUT SUMMARY", table_rows, table_specs)
    plan = build_restore_plan(table_rows=table_rows, truncate=args.truncate, table_specs=table_specs)
    print("\nRestore plan:")
    for step in plan:
        print(f"- {step['phase']}: {step['table']} ({step['rows']} rows)")

    if not args.apply:
        print("\nDry-run completed. No changes were applied to Supabase.")
        return 0

    supabase = get_supabase_client()

    if args.truncate:
        print("\nTruncating target tables...")
        for spec in sorted(table_specs, key=lambda item: item.truncate_order):
            deleted = delete_table_rows(
                supabase=supabase,
                spec=spec,
                page_size=args.page_size,
                delete_batch_size=args.delete_batch_size,
            )
            print(f"- {spec.name}: deleted {deleted}")

    print("\nRestoring rows...")
    for spec in sorted(table_specs, key=lambda item: item.restore_order):
        rows = table_rows.get(spec.name, [])
        if spec.restore_mode == "insert_missing":
            inserted, skipped = insert_missing_rows(
                supabase=supabase,
                spec=spec,
                rows=rows,
                page_size=args.page_size,
                batch_size=args.batch_size,
            )
            print(f"- {spec.name}: inserted {inserted}, skipped_existing {skipped}")
            continue

        try:
            restored = upsert_rows(
                supabase=supabase,
                spec=spec,
                rows=rows,
                batch_size=args.batch_size,
            )
            print(f"- {spec.name}: restored {restored}")
        except APIError as exc:
            message = str(exc).lower()
            # Defensive fallback for environments with inconsistent update triggers.
            if "updated_at" in message and "has no field" in message:
                inserted, skipped = insert_missing_rows(
                    supabase=supabase,
                    spec=spec,
                    rows=rows,
                    page_size=args.page_size,
                    batch_size=args.batch_size,
                )
                print(
                    f"- {spec.name}: fallback insert_missing used; "
                    f"inserted {inserted}, skipped_existing {skipped}"
                )
            else:
                raise

    if args.integrity_check:
        integrity = run_integrity_check(supabase=supabase, page_size=args.page_size)
        print("\nINTEGRITY CHECK")
        print(f"- documentos_distinct: {integrity['documentos_distinct']}")
        print(f"- cobranzas_distinct_documentos: {integrity['cobranzas_distinct_documentos']}")
        print(f"- orphan_count: {integrity['orphan_count']}")
        if integrity["orphan_sample"]:
            print(f"- orphan_sample: {integrity['orphan_sample']}")
        if integrity["orphan_count"] > 0:
            print("ERROR: orphan records detected after restore.")
            return 2

    print("\nRestore applied successfully.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backup and restore utilities for Supabase.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create backup from Supabase tables")
    backup_parser.add_argument("--output-dir", default="backups", help="Directory where backup folder will be created")
    backup_parser.add_argument("--tables", default="", help="Comma-separated list of tables to include")
    backup_parser.add_argument("--page-size", type=int, default=1000, help="Pagination size for reads")

    restore_parser = subparsers.add_parser("restore", help="Restore backup into Supabase tables")
    restore_parser.add_argument("--backup-dir", required=True, help="Backup folder that contains manifest.json and table files")
    restore_parser.add_argument("--tables", default="", help="Comma-separated list of tables to restore")
    restore_parser.add_argument("--apply", action="store_true", help="Apply restore changes (default is dry-run)")
    restore_parser.add_argument("--truncate", action="store_true", help="Delete target data before restore")
    restore_parser.add_argument("--integrity-check", action="store_true", help="Run orphan integrity check after restore")
    restore_parser.add_argument("--page-size", type=int, default=1000, help="Pagination size for reads/deletes")
    restore_parser.add_argument("--batch-size", type=int, default=200, help="Batch size for upsert")
    restore_parser.add_argument("--delete-batch-size", type=int, default=500, help="Batch size for delete by PK")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "backup":
        return run_backup(args)
    if args.command == "restore":
        return run_restore(args)
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
