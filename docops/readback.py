
import os
import sys
import json
from notion_client import Client

# Re-using IDs from JSON
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

def readback():
    print("--- READBACK ---")
    page_id = IDS["estado_page_id"]
    try:
        children = client.blocks.children.list(block_id=page_id).get("results", [])
    except:
        print("Error reading page")
        return

    anchor_id = IDS["handoff_anchor_block_id"]
    capturing = False
    
    for b in children:
        if b['id'] == anchor_id:
            capturing = True
            continue
        
        if capturing:
            if b["type"] in ["heading_1", "heading_2", "heading_3", "divider"]:
                break
            
            txt = ""
            if "rich_text" in b.get(b["type"], {}):
                 txt = get_plain_text(b[b["type"]]["rich_text"])
            
            if txt.strip():
                print(txt)

if __name__ == "__main__":
    readback()
