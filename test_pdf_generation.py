"""
Test script para verificar generación de PDF.
"""
import os
import sys
import pandas as pd

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.whatsapp_sender import generate_pdf_statement
from utils.settings_manager import load_settings

def test_pdf_generation():
    """Prueba la generación de PDF con estado de cuenta"""
    
    print("="*60)
    print("TEST: Generación de PDF Estado de Cuenta")
    print("="*60)
    
    # Cargar configuración
    CONFIG = load_settings()
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo_dacta.png")
    
    # Datos de prueba del cliente
    sample_data = {
        'EMPRESA': 'EMPRESA DE PRUEBA S.A.C.'
    }
    
    # DataFrame de documentos de prueba
    docs_df = pd.DataFrame({
        'COMPROBANTE': ['FAC-001-00123', 'FAC-001-00124', 'BOL-002-00045'],
        'FECH EMIS': pd.to_datetime(['2025-01-01', '2025-01-05', '2025-01-10']),
        'FECH VENC': pd.to_datetime(['2025-02-01', '2025-02-05', '2025-02-10']),
        'MONEDA': ['SOLES', 'DOLARES', 'SOLES'],
        'MONT EMIT': [1000.00, 500.00, 750.00],
        'SALDO REAL': [800.00, 400.00, 750.00],
        'DETRACCIÓN': [80.00, 0.00, 0.00],
        'ESTADO DETRACCION': ['PENDIENTE', 'NO APLICA', 'NO APLICA']
    })
    
    print(f"\n📊 Datos de prueba:")
    print(f"   Empresa: {sample_data['EMPRESA']}")
    print(f"   Documentos: {len(docs_df)}")
    print(f"   Logo: {logo_path}")
    
    print(f"\n🔄 Generando PDF...")
    
    try:
        pdf_path = generate_pdf_statement(sample_data, docs_df, CONFIG, logo_path)
        
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / 1024  # KB
            print(f"\n✅ PDF generado exitosamente!")
            print(f"   Ruta: {pdf_path}")
            print(f"   Tamaño: {file_size:.2f} KB")
            
            # Abrir PDF para inspección visual
            print(f"\n👁️  Abriendo PDF para inspección visual...")
            os.startfile(pdf_path)
            
            return True
        else:
            print(f"\n❌ Error: PDF no generado")
            return False
            
    except ImportError as ie:
        print(f"\n❌ Error de dependencia: {str(ie)}")
        print(f"\n💡 Solución: Ejecuta 'pip install weasyprint'")
        return False
    except Exception as e:
        print(f"\n❌ Error durante generación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    
    if success:
        print(f"\n{'='*60}")
        print("✅ TEST EXITOSO")
        print("="*60)
    else:
        print(f"\n{'='*60}")
        print("❌ TEST FALLIDO")
        print("="*60)
        sys.exit(1)
