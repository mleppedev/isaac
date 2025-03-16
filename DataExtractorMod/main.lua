-- main.lua
local Config = require("config")

-- Variable global para almacenar datos de la partida
local extractedData = {}

-- Función para convertir datos a formato JSON
local function toJSON(data)
  local json = "{"
  local i = 0
  for k, v in pairs(data) do
    if i > 0 then json = json .. "," end
    if type(v) == "string" then
      json = json .. '"' .. k .. '":"' .. v .. '"'
    elseif type(v) == "number" then
      json = json .. '"' .. k .. '":' .. v
    elseif type(v) == "table" then
      json = json .. '"' .. k .. '":' .. toJSON(v)
    elseif type(v) == "boolean" then
      json = json .. '"' .. k .. '":' .. (v and "true" or "false")
    end
    i = i + 1
  end
  return json .. "}"
end

-- Función para obtener timestamp actual
local function getTimestamp()
  return os.date("%Y-%m-%dT%H:%M:%S")
end

-- Función para enviar datos a un servidor externo
local function sendDataToServer(data)
  -- Preparar los datos en formato JSON
  local jsonData = toJSON(data)
  
  -- Imprimir información de depuración
  print("Enviando datos a: " .. Config.SERVER_URL)
  print("Usando API key: " .. Config.API_KEY)
  print("Para usuario: " .. Config.USER_ID)
  print("Datos: " .. jsonData)
  
  -- Aquí iría el código para enviar los datos al servidor
  -- Como Lua en Isaac no tiene soporte nativo para HTTP,
  -- esto es una simulación del envío
  
  -- En un entorno real, podrías usar:
  -- 1. Un módulo externo como luasocket (si está disponible)
  -- 2. Escribir los datos a un archivo que un script externo lea y envíe
  -- 3. Usar un plugin o extensión específica de Isaac que permita HTTP
  
  print("Simulando envío de datos al servidor...")
  
  -- Guardar en un archivo para que un script externo lo procese
  local file = io.open("pending_data.json", "a")
  if file then
    file:write(jsonData .. "\n")
    file:close()
    print("Datos guardados para envío posterior")
    return true
  else
    print("Error al guardar datos para envío")
    return false
  end
end

-- Función para guardar datos (por ejemplo, en un archivo de texto)
local function saveDataToFile(data)
  -- Guardar en formato legible
  local file = io.open("extracted_data.txt", "a")  -- 'a' para agregar contenido
  if file then
    local dataString = string.format("Room: %d, Health: %d, Pos: (%.2f, %.2f), Enemies: %d, Time: %s", 
                                    data.room_id, data.health, data.position.x, data.position.y, 
                                    data.enemies, data.timestamp)
    file:write(dataString .. "\n")
    file:close()
  else
    print("Error al abrir el archivo para escribir datos.")
  end
  
  -- Opcionalmente, enviar a servidor si está configurado
  if Config.SERVER_URL ~= "http://localhost:8000" then
    return sendDataToServer(data)
  end
  
  return true
end

-- Ejemplo: Hook en el inicio de una nueva habitación
function MC_POST_NEW_ROOM()
  local room = Game():GetRoom()
  local player = Isaac.GetPlayer(0)
  
  -- Extraemos algunos datos básicos
  local health = player:GetHearts()
  local posX = player.Position.X
  local posY = player.Position.Y
  local enemyCount = room:GetAliveEnemiesCount()
  local roomSeed = room:GetAwardSeed()
  local timestamp = getTimestamp()
  
  -- Crear estructura de datos
  local data = {
    room_id = roomSeed,
    health = health,
    position = {
      x = posX,
      y = posY
    },
    enemies = enemyCount,
    timestamp = timestamp
  }
  
  -- Almacena y guarda la información
  table.insert(extractedData, data)
  saveDataToFile(data)
  
  -- Imprime en consola para depuración
  print("Datos extraídos para la habitación: " .. roomSeed)
end

-- Registra la función MC_POST_NEW_ROOM para que se ejecute al iniciar una nueva habitación
Isaac.RegisterCallback(Mod(), MC_POST_NEW_ROOM, ModCallbacks.MC_POST_NEW_ROOM) 