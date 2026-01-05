
import os
import sys
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
client = Client(auth=NOTION_TOKEN)

ID = "2de7544a-512b-80de-b980-fecb94b6e5ee"

def inspect():
    print(f"Inspecting {ID}...")
    
    # Try as Database
    try:
        db = client.databases.retrieve(database_id=ID)
        print(f"✅ It is a DATABASE. Title: {db.get('title')}")
        return
    except Exception as e:
        print(f"Not a database: {e}")

    # Try as Page
    try:
        pg = client.pages.retrieve(page_id=ID)
        print(f"✅ It is a PAGE. Parent: {pg.get('parent')}")
        return
    except Exception as e:
        print(f"Not a page: {e}")
        
    # Try as Block
    try:
        blk = client.blocks.retrieve(block_id=ID)
        print(f"✅ It is a BLOCK. Type: {blk.get('type')}")
        return
    except Exception as e:
        print(f"Not a block: {e}")

if __name__ == "__main__":
    inspect()
