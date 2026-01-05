"""
Paso 2: Agregar guard rail COD CLIENTE en tracking update
"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar el bloque específico
old_code = """                                              if msg and msg.get('match_keys'):
                                                  # Actualizar por MATCH_KEY (estable por documento, no por email)
                                                  for mk in msg['match_keys']:
                                                      mask = st.session_state['df_final']['MATCH_KEY'] == mk
                                                      num_updated = mask.sum()"""

new_code = """                                              if msg and msg.get('match_keys'):
                                                  # Actualizar por MATCH_KEY (estable por documento, no por email)
                                                  # GUARD RAIL: También filtrar por COD CLIENTE para evitar updates masivos
                                                  cod_cliente_msg = msg.get('cod_cliente')
                                                  
                                                  for mk in msg['match_keys']:
                                                      # Filtro doble: MATCH_KEY + COD CLIENTE
                                                      mask = (st.session_state['df_final']['MATCH_KEY'] == mk) & \\
                                                             (st.session_state['df_final']['COD CLIENTE'] == cod_cliente_msg)
                                                      num_updated = mask.sum()"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Guard rail COD CLIENTE agregado")
else:
    print("❌ No se encontró el código a reemplazar")
