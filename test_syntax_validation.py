"""
Test de Validación de Sintaxis - WhatsApp Sender
Verifica que no hay errores de sintaxis y que las funciones se pueden importar
"""
import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("TEST DE VALIDACIÓN - WhatsApp Sender")
print("="*70)

# Test 1: Importar módulo
print("\n[1/3] Validando importación del módulo...")
try:
    from utils import whatsapp_sender
    print("   ✅ Módulo importado correctamente")
except SyntaxError as e:
    print(f"   ❌ ERROR DE SINTAXIS: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

# Test 2: Verificar funciones existen
print("\n[2/3] Verificando funciones principales...")
try:
    assert hasattr(whatsapp_sender, 'send_whatsapp_messages_direct'), "Falta send_whatsapp_messages_direct"
    assert hasattr(whatsapp_sender, 'generate_executive_card_image'), "Falta generate_executive_card_image"
    assert hasattr(whatsapp_sender, 'generate_pdf_statement'), "Falta generate_pdf_statement"
    assert hasattr(whatsapp_sender, '_check_pdf_sent'), "Falta _check_pdf_sent"
    print("   ✅ Todas las funciones existen")
except AssertionError as e:
    print(f"   ❌ FUNCIÓN FALTANTE: {e}")
    sys.exit(1)

# Test 3: Verificar firma de función principal
print("\n[3/3] Verificando firma de send_whatsapp_messages_direct...")
try:
    import inspect
    sig = inspect.signature(whatsapp_sender.send_whatsapp_messages_direct)
    params = list(sig.parameters.keys())
    
    required_params = ['contacts', 'message', 'speed', 'progress_callback', 'send_mode', 'branding_config', 'logo_path']
    for param in required_params:
        assert param in params, f"Falta parámetro: {param}"
    
    print(f"   ✅ Firma correcta: {len(params)} parámetros")
    print(f"   📋 Parámetros: {', '.join(params)}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ VALIDACIÓN EXITOSA - Código sin errores de sintaxis")
print("="*70)
print("\n💡 El código está listo para pruebas funcionales")
print("   Próximo paso: Prueba end-to-end con WhatsApp Web")
sys.exit(0)
