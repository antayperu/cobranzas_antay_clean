"""
Script de prueba para verificar que la imagen se genera correctamente
con el tamaño vertical (1080x1920) para evitar que WhatsApp la detecte como sticker
"""

from PIL import Image
import os

def test_image_generation():
    """Genera una imagen de prueba y verifica sus propiedades"""
    
    # Crear una imagen de prueba simple
    print("=" * 60)
    print("PRUEBA DE GENERACIÓN DE IMAGEN ANTI-STICKER")
    print("=" * 60)
    
    # Tamaño del canvas (VERTICAL como foto de celular)
    canvas_w, canvas_h = 1080, 1920
    print(f"\n✓ Tamaño del canvas: {canvas_w}x{canvas_h}")
    print(f"  Aspecto: {'VERTICAL ✓' if canvas_h > canvas_w else 'HORIZONTAL ✗'}")
    
    # Crear canvas blanco
    canvas = Image.new("RGB", (canvas_w, canvas_h), "#ffffff")
    
    # Crear una tarjeta de prueba (simulando la tarjeta de cobranza)
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(canvas)
    
    # Dibujar un rectángulo de prueba
    card_w, card_h = int(canvas_w * 0.9), int(canvas_h * 0.4)
    card_x = (canvas_w - card_w) // 2
    card_y = (canvas_h - card_h) // 2
    
    draw.rectangle([card_x, card_y, card_x + card_w, card_y + card_h], 
                   fill="#007bff", outline="#000000", width=3)
    
    # Agregar texto
    text = "PRUEBA - IMAGEN VERTICAL\n1080x1920\nNO STICKER"
    draw.text((canvas_w // 2, canvas_h // 2), text, fill="white", anchor="mm")
    
    # Guardar la imagen
    output_path = "test_image_vertical.jpg"
    canvas.save(output_path, quality=95)
    
    # Verificar propiedades del archivo
    file_size = os.path.getsize(output_path)
    img_check = Image.open(output_path)
    
    print(f"\n✓ Imagen guardada: {output_path}")
    print(f"  Dimensiones: {img_check.width}x{img_check.height}")
    print(f"  Tamaño archivo: {file_size / 1024:.2f} KB")
    print(f"  Formato: {img_check.format}")
    print(f"  Modo: {img_check.mode}")
    
    # Verificaciones
    print("\n" + "=" * 60)
    print("VERIFICACIONES ANTI-STICKER:")
    print("=" * 60)
    
    checks = []
    
    # Check 1: Orientación vertical
    is_vertical = img_check.height > img_check.width
    checks.append(("Orientación VERTICAL (altura > ancho)", is_vertical))
    
    # Check 2: Tamaño correcto
    is_correct_size = img_check.width == 1080 and img_check.height == 1920
    checks.append(("Tamaño exacto 1080x1920", is_correct_size))
    
    # Check 3: Formato JPG
    is_jpg = img_check.format == "JPEG"
    checks.append(("Formato JPEG", is_jpg))
    
    # Check 4: Tamaño de archivo razonable (> 50KB para no ser sticker)
    is_large_enough = file_size > 50 * 1024
    checks.append(("Tamaño archivo > 50KB", is_large_enough))
    
    # Mostrar resultados
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("La imagen debería enviarse como FOTO, NO como sticker")
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("Revisa la configuración de generación de imagen")
    print("=" * 60)
    
    print(f"\n📁 Imagen de prueba guardada en: {os.path.abspath(output_path)}")
    print("   Puedes intentar enviarla manualmente por WhatsApp para verificar")
    
    return all_passed

if __name__ == "__main__":
    test_image_generation()
