from types import SimpleNamespace

import utils.db_manager as dbm


class _FakeTableClientes:
    def __init__(self, rows, update_sink):
        self.rows = rows
        self.update_sink = update_sink
        self.query = {}
        self.payload = None

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

    def eq(self, field, value):
        self.query[field] = value
        return self

    def execute(self):
        if self.payload is not None:
            self.update_sink.append({"payload": self.payload, "query": dict(self.query)})
            return SimpleNamespace(data=[{"ok": True}])
        return SimpleNamespace(data=self.rows)


class _FakeClient:
    def __init__(self, rows, update_sink):
        self.rows = rows
        self.update_sink = update_sink

    def table(self, name):
        assert name == "clientes"
        return _FakeTableClientes(self.rows, self.update_sink)


def test_list_clientes_for_admin_filters_by_search(monkeypatch):
    rows = [
        {"cliente_id": "000001", "nombre": "ACME SAC", "email": "acme@x.com"},
        {"cliente_id": "000002", "nombre": "BETA SAC", "email": "beta@x.com"},
    ]
    update_sink = []
    monkeypatch.setattr(dbm, "get_supabase_client", lambda: _FakeClient(rows, update_sink))

    result = dbm.list_clientes_for_admin(search="acme", limit=100)
    assert len(result) == 1
    assert result[0]["cliente_id"] == "000001"


def test_update_cliente_fields_rejects_invalid_estado():
    ok, msg = dbm.update_cliente_fields(cliente_id="000001", estado="DESCONOCIDO")
    assert ok is False
    assert "estado invalido" in msg


def test_update_cliente_fields_sends_payload(monkeypatch):
    rows = []
    update_sink = []
    monkeypatch.setattr(dbm, "get_supabase_client", lambda: _FakeClient(rows, update_sink))

    ok, msg = dbm.update_cliente_fields(
        cliente_id="000010",
        email="CLIENTE@MAIL.COM",
        telefono="999111222",
        estado="activo",
    )

    assert ok is True
    assert "actualizado" in msg.lower()
    assert len(update_sink) == 1
    payload = update_sink[0]["payload"]
    assert payload["email"] == "cliente@mail.com"
    assert payload["telefono"] == "999111222"
    assert payload["estado"] == "ACTIVO"
