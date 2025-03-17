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
if "%1"=="test" goto test_data_sending
if "%1"=="extract" goto extract_data

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
echo  [7] Probar envio de datos
echo  [8] Extraer datos locales
echo  [9] Salir
echo.
echo ===================================================
echo  Configuracion actual:
echo  - Ruta del juego: "%GAME_PATH%"
echo  - Nombre del mod: "%MOD_NAME%"
echo  - Ejecutable: "%GAME_EXE%"
echo ===================================================
echo.

set /p opcion="Selecciona una opcion (1-9): "

if "%opcion%"=="1" goto start_server
if "%opcion%"=="2" goto update_mod
if "%opcion%"=="3" goto menu_setpath
if "%opcion%"=="4" goto auto_send
if "%opcion%"=="5" goto play_game
if "%opcion%"=="6" goto show_help
if "%opcion%"=="7" goto test_data_sending
if "%opcion%"=="8" goto extract_data
if "%opcion%"=="9" goto end

echo.
echo Opcion no valida. Intentalo de nuevo.
timeout /t 2 >nul
goto menu

:auto_send
cls
echo ===================================================
echo    Monitoreo Automático de Datos
echo ===================================================
echo.
echo Este proceso ejecutará el extractor de datos en segundo plano,
echo vigilando periódicamente si hay nuevos archivos JSON generados 
echo por el mod mientras juegas.
echo.
echo Debes mantener esta ventana abierta mientras juegas.
echo Presiona Ctrl+C para detener el proceso.
echo.
pause
echo.
echo Iniciando monitoreo automático...
echo.

:: Crear carpeta server si no existe
if not exist "server" (
    echo Creando carpeta server...
    mkdir server
    echo Carpeta creada.
    echo.
)

:: Verificar si existe auto_extract.cmd
if not exist "server\auto_extract.cmd" (
    echo Creando script de extracción automática...
    (
        echo @echo off
        echo title DEM - Extracción Automática de Datos
        echo echo Iniciando monitoreo automático de datos...
        echo echo Este proceso debe mantenerse abierto mientras juegas.
        echo echo ===================================================
        echo :loop
        echo echo [%%date%% %%time%%] Comprobando nuevos datos...
        echo python extract_data.py --keep-files
        echo timeout /t 120 /nobreak ^> nul
        echo goto loop
    ) > "server\auto_extract.cmd"
    echo Script creado.
    echo.
)

start "Monitoreo Automático de Datos" /min cmd /c "cd server && auto_extract.cmd"
echo Proceso iniciado en segundo plano.
echo.
pause
goto menu

:test_data_sending
cls
echo ===================================================
echo    Prueba del Sistema de Datos
echo ===================================================
echo.
echo Esta opción crea datos de prueba para verificar que el
echo sistema está funcionando correctamente.
echo.
echo 1. Crear datos de prueba
echo 2. Verificar logs de extracción
echo 3. Limpiar carpeta de datos
echo 4. Volver al menú principal
echo.
echo ===================================================
echo.

set /p test_option="Selecciona una opción (1-4): "

if "%test_option%"=="1" goto create_test_data
if "%test_option%"=="2" goto view_logs
if "%test_option%"=="3" goto clean_data_dir
if "%test_option%"=="4" goto menu

echo.
echo Opción no válida. Inténtalo de nuevo.
timeout /t 2 >nul
goto test_data_sending

:create_test_data
echo.
echo Creando datos de prueba...

:: Verificar si existe la carpeta de datos
set "DATA_DIR=%USERPROFILE%\Documents\My Games\Binding of Isaac Repentance\Mods\DEM\DEM_Data"
if not exist "%DATA_DIR%" (
    echo Creando carpeta de datos...
    mkdir "%DATA_DIR%"
    echo Carpeta creada.
)

:: Crear archivo de datos de prueba con timestamp actual
set "timestamp=%time:~0,2%%time:~3,2%%time:~6,2%"
set "random_num=%random%"
set "test_file=%DATA_DIR%\dem_test_event_%timestamp%_%random_num%.json"

:: Crear un JSON de prueba
(
    echo {
    echo   "event_type": "test_event",
    echo   "timestamp": %timestamp%,
    echo   "data": {
    echo     "test": true,
    echo     "message": "Datos de prueba generados automáticamente"
    echo   },
    echo   "game_data": {
    echo     "seed": 12345,
    echo     "level": 1,
    echo     "room_id": 1001,
    echo     "room_type": 1,
    echo     "frame_count": 5000
    echo   }
    echo }
) > "%test_file%"

echo Datos de prueba creados en:
echo %test_file%
echo.
echo ¿Deseas ejecutar el extractor de datos ahora? (S/N)
set /p extract_now="Opción: "

if /i "%extract_now%"=="S" (
    echo.
    echo Ejecutando extractor de datos...
    cd server
    python extract_data.py
    cd ..
    echo.
    echo Proceso finalizado.
) else (
    echo.
    echo Puedes procesar los datos más tarde usando la opción "Extraer datos locales".
)

echo.
pause
goto test_data_sending

:view_logs
echo.
echo Mostrando últimas líneas del log de extracción...
echo.
if exist "server\extract_data.log" (
    type "server\extract_data.log" | findstr /n "." | findstr /r "^[0-9][0-9]*:" | sort /r | findstr /r "^[1-9][0-9]\?:" | sort | more
) else (
    echo No se encontró archivo de log.
    echo Ejecuta la extracción de datos primero.
)
echo.
pause
goto test_data_sending

:clean_data_dir
echo.
echo Limpiando carpeta de datos...
set "DATA_DIR=%USERPROFILE%\Documents\My Games\Binding of Isaac Repentance\Mods\DEM\DEM_Data"

echo.
echo ADVERTENCIA: Esto eliminará todos los archivos JSON en:
echo %DATA_DIR%
echo.
echo ¿Estás seguro de que deseas continuar? (S/N)
set /p confirm_clean="Opción: "

if /i "%confirm_clean%"=="S" (
    echo.
    echo Eliminando archivos...
    if exist "%DATA_DIR%\*.json" (
        del /q "%DATA_DIR%\*.json"
        echo Archivos eliminados.
    ) else (
        echo No se encontraron archivos para eliminar.
    )
) else (
    echo.
    echo Operación cancelada.
)

echo.
pause
goto test_data_sending

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

:: Crear archivo de metadatos del mod si no existe
if not exist "!GAME_MOD_PATH!\metadata.xml" (
    echo Creando archivo metadata.xml...
    (
        echo ^<metadata^>
        echo     ^<name^>Data Event Manager^</name^>
        echo     ^<directory^>%MOD_NAME%^</directory^>
        echo     ^<id^>dem^</id^>
        echo     ^<description^>Recolector simplificado de datos de eventos del juego. Solo genera archivos JSON locales sin envío externo.^</description^>
        echo     ^<version^>1.1^</version^>
        echo     ^<visibility^>Private^</visibility^>
        echo     ^<tag^>Tool^</tag^>
        echo ^</metadata^>
    ) > "!GAME_MOD_PATH!\metadata.xml"
    echo Archivo metadata.xml creado.
)

:: Crear carpeta de datos del mod si no existe
if not exist "!GAME_MOD_PATH!\DEM_Data" (
    echo Creando carpeta de datos...
    mkdir "!GAME_MOD_PATH!\DEM_Data"
    echo Carpeta de datos creada.
)

:: Verificar si el main.lua ya existe en el directorio del proyecto
if not exist "DEM\main.lua" (
    echo AVISO: No se encontró main.lua en el directorio del proyecto.
    echo Se necesita este archivo para que el mod funcione.
    echo.
    echo Asegúrate de crear un archivo main.lua que cargue el data_manager.
    echo Ejemplo: local DataManager = require("data_manager")
    echo.
)

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
echo   go server                - Inicia el servidor (si está configurado)
echo   go update                - Actualiza el mod en el juego
echo   go setpath "RUTA_JUEGO"  - Configura la ruta del juego
echo   go play                  - Ejecuta el juego directamente
echo   go autosend              - Inicia el monitoreo automático
echo   go test                  - Prueba el sistema de datos
echo   go extract               - Extrae datos locales
echo   go help                  - Muestra esta ayuda
echo.
echo ===================================================
echo.
echo DESCRIPCIÓN DEL SISTEMA:
echo.
echo DEM (Data Event Manager) es un sistema simplificado para recopilar
echo datos de eventos del juego The Binding of Isaac: Rebirth.
echo.
echo El sistema utiliza un enfoque en dos pasos:
echo.
echo 1. Mod Lua para el juego:
echo    - Registra eventos durante el juego
echo    - Genera archivos JSON individuales por cada evento
echo    - Guarda los archivos en una carpeta local (DEM_Data)
echo.
echo 2. Extractor de datos:
echo    - Lee los archivos JSON generados
echo    - Los consolida en una base de datos JSON
echo    - Facilita el análisis posterior
echo.
echo Los datos se guardan en la siguiente ubicación:
echo %USERPROFILE%\Documents\My Games\Binding of Isaac Repentance\Mods\DEM\DEM_Data
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

:extract_data
cls
echo ===================================================
echo    Extraccion de Datos Locales
echo ===================================================
echo.
echo Esta opcion extrae los datos generados localmente por el mod
echo y los consolida en una base de datos local para su analisis.
echo.
echo 1. Extraer datos ahora
echo 2. Configurar directorio de datos
echo 3. Ver estado de la base de datos
echo 4. Volver al menu principal
echo.
echo ===================================================
echo.

set /p extract_option="Selecciona una opcion (1-4): "

if "%extract_option%"=="1" goto run_extraction
if "%extract_option%"=="2" goto config_data_dir
if "%extract_option%"=="3" goto view_db_status
if "%extract_option%"=="4" goto menu

echo.
echo Opcion no valida. Intentalo de nuevo.
timeout /t 2 >nul
goto extract_data

:run_extraction
echo.
echo Extrayendo datos locales...

:: Verificar si existe el script de extracción
if not exist "server\extract_data.py" (
    echo Error: No se encuentra el script de extraccion.
    echo Asegúrate de que el archivo server\extract_data.py existe.
    pause
    goto extract_data
)

:: Ejecutar script de extracción
cd server
python extract_data.py
cd ..

echo.
echo Proceso de extraccion finalizado.
pause
goto extract_data

:config_data_dir
echo.
echo Configurando directorio de datos...
echo.
echo El directorio predeterminado es:
echo %USERPROFILE%\Documents\My Games\Binding of Isaac Repentance\Mods\DEM\DEM_Data
echo.
echo ¿Deseas especificar un directorio diferente? (S/N)
set /p custom_dir="Opcion: "

if /i "%custom_dir%"=="S" (
    echo.
    echo Ingresa la ruta completa del directorio de datos:
    set /p data_dir="Ruta: "
    
    :: Verificar si la ruta existe
    if not exist "!data_dir!" (
        echo.
        echo El directorio no existe. ¿Deseas crearlo? (S/N)
        set /p create_dir="Opcion: "
        
        if /i "!create_dir!"=="S" (
            mkdir "!data_dir!"
            echo Directorio creado.
        ) else (
            echo Operacion cancelada.
            pause
            goto extract_data
        )
    )
    
    :: Crear/actualizar archivo de configuración para el extractor
    echo # Configuracion del extractor de datos> server\extract_config.txt
    echo DATA_DIR=!data_dir!>> server\extract_config.txt
    
    echo.
    echo Configuracion guardada.
) else (
    echo.
    echo Se usara el directorio predeterminado.
)

echo.
pause
goto extract_data

:view_db_status
echo.
echo Estado de la base de datos...

:: Verificar si existe la base de datos
if exist "server\dem_database.json" (
    echo.
    echo Información de la base de datos:
    
    :: Contar número de eventos (aproximado)
    for /f "tokens=1,* delims=:" %%a in ('findstr /n /c:"\"event_type\"" "server\dem_database.json"') do set count=%%a
    echo - Eventos aproximados: !count!
    
    :: Obtener fecha de última modificación
    for /f "tokens=1,2 delims= " %%a in ('dir /T:W "server\dem_database.json" ^| findstr dem_database') do set modified=%%a %%b
    echo - Última actualización: !modified!
    
    :: Obtener tamaño
    for /f "tokens=3" %%a in ('dir "server\dem_database.json" ^| findstr dem_database') do set size=%%a
    echo - Tamaño del archivo: !size! bytes
) else (
    echo.
    echo No se encontró la base de datos.
    echo Ejecuta la extracción de datos primero.
)

echo.
pause
goto extract_data 