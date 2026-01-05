"""
Paso 3: Descomentar st.rerun()
"""

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar las líneas comentadas del st.rerun()
for i, line in enumerate(lines):
    if '# if len(updated_match_keys) > 0:' in line and i > 1800:
        # Encontrado! Descomentar estas 2 líneas
        lines[i-2] = lines[i-2].replace('# IMPORTANTE: Forzar rerun para refrescar Reporte General', 
                                         '# IMPORTANTE: Forzar rerun para refrescar KPIs')
        lines[i-1] = lines[i-1].replace('# Los resultados quedan guardados en session_state',
                                         '# Los resultados quedan guardados en session_state para renderizar post-rerun')
        lines[i] = lines[i].replace('# if len(updated_match_keys) > 0:', 
                                     'if len(updated_match_keys) > 0:')
        lines[i+1] = lines[i+1].replace('#     st.rerun()  # Comentado: permite renderizar reporte post-envío (líneas 1817+)',
                                         '    st.rerun()  # Refresca KPIs + mantiene Reporte Post-Envío vía session_state')
        print(f"✅ st.rerun() descomentado en línea {i+1}")
        break

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Paso 3 completado")
