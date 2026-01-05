
import os
import sys
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
client = Client(auth=NOTION_TOKEN)

PAGE_ID = "2dd7544a512b8023a8efcaec365ce966"
ANCHOR_TEXT = "DOCOPS_ANCHOR_HANDOFF"

def restore_anchor():
    print(f"Scanning {PAGE_ID} for {ANCHOR_TEXT}...")
    try:
        children = client.blocks.children.list(block_id=PAGE_ID).get("results", [])
    except Exception as e:
        print(f"Error: {e}")
        return

    found = False
    for b in children:
        b_type = b["type"]
        txt = ""
        if "rich_text" in b.get(b_type, {}):
            rich_text = b[b_type].get("rich_text", [])
            txt = "".join([t.get("plain_text", "") for t in rich_text])
        if ANCHOR_TEXT in txt:
            print(f"✅ Found Anchor: {b['id']}")
            found = True
            break
            
    if not found:
        print("❌ Anchor missing. Restoring...")
        # Append Anchor + Divider
        client.blocks.children.append(
            block_id=PAGE_ID,
            children=[
                {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": ANCHOR_TEXT}}]}},
                {"object": "block", "type": "divider", "divider": {}}
            ]
        )
        print("✅ Restored Anchor.")

if __name__ == "__main__":
    restore_anchor()
