
import os
import sys
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
client = Client(auth=NOTION_TOKEN)

ID_DASH = "2de7544a-512b-80de-b980-fecb94b6e5ee"
ID_NODASH = ID_DASH.replace("-", "")

def test(id_val, label):
    print(f"Testing {label}: {id_val}")
    try:
        resp = client.request(
            path=f"databases/{id_val}/query",
            method="POST",
            body={"page_size": 1}
        )
        print(f"✅ Success! Results: {len(resp.get('results',[]))}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test(ID_DASH, "Dashed")
    test(ID_NODASH, "No Dash")
