from types import SimpleNamespace

import pandas as pd

import utils.db_manager as dbm


class _FakeTableClientes:
    def __init__(self, rows, sinks):
        self.rows = rows
        self.sinks = sinks
        self.query = {}
        self.payload = None
        self.upsert_payload = None
        self.delete_flag = False

    def select(self, fields):
        self.query["select"] = fields
        return self

    def order(self, field):
        self.query["order"] = field
        return self

    def limit(self, value):
        self.query["limit"] = value
        return self

    def update(self, payload):
        self.payload = payload
        return self

    def upsert(self, payload, on_conflict=None):
        self.upsert_payload = payload
        self.query["on_conflict"] = on_conflict
        return self

    def delete(self):
        self.delete_flag = True
        return self

    def eq(self, field, value):
        self.query[field] = value
        return self

    def in_(self, field, value):
        self.query[field] = value
        return self

    def execute(self):
        if self.payload is not None:
            self.sinks["updates"].append({"payload": self.payload, "query": dict(self.query)})
            return SimpleNamespace(data=[{"ok": True}])
        if self.upsert_payload is not None:
            self.sinks["upserts"].append({"payload": self.upsert_payload, "query": dict(self.query)})
            return SimpleNamespace(data=list(self.upsert_payload))
        if self.delete_flag:
            self.sinks["deletes"].append({"query": dict(self.query)})
            return SimpleNamespace(data=[{"deleted": True}])
        return SimpleNamespace(data=self.rows)


class _FakeClient:
    def __init__(self, rows, sinks):
        self.rows = rows
        self.sinks = sinks

    def table(self, name):
        assert name == "clientes"
        return _FakeTableClientes(self.rows, self.sinks)


class _FakeLegacyMissingColumnsTable(_FakeTableClientes):
    def execute(self):
        if self.upsert_payload is not None:
            self.sinks["upserts"].append({"payload": self.upsert_payload, "query": dict(self.query)})
            keys = set()
            for row in self.upsert_payload:
                keys.update(row.keys())
            if "enviar_email" in keys:
                raise Exception("Could not find the 'enviar_email' column of 'clientes' in the schema cache")
            if "extra_fields" in keys:
                raise Exception("Could not find the 'extra_fields' column of 'clientes' in the schema cache")
            return SimpleNamespace(data=list(self.upsert_payload))
        return super().execute()


class _FakeLegacyMissingColumnsClient(_FakeClient):
    def table(self, name):
        assert name == "clientes"
        return _FakeLegacyMissingColumnsTable(self.rows, self.sinks)


def _make_state(rows):
    return {
        "rows": rows,
        "sinks": {
            "updates": [],
            "upserts": [],
            "deletes": [],
        },
    }


def test_list_clientes_for_admin_filters_by_search(monkeypatch):
    state = _make_state(
        [
            {"cliente_id": "000001", "nombre": "ACME SAC", "email": "acme@x.com"},
            {"cliente_id": "000002", "nombre": "BETA SAC", "email": "beta@x.com"},
        ]
    )
    monkeypatch.setattr(
        dbm,
        "get_supabase_client",
        lambda: _FakeClient(state["rows"], state["sinks"]),
    )

    result = dbm.list_clientes_for_admin(search="acme", limit=100)
    assert len(result) == 1
    assert result[0]["cliente_id"] == "000001"


def test_update_cliente_fields_rejects_invalid_estado():
    ok, msg = dbm.update_cliente_fields(cliente_id="000001", estado="DESCONOCIDO")
    assert ok is False
    assert "estado invalido" in msg


def test_update_cliente_fields_accepts_full_payload(monkeypatch):
    state = _make_state([])
    monkeypatch.setattr(
        dbm,
        "get_supabase_client",
        lambda: _FakeClient(state["rows"], state["sinks"]),
    )

    ok, msg = dbm.update_cliente_fields(
        cliente_id="000010",
        nombre="Cliente 10",
        email="CLIENTE@MAIL.COM",
        telefono="999111222",
        ruc="20123456789",
        direccion="Lima",
        estado="activo",
        notas="VIP",
    )

    assert ok is True
    assert "actualizado" in msg.lower()
    assert len(state["sinks"]["updates"]) == 1
    payload = state["sinks"]["updates"][0]["payload"]
    assert payload["nombre"] == "Cliente 10"
    assert payload["email"] == "cliente@mail.com"
    assert payload["telefono"] == "999111222"
    assert payload["ruc"] == "20123456789"
    assert payload["direccion"] == "Lima"
    assert payload["estado"] == "ACTIVO"
    assert payload["notas"] == "VIP"


def test_get_clientes_master_returns_rows(monkeypatch):
    state = _make_state(
        [
            {"cliente_id": "000001", "nombre": "ACME SAC", "email": "acme@x.com"},
            {"cliente_id": "000002", "nombre": "BETA SAC", "email": "beta@x.com"},
        ]
    )
    monkeypatch.setattr(
        dbm,
        "get_supabase_client",
        lambda: _FakeClient(state["rows"], state["sinks"]),
    )

    result = dbm.get_clientes_master(limit=1000)
    assert len(result) == 2
    assert result[0]["cliente_id"] == "000001"


def test_list_clientes_full_reads_enviar_email_from_legacy_notas(monkeypatch):
    state = _make_state(
        [
            {
                "cliente_id": "000023",
                "nombre": "ALMACO PERU SAC",
                "notas": '[EXTRA_FIELDS]{"enviar_email":"SI","dni":"12345678","empresa":"1"}',
            }
        ]
    )
    monkeypatch.setattr(
        dbm,
        "get_supabase_client",
        lambda: _FakeClient(state["rows"], state["sinks"]),
    )

    result = dbm.list_clientes_full(search="", estado="", limit=100)
    assert len(result) == 1
    assert result[0]["enviar_email"] == "SI"
    assert result[0]["dni"] == "12345678"
    assert result[0]["notas"] == ""


def test_upsert_clientes_rows_normalizes_email_and_estado(monkeypatch):
    state = _make_state([])
    monkeypatch.setattr(
        dbm,
        "get_supabase_client",
        lambda: _FakeClient(state["rows"], state["sinks"]),
    )

    ok, msg = dbm.upsert_clientes_rows(
        [
            {
                "cliente_id": "10",
                "nombre": "Cliente 10",
                "email": "CLIENTE@MAIL.COM",
                "estado": "a",
            }
        ]
    )

    assert ok is True
    assert "guardados" in msg.lower()
    assert len(state["sinks"]["upserts"]) == 1
    payload = state["sinks"]["upserts"][0]["payload"][0]
    assert payload["cliente_id"] == "000010"
    assert payload["email"] == "cliente@mail.com"
    assert payload["estado"] == "ACTIVO"


def test_upsert_clientes_rows_retries_when_schema_is_legacy(monkeypatch):
    state = _make_state([])
    monkeypatch.setattr(
        dbm,
        "get_supabase_client",
        lambda: _FakeLegacyMissingColumnsClient(state["rows"], state["sinks"]),
    )

    ok, msg = dbm.upsert_clientes_rows(
        [
            {
                "cliente_id": "11",
                "nombre": "Cliente 11",
                "enviar_email": "SI",
                "notas": "VIP",
            }
        ]
    )

    assert ok is True
    assert "guardados" in msg.lower()
    assert len(state["sinks"]["upserts"]) == 3
    final_payload = state["sinks"]["upserts"][-1]["payload"][0]
    assert "enviar_email" not in final_payload
    assert "extra_fields" not in final_payload
    assert "[EXTRA_FIELDS]" in (final_payload.get("notas") or "")
    assert '"enviar_email": "SI"' in (final_payload.get("notas") or "")


def test_delete_clientes_by_ids_uses_in_filter(monkeypatch):
    state = _make_state([])
    monkeypatch.setattr(
        dbm,
        "get_supabase_client",
        lambda: _FakeClient(state["rows"], state["sinks"]),
    )

    ok, msg = dbm.delete_clientes_by_ids(["1", "2"])
    assert ok is True
    assert "eliminados" in msg.lower()
    assert len(state["sinks"]["deletes"]) == 1
    query = state["sinks"]["deletes"][0]["query"]
    assert query["cliente_id"] == ["000001", "000002"]


def test_migrate_clientes_from_cartera_df_calls_upsert(monkeypatch):
    state = _make_state([])
    monkeypatch.setattr(
        dbm,
        "get_supabase_client",
        lambda: _FakeClient(state["rows"], state["sinks"]),
    )

    df_cartera = pd.DataFrame(
        [
            {
                "codigo_cliente": 1,
                "nombre_cliente": "ACME SAC",
                "email": "acme@x.com",
                "telefono": "999111222",
            }
        ]
    )

    result = dbm.migrate_clientes_from_cartera_df(df_cartera)
    assert result["ok"] is True
    assert result["counts"]["rows"] >= 1
    assert len(state["sinks"]["upserts"]) >= 1
