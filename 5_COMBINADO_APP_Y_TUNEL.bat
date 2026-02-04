@echo off
setlocal
title REPORTE COBRANZAS ANTAY - LANZADOR PROFESIONAL

:: Configuración de colores (Fondo negro, texto aguamarina)
color 0B

echo ======================================================
echo    REPORTE COBRANZAS ANTAY - MODO HIBRIDO (CLOUDFLARE)
echo ======================================================
echo.
echo [1/3] Verificando entorno Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta en el PATH.
    pause
    exit /b
)

echo [2/3] Lanzando Aplicacion Streamlit en segundo plano...
:: Usamos taskkill para limpiar sesiones previas en el puerto 8501 si las hubiera
taskkill /f /im python.exe /fi "windowtitle eq Streamlit*" >nul 2>&1
start "StreamlitApp" /b cmd /c "python -m streamlit run app.py --server.port 8501 --server.headless true"

echo [3/3] Iniciando Tunel PROFESIONAL (Cloudflare)...
echo.
echo    ESTABLECIENDO CONEXION SEGURA...
echo    (Esto tardara unos segundos)
echo.
echo    Paciencia: npm esta preparando el tunel...
echo.

:: Corregido: el paquete es 'cloudflared' directamente
npx -y cloudflared tunnel --url http://localhost:8501

echo.
echo Aplicacion cerrada o error en el tunel.
pause
