import os
from notion_client import Client

# Token hardcoded from fetch_notion_pages.py
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
LOG_PAGE_ID = "2dd7544a512b8095bff0c4e2071c08bb"

def test_write_permission():
    client = Client(auth=NOTION_TOKEN)
    
    print(f"Testing write permission to Page ID: {LOG_PAGE_ID}")
    
    try:
        # Try to append a simple text block
        response = client.blocks.children.append(
            block_id=LOG_PAGE_ID,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "🤖 [Antigravity Auto-Test] Write permission verification."
                                }
                            }
                        ]
                    }
                }
            ]
        )
        print("✅ Success! Block appended.")
        print(response)
        
    except Exception as e:
        print(f"❌ Error writing to Notion: {str(e)}")

if __name__ == "__main__":
    test_write_permission()
