--[[
    DEM Data Manager - Versión Avanzada para ML/IA
    
    Este módulo gestiona la recopilación y persistencia de datos granulares
    para entrenar un modelo de aprendizaje automático que pueda jugar
    The Binding of Isaac.
    
    CARACTERÍSTICAS:
    - Recopilación de datos por frame (60 FPS)
    - Almacenamiento eficiente con compresión opcional
    - Tamaño de buffer ajustable basado en la complejidad de los datos
    - Rotación de archivos para evitar archivos demasiado grandes
    - Eliminación de datos duplicados
    
    FORMATO DE DATOS:
    Los datos se almacenan en formato JSON estructurado 
    para facilitar su procesamiento posterior.
]]

-- Registrar el mod
local DEM = RegisterMod("Data Event Manager", 1)

-- Cargar librería JSON
local json = require("json")

-- Configuración avanzada
local CONFIG = {
    DEBUG_MODE = true,       -- Activa mensajes de depuración
    BUFFER_SIZE = 300,       -- Mayor buffer para datos de ML (aprox. 5 segundos de juego a 60 FPS)
    FRAME_LIMIT = 60 * 30,   -- Guardar al menos cada 30 segundos (60 FPS * 30)
    DATA_COMPRESSION = false, -- Compresión de datos (desactivada por defecto)
    FILE_ROTATION = true,    -- Rotar archivos para evitar tamaño excesivo
    MAX_FILE_ENTRIES = 10000, -- Máximo de eventos por archivo antes de rotar
    SMART_BUFFERING = true,  -- Ajustar buffer dinámicamente
    TRACK_PERFORMANCE = true -- Monitorizar performance
}

-- Buffer temporal para almacenar múltiples eventos
local eventBuffer = {}

-- Contadores y estadísticas
local stats = {
    total_events_recorded = 0,
    total_events_saved = 0,
    largest_event_size = 0,
    save_operations = 0,
    current_file_index = 1,
    last_save_timestamp = 0,
    performance = {
        avg_processing_time = 0,
        processing_samples = 0
    }
}

-- Generar un timestamp único basado en el frame count
local function generateTimestamp()
    -- Usamos el frame count como timestamp ya que os.time() no está disponible
    local game = Game()
    if game then
        return game:GetFrameCount()
    end
    return 0
end

-- Crear un hash rápido para una cadena
local function quickHash(str)
    if not str then return 0 end
    
    local hash = 5381
    for i = 1, #str do
        hash = ((hash << 5) + hash) + string.byte(str, i)
        hash = hash & 0xFFFFFFFF -- Mantener dentro de 32 bits
    end
    return hash
end

-- Generar identificador para un evento
local function generateEventId(eventType, timestamp)
    local time = timestamp or generateTimestamp()
    -- Usar frame_count para mejorar la unicidad
    local random = Game():GetFrameCount() % 10000
    -- Sanitizar el tipo de evento
    eventType = string.gsub(eventType, "[^a-zA-Z0-9_]", "_")
    -- Crear un ID único más corto
    return "dem_" .. eventType .. "_" .. time .. "_" .. random
end

-- Calcular un hash para los datos (útil para eliminar duplicados)
local function calculateDataHash(data)
    if type(data) ~= "table" then
        return tostring(data)
    end
    
    -- Para datos más complejos, crear una representación simplificada para el hash
    local hashParts = {}
    
    -- Procesar solo campos clave para evitar overhead
    if data.position then
        table.insert(hashParts, math.floor(data.position.x or 0) .. "," .. math.floor(data.position.y or 0))
    end
    
    if data.frame_count then
        table.insert(hashParts, tostring(data.frame_count))
    end
    
    if data.event_type then
        table.insert(hashParts, data.event_type)
    end
    
    if data.timestamp then
        table.insert(hashParts, tostring(data.timestamp))
    end
    
    -- Crear una cadena para el hash
    local hashStr = table.concat(hashParts, "_")
    return quickHash(hashStr)
end

-- Crear carpeta de datos si no existe
local function ensureDataSaving()
    -- En Isaac no podemos crear carpetas, solo guardar un archivo usando SaveModData
    if CONFIG.DEBUG_MODE then
        Isaac.DebugString("DEM: Sistema de guardado mejorado para recopilación ML")
        Isaac.DebugString("DEM: Los datos se guardarán usando SaveModData")
        Isaac.DebugString("DEM: El archivo se escribirá en la carpeta data/dem/ del juego")
    end
    
    -- Intentar guardar un archivo de prueba usando la API de Isaac
    local success = pcall(function()
        Isaac.SaveModData(DEM, "test")
        
        -- Intentar cargar para confirmar la escritura
        local test_data = Isaac.LoadModData(DEM)
        if test_data and test_data == "test" then
            if CONFIG.DEBUG_MODE then
                Isaac.DebugString("DEM: ¡ÉXITO! Archivo de prueba guardado y leído correctamente.")
            end
            return true
        else
            if CONFIG.DEBUG_MODE then
                Isaac.DebugString("DEM: ¡ERROR! No se pudo leer el archivo de prueba.")
            end
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
    
    -- Intentar cargar las estadísticas anteriores
    local savedStats = Isaac.LoadModData(DEM)
    if savedStats and savedStats:sub(1, 1) == "{" then
        local success, loadedStats = pcall(json.decode, savedStats)
        if success and loadedStats and loadedStats.stats then
            stats = loadedStats.stats
            if CONFIG.DEBUG_MODE then
                Isaac.DebugString("DEM: Estadísticas cargadas. Total de eventos: " .. stats.total_events_saved)
            end
        end
    end
    
    -- Mensaje de inicialización
    if CONFIG.DEBUG_MODE then
        Isaac.DebugString("DEM: Data Manager ML inicializado")
        Isaac.DebugString("DEM: Buffer configurado para " .. CONFIG.BUFFER_SIZE .. " eventos")
        Isaac.DebugString("DEM: Se guardarán datos al menos cada " .. (CONFIG.FRAME_LIMIT / 60) .. " segundos")
    end
end

-- Sanitizar strings para JSON
local function sanitizeString(str)
    if not str then return "" end
    -- Reemplazar comillas y caracteres especiales
    str = string.gsub(str, '\\', '\\\\')
    str = string.gsub(str, '"', '\\"')
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
    elseif type(value) == "nil" then
        return "null"
    elseif type(value) == "table" then
        -- Detectar si la tabla es un array
        local isArray = true
        local maxIndex = 0
        
        for k, v in pairs(value) do
            if type(k) ~= "number" or k <= 0 or math.floor(k) ~= k then
                isArray = false
                break
            end
            maxIndex = math.max(maxIndex, k)
        end
        
        -- Si la tabla tiene índices no consecutivos, no es un array
        if isArray and maxIndex > 0 then
            for i = 1, maxIndex do
                if value[i] == nil then
                    isArray = false
                    break
                end
            end
        end
        
        -- Si la tabla está vacía, devolverla como {} sin formato
        if next(value) == nil then
            return isArray and "[]" or "{}"
        end
        
        local inner_indent = indent + 1
        local inner_indentStr = string.rep("  ", inner_indent)
        local tableJson
        
        if isArray then
            tableJson = "[\n"
            for i = 1, maxIndex do
                if i > 1 then
                    tableJson = tableJson .. ",\n"
                end
                tableJson = tableJson .. inner_indentStr .. valueToJson(value[i], inner_indent)
            end
            tableJson = tableJson .. "\n" .. indentStr .. "]"
        else
            tableJson = "{\n"
            local isFirst = true
            
            for k, v in pairs(value) do
                if not isFirst then
                    tableJson = tableJson .. ",\n"
                else
                    isFirst = false
                end
                
                tableJson = tableJson .. inner_indentStr .. '"' .. sanitizeString(tostring(k)) .. '": ' .. valueToJson(v, inner_indent)
            end
            
            tableJson = tableJson .. "\n" .. indentStr .. "}"
        end
        
        return tableJson
    else
        return '"unknown"'
    end
end

-- Verificar si un evento es similar a otro reciente (para eliminar duplicados)
local function isDuplicateEvent(eventType, eventData)
    -- Solo aplicar a eventos de frame y similares
    if eventType ~= "frame_state" then
        return false
    end
    
    -- Si no hay suficientes eventos en el buffer, no es duplicado
    if #eventBuffer < 5 then
        return false
    end
    
    -- Calcular hash para los nuevos datos
    local newHash = calculateDataHash(eventData)
    
    -- Comprobar últimos eventos del mismo tipo
    local duplicateCount = 0
    local recentCount = 0
    
    for i = #eventBuffer, math.max(1, #eventBuffer - 10), -1 do
        local event = eventBuffer[i]
        if type(event) == "table" and event.event_type == eventType then
            recentCount = recentCount + 1
            
            -- Calcular hash para el evento existente
            local existingHash = calculateDataHash(event.data)
            
            -- Si los hashes son muy similares, considerar duplicado
            if newHash == existingHash then
                duplicateCount = duplicateCount + 1
            end
            
            -- Si hemos encontrado al menos 2 duplicados en 5 eventos recientes, es duplicado
            if duplicateCount >= 2 and recentCount >= 5 then
                return true
            end
        end
    end
    
    return false
end

-- Obtener el nombre de archivo basado en rotación
local function getDataFileName()
    if not CONFIG.FILE_ROTATION then
        return "save1.dat"
    else
        return "save" .. stats.current_file_index .. ".dat"
    end
end

-- Rotar archivo si es necesario
local function rotateFileIfNeeded()
    if not CONFIG.FILE_ROTATION then
        return
    end
    
    -- Si el número de eventos excede el máximo, rotar a un nuevo archivo
    if stats.total_events_saved % CONFIG.MAX_FILE_ENTRIES == 0 and stats.total_events_saved > 0 then
        stats.current_file_index = stats.current_file_index + 1
        
        if CONFIG.DEBUG_MODE then
            Isaac.DebugString("DEM: Rotando a nuevo archivo: save" .. stats.current_file_index .. ".dat")
        end
    end
end

-- Comprimir JSON si está habilitado
local function compressIfEnabled(jsonData)
    if not CONFIG.DATA_COMPRESSION then
        return jsonData
    end
    
    -- Implementación básica de compresión con método simple
    -- En la API de Isaac no hay compresión real, esta es una simulación simple
    -- Eliminar espacios y saltos de línea
    local compressed = jsonData:gsub("[ \t\n\r]+", "")
    
    if CONFIG.DEBUG_MODE then
        local savingRatio = math.floor((1 - (string.len(compressed) / string.len(jsonData))) * 100)
        Isaac.DebugString("DEM: Compresión aplicada. Ahorro: " .. savingRatio .. "%")
    end
    
    return compressed
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
    
    -- Ordenar eventos por timestamp
    table.sort(eventBuffer, function(a, b) 
        return a.timestamp < b.timestamp 
    end)
    
    -- Construir objeto con metadatos
    local dataPackage = {
        metadata = {
            version = "2.0",
            timestamp = generateTimestamp(),
            event_count = #eventBuffer,
            file_id = stats.current_file_index,
            is_ml_data = true
        },
        stats = stats,
        events = eventBuffer
    }
    
    -- Convertir a JSON con formato
    local bufferJson = valueToJson(dataPackage)
    
    -- Comprimir si está habilitado
    bufferJson = compressIfEnabled(bufferJson)
    
    -- Guardar el buffer usando SaveModData
    local startTime = Isaac.GetTime()
    local success = pcall(function()
        -- Rotar archivo si es necesario
        rotateFileIfNeeded()
        
        -- Guardar en el archivo correspondiente
        local fileName = getDataFileName()
        Isaac.SaveModData(DEM, bufferJson)
        
        if CONFIG.DEBUG_MODE then
            local saveTime = Isaac.GetTime() - startTime
            Isaac.DebugString("DEM: Buffer de " .. #eventBuffer .. " eventos guardado en " .. saveTime .. "ms")
            Isaac.DebugString("DEM: Tamaño: " .. string.len(bufferJson) .. " bytes (Archivo: " .. fileName .. ")")
        end
        
        -- Actualizar estadísticas
        stats.total_events_saved = stats.total_events_saved + #eventBuffer
        stats.save_operations = stats.save_operations + 1
        stats.last_save_timestamp = generateTimestamp()
        
        -- Limpiar el buffer después de guardar exitosamente
        eventBuffer = {}
        
        -- Ajustar buffer dinámicamente si está habilitado
        if CONFIG.SMART_BUFFERING then
            -- Ajustar el tamaño del buffer según el rendimiento
            if saveTime > 200 then -- Si tarda más de 200ms, reducir buffer
                CONFIG.BUFFER_SIZE = math.max(60, CONFIG.BUFFER_SIZE * 0.8)
                if CONFIG.DEBUG_MODE then
                    Isaac.DebugString("DEM: Buffer reducido a " .. CONFIG.BUFFER_SIZE .. " eventos por rendimiento")
                end
            elseif saveTime < 50 and #eventBuffer >= CONFIG.BUFFER_SIZE * 0.9 then
                -- Si es rápido y estamos cerca del límite, aumentar
                CONFIG.BUFFER_SIZE = math.min(1000, CONFIG.BUFFER_SIZE * 1.2)
                if CONFIG.DEBUG_MODE then
                    Isaac.DebugString("DEM: Buffer aumentado a " .. CONFIG.BUFFER_SIZE .. " eventos")
                end
            end
        end
        
        return true
    end)
    
    if not success and CONFIG.DEBUG_MODE then
        Isaac.DebugString("DEM: Error al guardar el buffer de eventos")
    end
    
    return success
end

-- Función pública para registrar eventos
local function recordEvent(eventType, eventData)
    -- Medir tiempo de procesamiento para estadísticas
    local startTime = nil
    if CONFIG.TRACK_PERFORMANCE then
        startTime = Isaac.GetTime()
    end
    
    -- Validar el tipo de evento
    if not eventType or eventType == "" then
        if CONFIG.DEBUG_MODE then
            Isaac.DebugString("DEM: Error - Tipo de evento vacío")
        end
        return false
    end
    
    -- Evitar duplicados para eventos de frame (optimización ML)
    if CONFIG.SMART_BUFFERING and isDuplicateEvent(eventType, eventData) then
        -- Eventos duplicados en frames cercanos, ignorar
        return true
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
        -- Añadir datos básicos del juego (más compactos para ML)
        game_state = {
            seed = game:GetSeeds():GetStartSeed(),
            level = level:GetStage(),
            room_id = level:GetCurrentRoomDesc().SafeGridIndex,
            frame = game:GetFrameCount()
        }
    }
    
    -- Para eventos de frame, reducir información duplicada
    if eventType == "frame_state" and eventData then
        -- Ya tenemos estos datos en eventData, no duplicarlos
        data.game_state = nil
    end
    
    -- Agregar el evento al buffer
    table.insert(eventBuffer, data)
    stats.total_events_recorded = stats.total_events_recorded + 1
    
    -- Medir tamaño para estadísticas
    local eventSize = string.len(valueToJson(data))
    stats.largest_event_size = math.max(stats.largest_event_size, eventSize)
    
    -- Medir tiempo de procesamiento
    if CONFIG.TRACK_PERFORMANCE and startTime then
        local processingTime = Isaac.GetTime() - startTime
        
        -- Actualizar promedio de tiempo de procesamiento
        stats.performance.avg_processing_time = 
            (stats.performance.avg_processing_time * stats.performance.processing_samples + processingTime) / 
            (stats.performance.processing_samples + 1)
        stats.performance.processing_samples = stats.performance.processing_samples + 1
    end
    
    if CONFIG.DEBUG_MODE and (eventType ~= "frame_state" or game:GetFrameCount() % 60 == 0) then
        -- Solo mostrar log para eventos importantes o cada 60 frames para no saturar
        Isaac.DebugString("DEM: Evento '" .. eventType .. "' agregado. Eventos en buffer: " .. #eventBuffer .. "/" .. CONFIG.BUFFER_SIZE)
    end
    
    -- Guardar si se alcanza alguna condición de guardado
    if #eventBuffer >= CONFIG.BUFFER_SIZE or 
       (game:GetFrameCount() - stats.last_save_timestamp > CONFIG.FRAME_LIMIT) then
        if CONFIG.DEBUG_MODE then
            if #eventBuffer >= CONFIG.BUFFER_SIZE then
                Isaac.DebugString("DEM: Buffer lleno, guardando eventos...")
            else
                Isaac.DebugString("DEM: Tiempo límite alcanzado, guardando eventos...")
            end
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
        local frame = Game():GetFrameCount()
        -- Guardar cada 600 frames (aproximadamente 10 segundos a 60 FPS)
        if frame % 600 == 0 and #eventBuffer > 0 then
            if CONFIG.DEBUG_MODE then
                Isaac.DebugString("DEM: Guardado periódico, " .. #eventBuffer .. " eventos pendientes")
            end
            saveEventBuffer()
        end
        
        -- Generar estadísticas de rendimiento periódicamente
        if CONFIG.TRACK_PERFORMANCE and frame % 1800 == 0 then -- Cada 30 segundos
            local memUsage = collectgarbage("count") -- Obtener uso de memoria en KB
            
            recordEvent("performance_stats", {
                avg_processing_time = stats.performance.avg_processing_time,
                buffer_size = CONFIG.BUFFER_SIZE,
                memory_usage_kb = memUsage,
                events_recorded = stats.total_events_recorded,
                events_saved = stats.total_events_saved,
                largest_event_size = stats.largest_event_size
            })
            
            if CONFIG.DEBUG_MODE then
                Isaac.DebugString("DEM: Stats - Tiempo promedio: " .. string.format("%.2f", stats.performance.avg_processing_time) .. "ms, Memoria: " .. memUsage .. "KB")
            end
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
    saveEvents = saveEventBuffer,
    
    -- Obtener estadísticas
    getStats = function()
        return stats
    end,
    
    -- Utilitarios para el módulo principal
    utils = {
        generateEventId = generateEventId,
        calculateDataHash = calculateDataHash,
        valueToJson = valueToJson
    },
    
    -- Añadir interfaz para controlar al personaje programáticamente
    control = {
        controller = nil, -- Referencia al controlador del jugador
        
        -- Establecer la referencia al controlador
        setController = function(controller_ref)
            DataManager.control.controller = controller_ref
            Isaac.DebugString("DataManager: Controlador de jugador registrado")
        end,
        
        -- Procesar comandos recibidos desde el servidor web
        processCommand = function(command)
            if not DataManager.control.controller then
                Isaac.DebugString("Error: No hay controlador de jugador registrado")
                return false
            end
            
            local controller = DataManager.control.controller
            
            -- Verificar que el controlador está activo y en modo IA
            if not controller.config.enabled or not controller.config.ai_control then
                controller.config.enabled = true
                controller.config.ai_control = true
                Isaac.DebugString("DataManager: Activando modo IA para procesar comando")
            end
            
            -- Procesar el comando
            if command.type == "movement" then
                -- Movimiento: {type: "movement", direction: "up/down/left/right", value: 0-1}
                if command.direction and command.value ~= nil then
                    return controller:move(command.direction, command.value)
                end
            elseif command.type == "shooting" then
                -- Disparo: {type: "shooting", direction: "up/down/left/right", value: 0-1}
                if command.direction and command.value ~= nil then
                    return controller:shoot(command.direction, command.value)
                end
            elseif command.type == "toggle_ai" then
                -- Alternar modo IA: {type: "toggle_ai"}
                return controller:toggleAI()
            elseif command.type == "clear" then
                -- Limpiar todas las entradas: {type: "clear"}
                controller:clearInputs()
                return true
            end
            
            return false
        end,
        
        -- Realizar una acción compleja (secuencia de movimientos)
        executeAction = function(actionName, params)
            if not DataManager.control.controller then
                return false
            end
            
            local controller = DataManager.control.controller
            
            -- Acciones predefinidas
            if actionName == "move_to_item" then
                -- TODO: Implementar lógica para moverse hacia un objeto cercano
                return true
            elseif actionName == "avoid_enemy" then
                -- TODO: Implementar lógica para evitar enemigo cercano
                return true
            elseif actionName == "clear_room" then
                -- TODO: Implementar lógica para limpiar la habitación
                return true
            end
            
            return false
        end
    }
}

-- Función para registrar un evento de control de IA
function DataManager.recordControlEvent(action, result)
    DataManager.recordEvent("ai_control", {
        action = action,
        result = result,
        timestamp = Game():GetFrameCount()
    })
end

-- Función para procesar comandos recibidos desde el servidor web
function DataManager.processCommandsFromServer()
    -- Necesitamos acceder al mod global o pasar la referencia
    local mod = DataManager.MOD_REF
    
    -- Si no tenemos referencia al mod, no podemos continuar
    if not mod then
        Isaac.DebugString("DataManager: No hay referencia al mod para procesar comandos")
        return
    end
    
    -- Verificar si el archivo existe
    if not Isaac.HasModData(mod) then
        return
    end
    
    -- Cargar los comandos
    local cmdData = Isaac.LoadModData(mod)
    if not cmdData or cmdData == "" then
        return
    end
    
    -- Parsear los comandos (formato JSON)
    local success, commands = pcall(json.decode, cmdData)
    if not success or not commands then
        Isaac.DebugString("DataManager: Error al decodificar comandos: " .. tostring(commands))
        return
    end
    
    -- Procesar cada comando
    local results = {}
    for i, cmd in ipairs(commands) do
        local result = DataManager.control.processCommand(cmd)
        table.insert(results, {
            id = cmd.id or i,
            success = result
        })
        
        -- Registrar el evento de control
        DataManager.recordControlEvent(cmd, result)
    end
    
    -- Limpiar el archivo de comandos (escribir resultado)
    local resultJson = json.encode(results)
    Isaac.SaveModData(mod, resultJson)
    
    -- Registrar la recepción de comandos
    if #commands > 0 then
        Isaac.DebugString("DataManager: Procesados " .. #commands .. " comandos desde el servidor")
    end
end

-- Añadir función de procesamiento de comandos al update
local originalUpdateFunction = DataManager.update
DataManager.update = function()
    -- Llamar a la función original
    originalUpdateFunction()
    
    -- Procesar comandos desde el servidor
    DataManager.processCommandsFromServer()
end

local DataManager = {
    -- Configuración
    config = {
        saveInterval = 60 * 5, -- Cada 5 segundos (60 fps * 5)
        maxEventsPerSave = 300, -- Número máximo de eventos por archivo
        compressionEnabled = true, -- Comprimir datos
        detailedDebug = false, -- Debug detallado
        dedicatedFiles = true -- Usar archivos dedicados para ML
    },
    
    -- Estado interno
    internal = {
        eventBuffer = {},
        totalEventsRecorded = 0,
        totalEventsSaved = 0,
        largestEventSize = 0,
        lastSaveTime = 0,
        fileIdCounter = 1,
        saveOperations = 0,
        modInitialized = false
    },
    
    -- Referencia al mod para acceso a SaveModData
    MOD_REF = nil,
    
    -- Versión del DataManager
    VERSION = "2.0"
}

-- Función para establecer la referencia al mod
function DataManager.setModReference(mod)
    DataManager.MOD_REF = mod
    return DataManager
end

return DataManager 