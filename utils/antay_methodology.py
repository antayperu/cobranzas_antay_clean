import os
from notion_client import Client
# Credenciales y Page ID Oficiales (Antay Fábrica de Software)
NOTION_TOKEN = "***REMOVED***"
PAGE_ID = "2377544a512b804db020d8e8b62fd00d"
OUTPUT_FILE = "docs/ANTAY_METHODOLOGY.md"
def get_block_content(block):
    block_type = block.get("type")
    content = ""
    prefix = ""
    
    if block_type == "paragraph":
        rich_text = block.get("paragraph", {}).get("rich_text", [])
        if rich_text:
            content = rich_text[0].get("plain_text", "")
    elif block_type == "heading_1":
        prefix = "# "
        rich_text = block.get("heading_1", {}).get("rich_text", [])
        if rich_text:
            content = rich_text[0].get("plain_text", "")
    elif block_type == "heading_2":
        prefix = "## "
        rich_text = block.get("heading_2", {}).get("rich_text", [])
        if rich_text:
            content = rich_text[0].get("plain_text", "")
    elif block_type == "heading_3":
        prefix = "### "
        rich_text = block.get("heading_3", {}).get("rich_text", [])
        if rich_text:
            content = rich_text[0].get("plain_text", "")
    elif block_type == "bulleted_list_item":
        prefix = "- "
        rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
        if rich_text:
            content = rich_text[0].get("plain_text", "")
    elif block_type == "numbered_list_item":
        prefix = "1. "
        rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
        if rich_text:
            content = rich_text[0].get("plain_text", "")
    elif block_type == "child_page":
        title = block.get("child_page", {}).get("title", "Sub-página")
        content = f"[{title}]"
        prefix = "### " 
    elif block_type == "link_to_page":
        link_info = block.get("link_to_page", {})
        page_id = link_info.get("page_id")
        content = f"[LINK TO PAGE] ID: {page_id}"
        prefix = "### "
    elif block_type == "child_database":
        title = block.get("child_database", {}).get("title", "Base de Datos")
        content = f"[DATABASE: {title}]"
        prefix = "### "
    else:
        # Debug para bloques desconocidos
        print(f"  [DEBUG] Unknown block type: {block_type} - ID: {block.get('id')}")
    if content:
        return f"{prefix}{content}"
    return f"[BLOCK: {block_type}]"
def fetch_children_recursive(client, block_id, depth=0, file_handle=None):
    indent = "  " * depth
    try:
        response = client.blocks.children.list(block_id=block_id)
        results = response.get("results", [])
        
        for block in results:
            text = get_block_content(block)
            if text:
                print(f"{indent}{text}")
                if file_handle:
                    file_handle.write(f"{indent}{text}\n")
            
            if block.get("has_children"):
                fetch_children_recursive(client, block["id"], depth + 1, file_handle)
                
    except Exception as e:
        print(f"{indent}Error fetching children for {block_id}: {e}")
def fetch_antay_methodology():
    print(f"Conectando a Notion (Page ID: {PAGE_ID})...")
    client = Client(auth=NOTION_TOKEN)
    
    # Ensure docs directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Metodología Antay Fábrica de Software\n")
        f.write(f"# Última sincronización: {os.environ.get('USERNAME', 'User')} - [LIVE NOTION FETCH]\n\n")
        print("Descargando última versión viva desde Notion...")
        fetch_children_recursive(client, PAGE_ID, file_handle=f)
    
    print(f"\n[OK] Metodología VIVA actualizada correctamente en: {OUTPUT_FILE}")
    print("      Utilice este archivo como SSOT para la sesión actual.")
if __name__ == "__main__":
    fetch_antay_methodology()
