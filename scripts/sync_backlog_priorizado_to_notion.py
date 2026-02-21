"""
Sincroniza docs/backlog_priorizado.md hacia la base de backlog en Notion
siguiendo el esquema oficial de propiedades del database.

Comportamiento:
- Upsert por propiedad "ID" (rich_text).
- Crea o actualiza tarjetas con propiedades completas.
- Opcionalmente archiva snapshots de "Supabase Cloud-Only Update".
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
BACKLOG_MD = ROOT / "docs" / "backlog_priorizado.md"
NOTION_IDS = ROOT / "docops" / "notion_ids.json"
NOTION_VERSION = "2022-06-28"


@dataclass
class BacklogItem:
    ticket_id: str
    title: str
    priority: str
    status_raw: str = "Pendiente"
    effort: str = ""
    dependencies: str = ""
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    item_type: str = "Migracion"


def _load_token() -> str:
    mcp_file = ROOT / ".mcp.json"
    if mcp_file.exists():
        data = json.loads(mcp_file.read_text(encoding="utf-8"))
        headers = data.get("mcpServers", {}).get("notion", {}).get("env", {}).get("OPENAPI_MCP_HEADERS")
        if headers:
            parsed = json.loads(headers)
            auth = parsed.get("Authorization", "")
            if auth.startswith("Bearer "):
                return auth.replace("Bearer ", "").strip()
    raise RuntimeError("No se pudo obtener token de Notion desde .mcp.json")


def _load_database_id() -> str:
    data = json.loads(NOTION_IDS.read_text(encoding="utf-8"))
    db_id = data.get("backlog_database_id", "").strip()
    if not db_id:
        raise RuntimeError("No se encontro backlog_database_id en docops/notion_ids.json")
    return db_id


def _infer_type(ticket_id: str) -> str:
    if ticket_id.startswith("SUPABASE-MIG-"):
        return "Migracion"
    if ticket_id.startswith("SUPABASE-"):
        return "Iniciativa"
    if ticket_id.startswith("CONFIG-"):
        return "Configuracion"
    if ticket_id.startswith("FEATURE-"):
        return "Feature"
    return "Backlog"


def _status_to_notion(status_raw: str) -> str:
    s = status_raw.strip().lower()
    if s == "completado":
        return "Done"
    if s in {"en progreso", "in progress"}:
        return "In Progress"
    if s == "bloqueado":
        return "Blocked"
    if s == "ready":
        return "Ready"
    return "Backlog"


def _gate3_for_status(status_raw: str) -> str:
    return "PASS" if status_raw.strip().lower() == "completado" else "PENDIENTE"


def _parse_backlog_md(path: Path) -> List[BacklogItem]:
    lines = path.read_text(encoding="utf-8").splitlines()

    current_priority = "P2"
    items: List[BacklogItem] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("## 1. Prioridad Critica"):
            current_priority = "P0"
        elif line.startswith("## 2. Prioridad Alta"):
            current_priority = "P1"
        elif line.startswith("## 3. Prioridad Media"):
            current_priority = "P2"
        elif line.startswith("## 4. Iniciativas"):
            current_priority = "P3"

        m = re.match(r"^###\s+([^:]+):\s*(.+)$", line)
        if not m:
            i += 1
            continue

        ticket_id = m.group(1).strip()
        title = m.group(2).strip()

        item = BacklogItem(
            ticket_id=ticket_id,
            title=title,
            priority=current_priority,
            item_type=_infer_type(ticket_id),
        )

        j = i + 1
        while j < len(lines) and not lines[j].startswith("### "):
            s = lines[j].strip()

            if s.startswith("- Estado:"):
                item.status_raw = s.split(":", 1)[1].strip()
            elif s.startswith("- Esfuerzo:"):
                item.effort = s.split(":", 1)[1].strip()
            elif s.startswith("- Dependencias:"):
                item.dependencies = s.split(":", 1)[1].strip()
            elif s.startswith("- Descripcion:"):
                item.description = s.split(":", 1)[1].strip()
            elif s.startswith("- Criterios de Aceptacion:"):
                k = j + 1
                while k < len(lines):
                    t = lines[k].strip()
                    if re.match(r"^- \[[ xX]\]\s+", t):
                        item.acceptance_criteria.append(re.sub(r"^- \[[ xX]\]\s*", "", t))
                        k += 1
                        continue
                    if t.startswith("### ") or t.startswith("## ") or t.startswith("---"):
                        break
                    if t == "":
                        k += 1
                        continue
                    break

            j += 1

        items.append(item)
        i = j

    return items


def _rt(text: str) -> List[Dict[str, Dict[str, str]]]:
    if not text:
        return []
    return [{"text": {"content": text[:1900]}}]


def _format_description(item: BacklogItem) -> str:
    chunks = []
    if item.description:
        chunks.append(item.description)
    if item.dependencies:
        chunks.append(f"Dependencias: {item.dependencies}")
    if item.effort:
        chunks.append(f"Esfuerzo: {item.effort}")
    return " | ".join(chunks)


def _format_ac(item: BacklogItem) -> str:
    if not item.acceptance_criteria:
        return ""
    return " ; ".join(item.acceptance_criteria)


def _notion_request(token: str, method: str, path: str, payload: Optional[Dict] = None) -> Dict:
    url = f"https://api.notion.com/v1/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API {e.code}: {body}") from e


def _query_page_by_id(token: str, database_id: str, ticket_id: str) -> Optional[Dict]:
    result = _notion_request(
        token=token,
        method="POST",
        path=f"databases/{database_id}/query",
        payload={
            "filter": {
                "property": "ID",
                "rich_text": {"equals": ticket_id},
            },
            "page_size": 1,
        },
    )
    rows = result.get("results", [])
    return rows[0] if rows else None


def _build_properties(item: BacklogItem, today: str) -> Dict:
    notion_status = _status_to_notion(item.status_raw)
    gate3 = _gate3_for_status(item.status_raw)
    return {
        "Tarea": {
            "title": _rt(f"{item.ticket_id}: {item.title}"),
        },
        "ID": {
            "rich_text": _rt(item.ticket_id),
        },
        "Estado": {
            "status": {"name": notion_status},
        },
        "Prioridad": {
            "rich_text": _rt(item.priority),
        },
        "Tipo": {
            "rich_text": _rt(item.item_type),
        },
        "Módulo": {
            "rich_text": _rt("Supabase"),
        },
        "Owner": {
            "rich_text": _rt("Antigravity"),
        },
        "Fecha": {
            "rich_text": _rt(today),
        },
        "Gate 0": {
            "select": {"name": "NA"},
        },
        "Gate 3": {
            "select": {"name": gate3},
        },
        "Commit/Tag": {
            "select": {"name": "v1.5.6"},
        },
        "Descripción": {
            "rich_text": _rt(_format_description(item)),
        },
        "AC (Criterios de aceptación)": {
            "rich_text": _rt(_format_ac(item)),
        },
        "Evidencia": {
            "rich_text": _rt("docs/backlog_priorizado.md"),
        },
    }


def _archive_old_snapshot_cards(token: str, database_id: str) -> int:
    query = _notion_request(
        token=token,
        method="POST",
        path=f"databases/{database_id}/query",
        payload={
            "filter": {
                "property": "Tarea",
                "title": {"contains": "Supabase Cloud-Only Update"},
            },
            "page_size": 50,
        },
    )
    count = 0
    for page in query.get("results", []):
        _notion_request(
            token=token,
            method="PATCH",
            path=f"pages/{page['id']}",
            payload={"archived": True},
        )
        count += 1
    return count


def sync_backlog(cleanup_old_snapshot: bool = True) -> None:
    token = _load_token()
    database_id = _load_database_id()

    items = _parse_backlog_md(BACKLOG_MD)
    if not items:
        raise RuntimeError("No se detectaron tickets en docs/backlog_priorizado.md")

    today = datetime.now().strftime("%Y-%m-%d")
    created = 0
    updated = 0

    for item in items:
        props = _build_properties(item, today)
        existing = _query_page_by_id(token, database_id, item.ticket_id)

        if existing:
            _notion_request(
                token=token,
                method="PATCH",
                path=f"pages/{existing['id']}",
                payload={"properties": props, "archived": False},
            )
            updated += 1
        else:
            _notion_request(
                token=token,
                method="POST",
                path="pages",
                payload={
                    "parent": {"database_id": database_id},
                    "properties": props,
                },
            )
            created += 1

    archived = 0
    if cleanup_old_snapshot:
        archived = _archive_old_snapshot_cards(token, database_id)

    print(f"SYNC_OK created={created} updated={updated} archived_old_snapshots={archived}")


if __name__ == "__main__":
    sync_backlog(cleanup_old_snapshot=True)
