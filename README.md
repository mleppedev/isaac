# DEM - Data Event Manager

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