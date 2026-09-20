from __future__ import annotations

import os
import pytest

import utils.storage_manager as storage_mgr


def test_build_export_storage_path_sanitizes_company_name():
    path = storage_mgr.build_export_storage_path(
        company_name='Empresa: "Demo"/2026',
        filename="Reporte Final.xlsx",
    )
    assert "Empresa_" in path
    assert path.endswith(".xlsx")
    assert "\\" not in path


def test_ensure_default_buckets_raises_storage_unavailable():
    with pytest.raises(storage_mgr.StorageUnavailableError):
        storage_mgr.ensure_default_buckets()


def test_upload_export_excel_raises_storage_unavailable():
    with pytest.raises(storage_mgr.StorageUnavailableError):
        storage_mgr.upload_export_excel(
            excel_bytes=b"excel-bytes",
            filename="Reporte.xlsx",
            company_name="Empresa Demo",
        )


def test_resolve_logo_path_returns_none_when_storage_unavailable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = {
        "logo_path": "",
        "logo_storage_bucket": storage_mgr.LOGOS_BUCKET,
        "logo_storage_path": "branding/current/logo_dacta_processed.png",
    }
    result = storage_mgr.resolve_logo_path(config)
    assert result is None


def test_resolve_logo_path_returns_local_file_when_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    local_logo = tmp_path / "logo.png"
    local_logo.write_bytes(b"png")
    config = {
        "logo_path": str(local_logo),
        "logo_storage_bucket": "",
        "logo_storage_path": "",
    }
    result = storage_mgr.resolve_logo_path(config)
    assert result == str(local_logo)


def test_delete_logo_assets_returns_ok_patch_without_storage(tmp_path):
    config = {
        "logo_path": "",
        "logo_storage_bucket": storage_mgr.LOGOS_BUCKET,
        "logo_storage_path": "branding/current/logo.png",
        "logo_storage_original_path": "branding/original/logo.png",
    }
    result = storage_mgr.delete_logo_assets(config)
    assert result["ok"] is True
    assert result["config_patch"]["logo_storage_path"] is None
    assert result["config_patch"]["logo_storage_original_path"] is None


def test_delete_logo_assets_removes_local_file(tmp_path):
    local_logo = tmp_path / "logo.png"
    local_logo.write_bytes(b"png")
    config = {
        "logo_path": str(local_logo),
        "logo_storage_bucket": "",
        "logo_storage_path": "",
        "logo_storage_original_path": "",
    }
    result = storage_mgr.delete_logo_assets(config)
    assert result["ok"] is True
    assert not local_logo.exists()
