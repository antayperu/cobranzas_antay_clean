from unittest.mock import patch

import pandas as pd

import utils.supabase_cycle_service as cycle_service


class DummySupabaseWrapperUnavailable:
    def is_available(self):
        return False

    def get_client(self):
        return None


class DummySupabaseWrapperAvailable:
    def __init__(self, client):
        self._client = client

    def is_available(self):
        return True

    def get_client(self):
        return self._client


def _dummy_rows():
    clientes = [{"cliente_id": "000001", "nombre": "Cliente 1"}]
    documentos = [{"documento_id": "D-1", "cliente_id": "000001"}]
    doc_lookup = {"K1": {"documento_id": "D-1", "cliente_id": "000001"}}
    cobranzas = [{"id": "C-1", "documento_id": "D-1", "cliente_id": "000001"}]
    return clientes, documentos, doc_lookup, cobranzas


def test_persist_cycle_fails_when_supabase_unavailable():
    df = pd.DataFrame([{"x": 1}])
    clientes, documentos, doc_lookup, cobranzas = _dummy_rows()

    with (
        patch.object(cycle_service, "build_clientes", return_value=(clientes, [])),
        patch.object(cycle_service, "build_documentos", return_value=(documentos, [], doc_lookup)),
        patch.object(cycle_service, "build_cobranzas", return_value=(cobranzas, [])),
        patch.object(cycle_service.SupabaseClient, "get_instance", return_value=DummySupabaseWrapperUnavailable()),
    ):
        result = cycle_service.persist_cycle_to_supabase(df, df, df)

    assert result["ok"] is False
    assert "Supabase no disponible" in result["message"]


def test_persist_cycle_success_writes_all_tables():
    df = pd.DataFrame([{"x": 1}])
    clientes, documentos, doc_lookup, cobranzas = _dummy_rows()
    client = object()

    with (
        patch.object(cycle_service, "build_clientes", return_value=(clientes, [])),
        patch.object(cycle_service, "build_documentos", return_value=(documentos, [], doc_lookup)),
        patch.object(cycle_service, "build_cobranzas", return_value=(cobranzas, [])),
        patch.object(cycle_service.SupabaseClient, "get_instance", return_value=DummySupabaseWrapperAvailable(client)),
        patch.object(cycle_service, "upsert_records", side_effect=[1, 1, 1]) as upsert_mock,
    ):
        result = cycle_service.persist_cycle_to_supabase(df, df, df)

    assert result["ok"] is True
    assert result["counts"]["clientes"] == 1
    assert result["counts"]["documentos"] == 1
    assert result["counts"]["cobranzas"] == 1
    assert upsert_mock.call_count == 3


def test_persist_cycle_returns_controlled_error_when_data_prep_fails():
    df = pd.DataFrame([{"x": 1}])

    with (
        patch.object(cycle_service, "build_clientes", side_effect=RuntimeError("boom")),
    ):
        result = cycle_service.persist_cycle_to_supabase(df, df, df)

    assert result["ok"] is False
    assert "Error preparando datos para persistencia" in result["message"]


def test_persist_cycle_accepts_legacy_document_builder_shape():
    df = pd.DataFrame([{"x": 1}])
    clientes, documentos, _, cobranzas = _dummy_rows()
    client = object()

    with (
        patch.object(cycle_service, "build_clientes", return_value=(clientes, [])),
        patch.object(cycle_service, "build_documentos", return_value=(documentos, [])),
        patch.object(cycle_service, "build_cobranzas", return_value=(cobranzas, [])),
        patch.object(cycle_service.SupabaseClient, "get_instance", return_value=DummySupabaseWrapperAvailable(client)),
        patch.object(cycle_service, "upsert_records", side_effect=[1, 1, 1]) as upsert_mock,
    ):
        result = cycle_service.persist_cycle_to_supabase(df, df, df)

    assert result["ok"] is True
    assert result["counts"]["clientes"] == 1
    assert result["counts"]["documentos"] == 1
    assert result["counts"]["cobranzas"] == 1
    assert upsert_mock.call_count == 3
