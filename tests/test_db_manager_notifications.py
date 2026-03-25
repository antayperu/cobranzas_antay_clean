from types import SimpleNamespace

import utils.db_manager as dbm


class _FakeTable:
    def __init__(self, name, inserts, select_rows):
        self.name = name
        self._inserts = inserts
        self._select_rows = select_rows
        self._query = {}

    def insert(self, payload):
        self._inserts.append((self.name, payload))
        return self

    def select(self, fields):
        self._query["select"] = fields
        return self

    def eq(self, field, value):
        self._query[field] = value
        return self

    def limit(self, value):
        self._query["limit"] = value
        return self

    def in_(self, field, values):
        self._query[field] = values
        return self

    def order(self, field, desc=False):
        self._query["order"] = (field, desc)
        return self

    def execute(self):
        if self._query.get("select"):
            return SimpleNamespace(data=self._select_rows)
        return SimpleNamespace(data=[])


class _FakeClient:
    def __init__(self, inserts, select_rows=None):
        self._inserts = inserts
        self._select_rows = select_rows or []

    def table(self, name):
        return _FakeTable(name, self._inserts, self._select_rows)


def test_persist_notification_event_sent_maps_to_enviado(monkeypatch):
    inserts = []
    monkeypatch.setattr(dbm, "get_supabase_client", lambda: _FakeClient(inserts))

    ok = dbm.persist_notification_event(
        cliente_id="000001",
        destinatario="cliente@acme.com",
        asunto="Estado de Cuenta",
        mensaje="Notificacion enviada correctamente.",
        status_code="SENT",
        run_id="run123",
        notification_key="nk123",
        match_keys=["MK-1"],
        documento_id=None,
        metadata_extra={"source": "test"},
    )

    assert ok is True
    assert len(inserts) == 1
    table_name, payload = inserts[0]
    assert table_name == "notificaciones"
    assert payload["tipo_notificacion"] == "EMAIL"
    assert payload["estado"] == "ENVIADO"
    assert payload["fecha_envio"] is not None
    assert payload["cliente_id"] == "000001"
    assert payload["metadata"]["run_id"] == "run123"
    assert payload["metadata"]["match_keys"] == ["MK-1"]
    assert payload["metadata"]["source"] == "test"


def test_persist_notification_event_failed_maps_to_gestion_fallida(monkeypatch):
    inserts = []
    monkeypatch.setattr(dbm, "get_supabase_client", lambda: _FakeClient(inserts))

    ok = dbm.persist_notification_event(
        cliente_id="000002",
        destinatario="x@acme.com",
        asunto="Estado de Cuenta",
        mensaje="SMTP timeout",
        status_code="FAILED",
    )

    assert ok is True
    _, payload = inserts[0]
    assert payload["tipo_notificacion"] == "EMAIL"
    assert payload["estado"] == "PENDIENTE"
    assert payload["fecha_envio"] is None


def test_get_documento_id_by_numero_returns_first_match(monkeypatch):
    inserts = []
    select_rows = [{"documento_id": "DOC-123"}]
    monkeypatch.setattr(dbm, "get_supabase_client", lambda: _FakeClient(inserts, select_rows))

    doc_id = dbm.get_documento_id_by_numero("000001", "F001-00000001")
    assert doc_id == "DOC-123"


def test_get_notifications_history_returns_rows(monkeypatch):
    inserts = []
    sample_rows = [
        {
            "cliente_id": "000001",
            "destinatario": "cliente@acme.com",
            "estado": "ENVIADO",
            "asunto": "Estado de Cuenta",
        }
    ]
    monkeypatch.setattr(dbm, "get_supabase_client", lambda: _FakeClient(inserts, sample_rows))

    rows = dbm.get_notifications_history(["000001"], limit=50)
    assert len(rows) == 1
    assert rows[0]["cliente_id"] == "000001"


def test_get_notifications_report_filters_estado_and_canal(monkeypatch):
    inserts = []
    sample_rows = [
        {
            "cliente_id": "000001",
            "destinatario": "cliente@acme.com",
            "estado": "ENVIADO",
            "fecha_envio": "2026-02-17 10:00:00",
            "created_at": "2026-02-17 10:00:00",
            "tipo_notificacion": "EMAIL",
            "metadata": {"channel": "EMAIL", "status_code": "SENT"},
        },
        {
            "cliente_id": "000002",
            "destinatario": "cliente2@acme.com",
            "estado": "PENDIENTE",
            "fecha_envio": None,
            "created_at": "2026-02-17 10:05:00",
            "tipo_notificacion": "EMAIL",
            "metadata": {"channel": "WHATSAPP", "status_code": "BLOCKED"},
        },
    ]
    monkeypatch.setattr(dbm, "get_supabase_client", lambda: _FakeClient(inserts, sample_rows))

    rows = dbm.get_notifications_report(
        date_from="2026-02-17",
        date_to="2026-02-17",
        estado="ENVIADO",
        canal="EMAIL",
        limit=100,
    )
    assert len(rows) == 1
    assert rows[0]["cliente_id"] == "000001"
