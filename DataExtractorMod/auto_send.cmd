@echo off
echo ===================================================
echo    Enviando Datos al Servidor (Modo Automático)
echo ===================================================
echo.

:: Obtener la ruta del script
set "SCRIPT_DIR=%~dp0"
cd "%SCRIPT_DIR%"

:: Verificar si Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python no está instalado o no está en el PATH.
    echo Por favor, instala Python y asegúrate de que esté en el PATH.
    pause
    exit /b 1
)

:: Verificar si el módulo requests está instalado
python -c "import requests" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando el módulo requests...
    python -m pip install requests
    if %ERRORLEVEL% NEQ 0 (
        echo Error: No se pudo instalar el módulo requests.
        pause
        exit /b 1
    )
)

echo Iniciando monitoreo de datos...
echo El script se ejecutará cada 30 segundos.
echo Presiona Ctrl+C para detener.
echo.

:loop
echo [%date% %time%] Verificando datos pendientes...
python send_data.py
timeout /t 30 /nobreak >nul
goto loop 