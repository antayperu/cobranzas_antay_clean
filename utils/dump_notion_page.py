
import os
import sys
from notion_client import Client

# Config
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if os.path.exists("secrets.txt"):
    try:
        with open("secrets.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if line.startswith("NOTION_TOKEN="):
                    NOTION_TOKEN = line.strip().split("=", 1)[1]
                    break
                elif "=" not in line:
                    NOTION_TOKEN = line
                    break
    except: pass

TARGET_PAGE_ID = "2dd7544a-512b-8023-a8ef-caec365ce966"
client = Client(auth=NOTION_TOKEN)

def get_rich_text(block, field_name):
    if field_name in block:
        return "".join([t.get("plain_text", "") for t in block[field_name].get("rich_text", [])])
    return ""

def get_block_text(block):
    b_type = block.get("type")
    content = ""
    if b_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "to_do", "toggle"]:
        content = get_rich_text(block, b_type)
    elif b_type == "child_page":
        content = block.get("child_page", {}).get("title", "")
    return content

def dump_entire_page():
    print(f"--- DUMP TOTAL PAGINA ...966 ---")
    
    try:
        # 1. Read Page Properties (Title)
        page = client.pages.retrieve(page_id=TARGET_PAGE_ID)
        props = page.get("properties", {})
        title = "Untitled"
        for key, val in props.items():
            if val["type"] == "title":
                title = val["title"][0]["plain_text"] if val["title"] else ""
        print(f"PAGE TITLE: {title}")
        print(f"PAGE URL: {page.get('url')}")
        
        # 2. Read Blocks
        results = client.blocks.children.list(block_id=TARGET_PAGE_ID).get("results", [])
        print(f"TOTAL BLOCKS: {len(results)}")
        
        for i, block in enumerate(results):
            text = get_block_text(block)
            b_id = block['id']
            b_type = block['type']
            print(f"[{i}] {b_type} | '{text}'")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    dump_entire_page()
