"""
Publica actualizacion cloud-only en Notion:
1) Crea snapshot del backlog en la base de backlog.
2) Agrega bitacora breve al FRD de ReporteCobranzas.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
IDS_FILE = ROOT / "docops" / "notion_ids.json"
BACKLOG_FILE = ROOT / "docs" / "backlog_priorizado.md"
FRD_PAGE_ID = "2dd7544a512b80c8a893e3b76fc51d2e"


def _get_token() -> str:
    mcp_path = ROOT / ".mcp.json"
    if mcp_path.exists():
        with mcp_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        headers = data.get("mcpServers", {}).get("notion", {}).get("env", {}).get("OPENAPI_MCP_HEADERS")
        if headers:
            parsed = json.loads(headers)
            auth = parsed.get("Authorization", "")
            if auth.startswith("Bearer "):
                return auth.replace("Bearer ", "").strip()

    token = (os.getenv("NOTION_TOKEN") or "").strip()
    if token:
        return token

    raise RuntimeError("No se encontro NOTION_TOKEN en entorno ni .mcp.json.")


def _get_backlog_db_id() -> str:
    with IDS_FILE.open("r", encoding="utf-8") as f:
        ids = json.load(f)
    db_id = ids.get("backlog_database_id", "").strip()
    if not db_id:
        raise RuntimeError("No se encontro backlog_database_id en docops/notion_ids.json.")
    return db_id


def _get_title_property_name(client: Client, database_id: str) -> str:
    db = client.databases.retrieve(database_id=database_id)
    properties = db.get("properties", {})
    for name, definition in properties.items():
        if definition.get("type") == "title":
            return name
    raise RuntimeError("La base de Notion no tiene propiedad de tipo title.")


def _safe_excerpt(path: Path, max_chars: int = 1400) -> str:
    if not path.exists():
        return "No se encontro backlog local para adjuntar."
    content = path.read_text(encoding="utf-8")
    content = content.strip().replace("\r\n", "\n")
    if len(content) <= max_chars:
        return content
    return content[: max_chars - 3] + "..."


def main():
    token = _get_token()
    client = Client(auth=token, notion_version="2022-06-28")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    backlog_db_id = _get_backlog_db_id()
    title_prop = _get_title_property_name(client, backlog_db_id)
    backlog_excerpt = _safe_excerpt(BACKLOG_FILE)

    page = client.pages.create(
        parent={"database_id": backlog_db_id},
        properties={
            title_prop: {
                "title": [
                    {
                        "text": {
                            "content": f"Supabase Cloud-Only Update - {now}",
                        }
                    }
                ]
            }
        },
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    "Actualizacion ejecutada: estrategia cloud-only aplicada "
                                    "(sin fallback local), con bloqueo controlado ante falla de Supabase."
                                )
                            },
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Backlog Priorizado (extracto)"},
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": backlog_excerpt},
                        }
                    ]
                },
            },
        ],
    )

    client.blocks.children.append(
        block_id=FRD_PAGE_ID,
        children=[
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"Update Cloud-Only - {now}"},
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Se eliminó fallback local (SQLite/session_state) del flujo de persistencia.",
                            },
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Se aplica bloqueo controlado cuando Supabase no está disponible.",
                            },
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Backlog y plan de migración actualizados para ejecución cloud-only premium.",
                            },
                        }
                    ]
                },
            },
        ],
    )

    print("NOTION_BACKLOG_PAGE_URL=", page.get("url", "N/A"))
    print("NOTION_FRD_PAGE_ID=", FRD_PAGE_ID)


if __name__ == "__main__":
    main()
