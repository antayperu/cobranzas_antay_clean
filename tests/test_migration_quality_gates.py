import json

import pandas as pd

from scripts.migrate_excel_to_supabase import (
    build_clientes,
    build_cobranzas,
    build_documentos,
)
import utils.supabase_cycle_service as cycle_service


def _sample_frames():
    df_ctas = pd.DataFrame(
        [
            {
                "codcli": 1,
                "coddoc": "FA",
                "sersun": "F001",
                "numsun": 1,
                "fecdoc": "2026-01-01",
                "fecvct": "2026-02-01",
                "mododo": 1000.0,
                "sldacl": 500.0,
                "codmnd": "SOLES",
            }
        ]
    )
    df_cartera = pd.DataFrame(
        [
            {
                "codigo_cliente": 1,
                "nombre": "Cliente Demo",
                "email": "cliente@demo.com",
                "telefono": "999000111",
                "estado": "ACTIVO",
            }
        ]
    )
    df_cobranza = pd.DataFrame(
        [
            {
                "coddoc": "FA",
                "numsun": "F001-00000001",
                "forpag": "DT",
                "fecpro": "2026-01-15",
                "monpag": 120.0,
                "nudopa": "OP-001",
                "numope": "NUM-001",
                "nombco": "BCP",
                "codbco": "002",
                "codven": "123",
                "codcli": "1",
                "nomcli": "Cliente Demo",
            }
        ]
    )
    return df_ctas, df_cartera, df_cobranza


def _rows_fingerprint(rows, sort_key):
    ordered = sorted(rows, key=lambda x: str(x.get(sort_key, "")))
    return [json.dumps(x, sort_keys=True, ensure_ascii=False) for x in ordered]


def test_idempotencia_builders_excel_to_rows():
    df_ctas, df_cartera, df_cobranza = _sample_frames()

    c1, ce1 = build_clientes(df_ctas, df_cartera)
    d1, de1, lookup1 = build_documentos(df_ctas, {x["cliente_id"] for x in c1})
    b1, be1 = build_cobranzas(df_cobranza, lookup1)

    c2, ce2 = build_clientes(df_ctas, df_cartera)
    d2, de2, lookup2 = build_documentos(df_ctas, {x["cliente_id"] for x in c2})
    b2, be2 = build_cobranzas(df_cobranza, lookup2)

    assert ce1 == ce2
    assert de1 == de2
    assert be1 == be2
    assert _rows_fingerprint(c1, "cliente_id") == _rows_fingerprint(c2, "cliente_id")
    assert _rows_fingerprint(d1, "documento_id") == _rows_fingerprint(d2, "documento_id")
    assert _rows_fingerprint(b1, "id") == _rows_fingerprint(b2, "id")


def test_integridad_fk_rows_cobranzas_vs_documentos():
    df_ctas, df_cartera, df_cobranza = _sample_frames()
    clientes_rows, _ = build_clientes(df_ctas, df_cartera)
    documentos_rows, _, lookup = build_documentos(df_ctas, {x["cliente_id"] for x in clientes_rows})
    cobranzas_rows, _ = build_cobranzas(df_cobranza, lookup)

    documento_ids = {x["documento_id"] for x in documentos_rows}
    assert len(cobranzas_rows) > 0
    assert all(x["documento_id"] in documento_ids for x in cobranzas_rows)


def test_cloud_only_policy_blocks_when_supabase_unavailable(monkeypatch):
    class _Unavailable:
        def is_available(self):
            return False

        def get_client(self):
            return None

    monkeypatch.setattr(cycle_service.SupabaseClient, "get_instance", lambda: _Unavailable())
    df_ctas, df_cartera, df_cobranza = _sample_frames()
    result = cycle_service.persist_cycle_to_supabase(df_ctas, df_cartera, df_cobranza)

    assert result["ok"] is False
    assert "Supabase no disponible" in result["message"]
