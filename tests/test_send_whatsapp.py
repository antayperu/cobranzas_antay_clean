"""
Test de envío de mensaje WhatsApp - Ejecutar desde VS Code terminal
Uso: python tests/test_send_whatsapp.py
"""
import sys
import os

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.whatsapp_sender import send_whatsapp_messages_direct

# ──────────────────────────────────────────
# DATOS DE PRUEBA
# ──────────────────────────────────────────
TEST_CONTACTS = [
    {
        "nombre_cliente": "Carlos Test",
        "nombre": "Carlos Test",
        "telefono": "+51921566036",
        "monto_deuda": "1,500.00",
        "nro_cuenta": "CTA-0001",
        "dias_vencido": "30",
    }
]

TEST_MESSAGE = (
    "Hola {nombre_cliente}, este es un mensaje de prueba del sistema Antay. "
    "Monto pendiente: S/ {monto_deuda}. "
    "Por favor ignorar, es solo una validación técnica."
)

# ──────────────────────────────────────────
# CALLBACK DE PROGRESO (muestra en consola)
# ──────────────────────────────────────────
def progress_callback(current, total, status, log_text):
    print(f"  [{current}/{total}] {status}")
    # Imprimir solo las últimas líneas del log para no saturar
    lines = log_text.strip().split("\n")
    for line in lines[-3:]:
        print(f"    {line}")
    print()


# ──────────────────────────────────────────
# EJECUTAR
# ──────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  TEST ENVÍO WHATSAPP - ANTAY COBRANZAS")
    print("=" * 60)
    print(f"  Destinatario: {TEST_CONTACTS[0]['telefono']}")
    print(f"  Mensaje: {TEST_MESSAGE[:80]}...")
    print("=" * 60)
    print()

    resultado = send_whatsapp_messages_direct(
        contacts=TEST_CONTACTS,
        message=TEST_MESSAGE,
        speed="Normal (Recomendado)",
        progress_callback=progress_callback,
        send_mode="texto",
    )

    print()
    print("=" * 60)
    print("  RESULTADO FINAL")
    print("=" * 60)
    print(f"  ✅ Exitosos : {resultado['exitosos']}")
    print(f"  ❌ Fallidos : {resultado['fallidos']}")
    print(f"  📊 Total    : {resultado.get('total', resultado['exitosos'] + resultado['fallidos'])}")
    if resultado['errores']:
        print(f"  ⚠️  Errores  :")
        for e in resultado['errores']:
            print(f"     - {e}")
    print("=" * 60)
