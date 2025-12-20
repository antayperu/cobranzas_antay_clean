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
            
            # 0. Limpieza Preventiva del Portapapeles (Enterprise Standard)
            # Evita que residuos de iteraciones anteriores contaminen la actual
            try:
                import subprocess
                subprocess.run('powershell -command "Set-Clipboard -Value $null"', shell=True, check=False)
                time.sleep(0.5) # Short sync wait
            except:
                pass
            
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
                # Esperamos carga del chat
                try:
                    # Tiempos dinámicos: El primero siempre tarda más (Cold Start)
                    timeout_val = 60 if i == 1 else 30 
                    
                    # Selectores de éxito (Chat cargado)
                    chat_loaded_xpath = '//div[@contenteditable="true"][@data-tab="10"] | //span[@data-icon="plus"] | //div[@title="Escribe un mensaje"]'
                    
                    # Verificar periódicamente para detectar popup de invalido rapido
                    start_time = time.time()
                    loaded = False
                    while time.time() - start_time < timeout_val:
                        try:
                            if driver.find_elements(By.XPATH, chat_loaded_xpath):
                                loaded = True
                                break
                            
                            # Check invalid number popup (Fast Fail)
                            invalid_xpath = '//div[contains(text(), "inválido") or contains(text(), "invalid") or contains(text(), "url is invalid")]'
                            if driver.find_elements(By.XPATH, invalid_xpath):
                                raise ValueError("NumeroInvalido")
                                
                        except ValueError as ve:
                            raise ve
                        except:
                            pass
                        time.sleep(1)
                    
                    if not loaded:
                        raise Exception("Timeout cargando chat (DOM no listo)")

                    time.sleep(2) # Stability buffer
                except ValueError:
                     add_log("    ❌ Número inválido detectado por WhatsApp")
                     errores.append(f"{nombre}: Número inválido")
                     fallidos += 1
                     continue
                except Exception as e_load:
                     raise Exception(f"Timeout cargando chat: {str(e_load)}")


                # ESTRATEGIA: JS-FORCE-CLICK + PASTE TRADICIONAL (Grado Militar)
                # Esta combinación "perfora" cualquier botón encima y activa los listeners de WhatsApp.
                if img_path and os.path.exists(img_path):
                    try:
                        image_sent_success = False
                        
                        # 1. Copiar imagen al portapapeles
                        add_log(f"    📋 Preparando imagen en memoria...")
                        if not copy_image_to_clipboard(img_path):
                            raise Exception("Error al copiar imagen (OS Clipboard Error)")
                        
                        # Espera extendida para sincronización de sistema operativo móvil/escritorio
                        time.sleep(3) 
                        
                        # 2. Localizar input principal
                        inp_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
                        input_box = wait.until(EC.presence_of_element_located((By.XPATH, inp_xpath)))
                        
                        # 3. CLICK FANTASMA (JS) + PEGAR
                        # El JS Click traspasa el botón "Clip" o cualquier interceptor visual.
                        add_log("    📋 Pegando imagen (JS Force & Paste)...")
                        driver.execute_script("arguments[0].focus(); arguments[0].click();", input_box)
                        time.sleep(1)
                        
                        # Usamos send_keys directo sobre el elemento para disparar el evento de pegado
                        input_box.send_keys(Keys.CONTROL, 'v')
                        
                        # 4. Verificar si apareció el modal con paciencia
                        try:
                            preview_indicator = '//span[@data-icon="x-alt"] | //div[@aria-label="Escribe un comentario"] | //div[@aria-label="Write a caption"]'
                            # Esperar hasta 15s porque la imagen puede ser pesada en red
                            wait_long = WebDriverWait(driver, 15) 
                            wait_long.until(EC.visibility_of_element_located((By.XPATH, preview_indicator)))
                            image_sent_success = True
                        except:
                            # REINTENTO DE EMERGENCIA: Si no hay modal, intentar pegar una vez más
                            add_log("      ⚠️ Modal lento, reintentando pegado manual...")
                            input_box.send_keys(Keys.CONTROL, 'v')
                            time.sleep(5)
                            if not driver.find_elements(By.XPATH, preview_indicator):
                                raise Exception("WhatsApp no detectó la imagen tras el pegado (Modal ausente)")

                        # 5. Una vez en el modal, buscar botón enviar
                        time.sleep(1.5) # Estabilizar modal
                        
                        send_btn_selectors = [
                            '//span[@data-icon="send"]',
                            '//div[@role="button"][@aria-label="Send"]',
                            '//div[@role="button"][@aria-label="Enviar"]',
                            '//span[@data-testid="send"]'
                        ]
                            
                        # 6. Buscar el botón de envío (Con paciencia)
                        send_button = None
                        for _ in range(15): 
                            for selector in send_btn_selectors:
                                try:
                                    btns = driver.find_elements(By.XPATH, selector)
                                    for btn in btns:
                                        if btn.is_displayed():
                                            send_button = btn
                                            break
                                    if send_button: break
                                except: pass
                            if send_button: break
                            time.sleep(0.5)
                        
                        if not send_button:
                                raise Exception("No se visualizó el botón Enviar en el modal")

                        # 7. Escribir el Caption (Mensaje)
                        try:
                            caption_selectors = [
                                '//div[@aria-label="Escribe un comentario"]',
                                '//div[@aria-label="Add a caption"]'
                            ]
                            
                            caption_box = None
                            for selector in caption_selectors:
                                try:
                                    candidates = driver.find_elements(By.XPATH, selector)
                                    for cand in candidates:
                                        if cand.is_displayed():
                                            caption_box = cand
                                            break
                                    if caption_box: break
                                except: pass
                            
                            if caption_box:
                                add_log("    📝 Agregando mensaje...")
                                import pyperclip
                                pyperclip.copy(final_msg)
                                
                                # Forzar foco en caption y pegar
                                driver.execute_script("arguments[0].focus(); arguments[0].click();", caption_box)
                                time.sleep(0.5)
                                caption_box.send_keys(Keys.CONTROL, 'v')
                                time.sleep(0.5)
                        except Exception as e_cap:
                            add_log(f"    ⚠️ Error en caption (opcional): {str(e_cap)}")

                        # 8. Envío Final (JS Click para no fallar por superposición)
                        driver.execute_script("arguments[0].click();", send_button)
                            
                        add_log(f"    ✅ Enviado a {nombre}")
                        exitosos += 1
                        time.sleep(3) 

                    except Exception as e_img:
                        err_msg = str(e_img).split('\n')[0]
                        add_log(f"    ❌ Falló envío de imagen: {err_msg}")
                        errores.append(f"{nombre}: Falló envío de imagen ({err_msg})")
                        fallidos += 1

                
                # ENVÍO SOLO TEXTO (Fallback o Standard)
                else:
                    try:
                        inp_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
                        input_box = wait.until(EC.presence_of_element_located((By.XPATH, inp_xpath)))
                        
                        # Paste Text (Robust Focus)
                        import pyperclip
                        pyperclip.copy(final_msg)
                        
                        # FIX: ElementClickInterceptedException (Text Mode)
                        driver.execute_script("arguments[0].focus();", input_box)
                        try:
                            input_box.click()
                        except:
                            driver.execute_script("arguments[0].click();", input_box)
                            
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
