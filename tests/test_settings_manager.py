from types import SimpleNamespace

import utils.settings_manager as sm


class _FakeTable:
    def __init__(self, table_name, state):
        self.table_name = table_name
        self.state = state
        self.query = {}
        self.upsert_payload = None
        self.on_conflict = None

    def select(self, fields):
        self.query["select"] = fields
        return self

    def eq(self, field, value):
        self.query[field] = value
        return self

    def limit(self, value):
        self.query["limit"] = value
        return self

    def upsert(self, payload, on_conflict=None):
        self.upsert_payload = payload
        self.on_conflict = on_conflict
        return self

    def execute(self):
        if self.upsert_payload is not None:
            self.state["upserts"].append(
                {
                    "table": self.table_name,
                    "payload": self.upsert_payload,
                    "on_conflict": self.on_conflict,
                }
            )
            return SimpleNamespace(data=[self.upsert_payload])
        return SimpleNamespace(data=self.state.get("select_rows", []))


class _FakeClient:
    def __init__(self, state):
        self.state = state

    def table(self, name):
        return _FakeTable(name, self.state)


class _FakeWrapper:
    def __init__(self, state, available=True):
        self.state = state
        self.available = available

    def is_available(self):
        return self.available

    def get_client(self):
        return _FakeClient(self.state)


def _clear_env(monkeypatch):
    for key in (
        "SMTP_SERVER",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "RESEND_API_KEY",
        "SENDGRID_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


def test_load_settings_reads_remote_payload(monkeypatch):
    state = {"select_rows": [{"payload": {"company_name": "ACME CLOUD"}}], "upserts": []}
    monkeypatch.setattr(sm.SupabaseClient, "get_instance", lambda: _FakeWrapper(state, available=True))
    _clear_env(monkeypatch)

    settings = sm.load_settings()

    assert settings["company_name"] == "ACME CLOUD"
    assert state["upserts"] == []


def test_load_settings_bootstraps_remote_from_legacy_file(monkeypatch, tmp_path):
    cfg = tmp_path / "legacy_config.json"
    cfg.write_text('{"company_name": "LEGACY LOCAL"}', encoding="utf-8")
    state = {"select_rows": [], "upserts": []}

    monkeypatch.setattr(sm.SupabaseClient, "get_instance", lambda: _FakeWrapper(state, available=True))
    monkeypatch.setattr(sm, "CONFIG_FILE", str(cfg))
    _clear_env(monkeypatch)

    settings = sm.load_settings()

    assert settings["company_name"] == "LEGACY LOCAL"
    assert len(state["upserts"]) == 1
    assert state["upserts"][0]["payload"]["config_key"] == sm.CONFIG_KEY
    assert state["upserts"][0]["on_conflict"] == "config_key"


def test_save_settings_persists_to_supabase(monkeypatch):
    state = {"select_rows": [], "upserts": []}
    monkeypatch.setattr(sm.SupabaseClient, "get_instance", lambda: _FakeWrapper(state, available=True))
    _clear_env(monkeypatch)

    ok = sm.save_settings({"company_name": "SAVE TEST"})

    assert ok is True
    assert len(state["upserts"]) == 1
    payload = state["upserts"][0]["payload"]
    assert payload["config_key"] == sm.CONFIG_KEY
    assert payload["payload"]["company_name"] == "SAVE TEST"
