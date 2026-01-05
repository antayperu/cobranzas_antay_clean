
import sys
from notion_client import Client

# Redirect stdout to file
sys.stdout = open("alignment_debug.txt", "w", encoding="utf-8")

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
    return ""

def dump_page(page_id, label="PAGE"):
    print(f"\n[{label}] Dumping ID: {page_id}")
    try:
        children = client.blocks.children.list(block_id=page_id).get("results", [])
        for b in children:
            txt = get_block_text(b)
            print(f"  - [{b['type']}] {txt} (ID: {b['id']})")
    except Exception as e:
        print(f"Error: {e}")

def dump_backlog():
    print("\n[BACKLOG SEARCH]")
    results = client.search(query="Backlog").get("results", [])
    
    for res in results:
        title = "Unknown"
        if res["object"] == "page" and "title" in res.get("properties", {}):
             title = get_plain_text(res["properties"]["title"].get("title", []))
        elif res["object"] == "database":
             title = get_plain_text(res.get("title", []))
        
        print(f"Found: {res['object']} | {res['id']} | {title}")
        
        if "reportecobranzas" in title.lower().replace(" ", ""):
            if res["object"] == "page":
                dump_page(res["id"], label="BACKLOG PAGE")
            elif res["object"] == "database":
                 print("Is Database. Dumping Query...")
                 # Query
                 try:
                    q = client.databases.query(database_id=res["id"]).get("results", [])
                    for p in q:
                        # Print status/title columns
                        props = p["properties"]
                        p_title = ""
                        p_status = ""
                        # infer
                        for k,v in props.items():
                            if v["id"] == "title": p_title = get_plain_text(v["title"])
                            if "status" in k.lower() or "estado" in k.lower():
                                if "status" in v: p_status = v["status"].get("name", "")
                                if "select" in v: p_status = v["select"].get("name", "")
                        print(f"    - Page: {p_title} | Status: {p_status}")
                 except Exception as e:
                     print(f"Query Error: {e}")

if __name__ == "__main__":
    dump_page(ESTADO_ACTUAL_ID, "ESTADO ACTUAL")
    dump_backlog()
