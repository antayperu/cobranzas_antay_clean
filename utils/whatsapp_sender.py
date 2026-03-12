import base64
import time
import os
import json
import shutil
import tempfile
import urllib.parse
import asyncio
from datetime import datetime

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    _PLAYWRIGHT_OK = True
except ImportError:
    _PLAYWRIGHT_OK = False

# Compatibilidad retroactiva con módulos UI que aún importan _SELENIUM_OK.
# Mantener este alias evita errores de importación durante la transición.
_SELENIUM_OK = _PLAYWRIGHT_OK

# ---------------------------------------------------------------------------
# Helpers de sesion WhatsApp
# ---------------------------------------------------------------------------

# Usar directorio temp LOCAL del sistema
WA_SESSION_DIR = os.path.join(tempfile.gettempdir(), "dacta_wa_session")
WA_SESSION_INFO = os.path.join(WA_SESSION_DIR, "_session_info.json")


def _ensure_playwright_browser() -> bool:
    """
    Garantiza que Chromium esté descargado. Se ejecuta una sola vez.
    Retorna True si está disponible, False si no.
    """
    if not _PLAYWRIGHT_OK:
        return False
    
    try:
        # Verificar si Chromium ya está descargado
        import subprocess
        result = subprocess.run(
            ["playwright", "install", "chromium"],
            capture_output=True,
            timeout=300,  # 5 minutos max
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def get_wa_session_info() -> dict:
    """
    Retorna info de la sesion WhatsApp almacenada localmente.
    Campos: status ('active'|'none'), verified_at, profile_name, phone
    """
    if not os.path.exists(WA_SESSION_INFO):
        return {"status": "none"}
    try:
        with open(WA_SESSION_INFO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"status": "none"}


def _save_wa_session_info(profile_name: str = "", phone: str = "") -> None:
    os.makedirs(WA_SESSION_DIR, exist_ok=True)
    data = {
        "status": "active",
        "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile_name": profile_name,
        "phone": phone,
    }
    with open(WA_SESSION_INFO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def clear_wa_session() -> bool:
    """Elimina la sesion de Chrome/WhatsApp Web almacenada localmente."""
    try:
        if os.path.exists(WA_SESSION_DIR):
            shutil.rmtree(WA_SESSION_DIR, ignore_errors=True)
        return True
    except Exception:
        return False


def update_wa_session_alias(alias: str = "", phone: str = "") -> bool:
    """
    Actualiza el alias y telefono de la sesion activa sin modificar el timestamp
    de verificacion original.

    Returns:
        True si se guardó correctamente, False si no hay sesion activa.
    """
    info = get_wa_session_info()
    if info.get("status") != "active":
        return False
    info["profile_name"] = alias.strip()
    info["phone"] = phone.strip()
    try:
        os.makedirs(WA_SESSION_DIR, exist_ok=True)
        with open(WA_SESSION_INFO, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False)
        return True
    except Exception:
        return False


def connect_wa_session(timeout_seconds: int = 120) -> tuple:
    """
    Abre Chromium (Playwright), navega a WhatsApp Web y espera que el usuario
    escanee el QR. Guarda la sesion en WA_SESSION_DIR para uso posterior.
    Chromium se descarga automáticamente con `playwright install chromium`.

    Returns:
        (ok: bool, phone: str, profile_name: str, error_msg: str)
    """
    if not _PLAYWRIGHT_OK:
        return False, "", "", (
            "❌ Playwright no está instalado.\n\n"
            "Ejecuta en el servidor:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        )

    # Descarga Chromium automáticamente si no está instalado (primera vez ~170MB)
    _ensure_playwright_browser()

    return asyncio.run(_connect_wa_session_async(timeout_seconds))


async def _connect_wa_session_async(timeout_seconds: int) -> tuple:
    """Implementación async interna de connect_wa_session."""
    os.makedirs(WA_SESSION_DIR, exist_ok=True)

    # Limpiar archivos que causan el dialogo "Chrome no se cerro correctamente"
    _profile_dir = os.path.join(WA_SESSION_DIR, "Default")
    _files_to_clean = [
        os.path.join(WA_SESSION_DIR, "SingletonLock"),
        os.path.join(WA_SESSION_DIR, "SingletonCookie"),
        os.path.join(WA_SESSION_DIR, "SingletonSocket"),
        os.path.join(_profile_dir, "Last Session"),
        os.path.join(_profile_dir, "Last Tabs"),
        os.path.join(_profile_dir, "Current Session"),
        os.path.join(_profile_dir, "Current Tabs"),
    ]
    for _f in _files_to_clean:
        try:
            if os.path.exists(_f):
                os.remove(_f)
        except OSError:
            pass

    try:
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=WA_SESSION_DIR,
                headless=False,
                args=[
                    "--profile-directory=Default",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-blink-features=AutomationControlled",
                ],
                ignore_default_args=["--enable-automation"],
            )
            page = context.pages[0] if context.pages else await context.new_page()

            await page.goto("https://web.whatsapp.com")
            await page.wait_for_timeout(4000)

            PANE_XPATH = '//div[@id="pane-side"]'
            QR_XPATHS = [
                '//canvas[@aria-label="Scan me!"]',
                '//div[@data-testid="qrcode"]',
            ]

            # Detectar si ya hay sesión o si se necesita QR
            page_state = "loading"
            try:
                await page.wait_for_selector(PANE_XPATH, timeout=20000)
                page_state = "logged_in"
            except PlaywrightTimeoutError:
                for qr_xpath in QR_XPATHS:
                    try:
                        if await page.query_selector(qr_xpath):
                            page_state = "qr_visible"
                            break
                    except Exception:
                        pass

            if page_state != "logged_in":
                # Esperar que el usuario escanee el QR
                try:
                    await page.wait_for_selector(
                        PANE_XPATH, timeout=timeout_seconds * 1000
                    )
                    page_state = "logged_in"
                except PlaywrightTimeoutError:
                    await context.close()
                    return False, "", "", f"Timeout: No se completó el login en {timeout_seconds}s."

            # Dar tiempo a que WhatsApp cargue el perfil en el DOM
            await page.wait_for_timeout(2000)

            phone = ""
            profile_name = ""
            try:
                phone = await page.evaluate(
                    "window.Store?.User?.getMaybeMeUser?.()?.id?.user || ''"
                ) or ""
                profile_name = await page.evaluate(
                    "document.querySelector('span[data-testid=\"default-user\"]')?.textContent "
                    "|| document.title || ''"
                ) or ""
                phone = str(phone).strip()
                profile_name = str(profile_name).strip()
            except Exception:
                pass

            _save_wa_session_info(profile_name=profile_name, phone=phone)
            await context.close()
            return True, phone, profile_name, ""

    except Exception as e:
        return False, "", "", f"Error al conectar WhatsApp: {str(e)}"


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
    Genera imagen JPG de tarjeta ejecutiva usando Playwright Chromium headless.
    
    Args:
        client_data: Dict con datos del cliente
        branding_config: Dict con configuración de branding
        logo_path: Ruta al archivo de logo (opcional)
    
    Returns:
        str: Ruta del archivo JPG temporal generado
    """
    import base64
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
    
    # Generar imagen usando Playwright headless (Chromium auto-descargado)
    from playwright.sync_api import sync_playwright as _sync_playwright
    temp_image_path = None
    try:
        with _sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 800, "height": 1000})
            page.set_content(html_content)
            page.wait_for_load_state("networkidle")
            temp_image_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
            page.screenshot(path=temp_image_path, full_page=True)
            browser.close()
    finally:
        # Limpiar HTML temporal
        try:
            os.remove(temp_html.name)
        except Exception:
            pass

    return temp_image_path

def generate_pdf_statement(client_data, docs_df, branding_config, logo_path=None):
    """
    Genera PDF con estado de cuenta detallado.
    Reutiliza el diseño HTML del email para consistencia visual.
    Usa Playwright Chromium headless para generar PDF (sin necesidad de Chrome instalado).
    
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
    
    # Generar PDF usando Playwright headless (Chromium auto-descargado)
    from playwright.sync_api import sync_playwright as _sync_playwright
    temp_pdf_path = None
    try:
        with _sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_content)
            page.wait_for_load_state("networkidle")
            temp_pdf_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
            page.pdf(
                path=temp_pdf_path,
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
            )
            browser.close()
    finally:
        # Limpiar HTML temporal
        try:
            os.remove(temp_html.name)
        except Exception:
            pass

    return temp_pdf_path


def _check_pdf_sent(page, pdf_path):
    """Verifica si el PDF fue enviado buscándolo en el chat (Playwright)"""
    try:
        base_name = os.path.basename(pdf_path)
        if page.query_selector(SELECTORS['doc_sent_check']):
            try:
                if page.query_selector(f'//span[contains(text(), "{base_name}")]'):
                    return True
            except Exception:
                pass
            return True
        return False
    except Exception:
        return False


def _check_modal_gone(page):
    """Verifica si el modal de envío de archivo se ha cerrado (Playwright)"""
    try:
        if page.query_selector(SELECTORS['modal_view']):
            return False
        return True
    except Exception:
        return True



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
    Envía mensajes de WhatsApp directamente usando Playwright desde Streamlit.

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

    from playwright.sync_api import sync_playwright as _sync_playwright, TimeoutError as _PWTimeoutError

    # Descarga Chromium automáticamente si no está instalado (primera vez ~170MB)
    _ensure_playwright_browser()

    wa_context = None
    page = None

    try:
        # Inicializar
        add_log("="*60)
        add_log("INICIANDO ENVÍO DE MENSAJES WHATSAPP (Playwright)")
        add_log("="*60)
        add_log(f"Total de mensajes a enviar: {len(processed_contacts)}")
        add_log(f"Velocidad: {speed} (Delay: {delay}s)")

        if progress_callback:
            progress_callback(0, len(processed_contacts), "Iniciando navegador...", "\n".join(log_lines))

        # Directorio de usuario para persistencia de sesion WhatsApp
        user_data_dir = WA_SESSION_DIR
        os.makedirs(user_data_dir, exist_ok=True)

        # Limpiar archivos que causan el dialogo "Chrome no se cerro correctamente"
        _profile_dir = os.path.join(user_data_dir, "Default")
        _files_to_clean = [
            os.path.join(user_data_dir, "SingletonLock"),
            os.path.join(user_data_dir, "SingletonCookie"),
            os.path.join(user_data_dir, "SingletonSocket"),
            os.path.join(_profile_dir, "Last Session"),
            os.path.join(_profile_dir, "Last Tabs"),
            os.path.join(_profile_dir, "Current Session"),
            os.path.join(_profile_dir, "Current Tabs"),
        ]
        for _f in _files_to_clean:
            try:
                if os.path.exists(_f):
                    os.remove(_f)
            except OSError:
                pass

        add_log("Abriendo Chromium (Playwright)...")
        _playwright = _sync_playwright().start()
        wa_context = _playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=[
                "--profile-directory=Default",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-blink-features=AutomationControlled",
            ],
            ignore_default_args=["--enable-automation"],
        )
        page = wa_context.pages[0] if wa_context.pages else wa_context.new_page()

        # Abrir WhatsApp Web
        add_log("Navegando a WhatsApp Web...")
        page.goto("https://web.whatsapp.com")
        page.wait_for_timeout(4000)

        # --- PASO 1: Detectar si hay QR o sesion activa ---
        PANE_XPATH = '//div[@id="pane-side"]'
        QR_XPATHS = [
            '//canvas[@aria-label="Scan me!"]',
            '//div[@data-testid="qrcode"]',
            '//div[@data-ref]',
        ]
        LOGIN_TIMEOUT = 120

        page_state = "loading"
        try:
            page.wait_for_selector(PANE_XPATH, timeout=20000)
            page_state = "logged_in"
        except _PWTimeoutError:
            for _qr in QR_XPATHS:
                try:
                    if page.query_selector(_qr):
                        page_state = "qr_visible"
                        break
                except Exception:
                    pass

        if page_state == "logged_in":
            add_log("✅ Sesion WhatsApp activa detectada. No es necesario escanear QR.")
        else:
            if page_state == "qr_visible":
                add_log("📱 QR visible en pantalla. Escanea con tu teléfono ahora.")
            else:
                add_log("⏳ Pagina cargando... el QR aparecera en instantes.")

            add_log(f"⚠️  ESCANEA EL CODIGO QR EN EL NAVEGADOR")
            add_log(f"⏳ Tienes {LOGIN_TIMEOUT} segundos para escanear...")

            if progress_callback:
                progress_callback(0, len(processed_contacts), "Escanea el QR en WhatsApp Web...", "\n".join(log_lines))

            try:
                page.wait_for_selector(PANE_XPATH, timeout=LOGIN_TIMEOUT * 1000)
                add_log("✅ Sesion iniciada correctamente.")
            except _PWTimeoutError:
                add_log("⚠️ Timeout de login. Verificando si la sesion esta activa...")
                page.wait_for_timeout(5000)

        # --- Capturar nombre de perfil y guardar info de sesion ---
        try:
            _profile_name = page.evaluate(
                "document.querySelector('span[data-testid=\"default-user\"]')?.textContent "
                "|| document.title || ''"
            ) or ""
            _phone = page.evaluate(
                "window.Store?.User?.getMaybeMeUser?.()?.id?.user || ''"
            ) or ""
            _save_wa_session_info(
                profile_name=str(_profile_name).strip(),
                phone=str(_phone).strip(),
            )
            if _phone:
                add_log(f"📱 Dispositivo: {_profile_name} ({_phone})")
            else:
                add_log(f"📱 Sesion guardada localmente.")
        except Exception:
            _save_wa_session_info()

        page.wait_for_timeout(3000)

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
                page.goto(url)

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
                            if page.query_selector_all(chat_loaded_xpath):
                                loaded = True
                                break

                            # Check invalid number popup (Fast Fail)
                            invalid_xpath = SELECTORS['invalid_number']
                            if page.query_selector_all(invalid_xpath):
                                raise ValueError("NumeroInvalido")

                        except ValueError as ve:
                            raise ve
                        except Exception:
                            pass
                        time.sleep(1)

                    if not loaded:
                        raise Exception("Timeout cargando chat (DOM no listo)")

                    time.sleep(2)  # Stability buffer
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

                        # Espera extendida para sincronización de sistema operativo
                        time.sleep(3)

                        # 2. Localizar input principal
                        inp_xpath = SELECTORS['input_box']
                        input_box = page.wait_for_selector(inp_xpath, timeout=30000)

                        # 3. CLICK FANTASMA (JS) + PEGAR
                        add_log("    📋 Pegando imagen (JS Force & Paste)...")
                        input_box.evaluate("el => { el.focus(); el.click(); }")
                        time.sleep(1)
                        page.keyboard.press("Control+V")

                        # 4. Verificar si apareció el modal con paciencia
                        try:
                            preview_indicator = SELECTORS['preview_loading']
                            page.wait_for_selector(preview_indicator, timeout=15000)
                            image_sent_success = True
                        except _PWTimeoutError:
                            # REINTENTO DE EMERGENCIA
                            add_log("      ⚠️ Modal lento, reintentando pegado manual...")
                            page.keyboard.press("Control+V")
                            time.sleep(5)
                            if not page.query_selector(preview_indicator):
                                raise Exception("WhatsApp no detectó la imagen tras el pegado (Modal ausente)")

                        # 5. Una vez en el modal, buscar botón enviar
                        time.sleep(1.5)

                        send_btn_selectors = SELECTORS['send_button']

                        # 6. Buscar el botón de envío (Con paciencia)
                        send_button = None
                        for _ in range(15):
                            for selector in send_btn_selectors:
                                try:
                                    btns = [b for b in page.query_selector_all(selector) if b.is_visible()]
                                    if btns:
                                        send_button = btns[0]
                                        break
                                except Exception:
                                    pass
                            if send_button:
                                break
                            time.sleep(0.5)

                        if not send_button:
                            raise Exception("No se visualizó el botón Enviar en el modal")

                        # 7. Escribir el Caption (Mensaje)
                        try:
                            caption_selectors = SELECTORS['modal_caption']
                            caption_box = None
                            for selector in caption_selectors:
                                try:
                                    candidates = [c for c in page.query_selector_all(selector) if c.is_visible()]
                                    if candidates:
                                        caption_box = candidates[0]
                                        break
                                except Exception:
                                    pass

                            if caption_box:
                                add_log("    📝 Agregando mensaje...")
                                import pyperclip
                                pyperclip.copy(final_msg)
                                caption_box.evaluate("el => { el.focus(); el.click(); }")
                                time.sleep(0.5)
                                page.keyboard.press("Control+V")
                                time.sleep(0.5)
                        except Exception as e_cap:
                            add_log(f"    ⚠️ Error en caption (opcional): {str(e_cap)}")

                        # 8. Envío Final (JS Click para no fallar por superposición)
                        send_button.evaluate("el => el.click()")

                        add_log(f"    ✅ Imagen enviada a {nombre}")

                        # NUEVO v5.0: Adjuntar PDF si está en modo imagen_pdf
                        pdf_path = contact.get('pdf_path')
                        if pdf_path and os.path.exists(pdf_path):
                            try:
                                add_log(f"    📎 Adjuntando PDF...")
                                time.sleep(5)

                                attachment_success = False
                                for attempt_idx in range(3):
                                    try:
                                        add_log(f"    📎 Intento adjuntar PDF ({attempt_idx+1}/3)...")

                                        attach_btn = None
                                        attach_selectors = SELECTORS['attach_menu_btn']
                                        for selector in attach_selectors:
                                            try:
                                                attach_btn = page.query_selector(selector)
                                                if attach_btn:
                                                    break
                                            except Exception:
                                                continue

                                        if not attach_btn:
                                            time.sleep(1)
                                            continue

                                        attach_btn.evaluate("el => el.click()")
                                        time.sleep(1)

                                        file_input = None
                                        try:
                                            file_input = page.wait_for_selector(SELECTORS['file_input'], timeout=5000)
                                        except _PWTimeoutError:
                                            pass

                                        if not file_input:
                                            add_log("    ⚠️ Input file no encontrado, reintentando...")
                                            continue

                                        abs_pdf_path = os.path.abspath(pdf_path)
                                        file_input.set_input_files(abs_pdf_path)

                                        preview_selectors = [SELECTORS['modal_view']] + SELECTORS['modal_caption']
                                        preview_found = False
                                        for _ in range(10):
                                            time.sleep(0.5)
                                            for selector in preview_selectors:
                                                if page.query_selector(selector):
                                                    preview_found = True
                                                    break
                                            if preview_found:
                                                break

                                        if preview_found:
                                            attachment_success = True
                                            add_log("    ✅ Preview detectado")
                                            break
                                        else:
                                            add_log("    ⚠️ Preview no apareció, reintentando clip...")
                                            try:
                                                page.keyboard.press("Escape")
                                            except Exception:
                                                pass
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
                                send_btn = None

                                # INTENTO 1: Escribir caption + Enter
                                try:
                                    caption_selectors = SELECTORS['modal_caption']
                                    caption_box = None
                                    for selector in caption_selectors:
                                        try:
                                            elems = [e for e in page.query_selector_all(selector) if e.is_visible()]
                                            if elems:
                                                caption_box = elems[0]
                                                break
                                        except Exception:
                                            pass

                                    if caption_box:
                                        add_log(f"    📝 Escribiendo caption para activar UI...")
                                        caption_box.evaluate("el => el.click()")
                                        time.sleep(0.5)
                                        caption_box.type("Adjunto estado de cuenta")
                                        time.sleep(1)

                                        add_log(f"    ⌨️  ENVIANDO CON ENTER (Fuerza Bruta)...")
                                        page.keyboard.press("Enter")
                                        time.sleep(3)

                                        if _check_modal_gone(page):
                                            pdf_sent_confirmed = True
                                            add_log(f"    ✅ Modal cerrado detectado (Enter)")
                                        else:
                                            add_log(f"    ⚠️ Modal sigue abierto, segundo Enter...")
                                            page.keyboard.press("Enter")
                                            time.sleep(2)
                                            if _check_modal_gone(page):
                                                pdf_sent_confirmed = True
                                                add_log(f"    ✅ Modal cerrado detectado (2do Enter)")
                                    else:
                                        add_log(f"    ⚠️ No se encontró caption, buscando botón...")
                                        send_btn_selectors = SELECTORS['send_button']
                                        for selector in send_btn_selectors:
                                            try:
                                                btns = [b for b in page.query_selector_all(selector) if b.is_visible()]
                                                if btns:
                                                    send_btn = btns[0]
                                                    break
                                            except Exception:
                                                pass

                                        if send_btn:
                                            add_log(f"    🖱️  Click Nativo en botón enviar...")
                                            send_btn.click()
                                            time.sleep(3)
                                            if _check_modal_gone(page):
                                                pdf_sent_confirmed = True
                                                add_log(f"    ✅ Modal cerrado (Click)")

                                except Exception as e:
                                    add_log(f"    ⚠️ Intento 1 falló: {str(e)[:50]}")

                                # INTENTO 2: JS Click si el modal sigue abierto
                                if not pdf_sent_confirmed:
                                    add_log(f"    🎯 Intento 2: JS Click Force...")
                                    try:
                                        if send_btn:
                                            send_btn.evaluate("el => el.click()")
                                            time.sleep(3)
                                            if _check_modal_gone(page):
                                                pdf_sent_confirmed = True
                                                add_log(f"    ✅ Modal cerrado detectado (JS Click)")
                                            elif _check_pdf_sent(page, pdf_path):
                                                pdf_sent_confirmed = True
                                                add_log(f"    ✅ Mensaje encontrado en chat (JS Click)")
                                    except Exception as e:
                                        add_log(f"    ⚠️ Intento 2 falló: {str(e)[:50]}")

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
                        input_box = page.wait_for_selector(inp_xpath, timeout=30000)

                        # Paste Text (Robust Focus)
                        import pyperclip
                        pyperclip.copy(final_msg)

                        input_box.evaluate("el => el.focus()")
                        try:
                            input_box.click()
                        except Exception:
                            input_box.evaluate("el => el.click()")

                        page.keyboard.press("Control+V")
                        time.sleep(1)
                        page.keyboard.press("Enter")

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
        add_log(f"ERROR FATAL NAVEGADOR: {str(e)}")
        if progress_callback:
            progress_callback(0, 0, "Error Fatal", "\n".join(log_lines))
    finally:
        if wa_context:
            add_log("Cerrando navegador...")
            try:
                wa_context.close()
            except Exception:
                pass
        try:
            _playwright.stop()
        except Exception:
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
