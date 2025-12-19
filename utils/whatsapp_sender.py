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

    def copy_image_to_clipboard(image_path):
        """Copia una imagen al portapapeles usando PowerShell (Nativo Windows)"""
        try:
            import subprocess
            abs_path = os.path.abspath(image_path)
            # Escapar comillas simples dentro de la ruta para PowerShell
            escaped_path = abs_path.replace("'", "''")
            cmd = f'powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile(\'{escaped_path}\'))"'
            subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            return True
        except Exception as e:
            add_log(f"    Error clipboard: {e}")
            return False

    driver = None

    try:
        # Inicializar
        add_log("="*60)
        add_log("INICIANDO ENVÍO DE MENSAJES WHATSAPP (Híbrido: Paste / Adjuntar)") # Updated log message
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
        add_log("⏳ Esperando 45 segundos para inicio de sesión...") # Updated log message
        
        if progress_callback:
           progress_callback(0, len(processed_contacts), "Escanea el QR en WhatsApp Web...", "\n".join(log_lines))

        # Espera inicial para login (QR)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]')))
            add_log("✅ Sesión iniciada detectada.")
        except:
             add_log("⏳ Tiempo de espera de login finalizado. Asumiendo sesión iniciada o continuando...")
             time.sleep(10) 
        
        time.sleep(5) 

        add_log("="*60)
        add_log("COMENZANDO ENVÍO")
        add_log("="*60)

        for i, contact in enumerate(processed_contacts, 1):
            phone = contact['telefono']
            final_msg = contact['mensaje']
            nombre = contact['nombre']
            img_path = contact.get('image_path', None) # Path Local de Imagen
            
            if not phone:
                add_log(f"[{i}/{len(processed_contacts)}] ⚠️ Salteando {nombre}: Sin teléfono")
                fallidos += 1
                continue

            try:
                add_log(f"[{i}/{len(processed_contacts)}] Enviando a: {nombre} ({phone})")
                
                if progress_callback:
                    progress_callback(i-1, len(processed_contacts), f"Enviando a {nombre}...", "\n".join(log_lines))

                url = f"https://web.whatsapp.com/send?phone={phone}"
                driver.get(url)
                
                # Esperamos carga del chat
                try:
                    chat_loaded_xpath = '//div[@contenteditable="true"][@data-tab="10"] | //span[@data-icon="plus"]'
                    wait.until(EC.presence_of_element_located((By.XPATH, chat_loaded_xpath)))
                    time.sleep(2) # Stability
                except:
                     # Check invalid number popup
                     invalid_xpath = '//div[contains(text(), "inválido") or contains(text(), "invalid")]'
                     if driver.find_elements(By.XPATH, invalid_xpath):
                             add_log("    ❌ Número inválido")
                             errores.append(f"{nombre}: Número inválido")
                             fallidos += 1
                             continue
                     else:
                             raise Exception("Timeout cargando chat")

                # ESTRATEGIA: IMAGEN
                if img_path and os.path.exists(img_path):
                    sent_image = False
                    
                    # 1. INTENTO: COPY & PASTE (Prioridad Usuario)
                    try:
                        add_log("    📋 Intentando Pegar (Ctrl+V)...")
                        if copy_image_to_clipboard(img_path):
                            time.sleep(0.5)
                            # Click en background o input para foco
                            try:
                                driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]').click()
                            except: pass
                            
                            # ActionChains Paste Global
                            actions = ActionChains(driver)
                            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                            
                            add_log("    ⏳ Esperando vista previa...")
                            send_btn_xpath = '//span[@data-icon="send"]'
                            wait.until(EC.presence_of_element_located((By.XPATH, send_btn_xpath)))
                            sent_image = True
                            add_log("    ✅ Imagen pegada correctamente.")
                    except Exception as e_paste:
                        add_log(f"    ⚠️ Falló pegar ({e_paste}). Intentando método tradicional...")

                    # 2. INTENTO: ADJUNTAR (Fallback)
                    if not sent_image:
                         add_log("    📎 Usando método Adjuntar Archivo...")
                         try:
                             # Buscar '+'
                             plus_xpaths = ['//div[@title="Adjuntar"]', '//span[@data-icon="plus"]', '//div[@aria-label="Adjuntar"]']
                             for xp in plus_xpaths:
                                 try:
                                     driver.find_element(By.XPATH, xp).click()
                                     time.sleep(0.5)
                                     break
                                 except: continue
                             
                             # Input File
                             # Buscar input type file (suele estar presente pero oculto si no se da click al mas, a veces funciona igual)
                             file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                             file_input.send_keys(os.path.abspath(img_path))
                             
                             # Wait Preview
                             wait.until(EC.presence_of_element_located((By.XPATH, '//span[@data-icon="send"]')))
                             sent_image = True
                         except Exception as e_attach:
                             add_log(f"    ❌ Falló adjuntar: {e_attach}")
                             raise e_attach

                    # 3. CAPTION & SEND
                    try:
                        add_log("    📝 Escribiendo caption...")
                        import pyperclip
                        pyperclip.copy(final_msg)
                        
                        # Pegar caption
                        actions = ActionChains(driver)
                        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                        time.sleep(1)
                        actions.send_keys(Keys.ENTER).perform() # Enviar con Enter
                        
                        # Doble check por si el enter no funcionó (a veces pasa en modo caption)
                        time.sleep(2)
                        send_btns = driver.find_elements(By.XPATH, '//span[@data-icon="send"]')
                        if send_btns:
                             send_btns[0].click()

                        add_log("    ✅ Enviado.")
                        exitosos += 1
                        time.sleep(3)
                        
                    except Exception as e_cap:
                         try:
                             driver.find_element(By.XPATH, '//span[@data-icon="send"]').click()
                             exitosos += 1
                             add_log("    ✅ Enviado (Click Fallback).")
                         except:
                             add_log(f"    ⚠️ Error final caption: {e_cap}")
                
                # ENVÍO SOLO TEXTO (Fallback o Standard)
                else:
                    try:
                        inp_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
                        input_box = wait.until(EC.presence_of_element_located((By.XPATH, inp_xpath)))
                        
                        # Paste Text
                        import pyperclip
                        pyperclip.copy(final_msg)
                        input_box.click()
                        input_box.send_keys(Keys.CONTROL, "v")
                        time.sleep(1)
                        input_box.send_keys(Keys.ENTER)
                        
                        add_log("    ✅ Enviado (Texto)")
                        exitosos += 1
                        time.sleep(2)

                    except Exception as e_txt:
                        add_log(f"    ❌ Error envío texto: {str(e_txt)}")
                        fallidos += 1
                        errores.append(f"{nombre}: {str(e_txt)}")

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
