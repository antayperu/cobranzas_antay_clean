@echo off
setlocal
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

call :resolve_python
if errorlevel 1 exit /b 1

echo [1/4] Iniciando App Streamlit (puerto %APP_PORT%)...
start /b cmd /c ""%PYTHON_CMD%" -m streamlit run app.py --server.port %APP_PORT% --server.headless true"

echo [2/4] Iniciando Tunel Cloudflare...
if exist cloudflared.exe (
    echo Iniciando tunel... > tunnel.log
    start /b cmd /c "cloudflared.exe tunnel --url http://localhost:%APP_PORT% > tunnel.log 2>&1"

    echo [3/4] Esperando URL del tunel...
    timeout /t 8 >nul
    "%PYTHON_CMD%" modules\url_notifier.py
    if errorlevel 1 (
        echo [AVISO] No se pudo enviar la notificacion de acceso.
        echo         Busca la URL en: 00_LINK_ACCESO_HOY.txt
    ) else (
        echo [OK] Notificacion de acceso enviada exitosamente.
    )
) else (
    echo [ERROR] No se encontro cloudflared.exe
    pause
    exit /b
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

:resolve_python
if exist "venv_prod\Scripts\python.exe" (
    set "PYTHON_CMD=venv_prod\Scripts\python.exe"
    goto :eof
)

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    goto :eof
)

set "SYSTEM_PYTHON="
py -3.12 --version >nul 2>nul && set "SYSTEM_PYTHON=py -3.12"
if not defined SYSTEM_PYTHON py -3 --version >nul 2>nul && set "SYSTEM_PYTHON=py -3"
if not defined SYSTEM_PYTHON python --version >nul 2>nul && set "SYSTEM_PYTHON=python"

if not defined SYSTEM_PYTHON (
    echo [ERROR] No se encontro Python 3 en el servidor QA.
    echo Instala Python 3.12 o copia venv_prod dentro de esta carpeta.
    pause
    exit /b 1
)

echo [SETUP] venv_prod no existe. Creando entorno por primera vez...
call %SYSTEM_PYTHON% -m venv venv_prod
if errorlevel 1 (
    echo [ERROR] No se pudo crear venv_prod.
    pause
    exit /b 1
)

echo [SETUP] Instalando dependencias...
"venv_prod\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Fallo actualizando pip en venv_prod.
    pause
    exit /b 1
)

"venv_prod\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo instalando dependencias desde requirements.txt.
    pause
    exit /b 1
)

set "PYTHON_CMD=venv_prod\Scripts\python.exe"
goto :eof
