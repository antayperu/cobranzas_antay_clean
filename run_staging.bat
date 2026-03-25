@echo off
cd /d c:\dev\ReporteCobranzas

set PYTHON=C:\Users\corte\AppData\Local\Programs\Python\Python312\python.exe
set PATH=C:\Users\corte\AppData\Local\Programs\Python\Python312\Scripts;C:\Users\corte\AppData\Local\Programs\Python\Python312;%PATH%

set SUPABASE_URL=https://hrnqngndnohkkegtzgjg.supabase.co
set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhybnFuZ25kbm9oa2tlZ3R6Z2pnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzQ1NzQ4NCwiZXhwIjoyMDg5MDMzNDg0fQ.Z0x-3mT7oqqDl1KOndu0EdifE8jGOUeF5U9F-vktqOY

echo ====================================
echo  ReporteCobranzas v1.9.0 - STAGING
echo  SUPABASE: %SUPABASE_URL%
echo  Puerto  : 8502
echo ====================================
echo.
echo Verificando Python...
%PYTHON% --version
echo.
echo Iniciando Streamlit...
%PYTHON% -m streamlit run app.py --server.port 8502 --browser.gatherUsageStats false
pause
