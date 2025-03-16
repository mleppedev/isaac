-- main.lua
-- Mod para extraer datos de The Binding of Isaac
-- Versión simplificada para garantizar compatibilidad

-- Obtener referencia al mod
local mod = RegisterMod("DataExtractorMod", 1)

-- Cargar configuración
local Config = {}
Config.API_KEY = "default_key"
Config.SERVER_URL = "http://localhost:8000/api/data"
Config.USER_ID = "test_user"

-- Intentar cargar desde archivo
local function loadConfig()
  local ok, err = pcall(function()
    local configFile = "config.lua"
    package.loaded[configFile] = nil
    Config = require(configFile)
  end)
  
  if not ok then
    print("Error al cargar config.lua: " .. tostring(err))
    print("Usando configuración por defecto")
  end
end

-- Cargar configuración
loadConfig()

-- Variables globales
local dataCollected = 0
local lastRoomId = 0
local showOverlay = true
local keyWasPressed = false -- Variable para evitar activaciones repetidas
local lastUpdate = 0 -- Para controlar la frecuencia de actualizaciones
local showCircles = true -- Mostrar círculos alrededor de entidades

-- Función para guardar datos en un archivo
local function saveData(data)
  -- Convertir a formato de texto simple
  local dataStr = string.format("Room: %d, Health: %d, Pos: (%.2f, %.2f), Enemies: %d, Time: %s\n", 
                               data.room_id, data.health, data.position.x, data.position.y, 
                               data.enemies, data.timestamp)
  
  -- Intentar guardar en el directorio del mod
  local success = false
  local paths = {
    ".", -- Directorio actual
    "./mods/DataExtractorMod/", -- Ruta relativa común
    "C:/Users/Public/Documents/", -- Ubicación alternativa accesible
    "D:/SteamLibrary/steamapps/common/The Binding of Isaac Rebirth/mods/DataExtractorMod/", -- Ruta específica
    "C:/Program Files (x86)/Steam/steamapps/common/The Binding of Isaac Rebirth/mods/DataExtractorMod/", -- Otra ruta común
    os.getenv("USERPROFILE") .. "/Documents/" -- Documentos del usuario
  }
  
  -- Intentar guardar en varias ubicaciones
  for _, path in ipairs(paths) do
    -- Archivo de datos extraídos
    local file = io.open(path .. "extracted_data.txt", "a")
    if file then
      file:write(dataStr)
      file:close()
      print("Datos guardados en: " .. path .. "extracted_data.txt")
      success = true
      
      -- También guardar en formato JSON para el script de envío
      local jsonFile = io.open(path .. "pending_data.json", "a")
      if jsonFile then
        -- Formato JSON simplificado
        local jsonStr = string.format('{"room_id":%d,"health":%d,"position":{"x":%.2f,"y":%.2f},"enemies":%d,"timestamp":"%s"}\n',
                                     data.room_id, data.health, data.position.x, data.position.y, 
                                     data.enemies, data.timestamp)
        jsonFile:write(jsonStr)
        jsonFile:close()
        print("JSON guardado en: " .. path .. "pending_data.json")
      end
      
      break
    end
  end
  
  if not success then
    print("Error: No se pudo guardar en ninguna ubicación")
  else
    dataCollected = dataCollected + 1
  end
  
  return success
end

-- Función para obtener timestamp actual
local function getTimestamp()
  return os.date("%Y-%m-%dT%H:%M:%S")
end

-- Función para dibujar un círculo alrededor de una entidad
local function drawCircle(entity, r, g, b, a, radius)
  if not entity or not entity.Position then return end
  
  -- Valores por defecto
  r = r or 1
  g = g or 0
  b = b or 0
  a = a or 0.5
  radius = radius or 20
  
  -- Obtener la posición en coordenadas de pantalla
  local pos = Isaac.WorldToScreen(entity.Position)
  if not pos then return end
  
  -- Método 1: Usar RenderCircle si está disponible
  if Isaac.RenderCircle then
    Isaac.RenderCircle(pos.X, pos.Y, radius, r, g, b, a)
    return
  end
  
  -- Método 2: Usar RenderLine para aproximar un círculo
  if Isaac.RenderLine then
    local segments = 16
    local prevX, prevY = nil, nil
    local firstX, firstY = nil, nil
    
    for i = 0, segments do
      local angle = (i / segments) * 6.28318 -- 2*PI
      local x = pos.X + math.cos(angle) * radius
      local y = pos.Y + math.sin(angle) * radius
      
      if prevX and prevY then
        Isaac.RenderLine(prevX, prevY, x, y, r, g, b, a)
      else
        firstX, firstY = x, y
      end
      
      prevX, prevY = x, y
    end
    
    -- Cerrar el círculo
    if firstX and firstY and prevX and prevY then
      Isaac.RenderLine(prevX, prevY, firstX, firstY, r, g, b, a)
    end
    
    return
  end
  
  -- Método 3: Usar RenderText para aproximar un círculo
  if Isaac.RenderText then
    local text = "O"
    local scale = radius / 10
    Isaac.RenderText(text, pos.X - 5 * scale, pos.Y - 10 * scale, r, g, b, a, scale)
  end
end

-- Función para recopilar datos del juego
local function collectGameData()
  -- Obtener referencias a objetos del juego
  local game = Game()
  if not game then return nil end
  
  local room = game:GetRoom()
  if not room then return nil end
  
  local player = Isaac.GetPlayer(0)
  if not player then return nil end
  
  -- Extraer datos básicos con verificaciones
  local health = 0
  if player.Hearts ~= nil then health = player.Hearts end
  
  local posX, posY = 0, 0
  if player.Position then
    posX = player.Position.X or 0
    posY = player.Position.Y or 0
  end
  
  local enemyCount = 0
  if room.GetAliveEnemiesCount then
    enemyCount = room:GetAliveEnemiesCount() or 0
  end
  
  local roomSeed = 0
  if room.GetAwardSeed then
    roomSeed = room:GetAwardSeed() or 0
  end
  
  local timestamp = getTimestamp()
  
  -- Actualizar variables globales
  lastRoomId = roomSeed
  
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
  
  return data
end

-- Función que se ejecuta al entrar en una nueva habitación
function mod:onNewRoom()
  local data = collectGameData()
  if data then
    -- Guardar datos
    saveData(data)
    
    -- Imprimir información de depuración
    print("DataExtractorMod: Datos extraídos para habitación " .. data.room_id)
    print("Salud: " .. data.health .. ", Enemigos: " .. data.enemies)
    print("Posición: (" .. data.position.x .. ", " .. data.position.y .. ")")
  end
end

-- Función para actualizar datos periódicamente
function mod:onUpdate()
  -- Actualizar cada 5 segundos (30 frames a 60 FPS)
  local currentTime = Game().FrameCount
  if currentTime - lastUpdate > 300 then
    lastUpdate = currentTime
    
    local data = collectGameData()
    if data then
      -- Guardar datos
      saveData(data)
    end
  end
end

-- Función para mostrar información en pantalla
function mod:onRender()
  if not showOverlay then return end
  
  -- Obtener referencia al juego
  local game = Game()
  
  -- Verificar si el HUD está visible
  if not game:GetHUD():IsVisible() then return end
  
  -- Obtener dimensiones de la pantalla
  local width, height = 0, 0
  if Isaac.GetScreenWidth and Isaac.GetScreenHeight then
    width = Isaac.GetScreenWidth()
    height = Isaac.GetScreenHeight()
  else
    width = 960  -- Valores por defecto para resolución 4:3
    height = 540
  end
  
  -- Posicionar en la parte inferior central
  local scale = 0.5  -- Escala más pequeña
  local lineHeight = 10
  
  -- Calcular ancho del texto para centrarlo
  local textWidth = 150 * scale  -- Estimación aproximada
  local baseX = (width / 2) - (textWidth / 2)
  local baseY = height - 50
  
  -- Mostrar información básica con texto más pequeño y discreto
  -- Usar la API de texto del juego
  Isaac.RenderText("DataExtractorMod | Datos: " .. dataCollected .. " | Sala: " .. lastRoomId, 
                  baseX, baseY, 0.7, 0.7, 0.7, 0.6, scale)
  
  -- Dibujar círculos alrededor de entidades si está activado
  if showCircles then
    -- Marcar al jugador
    local player = Isaac.GetPlayer(0)
    if player then
      -- Dibujar círculo verde alrededor del jugador
      drawCircle(player, 0, 1, 0, 0.5, 25)
    end
    
    -- Marcar a los enemigos
    local room = game:GetRoom()
    if room then
      -- Obtener todas las entidades en la habitación
      for i, entity in ipairs(Isaac.GetRoomEntities()) do
        -- Verificar si es un enemigo
        if entity:IsActiveEnemy() and entity:IsVulnerableEnemy() then
          -- Dibujar círculo rojo alrededor del enemigo
          drawCircle(entity, 1, 0, 0, 0.5, 20)
        end
      end
    end
  end
  
  -- Verificar teclas para alternar la visibilidad
  -- Usar Input.IsButtonPressed en lugar de callbacks para mayor compatibilidad
  if Input and Input.IsButtonPressed then
    -- Tecla Tab (9)
    local isTabPressed = Input.IsButtonPressed(Keyboard.KEY_TAB, 0)
    
    -- Alternar visibilidad solo cuando se presiona la tecla (no cuando se mantiene)
    if isTabPressed and not keyWasPressed then
      showOverlay = not showOverlay
      print("DataExtractorMod: Overlay " .. (showOverlay and "ACTIVADO" or "DESACTIVADO"))
      keyWasPressed = true
    elseif not isTabPressed and keyWasPressed then
      keyWasPressed = false
    end
    
    -- Tecla F3 para alternar círculos
    local isF3Pressed = Input.IsButtonPressed(Keyboard.KEY_F3, 0)
    if isF3Pressed and not keyWasPressed then
      showCircles = not showCircles
      print("DataExtractorMod: Círculos " .. (showCircles and "ACTIVADOS" or "DESACTIVADOS"))
      keyWasPressed = true
    elseif not isF3Pressed and not isTabPressed and keyWasPressed then
      keyWasPressed = false
    end
  end
end

-- Función que se ejecuta al iniciar el juego
function mod:onGameStart(isContinued)
  print("DataExtractorMod iniciado correctamente")
  print("Versión: 1.6 (Visual)")
  print("URL del servidor: " .. Config.SERVER_URL)
  print("Presiona TAB para mostrar/ocultar información")
  print("Presiona F3 para mostrar/ocultar círculos")
  
  -- Reiniciar contadores
  dataCollected = 0
  lastRoomId = 0
  showOverlay = true
  showCircles = true
  keyWasPressed = false
  lastUpdate = 0
  
  -- Recopilar datos iniciales
  local data = collectGameData()
  if data then
    saveData(data)
  end
end

-- Registrar callbacks
mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, mod.onNewRoom)
mod:AddCallback(ModCallbacks.MC_POST_RENDER, mod.onRender)
mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, mod.onGameStart)
mod:AddCallback(ModCallbacks.MC_POST_UPDATE, mod.onUpdate)

-- Mensaje de inicialización
print("DataExtractorMod cargado correctamente")
print("Presiona TAB para mostrar/ocultar información")
print("Presiona F3 para mostrar/ocultar círculos") 