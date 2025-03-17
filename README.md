# Data Event Manager (DEM) para The Binding of Isaac

## Visión General
Este mod recopila datos detallados del juego para entrenar modelos de Inteligencia Artificial que puedan aprender a jugar The Binding of Isaac.

### Características Avanzadas para ML/IA
- **Recopilación de Datos por Frame**: Captura el estado completo del juego 60 veces por segundo
- **Mapeo de Habitaciones**: Documentación detallada de la estructura de cada habitación, obstáculos y áreas transitables
- **Seguimiento de Entidades**: Seguimiento preciso de la posición, velocidad y estado de todas las entidades
- **Entrada del Usuario**: Captura todas las acciones del jugador para entrenar el modelo de IA
- **Vectores de Movimiento**: Cálculos de física para determinar trayectorias y patrones de movimiento
- **Optimización de Datos**: Eliminación de datos duplicados y compresión para reducir el tamaño del conjunto de datos

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

## Tipos de Eventos
El mod registra varios tipos de eventos, incluyendo:

1. **frame_state**: Estado completo del juego capturado cada frame
2. **room_detailed**: Información detallada sobre una habitación al entrar
3. **player_damage_detailed**: Información sobre daño recibido con contexto completo
4. **enemy_killed_detailed**: Datos detallados sobre la muerte de un enemigo
5. **item_collected_detailed**: Información sobre ítems recogidos y sus efectos
6. **input_change**: Cambios en la entrada del usuario para aprendizaje secuencial
7. **performance_stats**: Estadísticas de rendimiento del mod para optimizaciones

## Entrenamiento de IA
El conjunto de datos generado puede utilizarse para entrenar varios tipos de modelos de IA:

- **Redes neuronales convolucionales (CNN)**: Para procesamiento de patrones espaciales
- **Redes recurrentes (LSTM/GRU)**: Para aprender secuencias de acción
- **Aprendizaje por refuerzo**: Para optimizar estrategias de juego
- **Modelos de atención**: Para focalizar en elementos importantes en el juego

## Instalación
1. Descarga el mod
2. Coloca la carpeta DEM en `...\Documents\My Games\Binding of Isaac Repentance+\mods\`
3. Activa el mod en el menú de mods del juego

## Uso
El mod funciona automáticamente en segundo plano, recopilando datos mientras juegas. Los datos se guardan periódicamente en:
```
[Carpeta de instalación del juego]/data/dem/save1.dat
```

## Scripts de Utilidad
- **go.cmd**: Script de inicio rápido que controla el juego y el servidor web
- **get_dem_data.py**: Extrae datos del juego para procesamiento
- **server/**: Servidor web para visualizar los datos recopilados

## Visualización y Análisis
El servidor web incluido proporciona visualizaciones básicas de los datos recopilados:
- Distribución de tipos de eventos
- Mapas de calor de posiciones de jugador y enemigos
- Gráficos de daño y tasa de supervivencia
- Secuencias de entrada del usuario

## Configuración
Puedes modificar varios parámetros en `data_manager.lua`:
- `BUFFER_SIZE`: Número de eventos antes de guardar
- `DATA_COMPRESSION`: Activar/desactivar compresión
- `FRAME_LIMIT`: Tiempo máximo entre guardados
- `FILE_ROTATION`: Activar rotación de archivos

## Rendimiento
El mod está optimizado para tener un impacto mínimo en el rendimiento del juego:
- Procesamiento asíncrono de datos
- Eliminación inteligente de datos duplicados
- Ajuste dinámico del tamaño del buffer basado en rendimiento
- Monitorización de uso de memoria

## Licencia
Este proyecto está licenciado bajo MIT License.

## Contacto
Para preguntas o sugerencias, abre un issue en el repositorio.

## Descripción

DEM (Data Event Manager) es un sistema simplificado para recolectar y analizar eventos del juego The Binding of Isaac: Rebirth. El sistema recopila diversos eventos durante el juego (como recoger ítems, recibir daño o derrotar enemigos) y los almacena para su posterior análisis.

## Características Principales

- **Recolección automática de eventos:** Registra eventos del juego sin intervención del usuario
- **Almacenamiento local:** Guarda los datos usando la API oficial de Isaac.SaveModData
- **Scripts de extracción:** Herramientas para procesar y analizar los datos recolectados
- **Interfaz simple:** Script `go.cmd` para gestionar todas las funciones del sistema

## Estructura del Sistema

El sistema consta de tres componentes principales:

1. **Módulo Lua (DEM):** Mod para el juego que recolecta eventos y los guarda usando SaveModData
2. **Scripts Python:** Herramientas para extraer y procesar los datos guardados por el mod
3. **Script de Control:** Archivo `go.cmd` que facilita la gestión del sistema

## Instalación

1. **Instalar el mod:**
   - Ejecuta `go update` para copiar los archivos al directorio de mods del juego

2. **Configurar Python (opcional):**
   - Si quieres usar las herramientas de extracción, asegúrate de tener Python instalado
   - El sistema configurará automáticamente un entorno virtual la primera vez que se ejecuten los scripts

3. **Configurar la ruta del juego:**
   - Si la ruta por defecto no es correcta, usa `go setpath "RUTA_DEL_JUEGO"`

## Uso

### Mediante el menú interactivo

Ejecuta `go` sin argumentos para acceder al menú interactivo con las siguientes opciones:

1. **Iniciar servidor** - Inicia el servidor local (si está configurado)
2. **Actualizar mod** - Copia los archivos del mod al directorio del juego
3. **Configurar ruta** - Establece la ubicación del juego
4. **Monitoreo automático** - Extrae datos periódicamente mientras juegas
5. **Ejecutar juego** - Inicia The Binding of Isaac: Rebirth
6. **Mostrar ayuda** - Muestra información detallada sobre el sistema
7. **Probar sistema** - Prueba el funcionamiento del sistema de datos
8. **Extraer datos** - Extrae y procesa los datos almacenados localmente
9. **Salir** - Cierra el programa

### Mediante línea de comandos

También puedes usar comandos directos:
- `go update` - Actualiza el mod
- `go play` - Inicia el juego
- `go extract` - Extrae los datos guardados
- `go test` - Prueba el sistema
- `go help` - Muestra la ayuda

## Datos Almacenados

### Ubicación de los Datos

El mod guarda todos los eventos en un único archivo:

```
%USERPROFILE%\Documents\My Games\Binding of Isaac Repentance+\Data Event Manager.dat
```

### Formato de Datos

Cada evento se guarda en formato JSON con la siguiente estructura:

```json
{
  "event_type": "tipo_de_evento",
  "timestamp": 1647359012,
  "event_id": "dem_tipo_de_evento_1647359012_1234",
  "data": {
    // Datos específicos del evento
  },
  "game_data": {
    "seed": 1234567890,
    "level": 1,
    "room_id": 1001,
    // Más información del estado del juego
  }
}
```

## Cómo Funciona

1. **Recolección de Datos:**
   - El mod Lua registra eventos durante el juego
   - Los datos se guardan usando la API de Isaac.SaveModData
   - Nota: Cada nuevo evento sobrescribe el anterior debido a limitaciones de la API

2. **Extracción de Datos:**
   - El script `extract_data.py` lee el archivo guardado por el mod
   - Consolida los datos en una base de datos local (JSON)
   - Hace copias de seguridad del archivo original

3. **Análisis de Datos:**
   - Los datos consolidados pueden analizarse con las herramientas proporcionadas

## Limitaciones Importantes

1. **Un solo evento a la vez:**
   - La API SaveModData solo permite guardar un archivo único por mod
   - Cada nuevo evento sobrescribe cualquier evento anterior que no se haya extraído
   - Por eso es importante extraer datos regularmente

2. **Ubicación del archivo de datos:**
   - Isaac guarda los datos en `Documents\My Games\Binding of Isaac Repentance+\` 
   - No se puede cambiar esta ubicación, es fijada por el juego

## Flujo de Trabajo Recomendado

1. Instala el mod con `go update`
2. Juega al juego normalmente
3. Ejecuta la extracción con `go extract` periódicamente durante o después de jugar
4. Repite el proceso para recolectar más datos

## Desarrollo y Extensión

Para extender el sistema, puedes:
- Añadir nuevos tipos de eventos en `data_manager.lua`
- Crear nuevas herramientas de análisis en Python
- Modificar el extractor para procesar los datos de diferentes maneras

## Licencia

Este proyecto está licenciado bajo MIT License. 