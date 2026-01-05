"""
Paso 4: Insertar Reporte Post-Envío al inicio del tab Email
"""

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Código a insertar
post_send_report = """        # --- Renderizar Reporte Post-Envío si existe en session_state ---
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
        
"""

# Buscar la línea "if not df_final.empty:" en el tab Email
for i, line in enumerate(lines):
    if 'if not df_final.empty:' in line and i > 1300 and i < 1320:
        # Insertar después de esta línea
        lines.insert(i+1, post_send_report)
        print(f"✅ Reporte Post-Envío insertado después de línea {i+1}")
        break

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Paso 4 completado")
