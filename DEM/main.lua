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
local showDetailedHitbox = true -- Mostrar información detallada del hitbox

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

-- Función para dibujar un hitbox alrededor de una entidad
local function drawCircle(entity, r, g, b, a, radius)
  if not entity or not entity.Position then return end
  
  -- Valores por defecto
  r = r or 1
  g = g or 0
  b = b or 0
  a = a or 0.5
  
  -- Intentar obtener el hitbox real de la entidad
  local entityRadius = radius or 20
  local entityType = "Unknown"
  local entityHP = 0
  local entityID = 0
  local entityVariant = 0
  local entitySubType = 0
  local entitySpeed = 0
  local entityDamage = 0
  local entityName = "Unknown"
  
  -- Intentar obtener el tamaño real del hitbox si está disponible
  if entity.Size then
    entityRadius = entity.Size
  elseif entity.HitPoints and entity.MaxHitPoints then
    -- Estimar tamaño basado en HP para enemigos (más HP = más grande)
    local hpRatio = entity.HitPoints / math.max(1, entity.MaxHitPoints)
    entityRadius = 10 + (20 * hpRatio)
  end
  
  -- Obtener información adicional de la entidad
  if entity.Type then
    entityID = entity.Type
    if entity.Variant then entityVariant = entity.Variant end
    if entity.SubType then entitySubType = entity.SubType end
    
    if entity.Type == EntityType.ENTITY_PLAYER then
      entityType = "Player"
      entityName = "Isaac"
      -- Intentar obtener el nombre real del personaje
      if entity:ToPlayer() then
        local player = entity:ToPlayer()
        if player:GetPlayerType() then
          local playerType = player:GetPlayerType()
          if playerType == PlayerType.PLAYER_ISAAC then entityName = "Isaac"
          elseif playerType == PlayerType.PLAYER_MAGDALENE then entityName = "Magdalene"
          elseif playerType == PlayerType.PLAYER_CAIN then entityName = "Cain"
          elseif playerType == PlayerType.PLAYER_JUDAS then entityName = "Judas"
          elseif playerType == PlayerType.PLAYER_XXX then entityName = "???"
          elseif playerType == PlayerType.PLAYER_EVE then entityName = "Eve"
          elseif playerType == PlayerType.PLAYER_SAMSON then entityName = "Samson"
          elseif playerType == PlayerType.PLAYER_AZAZEL then entityName = "Azazel"
          elseif playerType == PlayerType.PLAYER_LAZARUS then entityName = "Lazarus"
          elseif playerType == PlayerType.PLAYER_EDEN then entityName = "Eden"
          elseif playerType == PlayerType.PLAYER_THELOST then entityName = "The Lost"
          elseif playerType == PlayerType.PLAYER_LAZARUS2 then entityName = "Lazarus II"
          elseif playerType == PlayerType.PLAYER_BLACKJUDAS then entityName = "Black Judas"
          elseif playerType == PlayerType.PLAYER_LILITH then entityName = "Lilith"
          elseif playerType == PlayerType.PLAYER_KEEPER then entityName = "Keeper"
          elseif playerType == PlayerType.PLAYER_APOLLYON then entityName = "Apollyon"
          elseif playerType == PlayerType.PLAYER_THEFORGOTTEN then entityName = "The Forgotten"
          elseif playerType == PlayerType.PLAYER_THESOUL then entityName = "The Soul"
          elseif playerType == PlayerType.PLAYER_BETHANY then entityName = "Bethany"
          elseif playerType == PlayerType.PLAYER_JACOB then entityName = "Jacob"
          elseif playerType == PlayerType.PLAYER_ESAU then entityName = "Esau"
          else entityName = "Player_" .. playerType
          end
        end
      end
      
      -- Obtener información adicional del jugador
      if entity.Damage then entityDamage = entity.Damage end
      if entity.MoveSpeed then entitySpeed = entity.MoveSpeed end
    elseif entity.Type == EntityType.ENTITY_TEAR then
      entityType = "Tear"
    elseif entity.Type == EntityType.ENTITY_FAMILIAR then
      entityType = "Familiar"
      -- Intentar identificar familiares comunes por su variante
      if entityVariant == FamiliarVariant.BROTHER_BOBBY then entityName = "Brother Bobby"
      elseif entityVariant == FamiliarVariant.SISTER_MAGGY then entityName = "Sister Maggy"
      elseif entityVariant == FamiliarVariant.ROBO_BABY then entityName = "Robo-Baby"
      elseif entityVariant == FamiliarVariant.LITTLE_STEVEN then entityName = "Little Steven"
      elseif entityVariant == FamiliarVariant.DEMON_BABY then entityName = "Demon Baby"
      else entityName = "Familiar_" .. entityVariant
      end
    elseif entity.Type == EntityType.ENTITY_BOMB then
      entityType = "Bomb"
    elseif entity.Type == EntityType.ENTITY_PICKUP then
      entityType = "Pickup"
      -- Identificar tipos de pickups
      if entityVariant == PickupVariant.PICKUP_HEART then entityName = "Heart"
      elseif entityVariant == PickupVariant.PICKUP_COIN then entityName = "Coin"
      elseif entityVariant == PickupVariant.PICKUP_KEY then entityName = "Key"
      elseif entityVariant == PickupVariant.PICKUP_BOMB then entityName = "Bomb"
      elseif entityVariant == PickupVariant.PICKUP_CHEST then entityName = "Chest"
      elseif entityVariant == PickupVariant.PICKUP_PILL then entityName = "Pill"
      elseif entityVariant == PickupVariant.PICKUP_TRINKET then entityName = "Trinket"
      elseif entityVariant == PickupVariant.PICKUP_COLLECTIBLE then entityName = "Item"
      else entityName = "Pickup_" .. entityVariant
      end
    elseif entity.Type == EntityType.ENTITY_LASER then
      entityType = "Laser"
    elseif entity.Type == EntityType.ENTITY_KNIFE then
      entityType = "Knife"
    elseif entity.IsActiveEnemy and entity:IsActiveEnemy() then
      entityType = "Enemy"
      -- Intentar identificar enemigos comunes
      if entityID == EntityType.ENTITY_FLY then entityName = "Fly"
      elseif entityID == EntityType.ENTITY_POOTER then entityName = "Pooter"
      elseif entityID == EntityType.ENTITY_CLOTTY then entityName = "Clotty"
      elseif entityID == EntityType.ENTITY_GAPER then entityName = "Gaper"
      elseif entityID == EntityType.ENTITY_MULLIGAN then entityName = "Mulligan"
      elseif entityID == EntityType.ENTITY_HOPPER then entityName = "Hopper"
      elseif entityID == EntityType.ENTITY_SPIDER then entityName = "Spider"
      else entityName = "Enemy_" .. entityID
      end
      
      -- Obtener información adicional del enemigo
      if entity.Damage then entityDamage = entity.Damage end
      if entity.MoveSpeed then entitySpeed = entity.MoveSpeed end
    elseif entity.IsBoss and entity:IsBoss() then
      entityType = "Boss"
      -- Intentar identificar jefes comunes
      if entityID == EntityType.ENTITY_MONSTRO then entityName = "Monstro"
      elseif entityID == EntityType.ENTITY_DUKE then entityName = "Duke of Flies"
      elseif entityID == EntityType.ENTITY_GEMINI then entityName = "Gemini"
      elseif entityID == EntityType.ENTITY_LARRY_JR then entityName = "Larry Jr."
      elseif entityID == EntityType.ENTITY_CHUB then entityName = "Chub"
      elseif entityID == EntityType.ENTITY_GURDY then entityName = "Gurdy"
      elseif entityID == EntityType.ENTITY_MOM then entityName = "Mom"
      elseif entityID == EntityType.ENTITY_SATAN then entityName = "Satan"
      elseif entityID == EntityType.ENTITY_ISAAC then entityName = "Isaac"
      elseif entityID == EntityType.ENTITY_HUSH then entityName = "Hush"
      else entityName = "Boss_" .. entityID
      end
      
      -- Obtener información adicional del jefe
      if entity.Damage then entityDamage = entity.Damage end
      if entity.MoveSpeed then entitySpeed = entity.MoveSpeed end
    end
  end
  
  -- Obtener HP si está disponible
  if entity.HitPoints then
    entityHP = math.floor(entity.HitPoints)
  end
  
  -- Obtener la posición en coordenadas de pantalla
  local pos = Isaac.WorldToScreen(entity.Position)
  if not pos then return end
  
  -- Dibujar el hitbox (círculo) alrededor de la entidad
  if Isaac.RenderCircle then
    Isaac.RenderCircle(pos.X, pos.Y, entityRadius, r, g, b, a)
    
    -- Dibujar líneas cruzadas en el CENTRO de la entidad para mejor visualización
    Isaac.RenderLine(pos.X - entityRadius, pos.Y, pos.X + entityRadius, pos.Y, r, g, b, a)
    Isaac.RenderLine(pos.X, pos.Y - entityRadius, pos.X, pos.Y + entityRadius, r, g, b, a)
    
    -- Dibujar puntos en los bordes para mejor visualización
    local pointSize = 2
    Isaac.RenderRect(pos.X - entityRadius - pointSize/2, pos.Y - pointSize/2, pointSize, pointSize, r, g, b, a)
    Isaac.RenderRect(pos.X + entityRadius - pointSize/2, pos.Y - pointSize/2, pointSize, pointSize, r, g, b, a)
    Isaac.RenderRect(pos.X - pointSize/2, pos.Y - entityRadius - pointSize/2, pointSize, pointSize, r, g, b, a)
    Isaac.RenderRect(pos.X - pointSize/2, pos.Y + entityRadius - pointSize/2, pointSize, pointSize, r, g, b, a)
    
    -- Dibujar una cruz en el CENTRO de la entidad (más visible)
    local crossSize = 6
    local crossThickness = 2
    
    -- Cruz horizontal
    Isaac.RenderRect(pos.X - crossSize/2, pos.Y - crossThickness/2, crossSize, crossThickness, 1, 1, 1, 0.9)
    
    -- Cruz vertical
    Isaac.RenderRect(pos.X - crossThickness/2, pos.Y - crossSize/2, crossThickness, crossSize, 1, 1, 1, 0.9)
    
    -- Mostrar información detallada (siempre mostrar nombre, ID y HP)
    -- Crear texto con información más completa
    local infoText = string.format("%s", entityName)
    
    -- Añadir HP si está disponible (siempre mostrar, incluso si es 0)
    infoText = infoText .. string.format(" HP:%d", entityHP)
    
    -- Añadir ID de entidad simplificada (solo mostrar valores no cero)
    if entityVariant == 0 and entitySubType == 0 then
      infoText = infoText .. string.format(" ID:%d", entityID)
    elseif entitySubType == 0 then
      infoText = infoText .. string.format(" ID:%d.%d", entityID, entityVariant)
    else
      infoText = infoText .. string.format(" ID:%d.%d.%d", entityID, entityVariant, entitySubType)
    end
    
    -- Añadir información de daño y velocidad para jugadores y enemigos
    if (entityType == "Player" or entityType == "Enemy" or entityType == "Boss") and entityDamage > 0 then
      infoText = infoText .. string.format(" DMG:%.1f", entityDamage)
    end
    
    if (entityType == "Player" or entityType == "Enemy" or entityType == "Boss") and entitySpeed > 0 then
      infoText = infoText .. string.format(" SPD:%.1f", entitySpeed)
    end
    
    -- Texto más pequeño (escala 0.3)
    Isaac.RenderText(infoText, pos.X - 50, pos.Y + entityRadius + 5, r, g, b, 0.8, 0.2)
    
    return
  end
  
  -- Método 2: Dibujar un círculo con líneas
  if Isaac.RenderLine then
    local segments = 24  -- Más segmentos para mayor precisión
    local prevX, prevY = nil, nil
    local firstX, firstY = nil, nil
    
    for i = 0, segments do
      local angle = (i / segments) * 6.28318 -- 2*PI
      local x = pos.X + math.cos(angle) * entityRadius
      local y = pos.Y + math.sin(angle) * entityRadius
      
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
    
    -- Dibujar líneas cruzadas en el CENTRO para mejor visualización del hitbox
    Isaac.RenderLine(pos.X - entityRadius, pos.Y, pos.X + entityRadius, pos.Y, r, g, b, a)
    Isaac.RenderLine(pos.X, pos.Y - entityRadius, pos.X, pos.Y + entityRadius, r, g, b, a)
    
    -- Dibujar una cruz en el CENTRO de la entidad (más visible)
    local crossSize = 6
    local crossThickness = 2
    
    -- Cruz horizontal
    if Isaac.RenderRect then
      Isaac.RenderRect(pos.X - crossSize/2, pos.Y - crossThickness/2, crossSize, crossThickness, 1, 1, 1, 0.9)
      
      -- Cruz vertical
      Isaac.RenderRect(pos.X - crossThickness/2, pos.Y - crossSize/2, crossThickness, crossSize, 1, 1, 1, 0.9)
    end
    
    -- Dibujar puntos en los bordes para mejor visualización
    local pointSize = 2
    if Isaac.RenderRect then
      Isaac.RenderRect(pos.X - entityRadius - pointSize/2, pos.Y - pointSize/2, pointSize, pointSize, r, g, b, a)
      Isaac.RenderRect(pos.X + entityRadius - pointSize/2, pos.Y - pointSize/2, pointSize, pointSize, r, g, b, a)
      Isaac.RenderRect(pos.X - pointSize/2, pos.Y - entityRadius - pointSize/2, pointSize, pointSize, r, g, b, a)
      Isaac.RenderRect(pos.X - pointSize/2, pos.Y + entityRadius - pointSize/2, pointSize, pointSize, r, g, b, a)
    end
    
    -- Mostrar información detallada (siempre mostrar nombre, ID y HP)
    local infoText = string.format("%s", entityName)
    
    -- Añadir HP si está disponible (siempre mostrar, incluso si es 0)
    infoText = infoText .. string.format(" HP:%d", entityHP)
    
    -- Añadir ID de entidad simplificada (solo mostrar valores no cero)
    if entityVariant == 0 and entitySubType == 0 then
      infoText = infoText .. string.format(" ID:%d", entityID)
    elseif entitySubType == 0 then
      infoText = infoText .. string.format(" ID:%d.%d", entityID, entityVariant)
    else
      infoText = infoText .. string.format(" ID:%d.%d.%d", entityID, entityVariant, entitySubType)
    end
    
    -- Texto más pequeño (escala 0.3)
    Isaac.RenderText(infoText, pos.X - 50, pos.Y + entityRadius + 5, r, g, b, 0.8, 0.2)
    
    return
  end
  
  -- Método 3: Usar formas geométricas como fallback
  if Isaac.RenderText then
    -- Crear un círculo con caracteres ASCII
    local chars = {"+", "-", "|", "/", "\\"}
    local scale = 0.3
    
    -- Dibujar un punto central
    Isaac.RenderText("+", pos.X - 2, pos.Y - 4, r, g, b, a, scale)
    
    -- Dibujar los bordes del círculo con caracteres
    Isaac.RenderText("-", pos.X - entityRadius, pos.Y - 4, r, g, b, a, scale)
    Isaac.RenderText("-", pos.X + entityRadius - 4, pos.Y - 4, r, g, b, a, scale)
    Isaac.RenderText("|", pos.X - 2, pos.Y - entityRadius, r, g, b, a, scale)
    Isaac.RenderText("|", pos.X - 2, pos.Y + entityRadius - 8, r, g, b, a, scale)
    
    -- Mostrar información detallada (siempre mostrar nombre, ID y HP)
    local infoText = string.format("%s", entityName)
    
    -- Añadir HP si está disponible (siempre mostrar, incluso si es 0)
    infoText = infoText .. string.format(" HP:%d", entityHP)
    
    -- Añadir ID de entidad simplificada (solo mostrar valores no cero)
    if entityVariant == 0 and entitySubType == 0 then
      infoText = infoText .. string.format(" ID:%d", entityID)
    elseif entitySubType == 0 then
      infoText = infoText .. string.format(" ID:%d.%d", entityID, entityVariant)
    else
      infoText = infoText .. string.format(" ID:%d.%d.%d", entityID, entityVariant, entitySubType)
    end
    
    -- Texto más pequeño (escala 0.2 para que sea aún más pequeño y debajo de la entidad)
    Isaac.RenderText(infoText, pos.X - 50, pos.Y + entityRadius + 5, r, g, b, 0.8, 0.2)
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
    
    -- Tecla F4 para alternar información detallada del hitbox
    local isF4Pressed = Input.IsButtonPressed(Keyboard.KEY_F4, 0)
    if isF4Pressed and not keyWasPressed then
      showDetailedHitbox = not showDetailedHitbox
      print("DataExtractorMod: Información detallada " .. (showDetailedHitbox and "ACTIVADA" or "DESACTIVADA"))
      keyWasPressed = true
    elseif not isF4Pressed and not isF3Pressed and not isTabPressed and keyWasPressed then
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
  print("Presiona F4 para mostrar/ocultar información detallada")
  
  -- Reiniciar contadores
  dataCollected = 0
  lastRoomId = 0
  showOverlay = true
  showCircles = true
  showDetailedHitbox = true
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
print("Presiona F4 para mostrar/ocultar información detallada") 
