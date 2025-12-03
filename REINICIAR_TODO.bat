@echo off
echo ========================================
echo REINICIO COMPLETO DEL SISTEMA SIAR
echo ========================================
echo.

echo [1/4] Matando todos los procesos Python y servidores...
taskkill /F /IM python.exe 2>nul
timeout /t 2 >nul

echo.
echo [2/4] Esperando 3 segundos...
timeout /t 3 >nul

echo.
echo [3/4] Iniciando servidor HTTP (puerto 8080)...
start "SIAR Frontend" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python -m http.server 8080 --directory frontend"
timeout /t 2 >nul

echo.
echo [4/4] Iniciando API FastAPI (puerto 8000)...
start "SIAR API" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python -m uvicorn src.integracion.api_siar:app --reload --port 8000"

echo.
echo ========================================
echo ✓ SISTEMA INICIADO
echo ========================================
echo.
echo Frontend: http://localhost:8080/index.html
echo API: http://localhost:8000/docs
echo Alertas FSM: http://localhost:8080/alertas_fsm.html
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
