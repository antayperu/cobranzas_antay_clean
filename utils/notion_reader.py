"""
Notion Reader - Módulo para leer la metodología de Antay Fábrica de Software desde Notion.

Este módulo permite acceder a la documentación de metodología almacenada en Notion
para alinear los desarrollos con los estándares de Antay.
"""

import os
from notion_client import Client
from typing import Dict, List, Optional, Any
import json


class NotionMethodologyReader:
    """
    Cliente para leer la metodología de Antay desde Notion.
    """
    
    # Page ID extraído del link: https://www.notion.so/Antay-F-brica-de-Software-2377544a512b80048f40e7cd8568c09c
    METHODOLOGY_PAGE_ID = "2377544a512b80048f40e7cd8568c09c"
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa el cliente de Notion.
        
        Args:
            token: Integration token de Notion. Si no se proporciona, se busca en variable de entorno.
        """
        self.token = token or os.getenv("NOTION_TOKEN")
        if not self.token:
            raise ValueError(
                "No se encontró el token de Notion. "
                "Proporciona el token o configura la variable de entorno NOTION_TOKEN"
            )
        
        self.client = Client(auth=self.token)
        self.methodology_cache = None
    
    def get_page_content(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene el contenido de una página de Notion.
        
        Args:
            page_id: ID de la página. Si no se proporciona, usa la página de metodología.
        
        Returns:
            Diccionario con el contenido de la página.
        """
        page_id = page_id or self.METHODOLOGY_PAGE_ID
        
        try:
            # Obtener metadata de la página
            page = self.client.pages.retrieve(page_id=page_id)
            
            # Obtener bloques (contenido) de la página
            blocks = self.client.blocks.children.list(block_id=page_id)
            
            return {
                "page": page,
                "blocks": blocks
            }
        except Exception as e:
            raise Exception(f"Error al leer la página de Notion: {str(e)}")
    
    def get_methodology(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtiene la metodología de Antay desde Notion.
        
        Args:
            force_refresh: Si es True, fuerza la recarga desde Notion ignorando el cache.
        
        Returns:
            Diccionario con la metodología completa.
        """
        if self.methodology_cache and not force_refresh:
            return self.methodology_cache
        
        content = self.get_page_content()
        self.methodology_cache = content
        return content
    
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extrae el texto plano de los bloques de Notion.
        
        Args:
            blocks: Lista de bloques de Notion.
        
        Returns:
            Texto plano concatenado.
        """
        text_parts = []
        
        for block in blocks.get("results", []):
            block_type = block.get("type")
            
            if block_type == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                text_parts.append(text)
            
            elif block_type == "heading_1":
                rich_text = block.get("heading_1", {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                text_parts.append(f"\n# {text}\n")
            
            elif block_type == "heading_2":
                rich_text = block.get("heading_2", {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                text_parts.append(f"\n## {text}\n")
            
            elif block_type == "heading_3":
                rich_text = block.get("heading_3", {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                text_parts.append(f"\n### {text}\n")
            
            elif block_type == "bulleted_list_item":
                rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                text_parts.append(f"- {text}")
            
            elif block_type == "numbered_list_item":
                rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                text_parts.append(f"1. {text}")
            
            elif block_type == "code":
                rich_text = block.get("code", {}).get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text])
                language = block.get("code", {}).get("language", "")
                text_parts.append(f"\n```{language}\n{text}\n```\n")
        
        return "\n".join(text_parts)
    
    def get_child_pages(self, page_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene las páginas hijas de una página.
        
        Args:
            page_id: ID de la página padre. Si no se proporciona, usa la página de metodología.
        
        Returns:
            Lista de páginas hijas.
        """
        page_id = page_id or self.METHODOLOGY_PAGE_ID
        
        try:
            blocks = self.client.blocks.children.list(block_id=page_id)
            child_pages = []
            
            for block in blocks.get("results", []):
                if block.get("type") == "child_page":
                    child_page_id = block.get("id")
                    child_page = self.client.pages.retrieve(page_id=child_page_id)
                    child_pages.append({
                        "id": child_page_id,
                        "title": block.get("child_page", {}).get("title", "Sin título"),
                        "page": child_page
                    })
            
            return child_pages
        except Exception as e:
            print(f"⚠️ Error al obtener páginas hijas: {str(e)}")
            return []
    
    def get_methodology_as_markdown(self, force_refresh: bool = False, include_subpages: bool = True) -> str:
        """
        Obtiene la metodología en formato Markdown.
        
        Args:
            force_refresh: Si es True, fuerza la recarga desde Notion.
            include_subpages: Si es True, incluye el contenido de las subpáginas.
        
        Returns:
            Contenido de la metodología en formato Markdown.
        """
        methodology = self.get_methodology(force_refresh=force_refresh)
        blocks = methodology.get("blocks", {})
        markdown_content = self.extract_text_from_blocks(blocks)
        
        # Si se solicita incluir subpáginas, obtenerlas y agregarlas
        if include_subpages:
            child_pages = self.get_child_pages()
            
            if child_pages:
                markdown_content += "\n\n---\n\n# 📚 Subpáginas de la Metodología\n\n"
                
                for i, child in enumerate(child_pages, 1):
                    print(f"📄 Procesando subpágina {i}/{len(child_pages)}: {child['title']}")
                    
                    # Obtener contenido de la subpágina
                    try:
                        child_blocks = self.client.blocks.children.list(block_id=child["id"])
                        child_content = self.extract_text_from_blocks(child_blocks)
                        
                        markdown_content += f"\n\n## {i}. {child['title']}\n\n"
                        markdown_content += child_content
                        markdown_content += "\n\n---\n"
                    except Exception as e:
                        print(f"⚠️ Error al procesar subpágina '{child['title']}': {str(e)}")
                        markdown_content += f"\n\n## {i}. {child['title']}\n\n"
                        markdown_content += f"*Error al cargar contenido: {str(e)}*\n\n---\n"
        
        return markdown_content
    
    def save_methodology_to_file(self, output_path: str, force_refresh: bool = False) -> str:
        """
        Guarda la metodología en un archivo local.
        
        Args:
            output_path: Ruta donde guardar el archivo.
            force_refresh: Si es True, fuerza la recarga desde Notion.
        
        Returns:
            Ruta del archivo guardado.
        """
        markdown_content = self.get_methodology_as_markdown(force_refresh=force_refresh)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        return output_path


def test_connection(token: str) -> bool:
    """
    Prueba la conexión con Notion y verifica el acceso a la página de metodología.
    
    Args:
        token: Integration token de Notion.
    
    Returns:
        True si la conexión es exitosa, False en caso contrario.
    """
    try:
        reader = NotionMethodologyReader(token=token)
        content = reader.get_methodology()
        print("✅ Conexión exitosa con Notion")
        print(f"📄 Página encontrada: {content['page'].get('id')}")
        
        # Mostrar preview del contenido
        markdown = reader.get_methodology_as_markdown()
        print("\n📖 Preview de la metodología:")
        print("=" * 80)
        print(markdown[:500] + "..." if len(markdown) > 500 else markdown)
        print("=" * 80)
        
        return True
    except Exception as e:
        print(f"❌ Error al conectar con Notion: {str(e)}")
        return False


if __name__ == "__main__":
    # Test de conexión
    import sys
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = os.getenv("NOTION_TOKEN")
    
    if not token:
        print("❌ No se proporcionó un token. Uso: python notion_reader.py <token>")
        sys.exit(1)
    
    test_connection(token)
