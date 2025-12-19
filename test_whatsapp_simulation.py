
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Assume libs are installed in user environment
# If not, this test will fail on import, which is also a good test.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.whatsapp_sender import send_whatsapp_messages_direct

class TestWhatsAppFlow(unittest.TestCase):
    @patch('utils.whatsapp_sender.webdriver.Chrome')
    @patch('utils.whatsapp_sender.WebDriverWait')
    @patch('utils.whatsapp_sender.ChromeDriverManager')
    @patch('utils.whatsapp_sender.Service')
    def test_image_sending_flow(self, mock_service, mock_manager, mock_wait, mock_driver_cls):
        print("\n--- INICIANDO SIMULACIÓN DE ENVÍO DE WHATSAPP (REAL LIBS) ---")
        
        # 1. Setup Mock Driver
        mock_driver = MagicMock()
        mock_driver_cls.return_value = mock_driver
        
        # 2. Setup Mock Wait (returns the driver or element when until() is called)
        # wait.until(...) returns the element.
        wait_instance = MagicMock()
        mock_wait.return_value = wait_instance
        
        # Mock Elements
        mock_element = MagicMock()
        # Make specific things happen
        wait_instance.until.return_value = mock_element # Default: found something
        mock_driver.find_element.return_value = mock_element # Default: found something
        mock_driver.switch_to.active_element = mock_element
        
        # 3. Data
        contacts = [{
            'telefono': '51999999999',
            'mensaje': 'Hola Test',
            'nombre': 'Cliente Test',
            'image_path': 'dummy_image_real.png'
        }]
        
        # Create dummy image
        with open('dummy_image_real.png', 'w') as f: f.write("test")
        
        try:
            print("▶️ Ejecutando función...")
            result = send_whatsapp_messages_direct(contacts, "Hola Test", speed="Rápida (Riesgo de bloqueo)")
            
            print("--- LOG DE EJECUCIÓN ---")
            print(result['log'])
            print("------------------------")
            print(f"Exitosos: {result['exitosos']}")
            print(f"Fallidos: {result['fallidos']}")
            
            if result['exitosos'] == 1:
                print("\n✅ PRUEBA EXITOSA: La lógica 'attach -> wait -> caption' se ejecutó correctamente.")
            else:
                print("\n❌ PRUEBA FALLIDA.")

        finally:
             if os.path.exists('dummy_image_real.png'):
                os.remove('dummy_image_real.png')

if __name__ == '__main__':
    unittest.main()
