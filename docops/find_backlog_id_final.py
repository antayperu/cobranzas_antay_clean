
import os
import sys
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
client = Client(auth=NOTION_TOKEN)

def find():
    print("Searching for 'Backlog — ReporteCobranzas'...")
    results = client.search(query="Backlog — ReporteCobranzas").get("results", [])
    for r in results:
        if r["object"] == "database":
            title = "".join([t["plain_text"] for t in r.get("title", [])])
            print(f"FOUND: {title} ID: {r['id']}")

if __name__ == "__main__":
    find()
