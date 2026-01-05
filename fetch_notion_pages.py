"""
Script para leer páginas específicas de Notion usando la API
"""
import os
from notion_client import Client

# Token de Notion
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")

# Page IDs extraídos de las URLs
PAGE_IDS = {
    "Estado Actual": "2dd7544a512b8023a8efcaec365ce966",
    "Log del Proyecto": "2dd7544a512b8095bff0c4e2071c08bb",
    "Gate 3 Checklist": "2dd7544a512b803788e9d0194fef6307"
}

def fetch_page_content(client, page_id, page_name):
    """Fetch content from a Notion page"""
    print(f"\n{'='*60}")
    print(f"Leyendo: {page_name}")
    print(f"Page ID: {page_id}")
    print(f"{'='*60}\n")
    
    try:
        # Get page blocks
        response = client.blocks.children.list(block_id=page_id)
        blocks = response.get("results", [])
        
        content_lines = []
        for block in blocks:
            block_type = block.get("type")
            
            if block_type == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                if rich_text:
                    text = " ".join([rt.get("plain_text", "") for rt in rich_text])
                    content_lines.append(text)
            
            elif block_type in ["heading_1", "heading_2", "heading_3"]:
                rich_text = block.get(block_type, {}).get("rich_text", [])
                if rich_text:
                    text = " ".join([rt.get("plain_text", "") for rt in rich_text])
                    prefix = "#" * int(block_type[-1])
                    content_lines.append(f"{prefix} {text}")
            
            elif block_type == "bulleted_list_item":
                rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                if rich_text:
                    text = " ".join([rt.get("plain_text", "") for rt in rich_text])
                    content_lines.append(f"- {text}")
            
            elif block_type == "numbered_list_item":
                rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
                if rich_text:
                    text = " ".join([rt.get("plain_text", "") for rt in rich_text])
                    content_lines.append(f"1. {text}")
            
            elif block_type == "to_do":
                rich_text = block.get("to_do", {}).get("rich_text", [])
                checked = block.get("to_do", {}).get("checked", False)
                if rich_text:
                    text = " ".join([rt.get("plain_text", "") for rt in rich_text])
                    checkbox = "[x]" if checked else "[ ]"
                    content_lines.append(f"{checkbox} {text}")
            
            elif block_type == "divider":
                content_lines.append("---")
        
        return "\n".join(content_lines)
    
    except Exception as e:
        print(f"Error fetching {page_name}: {e}")
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    client = Client(auth=NOTION_TOKEN)
    
    all_content = {}
    for page_name, page_id in PAGE_IDS.items():
        content = fetch_page_content(client, page_id, page_name)
        all_content[page_name] = content
        print(content)
        print("\n")
    
    # Save to file
    output_file = "docs/NOTION_SSOT_PAGES.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Documentación SSOT desde Notion\n\n")
        f.write(f"Fecha de descarga: {os.environ.get('DATE', 'N/A')}\n\n")
        
        for page_name, content in all_content.items():
            f.write(f"\n## {page_name}\n\n")
            f.write(content)
            f.write("\n\n")
    
    print(f"\n✅ Contenido guardado en: {output_file}")
