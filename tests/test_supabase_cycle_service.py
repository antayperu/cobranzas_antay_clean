from unittest.mock import patch

import pandas as pd

import utils.cycle_service as cycle_service


def _dummy_rows():
    clientes = [{"cliente_id": "000001", "nombre": "Cliente 1"}]
    documentos = [{"documento_id": "D-1", "cliente_id": "000001"}]
    doc_lookup = {"K1": {"documento_id": "D-1", "cliente_id": "000001"}}
    return clientes, documentos, doc_lookup


def test_persist_cycle_fails_when_db_unavailable():
    df = pd.DataFrame([{"x": 1}])
    clientes, documentos, doc_lookup = _dummy_rows()

    with (
        patch.object(cycle_service, "build_clientes", return_value=(clientes, [])),
        patch.object(cycle_service, "build_documentos", return_value=(documentos, [], doc_lookup)),
        patch.object(cycle_service.dbm, "get_db_client", return_value=None),
    ):
        result = cycle_service.persist_cycle_to_supabase(df, df, df)

    assert result["ok"] is False
    assert "Base de datos no disponible" in result["message"]


def test_persist_cycle_success_writes_all_tables():
    df = pd.DataFrame([{"x": 1}])
    clientes, documentos, doc_lookup = _dummy_rows()
    client = object()

    with (
        patch.object(cycle_service, "build_clientes", return_value=(clientes, [])),
        patch.object(cycle_service, "build_documentos", return_value=(documentos, [], doc_lookup)),
        patch.object(cycle_service.dbm, "get_db_client", return_value=client),
        patch.object(cycle_service.dbm, "upsert_clientes_rows", return_value=(True, "ok")) as upsert_clientes_mock,
        patch.object(cycle_service, "upsert_records", side_effect=[1]) as upsert_mock,
    ):
        result = cycle_service.persist_cycle_to_supabase(df, df, df)

    assert result["ok"] is True
    assert result["counts"]["clientes"] == 1
    assert result["counts"]["documentos"] == 1
    assert "cobranzas" not in result["counts"]
    assert upsert_clientes_mock.call_count == 1
    assert upsert_mock.call_count == 1


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
    clientes, documentos, _ = _dummy_rows()
    client = object()

    with (
        patch.object(cycle_service, "build_clientes", return_value=(clientes, [])),
        patch.object(cycle_service, "build_documentos", return_value=(documentos, [])),
        patch.object(cycle_service.dbm, "get_db_client", return_value=client),
        patch.object(cycle_service.dbm, "upsert_clientes_rows", return_value=(True, "ok")) as upsert_clientes_mock,
        patch.object(cycle_service, "upsert_records", side_effect=[1]) as upsert_mock,
    ):
        result = cycle_service.persist_cycle_to_supabase(df, df, df)

    assert result["ok"] is True
    assert result["counts"]["clientes"] == 1
    assert result["counts"]["documentos"] == 1
    assert "cobranzas" not in result["counts"]
    assert upsert_clientes_mock.call_count == 1
    assert upsert_mock.call_count == 1


def test_persist_cycle_returns_error_when_clientes_upsert_fails():
    df = pd.DataFrame([{"x": 1}])
    clientes, documentos, doc_lookup = _dummy_rows()
    client = object()

    with (
        patch.object(cycle_service, "build_clientes", return_value=(clientes, [])),
        patch.object(cycle_service, "build_documentos", return_value=(documentos, [], doc_lookup)),
        patch.object(cycle_service.dbm, "get_db_client", return_value=client),
        patch.object(cycle_service.dbm, "upsert_clientes_rows", return_value=(False, "No se pudo guardar clientes: PGRST204")),
    ):
        result = cycle_service.persist_cycle_to_supabase(df, df, df)

    assert result["ok"] is False
    assert "Error al guardar clientes" in result["message"]
