import os
import json
import sys
from pathlib import Path
from notion_client import Client

# IDs provided by user
# Page: ReporteCobranzas
PAGE_ID_DOCS = "2dd7544a512b800abdf3d65c5c42089d"
# DB: Backlog
DATABASE_ID_BACKLOG = "2de7544a512b80deb980fecb94b6e5ee"

def get_notion_token():
    try:
        mcp_path = Path("c:/dev/ReporteCobranzas/.mcp.json")
        if not mcp_path.exists():
            print(f"❌ .mcp.json not found at {mcp_path}")
            return None
        with open(mcp_path, 'r') as f:
            config = json.load(f)
            env_headers = config.get('mcpServers', {}).get('notion', {}).get('env', {}).get('OPENAPI_MCP_HEADERS')
            if env_headers:
                 headers = json.loads(env_headers)
                 token = headers.get('Authorization', '').replace('Bearer ', '')
                 return token
            return None
    except Exception as e:
        print(f"Error reading token: {e}")
        return None

def inspect_database(client, db_id):
    print(f"\n--- Inspecting Object ID {db_id} ---")
    try:
        # 1. Try retrieving as Database
        try:
            db_obj = client.databases.retrieve(database_id=db_id)
            obj_type = db_obj.get('object', 'unknown')
            print(f"Object Type: {obj_type}")
            
            if obj_type == 'database':
                print("✅ Found Database!")
                print("Properties:")
                for name, prop in db_obj.get('properties', {}).items():
                    print(f"  - {name} ({prop['type']})")
                    if prop['type'] in ['select', 'status']:
                        options = [opt['name'] for opt in prop[prop['type']]['options']]
                        print(f"    Options: {options}")
                
                print("\nQuerying Items...")
                res = client.databases.query(database_id=db_id, page_size=5)
                for page in res.get('results', []):
                    title = "Untitled"
                    status = "None"
                    # Find Title
                    for k, v in page['properties'].items():
                        if v['type'] == 'title':
                            t_list = v.get('title', []) 
                            if t_list: title = t_list[0].get('plain_text', '')
                    # Find Status
                    for k, v in page['properties'].items():
                        if v['type'] == 'status':
                            status = v['status']['name']
                        elif v['type'] == 'select':
                             if v['select']: status = v['select']['name']
                    
                    print(f"  [{status}] {title} ({page['id']})")
                return

        except Exception as e:
            print(f"Not a database or error retrieving: {e}")

        # 2. Try retrieving as Page and look for child database
        try:
             page_obj = client.pages.retrieve(page_id=db_id)
             print(f"Object Type: {page_obj.get('object', 'unknown')}")
             if page_obj.get('object') == 'page':
                  print("It's a PAGE. Looking for child databases...")
                  children = client.blocks.children.list(block_id=db_id)
                  found = False
                  for block in children.get('results', []):
                      if block['type'] == 'child_database':
                          print(f"Found Child DB: '{block['child_database']['title']}' ID: {block['id']}")
                          inspect_database(client, block['id'])
                          found = True
                  if not found:
                      print("No child databases found in this page.")
        except Exception as e:
             print(f"Not a page or error retrieving: {e}")

    except Exception as e:
        print(f"Critical Error: {e}")

def main():
    token = get_notion_token()
    if not token: return
    
    client = Client(auth=token)
    inspect_database(client, DATABASE_ID_BACKLOG)

if __name__ == "__main__":
    main()
