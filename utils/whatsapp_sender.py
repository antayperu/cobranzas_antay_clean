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

# --- RC-ARCH-001: CENTRALIZED SELECTORS ---
SELECTORS = {
    'chat_loaded': '//div[@contenteditable="true"][@data-tab="10"] | //span[@data-icon="plus"] | //div[@title="Escribe un mensaje"]',
    'invalid_number': '//div[contains(text(), "inválido") or contains(text(), "invalid") or contains(text(), "url is invalid")]',
    'input_box': '//div[@contenteditable="true"][@data-tab="10"]',
    'preview_loading': '//span[@data-icon="x-alt"] | //div[@aria-label="Escribe un comentario"] | //div[@aria-label="Write a caption"]',
    'send_button': [
        '//span[@data-icon="send"]',
        '//div[@role="button"][@aria-label="Send"]',
        '//div[@role="button"][@aria-label="Enviar"]',
        '//span[@data-testid="send"]'
    ],
    'attach_menu_btn': [
        '//div[@title="Adjuntar"]',
        '//div[@title="Attach"]',
        '//span[@data-icon="plus"]',
        '//span[@data-icon="clip"]'
    ],
    'file_input': '//input[@type="file"]',
    'modal_caption': [
        '//div[@aria-label="Añade un comentario"]',
        '//div[@aria-label="Add a caption"]',
        '//div[@aria-label="Escribe un comentario"]'
    ],
    'modal_view': '//div[@aria-label="Enviar archivo"] | //div[contains(@class, "media-viewer")] | //span[@data-icon="x-viewer"]',
    'doc_sent_check': '//span[@data-icon="document"]'
}


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

def generate_executive_card_html(client_data, branding_config, logo_b64=None):
    """
    Genera HTML de tarjeta ejecutiva compacta para WhatsApp.
    
    Args:
        client_data: Dict con datos del cliente (EMPRESA, totales, conteos)
        branding_config: Dict con configuración de branding
        logo_b64: Logo en base64 (opcional)
    
    Returns:
        str: HTML completo de la tarjeta
    """
    # Extraer datos
    empresa = client_data.get('EMPRESA', 'Cliente')
    
    # Totales y conteos por moneda
    total_s = client_data.get('TOTAL_SALDO_S', 'S/ 0.00')
    total_d = client_data.get('TOTAL_SALDO_D', '$ 0.00')
    count_s = client_data.get('COUNT_DOCS_S', 0)
    count_d = client_data.get('COUNT_DOCS_D', 0)
    
    # Branding
    primary_color = branding_config.get('primary_color', '#2e4af6')
    secondary_color = branding_config.get('secondary_color', '#6fa3b2')
    company_name = branding_config.get('company_name', 'DACTA S.A.C.')
    company_ruc = branding_config.get('company_ruc', '20375779448')
    phone_contact = branding_config.get('phone_contact', '+51 998 080 797')
    
    # Logo (usar base64 si está disponible, sino placeholder)
    logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""
    logo_html = f'<img src="{logo_src}" alt="{company_name}" style="max-width: 280px; height: auto; margin-bottom: 20px;">' if logo_b64 else f'<h1 style="color: {primary_color}; margin: 0;">{company_name}</h1>'
    
    # Construir secciones de totales
    totales_html = ""
    
    if count_s > 0:
        totales_html += f"""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 20px; 
                    border-radius: 12px; 
                    margin: 15px 0;
                    border-left: 5px solid {primary_color};">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="font-size: 48px; margin-right: 15px;">💰</div>
                <div style="flex: 1;">
                    <div style="font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Soles</div>
                    <div style="font-size: 32px; font-weight: bold; color: {primary_color}; line-height: 1;">{total_s}</div>
                    <div style="font-size: 14px; color: #888; margin-top: 5px;">({count_s:02d} documento{'s' if count_s != 1 else ''})</div>
                </div>
            </div>
        </div>
        """
    
    if count_d > 0:
        totales_html += f"""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 20px; 
                    border-radius: 12px; 
                    margin: 15px 0;
                    border-left: 5px solid {secondary_color};">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="font-size: 48px; margin-right: 15px;">💵</div>
                <div style="flex: 1;">
                    <div style="font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Dólares</div>
                    <div style="font-size: 32px; font-weight: bold; color: {secondary_color}; line-height: 1;">{total_d}</div>
                    <div style="font-size: 14px; color: #888; margin-top: 5px;">({count_d:02d} documento{'s' if count_d != 1 else ''})</div>
                </div>
            </div>
        </div>
        """
    
    # Si no hay documentos, mostrar mensaje
    if count_s == 0 and count_d == 0:
        totales_html = f"""
        <div style="background: #f8f9fa; padding: 30px; border-radius: 12px; text-align: center; color: #666;">
            <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
            <div style="font-size: 18px;">Sin documentos pendientes</div>
        </div>
        """
    
    # HTML completo
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, {primary_color}15 0%, {secondary_color}15 100%);
                padding: 40px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .card {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                padding: 40px;
                max-width: 800px;
                width: 100%;
            }}
            .header {{
                text-align: center;
                padding-bottom: 30px;
                border-bottom: 3px solid {primary_color};
                margin-bottom: 30px;
            }}
            .greeting {{
                font-size: 20px;
                color: #333;
                margin-bottom: 10px;
            }}
            .company-name {{
                font-size: 26px;
                font-weight: bold;
                color: {primary_color};
                margin-bottom: 20px;
            }}
            .intro {{
                font-size: 16px;
                color: #555;
                line-height: 1.6;
                margin-bottom: 30px;
                text-align: center;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 25px;
                border-top: 2px solid #e9ecef;
                text-align: center;
            }}
            .footer-company {{
                font-size: 14px;
                color: #666;
                margin-bottom: 8px;
            }}
            .footer-contact {{
                font-size: 16px;
                color: {primary_color};
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                {logo_html}
            </div>
            
            <div class="greeting">Estimados</div>
            <div class="company-name">{empresa}</div>
            
            <div class="intro">
                A la fecha presentan documentos pendientes de pago.<br>
                Agradeceremos gestionar la cancelación a la brevedad.
            </div>
            
            {totales_html}
            
            <div class="footer">
                <div class="footer-company">{company_name} | RUC: {company_ruc}</div>
                <div class="footer-company">Notificación automática de cobranza</div>
                <div class="footer-contact">📞 Consultas: {phone_contact}</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_executive_card_image(client_data, branding_config, logo_path=None):
    """
    Genera imagen JPG de tarjeta ejecutiva usando Selenium headless.
    
    Args:
        client_data: Dict con datos del cliente
        branding_config: Dict con configuración de branding
        logo_path: Ruta al archivo de logo (opcional)
    
    Returns:
        str: Ruta del archivo JPG temporal generado
    """
    import base64
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    # Convertir logo a base64 si existe
    logo_b64 = None
    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                logo_b64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Warning: No se pudo cargar logo: {e}")
    
    # Generar HTML
    html_content = generate_executive_card_html(client_data, branding_config, logo_b64)
    
    # Crear archivo HTML temporal
    temp_html = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
    temp_html.write(html_content)
    temp_html.close()
    
    # Configurar Chrome headless
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=800,1000')
    
    driver = None
    temp_image_path = None
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Cargar HTML
        driver.get(f'file:///{temp_html.name}')
        
        # Esperar carga completa
        time.sleep(1.5)
        
        # Obtener dimensiones reales del contenido
        total_height = driver.execute_script("return document.body.scrollHeight")
        total_width = driver.execute_script("return document.body.scrollWidth")
        
        # Ajustar ventana al contenido
        driver.set_window_size(total_width, total_height)
        time.sleep(0.5)
        
        # Capturar screenshot
        temp_image_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
        driver.save_screenshot(temp_image_path)
        
    finally:
        if driver:
            driver.quit()
        
        # Limpiar HTML temporal
        try:
            os.remove(temp_html.name)
        except:
            pass
    
    return temp_image_path

def generate_pdf_statement(client_data, docs_df, branding_config, logo_path=None):
    """
    Genera PDF con estado de cuenta detallado.
    Reutiliza el diseño HTML del email para consistencia visual.
    VERSIÓN WINDOWS: Usa Selenium + Chrome headless para generar PDF (compatible con Windows)
    
    Args:
        client_data: Dict con datos del cliente (EMPRESA, etc.)
        docs_df: DataFrame con documentos pendientes
        branding_config: Dict con configuración de branding
        logo_path: Ruta al archivo de logo (opcional)
    
    Returns:
        str: Ruta del archivo PDF temporal generado
    """
    # Importar función de generación de HTML del email
    from utils.email_sender import generate_premium_email_body_cid
    import base64
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    # Convertir logo a base64 si existe
    logo_b64 = None
    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                logo_b64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Warning: No se pudo cargar logo para PDF: {e}")
    
    # Calcular totales por moneda
    try:
        mask_soles = docs_df['MONEDA'].astype(str).str.strip().str.upper().str.startswith('S', na=False)
        df_sol = docs_df[mask_soles]
        df_dol = docs_df[~mask_soles]
        
        sum_s = df_sol['SALDO REAL'].sum()
        sum_d = df_dol['SALDO REAL'].sum()
        
        total_s = f"S/ {sum_s:,.2f}" if sum_s > 0 else ""
        total_d = f"$ {sum_d:,.2f}" if sum_d > 0 else ""
    except:
        total_s = "S/ 0.00"
        total_d = ""
    
    # Generar HTML usando la función del email
    html_content = generate_premium_email_body_cid(
        client_name=client_data.get('EMPRESA', 'Cliente'),
        docs_df=docs_df,
        total_s=total_s,
        total_d=total_d,
        branding_config=branding_config
    )
    
    # Reemplazar CID del logo con base64 (para PDF)
    if logo_b64:
        html_content = html_content.replace(
            'src="cid:logo_dacta"',
            f'src="data:image/png;base64,{logo_b64}"'
        )
    
    # Crear archivo HTML temporal
    temp_html = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
    temp_html.write(html_content)
    temp_html.close()
    
    # Configurar Chrome headless para PDF
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Configuración para imprimir a PDF
    options.add_argument('--kiosk-printing')
    
    driver = None
    temp_pdf_path = None
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Cargar HTML
        driver.get(f'file:///{temp_html.name}')
        
        # Esperar carga completa
        time.sleep(2)
        
        # Generar PDF usando Chrome's print to PDF
        temp_pdf_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        
        print_options = {
            'landscape': False,
            'displayHeaderFooter': False,
            'printBackground': True,
            'preferCSSPageSize': True,
        }
        
        result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
        
        # Decodificar y guardar PDF
        import base64 as b64
        with open(temp_pdf_path, 'wb') as f:
            f.write(b64.b64decode(result['data']))
        
    finally:
        if driver:
            driver.quit()
        
        # Limpiar HTML temporal
        try:
            os.remove(temp_html.name)
        except:
            pass
    
    return temp_pdf_path


def _check_pdf_sent(driver, pdf_path):
    """Verifica si el PDF fue enviado buscándolo en el chat"""
    try:
        # Check genérico de documento + check específico por nombre
        base_name = os.path.basename(pdf_path)
        
        # 1. Verificar si existe algún icono de documento reciente
        if driver.find_elements(By.XPATH, SELECTORS['doc_sent_check']):
            # 2. Refinar búsqueda por nombre si es posible (más costoso)
            try:
                if driver.find_elements(By.XPATH, f'//span[contains(text(), "{base_name}")]'):
                    return True
            except:
                pass
            return True # Asumimos éxito si hay icono de documento y no saltó error
            
        return False
    except:
        return False


def _check_modal_gone(driver):
    """Verifica si el modal de envío de archivo se ha cerrado"""
    try:
        # Usamos el selector centralizado
        if driver.find_elements(By.XPATH, SELECTORS['modal_view']):
            return False # Aún está presente
        return True # No se encontró -> Se cerró
    except:
        return True # Si da error al buscar, asumimos que no está



def send_whatsapp_messages_direct(
    contacts, 
    message, 
    speed="Normal (Recomendado)", 
    progress_callback=None,
    send_mode="texto",  # NUEVO: "texto", "imagen_ejecutiva", "imagen_pdf"
    branding_config=None,  # NUEVO: Configuración de branding
    logo_path=None  # NUEVO: Ruta al logo
):
    """
    Envía mensajes de WhatsApp directamente usando Selenium desde Streamlit.

    Args:
        contacts: Lista de diccionarios con datos de clientes
        message: Plantilla de mensaje con variables
        speed: Velocidad de envío (Rápida/Normal/Lenta)
        progress_callback: Función callback(current, total, status, log_text) para reportar progreso
        send_mode: Modo de envío ("texto", "imagen_ejecutiva", "imagen_pdf")
        branding_config: Dict con configuración de branding (requerido para modos de imagen)
        logo_path: Ruta al archivo de logo (opcional)

    Returns:
        dict: {
            'exitosos': int,
            'fallidos': int,
            'total': int,
            'errores': list,
            'log': str
        }
    """
    # [HOTFIX RC-OPS-001] SAFETY GUARD - DESHABILITAR MODOS DE IMAGEN
    if send_mode in ["imagen_ejecutiva", "imagen_pdf"]:
        print(f"⚠️ [HOTFIX] El modo '{send_mode}' está deshabilitado temporalmente. Se forzará 'texto'.")
        # Log visual en consola/streamlit si fuera posible, aqui solo print backend
        if progress_callback: progress_callback(f"⚠️ Alerta: Modo Imagen en mantenimiento. Enviando solo texto.")
        send_mode = "texto"

    # Configurar delays según velocidad
    delays = {
        "Rápida (Riesgo de bloqueo)": 1,
        "Normal (Recomendado)": 4,
        "Lenta (Más seguro)": 10
    }
    delay = delays.get(speed, 4)

    # Procesar contactos
    processed_contacts = []
    temp_files_to_cleanup = []  # Track de archivos temporales para limpieza
    
    for contact in contacts:
        # Aseguramos que 'nombre' exista para el log, aunque sea duplicado de 'nombre_cliente'
        contact_copy = contact.copy()
        contact_copy['telefono'] = normalize_phone(contact.get('telefono', ''))
        # Reemplazamos variables AQUI para que el mensaje final ya esté listo
        contact_copy['mensaje'] = replace_variables(message, contact_copy)
        if 'nombre' not in contact_copy:
            contact_copy['nombre'] = contact_copy.get('nombre_cliente', 'Cliente')
        
        # NUEVO: Generar archivos según modo de envío
        if send_mode in ["imagen_ejecutiva", "imagen_pdf"] and branding_config:
            try:
                # Generar imagen ejecutiva
                img_path = generate_executive_card_image(contact_copy, branding_config, logo_path)
                contact_copy['image_path'] = img_path
                temp_files_to_cleanup.append(img_path)
                
                # Si modo incluye PDF, generarlo también
                if send_mode == "imagen_pdf" and 'docs_df' in contact_copy:
                    pdf_path = generate_pdf_statement(
                        contact_copy, 
                        contact_copy['docs_df'], 
                        branding_config, 
                        logo_path
                    )
                    contact_copy['pdf_path'] = pdf_path
                    temp_files_to_cleanup.append(pdf_path)
            except Exception as e:
                print(f"Warning: Error generando archivos para {contact_copy.get('nombre', 'Cliente')}: {e}")
                # Continuar sin archivos si falla la generación
                contact_copy['image_path'] = None
                contact_copy['pdf_path'] = None
        
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
                    chat_loaded_xpath = SELECTORS['chat_loaded']
                    
                    # Verificar periódicamente para detectar popup de invalido rapido
                    start_time = time.time()
                    loaded = False
                    while time.time() - start_time < timeout_val:
                        try:
                            if driver.find_elements(By.XPATH, chat_loaded_xpath):
                                loaded = True
                                break
                            
                            # Check invalid number popup (Fast Fail)
                            invalid_xpath = SELECTORS['invalid_number']
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
                        inp_xpath = SELECTORS['input_box']
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
                            preview_indicator = SELECTORS['preview_loading']
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
                        
                        send_btn_selectors = SELECTORS['send_button']
                            
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
                            caption_selectors = SELECTORS['modal_caption']
                            
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
                            
                        add_log(f"    ✅ Imagen enviada a {nombre}")
                        
                        # NUEVO v5.0: Adjuntar PDF si está en modo imagen_pdf
                        pdf_path = contact.get('pdf_path')
                        if pdf_path and os.path.exists(pdf_path):
                            try:
                                add_log(f"    📎 Adjuntando PDF...")
                                
                                # Esperar a que WhatsApp vuelva al estado normal después de enviar imagen
                                time.sleep(5)
                                
                                # 1. Buscar el botón de adjuntar (clip) - Múltiples selectores
                                # RETRY LOOP FOR ATTACHMENT
                                attachment_success = False
                                for attempt_idx in range(3):
                                    try:
                                        add_log(f"    📎 Intento adjuntar PDF ({attempt_idx+1}/3)...")
                                        
                                        # 1. Buscar el botón de adjuntar (clip)
                                        attach_btn = None
                                        attach_selectors = SELECTORS['attach_menu_btn']
                                        
                                        for selector in attach_selectors:
                                            try:
                                                attach_btn = driver.find_element(By.XPATH, selector)
                                                if attach_btn: break
                                            except: continue
                                        
                                        if not attach_btn:
                                            time.sleep(1)
                                            continue
                                        
                                        # Click en el botón de adjuntar
                                        driver.execute_script("arguments[0].click();", attach_btn)
                                        time.sleep(1)
                                        
                                        # 2. Buscar el input de archivo (Wait for presence)
                                        file_input = None
                                        
                                        try:
                                            # Usamos wait explícito para el input file
                                            input_wait = WebDriverWait(driver, 5)
                                            file_input = input_wait.until(EC.presence_of_element_located((By.XPATH, SELECTORS['file_input'])))
                                        except:
                                            pass
                                        
                                        if not file_input:
                                            add_log("    ⚠️ Input file no encontrado, reintentando...")
                                            continue
                                        
                                        # 3. Enviar ruta del PDF
                                        abs_pdf_path = os.path.abspath(pdf_path)
                                        file_input.send_keys(abs_pdf_path)
                                        
                                        # 4. Esperar modal de preview (CRITICO)
                                        preview_selectors = [SELECTORS['modal_view']] + SELECTORS['modal_caption']
                                        
                                        preview_found = False
                                        for _ in range(10): # Esperar hasta 5s
                                            time.sleep(0.5)
                                            for selector in preview_selectors:
                                                if driver.find_elements(By.XPATH, selector):
                                                    preview_found = True
                                                    break
                                            if preview_found: break
                                        
                                        if preview_found:
                                            attachment_success = True
                                            add_log("    ✅ Preview detectado")
                                            break
                                        else:
                                            add_log("    ⚠️ Preview no apareció, reintentando clip...")
                                            # Intentar cerrar menú si quedó abierto o resetear
                                            try:
                                                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                                            except: pass
                                            time.sleep(1)
                                            
                                    except Exception as e:
                                        add_log(f"    ⚠️ Error intento {attempt_idx+1}: {str(e)[:50]}")
                                        time.sleep(1)
                                
                                if not attachment_success:
                                    add_log("    ❌ No se pudo abrir el modal de PDF tras 3 intentos")
                                
                                time.sleep(2)
                                
                                time.sleep(2)
                                
                                # 5. ENVIAR PDF - ESTRATEGIA: VERIFICAR CIERRE DE MODAL
                                add_log(f"    📤 Iniciando envío PDF (Estrategia Modal-Close)...")
                                
                                pdf_sent_confirmed = False
                                
                                # Definir selector del modal para verificar si se cierra
                                modal_selector = '//div[@aria-label="Enviar archivo"]' # o similar
                                
                                # INTENTO 1: Escribir caption real + Click en botón (Nativo)
                                try:
                                    # Buscar input de comentario
                                    caption_selectors = SELECTORS['modal_caption']
                                    
                                    caption_box = None
                                    for selector in caption_selectors:
                                        try:
                                            elements = driver.find_elements(By.XPATH, selector)
                                            for elem in elements:
                                                if elem.is_displayed():
                                                    caption_box = elem
                                                    break
                                            if caption_box: break
                                        except: pass
                                    
                                    if caption_box:
                                        # Escribir algo real para despertar la UI
                                        add_log(f"    📝 Escribiendo caption para activar UI...")
                                        driver.execute_script("arguments[0].click();", caption_box)
                                        time.sleep(0.5)
                                        caption_box.send_keys("Adjunto estado de cuenta")
                                        time.sleep(1)
                                        
                                        # ESTRATEGIA FUERZA BRUTA: ENTER DIRECTO
                                        # Ignoramos buscar botón porque da falsos positivos
                                        add_log(f"    ⌨️  ENVIANDO CON ENTER (Fuerza Bruta)...")
                                        caption_box.send_keys(Keys.ENTER)
                                        time.sleep(3)
                                        
                                        # Verificación
                                        if _check_modal_gone(driver):
                                            pdf_sent_confirmed = True
                                            add_log(f"    ✅ Modal cerrado detectado (Enter)")
                                        else:
                                            # Intentar un segundo Enter si no se cerró
                                            add_log(f"    ⚠️ Modal sigue abierto, segundo Enter...")
                                            caption_box.send_keys(Keys.ENTER)
                                            time.sleep(2)
                                            if _check_modal_gone(driver):
                                                pdf_sent_confirmed = True
                                                add_log(f"    ✅ Modal cerrado detectado (2do Enter)")
                                    
                                    # Si no hubo caption box (raro), intentamos botón
                                    else:
                                        add_log(f"    ⚠️ No se encontró caption, buscando botón...")
                                        # Buscar botón enviar
                                        send_btn_selectors = SELECTORS['send_button']
                                        
                                        send_btn = None
                                        for selector in send_btn_selectors:
                                            try:
                                                btns = driver.find_elements(By.XPATH, selector)
                                                for btn in btns:
                                                    if btn.is_displayed():
                                                        send_btn = btn
                                                        break
                                                if send_btn: break
                                            except: pass
                                        
                                        if send_btn:
                                            add_log(f"    🖱️  Click Nativo en botón enviar...")
                                            send_btn.click()
                                            time.sleep(3)
                                            if _check_modal_gone(driver):
                                                pdf_sent_confirmed = True
                                                add_log(f"    ✅ Modal cerrado (Click)")

                                except Exception as e:
                                    add_log(f"    ⚠️ Intento 1 falló: {str(e)[:50]}")

                                # INTENTO 2: JS Click si el modal sigue abierto (Solo si falló Enter)
                                if not pdf_sent_confirmed:
                                    add_log(f"    🎯 Intento 2: JS Click Force...")
                                    try:
                                        if send_btn:
                                            driver.execute_script("arguments[0].click();", send_btn)
                                            time.sleep(3)
                                            if _check_modal_gone(driver):
                                                pdf_sent_confirmed = True
                                                add_log(f"    ✅ Modal cerrado detectado (JS Click)")
                                            elif _check_pdf_sent(driver, pdf_path): # Fallback a buscar en chat
                                                pdf_sent_confirmed = True
                                                add_log(f"    ✅ Mensaje encontrado en chat (JS Click)")
                                    except Exception as e:
                                        add_log(f"    ⚠️ Intento 2 falló: {str(e)[:50]}")

                                # Resultado final
                                if pdf_sent_confirmed:
                                    add_log(f"    ✅ PDF adjuntado exitosamente")
                                else:
                                    add_log(f"    ❌ PDF NO se pudo enviar (Modal sigue abierto)")
                                
                                time.sleep(2)
                                
                            except Exception as e_pdf:
                                error_msg = str(e_pdf).split('\n')[0][:150]
                                add_log(f"    ⚠️ Error adjuntando PDF: {error_msg}")
                        
                        exitosos += 1

                    except Exception as e_img:
                        err_msg = str(e_img).split('\n')[0]
                        add_log(f"    ❌ Falló envío de imagen: {err_msg}")
                        errores.append(f"{nombre}: Falló envío de imagen ({err_msg})")
                        fallidos += 1

                
                # ENVÍO SOLO TEXTO (Fallback o Standard)
                else:
                    try:
                        inp_xpath = SELECTORS['input_box']
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
        
        # NUEVO: Limpieza de archivos temporales (JPG + PDF)
        if temp_files_to_cleanup:
            add_log(f"Limpiando {len(temp_files_to_cleanup)} archivos temporales...")
            for file_path in temp_files_to_cleanup:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    add_log(f"    Warning: No se pudo eliminar {file_path}: {e}")

    return {
        'exitosos': exitosos, 
        'fallidos': fallidos, 
        'log': "\n".join(log_lines)
    }
