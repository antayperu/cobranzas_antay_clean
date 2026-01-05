import os
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PIL import Image

def create_whatsapp_card_html(content_html):
    return f"""
    <html>
    <body style="margin:0; padding:0;">
        <div id="card" style="width:400px; padding:20px; background:white; border:1px solid black;">
            <h1>Header</h1>
            {content_html}
            <h1>Footer</h1>
        </div>
    </body>
    </html>
    """

def test_dynamic_resize():
    # 1. Generar contenido MASIVO (200 items -> ~10,000px height estim approx)
    print("Generando contenido MASIVO (200 items)...")
    lines = []
    for i in range(1, 201):
        lines.append(f"<p>Documento #{i}</p>")
    full_html = create_whatsapp_card_html("".join(lines))
    
    # 2. Configurar Driver (Tamaño inicial pequeño)
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--window-size=500,800") # Start small
    chrome_opts.add_argument("--hide-scrollbars")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)
    
    try:
        # Cargar HTML
        t_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8')
        t_html.write(full_html)
        t_html.close()
        driver.get(f"file:///{t_html.name}")
        
        # 3. Lógica Enterprise: MEDIR y REDIMENSIONAR
        # Esperar elemento
        card = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "card")))
        
        # Obtener altura requerida
        required_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        card_height = driver.execute_script("return document.getElementById('card').offsetHeight")
        
        print(f"Altura inicial ventana: {driver.get_window_size()['height']}")
        print(f"Altura requerida (Body): {required_height}")
        print(f"Altura Card: {card_height}")
        
        # Redimensionar (Factor de seguridad +100)
        new_height = required_height + 200
        print(f"Redimensionando ventana a: {new_height}...")
        driver.set_window_size(500, new_height)
        
        # Verificar nuevo tamaño
        print(f"Altura nueva ventana: {driver.get_window_size()['height']}")
        
        # Screenshot
        t_png = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        t_png.close()
        card.screenshot(t_png.name)
        
        img = Image.open(t_png.name)
        print(f"Imagen Generada: {img.width}x{img.height}")
        
        if img.height >= card_height:
            print("✅ ÉXITO: La imagen capturó todo el contenido tras el resize.")
        else:
            print("❌ FALLO: La imagen sigue cortada.")

    finally:
        driver.quit()
        if os.path.exists(t_html.name): os.remove(t_html.name)

if __name__ == "__main__":
    test_dynamic_resize()
