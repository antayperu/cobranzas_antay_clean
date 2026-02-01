import os
import sys

# Añadir el directorio actual al path para encontrar utils
sys.path.append(os.path.dirname(__file__))

# Importar app de streamlit
# Vercel necesita un handler WSGI/ASGI, pero Streamlit corre como proceso.
# Para Vercel usaremos el patrón de serverless function que levanta streamlit.
# NOTA: En 2026 Vercel tiene soporte mejorado pero el patrón index.py sigue siendo el más estable.

from streamlit.web.bootstrap import run

if __name__ == "__main__":
    run("app.py", "", [], flag_options={})
