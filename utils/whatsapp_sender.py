import base64
import time
import os
import tempfile
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def format_soles(amount):
    """Formatea un monto en soles peruanos."""
    try:
        return f"S/ {float(amount):,.2f}"
    except:
        return "S/ 0.00"

def normalize_phone(phone):
    """
    Normaliza número de teléfono para WhatsApp Web.

    Ejemplos:
        +51942841923 → 51942841923
        942841923 → 51942841923
        51942841923 → 51942841923
    """
    if not phone:
        return ""

    phone = str(phone).strip()

    # Quitar + si existe
    if phone.startswith('+'):
        phone = phone[1:]

    # Agregar 51 si solo tiene 9 dígitos
    if len(phone) == 9 and phone.isdigit():
        phone = '51' + phone

    return phone

def replace_variables(message, client_data):
    """
    Reemplaza todas las variables en el mensaje con datos del cliente.
    Soporta variables estándar y cualquier llave extra en client_data.
    """
    # Variables estándar calculadas (si faltan)
    ticket_promedio = client_data.get('ticket_promedio', 0)
    if not ticket_promedio and 'venta_neta' in client_data and 'numero_transacciones' in client_data:
        num_compras = max(client_data.get('numero_transacciones', 1), 1)
        ticket_promedio = client_data.get('venta_neta', 0) / num_compras

    # Diccionario base de reemplazos
    replacements = {
        '{nombre}': client_data.get('nombre_cliente', ''),
        '{producto}': client_data.get('producto', 'nuestros productos'),
        '{marca}': client_data.get('marca', 'nuestros productos'),
        '{linea}': client_data.get('linea', 'nuestros productos'),
        '{familia}': client_data.get('familia', 'nuestros productos'),
        '{grupo}': client_data.get('grupo', 'nuestros productos'),
        '{ticket_promedio}': format_soles(ticket_promedio),
        '{venta_total}': format_soles(client_data.get('venta_neta', 0)),
        '{num_compras}': str(int(client_data.get('numero_transacciones', 0)))
    }

    # Agregar cualquier otra variable presente en client_data
    # Esto permite que variables como {RESUMEN_DOCS} o {TOTAL_SALDO_REAL} funcionen automáticamente
    for key, value in client_data.items():
        placeholder = f"{{{key}}}"
        if placeholder not in replacements:
            replacements[placeholder] = str(value)

    # Realizar reemplazos
    for var, value in replacements.items():
        if var in message:
             message = message.replace(var, str(value))

    return message

def send_whatsapp_messages_direct(contacts, message, speed="Normal (Recomendado)", progress_callback=None):
    """
    Envía mensajes de WhatsApp directamente usando Selenium desde Streamlit.

    Args:
        contacts: Lista de diccionarios con datos de clientes
        message: Plantilla de mensaje con variables
        speed: Velocidad de envío (Rápida/Normal/Lenta)
        progress_callback: Función callback(current, total, status, log_text) para reportar progreso

    Returns:
        dict: {
            'exitosos': int,
            'fallidos': int,
            'total': int,
            'errores': list,
            'log': str
        }
    """
    # Configurar delays según velocidad
    delays = {
        "Rápida (Riesgo de bloqueo)": 1,
        "Normal (Recomendado)": 4,
        "Lenta (Más seguro)": 10
    }
    delay = delays.get(speed, 4)

    # Procesar contactos
    processed_contacts = []
    for contact in contacts:
        # Aseguramos que 'nombre' exista para el log, aunque sea duplicado de 'nombre_cliente'
        contact_copy = contact.copy()
        contact_copy['telefono'] = normalize_phone(contact.get('telefono', ''))
        # Reemplazamos variables AQUI para que el mensaje final ya esté listo
        contact_copy['mensaje'] = replace_variables(message, contact_copy)
        if 'nombre' not in contact_copy:
            contact_copy['nombre'] = contact_copy.get('nombre_cliente', 'Cliente')
        
        processed_contacts.append(contact_copy)

    # Variables para tracking
    exitosos = 0
    fallidos = 0
    errores = []
    log_lines = []

    def add_log(text):
        """Agrega línea al log y reporta progreso"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_lines.append(f"[{timestamp}] {text}")
        return "\n".join(log_lines)

    driver = None

    try:
        # Inicializar
        add_log("="*60)
        add_log("INICIANDO ENVÍO DE MENSAJES WHATSAPP (Selenium)")
        add_log("="*60)
        add_log(f"Total de mensajes a enviar: {len(processed_contacts)}")
        add_log(f"Velocidad: {speed} (Delay: {delay}s)")
        
        if progress_callback:
            progress_callback(0, len(processed_contacts), "Iniciando navegador...", "\n".join(log_lines))

        # Configurar opciones de Chrome
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        options = webdriver.ChromeOptions()
        
        # Directorio de usuario para persistencia
        user_data_dir = os.path.join(tempfile.gettempdir(), "whatsapp_session_antay_cobranzas")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        # Anti-detección básica
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")

        add_log("Abriendo Chrome...")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 30)

        # Abrir WhatsApp Web
        add_log("Navegando a WhatsApp Web...")
        driver.get("https://web.whatsapp.com")

        add_log("")
        add_log("⚠️  ESCANEA EL CÓDIGO QR AHORA")
        add_log("⏳ Esperando 45 segundos para inicio de sesión...")
        
        if progress_callback:
           progress_callback(0, len(processed_contacts), "Escanea el QR en WhatsApp Web...", "\n".join(log_lines))

        # Espera inicial para login (QR)
        # Podríamos mejorar esto esperando un elemento clave de la UI de WhatsApp cargado (ej. panel lateral)
        try:
            # Esperar a que aparezca el panel de chats (indicador de login exitoso)
            # O esperar el tiempo fijo si falla la detección rápida
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]')))
            add_log("✅ Sesión iniciada detectada.")
        except:
             add_log("⏳ Tiempo de espera de login finalizado. Asumiendo sesión iniciada o continuando...")
             time.sleep(10) # Wait extra if element not found quickly
        
        time.sleep(5) 

        add_log("="*60)
        add_log("COMENZANDO ENVÍO")
        add_log("="*60)

        for i, contact in enumerate(processed_contacts, 1):
            phone = contact['telefono']
            final_msg = contact['mensaje']
            nombre = contact['nombre']
            
            if not phone:
                add_log(f"[{i}/{len(processed_contacts)}] ⚠️ Salteando {nombre}: Sin teléfono")
                fallidos += 1
                continue

            try:
                add_log(f"[{i}/{len(processed_contacts)}] Enviando a: {nombre} ({phone})")
                
                if progress_callback:
                    progress_callback(i-1, len(processed_contacts), f"Enviando a {nombre}...", "\n".join(log_lines))

                encoded_msg = urllib.parse.quote(final_msg)
                url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"
                
                driver.get(url)
                
                # Esperamos carga del chat
                time.sleep(5)
                
                # Intentar enviar
                try:
                    # Buscamos el botón de enviar
                    # Selectores comunes de WhatsApp Web (pueden cambiar)
                    # El script original usaba //span[@data-icon="send"] o Enter en input
                    # Vamos a intentar el enfoque de ENTER en el input que es más robusto a veces
                    
                    # 1. Esperar al input box
                    inp_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
                    input_box = wait.until(EC.presence_of_element_located((By.XPATH, inp_xpath)))
                    
                    # 2. Focus y Enter
                    input_box.click()
                    time.sleep(1)
                    input_box.send_keys(Keys.ENTER)
                    
                    add_log("    ✅ Enviado (Enter)")
                    exitosos += 1
                    time.sleep(2) # Esperar confirmación visual (check) implícita

                except TimeoutException:
                    # Si no encuentra el input, puede que el número sea inválido
                    # O que haya un popup de "Número no válido"
                    try:
                        # Buscar popup de invalido
                        invalid_xpath = '//div[contains(text(), "inválido") or contains(text(), "invalid")]'
                        if driver.find_elements(By.XPATH, invalid_xpath):
                             add_log("    ❌ Número inválido")
                             errores.append(f"{nombre}: Número inválido")
                        else:
                             add_log("    ❌ Timeout esperando chat")
                             errores.append(f"{nombre}: Timeout chat")
                    except:
                        add_log("    ❌ Timeout genérico")
                        errores.append(f"{nombre}: Timeout")
                    
                    fallidos += 1

                except Exception as e:
                     add_log(f"    ❌ Error al hacer click/enter: {str(e)}")
                     fallidos += 1
                     errores.append(f"{nombre}: {str(e)}")

                # Delay entre mensajes
                if i < len(processed_contacts):
                    add_log(f"    ⏳ Esperando {delay}s...")
                    time.sleep(delay)

            except Exception as e:
                add_log(f"    ❌ Error iteración: {str(e)}")
                fallidos += 1
        
        # Final
        if progress_callback:
            progress_callback(len(processed_contacts), len(processed_contacts), "Finalizado", "\n".join(log_lines))

    except Exception as e:
        add_log(f"ERROR FATAL DRIVER: {str(e)}")
        if progress_callback:
             progress_callback(0, 0, "Error Fatal", "\n".join(log_lines))
    finally:
        if driver:
            add_log("Cerrando navegador...")
            try:
                driver.quit()
            except:
                pass

    return {
        'exitosos': exitosos, 
        'fallidos': fallidos, 
        'log': "\n".join(log_lines)
    }
