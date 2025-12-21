"""
Test Unitario Completo - WhatsApp Pro v5.0
Valida generación de imagen ejecutiva y PDF
"""
import os
import sys
import pandas as pd

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.whatsapp_sender import generate_executive_card_image, generate_pdf_statement
from utils.settings_manager import load_settings

def test_whatsapp_v5_complete():
    """Test completo del sistema v5.0"""
    
    print("="*70)
    print("TEST UNITARIO: WhatsApp Pro v5.0 - Generación Completa")
    print("="*70)
    
    # 1. Cargar configuración
    print("\n[1/5] Cargando configuración...")
    try:
        CONFIG = load_settings()
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_dacta.png")
        
        if not os.path.exists(logo_path):
            print(f"   ⚠️  Logo no encontrado en: {logo_path}")
            logo_path = None
        else:
            print(f"   ✅ Logo encontrado: {logo_path}")
        
        print(f"   ✅ Configuración cargada")
    except Exception as e:
        print(f"   ❌ Error cargando configuración: {e}")
        return False
    
    # 2. Preparar datos de prueba
    print("\n[2/5] Preparando datos de prueba...")
    try:
        # Datos del cliente
        sample_client = {
            'EMPRESA': 'MACLABI S.A.C.',
            'TOTAL_SALDO_S': 'S/ 15,450.00',
            'TOTAL_SALDO_D': '$ 2,300.00',
            'COUNT_DOCS_S': 5,
            'COUNT_DOCS_D': 2,
            'nombre_cliente': 'MACLABI S.A.C.',
            'telefono': '+51921566036'
        }
        
        # DataFrame de documentos
        docs_data = {
            'COMPROBANTE': ['FAC-001', 'FAC-002', 'FAC-003'],
            'FECHA EMISION': ['2024-01-15', '2024-02-20', '2024-03-10'],
            'FECHA VENCIMIENTO': ['2024-02-15', '2024-03-20', '2024-04-10'],
            'MONEDA': ['SOLES', 'DOLARES', 'SOLES'],
            'SALDO REAL': [5000.00, 2300.00, 10450.00],
            'DIAS VENCIDOS': [45, 30, 15]
        }
        sample_client['docs_df'] = pd.DataFrame(docs_data)
        
        print(f"   ✅ Cliente: {sample_client['EMPRESA']}")
        print(f"   ✅ Documentos: {len(sample_client['docs_df'])} registros")
    except Exception as e:
        print(f"   ❌ Error preparando datos: {e}")
        return False
    
    # 3. Test: Generación de Imagen Ejecutiva
    print("\n[3/5] Generando Imagen Ejecutiva...")
    img_path = None
    try:
        img_path = generate_executive_card_image(
            sample_client,
            CONFIG,
            logo_path
        )
        
        if img_path and os.path.exists(img_path):
            file_size = os.path.getsize(img_path) / 1024  # KB
            print(f"   ✅ Imagen generada: {os.path.basename(img_path)}")
            print(f"   ✅ Tamaño: {file_size:.2f} KB")
            print(f"   ✅ Ruta: {img_path}")
        else:
            print(f"   ❌ Imagen no generada o no existe")
            return False
            
    except Exception as e:
        print(f"   ❌ Error generando imagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Test: Generación de PDF
    print("\n[4/5] Generando PDF Estado de Cuenta...")
    pdf_path = None
    try:
        pdf_path = generate_pdf_statement(
            sample_client,
            sample_client['docs_df'],
            CONFIG,
            logo_path
        )
        
        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / 1024  # KB
            print(f"   ✅ PDF generado: {os.path.basename(pdf_path)}")
            print(f"   ✅ Tamaño: {file_size:.2f} KB")
            print(f"   ✅ Ruta: {pdf_path}")
        else:
            print(f"   ❌ PDF no generado o no existe")
            return False
            
    except Exception as e:
        print(f"   ❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Verificación Final
    print("\n[5/5] Verificación Final...")
    try:
        # Verificar que ambos archivos existen
        img_exists = img_path and os.path.exists(img_path)
        pdf_exists = pdf_path and os.path.exists(pdf_path)
        
        print(f"   {'✅' if img_exists else '❌'} Imagen ejecutiva: {'EXISTE' if img_exists else 'NO EXISTE'}")
        print(f"   {'✅' if pdf_exists else '❌'} PDF estado cuenta: {'EXISTE' if pdf_exists else 'NO EXISTE'}")
        
        if img_exists and pdf_exists:
            print("\n" + "="*70)
            print("✅ TEST EXITOSO - Todos los componentes funcionan correctamente")
            print("="*70)
            print("\n📋 ARCHIVOS GENERADOS:")
            print(f"   1. Imagen: {img_path}")
            print(f"   2. PDF:    {pdf_path}")
            print("\n💡 Los archivos se han dejado para inspección manual.")
            print("   Puedes abrirlos para verificar la calidad y contenido.")
            return True
        else:
            print("\n" + "="*70)
            print("❌ TEST FALLIDO - Algunos componentes no funcionaron")
            print("="*70)
            return False
            
    except Exception as e:
        print(f"   ❌ Error en verificación: {e}")
        return False

if __name__ == "__main__":
    success = test_whatsapp_v5_complete()
    sys.exit(0 if success else 1)
