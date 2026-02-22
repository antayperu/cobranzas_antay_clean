import time
import re
import os
import sys
from datetime import datetime
from email_sender import send_access_link # Nuevo modulo de notificacion

SENT_LOCK = "url_sent.lock"


def find_and_save_tunnel_url(log_file="tunnel.log", output_file="00_LINK_ACCESO_HOY.txt", timeout_seconds=60):
    """
    Monitorea el archivo de log hasta encontrar la URL de Cloudflare y la guarda.
    """
    # Guardia de deduplicacion: si ya se envio el correo en esta sesion, no reenviar
    if os.path.exists(SENT_LOCK):
        with open(SENT_LOCK, 'r', encoding='utf-8') as _f:
            _sent_url = _f.read().strip()
        print(f"[SKIP] Correo ya enviado para esta sesion: {_sent_url}")
        return True

    print(f"🔍 Buscando URL en {log_file}...")
    
    start_time = time.time()
    url_pattern = r"https://[a-zA-Z0-9-]+\.trycloudflare\.com"
    
    # Esperar a que exista el archivo de log
    while not os.path.exists(log_file):
        if time.time() - start_time > timeout_seconds:
            print("❌ Timeout esperando creación del archivo de log.")
            return False
        time.sleep(1)

    # Leer el archivo buscando la URL
    while time.time() - start_time < timeout_seconds:
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                match = re.search(url_pattern, content)
                
                if match:
                    url = match.group(0)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Guardar URL en archivo visible
                    with open(output_file, 'w', encoding='utf-8') as out:
                        out.write("==========================================\n")
                        out.write(f"🔗 LINK DE ACCESO ANTAY REPORTE\n")
                        out.write("==========================================\n\n")
                        out.write(f"Fecha: {timestamp}\n")
                        out.write(f"URL:   {url}\n\n")
                        out.write("Este link cambiara si el servidor se reinicia.\n")
                    
                    print(f"✅ URL encontrada y guardada en {output_file}: {url}")

                    # Crear lock ANTES de enviar para evitar doble envio si hay reintentos
                    with open(SENT_LOCK, 'w', encoding='utf-8') as _lf:
                        _lf.write(url)

                    # Notificar por Email
                    send_access_link(url)

                    return True
                    
        except Exception as e:
            print(f"⚠️ Error leyendo log: {e}")
        
        time.sleep(2)
        
    print("❌ Timeout: No se encontró la URL en el tiempo esperado.")
    return False

if __name__ == "__main__":
    # Ajustar directorio de trabajo al del script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # Subir un nivel para estar en root del proyecto
    os.chdir("..")
    
    find_and_save_tunnel_url()
