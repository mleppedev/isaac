@echo off
setlocal enabledelayedexpansion

:: Establecer valores predeterminados
set "GAME_PATH=D:\SteamLibrary\steamapps\common\The Binding of Isaac Rebirth"
set "MOD_NAME=DataExtractorMod"

:: Cargar configuración desde config.txt si existe
if exist "config.txt" (
    echo Cargando configuración desde config.txt...
    for /F "usebackq tokens=1,* delims==" %%A in ("config.txt") do (
        if not "%%A"=="" (
            if not "%%A:~0,1%"=="#" (
                set "%%A=%%B"
            )
        )
    )
) else (
    echo Archivo config.txt no encontrado. Creando uno con valores predeterminados...
    echo # Configuración del entorno> config.txt
    echo GAME_PATH=%GAME_PATH%>> config.txt
    echo MOD_NAME=%MOD_NAME%>> config.txt
)

:: Verificar si se pasó un parámetro
if "%1"=="update" goto update_mod
if "%1"=="help" goto show_help
if "%1"=="setpath" goto set_path
if "%1"=="server" goto start_server
if "%1"=="autosend" goto auto_send

:: Si no hay parámetros, mostrar menú
:menu
cls
echo ===================================================
echo    DataExtractorMod - Menú Principal
echo ===================================================
echo.
echo  [1] Iniciar servidor
echo  [2] Actualizar mod en el juego
echo  [3] Configurar ruta del juego
echo  [4] Iniciar envío automático de datos
echo  [5] Mostrar ayuda
echo  [6] Salir
echo.
echo ===================================================
echo  Configuración actual:
echo  - Ruta del juego: "%GAME_PATH%"
echo  - Nombre del mod: "%MOD_NAME%"
echo ===================================================
echo.

set /p opcion="Selecciona una opción (1-6): "

if "%opcion%"=="1" goto start_server
if "%opcion%"=="2" goto update_mod
if "%opcion%"=="3" goto menu_setpath
if "%opcion%"=="4" goto auto_send
if "%opcion%"=="5" goto show_help
if "%opcion%"=="6" goto end

echo.
echo Opción no válida. Inténtalo de nuevo.
timeout /t 2 >nul
goto menu

:auto_send
cls
echo ===================================================
echo    Iniciar Envío Automático de Datos
echo ===================================================
echo.
echo Este proceso ejecutará el script de envío de datos
echo cada 30 segundos para asegurar que los datos recopilados
echo por el mod se envíen al servidor.
echo.
echo Debes mantener esta ventana abierta mientras juegas.
echo Presiona Ctrl+C para detener el proceso.
echo.
pause
echo.
echo Iniciando envío automático...
echo.
start "Envío Automático de Datos" /min cmd /c "cd DataExtractorMod && auto_send.cmd"
echo Proceso iniciado en segundo plano.
echo.
pause
goto menu

:menu_setpath
cls
echo ===================================================
echo    Configurar Ruta del Juego
echo ===================================================
echo.
echo Ruta actual: "%GAME_PATH%"
echo.
echo Ingresa la nueva ruta del juego:
echo (Ejemplo: D:\SteamLibrary\steamapps\common\The Binding of Isaac Rebirth)
echo.
set /p nueva_ruta="Nueva ruta: "

if "%nueva_ruta%"=="" (
    echo.
    echo La ruta no puede estar vacía.
    timeout /t 2 >nul
    goto menu
)

set "GAME_PATH=%nueva_ruta%"
echo.
echo Ruta del juego configurada: "%GAME_PATH%"

:: Guardar la configuración actualizada
call :save_config
echo.
echo Configuración guardada.
echo.
pause
goto menu

:: Función para guardar la configuración
:save_config
echo # Configuración del entorno> config.txt
echo GAME_PATH=%GAME_PATH%>> config.txt
echo MOD_NAME=%MOD_NAME%>> config.txt
exit /b

:start_server
echo ===================================================
echo    Iniciando Servidor para DataExtractorMod
echo ===================================================
echo.

:: Verificar si existe el entorno virtual, si no, crearlo
if not exist "server\venv" (
    echo Creando entorno virtual...
    cd server
    python -m venv venv
    cd ..
    echo Entorno virtual creado.
    echo.
)

:: Activar el entorno virtual e instalar dependencias si es necesario
echo Activando entorno virtual...
cd server
call venv\Scripts\activate

:: Verificar si las dependencias están instaladas
if not exist "venv\Lib\site-packages\pandas" (
    echo Instalando dependencias...
    venv\Scripts\pip install -r requirements.txt
    echo Dependencias instaladas.
    echo.
)

:: Iniciar el servidor
echo Iniciando servidor...
echo El servidor estará disponible en http://localhost:8000
echo Presiona Ctrl+C para detener el servidor
echo.
python app.py

:: Esta parte solo se ejecutará si el servidor se detiene
echo.
echo Servidor detenido.
pause
goto menu

:update_mod
cls
echo ===================================================
echo    Actualizando Mod en el Juego
echo ===================================================
echo.

echo Ruta del juego: "%GAME_PATH%"
echo Nombre del mod: "%MOD_NAME%"
echo.

:: Verificar si la ruta del juego existe
if not exist "%GAME_PATH%" (
    echo Error: La ruta del juego no existe: "%GAME_PATH%"
    echo Usa la opción 3 del menú para configurar la ruta correcta.
    pause
    goto menu
)

:: Verificar si la carpeta de mods existe
set "MOD_FOLDER=%GAME_PATH%\mods"
if not exist "!MOD_FOLDER!" (
    echo Error: La carpeta de mods no existe: "!MOD_FOLDER!"
    echo Usa la opción 3 del menú para configurar la ruta correcta.
    pause
    goto menu
)

:: Verificar si la carpeta del mod existe en el proyecto
if not exist "DataExtractorMod" (
    echo Error: La carpeta del mod no existe en el proyecto
    pause
    goto menu
)

:: Crear o actualizar la carpeta del mod en el juego
set "GAME_MOD_PATH=!MOD_FOLDER!\%MOD_NAME%"
echo Copiando archivos a: "!GAME_MOD_PATH!"

:: Crear la carpeta si no existe
if not exist "!GAME_MOD_PATH!" mkdir "!GAME_MOD_PATH!"

:: Copiar todos los archivos del mod
xcopy /E /Y /I "DataExtractorMod\*" "!GAME_MOD_PATH!"

echo.
echo Mod actualizado correctamente.
echo.
pause
goto menu

:set_path
if "%~2"=="" (
    echo Error: Debes especificar una ruta.
    echo Ejemplo: go setpath "D:\SteamLibrary\steamapps\common\The Binding of Isaac Rebirth"
    pause
    goto menu
)

set "GAME_PATH=%~2"
echo Ruta del juego configurada: "%GAME_PATH%"
echo.

:: Guardar la configuración actualizada
call :save_config
echo Configuración guardada.
pause
goto menu

:show_help
cls
echo ===================================================
echo    Ayuda de DataExtractorMod
echo ===================================================
echo.
echo Uso desde línea de comandos:
echo   go                       - Muestra este menú
echo   go server                - Inicia el servidor directamente
echo   go update                - Actualiza el mod en el juego
echo   go setpath "RUTA_JUEGO"  - Configura la ruta del juego
echo   go autosend              - Inicia el envío automático de datos
echo   go help                  - Muestra esta ayuda
echo.
echo Desde el menú interactivo:
echo   [1] Iniciar servidor     - Inicia el servidor para recibir datos
echo   [2] Actualizar mod       - Copia los archivos del mod al juego
echo   [3] Configurar ruta      - Establece la ubicación del juego
echo   [4] Iniciar envío auto.  - Ejecuta el script de envío automático
echo   [5] Mostrar ayuda        - Muestra esta pantalla
echo   [6] Salir                - Cierra el programa
echo.
echo Configuración:
echo   La configuración se guarda en el archivo config.txt
echo   Puedes editar este archivo manualmente o usar la opción 3 del menú
echo.
echo Solución de problemas:
echo   1. Asegúrate de que el mod esté correctamente instalado
echo   2. Verifica que el servidor esté en ejecución
echo   3. Ejecuta el envío automático mientras juegas
echo   4. Revisa los archivos de log para más información
echo.
pause
goto menu

:end
endlocal 