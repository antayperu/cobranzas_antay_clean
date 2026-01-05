
import sys
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
ESTADO_ACTUAL_ID = "2dd7544a512b8023a8efcaec365ce966"

client = Client(auth=NOTION_TOKEN)

# Redirect stdout to file
sys.stdout = open("alignment_result.txt", "w", encoding="utf-8")

def get_plain_text(rich_text):
    return "".join([t.get("plain_text", "") for t in rich_text])

def get_block_text(block):
    b_type = block["type"]
    if "rich_text" in block.get(b_type, {}):
        return get_plain_text(block[b_type].get("rich_text", []))
    if b_type == "child_page":
        return block["child_page"].get("title", "")
    return ""

def read_handoff():
    print("\n--- 1. SSOT READ (Handoff Automático) ---")
    # Because we know it's "siblings" from previous turn, we must scan the page children
    # and look for the header, then read following lines.
    
    try:
        children = client.blocks.children.list(block_id=ESTADO_ACTUAL_ID).get("results", [])
    except Exception as e:
        print(f"Error reading Page: {e}")
        return

    capture = False
    lines_found = 0
    
    for block in children:
        text = get_block_text(block)
        
        # Detect Header
        if "handoff automático" in text.lower():
            capture = True
            print(f"HEADER FOUND: {text}")
            continue
        
        if capture:
            # Stop conditions
            if block["type"] in ["heading_1", "heading_2", "heading_3", "divider"]:
                break
            
            if text.strip():
                print(f"  > {text}")
                lines_found += 1
                
    if lines_found == 0:
        print("WARNING: No lines found after header.")

def read_backlog():
    print("\n--- 2. BACKLOG READ ---")
    # Search for any page/db named "Backlog"
    results = client.search(query="Backlog").get("results", [])
    
    backlog_id = None
    for res in results:
        title = ""
        if res["object"] == "page":
            props = res.get("properties", {})
            if "title" in props: # Database page?
                title = get_plain_text(props["title"].get("title", []))
            else: # Standard page?
                # Check blocks? 
                pass
        elif res["object"] == "database":
             title = get_plain_text(res.get("title", []))
        
        print(f"Found Candidate: {res['object']} | ID: {res['id']} | Title: {title}")
        
        if "reportecobranzas" in title.lower().replace(" ", ""):
            backlog_id = res['id']
            break
            
    if not backlog_id and results:
        # Default to first one if detailed match fails
        backlog_id = results[0]['id']
        print(f"Defaulting to first candidate: {backlog_id}")

    if not backlog_id:
        print("No Backlog found.")
        return

    # Check content (Children) looking for "Ready" column/section
    print(f"Scanning Backlog ID: {backlog_id}...")
    children = client.blocks.children.list(block_id=backlog_id).get("results", [])
    
    ready_section = False
    
    for block in children:
        text = get_block_text(block)
        
        # Check for Ready Header
        if "ready" in text.lower() and "heading" in block["type"]:
            print(f"READY COLUMN/HEADER: {text}")
            ready_section = True
            continue
            
        if ready_section:
            if "heading" in block["type"] or block["type"] == "divider":
                break
            
            if text.strip():
                print(f"  [CARD] {text}")
                # We stop after finding the first one for the test requirements
                # But let's verify if there is an ID
                # Assuming format: "QA-E2E-001 (Validación...)" or similar
                
if __name__ == "__main__":
    read_handoff()
    read_backlog()
