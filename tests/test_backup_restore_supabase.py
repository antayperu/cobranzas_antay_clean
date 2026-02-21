import json

from scripts.backup_restore_supabase import (
    TABLE_SPECS,
    build_backup_manifest,
    build_restore_plan,
    compute_orphan_document_ids,
    stable_rows_hash,
    verify_backup_bundle,
)


def _sample_table_rows():
    return {
        "app_config": [
            {"config_key": "global", "payload": {"company_name": "Demo Co"}},
        ],
        "clientes": [
            {"cliente_id": "000001", "nombre": "Cliente A", "estado": "ACTIVO"},
            {"cliente_id": "000002", "nombre": "Cliente B", "estado": "MOROSO"},
        ],
        "documentos": [
            {"documento_id": "DOC-1", "cliente_id": "000001"},
            {"documento_id": "DOC-2", "cliente_id": "000002"},
        ],
        "cobranzas": [
            {"id": "COB-1", "documento_id": "DOC-1", "cliente_id": "000001"},
        ],
        "notificaciones": [
            {"id": "NOTIF-1", "cliente_id": "000001", "estado": "ENVIADO"},
        ],
        "ledger_last_send": [
            {"ledger_key": "K1", "send_count": 2},
        ],
        "send_attempts": [
            {"id": 1, "ledger_key": "K1", "status": "SENT"},
        ],
    }


def test_stable_rows_hash_is_deterministic_even_if_order_changes():
    rows_a = [
        {"cliente_id": "000002", "nombre": "B"},
        {"cliente_id": "000001", "nombre": "A"},
    ]
    rows_b = list(reversed(rows_a))

    hash_a = stable_rows_hash(rows_a, "cliente_id")
    hash_b = stable_rows_hash(rows_b, "cliente_id")
    assert hash_a == hash_b


def test_build_manifest_and_verify_bundle_ok():
    table_rows = _sample_table_rows()
    manifest = build_backup_manifest(
        table_rows=table_rows,
        table_specs=TABLE_SPECS,
        started_at="2026-02-17T10:00:00",
        finished_at="2026-02-17T10:00:10",
    )
    errors = verify_backup_bundle(manifest=manifest, table_rows=table_rows, table_specs=TABLE_SPECS)

    assert errors == []
    assert manifest["total_rows"] == 9
    assert manifest["tables"]["clientes"]["row_count"] == 2


def test_verify_bundle_detects_row_count_and_hash_mismatch():
    table_rows = _sample_table_rows()
    manifest = build_backup_manifest(
        table_rows=table_rows,
        table_specs=TABLE_SPECS,
        started_at="2026-02-17T10:00:00",
        finished_at="2026-02-17T10:00:10",
    )

    table_rows["clientes"].append({"cliente_id": "000003", "nombre": "Cliente C"})
    errors = verify_backup_bundle(manifest=manifest, table_rows=table_rows, table_specs=TABLE_SPECS)

    serialized = json.dumps(errors, ensure_ascii=False)
    assert "clientes: row_count mismatch" in serialized
    assert "clientes: sha256 mismatch" in serialized


def test_build_restore_plan_orders_truncate_then_restore():
    table_rows = _sample_table_rows()
    plan = build_restore_plan(table_rows=table_rows, truncate=True)

    truncate_steps = [step for step in plan if step["phase"] == "truncate"]
    restore_steps = [step for step in plan if step["phase"] == "restore"]

    assert len(truncate_steps) == len(TABLE_SPECS)
    assert len(restore_steps) == len(TABLE_SPECS)
    assert plan[0]["phase"] == "truncate"
    assert plan[-1]["phase"] == "restore"
    assert restore_steps[0]["table"] == "app_config"
    assert restore_steps[1]["table"] == "clientes"


def test_compute_orphan_document_ids_returns_only_unmatched_values():
    documento_ids = ["DOC-1", "DOC-2", "DOC-2", " "]
    cobranza_doc_ids = ["DOC-2", "DOC-3", "DOC-4", ""]
    orphan_ids = compute_orphan_document_ids(documento_ids, cobranza_doc_ids)
    assert orphan_ids == ["DOC-3", "DOC-4"]
