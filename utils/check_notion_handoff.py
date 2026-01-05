import os
import sys
from notion_client import Client

# Force UTF-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

# Config
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
TARGET_PAGE_TITLE = "Estado Actual — ReporteCobranzas"
HANDOFF_SECTION_TITLE = "Handoff Automático — para IA"

client = Client(auth=NOTION_TOKEN)

def get_block_text(block):
    block_type = block.get("type")
    content = ""
    if block_type == "paragraph":
        rich_text = block.get("paragraph", {}).get("rich_text", [])
        content = "".join([t.get("plain_text", "") for t in rich_text])
    elif block_type in ["heading_1", "heading_2", "heading_3"]:
        rich_text = block.get(block_type, {}).get("rich_text", [])
        content = "".join([t.get("plain_text", "") for t in rich_text])
    elif block_type in ["bulleted_list_item", "numbered_list_item", "to_do", "toggle"]:
        rich_text = block.get(block_type, {}).get("rich_text", [])
        content = "".join([t.get("plain_text", "") for t in rich_text])
    elif block_type == "child_page":
        content = block.get("child_page", {}).get("title", "")
    
    return content

def print_children(block_id, depth=0):
    indent = "  " * depth
    try:
        response = client.blocks.children.list(block_id=block_id)
        results = response.get("results", [])
        for block in results:
            text = get_block_text(block)
            b_type = block.get("type")
            
            # Print the block
            if text or b_type == "divider":
                 print(f"{indent}[{b_type}] {text} (ID: {block['id']})")
            
            # Recursively print children if it has them (e.g. toggles, or the handoff section itself)
            if block.get("has_children"):
                print_children(block["id"], depth + 1)
                
    except Exception as e:
        print(f"{indent}Error fetching children: {e}")

def main():
    print(f"Searching for page: '{TARGET_PAGE_TITLE}'...")
    search_res = client.search(query=TARGET_PAGE_TITLE).get("results", [])
    
    page_id = None
    for r in search_res:
        if r["object"] == "page":
            # Try to verify title matches roughly
            # Getting title from page object is valid but structure varies. 
            # We assume the search is good enough or we take the first high relevance one.
            # Let's just take the first page found.
            page_id = r["id"]
            print(f"Found page ID: {page_id}")
            break
            
    if not page_id:
        print("Page not found.")
        return

    print("Scanning page children for Handoff section...")
    children = client.blocks.children.list(block_id=page_id).get("results", [])
    
    handoff_found = False
    for block in children:
        text = get_block_text(block)
        if HANDOFF_SECTION_TITLE.lower() in text.lower():
            print(f"\n>>> FOUND HANDOFF SECTION: {text}")
            handoff_found = True
            # Print everything inside this block (if it has children, e.g. toggle or page)
            if block.get("has_children"):
                print_children(block["id"], depth=1)
            else:
                # If it's just a header, we might want to print the *following* blocks until next header?
                # But the prompt says "Abre... y lee". Usually these are toggles or sections.
                # Let's assume it might be a header and the content follows.
                # If it's a header and has no children, we should print the subsequent blocks of the parent.
                # But `print_children` iterates the list.
                # Let's change strategy: just print ALL blocks in the page to be safe, 
                # or print blocks starting from this one.
                pass
            
            # If it was a header and didn't have children (not a toggle), we need to continue printing sibling blocks
            # until we hit another header of same or higher level.
            # simpler: just print all children of the page to output, we can filter visually.
            pass
            
    if handoff_found:
        pass
    else:
        print("Handoff section explicitly NOT found in top level blocks. Dumping all blocks for manual check:")
        for block in children:
            print(f"[{block['type']}] {get_block_text(block)}")
            if block.get("has_children"):
                 # Optional: deep dive
                 pass

    # improving the "read subsequent blocks" logic:
    # Just print the whole page structure, it's safer.
    print("\n--- FULL PAGE DUMP (Top Level) ---")
    for block in children:
        txt = get_block_text(block)
        print(f"[{block['type']}] {txt}")
        if HANDOFF_SECTION_TITLE.lower() in txt.lower() or block.get("has_children"):
             if block.get("has_children"):
                 print_children(block["id"], depth=1)

if __name__ == "__main__":
    main()
