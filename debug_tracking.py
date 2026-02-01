"""
Script de debug para rastrear el problema de tracking en fullscreen.
Ejecutar ANTES de abrir fullscreen para ver el estado de session_state.
"""

import streamlit as st
import pandas as pd

print("\n" + "="*80)
print("DEBUG TRACKING - Estado de Session State")
print("="*80)

# Verificar flags críticos
print(f"\n1. FLAGS CRÍTICOS:")
print(f"   - data_ready: {st.session_state.get('data_ready', 'NO EXISTE')}")
print(f"   - fresh_load: {st.session_state.get('fresh_load', 'NO EXISTE')}")
print(f"   - tracking_dirty: {st.session_state.get('tracking_dirty', 'NO EXISTE')}")
print(f"   - loading_new_files: {st.session_state.get('loading_new_files', 'NO EXISTE')}")

# Verificar df_final
if 'df_final' in st.session_state:
    df = st.session_state['df_final']
    print(f"\n2. DATAFRAME df_final:")
    print(f"   - Filas totales: {len(df)}")
    
    if 'ESTADO_EMAIL' in df.columns:
        enviados = (df['ESTADO_EMAIL'].str.contains('ENVIADO', na=False)).sum()
        pendientes = (df['ESTADO_EMAIL'] == 'PENDIENTE').sum()
        print(f"   - ENVIADOS: {enviados}")
        print(f"   - PENDIENTES: {pendientes}")
        
        # Mostrar primeros 5 registros
        print(f"\n3. PRIMEROS 5 REGISTROS:")
        for idx, row in df.head(5).iterrows():
            correo = row.get('CORREO', 'N/A')
            estado = row.get('ESTADO_EMAIL', 'N/A')
            fecha = row.get('FECHA_ULTIMO_ENVIO', 'N/A')
            print(f"   [{idx}] {correo[:30]:30s} | {estado:20s} | {fecha}")
    else:
        print(f"   - COLUMNA 'ESTADO_EMAIL' NO EXISTE")
else:
    print(f"\n2. df_final NO EXISTE en session_state")

print("\n" + "="*80 + "\n")
