@echo off
setlocal
cd /d "%~dp0"
title REPORTE COBRANZAS ANTAY - SERVIDOR QA

color 0B
echo ============================================================
echo   REPORTE COBRANZAS ANTAY - APP + TUNEL (Puerto 8503)
echo ============================================================
echo.

echo [0/4] Limpiando estado de sesion anterior...
del /f /q url_sent.lock 2>nul
del /f /q tunnel.log 2>nul

echo [1/4] Iniciando App Streamlit (puerto 8503)...
start /b cmd /c "call venv_prod\Scripts\activate && streamlit run app.py --server.port 8503 --server.headless true"

echo [2/4] Iniciando Tunel Cloudflare...
if exist cloudflared.exe (
    echo Iniciando tunel... > tunnel.log
    start /b cmd /c "cloudflared.exe tunnel --url http://localhost:8503 > tunnel.log 2>&1"

    echo [3/4] Esperando URL del tunel...
    timeout /t 8 >nul
    call venv_prod\Scripts\activate && python modules\url_notifier.py
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
echo  Puerto: 8503
echo ============================================================
timeout /t 60 >nul
goto monitor_loop
