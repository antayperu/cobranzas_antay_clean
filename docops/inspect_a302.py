
import os
import sys
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
client = Client(auth=NOTION_TOKEN)

ID = "2de7544a-512b-80de-a302-e257ebc9735e"

def inspect():
    print(f"Inspecting {ID}...")
    try:
        db = client.databases.retrieve(database_id=ID)
        print(f"✅ RETRIEVE SUCCESS. Title: {db.get('title')}")
    except Exception as e:
        print(f"❌ RETRIEVE FAILED: {e}")

    try:
        client.databases.query(database_id=ID, page_size=1)
        print("✅ QUERY SUCCESS")
    except Exception as e:
        print(f"❌ QUERY FAILED: {e}")

if __name__ == "__main__":
    inspect()
