
import sys
from notion_client import Client

# sys.stdout = open("alignment_final_out.txt", "w", encoding="utf-8") # Let's try stdout first, usually works if short

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
ESTADO_ACTUAL_ID = "2dd7544a512b8023a8efcaec365ce966"

client = Client(auth=NOTION_TOKEN)

def get_plain_text(rich_text):
    return "".join([t.get("plain_text", "") for t in rich_text])

def get_block_text(block):
    b_type = block["type"]
    if "rich_text" in block.get(b_type, {}):
        return get_plain_text(block[b_type].get("rich_text", []))
    if b_type == "child_page":
        return block["child_page"].get("title", "")
    if b_type == "child_database":
        return block["child_database"].get("title", "Database")
    return ""

def main():
    print("--- 1. SSOT READ ---")
    try:
        children = client.blocks.children.list(block_id=ESTADO_ACTUAL_ID).get("results", [])
    except Exception as e:
        print(f"Error: {e}")
        return

    capture_handoff = False
    backlog_id = None
    
    for block in children:
        text = get_block_text(block)
        
        # Handoff Logic
        if "handoff automático" in text.lower():
            capture_handoff = True
            # print(f"HEADER: {text}")
            continue
        
        if capture_handoff:
            if block["type"] in ["heading_1", "heading_2", "heading_3", "divider"]:
                capture_handoff = False
            elif text.strip():
                print(f"HANDOFF_LINE: {text}")

        # Backlog Detection
        if block["type"] == "child_database" or "backlog" in text.lower():
            # Potential backlog
            if "backlog" in text.lower():
                backlog_id = block["id"]
                print(f"BACKLOG_FOUND_ID: {backlog_id} ({text})")

    if not backlog_id:
        # Fallback search
        res = client.search(query="Backlog").get("results", [])
        if res:
            backlog_id = res[0]["id"]
            print(f"BACKLOG_SEARCH_ID: {backlog_id}")

    print("\n--- 2. BACKLOG READ (READY) ---")
    if backlog_id:
        # Assume Database
        try:
             # Query for Ready
            q = client.databases.query(
                database_id=backlog_id,
                filter={
                    "or": [
                        {"property": "Status", "status": {"equals": "Ready"}},
                        {"property": "Estado", "select": {"equals": "Ready"}},
                        {"property": "Estado", "status": {"equals": "Ready"}}
                    ]
                }
            ).get("results", [])
            
            if q:
                page = q[0]
                props = page["properties"]
                title = "Untitled"
                for k,v in props.items():
                    if v["id"] == "title": title = get_plain_text(v["title"])
                
                # ID ?
                card_id_val = "N/A"
                if "ID" in props:
                    # simplistic extraction
                    ptype = props["ID"]["type"]
                    if ptype == "unique_id": card_id_val = f"{props['ID']['unique_id'].get('prefix','')}-{props['ID']['unique_id'].get('number','')}"
                    elif ptype == "number": card_id_val = str(props["ID"]["number"])
                    
                print(f"CARD: {title}")
                print(f"ID: {card_id_val}")
                
            else:
                print("No Ready cards found.")
                
        except Exception as e:
            print(f"Backlog Query Error (maybe it is a page?): {e}")

if __name__ == "__main__":
    main()
