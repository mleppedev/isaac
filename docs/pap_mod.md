# Guía para Crear un Mod de Extracción de Datos en The Binding of Isaac

## 1. Configuración del Entorno

### a. Preparar la carpeta de mods

**Ubicación del directorio de mods:**

Los mods se suelen colocar en la carpeta:

**Steam:**
```
{SteamInstallPath}\Steam\userdata\{tuSteamID}\250900\mods
```

**No-Steam:**
```
Documentos\My Games\Binding of Isaac Rebirth\mods
```

**Crear una carpeta para tu mod:**
Por ejemplo, crea una carpeta llamada `DataExtractorMod`.

## 2. Estructura Básica del Mod

Dentro de la carpeta `DataExtractorMod` crea al menos los siguientes archivos:

- **metadata.xml**: Este archivo contiene la información básica del mod.
- **main.lua**: Archivo principal donde escribirás el código en Lua.

### Ejemplo de metadata.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<metadata>
  <name>DataExtractorMod</name>
  <version>1.0</version>
  <author>TuNombre</author>
  <description>Mod para extraer datos relevantes del juego para entrenar una IA.</description>
</metadata>
```

## 3. Creando el Archivo Principal (main.lua)

En main.lua escribirás el código para interceptar eventos y capturar la información. Comenzaremos con una estructura básica.

### a. Inicialización del Mod

Utilizaremos funciones de The Binding of Isaac para enganchar eventos importantes. Un ejemplo básico:

```lua
-- main.lua

-- Variable global para almacenar datos de la partida
local extractedData = {}

-- Función para guardar datos (por ejemplo, en un archivo de texto)
local function saveDataToFile(data)
  local file = io.open("extracted_data.txt", "a")  -- 'a' para agregar contenido
  if file then
    file:write(data .. "\n")
    file:close()
  else
    print("Error al abrir el archivo para escribir datos.")
  end
end

-- Ejemplo: Hook en el inicio de una nueva habitación
function MC_POST_NEW_ROOM()
  local room = Game():GetRoom()
  local player = Isaac.GetPlayer(0)
  
  -- Extraemos algunos datos básicos: salud, posición del jugador y número de enemigos en la habitación
  local health = player:GetHearts()
  local posX = player.Position.X
  local posY = player.Position.Y
  local enemyCount = room:GetAliveEnemiesCount()
  
  local dataString = string.format("Room: %d, Health: %d, Pos: (%.2f, %.2f), Enemies: %d", 
                                   room:GetAwardSeed(), health, posX, posY, enemyCount)
  
  -- Almacena y guarda la información
  table.insert(extractedData, dataString)
  saveDataToFile(dataString)
  
  -- Imprime en consola para depuración
  print(dataString)
end

-- Registra la función MC_POST_NEW_ROOM para que se ejecute al iniciar una nueva habitación
Isaac.RegisterCallback(Mod(), MC_POST_NEW_ROOM, ModCallbacks.MC_POST_NEW_ROOM)
```

### b. Explicación del Código

- **Variable extractedData**:
  Se usa para almacenar en memoria las líneas de datos que luego podrías procesar o enviar a otro sistema.

- **Función saveDataToFile**:
  Abre (o crea) un archivo llamado `extracted_data.txt` en la carpeta del mod y añade la información extraída. Esto puede servir como registro para entrenar la IA.

- **Función MC_POST_NEW_ROOM**:
  Se ejecuta cada vez que el juego carga una nueva habitación. En este ejemplo se extraen:
  - La salud del jugador.
  - La posición del jugador.
  - El número de enemigos vivos en la habitación.
  
  Se formatea la información y se guarda tanto en el archivo como en la variable global.

- **Registro del Callback**:
  La línea final `Isaac.RegisterCallback(Mod(), MC_POST_NEW_ROOM, ModCallbacks.MC_POST_NEW_ROOM)` indica al juego que llame a la función cada vez que se inicie una nueva habitación.

## 4. Pruebas y Ajustes

**Carga el mod en el juego:**
1. Arranca The Binding of Isaac: Rebirth.
2. En el menú de mods, activa DataExtractorMod.

**Verifica la extracción:**
1. Juega y cambia de habitaciones.
2. Revisa la consola (si está habilitada) o el archivo `extracted_data.txt` que debería crearse en la carpeta del mod.

**Ajusta los datos según lo que necesites:**
- Si necesitas más información (por ejemplo, datos de objetos recogidos, estadísticas de enemigos, etc.), añade nuevos hooks o extiende la función MC_POST_NEW_ROOM u otras callbacks disponibles (como MC_POST_PLAYER_UPDATE o MC_PRE_TEAR_COLLISION).

## 5. Documentación y Recursos

**Documentación de modding para Isaac:**
Te recomiendo revisar la wiki de modding de The Binding of Isaac para conocer todos los eventos y funciones disponibles.

**Comunidades y Foros:**
Existen foros y comunidades en línea (como en Reddit o Discord) donde modders comparten ejemplos y resuelven dudas, lo cual puede ser muy útil si te encuentras con algún problema.

## 6. Próximos Pasos para la IA

Una vez que el mod extraiga los datos necesarios, puedes:
- Enviar los datos a un servidor o guardarlos en un formato estructurado (JSON, CSV, etc.) para su procesamiento.
- Desarrollar scripts en Python que consuman estos datos y los utilicen para entrenar modelos de aprendizaje por refuerzo u otras técnicas.

## 7. Manejo de Variables de Entorno para Información Sensible

Para evitar subir información sensible (como claves API, URLs de servidores, etc.) al repositorio, podemos implementar un sistema de variables de entorno en nuestro mod.

### a. Crear un archivo de configuración local

1. Crea un archivo llamado `config.lua` en la carpeta de tu mod:

```lua
-- config.lua
local Config = {}

-- Variables sensibles (valores por defecto)
Config.API_KEY = "default_key"
Config.SERVER_URL = "http://localhost:8000"
Config.USER_ID = "test_user"

return Config
```

2. Añade este archivo a tu `.gitignore` para evitar subirlo al repositorio:

```
# .gitignore
config.lua
```

3. Crea un archivo de ejemplo `config.example.lua` que sí subirás al repositorio:

```lua
-- config.example.lua
-- Copia este archivo como config.lua y configura tus valores
local Config = {}

Config.API_KEY = "tu_api_key_aquí"
Config.SERVER_URL = "url_de_tu_servidor_aquí"
Config.USER_ID = "tu_id_de_usuario_aquí"

return Config
```

### b. Usar la configuración en tu código principal

Modifica tu `main.lua` para importar y usar estas variables:

```lua
-- main.lua
local Config = require("config")

-- Variable global para almacenar datos de la partida
local extractedData = {}

-- Función para enviar datos a un servidor externo
local function sendDataToServer(data)
  -- Aquí usarías las variables de Config
  print("Enviando datos a: " .. Config.SERVER_URL)
  print("Usando API key: " .. Config.API_KEY)
  print("Para usuario: " .. Config.USER_ID)
  
  -- Implementación real de envío de datos
  -- (requeriría una biblioteca HTTP para Lua)
end

-- Función para guardar datos (por ejemplo, en un archivo de texto)
local function saveDataToFile(data)
  -- Código existente...
  
  -- Opcionalmente, enviar a servidor si está configurado
  if Config.SERVER_URL ~= "http://localhost:8000" then
    sendDataToServer(data)
  end
end

-- Resto del código existente...
```

### c. Instrucciones para otros desarrolladores

Añade estas instrucciones a tu README para que otros desarrolladores sepan cómo configurar el entorno:

1. Copia `config.example.lua` como `config.lua`
2. Edita `config.lua` con tus credenciales y configuración personal
3. Nunca subas `config.lua` al repositorio

### d. Alternativa: Cargar desde archivo externo

Si prefieres mantener las variables completamente fuera del mod, puedes cargarlas desde un archivo externo:

```lua
-- main.lua
local function loadExternalConfig()
  local config = {}
  local file = io.open("../env_config.txt", "r")
  
  if file then
    for line in file:lines() do
      local key, value = line:match("([^=]+)=(.+)")
      if key and value then
        config[key:trim()] = value:trim()
      end
    end
    file:close()
    return config
  else
    print("No se pudo cargar la configuración externa")
    return {
      API_KEY = "default_key",
      SERVER_URL = "http://localhost:8000",
      USER_ID = "test_user"
    }
  end
end

local ExternalConfig = loadExternalConfig()
```

Con este enfoque, puedes mantener un archivo `env_config.txt` fuera de la carpeta del mod con el formato:

```
API_KEY=tu_clave_secreta
SERVER_URL=https://tu-servidor.com/api
USER_ID=tu_id
```