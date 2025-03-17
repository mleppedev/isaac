# Data Event Manager (DEM) para The Binding of Isaac

## Visión General
Este mod recopila datos detallados del juego para entrenar modelos de Inteligencia Artificial que puedan aprender a jugar The Binding of Isaac. Funciona como un sistema completo que incluye recolección de datos, procesamiento y visualización a través de un servidor web dedicado.

### Características Avanzadas para ML/IA
- **Recopilación de Datos por Frame**: Captura el estado completo del juego 60 veces por segundo
- **Mapeo de Habitaciones**: Documentación detallada de la estructura de cada habitación, obstáculos y áreas transitables
- **Seguimiento de Entidades**: Seguimiento preciso de la posición, velocidad y estado de todas las entidades
- **Entrada del Usuario**: Captura todas las acciones del jugador para entrenar el modelo de IA
- **Vectores de Movimiento**: Cálculos de física para determinar trayectorias y patrones de movimiento
- **Optimización de Datos**: Eliminación de datos duplicados y compresión para reducir el tamaño del conjunto de datos
- **Automatización Completa**: Sistema integrado que maneja la recolección, extracción y procesamiento de datos

## Componentes del Sistema

El sistema DEM consta de tres componentes principales:

1. **Mod Lua (carpeta DEM)**: 
   - Recopila datos durante el juego
   - Optimiza y comprime la información en tiempo real
   - Guarda periódicamente los datos usando la API de Isaac.SaveModData

2. **Servidor Web (carpeta server)**:
   - Visualiza los datos recopilados en tiempo real
   - Proporciona análisis estadísticos y representaciones gráficas
   - Permite la exploración interactiva de los datos de juego
   - Implementa comunicación bidireccional con el mod mediante websockets

3. **Script de Control (go.cmd)**:
   - Facilita la gestión del sistema completo
   - Proporciona un menú interactivo en español
   - Automatiza tareas comunes como actualizar el mod y extraer datos

## Estructura de Datos
Los datos se recopilan en formato JSON estructurado para facilitar su procesamiento posterior. La estructura básica es:

```json
{
  "metadata": {
    "version": "2.0",
    "timestamp": 12345,
    "event_count": 300,
    "file_id": 1,
    "is_ml_data": true
  },
  "stats": {
    "total_events_recorded": 15000,
    "total_events_saved": 14700,
    "largest_event_size": 1240,
    "save_operations": 49
  },
  "events": [
    {
      "event_type": "frame_state",
      "timestamp": 12345,
      "event_id": "dem_frame_state_12345_1234",
      "data": {
        "frame_count": 12345,
        "room_id": 123,
        "player": {
          "position": {"x": 320, "y": 280},
          "velocity": {"x": 0.5, "y": 0},
          "health": {"hearts": 6, "soul_hearts": 0},
          "stats": {"speed": 1.0, "damage": 3.5}
        },
        "entities": [
          {
            "type": 10,
            "position": {"x": 400, "y": 300},
            "velocity": {"x": -0.3, "y": 0.2},
            "is_enemy": true,
            "hp": 15
          }
        ],
        "inputs": {
          "LEFT": 0,
          "RIGHT": 1.0,
          "SHOOT_UP": 1.0
        }
      }
    }
  ]
}
```

## Características del Servidor

El servidor web implementa una serie de funcionalidades esenciales para el análisis de datos:

- **Visualización en Tiempo Real**: Muestra estadísticas actualizadas mientras juegas
- **Dashboard Interactivo**: Interfaz web para explorar los datos recopilados
- **Gráficos y Visualizaciones**:
  - Mapas de calor de posiciones de jugador y enemigos
  - Gráficos de daño y tasa de supervivencia
  - Análisis temporal de eventos
  - Patrones de movimiento del jugador
- **Análisis Estadístico**: Procesamiento automático para identificar patrones
- **API REST**: Permite acceder a los datos desde otras aplicaciones
- **Conexión WebSocket**: Comunicación bidireccional con el mod durante el juego
- **Preprocesamiento para ML**: Preparación de datos para entrenamiento de modelos

## Machine Learning con DEM

El sistema está diseñado específicamente para facilitar el entrenamiento de modelos de ML:

- **Preparación de Datasets**: Scripts para convertir los datos en formatos compatibles con frameworks de ML
- **Vectorización de Estados**: Conversión de estados del juego en representaciones vectoriales
- **Secuencias Temporales**: Captura de secuencias de eventos para modelos recurrentes
- **Características para Entrenamiento**:
  - Estados completos del juego por frame
  - Acciones del jugador etiquetadas
  - Contexto de decisiones (proximidad de enemigos, objetos, etc.)
  - Resultados de acciones (daño, recolección de ítems, etc.)

### Modelos de IA Compatibles

El conjunto de datos generado puede utilizarse para entrenar varios tipos de modelos de IA:

- **Redes Neuronales Convolucionales (CNN)**: Para procesamiento de patrones espaciales
- **Redes Recurrentes (LSTM/GRU)**: Para aprender secuencias de acción
- **Aprendizaje por Refuerzo (RL)**: Para optimizar estrategias de juego
- **Modelos de Atención**: Para focalizar en elementos importantes en el juego
- **Aprendizaje por Imitación**: Para replicar el comportamiento del jugador humano

## Instalación y Uso

### Requisitos Previos
- The Binding of Isaac: Rebirth con la expansión Repentance+
- Python 3.8 o superior (para el servidor y scripts)
- Paquetes Python (instalados automáticamente): Flask, Pandas, Matplotlib, NumPy, SciKit-Learn, Flask-SocketIO

### Instalación Rápida

1. Clona o descarga este repositorio
2. Ejecuta `go.cmd` desde la línea de comandos
3. Selecciona la opción 1 para copiar el mod al directorio del juego
4. Activa el mod en el menú de mods del juego

### Uso del Sistema Completo

Para utilizar todas las funcionalidades del sistema:

1. Ejecuta `go.cmd` sin argumentos para ver el menú interactivo
2. Selecciona la opción adecuada según tus necesidades:
   - **Opción 1**: Copiar archivos del mod al directorio del juego
   - **Opción 2**: Iniciar el servidor web para visualización
   - **Opción 3**: Lanzar el juego
   - **Opción 4**: Hacer todo lo anterior en un solo paso
   - **Opción 5**: Salir

### Archivo de Configuración

El sistema utiliza `config.txt` para configurar las rutas y parámetros:

```
# Configuracion del entorno
GAME_PATH=D:\SteamLibrary\steamapps\common\The Binding of Isaac Rebirth
MOD_NAME=DEM
GAME_EXE=isaac-ng.exe
```

## Estructura de Archivos

```
/
├── config.txt           # Configuración del sistema
├── go.cmd               # Script principal de control
├── DEM/                 # Archivos del mod
│   ├── main.lua         # Punto de entrada del mod
│   ├── data_manager.lua # Sistema de gestión de datos
│   ├── metadata.xml     # Metadatos del mod
│   ├── json.lua         # Biblioteca para manejo de JSON
│   └── README.md        # Documentación del mod
└── server/              # Servidor web y herramientas
    ├── app.py           # Aplicación principal del servidor
    ├── extract_data.py  # Script de extracción de datos
    ├── process_data.py  # Procesamiento de datos
    ├── train_model.py   # Entrenamiento de modelos ML
    ├── find_data.py     # Herramienta de búsqueda de datos
    ├── requirements.txt # Dependencias Python
    ├── static/          # Archivos estáticos del servidor
    ├── templates/       # Plantillas HTML
    ├── data/            # Datos procesados
    ├── logs/            # Archivos de registro
    ├── received_data/   # Datos recibidos sin procesar
    └── processed_data/  # Datos procesados para ML
```

## Flujo de Trabajo para ML

Para utilizar los datos en proyectos de Machine Learning:

1. **Recolección de Datos**: Juega al juego con el mod activado
2. **Extracción**: El servidor extrae y procesa automáticamente los datos
3. **Preprocesamiento**: Los scripts en la carpeta `server` preparan los datos para ML
4. **Entrenamiento**: Utiliza `train_model.py` para entrenar modelos básicos o exporta los datos para frameworks externos

### Scripts de ML Disponibles

- **process_data.py**: Preprocesa los datos para entrenamiento
- **train_model.py**: Implementa modelos básicos de ML
- **find_data.py**: Busca patrones específicos en los datos

## Rendimiento y Limitaciones

El mod está optimizado para tener un impacto mínimo en el rendimiento del juego:
- Procesamiento asíncrono de datos
- Eliminación inteligente de datos duplicados
- Ajuste dinámico del tamaño del buffer basado en rendimiento
- Monitorización de uso de memoria

### Limitaciones Importantes

1. **Un solo evento a la vez**:
   - La API SaveModData solo permite guardar un archivo único por mod
   - Cada nuevo evento sobrescribe cualquier evento anterior que no se haya extraído
   - Por eso es importante ejecutar el servidor para extraer datos continuamente

2. **Ubicación del archivo de datos**:
   - Isaac guarda los datos en `Documents\My Games\Binding of Isaac Repentance+\` 
   - No se puede cambiar esta ubicación, es fijada por el juego

## Acceso al Servidor Web

Una vez iniciado el servidor (opción 2 en go.cmd), puedes acceder a la interfaz web:

- **URL**: http://localhost:5000
- **Dashboard**: http://localhost:5000/dashboard
- **API**: http://localhost:5000/api/events

## Licencia
Este proyecto está licenciado bajo MIT License.

## Contacto
Para preguntas o sugerencias, abre un issue en el repositorio.

# Mejoras en la Captura de Datos - Mod DEM

Este proyecto incluye varias mejoras significativas para aumentar la cantidad y calidad de datos que captura el mod DEM (Data Extraction Mod) para The Binding of Isaac.

## Características Principales

- **Mayor frecuencia de muestreo**: Reducción de intervalos de captura para obtener datos más precisos
- **Captura adaptativa**: Aumenta la frecuencia durante combates y encuentros con jefes
- **Captura de eventos específicos**: Registra eventos clave independientemente del intervalo regular
- **Enriquecimiento de datos**: Añade metadatos, coordenadas de cuadrícula y clasificación mejorada
- **Gestión mejorada de datos**: Archivos separados por nivel y mejor organización

## Archivos Modificados

- `server/app.py`: Intervalos reducidos, nuevas opciones de configuración
- `config.json`: Configuración global centralizada para el servidor
- `extract_data.py`: Script mejorado con procesamiento y captura más detallada
- `mod_config.lua`: Configuración del mod para el juego (copiar al directorio del mod)

## Nuevas Capacidades de Captura

### Datos del Jugador
- Posición y velocidad en cada captura
- Datos completos de salud y estadísticas
- Seguimiento de todos los coleccionables, trinkets, cartas y píldoras
- Registro de familiares y su comportamiento

### Datos de Enemigos
- Posiciones y movimientos
- Salud y cambios en tiempo real
- Patrones de ataque y objetivos
- Seguimiento de proyectiles enemigos

### Datos de Combate
- Eventos de daño (dado y recibido)
- Registro de proyectiles, lágrimas, láseres y explosiones
- Información sobre el combate con detalles del contexto

### Sala y Nivel
- Disposición completa de salas
- Tipos de habitaciones y contenido
- Eventos de transición entre salas
- Datos sobre trampas y secretos

### Eventos Específicos
- Inicio y fin de partida
- Inicio y fin de nivel
- Encuentros con jefes
- Recolección de objetos
- Uso de objetos activos y consumibles

## Configuración

Puedes personalizar el comportamiento modificando:

1. `config.json` - Para el servidor web
2. `mod_config.lua` - Para el mod en el juego (requiere reiniciar el juego)

## Instalación

1. Copia todos los archivos a la carpeta del servidor
2. Copia `mod_config.lua` a la carpeta del mod en el juego
3. Reinicia tanto el servidor como el juego

## Recomendaciones

Para obtener la captura de datos óptima:

- Mantén activada la opción `events.key_events`
- Reduce `capture_interval` si tu sistema tiene buen rendimiento
- Activa `advanced.track_combat_metrics` para análisis detallado
- Usa `file.split_files_by_level = true` para mejor organización 