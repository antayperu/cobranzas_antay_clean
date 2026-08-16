@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title REPORTE COBRANZAS ANTAY - SERVIDOR QA
set "APP_PORT=8503"
if not defined ACCESS_LINK_RECIPIENT set "ACCESS_LINK_RECIPIENT=cortega@antayperu.com"

color 0B
echo ============================================================
echo   REPORTE COBRANZAS ANTAY - APP + TUNEL (Puerto %APP_PORT%)
echo ============================================================
echo.

echo [0/4] Limpiando estado de sesion anterior...
del /f /q url_sent.lock 2>nul
del /f /q tunnel.log 2>nul
del /f /q 00_LINK_ACCESO_HOY.txt 2>nul
del /f /q url_notifier.log 2>nul
del /f /q streamlit.log 2>nul

if not exist cloudflared.exe (
    echo [ERROR] No se encontro cloudflared.exe
    pause
    exit /b
)

echo [0b/4] Reparando dependencias del entorno (puede tomar 3-5 min)...
venv_prod\Scripts\pip install pandas PyJWT python-dotenv GitPython markdown-it-py nest-asyncio Pillow protobuf rpds-py --force-reinstall --quiet > pip_install.log 2>&1
venv_prod\Scripts\pip install -r requirements.txt --quiet >> pip_install.log 2>&1
echo [OK] Dependencias listas.

echo [1/4] Iniciando App Streamlit (puerto %APP_PORT%)...
start /b cmd /c "call venv_prod\Scripts\activate && set PYTHONIOENCODING=utf-8 && streamlit run app.py --server.port %APP_PORT% --server.headless true > streamlit.log 2>&1"

echo [2/4] Iniciando Tunel Cloudflare...
echo Iniciando tunel... > tunnel.log
start /b cmd /c "cloudflared.exe tunnel --url http://localhost:%APP_PORT% > tunnel.log 2>&1"

echo [3/4] Esperando URL del tunel (15s)...
timeout /t 15 >nul

echo [3b/4] Ejecutando notificador Python...
set PYTHONIOENCODING=utf-8
call venv_prod\Scripts\activate && python modules\url_notifier.py > url_notifier.log 2>&1

if exist 00_LINK_ACCESO_HOY.txt goto :url_ok

echo [3c/4] Python no genero el archivo. Extrayendo URL con PowerShell...
powershell -NoProfile -Command "$m=(Select-String -Pattern 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' -Path 'tunnel.log' -ErrorAction SilentlyContinue).Matches[0].Value; if ($m){'URL: '+$m | Out-File -Encoding utf8 '00_LINK_ACCESO_HOY.txt'; Write-Host 'URL extraida: '+$m} else {Write-Host 'URL no encontrada en tunnel.log'}"

:url_ok
if exist 00_LINK_ACCESO_HOY.txt (
    echo [OK] URL de acceso lista.
) else (
    echo [AVISO] URL no disponible. Revisa url_notifier.log y tunnel.log
)

echo.
echo [4/4] Sistema iniciado. Monitoreo activo...
echo ============================================================
timeout /t 10 >nul

:monitor_loop
cls
echo ============================================================
echo   REPORTE COBRANZAS ANTAY - EJECUTANDOSE EN SERVIDOR QA
echo ============================================================
echo.
echo  [!] NO CIERRES ESTA VENTANA  [!]
echo      Puedes minimizarla.
echo.
echo  Estado: ACTIVO
echo  Hora  : %TIME%
echo  Puerto: %APP_PORT%
echo.
echo  URL DE ACCESO HOY:
if exist 00_LINK_ACCESO_HOY.txt (
    for /f "tokens=2 delims= " %%A in ('findstr "URL:" 00_LINK_ACCESO_HOY.txt') do echo  %%A
) else (
    echo  (pendiente de generar)
)
echo ============================================================
timeout /t 60 >nul
goto monitor_loop
