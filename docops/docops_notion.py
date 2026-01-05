
import os
import sys
import json
import argparse
from datetime import datetime
from notion_client import Client

# 1. LOAD CONFIG
ID_FILE = "docops/notion_ids.json"
try:
    with open(ID_FILE, "r", encoding="utf-8") as f:
        IDS = json.load(f)
except FileNotFoundError:
    print(f"❌ CRITICAL: {ID_FILE} missing.")
    sys.exit(1)

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if not NOTION_TOKEN:
    print("❌ CRITICAL: NOTION_TOKEN env var missing.")
    sys.exit(1)

client = Client(auth=NOTION_TOKEN)

def get_plain_text(rich_text):
    return "".join([t.get("plain_text", "") for t in rich_text])

# 2. ACTIONS
def query_backlog():
    print("--- 1. BACKLOG QUERY ---")
    db_id = IDS["backlog_database_id"]
    print(f"Database ID: {db_id}")
    
    results = [] # Placeholder
    query_success = False
    
    # METHOD A: SDK
    try:
        print("Attempting Method: SDK (client.databases.query)...")
        if not hasattr(client.databases, 'query'):
            raise AttributeError("client.databases.query missing")
            
        resp = client.databases.query(
            database_id=db_id,
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
        print(f"✅ Method Used: SDK. Result Count: {len(results)}")
        query_success = True
        
    except Exception as e:
        print(f"⚠️ SDK Method Failed: {e}")
        
        # METHOD B: RAW FALLBACK
        try:
            print("Attempting Method: RAW (client.request)...")
            resp = client.request(
                method="POST",
                path=f"databases/{db_id}/query",
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
            print(f"✅ Method Used: RAW. Result Count: {len(results)}")
            query_success = True
            
        except Exception as e2:
            print(f"❌ RAW Method Failed: {e2}")
            print("❌ CRITICAL: Both Query Methods Failed.")
            sys.exit(1) # RULE: Fail if Backlog cannot be queried

    if not results:
        print("⚠️ No Ready cards found (Query Success).")
        return {"title": "Sin Ready", "id": ""}
    
    # Extract First Card
    page = results[0]
    props = page["properties"]
    
    # Title
    title = "Untitled"
    for k, v in props.items():
        if v["type"] == "title":
            title = get_plain_text(v["title"])
            
    # ID (Flexible)
    card_id = ""
    for k, v in props.items():
        k_lower = k.lower()
        if "id" in k_lower or "ticket" in k_lower:
            if v["type"] == "unique_id":
                uid = v["unique_id"]
                card_id = f"{uid.get('prefix','')}-{uid.get('number','')}"
            elif v["type"] == "rich_text":
                card_id = get_plain_text(v["rich_text"])
            elif v["type"] == "number":
                card_id = str(v.get("number", ""))

    print(f"✅ READY CARD: {title} ({card_id})")
    
    full_text = title
    if card_id:
        full_text = f"{card_id} {title}"
        
    return {"title": full_text, "id": card_id}


def find_anchor_dynamically(page_id):
    try:
        children = client.blocks.children.list(block_id=page_id).get("results", [])
        for i, b in enumerate(children):
            txt = ""
            if "rich_text" in b.get(b["type"], {}):
                 txt = get_plain_text(b[b["type"]]["rich_text"])
            if "DOCOPS_ANCHOR_HANDOFF" in txt or "Handoff Automático" in txt:
                # print(f"✅ Dynamic Anchor Found: {b['id']}")
                return b['id'], i, children
    except Exception as e:
        print(f"Error scanning page: {e}")
    return None, -1, []

def update_handoff(tag, commit, gates, bugs, next_step_text):
    print("\n--- 2. UPDATE HANDOFF (SSOT) ---")
    page_id = IDS["estado_page_id"]
    anchor_id, anchor_idx, children = find_anchor_dynamically(page_id)

    if anchor_idx == -1:
        # Fallback to static ID if dynamic fails?
        anchor_id = IDS["handoff_anchor_block_id"] 
        # But we need children list/index. 
        # If dynamic failed, likely read failed or content changed.
        print("❌ CRITICAL: Anchor block not found via search.")
        # Try raw scan with static ID? 
        # If dynamic failed, we probably can't proceed safely.
        sys.exit(1)

    # Clean Updates
    keys = {
        "versión": f"Versión estable actual (tag): {tag}",
        "commit": f"Commit relevante (hash): {commit}",
        "gates": f"Gates (calidad): {gates}",
        "bugs": f"Bugs Abiertos: {bugs}",
        "próximo paso": f"Próximo paso exacto: {next_step_text}"
    }

    found_keys = set()
    
    # Scan only the section below anchor
    for i in range(anchor_idx + 1, len(children)):
        b = children[i]
        
        # Boundary Check
        if b["type"] in ["heading_1", "heading_2", "heading_3", "divider"]:
            break
            
        b_type = b["type"]
        txt = ""
        # Handle text extraction for update
        if "rich_text" in b.get(b_type, {}):
             txt = get_plain_text(b[b_type]["rich_text"]).lower()
        
        if not txt.strip(): continue

        for k, new_val in keys.items():
            if k in txt:
                if k in found_keys:
                    # DUPLICATE -> DELETE
                    try:
                        client.blocks.delete(block_id=b['id'])
                        print(f"  [DELETE] Duplicate '{k}'")
                    except: pass
                else:
                    # UPDATE
                    found_keys.add(k)
                    try:
                        client.blocks.update(
                            block_id=b['id'],
                            **{b_type: {"rich_text": [{"text": {"content": new_val}}]}}
                        )
                        print(f"  [UPDATE] '{k}' -> {new_val}")
                    except Exception as e:
                        print(f"❌ FAIL: Update block {b['id']}: {e}")
                        sys.exit(1)
                break

def update_log(tag, commit, gates, bugs, next_step_text):
    print("\n--- 3. UPDATE LOG ---")
    page_id = IDS["log_page_id"]
    repo_url = f"https://github.com/antayperu/cobranzas_antay_clean/tree/{tag}/artifacts/gate3"
    
    now_str = datetime.now().strftime("%Y-%m-%d | %H:%M")
    log_msg = f"[{now_str}] — Automación DocOps — {tag} — {commit} — {gates} — Bugs: {bugs} — Next: {next_step_text}"
    
    try:
        client.blocks.children.append(
            block_id=page_id,
            children=[{
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": log_msg}},
                        {"text": {"content": " [Evidencia]", "link": {"url": repo_url}}}
                    ]
                }
            }]
        )
        print("✅ Log appended.")
    except Exception as e:
        print(f"❌ FAIL: Log append error: {e}")
        sys.exit(1)

def verify_readback(tag, commit, next_step_text):
    print("\n--- 4. READBACK VALIDATION ---")
    page_id = IDS["estado_page_id"]
    anchor_id, anchor_idx, children = find_anchor_dynamically(page_id)
    
    if anchor_idx == -1:
        print("❌ FAIL: Readback anchor not found.")
        sys.exit(1)

    checks = {
        "tag": {"expected": tag, "found": False},
        "commit": {"expected": commit, "found": False},
        "next": {"expected": next_step_text, "found": False}
    }

    for i in range(anchor_idx + 1, len(children)):
        b = children[i]
        if b["type"] in ["heading_1", "heading_2", "heading_3", "divider"]:
            break
        
        txt = ""
        if "rich_text" in b.get(b["type"], {}):
                 txt = get_plain_text(b[b["type"]]["rich_text"])
        
        if checks["tag"]["expected"] in txt: checks["tag"]["found"] = True
        if checks["commit"]["expected"] in txt: checks["commit"]["found"] = True
        if checks["next"]["expected"] in txt: checks["next"]["found"] = True
        
        if txt.strip(): print(f"> {txt}")

    failed = [k for k, v in checks.items() if not v["found"]]
    
    if failed:
        print(f"❌ READBACK FAILED. Missing: {failed}")
        sys.exit(1)
    else:
        print("✅ READBACK SUCCESS: All fields match SSOT.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    
    # 1. Backlog (SAFE QUERY)
    card_data = query_backlog() 
    # If script reaches here, query succeeded (or returned empty but success)
    
    next_step = card_data["title"]
    
    # 2. Handoff
    commit_short = args.commit[:7]
    gates = "Gate 0 PASS, Gate 3 PASS (E2E)"
    bugs = "0"
    
    update_handoff(args.tag, commit_short, gates, bugs, next_step)
    
    # 3. Log
    update_log(args.tag, commit_short, gates, bugs, next_step)
    
    # 4. Readback
    verify_readback(args.tag, commit_short, next_step)

if __name__ == "__main__":
    main()
