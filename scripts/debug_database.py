import os
import json
import sys
from pathlib import Path
from notion_client import Client

DATABASE_ID = "2de7544a512b80deb980fecb94b6e5ee"

def get_notion_token():
    try:
        mcp_path = Path("c:/dev/ReporteCobranzas/.mcp.json")
        with open(mcp_path, 'r') as f:
            config = json.load(f)
            env_headers = config.get('mcpServers', {}).get('notion', {}).get('env', {}).get('OPENAPI_MCP_HEADERS')
            if env_headers:
                 headers = json.loads(env_headers)
                 token = headers.get('Authorization', '').replace('Bearer ', '')
                 return token
    except: return None

def main():
    token = get_notion_token()
    client = Client(auth=token)
    
    try:
        db = client.databases.retrieve(database_id=DATABASE_ID)
        print("Success retrieving!")
        print(f"Object type: {db.get('object')}")
        print(f"Keys: {list(db.keys())}")
        
        if 'properties' in db:
             print("Has properties!")
        else:
             print("NO properties key found.")

        print("\nAttempting QUERY...")
        res = client.databases.query(database_id=DATABASE_ID, page_size=2)
        print(f"Query Results: {len(res['results'])} items found.")
        if res['results']:
            item = res['results'][0]
            print("First Item Properties Keys:", list(item['properties'].keys()))
            # Print status possibilities from item if possible?
            # No, item has values, not schema.
            # But we can see the property names.
            for k, v in item['properties'].items():
                print(f" - {k}: {v['type']}")
                if v['type'] == 'status':
                    print(f"   Value: {v['status']}")
                if v['type'] == 'select':
                    print(f"   Value: {v['select']}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        # Try listing databases to see if we have access?
        # search = client.search(filter={"value": "database", "property": "object"})
        # print("Available Databases:", [r['id'] for r in search['results']])

if __name__ == "__main__":
    main()
