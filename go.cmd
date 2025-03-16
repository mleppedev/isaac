@echo off
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