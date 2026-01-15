
import sys
import os
import subprocess
import requests
import json

# --- CONFIG INLINE ---
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
if os.path.exists("secrets.txt"):
    try:
        with open("secrets.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if line.startswith("NOTION_TOKEN="):
                    NOTION_TOKEN = line.split("=", 1)[1].strip()
                    break
                elif "=" not in line:
                    NOTION_TOKEN = line.strip()
                    break
    except: pass

PAGE_ID = "2dd7544a-512b-8023-a8ef-caec365ce966"

# 1. LOCAL GIT STATE
print("\n=== VERIFICACIÓN DE ALINEACIÓN FINAL ===\n")
try:
    tag = subprocess.check_output("git describe --tags --abbrev=0", shell=True).decode().strip()
    commit = subprocess.check_output("git rev-parse --short HEAD", shell=True).decode().strip()
    print(f"🖥️  [CÓDIGO LOCAL]")
    print(f"    Tag:    {tag}")
    print(f"    Commit: {commit}")
except:
    print("🖥️  [CÓDIGO LOCAL] Error al leer Git (¿Está el repo correcto?)")
    tag = "Unknown"
    commit = "Unknown"

# 2. NOTION STATE
print("\n☁️  [NOTION DOCOPS]")
try:
    url = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"    Error HTTP: {resp.status_code}")
    else:
        results = resp.json().get("results", [])
        
        found_header = False
        handoff_header = "N/A"
        version_bullet = "N/A"
        commit_bullet = "N/A"
        
        for b in results:
            b_type = b.get("type", "")
            content = ""
            if "rich_text" in b.get(b_type, {}):
                content = "".join([t["plain_text"] for t in b[b_type]["rich_text"]])
            
            if "Handoff Automático" in content:
                handoff_header = content
                found_header = True
                continue
            
            if found_header:
                if b_type.startswith("heading"): break # New section
                if "tag =" in content or "Versión estable" in content:
                    version_bullet = content
                if "hash =" in content or "Commit relevante" in content:
                    commit_bullet = content

        print(f"    Header: {handoff_header}")
        print(f"    Bullet: {version_bullet}")
        print(f"    Bullet: {commit_bullet}")
        
        # COMPARISON
        print("\n⚖️  [RESULTADO]")
        aligned = True
        
        # Check Commit
        if commit in commit_bullet or commit in handoff_header:
            print("    ✅ Commit Coincide")
        else:
            print(f"    ❌ COMMIT DESALINEADO (Local: {commit} vs Notion)")
            aligned = False
            
        # Check Tag
        if tag in version_bullet or tag in handoff_header:
            print("    ✅ Tag Coincide")
        else:
            print(f"    ❌ TAG DESALINEADO (Local: {tag} vs Notion)")
            aligned = False
            
        if aligned:
            print("\n✅ SISTEMA 100% SINCRONIZADO")
        else:
            print("\n⚠️  ATENCIÓN: REVISAR SINCRONIZACIÓN")

except Exception as e:
    print(f"❌ Error script: {e}")
print("\n========================================\n")
