"""
Supabase Storage manager for files and images.

Scope:
- logos bucket
- exports bucket
- whatsapp-images bucket
"""

from __future__ import annotations

import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import utils.helpers as helpers
from utils.supabase_client import SupabaseClient


LOGOS_BUCKET = os.getenv("SUPABASE_STORAGE_LOGOS_BUCKET", "logos")
EXPORTS_BUCKET = os.getenv("SUPABASE_STORAGE_EXPORTS_BUCKET", "exports")
WHATSAPP_IMAGES_BUCKET = os.getenv("SUPABASE_STORAGE_WHATSAPP_BUCKET", "whatsapp-images")

DEFAULT_BUCKETS = (
    (LOGOS_BUCKET, False),
    (EXPORTS_BUCKET, False),
    (WHATSAPP_IMAGES_BUCKET, False),
)


class StorageUnavailableError(RuntimeError):
    """Supabase Storage is not available."""


def _normalize_storage_path(storage_path: str) -> str:
    normalized = str(storage_path or "").strip().lstrip("/").replace("\\", "/")
    if not normalized:
        raise ValueError("storage_path no puede estar vacio.")
    return normalized


def _guess_content_type(path: str, fallback: str = "application/octet-stream") -> str:
    content_type, _ = mimetypes.guess_type(path)
    return content_type or fallback


def _get_storage_client(required: bool = True):
    wrapper = SupabaseClient.get_instance()
    if not wrapper.is_available():
        if required:
            raise StorageUnavailableError(
                "Supabase no disponible. Verifica SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY."
            )
        return None
    return wrapper.get_client().storage


def ensure_bucket(bucket_name: str, public: bool = False) -> Dict[str, Any]:
    storage = _get_storage_client(required=True)
    existing = {
        getattr(bucket, "id", None) or str(bucket.get("id"))
        for bucket in storage.list_buckets()
    }

    if bucket_name in existing:
        return {"ok": True, "created": False, "bucket": bucket_name}

    storage.create_bucket(bucket_name, options={"public": public})
    return {"ok": True, "created": True, "bucket": bucket_name}


def ensure_default_buckets() -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    for bucket_name, is_public in DEFAULT_BUCKETS:
        results[bucket_name] = ensure_bucket(bucket_name, public=is_public)
    return results


def upload_bytes(
    *,
    bucket: str,
    storage_path: str,
    payload: bytes,
    content_type: Optional[str] = None,
    upsert: bool = True,
) -> Dict[str, Any]:
    if not payload:
        raise ValueError("payload vacio.")

    normalized_path = _normalize_storage_path(storage_path)
    ensure_bucket(bucket_name=bucket, public=False)
    storage = _get_storage_client(required=True)

    file_options = {
        "content-type": content_type or _guess_content_type(normalized_path),
        "upsert": "true" if upsert else "false",
    }
    storage.from_(bucket).upload(path=normalized_path, file=payload, file_options=file_options)
    public_url = storage.from_(bucket).get_public_url(normalized_path)

    return {
        "bucket": bucket,
        "path": normalized_path,
        "content_type": file_options["content-type"],
        "public_url": public_url,
    }


def build_export_storage_path(company_name: str, filename: str, now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    safe_company = helpers.sanitize_filename(company_name or "Empresa")
    safe_filename = helpers.sanitize_filename(filename or "reporte.xlsx")
    return (
        f"exports/{safe_company}/{now.strftime('%Y')}/{now.strftime('%m')}/"
        f"{now.strftime('%Y%m%d_%H%M%S')}_{safe_filename}"
    )


def upload_export_excel(excel_bytes: bytes, filename: str, company_name: str) -> Dict[str, Any]:
    path = build_export_storage_path(company_name=company_name, filename=filename)
    return upload_bytes(
        bucket=EXPORTS_BUCKET,
        storage_path=path,
        payload=excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        upsert=False,
    )


def upload_logo_assets(
    *,
    original_bytes: bytes,
    processed_bytes: bytes,
    original_name: str,
) -> Dict[str, Any]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = Path(original_name or "logo.png").suffix.lower() or ".png"
    safe_stem = helpers.sanitize_filename(Path(original_name or "logo").stem)
    original_path = f"branding/original/{stamp}_{safe_stem}{suffix}"
    processed_path = "branding/current/logo_dacta_processed.png"

    original_upload = upload_bytes(
        bucket=LOGOS_BUCKET,
        storage_path=original_path,
        payload=bytes(original_bytes),
        content_type=_guess_content_type(original_path, fallback="image/png"),
        upsert=False,
    )
    processed_upload = upload_bytes(
        bucket=LOGOS_BUCKET,
        storage_path=processed_path,
        payload=bytes(processed_bytes),
        content_type="image/png",
        upsert=True,
    )

    return {
        "original_upload": original_upload,
        "processed_upload": processed_upload,
        "config_patch": {
            "logo_storage_bucket": LOGOS_BUCKET,
            "logo_storage_path": processed_upload["path"],
            "logo_storage_public_url": processed_upload["public_url"],
            "logo_storage_original_path": original_upload["path"],
            "logo_storage_synced_at": datetime.now().isoformat(),
        },
    }


def resolve_logo_path(config: Dict[str, Any], target_local_path: Optional[str] = None) -> Optional[str]:
    local_logo_path = str(config.get("logo_path") or "").strip()
    if local_logo_path and os.path.exists(local_logo_path):
        return local_logo_path

    bucket = str(config.get("logo_storage_bucket") or LOGOS_BUCKET).strip()
    storage_path = str(config.get("logo_storage_path") or "").strip()
    if not storage_path:
        return None

    storage = _get_storage_client(required=False)
    if storage is None:
        return None

    output_path = Path(
        target_local_path or os.path.join(os.getcwd(), "assets", "logo_dacta_processed.png")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_bytes = storage.from_(bucket).download(_normalize_storage_path(storage_path))
    output_path.write_bytes(file_bytes)
    return str(output_path)


def delete_logo_assets(config: Dict[str, Any]) -> Dict[str, Any]:
    bucket = str(config.get("logo_storage_bucket") or LOGOS_BUCKET).strip()
    storage_paths = []

    if config.get("logo_storage_path"):
        storage_paths.append(_normalize_storage_path(str(config["logo_storage_path"])))
    if config.get("logo_storage_original_path"):
        storage_paths.append(_normalize_storage_path(str(config["logo_storage_original_path"])))

    storage = _get_storage_client(required=False)
    if storage and storage_paths:
        # remove() accepts a list and ignores missing paths gracefully.
        storage.from_(bucket).remove(storage_paths)

    local_logo_path = str(config.get("logo_path") or "").strip()
    if local_logo_path and os.path.exists(local_logo_path):
        try:
            os.remove(local_logo_path)
        except OSError:
            pass

    return {
        "ok": True,
        "removed_paths": storage_paths,
        "config_patch": {
            "logo_path": None,
            "logo_storage_bucket": None,
            "logo_storage_path": None,
            "logo_storage_public_url": None,
            "logo_storage_original_path": None,
            "logo_storage_synced_at": None,
        },
    }
