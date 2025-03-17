--[[
    DEM Data Manager - Ultra Simplificado
    Este módulo gestiona la persistencia de datos del juego.
    Solo se encarga de guardar archivos JSON localmente para que el servidor los lea directamente.
    
    RUTAS DE GUARDADO:
    El archivo se guarda mediante Isaac.SaveModData() en:
    
    Ruta real encontrada:
    - D:\SteamLibrary\steamapps\common\The Binding of Isaac Rebirth\data\dem\save1.dat
    
    Documentación indica que debería guardar en:
    - Windows: Documents\My Games\Binding of Isaac Repentance+\Data Event Manager.dat
    - Mac/Linux: ~/.local/share/Binding of Isaac Repentance+/Data Event Manager.dat
    
    NOTA: Los datos se guardan en la carpeta "data" dentro de la instalación del juego,
    NO en el directorio de documentos del usuario como se pensaba originalmente.
]]

-- Registrar el mod
local DEM = RegisterMod("Data Event Manager", 1)

-- Configuración básica
local CONFIG = {
    DEBUG_MODE = true,  -- Activa mensajes de depuración
    BUFFER_SIZE = 5     -- Número máximo de eventos antes de guardar todo el buffer
}

-- Buffer temporal para almacenar múltiples eventos
local eventBuffer = {}

-- Generar un timestamp único basado en el frame count
local function generateTimestamp()
    -- Usamos el frame count como timestamp ya que os.time() no está disponible
    local game = Game()
    if game then
        return game:GetFrameCount()
    end
    return 0
end

-- Crear carpeta de datos si no existe
local function ensureDataSaving()
    -- En Isaac no podemos crear carpetas, solo guardar un archivo usando SaveModData
    if CONFIG.DEBUG_MODE then
        Isaac.DebugString("DEM: Los datos se guardarán usando SaveModData")
        Isaac.DebugString("DEM: El archivo se escribirá como save1.dat")
        Isaac.DebugString("DEM: En: " .. "D:/SteamLibrary/steamapps/common/The Binding of Isaac Rebirth/data/DEM/")
        
        -- Más información sobre rutas
        Isaac.DebugString("DEM: AVISO: Los datos se guardan en la carpeta del juego, NO en Documents")
        Isaac.DebugString("DEM: AVISO: Comprobado en búsqueda de archivos")
    end
    
    -- Intentar guardar un archivo de prueba usando la API de Isaac
    local success = pcall(function()
        Isaac.SaveModData(DEM, "test")
        
        -- Intentar cargar para confirmar la escritura
        local test_data = Isaac.LoadModData(DEM)
        if test_data and test_data == "test" then
            Isaac.DebugString("DEM: ¡ÉXITO! Archivo de prueba guardado y leído correctamente.")
            return true
        else
            Isaac.DebugString("DEM: ¡ERROR! No se pudo leer el archivo de prueba.")
            return false
        end
    end)
    
    if CONFIG.DEBUG_MODE then
        if success then
            Isaac.DebugString("DEM: Prueba de escritura exitosa")
        else
            Isaac.DebugString("DEM: ADVERTENCIA - No se pudo verificar la escritura de datos")
        end
    end
    
    -- Limpiar el buffer al inicio
    eventBuffer = {}
    
    return success
end

-- Inicializar
local function initialize()
    -- Verificar que podemos escribir datos
    ensureDataSaving()
    
    -- Mensaje de inicialización
    if CONFIG.DEBUG_MODE then
        Isaac.DebugString("DEM: Data Manager inicializado")
    end
end

-- Generar identificador para un evento
local function generateEventId(eventType, timestamp)
    local time = timestamp or generateTimestamp()
    -- Usar frame_count para mejorar la unicidad
    local random = Game():GetFrameCount() % 10000
    -- Sanitizar el tipo de evento (por si acaso)
    eventType = string.gsub(eventType, "[^a-zA-Z0-9_]", "_")
    return "dem_" .. eventType .. "_" .. time .. "_" .. random
end

-- Sanitizar strings para JSON
local function sanitizeString(str)
    if not str then return "" end
    -- Reemplazar comillas y caracteres especiales
    str = string.gsub(str, '"', '\\"')
    str = string.gsub(str, '\\', '\\\\')
    str = string.gsub(str, '\n', '\\n')
    str = string.gsub(str, '\r', '\\r')
    str = string.gsub(str, '\t', '\\t')
    return str
end

-- Construir JSON para un valor, con opción de indentación
local function valueToJson(value, indent)
    indent = indent or 0  -- Nivel de indentación
    local indentStr = string.rep("  ", indent)  -- 2 espacios por nivel
    
    if type(value) == "string" then
        return '"' .. sanitizeString(value) .. '"'
    elseif type(value) == "number" then
        return tostring(value)
    elseif type(value) == "boolean" then
        return value and "true" or "false"
    elseif type(value) == "table" then
        -- Si la tabla está vacía, devolverla como {} sin formato
        if next(value) == nil then
            return "{}"
        end
        
        local inner_indent = indent + 1
        local inner_indentStr = string.rep("  ", inner_indent)
        
        local tableJson = "{\n"
        local isFirst = true
        
        for k, v in pairs(value) do
            if not isFirst then
                tableJson = tableJson .. ",\n"
            else
                isFirst = false
            end
            
            tableJson = tableJson .. inner_indentStr .. '"' .. sanitizeString(k) .. '": ' .. valueToJson(v, inner_indent)
        end
        
        tableJson = tableJson .. "\n" .. indentStr .. "}"
        return tableJson
    else
        return '"unknown"'
    end
end

-- Guardar el buffer completo de eventos
local function saveEventBuffer()
    -- Si no hay eventos en el buffer, no hacemos nada
    if #eventBuffer == 0 then
        if CONFIG.DEBUG_MODE then
            Isaac.DebugString("DEM: No hay eventos para guardar")
        end
        return false
    end
    
    -- Ordenar eventos por timestamp antes de guardar
    -- Extraer eventos y su timestamp para ordenarlos
    local eventsForSorting = {}
    for i, eventJson in ipairs(eventBuffer) do
        -- Intentar extraer el timestamp
        local timestamp = 0
        local timestampPattern = '"timestamp":%s*(%d+)'
        local found = eventJson:match(timestampPattern)
        
        if found then
            timestamp = tonumber(found)
        end
        
        table.insert(eventsForSorting, {
            json = eventJson,
            timestamp = timestamp or 0
        })
    end
    
    -- Ordenar eventos por timestamp
    table.sort(eventsForSorting, function(a, b) 
        return a.timestamp < b.timestamp 
    end)
    
    -- Construir el JSON final con los eventos ordenados
    local bufferJson = "[\n"
    for i, eventData in ipairs(eventsForSorting) do
        if i > 1 then
            bufferJson = bufferJson .. ",\n"
        end
        -- Añadir indentación de 2 espacios para cada línea de eventos
        local indentedJson = "  " .. eventData.json:gsub("\n", "\n  ")
        bufferJson = bufferJson .. indentedJson
    end
    bufferJson = bufferJson .. "\n]"
    
    -- Guardar el buffer usando SaveModData
    local success = pcall(function()
        Isaac.SaveModData(DEM, bufferJson)
        
        if CONFIG.DEBUG_MODE then
            Isaac.DebugString("DEM: Buffer de " .. #eventBuffer .. " eventos guardado correctamente")
            Isaac.DebugString("DEM: Tamaño total: " .. string.len(bufferJson) .. " bytes")
            Isaac.DebugString("DEM: Archivo guardado en D:/SteamLibrary/steamapps/common/The Binding of Isaac Rebirth/data/dem/save1.dat")
            Isaac.DebugString("DEM: Datos ordenados por timestamp")
        end
        
        -- Limpiar el buffer después de guardar exitosamente
        eventBuffer = {}
        
        return true
    end)
    
    if not success and CONFIG.DEBUG_MODE then
        Isaac.DebugString("DEM: Error al guardar el buffer de eventos")
    end
    
    return success
end

-- Función pública para registrar eventos
local function recordEvent(eventType, eventData)
    -- Validar el tipo de evento
    if not eventType or eventType == "" then
        if CONFIG.DEBUG_MODE then
            Isaac.DebugString("DEM: Error - Tipo de evento vacío")
        end
        return false
    end
    
    -- Obtener datos del juego
    local timestamp = generateTimestamp()
    local game = Game()
    local level = game:GetLevel()
    local room = game:GetRoom()
    
    -- Crear estructura del evento
    local data = {
        event_type = eventType,
        timestamp = timestamp,
        event_id = generateEventId(eventType, timestamp),
        data = eventData or {},
        game_data = {
            seed = game:GetSeeds():GetStartSeed(),
            level = level:GetStage(),
            stage_type = level:GetStageType(),
            room_id = level:GetCurrentRoomDesc().SafeGridIndex,
            room_type = room:GetType(),
            frame_count = game:GetFrameCount()
        }
    }
    
    -- Convertir a JSON usando valueToJson, que ahora tiene formato
    local eventJson = valueToJson(data)
    
    -- Agregar el evento al buffer
    table.insert(eventBuffer, eventJson)
    
    if CONFIG.DEBUG_MODE then
        Isaac.DebugString("DEM: Evento '" .. eventType .. "' agregado al buffer. ID: " .. data.event_id)
        Isaac.DebugString("DEM: Eventos en buffer: " .. #eventBuffer .. "/" .. CONFIG.BUFFER_SIZE)
    end
    
    -- Si el buffer alcanzó el tamaño máximo, guardarlo
    if #eventBuffer >= CONFIG.BUFFER_SIZE then
        if CONFIG.DEBUG_MODE then
            Isaac.DebugString("DEM: Buffer lleno, guardando eventos...")
        end
        saveEventBuffer()
    end
    
    return true
end

-- Registrar callbacks para eventos automáticos
local function registerCallbacks()
    -- Cuando comienza el juego
    function DEM:onGameStart(isContinued)
        recordEvent("game_start", {
            continued = isContinued,
            player_type = Isaac.GetPlayer(0):GetPlayerType(),
            hard_mode = Game().Difficulty == Difficulty.DIFFICULTY_HARD
        })
    end
    DEM:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, DEM.onGameStart)
    
    -- Nueva habitación
    function DEM:onNewRoom()
        recordEvent("room_entered", {
            room_type = Game():GetRoom():GetType(),
            room_shape = Game():GetRoom():GetRoomShape()
        })
    end
    DEM:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, DEM.onNewRoom)
    
    -- Al salir del juego
    function DEM:onGameExit()
        recordEvent("game_exit", {
            timestamp = generateTimestamp()
        })
        
        -- Guardar todos los eventos pendientes al salir
        saveEventBuffer()
        
        if CONFIG.DEBUG_MODE then
            Isaac.DebugString("DEM: Juego terminado, eventos guardados")
        end
    end
    DEM:AddCallback(ModCallbacks.MC_PRE_GAME_EXIT, DEM.onGameExit)
    
    -- Cada cierto número de frames, para guardar periódicamente
    function DEM:onUpdate()
        -- Guardar cada 600 frames (aproximadamente 20 segundos a 30 FPS)
        if Game():GetFrameCount() % 600 == 0 and #eventBuffer > 0 then
            if CONFIG.DEBUG_MODE then
                Isaac.DebugString("DEM: Guardado periódico, " .. #eventBuffer .. " eventos pendientes")
            end
            saveEventBuffer()
        end
    end
    DEM:AddCallback(ModCallbacks.MC_POST_UPDATE, DEM.onUpdate)
end

-- Inicializar el módulo
initialize()
registerCallbacks()

-- Exponer la API
return {
    -- Registrar evento manualmente
    recordEvent = recordEvent,
    
    -- Obtener configuración
    getConfig = function()
        return CONFIG
    end,
    
    -- Establecer configuración
    setConfig = function(key, value)
        if CONFIG[key] ~= nil then
            CONFIG[key] = value
            return true
        end
        return false
    end,
    
    -- Guardar eventos manualmente
    saveEvents = saveEventBuffer
} 