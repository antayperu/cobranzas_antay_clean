"""
Script para aplicar el fix del bug de tracking automáticamente.
Descomenta st.rerun() en app.py línea 1814-1815
"""

import re

# Leer el archivo
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón a buscar (con comentarios)
pattern = r'(\s+)# if len\(updated_match_keys\) > 0:\s*\n\s+#\s+st\.rerun\(\)\s+# Comentado: permite renderizar reporte post-envío'

# Reemplazo (sin comentarios)
replacement = r'\1if len(updated_match_keys) > 0:\n\1    st.rerun()  # Refresca KPIs + mantiene Reporte Post-Envío vía session_state'

# Aplicar cambio
new_content = re.sub(pattern, replacement, content)

# Guardar
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Fix aplicado: st.rerun() descomentado")
