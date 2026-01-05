"""
Script para mover el Resumen del Proceso al inicio del tab Email
para que sea visible después del st.rerun()
"""

# Leer el archivo
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Código a insertar después de línea 1305 (if not df_final.empty:)
post_send_report_code = '''        # --- Renderizar Reporte Post-Envío si existe en session_state ---
        if 'last_send_results' in st.session_state and st.session_state['last_send_results']:
            results = st.session_state['last_send_results']
            
            st.success("✅ Envío completado. Resultados del último proceso:")
            
            # --- RC-UX-002: Panel de Resultados Amigable ---
            st.divider()
            st.subheader("📊 Resumen del Proceso")
            
            # A) Resumen Ejecutivo (Métricas)
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Enviados", results['success'])
            c2.metric("❌ Fallidos", results['failed'])
            c3.metric("🔒 Bloqueados (TTL)", results.get('blocked', 0))
            
            # B) Tabla de Detalles (Negocio)
            if 'details' in results and results['details']:
                import pandas as pd
                df_res = pd.DataFrame(results['details'])
                
                st.write("📝 **Detalle por Cliente:**")
                st.dataframe(
                    df_res[['Cliente', 'Email', 'Estado', 'Detalle']], 
                    use_container_width=True,
                    hide_index=True
                )
                
                # Botón descarga
                csv = df_res.to_csv(index=False).encode('utf-8')
                batch_id = st.session_state.get('last_processed_batch_id', 'unknown')
                st.download_button(
                    "📄 Descargar Reporte de Envío (CSV)",
                    data=csv,
                    file_name=f"reporte_envio_{batch_id[:8]}.csv",
                    mime="text/csv"
                )
            
            # Botón para cerrar el reporte
            if st.button("✅ Cerrar Reporte"):
                del st.session_state['last_send_results']
                st.rerun()
            
            st.divider()
        
'''

# Insertar después de línea 1305 (índice 1305 porque las líneas empiezan en 0)
lines.insert(1306, post_send_report_code)

# Comentar el bloque original (líneas 1819-1882 aproximadamente, ahora desplazadas)
# Buscar el inicio del bloque original
for i, line in enumerate(lines):
    if '# --- RC-UX-002: Panel de Resultados Amigable ---' in line and i > 1400:
        # Comentar desde aquí hasta el final del bloque
        # Encontrar el final (después del expander de QA)
        for j in range(i, min(i + 100, len(lines))):
            if 'st.text(l)' in lines[j] and 'for l in results' in lines[j-1]:
                # Comentar todo el bloque
                for k in range(i, j+2):
                    if not lines[k].strip().startswith('#'):
                        lines[k] = '                            # ' + lines[k].lstrip()
                break
        break

# Guardar
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Resumen del Proceso movido al inicio del tab")
