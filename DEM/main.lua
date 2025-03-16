-- main.lua
-- Mod para extraer datos de The Binding of Isaac
-- Versión con fuente personalizada

-- Obtener referencia al mod
local mod = RegisterMod("DataExtractorMod", 1)

-- Variables globales
local dataCollected = 0
local myFont = nil -- Variable para guardar nuestra fuente personalizada
local showEntityData = true -- Control para mostrar datos de entidades

-- Función para obtener timestamp actual
local function getTimestamp()
  return os.date("%Y-%m-%dT%H:%M:%S")
end

-- Función para inicializar la fuente
local function initializeFont()
  if myFont == nil then
    myFont = Font() -- Crear objeto Font
    myFont:Load("font/upheaval.fnt")
  end
  return myFont:IsLoaded()
end

-- Función para mostrar información básica
function mod:onRender()
  -- Obtener jugador
  local player = Isaac.GetPlayer(0)
  if not player then return end
  
  -- Obtener dimensiones de la pantalla
  local screenWidth = Isaac.GetScreenWidth() or 960
  local screenHeight = Isaac.GetScreenHeight() or 540
  
  -- Asegurarse de que tenemos una fuente cargada
  if not initializeFont() then
    -- Si no se pudo cargar ninguna fuente, usar el método predeterminado
    Isaac.RenderText("DATA EXTRACTOR MOD - No se pudo cargar fuente personalizada", 50, 30, 1, 0, 0, 1)
    return
  end
  
  -- Configuración de texto
  local lineHeight = 8 -- Reducir altura de línea
  local baseY = 0 -- Posición Y inicial
  local scaleX = 0.4 -- Factor de escala horizontal para reducir tamaño
  local scaleY = 0.4 -- Factor de escala vertical para reducir tamaño
  
  -- Definir color blanco usando KColor
  local whiteColor = KColor(1, 1, 1, 1)
  local redColor = KColor(1, 0, 0, 1)
  local greenColor = KColor(0, 1, 0, 1)
  local grayColor = KColor(0.7, 0.7, 0.7, 0.8)
  
  -- Usar caracteres especiales con códigos de escape:
  -- \3 = Corazón \4 = Medio corazón \5 = Corazón vacío
  -- \6 = Moneda \7 = Llave \8 = Bomba \1 = Píldora

  -- Mostrar vida del jugador con símbolos especiales
  local health = player.Hearts or 0
  local maxHealth = player.MaxHearts or 0
  local coins = player.Coins or 0
  local bombs = player.Bombs or 0
  local keys = player.Keys or 0
  
  -- Usar caracteres especiales directamente con la secuencia de escape \número
  local healthText = string.format("Vida: \3 %d/%d | \6 %d | \8 %d | \7 %d", 
                                  health/2, maxHealth/2, coins, bombs, keys)
  local healthWidth = (myFont:GetStringWidth(healthText) * scaleX)
  centerX = (screenWidth / 2) - (healthWidth / 2)
  myFont:DrawStringScaled(healthText, centerX, baseY + lineHeight, scaleX, scaleY, whiteColor, 0, true)
  
  -- Mostrar posición del jugador si está disponible
  if player.Position then
    local posX = player.Position.X or 0
    local posY = player.Position.Y or 0
    local posText = string.format("Posición: (%.1f, %.1f)", posX, posY)
    local posWidth = (myFont:GetStringWidth(posText) * scaleX)
    centerX = (screenWidth / 2) - (posWidth / 2)
    myFont:DrawStringScaled(posText, centerX, baseY + lineHeight * 2, scaleX, scaleY, whiteColor, 0, true)
  end
    
  -- Mostrar contador de habitaciones con símbolo de mapa
  local roomText = string.format("Habitaciones visitadas: %d", dataCollected)
  local roomWidth = (myFont:GetStringWidth(roomText) * scaleX)
  centerX = (screenWidth / 2) - (roomWidth / 2)
  myFont:DrawStringScaled(roomText, centerX, baseY + lineHeight * 3, scaleX, scaleY, greenColor, 0, true)
  
  -- Dibujar ID y HP debajo de cada entidad
  if showEntityData then
    -- Configuración para el texto de entidades
    local entityScaleX = 0.4 -- Escala más pequeña para los textos de entidades
    local entityScaleY = 0.4
    
    -- Obtener todas las entidades de la habitación actual
    local room = Game():GetRoom()
    local entities = Isaac.GetRoomEntities()
    
    for _, entity in ipairs(entities) do
      -- Solo procesar jugadores y enemigos (NPCs)
      if entity:ToPlayer() or entity:ToNPC() then
        -- Obtener posición en la pantalla
        local pos = Isaac.WorldToScreen(entity.Position)
        local yOffset = 0 -- Ajusta este valor para posicionar el texto correctamente debajo de la entidad
        
        -- Obtener información
        local entityId = entity.InitSeed -- Usamos InitSeed como ID único
        local entityHP = 0
        
        -- Obtener HP según el tipo de entidad
        if entity:ToPlayer() then
          -- Para jugadores, calcular el HP total basado en todos los tipos de corazones
          local player = entity:ToPlayer()
          local redHearts = player:GetHearts() or 0
          local soulHearts = player:GetSoulHearts() or 0
          local boneHearts = player:GetBoneHearts() or 0
          
          -- Total de HP (cada unidad representa medio corazón)
          entityHP = math.floor((redHearts + soulHearts) / 2)
        else
          -- Para enemigos, usar el HitPoints normal
          entityHP = math.floor(entity.HitPoints or 0)
        end
        
        -- Formatear texto
        local entityText = string.format("ID:%d HP:%d", entityId % 10000, entityHP)
        
        -- Calcular ancho del texto para centrarlo
        local textWidth = myFont:GetStringWidth(entityText) * entityScaleX
        local textX = pos.X - (textWidth / 2)
        local textY = pos.Y + yOffset
        
        -- Color según tipo (jugadores en verde, enemigos en rojo)
        local textColor = entity:ToPlayer() and greenColor or redColor
        
        -- Renderizar texto centrado debajo de la entidad
        myFont:DrawStringScaled(entityText, textX, textY, entityScaleX, entityScaleY, textColor, 0, true)
      end
    end
  end
end

-- Función simple para recopilar datos al cambiar de habitación
function mod:onNewRoom()
  dataCollected = dataCollected + 1
  print("DataExtractorMod: Nueva habitación registrada. Total: " .. dataCollected)
end

-- Función para iniciar
function mod:onGameStart(isContinued)
  print("DataExtractorMod iniciado correctamente - Versión con fuente personalizada")
  dataCollected = 0
  
  -- Inicializar la fuente al comenzar el juego
  initializeFont()
end

-- Función para alternar la visualización de datos con una tecla
function mod:onKeyPress(entity, inputHook, buttonAction)
  -- Usar la tecla F2 para alternar la visualización (ButtonAction.ACTION_DEBUG)
  if buttonAction == ButtonAction.ACTION_DEBUG then
    showEntityData = not showEntityData
    print("DataExtractorMod: Visualización de ID/HP " .. (showEntityData and "activada" or "desactivada"))
    return true
  end
  return nil
end

-- Registrar callbacks
mod:AddCallback(ModCallbacks.MC_POST_RENDER, mod.onRender)
mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, mod.onNewRoom)
mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, mod.onGameStart)
mod:AddCallback(ModCallbacks.MC_INPUT_ACTION, mod.onKeyPress)

-- Mensaje de inicialización
print("DataExtractorMod: Versión con fuente personalizada cargada") 
