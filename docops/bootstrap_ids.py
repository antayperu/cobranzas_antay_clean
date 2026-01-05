
import os
import sys
import json
from notion_client import Client

# Use ENV VARS, default to known IDs if safe, or fail if missing token
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("❌ NOTION_TOKEN not found.")
    sys.exit(1)

# Known IDs (public/safe)
ESTADO_ACTUAL_ID = "2dd7544a512b8023a8efcaec365ce966"
LOG_PAGE_ID = "2dd7544a512b8095bff0c4e2071c08bb"
# ID derived from User URL: https://exciting-guitar-bc0.notion.site/2de7544a512b80deb980fecb94b6e5ee
BACKLOG_DB_ID = "2de7544a-512b-80de-b980-fecb94b6e5ee"

client = Client(auth=NOTION_TOKEN)

def get_plain_text(rich_text):
    return "".join([t.get("plain_text", "") for t in rich_text])

def find_anchor_block(page_id, anchor_text="DOCOPS_ANCHOR_HANDOFF"):
    try:
        children = client.blocks.children.list(block_id=page_id).get("results", [])
    except: return None
    for b in children:
        b_type=b["type"]
        txt=""
        if "rich_text" in b.get(b_type, {}): txt=get_plain_text(b[b_type]["rich_text"])
        if anchor_text in txt: return b['id']
    return None

def main():
    anchor_id = find_anchor_block(ESTADO_ACTUAL_ID)
    if not anchor_id:
        print("Anchor not found, using generic.")
        # Fallback? No, fail.
        sys.exit(1)

    ids = {
        "estado_page_id": ESTADO_ACTUAL_ID,
        "log_page_id": LOG_PAGE_ID,
        "backlog_database_id": BACKLOG_DB_ID,
        "handoff_anchor_block_id": anchor_id
    }
    
    with open("docops/notion_ids.json", "w", encoding="utf-8") as f:
        json.dump(ids, f, indent=2)
    print("ids generated")

if __name__ == "__main__":
    main()
