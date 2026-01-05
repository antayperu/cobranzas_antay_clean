"""
Test script para verificar generación de tarjeta ejecutiva.
"""
import os
import sys

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.whatsapp_sender import generate_executive_card_image
from utils.settings_manager import load_settings

def test_executive_card():
    """Prueba la generación de tarjeta ejecutiva"""
    
    print("="*60)
    print("TEST: Generación de Tarjeta Ejecutiva")
    print("="*60)
    
    # Cargar configuración
    CONFIG = load_settings()
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo_dacta.png")
    
    # Datos de prueba
    sample_data = {
        'EMPRESA': 'EMPRESA DE PRUEBA S.A.C.',
        'TOTAL_SALDO_S': 'S/ 15,450.00',
        'TOTAL_SALDO_D': '$ 2,300.00',
        'COUNT_DOCS_S': 5,
        'COUNT_DOCS_D': 2
    }
    
    print(f"\n📊 Datos de prueba:")
    print(f"   Empresa: {sample_data['EMPRESA']}")
    print(f"   Soles: {sample_data['TOTAL_SALDO_S']} ({sample_data['COUNT_DOCS_S']} docs)")
    print(f"   Dólares: {sample_data['TOTAL_SALDO_D']} ({sample_data['COUNT_DOCS_D']} docs)")
    print(f"   Logo: {logo_path}")
    
    print(f"\n🔄 Generando tarjeta ejecutiva...")
    
    try:
        img_path = generate_executive_card_image(sample_data, CONFIG, logo_path)
        
        if os.path.exists(img_path):
            file_size = os.path.getsize(img_path) / 1024  # KB
            print(f"\n✅ Tarjeta generada exitosamente!")
            print(f"   Ruta: {img_path}")
            print(f"   Tamaño: {file_size:.2f} KB")
            
            # Abrir imagen para inspección visual
            print(f"\n👁️  Abriendo imagen para inspección visual...")
            os.startfile(img_path)
            
            return True
        else:
            print(f"\n❌ Error: Imagen no generada")
            return False
            
    except Exception as e:
        print(f"\n❌ Error durante generación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_executive_card()
    
    if success:
        print(f"\n{'='*60}")
        print("✅ TEST EXITOSO")
        print("="*60)
    else:
        print(f"\n{'='*60}")
        print("❌ TEST FALLIDO")
        print("="*60)
        sys.exit(1)
