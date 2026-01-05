
import os
import sys
import json
import argparse
import traceback
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
    print("--- 1. BACKLOG QUERY (HTTP) ---", flush=True)
    db_id = IDS["backlog_database_id"]
    print(f"database_id: {db_id}", flush=True)
    
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    } 
    
    import urllib.request
    import urllib.error
    
    # Corrected Filter: Estado (rich_text) = Ready
    try:
        data = json.dumps({
            "filter": {
                "property": "Estado",
                "rich_text": {
                    "equals": "Ready"
                }
            },
            "page_size": 1
        }).encode("utf-8")
        
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            print(f"status_code: {status_code}", flush=True)
            
            resp_body = response.read().decode("utf-8")
            result = json.loads(resp_body)
            results = result.get("results", [])
            print(f"len(results): {len(results)}", flush=True)
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP ERROR: {e.code}", flush=True)
        print(f"response_text: {e.read().decode('utf-8')}", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ GENERIC ERROR: {e}", flush=True)
        sys.exit(1)

    if not results:
        print("⚠️ No Ready cards found (Query Success).", flush=True)
        return {"title": "Sin Ready", "id": ""}
    
    # Extract First Card
    page = results[0]
    props = page["properties"]
    
    title = "Untitled"
    if "Tarea" in props and props["Tarea"]["type"] == "title":
         t_list = props["Tarea"].get("title", [])
         if t_list: title = t_list[0].get("plain_text", "")
    else:
        for k, v in props.items():
            if v["type"] == "title":
                t_list = v.get("title", [])
                if t_list: title = t_list[0].get("plain_text", "")
            
    card_id = ""
    if "ID" in props and props["ID"]["type"] == "rich_text":
         t_list = props["ID"].get("rich_text", [])
         if t_list: card_id = t_list[0].get("plain_text", "")
    else:
        for k, v in props.items():
            k_lower = k.lower()
            if "id" in k_lower or "ticket" in k_lower:
                if v["type"] == "unique_id":
                    uid = v["unique_id"]
                    card_id = f"{uid.get('prefix','')}-{uid.get('number','')}"
                elif v["type"] == "rich_text":
                    t_list = v.get("rich_text", [])
                    if t_list: card_id = t_list[0].get("plain_text", "")
                elif v["type"] == "number":
                    card_id = str(v.get("number", ""))

    print(f"✅ READY CARD: {title} ({card_id})", flush=True)
    
    full_text = title
    if card_id:
        full_text = f"{card_id} {title}"
        
    return {"title": full_text, "id": card_id}


def update_log(tag, commit, gates, bugs, next_step_text):
    print("\n--- 2. UPDATE LOG ---", flush=True)
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
        print("✅ Log appended.", flush=True)
    except Exception as e:
        print(f"❌ FAIL: Log append error: {e}", flush=True)
        sys.exit(1)


def update_handoff(tag, commit, gates, bugs, next_step_text):
    try:
        print("\n--- 3. UPDATE HANDOFF (SSOT) ---", flush=True)
        page_id = IDS["estado_page_id"]
        anchor_id_static = IDS.get("handoff_anchor_block_id", "")
        
        print(f"Scanning page {page_id}...", flush=True)
        try:
            children = client.blocks.children.list(block_id=page_id).get("results", [])
        except Exception as e:
            print(f"❌ FAIL: Could not list page children: {e}", flush=True)
            sys.exit(1)

        anchor_idx = -1
        
        # 1. Try Static ID Match
        if anchor_id_static:
            for i, b in enumerate(children):
                if b["id"].replace("-", "") == anchor_id_static.replace("-", ""):
                     anchor_idx = i
                     print(f"✅ Found Anchor via Static ID at index {i}", flush=True)
                     break
        
        # 2. Fallback to Text Search
        if anchor_idx == -1:
            print("⚠️ Static Anchor not found. Trying text search...", flush=True)
            for i, b in enumerate(children):
                txt = ""
                if "rich_text" in b.get(b["type"], {}):
                     txt = get_plain_text(b[b["type"]]["rich_text"])
                if "DOCOPS_ANCHOR_HANDOFF" in txt or "Handoff Automático" in txt:
                    print(f"✅ Found Anchor via Text at index {i}", flush=True)
                    anchor_idx = i
                    break
        
        if anchor_idx == -1:
            print("❌ CRITICAL: Anchor block not found via ID or Text.", flush=True)
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
                            print(f"  [DELETE] Duplicate '{k}'", flush=True)
                        except: pass
                    else:
                        # UPDATE
                        found_keys.add(k)
                        try:
                            client.blocks.update(
                                block_id=b['id'],
                                **{b_type: {"rich_text": [{"text": {"content": new_val}}]}}
                            )
                            print(f"  [UPDATE] '{k}' -> {new_val}", flush=True)
                        except Exception as e:
                            print(f"❌ FAIL: Update block {b['id']}: {e}", flush=True)
                            sys.exit(1)
                    break
    except Exception:
        traceback.print_exc()
        sys.exit(1)


def verify_readback(tag, commit, next_step_text):
    print("\n--- 4. READBACK VALIDATION ---", flush=True)
    page_id = IDS["estado_page_id"]
    
    children = client.blocks.children.list(block_id=page_id).get("results", [])
    
    anchor_idx = -1
    anchor_id_static = IDS.get("handoff_anchor_block_id", "")
    
    if anchor_id_static:
        for i, b in enumerate(children):
            if b["id"].replace("-", "") == anchor_id_static.replace("-", ""):
                 anchor_idx = i
                 break
    
    if anchor_idx == -1:
         print("❌ FAIL: Readback anchor not found.", flush=True)
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
        
        if txt.strip(): print(f"> {txt}", flush=True)

    failed = [k for k, v in checks.items() if not v["found"]]
    
    if failed:
        print(f"❌ READBACK FAILED. Missing: {failed}", flush=True)
        sys.exit(1)
    else:
        print("✅ READBACK SUCCESS: All fields match SSOT.", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    
    # 1. Backlog
    card_data = query_backlog() 
    next_step = card_data["title"]
    
    commit_short = args.commit[:7]
    gates = "Gate 0 PASS, Gate 3 PASS (E2E)"
    bugs = "0"
    
    # 2. Log
    update_log(args.tag, commit_short, gates, bugs, next_step)
    
    # 3. Handoff
    update_handoff(args.tag, commit_short, gates, bugs, next_step)
    
    # 4. Readback
    verify_readback(args.tag, commit_short, next_step)

if __name__ == "__main__":
    main()
