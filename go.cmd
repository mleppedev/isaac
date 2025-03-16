@echo off
setlocal enabledelayedexpansion

:: Establecer valores predeterminados
set "GAME_PATH=D:\SteamLibrary\steamapps\common\The Binding of Isaac Rebirth"
set "MOD_NAME=DEM"
set "GAME_EXE=isaac-ng.exe"

:: Cargar configuracion desde config.txt si existe
if exist "config.txt" (
    echo Cargando configuracion desde config.txt...
    for /F "usebackq tokens=1,* delims==" %%A in ("config.txt") do (
        if not "%%A"=="" (
            set "line=%%A"
            if not "!line:~0,1!"=="#" (
                if not "%%B"=="" (
                    set "%%A=%%B"
                )
            )
        )
    )
) else (
    echo Archivo config.txt no encontrado. Creando uno con valores predeterminados...
    echo # Configuracion del entorno> config.txt
    echo GAME_PATH=%GAME_PATH%>> config.txt
    echo MOD_NAME=%MOD_NAME%>> config.txt
    echo GAME_EXE=%GAME_EXE%>> config.txt
)

:: Verificar si se paso un parametro
if "%1"=="update" goto update_mod
if "%1"=="help" goto show_help
if "%1"=="setpath" goto set_path
if "%1"=="server" goto start_server
if "%1"=="autosend" goto auto_send
if "%1"=="play" goto play_game

:: Si no hay parametros, mostrar menu
:menu
cls
echo ===================================================
echo    DEM - Menu Principal
echo ===================================================
echo.
echo  [1] Iniciar servidor
echo  [2] Actualizar mod en el juego
echo  [3] Configurar ruta del juego
echo  [4] Iniciar envio automatico de datos
echo  [5] Ejecutar el juego
echo  [6] Mostrar ayuda
echo  [7] Salir
echo.
echo ===================================================
echo  Configuracion actual:
echo  - Ruta del juego: "%GAME_PATH%"
echo  - Nombre del mod: "%MOD_NAME%"
echo  - Ejecutable: "%GAME_EXE%"
echo ===================================================
echo.

set /p opcion="Selecciona una opcion (1-7): "

if "%opcion%"=="1" goto start_server
if "%opcion%"=="2" goto update_mod
if "%opcion%"=="3" goto menu_setpath
if "%opcion%"=="4" goto auto_send
if "%opcion%"=="5" goto play_game
if "%opcion%"=="6" goto show_help
if "%opcion%"=="7" goto end

echo.
echo Opcion no valida. Intentalo de nuevo.
timeout /t 2 >nul
goto menu

:auto_send
cls
echo ===================================================
echo    Iniciar Envio Automatico de Datos
echo ===================================================
echo.
echo Este proceso ejecutara el script de envio de datos
echo cada 30 segundos para asegurar que los datos recopilados
echo por el mod se envien al servidor.
echo.
echo Debes mantener esta ventana abierta mientras juegas.
echo Presiona Ctrl+C para detener el proceso.
echo.
pause
echo.
echo Iniciando envio automatico...
echo.

:: Crear la carpeta del mod si no existe
if not exist "DEM" (
    echo Creando carpeta del mod...
    mkdir DEM
    
    :: Copiar contenido de DataExtractorMod a DEM si existe
    if exist "DataExtractorMod" (
        echo Copiando archivos de DataExtractorMod a DEM...
        xcopy /E /Y /I "DataExtractorMod\*" "DEM\"
        echo Archivos copiados correctamente.
    )
    
    echo Carpeta creada.
    echo.
)

start "Envio Automatico de Datos" /min cmd /c "cd DEM && auto_send.cmd"
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
    echo La ruta no puede estar vacia.
    timeout /t 2 >nul
    goto menu
)

set "GAME_PATH=%nueva_ruta%"
echo.
echo Ruta del juego configurada: "%GAME_PATH%"

:: Guardar la configuracion actualizada
call :save_config_value GAME_PATH "%GAME_PATH%"
echo.
echo Configuracion guardada.
echo.
pause
goto menu

:start_server
echo ===================================================
echo    Iniciando Servidor para DEM
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

:: Verificar si las dependencias estan instaladas
if not exist "venv\Lib\site-packages\pandas" (
    echo Instalando dependencias...
    venv\Scripts\pip install -r requirements.txt
    echo Dependencias instaladas.
    echo.
)

:: Iniciar el servidor
echo Iniciando servidor...
echo El servidor estara disponible en http://localhost:8000
echo Presiona Ctrl+C para detener el servidor
echo.
python app.py

:: Esta parte solo se ejecutara si el servidor se detiene
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
    echo Usa la opcion 3 del menu para configurar la ruta correcta.
    pause
    goto menu
)

:: Verificar si la carpeta de mods existe
set "MOD_FOLDER=%GAME_PATH%\mods"
if not exist "!MOD_FOLDER!" (
    echo Error: La carpeta de mods no existe: "!MOD_FOLDER!"
    echo Usa la opcion 3 del menu para configurar la ruta correcta.
    pause
    goto menu
)

:: Verificar si la carpeta del mod existe en el proyecto
if not exist "DEM" (
    echo La carpeta del mod no existe en el proyecto. Creando...
    mkdir DEM
    
    :: Copiar contenido de DataExtractorMod a DEM si existe
    if exist "DataExtractorMod" (
        echo Copiando archivos de DataExtractorMod a DEM...
        xcopy /E /Y /I "DataExtractorMod\*" "DEM\"
        echo Archivos copiados correctamente.
    )
    
    echo Carpeta creada.
    echo.
)

:: Crear o actualizar la carpeta del mod en el juego
set "GAME_MOD_PATH=!MOD_FOLDER!\%MOD_NAME%"
echo Copiando archivos a: "!GAME_MOD_PATH!"

:: Crear la carpeta si no existe
if not exist "!GAME_MOD_PATH!" mkdir "!GAME_MOD_PATH!"

:: Copiar todos los archivos del mod
xcopy /E /Y /I "DEM\*" "!GAME_MOD_PATH!"

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

:: Guardar la configuracion actualizada
call :save_config_value GAME_PATH "%GAME_PATH%"
echo Configuracion guardada.
pause
goto menu

:play_game
cls
echo ===================================================
echo    Ejecutando The Binding of Isaac Rebirth
echo ===================================================
echo.

echo Ruta del juego: "%GAME_PATH%"
echo Ejecutable: "%GAME_EXE%"
echo.

:: Verificar si la ruta del juego existe
if not exist "%GAME_PATH%" (
    echo Error: La ruta del juego no existe: "%GAME_PATH%"
    echo Usa la opcion 3 del menu para configurar la ruta correcta.
    pause
    goto menu
)

:: Verificar si el ejecutable existe
set "GAME_EXECUTABLE=%GAME_PATH%\%GAME_EXE%"
if not exist "!GAME_EXECUTABLE!" (
    echo Error: El ejecutable del juego no existe: "!GAME_EXECUTABLE!"
    echo Verifica que el nombre del ejecutable sea correcto.
    echo.
    echo Ingresa el nombre correcto del ejecutable:
    set /p GAME_EXE="Nombre del ejecutable: "
    
    :: Guardar la configuracion actualizada
    call :save_config_value GAME_EXE "%GAME_EXE%"
    
    :: Verificar nuevamente
    set "GAME_EXECUTABLE=%GAME_PATH%\%GAME_EXE%"
    if not exist "!GAME_EXECUTABLE!" (
        echo Error: El ejecutable del juego sigue sin encontrarse.
        pause
        goto menu
    )
)

:: Ejecutar el juego
echo Iniciando el juego...
start "" "!GAME_EXECUTABLE!"
echo.
echo El juego se ha iniciado.
echo.
pause
goto menu

:show_help
cls
echo ===================================================
echo    Ayuda de DEM
echo ===================================================
echo.
echo Uso desde linea de comandos:
echo   go                       - Muestra este menu
echo   go server                - Inicia el servidor directamente
echo   go update                - Actualiza el mod en el juego
echo   go setpath "RUTA_JUEGO"  - Configura la ruta del juego
echo   go play                  - Ejecuta el juego directamente
echo   go autosend              - Inicia el envio automatico de datos
echo   go help                  - Muestra esta ayuda
echo.
echo ===================================================
echo.
pause
goto menu

:end
endlocal 
exit /b

:: Funcion para guardar un valor específico en config.txt
:save_config_value
set "key=%~1"
set "value=%~2"

:: Crear un archivo temporal
type nul > config_temp.txt

:: Copiar el contenido actual de config.txt al temporal, reemplazando la línea del valor
for /F "usebackq tokens=1,* delims==" %%A in ("config.txt") do (
    if "%%A"=="%key%" (
        echo %key%=%value%>> config_temp.txt
    ) else (
        if "%%A"=="" (
            echo.>> config_temp.txt
        ) else (
            echo %%A=%%B>> config_temp.txt
        )
    )
)

:: Reemplazar el archivo original con el temporal
move /y config_temp.txt config.txt >nul
exit /b 