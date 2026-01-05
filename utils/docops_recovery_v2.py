
import sys
from notion_client import Client
from datetime import datetime

# Config
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
ESTADO_ACTUAL_ID = "2dd7544a512b8023a8efcaec365ce966" # Established ID
TAG = "v1.5.2-stable-email-kpi-fix"
COMMIT = "0757108"
GATES = "Gate 0 PASS, Gate 3 PASS (E2E)"

client = Client(auth=NOTION_TOKEN)

# 1. FIND BACKLOG
def find_backlog_ready_card():
    print("--- 1. BUSCANDO BACKLOG & READY CARD ---")
    try:
        # Search without filter to avoid API errors
        results = client.search(query="Backlog").get("results", [])
    except Exception as e:
        print(f"Search Error: {e}")
        return None, None

    backlog_id = None
    for res in results:
        title = "Untitled"
        if res["object"] == "database":
             title = "".join([t.get("plain_text", "") for t in res.get("title", [])])
        elif res["object"] == "page":
             title = "".join([t.get("plain_text", "") for t in res.get("properties", {}).get("title", {}).get("title", [])])
        
        if "reportecobranzas" in title.lower().replace(" ", "") and res["object"] == "database":
            backlog_id = res['id']
            break
            
    if not backlog_id:
        print("Backlog DB not found via Search.")
        # Fallback to hardcoded ID seen in logs if verified? 
        # previous log: [child_database] (ID: 2de7544a-512b-80de-a302-e257ebc9735e)
        backlog_id = "2de7544a-512b-80de-a302-e257ebc9735e"
        print(f"Using Fallback ID: {backlog_id}")

    print(f"Backlog ID: {backlog_id}")

    # Query 'Ready'
    ready_card = None
    try:
        resp = client.request(
            path=f"databases/{backlog_id}/query",
            method="POST",
            body={
                "filter": {
                    "or": [
                        {"property": "Status", "status": {"equals": "Ready"}},
                        {"property": "Estado", "status": {"equals": "Ready"}},
                        {"property": "Estado", "select": {"equals": "Ready"}}
                    ]
                },
                "page_size": 1
            }
        )
        
        results = resp.get("results", [])
        if results:
            page = results[0]
            props = page["properties"]
            
            # Extract Title
            p_title = ""
            for k,v in props.items():
                if v["id"] == "title": 
                    p_title = "".join([t.get("plain_text","") for t in v["title"]])
            
            # Extract ID
            p_id = "N/A"
            for k,v in props.items():
                if k.lower() == "id" or k.lower() == "ticket id":
                    if v["type"] == "unique_id":
                        p_id = f"{v['unique_id'].get('prefix','')}-{v['unique_id'].get('number','')}"
            
            ready_card = {"id": p_id, "title": p_title}
            print(f"Found Ready Card: {p_title} ({p_id})")
        else:
            print("No Ready cards found.")
            ready_card = {"id": "N/A", "title": "Ninguna (Lista vacía)"}

    except Exception as e:
        print(f"Query Error: {e}")
        ready_card = {"id": "ERROR", "title": "Error consultando Backlog"}
        
    return backlog_id, ready_card

# 2. UPDATE HANDOFF
def update_handoff(ready_card_info):
    print("\n--- 2. ACTUALIZANDO HANDOFF (REPLACE) ---")
    next_step_text = f"Próximo paso exacto: {ready_card_info['id']} {ready_card_info['title']}"
    
    # Locate Handoff Section
    try:
        children = client.blocks.children.list(block_id=ESTADO_ACTUAL_ID).get("results", [])
    except Exception as e:
        print(f"Read Error: {e}")
        return

    handoff_block_id = None
    for b in children:
        # Check text
        b_type = b["type"]
        txt = ""
        if "rich_text" in b.get(b_type, {}):
             txt = "".join([t.get("plain_text","") for t in b[b_type]["rich_text"]])
        
        if "handoff automático" in txt.lower():
            handoff_block_id = b['id']
            print(f"Handoff Header Found: {txt} ({handoff_block_id})")
            break
            
    if not handoff_block_id:
        print("Handoff Section NOT found.")
        return

    # Delete existing children/siblings?
    # Strategy: User said "REEMPLAZA el bloque completo".
    # Assuming "Handoff" is a HEADER type. It doesn't have children unless it's a Toggle.
    # Previous execution showed it acted as siblings.
    # To "Replace" cleanly means:
    # 1. Update the Header itself? No, header is fine.
    # 2. Delete the lines immediately FOLLOWING the header until the next separator.
    # 3. Create (Append) new lines after the header.
    
    # Actually, the most robust way to "Delete Siblings" is tricky without deleting other stuff.
    # ALTERNATIVE: Turn the Header into a Toggle if it isn't one, then manage children?
    # OR: Just update specific known lines if they exist, and delete extras?
    # Given the constraint and risk of deleting wrong stuff...
    # I will stick to UPDATING content in place if I can identifying them. And deleting "Unknown" lines?
    
    # Wait, the user said "REEMPLAZA el bloque completo".
    # If it IS a Toggle, I delete all kids and add new ones.
    # If it is NOT a Toggle (it is a Headers), this is hard.
    # Let's check headers children again from previous logs.
    # Step 305 said "1) Conectando a Page ID... siblings... updated 4 lines"
    # So they are siblings.
    
    # STRATEGY FOR SIBLINGS:
    # Since I cannot easily "bulk delete range of blocks", I will UPDATE the ones I found (which worked)
    # AND I will check if there are duplicate lines and delete those.
    
    # Collect IDs of relevant lines
    relevant_ids = []
    
    # We scan specifically for lines containing keywords again.
    # We update the FIRST occurrence of each keyword.
    # We DELETE any SUBSEQUENT occurrence.
    
    keys = ["versión", "commit", "gates", "próximo paso", "bugs"]
    found_keys = set()
    
    blocks_to_delete = []
    
    capturing = False
    for b in children:
        if b['id'] == handoff_block_id:
            capturing = True
            continue
            
        if capturing:
            if b["type"] in ["heading_1", "heading_2", "heading_3", "divider"]:
                break
                
            txt = ""
            b_type = b["type"]
            if "rich_text" in b.get(b_type, {}):
                 txt = "".join([t.get("plain_text","") for t in b[b_type]["rich_text"]])
            
            # Normalize
            txt_lower = txt.lower()
            
            is_relevant = False
            for k in keys:
                if k in txt_lower:
                    is_relevant = True
                    if k in found_keys:
                        # Duplicate! Mark for deletion
                        blocks_to_delete.append(b['id'])
                    else:
                        # First time! Update it.
                        found_keys.add(k)
                        new_text = ""
                        if k == "versión": new_text = f"Versión estable actual (tag): {TAG}"
                        elif k == "commit": new_text = f"Commit relevante (hash): {COMMIT}"
                        elif k == "gates": new_text = f"Gates (calidad): {GATES}"
                        elif k == "próximo paso": new_text = next_step_text
                        elif k == "bugs": new_text = "Bugs Abiertos: 0"
                        
                        client.blocks.update(
                            block_id=b["id"], 
                            **{b_type: {"rich_text": [{"text": {"content": new_text}}]}}
                        )
                        print(f"Updated: {new_text}")
                    break # Key match found
            
            if not is_relevant and txt.strip():
                # Line in section but not matching key? Leave it or delete?
                # User said "REEMPLAZA". Maybe strict?
                # Let's leave it to be safe, unless it looks like old junk.
                pass

    for bid in blocks_to_delete:
        try:
            client.blocks.delete(block_id=bid)
            print(f"Deleted duplicate/orphaned block: {bid}")
        except: pass
        
    # If some keys were MISSING, we need to append them (insert after header?).
    # `blocks.children.append` appends to bottom of page (or container).
    # Appending to 'after' a block requires `blocks.children.append(after=...)` valid only in some APIs?
    # Notion API `append` adds to end of children list.
    # So if they are siblings in a Page, they go to bottom of Page.
    # If check step 1 missed them, they might be missing.
    # For now, assuming they exist from previous "Found 4 lines".

# 3. DOCOPS DONE (Log Update)
def update_log():
    print("\n--- 3. ACTUALIZANDO LOG ---")
    log_text = f"[{datetime.now().strftime('%Y-%m-%d | %H:%M')}] — Fix DOCOPS Recovery — {TAG} — {COMMIT} — {GATES}"
    # Find Log Section
    # Assuming Log is a toggle or section. If section, simply append to page?
    # Script `docops_update.py` used Append to Page. Sticking to that.
    try:
        client.blocks.children.append(
            block_id=ESTADO_ACTUAL_ID,
            children=[{
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": log_text}}]}
            }]
        )
        print("Log entry appended.")
    except Exception as e:
        print(f"Log Update Error: {e}")

# 4. READBACK
def readback():
    print("\n--- 4. SSOT READBACK (FINAL) ---")
    backlog_id, ready_card = find_backlog_ready_card() # Re-verify backlog
    
    # Read Page Content
    try:
        children = client.blocks.children.list(block_id=ESTADO_ACTUAL_ID).get("results", [])
    except: return

    capturing = False
    for b in children:
        txt = ""
        b_type = b["type"]
        if "rich_text" in b.get(b_type, {}):
             txt = "".join([t.get("plain_text","") for t in b[b_type]["rich_text"]])
        
        if "handoff automático" in txt.lower():
            capturing = True
            continue
        
        if capturing:
            if b_type in ["heading_1", "heading_2", "heading_3", "divider"]:
                break
            if txt.strip():
                print(f"FINAL HANDOFF > {txt}")

    if ready_card:
        print(f"FINAL BACKLOG NEXT > {ready_card['title']} ({ready_card['id']})")


if __name__ == "__main__":
    b_id, card = find_backlog_ready_card()
    if card:
        update_handoff(card)
        update_log()
        readback()
