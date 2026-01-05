
import sys
from notion_client import Client

# Config (Configuración)
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
TARGET_PAGE_TITLE = "Estado Actual — ReporteCobranzas"

client = Client(auth=NOTION_TOKEN)

def get_rich_text(block, field_name):
    # Extract text from rich_text arrays (Extraer texto de arrays rich_text)
    if field_name in block:
        return "".join([t.get("plain_text", "") for t in block[field_name].get("rich_text", [])])
    return ""

def get_block_text(block):
    b_type = block.get("type")
    content = ""
    if b_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "to_do", "toggle"]:
        content = get_rich_text(block, b_type)
    elif b_type == "child_page":
        content = block.get("child_page", {}).get("title", "")
    return content

def get_children_recursive(block_id, depth=0, max_depth=2):
    # Limits depth to avoid infinite loops (Limita profundidad para evitar bucles infinitos)
    if depth > max_depth: return []
    
    results = []
    try:
        children = client.blocks.children.list(block_id=block_id).get("results", [])
        for block in children:
            txt = get_block_text(block)
            b_type = block.get("type")
            checked = block.get("to_do", {}).get("checked", False) if b_type == "to_do" else None
            
            results.append({
                "id": block["id"],
                "type": b_type,
                "text": txt,
                "checked": checked,
                "children": get_children_recursive(block["id"], depth + 1, max_depth) if block.get("has_children") else []
            })
    except Exception as e:
        print(f"Error reading children of {block_id}: {e}")
    return results

def main():
    print("--- FASE 1: LEER (Readback) ---")
    print(f"Buscando página: '{TARGET_PAGE_TITLE}'...")
    search_res = client.search(query=TARGET_PAGE_TITLE).get("results", [])
    
    if not search_res:
        print("❌ Página no encontrada.")
        return

    page_id = search_res[0]["id"]
    print(f"✅ Página encontrada ID: {page_id}")
    
    # Read Top Level Blocks (Leer bloques de nivel superior)
    print("Leyendo bloques principales...")
    blocks = get_children_recursive(page_id, max_depth=2)
    
    sections = {"status": [], "log": [], "backlog": []}
    
    current_section = None
    
    for b in blocks:
        txt = b["text"].lower()
        # Identify sections (Identificar secciones)
        if "estado actual" in txt or "handoff automático" in txt:
            current_section = "status"
        elif "log del proyecto" in txt:
            current_section = "log"
        elif "backlog" in txt:
            current_section = "backlog"
            
        if current_section:
            sections[current_section].append(b)

    # Report Results (Reportar Resultados)
    
    print("\n--- A) ESTADO ACTUAL (Handoff) ---")
    for b in sections["status"]:
        print_block_tree(b)
        
    print("\n--- B) LOG DEL PROYECTO ---")
    # Show last few entries? (¿Mostrar últimas entradas?)
    # Just show all for now to verify match.
    for b in sections["log"]:
        print_block_tree(b)

    print("\n--- C) BACKLOG ---")
    for b in sections["backlog"]:
        print_block_tree(b)

def print_block_tree(block, indent=0):
    prefix = "  " * indent
    check_mark = "[x] " if block.get("checked") is True else "[ ] " if block.get("checked") is False else ""
    print(f"{prefix}- {check_mark}{block['text']}")
    for child in block.get("children", []):
        print_block_tree(child, indent + 1)

if __name__ == "__main__":
    main()
