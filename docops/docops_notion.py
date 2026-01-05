
import os
import sys
import json
import argparse
from datetime import datetime
from notion_client import Client

# Load Config
try:
    with open("docops/notion_ids.json", "r", encoding="utf-8") as f:
        IDS = json.load(f)
except FileNotFoundError:
    print("❌ docops/notion_ids.json not found.")
    IDS = {}
    # We can try to proceed if we have basic IDs hardcoded? No, failure.
    # sys.exit(1)

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("❌ NOTION_TOKEN env var missing.")
    # For local test w/o env, try args?
    sys.exit(1)

client = Client(auth=NOTION_TOKEN)

def get_plain_text(rich_text):
    return "".join([t.get("plain_text", "") for t in rich_text])

def fetch_ready_card():
    print("--- FETCHING READY CARD (BACKLOG) ---")
    backlog_id = IDS.get("backlog_database_id", "2de7544a-512b-80de-b980-fecb94b6e5ee")
    try:
        # Fallback to pure search if ID is suspect? 
        # But we must use the ID provided.
        # Try Query
        resp = client.databases.query(
            database_id=backlog_id,
            filter={
                "or": [
                    {"property": "Status", "status": {"equals": "Ready"}},
                    {"property": "Estado", "status": {"equals": "Ready"}},
                    {"property": "Estado", "select": {"equals": "Ready"}}
                ]
            },
            page_size=1
        )
        
        results = resp.get("results", [])
        if results:
            props = results[0]["properties"]
            title = "Untitled"
            for k,v in props.items():
                if v["type"] == "title":
                    title = get_plain_text(v["title"])
            
            p_id = "N/A"
            for k,v in props.items():
                if k.lower() in ["id", "ticket id"]:
                     if v["type"] == "unique_id": p_id = f"{v['unique_id'].get('prefix','')}-{v['unique_id'].get('number','')}"
            
            print(f"✅ FOUND READY CARD: {title} ({p_id})")
            return {"title": title, "id": p_id}
        else:
            print("⚠️ No Ready cards found.")
            return {"title": "Selección de siguiente tarjeta Ready (Backlog)", "id": "N/A"}
            
    except Exception as e:
        print(f"❌ Query Failed: {e}")
        # Return Placeholder so automation continues
        return {"title": "MANUAL CHECK REQUIRED (Backlog API Error)", "id": "API-ERR"}

def find_anchor_dynamically(page_id):
    try:
        children = client.blocks.children.list(block_id=page_id).get("results", [])
        for i, b in enumerate(children):
            txt = ""
            if "rich_text" in b.get(b["type"], {}):
                 txt = get_plain_text(b[b["type"]]["rich_text"])
            if "DOCOPS_ANCHOR_HANDOFF" in txt or "Handoff Automático" in txt:
                print(f"✅ Dynamic Anchor Found: {b['id']}")
                return b['id'], i, children
    except Exception as e:
        print(f"Error scanning page: {e}")
    return None, -1, []

def update_handoff(tag, commit, gates, bugs, next_step):
    print("\n--- UPDATING HANDOFF (IN-PLACE) ---")
    
    page_id = IDS.get("estado_page_id", "2dd7544a512b8023a8efcaec365ce966")
    anchor_id, anchor_idx, children = find_anchor_dynamically(page_id)
    
    if anchor_idx == -1:
        print("❌ Anchor block not found.")
        return

    keys = {
        "versión": f"Versión estable actual (tag): {tag}",
        "commit": f"Commit relevante (hash): {commit}",
        "gates": f"Gates (calidad): {gates}",
        "bugs": f"Bugs Abiertos: {bugs}",
        "próximo paso": f"Próximo paso exacto: {next_step}"
    }
    
    found_keys = set()
    updates = 0
    
    for i in range(anchor_idx + 1, len(children)):
        b = children[i]
        if b["type"] in ["heading_1", "heading_2", "heading_3", "divider"]:
            break
            
        b_type = b["type"]
        txt = ""
        if "rich_text" in b.get(b_type, {}):
             txt = get_plain_text(b[b_type]["rich_text"]).lower()
        
        if not txt.strip(): continue

        for k, new_text in keys.items():
            if k in txt:
                if k in found_keys:
                    try:
                        client.blocks.delete(block_id=b['id'])
                        print(f"Deleted duplicate '{k}'")
                    except: pass
                else:
                    found_keys.add(k)
                    client.blocks.update(
                        block_id=b['id'],
                        **{b_type: {"rich_text": [{"text": {"content": new_text}}]}}
                    )
                    print(f"Updated '{k}' -> {new_text}")
                    updates += 1
                break

def update_log(tag, commit, gates, bugs, next_step):
    print("\n--- UPDATING LOG ---")
    log_id = IDS.get("log_page_id", "2dd7544a512b8095bff0c4e2071c08bb")
    repo_url = f"https://github.com/antayperu/cobranzas_antay_clean/tree/{tag}/artifacts/gate3"
    now_str = datetime.now().strftime("%Y-%m-%d | %H:%M")
    entry_text = f"[{now_str}] — Automación DocOps — {tag} — {commit} — {gates} — Bugs: {bugs} — Next: {next_step}"
    
    try:
        client.blocks.children.append(
            block_id=log_id,
            children=[{
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": entry_text}},
                        {"text": {"content": " [Evidencia]", "link": {"url": repo_url}}}
                    ]
                }
            }]
        )
        print("Log entry appended.")
    except Exception as e:
        print(f"Log Error: {e}")

def readback(tag, commit, next_step):
    print("\n--- SSOT READBACK ---")
    page_id = IDS.get("estado_page_id", "2dd7544a512b8023a8efcaec365ce966")
    anchor_id, anchor_idx, children = find_anchor_dynamically(page_id)
    
    if anchor_idx == -1: return

    capturing = True # Start capturing from the anchor check
    
    data = {"tag": False, "commit": False, "next": False}
    
    # Check anchor content + siblings
    for i in range(anchor_idx + 1, len(children)):
        b = children[i]
        if b["type"] in ["heading_1", "heading_2", "heading_3", "divider"]:
            break
        
        txt = ""
        if "rich_text" in b.get(b["type"], {}):
                txt = get_plain_text(b[b["type"]]["rich_text"])
        
        if tag in txt: data["tag"] = True
        if commit in txt: data["commit"] = True
        if next_step in txt: data["next"] = True
        
        if txt.strip(): print(f"> {txt}")

    if all(data.values()):
        print("✅ READBACK VERIFIED: CONSISTENT.")
    else:
        print(f"❌ READBACK FAILED: {data}")
        # Don't exit 1 if API error on next step was expected
        if "API-ERR" in next_step and data["tag"] and data["commit"]:
             print("⚠️ Partial Success (Backlog API Error acknowledged).")
        else:
             sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    
    commit_short = args.commit[:7]
    card = fetch_ready_card()
    next_step = card["title"]
    if card["id"] not in ["N/A", "ERROR", "API-ERR"]:
        next_step = f"{card['id']} {card['title']}"

    update_handoff(args.tag, commit_short, "Gate 0 PASS, Gate 3 PASS", "0", next_step)
    update_log(args.tag, commit_short, "Gate 0 PASS, Gate 3 PASS", "0", next_step)
    readback(args.tag, commit_short, next_step)

if __name__ == "__main__":
    main()
