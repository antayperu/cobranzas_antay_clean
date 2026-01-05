import os
import tempfile
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image

def create_whatsapp_card_html(content_html, p_col, s_col, logo_data_b64):
    """Mismo HTML generator que app.py"""
    img_tag_html = ""
    if logo_data_b64:
        img_tag_html = f'<img src="data:image/png;base64,{logo_data_b64}" class="wa-logo" alt="Logo"/>'
    
    return f"""
    <html>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        body {{ margin: 0; padding: 0; background: transparent; font-family: 'Roboto', sans-serif; }}
        .wa-card {{
            width: 400px;
            max-width: 100%;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            overflow: hidden;
            margin: 10px auto;
            border: 1px solid #e0e0e0;
        }}
        .wa-banner {{
            background: linear-gradient(135deg, {p_col} 0%, {s_col} 100%);
            min-height: 120px;
            position: relative;
            padding: 20px;
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: flex-start;
        }}
        .wa-content {{
            padding: 20px 25px 30px 25px;
            color: #333;
            font-size: 14px;
            line-height: 1.5;
        }}
    </style>
    <body>
        <div class="wa-card" id="card">
            <div class="wa-banner">
                {img_tag_html}
                <div style="font-size: 20px; font-weight: 700;">Importante</div>
            </div>
            <div class="wa-content">
                {content_html}
            </div>
        </div>
    </body>
    </html>
    """

def test_long_content():
    print("Generando contenido largo (50 items)...")
    
    lines = []
    for i in range(1, 51):
        lines.append(f"<p>Documento Pendiente #{i} - S/ 1,000.00 (Vencido)</p><hr>")
    
    long_html = "".join(lines)
    
    full_html = create_whatsapp_card_html(long_html, "#007bff", "#00d4ff", None)
    
    # Configuración Selenium (LA MISMA QUE APP.PY CON EL FIX)
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--window-size=500,2500") # <--- EL FIX
    chrome_opts.add_argument("--hide-scrollbars")
    chrome_opts.add_argument("--disable-gpu")
    
    print("Iniciando Selenium...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)
    wait = WebDriverWait(driver, 10)
    
    try:
        t_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8')
        t_html.write(full_html)
        t_html.close()
        
        driver.get(f"file:///{t_html.name}")
        card_elem = wait.until(EC.presence_of_element_located((By.ID, "card")))
        
        # Obtener altura real del elemento
        height = card_elem.size['height']
        print(f"Altura detectada del elemento card: {height}px")
        
        t_png = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        t_png.close()
        card_elem.screenshot(t_png.name)
        
        img = Image.open(t_png.name)
        print(f"Imagen generada: {img.width}x{img.height}")
        
        # Verificación
        if img.height >= height:
            print("✅ La imagen capturó TODO el contenido (Height match or greater)")
        else:
            print(f"❌ La imagen se cortó. Elemento: {height}px, Imagen: {img.height}px")
            
        # Limpieza
        try:
            os.remove(t_html.name)
            os.remove(t_png.name)
        except: pass
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_long_content()
