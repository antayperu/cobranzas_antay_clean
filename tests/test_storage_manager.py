from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import utils.storage_manager as storage_mgr


class _FakeBucketProxy:
    def __init__(self, storage: "_FakeStorage", bucket: str):
        self._storage = storage
        self._bucket = bucket

    def upload(self, path, file, file_options=None):
        key = (self._bucket, path)
        payload = bytes(file) if isinstance(file, (bytes, bytearray)) else bytes(file.read())
        self._storage.files[key] = {
            "payload": payload,
            "options": dict(file_options or {}),
        }
        return {"path": path}

    def get_public_url(self, path):
        return f"https://example.supabase.co/storage/v1/object/public/{self._bucket}/{path}"

    def download(self, path, options=None, query_params=None):
        key = (self._bucket, path)
        if key not in self._storage.files:
            raise FileNotFoundError(path)
        return self._storage.files[key]["payload"]

    def remove(self, paths):
        removed = []
        for path in paths:
            key = (self._bucket, path)
            self._storage.files.pop(key, None)
            removed.append({"name": path})
        return removed


class _FakeStorage:
    def __init__(self):
        self.buckets = set()
        self.files = {}

    def list_buckets(self):
        return [SimpleNamespace(id=bucket_id) for bucket_id in sorted(self.buckets)]

    def create_bucket(self, bucket_id, options=None):
        self.buckets.add(bucket_id)
        return {"id": bucket_id, "options": options or {}}

    def from_(self, bucket_id):
        self.buckets.add(bucket_id)
        return _FakeBucketProxy(self, bucket_id)


class _FakeSupabaseWrapper:
    def __init__(self, storage: _FakeStorage):
        self._storage = storage

    def is_available(self):
        return True

    def get_client(self):
        return SimpleNamespace(storage=self._storage)


def _inject_fake_storage(monkeypatch) -> _FakeStorage:
    fake_storage = _FakeStorage()
    wrapper = _FakeSupabaseWrapper(fake_storage)
    monkeypatch.setattr(storage_mgr.SupabaseClient, "get_instance", lambda: wrapper)
    return fake_storage


def test_ensure_default_buckets_creates_expected(monkeypatch):
    fake_storage = _inject_fake_storage(monkeypatch)
    result = storage_mgr.ensure_default_buckets()

    assert storage_mgr.LOGOS_BUCKET in fake_storage.buckets
    assert storage_mgr.EXPORTS_BUCKET in fake_storage.buckets
    assert storage_mgr.WHATSAPP_IMAGES_BUCKET in fake_storage.buckets
    assert result[storage_mgr.LOGOS_BUCKET]["ok"] is True


def test_build_export_storage_path_sanitizes_company_name():
    path = storage_mgr.build_export_storage_path(
        company_name='Empresa: "Demo"/2026',
        filename="Reporte Final.xlsx",
    )
    assert "Empresa_" in path
    assert path.endswith(".xlsx")
    assert "\\" not in path


def test_upload_export_excel_writes_to_exports_bucket(monkeypatch):
    fake_storage = _inject_fake_storage(monkeypatch)
    payload = b"excel-bytes"
    result = storage_mgr.upload_export_excel(
        excel_bytes=payload,
        filename="Reporte.xlsx",
        company_name="Empresa Demo",
    )

    assert result["bucket"] == storage_mgr.EXPORTS_BUCKET
    file_key = (result["bucket"], result["path"])
    assert file_key in fake_storage.files
    assert fake_storage.files[file_key]["payload"] == payload
    assert fake_storage.files[file_key]["options"]["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_resolve_logo_path_downloads_and_caches_local(monkeypatch, tmp_path):
    fake_storage = _inject_fake_storage(monkeypatch)
    monkeypatch.chdir(tmp_path)

    bucket = storage_mgr.LOGOS_BUCKET
    path = "branding/current/logo_dacta_processed.png"
    fake_storage.from_(bucket).upload(
        path,
        b"png-bytes",
        file_options={"content-type": "image/png", "upsert": "true"},
    )

    config = {
        "logo_path": "",
        "logo_storage_bucket": bucket,
        "logo_storage_path": path,
    }
    local_path = storage_mgr.resolve_logo_path(config)

    assert local_path is not None
    assert os.path.exists(local_path)
    assert Path(local_path).read_bytes() == b"png-bytes"


def test_delete_logo_assets_returns_patch_and_removes_paths(monkeypatch):
    fake_storage = _inject_fake_storage(monkeypatch)
    bucket = storage_mgr.LOGOS_BUCKET
    path_current = "branding/current/logo_dacta_processed.png"
    path_original = "branding/original/20260217_logo.png"

    fake_storage.from_(bucket).upload(
        path_current,
        b"a",
        file_options={"content-type": "image/png", "upsert": "true"},
    )
    fake_storage.from_(bucket).upload(
        path_original,
        b"b",
        file_options={"content-type": "image/png", "upsert": "false"},
    )

    config = {
        "logo_path": "",
        "logo_storage_bucket": bucket,
        "logo_storage_path": path_current,
        "logo_storage_original_path": path_original,
    }
    result = storage_mgr.delete_logo_assets(config)

    assert result["ok"] is True
    assert (bucket, path_current) not in fake_storage.files
    assert (bucket, path_original) not in fake_storage.files
    assert result["config_patch"]["logo_storage_path"] is None
