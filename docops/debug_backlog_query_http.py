
import os
import json
import urllib.request
import urllib.error

# Load Config
try:
    with open("docops/notion_ids.json", "r", encoding="utf-8") as f:
        IDS = json.load(f)
except Exception as e:
    print(f"Error loading IDs: {e}")
    exit(1)

DB_ID = IDS.get("backlog_database_id", "").strip()
TOKEN = os.environ.get("NOTION_TOKEN", "").strip()

print(f"database_id: {DB_ID}")

if not DB_ID or not TOKEN:
    print("Missing DB_ID or NOTION_TOKEN")
    exit(1)

url = f"https://api.notion.com/v1/databases/{DB_ID}/query"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

data = json.dumps({}).encode("utf-8")

req = urllib.request.Request(url, data=data, headers=headers, method="POST")

try:
    with urllib.request.urlopen(req) as response:
        status_code = response.getcode()
        print(f"status_code: {status_code}")
        
        response_body = response.read().decode("utf-8")
        result = json.loads(response_body)
        
        results_list = result.get("results", [])
        print(f"len(results): {len(results_list)}")
        
        if results_list:
            first = results_list[0]
            # Try to find a title
            title = "Untitled"
            props = first.get("properties", {})
            for k, v in props.items():
                if v["type"] == "title":
                    title_list = v.get("title", [])
                    if title_list:
                        title = title_list[0].get("plain_text", "")
            print(f"Primer Item: {title}")

except urllib.error.HTTPError as e:
    print(f"status_code: {e.code}")
    print(f"response_text: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
