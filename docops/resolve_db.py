
import os
import sys
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
client = Client(auth=NOTION_TOKEN)

# User provided ID from URL
PROVIDED_ID = "2de7544a-512b-80de-b980-fecb94b6e5ee"

def resolve():
    print(f"Scanning children of {PROVIDED_ID}...")
    try:
        children = client.blocks.children.list(block_id=PROVIDED_ID).get("results", [])
        for b in children:
            if b["type"] == "child_database":
                title = b["child_database"].get("title", "Untitled")
                print(f"✅ FOUND CHILD DATABASE: {title} (ID: {b['id']})")
                return b['id']
            # Also check linked_db?
            if b["type"] == "linked_database": # not standard type name?
                 print(f"Found linked: {b['id']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    resolve()
