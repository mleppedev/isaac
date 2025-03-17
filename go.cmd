@echo off
setlocal enabledelayedexpansion

REM Leer configuración desde config.txt
for /F "tokens=1,* delims==" %%a in (config.txt) do (
    if not "%%a"=="#" (
        set "%%a=%%b"
    )
)

REM Verificar si las variables están definidas
if not defined GAME_PATH (
    echo Error: GAME_PATH no está definido en config.txt
    exit /b 1
)
if not defined MOD_NAME (
    echo Error: MOD_NAME no está definido en config.txt
    exit /b 1
)
if not defined GAME_EXE (
    echo Error: GAME_EXE no está definido en config.txt
    exit /b 1
)

REM Definir rutas del mod
set "MOD_SOURCE=.\%MOD_NAME%"
set "MOD_DEST=%GAME_PATH%\mods\%MOD_NAME%"
set "SERVER_PATH=.\server"

:menu
cls
echo === Herramienta de Despliegue del Mod DEM ===
echo.
echo Elija una opción:
echo 1. Copiar archivos del mod al directorio del juego
echo 2. Iniciar el servidor
echo 3. Lanzar el juego
echo 4. Hacer todo (copiar, iniciar servidor, lanzar juego)
echo 5. Salir
echo.
set /p choice="Ingrese su elección (1-5): "

if "%choice%"=="1" goto copy_mod
if "%choice%"=="2" goto start_server
if "%choice%"=="3" goto launch_game
if "%choice%"=="4" goto do_all
if "%choice%"=="5" goto end
echo Opción inválida. Por favor intente de nuevo.
timeout /t 2 >nul
goto menu

:copy_mod
echo.
echo Copiando archivos del mod a %MOD_DEST%...
if not exist "%MOD_DEST%" mkdir "%MOD_DEST%"
xcopy /E /Y /Q "%MOD_SOURCE%\*" "%MOD_DEST%\" > nul
if %ERRORLEVEL% neq 0 (
    echo Error: No se pudieron copiar los archivos del mod.
    pause
    goto menu
)
echo Archivos del mod copiados exitosamente.
pause
goto menu

:start_server
echo.
echo Iniciando servidor...
if not exist "%SERVER_PATH%" (
    echo Error: Directorio del servidor no encontrado en %SERVER_PATH%
    pause
    goto menu
)
cd "%SERVER_PATH%"
start cmd /k "python app.py"
cd ..
echo Servidor iniciado en una nueva ventana.
pause
goto menu

:launch_game
echo.
echo Lanzando juego...
start "" "%GAME_PATH%\%GAME_EXE%"
echo Juego lanzado.
pause
goto menu

:do_all
echo.
echo === Realizando todas las operaciones ===
echo.
echo Copiando archivos del mod a %MOD_DEST%...
if not exist "%MOD_DEST%" mkdir "%MOD_DEST%"
xcopy /E /Y /Q "%MOD_SOURCE%\*" "%MOD_DEST%\" > nul
if %ERRORLEVEL% neq 0 (
    echo Error: No se pudieron copiar los archivos del mod.
    pause
    goto menu
)
echo Archivos del mod copiados exitosamente.
echo.
echo Iniciando servidor...
if not exist "%SERVER_PATH%" (
    echo Error: Directorio del servidor no encontrado en %SERVER_PATH%
    pause
    goto menu
)
cd "%SERVER_PATH%"
start cmd /k "python app.py"
cd ..
echo Servidor iniciado en una nueva ventana.
echo.
echo Lanzando juego...
start "" "%GAME_PATH%\%GAME_EXE%"
echo Juego lanzado.
echo.
echo === Todas las operaciones completadas exitosamente ===
pause
goto menu

:end
echo Saliendo...
exit /b 0 