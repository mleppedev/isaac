-- main.lua
-- Mod para extraer datos de The Binding of Isaac
-- Versión extremadamente simplificada 

-- Obtener referencia al mod
local mod = RegisterMod("DataExtractorMod", 1)

-- Variables globales
local dataCollected = 0

-- Función para obtener timestamp actual
local function getTimestamp()
  return os.date("%Y-%m-%dT%H:%M:%S")
end

-- Función extremadamente simplificada para mostrar información básica
function mod:onRender()
  -- Obtener jugador
  local player = Isaac.GetPlayer(0)
  if not player then return end
  
  -- Obtener dimensiones de la pantalla
  local screenWidth = Isaac.GetScreenWidth() or 960
  local screenHeight = Isaac.GetScreenHeight() or 540
  
  -- Configuración de texto
  local scale = 0.6  -- Letra considerablemente más pequeña
  local lineHeight = 10  -- Reducir también el espacio entre líneas
  local baseY = 100  -- Ajustar posición Y inicial
  
  -- Mostrar texto simple sin importar nada más
  local text = "DATA EXTRACTOR MOD - Información básica:"
  -- Calcular posición X para centrar (ajuste para escala reducida)
  local textWidth = #text * 5 * scale  -- Reducir el ancho estimado por carácter
  local centerX = (screenWidth / 2) - (textWidth / 2)
  -- Renderizar texto centrado
  Isaac.RenderText(text, centerX, baseY, 1, 0, 0, 1, scale)
  
  -- Mostrar vida del jugador
  local health = player.Hearts or 0
  local maxHealth = player.MaxHearts or 0
  local coins = player.Coins or 0
  local bombs = player.Bombs or 0
  local keys = player.Keys or 0
  
  local healthText = string.format("Vida: %d/%d | Monedas: %d | Bombas: %d | Llaves: %d", 
                                  health/2, maxHealth/2, coins, bombs, keys)
  -- Centrar este texto también
  textWidth = #healthText * 5 * scale
  centerX = (screenWidth / 2) - (textWidth / 2)
  Isaac.RenderText(healthText, centerX, baseY + lineHeight, 1, 1, 1, 1, scale)
  
  -- Mostrar posición del jugador si está disponible
  if player.Position then
    local posX = player.Position.X or 0
    local posY = player.Position.Y or 0
    local posText = string.format("Posición: (%.1f, %.1f)", posX, posY)
    -- Centrar este texto también
    textWidth = #posText * 5 * scale
    centerX = (screenWidth / 2) - (textWidth / 2)
    Isaac.RenderText(posText, centerX, baseY + lineHeight * 2, 1, 1, 1, 1, scale)
  end
  
  -- Mostrar estadísticas básicas
  if player.Damage then
    local damage = player.Damage or 0
    local speed = player.MoveSpeed or 0
    local statsText = string.format("Daño: %.1f | Velocidad: %.1f", damage, speed)
    -- Centrar este texto también
    textWidth = #statsText * 5 * scale
    centerX = (screenWidth / 2) - (textWidth / 2)
    Isaac.RenderText(statsText, centerX, baseY + lineHeight * 3, 1, 1, 1, 1, scale)
  end
  
  -- Mostrar contador de habitaciones
  local roomText = string.format("Habitaciones visitadas: %d", dataCollected)
  textWidth = #roomText * 5 * scale
  centerX = (screenWidth / 2) - (textWidth / 2)
  Isaac.RenderText(roomText, centerX, baseY + lineHeight * 4, 0, 1, 0, 1, scale)
  
  -- Añadir texto pequeño con fecha y hora
  local timeText = "Timestamp: " .. getTimestamp()
  textWidth = #timeText * 5 * scale
  centerX = (screenWidth / 2) - (textWidth / 2)
  Isaac.RenderText(timeText, centerX, baseY + lineHeight * 5, 0.7, 0.7, 0.7, 1, scale * 0.8)
end

-- Función simple para recopilar datos al cambiar de habitación
function mod:onNewRoom()
  dataCollected = dataCollected + 1
  print("DataExtractorMod: Nueva habitación registrada. Total: " .. dataCollected)
end

-- Función simple para iniciar
function mod:onGameStart(isContinued)
  print("DataExtractorMod iniciado correctamente - Versión ultra-simplificada")
  dataCollected = 0
end

-- Registrar callbacks
mod:AddCallback(ModCallbacks.MC_POST_RENDER, mod.onRender)
mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, mod.onNewRoom)
mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, mod.onGameStart)

-- Mensaje de inicialización
print("DataExtractorMod: Versión ultra-simplificada cargada") 
