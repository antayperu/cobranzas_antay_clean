import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Configuración
NOTION_VERSION = "2022-06-28"
# ID de la página proporcionado por el usuario
PAGE_ID = "2de7544a512b80deb980fecb94b6e5ee"

def get_notion_token():
    """Obtiene el token de Notion desde .mcp.json."""
    try:
        mcp_path = Path(__file__).parent.parent / ".mcp.json"
        with open(mcp_path, 'r') as f:
            config = json.load(f)
            headers = json.loads(config['mcpServers']['notion']['env']['OPENAPI_MCP_HEADERS'])
            token = headers['Authorization'].replace('Bearer ', '')
            return token
    except Exception as e:
        print(f"Error leyendo token: {e}")
        return None

def get_project_status():
    """Lee el estado actual del proyecto."""
    # (Misma implementación anterior, simplificada para el ejemplo)
    status = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "v1.5.6",
        "integracion": "40%"
    }
    return status

def sync_to_notion(token, database_id, content):
    """Crea una nueva página en la base de datos de Notion."""
    url = "https://api.notion.com/v1/pages"
    
    # Payload para crear página en base de datos
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {
                "title": [
                    {"text": {"content": f"Status Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Versión: v1.5.6 | Integración Supabase: 40%\n\n{content[:1800]}..."}}]
                }
            }
        ]
    }
    
    data = json.dumps(payload).encode('utf-8')
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Respuesta Notion: {response.status}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Error API Notion: {e.code} - {error_body}")
        
        # Si falla por nombre de propiedad, intentar "Title" o "Task"
        if "properties.Name" in error_body:
            print("⚠️ Reintentando con propiedad 'Title'...")
            payload["properties"] = {
                "Title": {
                    "title": [{"text": {"content": f"Status Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
                }
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            try:
                with urllib.request.urlopen(req) as response:
                    print(f"Respuesta Notion (Reintento): {response.status}")
                    return True
            except Exception as e2:
                print(f"Fallo reintento: {e2}")
                return False
                
        return False
    except Exception as e:
        print(f"Error conexión: {e}")
        return False

def main():
    print("🔄 Iniciando sincronización Notion...")
    token = get_notion_token()
    if not token:
        print("❌ No se encontró token en .mcp.json")
        return 1
        
    # Leer backlog local
    backlog_path = Path(__file__).parent.parent / "docs" / "backlog_priorizado.md"
    content = ""
    if backlog_path.exists():
        with open(backlog_path, 'r', encoding='utf-8') as f:
            content = f.read()
    
    success = sync_to_notion(token, PAGE_ID, content)
    
    if success:
        print("✅ Sincronización Exitosa!")
        return 0
    else:
        print("❌ Falló la sincronización")
        return 1

if __name__ == "__main__":
    exit(main())
