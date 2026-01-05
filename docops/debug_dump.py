
import os
import sys
import json
from notion_client import Client

try:
    with open("docops/notion_ids.json", "r", encoding="utf-8") as f:
        IDS = json.load(f)
except:
    print("IDs not found")
    sys.exit(1)

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
client = Client(auth=NOTION_TOKEN)

def get_plain_text(rich_text):
    return "".join([t.get("plain_text", "") for t in rich_text])

def dump():
    print("--- DUMP ---")
    page_id = IDS["estado_page_id"]
    try:
        children = client.blocks.children.list(block_id=page_id).get("results", [])
    except Exception as e:
        print(f"Error: {e}")
        return

    for b in children:
        b_type = b["type"]
        txt = ""
        if "rich_text" in b.get(b["type"], {}):
            txt = get_plain_text(b[b["type"]]["rich_text"])
        print(f"[{b_type}] {txt} ({b['id']})")

if __name__ == "__main__":
    dump()
