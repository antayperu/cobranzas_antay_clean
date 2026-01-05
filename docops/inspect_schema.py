
import os
import json
import urllib.request

TOKEN = os.environ.get("NOTION_TOKEN")
DB_ID = "2de7544a-512b-80de-b980-fecb94b6e5ee"

url = f"https://api.notion.com/v1/databases/{DB_ID}"
headers = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28"}

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8"))
    print("PROPERTIES:")
    for k, v in data.get("properties", {}).items():
        print(f" - {k} ({v['type']})")
