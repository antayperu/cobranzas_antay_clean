
import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

# CONFIG
IDS = {
    "Estado Actual": "2dd7544a-512b-8023-a8ef-caec365ce966",
    "Log del Proyecto": "2dd7544a-512b-8095-bff0-c4e2071c08bb",
    "Backlog DB": "2de7544a-512b-80de-b980-fecb94b6e5ee"
}
TOKEN = os.environ.get("NOTION_TOKEN")

results = []

def log_step(step, endpoint, ok_fail, code, msg):
    entry = f"| {step} | {endpoint} | {ok_fail} | {code} | {msg} |"
    results.append(entry)
    print(entry, flush=True)
    return ok_fail == "OK"

def make_request(method, url, data=None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    encoded_data = json.dumps(data).encode("utf-8") if data else None
    
    try:
        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.getcode(), response.read().decode("utf-8"), "Success"
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8"), e.reason
    except Exception as e:
        return 0, str(e), "Connection Error"

print("Starting Connectivity Test...", flush=True)
print("| Step | Endpoint | OK/FAIL | Code | Message |")
print("|---|---|---|---|---|")

# 1. READ TESTS
success = True

# Page: Estado Actual
code, body, msg = make_request("GET", f"https://api.notion.com/v1/pages/{IDS['Estado Actual']}")
if not log_step("READ Page: Estado Actual", f"pages/...caec365ce966", "OK" if code==200 else "FAIL", code, msg): success = False

# Page: Log del Proyecto
code, body, msg = make_request("GET", f"https://api.notion.com/v1/pages/{IDS['Log del Proyecto']}")
if not log_step("READ Page: Log", f"pages/...c4e2071c08bb", "OK" if code==200 else "FAIL", code, msg): success = False

# DB: Backlog (Retrieve)
code, body, msg = make_request("GET", f"https://api.notion.com/v1/databases/{IDS['Backlog DB']}")
if not log_step("READ DB: Backlog", f"databases/...fecb94b6e5ee", "OK" if code==200 else "FAIL", code, msg): success = False

# DB: Backlog (Query)
code, body, msg = make_request("POST", f"https://api.notion.com/v1/databases/{IDS['Backlog DB']}/query", {"page_size": 1})
if not log_step("QUERY DB: Backlog", f"databases/.../query", "OK" if code==200 else "FAIL", code, msg): success = False

# 2. WRITE TEST (Only if READ Log was OK)
if not success:
    print("\n❌ SKIPPING WRITE TEST DUE TO READ FAILURES.")
else:
    # Append Block
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    test_text = f"[DOCOPS-CONNECTIVITY-TEST] {now} — write_ok"
    block_data = {
        "children": [{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": test_text}}]
            }
        }]
    }
    
    code, body, msg = make_request("PATCH", f"https://api.notion.com/v1/blocks/{IDS['Log del Proyecto']}/children", block_data)
    if log_step("WRITE Log Block", "blocks/.../children", "OK" if code==200 else "FAIL", code, "Created"):
        
        # Readback (Find the block)
        resp_json = json.loads(body)
        results_list = resp_json.get("results", [])
        new_block_id = results_list[0].get("id") if results_list else None
        
        if new_block_id:
             log_step("READBACK Check", "Parse Response", "OK", 200, f"ID: {new_block_id}")
             
             # Delete it
             code_del, _, msg_del = make_request("DELETE", f"https://api.notion.com/v1/blocks/{new_block_id}")
             log_step("CLEANUP Delete", f"blocks/{new_block_id}", "OK" if code_del==200 else "FAIL", code_del, msg_del)
        else:
             log_step("READBACK Check", "Parse Response", "FAIL", 0, "No block ID returned")
             success = False
    else:
        success = False

# Conclusion
if success:
    print("\nCONCLUSION: NOTION CONNECTED = YES")
else:
    print("\nCONCLUSION: NOTION CONNECTED = NO")
    sys.exit(1)
