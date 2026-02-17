from pathlib import Path

import pandas as pd

from scripts.migrate_excel_to_supabase import (
    collect_no_match_rows,
    compute_orphan_document_ids,
    write_no_match_reports,
)


def test_compute_orphan_document_ids_returns_difference_sorted():
    docs = ["D-1", "D-2", "D-3"]
    cobs = ["D-2", "D-4", "D-5", "D-4"]

    orphan_ids = compute_orphan_document_ids(docs, cobs)
    assert orphan_ids == ["D-4", "D-5"]


def test_collect_no_match_rows_detects_unmatched_records():
    df = pd.DataFrame(
        [
            {"coddoc": "FA", "numsun": "F001-00000001", "codcli": "1", "nomcli": "ACME", "forpag": "DT"},
            {"coddoc": "FA", "numsun": "F001-00000002", "codcli": "2", "nomcli": "BETA", "forpag": "DT"},
        ]
    )
    doc_lookup = {
        "FAF00100000001": {"documento_id": "DOC-1", "cliente_id": "000001"},
    }

    no_match = collect_no_match_rows(df, doc_lookup)

    assert len(no_match) == 1
    assert no_match[0]["fila_excel"] == 2
    assert no_match[0]["lookup_key"] == "FAF00100000002"
    assert no_match[0]["reason"] == "sin_match_documento"


def test_collect_no_match_rows_respects_max_rows():
    df = pd.DataFrame(
        [
            {"coddoc": "FA", "numsun": f"F001-0000000{i}"} for i in range(1, 6)
        ]
    )
    no_match = collect_no_match_rows(df, doc_lookup={}, max_rows=2)
    assert len(no_match) == 2


def test_write_no_match_reports_creates_csv_and_json(tmp_path: Path):
    rows = [
        {
            "fila_excel": 10,
            "reason": "sin_match_documento",
            "lookup_key": "FAF00100000010",
            "coddoc": "FA",
            "numsun": "F001-00000010",
        }
    ]

    paths = write_no_match_reports(rows, tmp_path)

    assert paths["csv"].exists()
    assert paths["json"].exists()
    csv_content = paths["csv"].read_text(encoding="utf-8-sig")
    assert "sin_match_documento" in csv_content
