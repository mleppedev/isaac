-- main.lua
-- Mod para extraer datos de The Binding of Isaac
-- Versión con fuente personalizada

-- Obtener referencia al mod
local mod = RegisterMod("DataExtractorMod", 1)

-- Variables globales
local dataCollected = 0
local myFont = nil -- Variable para guardar nuestra fuente personalizada

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

-- Registrar callbacks
mod:AddCallback(ModCallbacks.MC_POST_RENDER, mod.onRender)
mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, mod.onNewRoom)
mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, mod.onGameStart)

-- Mensaje de inicialización
print("DataExtractorMod: Versión con fuente personalizada cargada") 
