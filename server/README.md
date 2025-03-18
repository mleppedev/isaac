# Servidor para DEM

Este es un servidor desarrollado en Flask para interactuar con el mod DEM para The Binding of Isaac. Proporciona funcionalidades para:
- Recibir y almacenar datos enviados por el mod
- Controlar el juego mediante comandos
- Analizar el juego usando visión por computadora y reinforcement learning

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Dependencias principales:
  - Flask
  - pandas
  - matplotlib
  - numpy
  - scikit-learn
- Para el módulo de visión por computadora:
  - OpenCV
  - PyTorch
  - PyWin32
  - Pillow

## Instalación

1. Clona este repositorio o descarga los archivos
2. Crea un entorno virtual (recomendado):
   ```
   python -m venv venv
   ```
3. Activa el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
5. Copia `.env.example` a `.env` y configura las variables según tus necesidades:
   ```
   cp .env.example .env
   ```

## Modos de Funcionamiento

El servidor puede funcionar con dos versiones del mod:

### 1. DEM (Recolección de datos)
- Recopila datos granulares del juego para entrenamiento
- Registra posiciones, estados, eventos y acciones del usuario
- Genera datasets estructurados para análisis y machine learning

### 2. DEM_CV (Control por visión por computadora)
- Utiliza visión por computadora para detectar elementos del juego
- Implementa un agente de reinforcement learning para tomar decisiones
- Envía comandos al juego basados en lo que "ve" en pantalla

## Uso

1. Selecciona la versión del mod a utilizar mediante el script `go.cmd`:
   ```
   go.cmd
   ```
   Y selecciona la opción 1 para elegir entre DEM o DEM_CV.

2. Inicia el servidor:
   ```
   python app.py
   ```
3. El servidor estará disponible en `http://localhost:5000`

## Endpoints API

- `GET /api/health` - Comprueba si el servidor está funcionando
- `POST /api/data` - Recibe datos del mod
- `POST /api/control` - Envía comandos de control al juego
- `GET /api/vision` - Obtiene el estado del sistema de visión por computadora
- `POST /api/vision` - Controla el sistema de visión por computadora

## Interfaz Web

El servidor incluye una interfaz web para:

1. **Página principal**: http://localhost:5000/
   - Muestra información general sobre el servidor

2. **Control del Personaje**: http://localhost:5000/control
   - Panel de control para enviar comandos al juego
   - Control del personaje mediante botones interactivos
   - Sistema de visión por computadora con:
     - Botones para iniciar/detener el sistema
     - Ajustes de tasa de exploración
     - Captura de templates para entrenamiento

3. **Datos extraídos**: http://localhost:5000/view/raw
   - Muestra los datos extraídos del juego en formato de tarjetas

4. **Datos procesados**: http://localhost:5000/view/processed
   - Visualizaciones y procesamiento de datos recopilados

## Sistema de Visión por Computadora

El módulo de visión por computadora (`vision_module`) está diseñado para:

1. **Capturar la pantalla del juego** en tiempo real
2. **Detectar elementos** como jugador, enemigos, items y puertas
3. **Tomar decisiones inteligentes** mediante un agente de RL
4. **Enviar comandos al mod DEM_CV** para controlar el juego

Para usar este sistema:
1. Asegúrate de tener instalado el mod DEM_CV (usando `go.cmd`)
2. Ve a la interfaz web en http://localhost:5000/control
3. En la sección "Sistema de Visión por Computadora", haz clic en "Iniciar Sistema"
4. El sistema comenzará a analizar la pantalla y controlar el juego

Para entrenar el sistema mejorando la detección:
1. Usa la función "Capturar" para guardar templates de los diferentes elementos del juego
2. Estos templates se utilizarán para mejorar la precisión de la detección

## Estructura de datos

El servidor espera recibir datos en formato JSON. Un ejemplo de la estructura esperada:

```json
{
  "room_id": 12345,
  "health": 6,
  "position": {
    "x": 123.45,
    "y": 67.89
  },
  "enemies": 5,
  "timestamp": "2023-03-16T12:34:56"
}
```

## Almacenamiento

- **Datos recibidos**: Se almacenan en la carpeta `received_data` en archivos JSON.
- **Datos procesados**: Se almacenan en la carpeta `processed_data`.
- **Templates**: Los templates del sistema de visión se guardan en `vision_module/templates`.

## Solución de problemas

### Generales
- Si el servidor no inicia, verifica que el puerto no esté en uso
- Revisa los logs en `server.log` para más información sobre errores
- Para instalar dependencias faltantes: `pip install -r requirements.txt`

### Sistema de Visión
- Si el botón "Iniciar Sistema" no responde, verifica las dependencias con:
  ```
  pip install opencv-python pywin32 torch torchvision
  ```
- Si hay errores de importación, verifica la estructura de carpetas (el módulo `vision_module` debe estar en la raíz del proyecto)
- Para problemas con la captura de pantalla, asegúrate que el juego esté visible
- Inicia el sistema directamente con `python -m vision_module.main` para ver errores detallados 