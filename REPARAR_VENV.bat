@echo off
cd /d C:\antay-cobranza
title REPARANDO DEPENDENCIAS - REPORTE COBRANZAS
color 0E
echo ============================================================
echo   REPARANDO DEPENDENCIAS DEL ENTORNO VIRTUAL
echo ============================================================
echo.
echo Este proceso reinstala todos los paquetes necesarios.
echo Puede tardar 5-10 minutos. NO cierres esta ventana.
echo.
echo [1/3] Reinstalando paquetes con historial de corrupcion conocida...
venv_prod\Scripts\pip install pandas PyJWT python-dotenv GitPython markdown-it-py nest-asyncio Pillow protobuf rpds-py --force-reinstall
echo.
echo [2/3] Instalando resto de dependencias desde requirements.txt...
venv_prod\Scripts\pip install -r requirements.txt
echo.
echo [3/3] Verificando Streamlit...
venv_prod\Scripts\python -c "import streamlit, pandas, jwt; print('[OK] Entorno verificado. Streamlit v' + streamlit.__version__ + ' / pandas v' + pandas.__version__)"
echo.
if errorlevel 1 (
    echo [ERROR] Aun hay problemas. Revisa la salida arriba y contacta soporte.
) else (
    echo [OK] Entorno reparado correctamente.
    echo      Ahora puedes abrir 5_COMBINADO_APP_Y_TUNEL.bat
)
echo.
pause
