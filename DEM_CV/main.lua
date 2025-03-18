--[[
    Data Event Manager - Versión CV (Computer Vision)
    
    Esta versión del mod está diseñada para recibir inputs externos
    desde un sistema de visión por computadora y aprendizaje por refuerzo
    que controle al jugador.
    
    FUNCIONALIDADES:
    - Recepción de comandos de control desde un servidor externo
    - Aplicación de inputs al jugador basados en decisiones de IA
    - Comunicación bidireccional para entrenamiento por refuerzo
]]

-- Registrar el mod
local DEM = RegisterMod("Data Event Manager - CV", 1)

-- Cargar librería JSON
local json = require("json")

-- Variables de estado
local dataCollectionEnabled = true  -- Recopilación de datos habilitada por defecto
local playerVelocity = {X = 0, Y = 0}  -- Para calcular velocidad real del jugador
local lastPosition = {X = 0, Y = 0}  -- Última posición conocida
local lastTimestamp = 0  -- Para cálculos de tiempo
local gameTicks = 0  -- Contador de ticks del juego
local currentRoomLayout = nil  -- Diseño actual de la habitación
local lastFrameProcessed = 0  -- Último frame procesado
local processingFrequency = 1  -- Capturar cada frame (1 = todos)
local lastActionReceived = nil  -- Última acción recibida
local lastActionTimestamp = 0  -- Timestamp de la última acción

-- Configuración de servidor
local SERVER_PORT = 12345  -- Puerto para comunicación con agente de RL

-- Debug
local DEBUG_MODE = true  -- Habilitar mensajes de depuración

-- Módulo DataManager (control de datos)
local DataManager = require("data_manager")

-- Configurar DataManager
DataManager.MOD_REF = DEM

-- Configuración principal del mod
local function setupMod()
    if DEBUG_MODE then
        Isaac.DebugString("DEM_CV: Inicializando mod de control por IA...")
    end
    
    -- Inicializar variables
    dataCollectionEnabled = true
    playerVelocity = {X = 0, Y = 0}
    lastPosition = {X = 0, Y = 0}
    lastTimestamp = 0
    gameTicks = 0
    currentRoomLayout = nil
    lastFrameProcessed = 0
    processingFrequency = 1  -- Capturar en cada frame
    
    -- Registramos eventos de juego a los que queremos responder
    DEM:AddCallback(ModCallbacks.MC_POST_UPDATE, DEM.onUpdate)
    DEM:AddCallback(ModCallbacks.MC_POST_PLAYER_UPDATE, DEM.onPlayerUpdate)
    DEM:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, DEM.onNewRoom)
    DEM:AddCallback(ModCallbacks.MC_POST_RENDER, DEM.onRender)
    
    -- Inicializar recepción de comandos
    initCommandReceiver()
    
    if DEBUG_MODE then
        Isaac.DebugString("DEM_CV: Mod inicializado correctamente")
        Isaac.DebugString("DEM_CV: Esperando comandos de control en puerto " .. SERVER_PORT)
    end
end

-- Inicializar receptor de comandos
function initCommandReceiver()
    -- En Lua de Isaac no podemos crear sockets directamente
    -- Usamos el sistema de archivos como interfaz
    if DEBUG_MODE then
        Isaac.DebugString("DEM_CV: Inicializando receptor de comandos...")
    end
    
    -- Limpiar archivo de comandos
    Isaac.SaveModData(DEM, "[]")
    
    if DEBUG_MODE then
        Isaac.DebugString("DEM_CV: Receptor de comandos listo")
    end
end

-- Función para mapear la habitación actual
function DEM:mapCurrentRoom()
    local room = Game():GetRoom()
    local level = Game():GetLevel()
    local roomDesc = level:GetCurrentRoomDesc()
    local roomData = {
        width = room:GetGridWidth(),
        height = room:GetGridHeight(),
        id = roomDesc.SafeGridIndex,
        type = room:GetType(),
        doors = {},
        obstacles = {},
        entities = {}
    }
    
    -- Mapear puertas
    for i = 0, 7 do -- 8 posibles direcciones para puertas
        local doorSlot = i
        if room:IsDoorSlotAllowed(doorSlot) and room:GetDoor(doorSlot) then
            local door = room:GetDoor(doorSlot)
            table.insert(roomData.doors, {
                slot = doorSlot,
                position = {
                    x = door.Position.X,
                    y = door.Position.Y
                },
                exists = true
            })
        end
    end
    
    -- Mapear obstáculos (grid entities)
    for i = 0, room:GetGridSize() do
        local gridEntity = room:GetGridEntity(i)
        if gridEntity then
            local data = {
                index = i,
                position = {
                    x = gridEntity.Position.X,
                    y = gridEntity.Position.Y
                },
                type = gridEntity:GetType()
            }
            table.insert(roomData.obstacles, data)
        end
    end
    
    return roomData
end

-- Capturar estado del jugador
function DEM:capturePlayerState(player)
    if not player then return nil end
    
    -- Posición
    local position = player.Position
    
    -- Calcular velocidad basada en posición anterior
    local currentVelocity = {
        X = position.X - lastPosition.X,
        Y = position.Y - lastPosition.Y
    }
    
    -- Actualizar posición anterior
    lastPosition.X = position.X
    lastPosition.Y = position.Y
    
    -- Otras propiedades útiles
    return {
        position = {
            x = position.X,
            y = position.Y
        },
        health = {
            hearts = player:GetHearts(),
            soul_hearts = player:GetSoulHearts(),
            black_hearts = player:GetBlackHearts(),
            eternal_hearts = player:GetEternalHearts(),
            bone_hearts = player:GetBoneHearts(),
            golden_hearts = player:GetGoldenHearts(),
            max_hearts = player:GetMaxHearts()
        },
        velocity = {
            x = currentVelocity.X,
            y = currentVelocity.Y
        },
        items = player:GetCollectibleCount(),
        fire_direction = player:GetFireDirection(),
        move_direction = player:GetMovementDirection(),
        bombs = player:GetNumBombs(),
        keys = player:GetNumKeys(),
        coins = player:GetNumCoins()
    }
end

-- Capturar entidades (enemigos, pickups, etc)
function DEM:captureEntities()
    local game = Game()
    local room = game:GetRoom()
    local entities = {}
    
    -- Iterar sobre todas las entidades de la habitación
    for i, entity in ipairs(Isaac.GetRoomEntities()) do
        local entityType = entity.Type
        local entityVariant = entity.Variant
        local position = entity.Position
        local velocity = entity.Velocity
        
        -- Excluir al jugador y lágrimas del jugador
        if entityType ~= EntityType.ENTITY_PLAYER then
            local entityData = {
                id = entity.Index,
                type = entityType,
                variant = entityVariant,
                position = {
                    x = position.X,
                    y = position.Y
                },
                velocity = {
                    x = velocity.X,
                    y = velocity.Y
                },
                hp = 0
            }
            
            -- Añadir HP si es un enemigo
            if entityType == EntityType.ENTITY_NPC and entity:ToNPC() then
                entityData.hp = entity:ToNPC().HitPoints
            end
            
            table.insert(entities, entityData)
        end
    end
    
    return entities
end

-- Capturar inputs del usuario (para aprendizaje)
function DEM:captureInputs()
    local inputs = {
        up = Input.IsActionPressed(ButtonAction.ACTION_UP, 0),
        down = Input.IsActionPressed(ButtonAction.ACTION_DOWN, 0),
        left = Input.IsActionPressed(ButtonAction.ACTION_LEFT, 0),
        right = Input.IsActionPressed(ButtonAction.ACTION_RIGHT, 0),
        shoot_up = Input.IsActionPressed(ButtonAction.ACTION_SHOOTUP, 0),
        shoot_down = Input.IsActionPressed(ButtonAction.ACTION_SHOOTDOWN, 0),
        shoot_left = Input.IsActionPressed(ButtonAction.ACTION_SHOOTLEFT, 0),
        shoot_right = Input.IsActionPressed(ButtonAction.ACTION_SHOOTRIGHT, 0),
        bomb = Input.IsActionPressed(ButtonAction.ACTION_BOMB, 0),
        item = Input.IsActionPressed(ButtonAction.ACTION_ITEM, 0),
        pill_card = Input.IsActionPressed(ButtonAction.ACTION_PILLCARD, 0),
        drop = Input.IsActionPressed(ButtonAction.ACTION_DROP, 0),
        map = Input.IsActionPressed(ButtonAction.ACTION_MAP, 0)
    }
    
    return inputs
end

-- Procesar comandos recibidos desde el agente de IA
function DEM:processCommands()
    -- Verificar si hay comandos nuevos
    if not Isaac.HasModData(DEM) then
        return
    end
    
    -- Cargar comandos del archivo
    local cmdData = Isaac.LoadModData(DEM)
    if cmdData == "" then
        return
    end
    
    -- Intentar parsear como JSON
    local success, commands = pcall(json.decode, cmdData)
    if not success or not commands then
        if DEBUG_MODE then
            Isaac.DebugString("DEM_CV: Error al decodificar comandos: " .. tostring(commands))
        end
        return
    end
    
    -- Procesar cada comando
    for _, cmd in ipairs(commands) do
        self:executeCommand(cmd)
    end
    
    -- Limpiar archivo de comandos
    Isaac.SaveModData(DEM, "[]")
end

-- Ejecutar un comando individual
function DEM:executeCommand(cmd)
    if not cmd or not cmd.type then
        if DEBUG_MODE then
            Isaac.DebugString("DEM_CV: Comando inválido recibido")
        end
        return
    end
    
    -- Actualizar última acción recibida
    lastActionReceived = cmd
    lastActionTimestamp = Game():GetFrameCount()
    
    if DEBUG_MODE then
        Isaac.DebugString("DEM_CV: Ejecutando comando: " .. json.encode(cmd))
    end
    
    local player = Isaac.GetPlayer(0)
    if not player then return end
    
    -- Procesar según tipo de comando
    if cmd.type == "move" then
        -- Movimiento simple
        self:executeMovement(player, cmd.direction)
    elseif cmd.type == "shoot" then
        -- Disparo
        self:executeShooting(player, cmd.direction)
    elseif cmd.type == "move_shoot" then
        -- Movimiento y disparo simultáneo
        self:executeMovement(player, cmd.move_direction)
        self:executeShooting(player, cmd.shoot_direction)
    elseif cmd.type == "use_item" then
        -- Usar item activo
        self:executeItemUse(player)
    elseif cmd.type == "use_pill_card" then
        -- Usar píldora o carta
        self:executePillCardUse(player)
    elseif cmd.type == "use_bomb" then
        -- Colocar bomba
        self:executeBombUse(player)
    elseif cmd.type == "none" then
        -- No hacer nada (comando nulo)
        -- Útil para observación sin interacción
    else
        if DEBUG_MODE then
            Isaac.DebugString("DEM_CV: Tipo de comando desconocido: " .. cmd.type)
        end
    end
    
    -- Registrar la acción para análisis
    DataManager.recordControlEvent(cmd, true)
end

-- Ejecutar movimiento
function DEM:executeMovement(player, direction)
    if direction == "up" then
        Input.SetActionValue(ButtonAction.ACTION_UP, 1.0, 0)
    elseif direction == "down" then
        Input.SetActionValue(ButtonAction.ACTION_DOWN, 1.0, 0)
    elseif direction == "left" then
        Input.SetActionValue(ButtonAction.ACTION_LEFT, 1.0, 0)
    elseif direction == "right" then
        Input.SetActionValue(ButtonAction.ACTION_RIGHT, 1.0, 0)
    end
end

-- Ejecutar disparo
function DEM:executeShooting(player, direction)
    if direction == "up" then
        Input.SetActionValue(ButtonAction.ACTION_SHOOTUP, 1.0, 0)
    elseif direction == "down" then
        Input.SetActionValue(ButtonAction.ACTION_SHOOTDOWN, 1.0, 0)
    elseif direction == "left" then
        Input.SetActionValue(ButtonAction.ACTION_SHOOTLEFT, 1.0, 0)
    elseif direction == "right" then
        Input.SetActionValue(ButtonAction.ACTION_SHOOTRIGHT, 1.0, 0)
    end
end

-- Ejecutar uso de item
function DEM:executeItemUse(player)
    Input.SetActionValue(ButtonAction.ACTION_ITEM, 1.0, 0)
end

-- Ejecutar uso de píldora o carta
function DEM:executePillCardUse(player)
    Input.SetActionValue(ButtonAction.ACTION_PILLCARD, 1.0, 0)
end

-- Ejecutar uso de bomba
function DEM:executeBombUse(player)
    Input.SetActionValue(ButtonAction.ACTION_BOMB, 1.0, 0)
end

-- Actualización principal de datos (llamada cada frame)
function DEM:onUpdate()
    local game = Game()
    -- No procesar si el juego está pausado o si la recolección está desactivada
    if not game:IsPaused() and dataCollectionEnabled then
        local currentFrame = game:GetFrameCount()
        
        -- Procesamiento en cada frame (sin saltar frames)
        -- Capturar el estado del juego en este momento
        local player = Isaac.GetPlayer(0)
        if player then
            -- Procesar comandos del agente de IA
            self:processCommands()
            
            -- Capturar el estado detallado actual
            local frameData = {
                frame_count = currentFrame,
                tick = gameTicks,
                time = game.TimeCounter,
                player = self:capturePlayerState(player),
                entities = self:captureEntities(),
                room = {
                    id = game:GetLevel():GetCurrentRoomDesc().SafeGridIndex,
                    type = game:GetRoom():GetType(),
                    clear = game:GetRoom():IsClear()
                }
            }
            
            -- Registrar el evento de estado del frame
            DataManager.recordEvent("frame_state", frameData)
            
            -- Actualizar el último frame procesado
            lastFrameProcessed = currentFrame
            
            -- Incrementar el contador de ticks del juego
            gameTicks = gameTicks + 1
        end
    end
end

-- Actualización específica del jugador
function DEM:onPlayerUpdate(player)
    -- Si es el primer jugador (sólo usamos el primer jugador por simplicidad)
    if player and player:GetPlayerType() == 0 then
        -- Calculamos velocidad real (para entrenamiento)
        local currentPosition = player.Position
        local currentTimestamp = Game():GetFrameCount()
        
        if lastTimestamp > 0 then
            local deltaTime = currentTimestamp - lastTimestamp
            if deltaTime > 0 then
                playerVelocity.X = (currentPosition.X - lastPosition.X) / deltaTime
                playerVelocity.Y = (currentPosition.Y - lastPosition.Y) / deltaTime
            end
        end
        
        lastPosition.X = currentPosition.X
        lastPosition.Y = currentPosition.Y
        lastTimestamp = currentTimestamp
    end
end

-- Al entrar a una nueva habitación
function DEM:onNewRoom()
    -- Mapear la nueva habitación
    currentRoomLayout = self:mapCurrentRoom()
    
    -- Registrar evento de nueva habitación
    DataManager.recordEvent("new_room", {
        room = currentRoomLayout,
        timestamp = Game():GetFrameCount()
    })
    
    if DEBUG_MODE then
        Isaac.DebugString("DEM_CV: Nueva habitación detectada, layout mapeado")
    end
end

-- Renderizado (para debug)
function DEM:onRender()
    -- Si el modo debug está activado, mostrar información sobre el último comando
    if DEBUG_MODE and lastActionReceived then
        local game = Game()
        local currentFrame = game:GetFrameCount()
        
        -- Solo mostrar por un tiempo limitado
        if currentFrame - lastActionTimestamp < 30 then  -- Mostrar por 30 frames (0.5 segundos)
            local font = Font()
            font:Load("font/terminus.fnt")
            
            local cmdText = "Acción: " .. lastActionReceived.type
            
            if lastActionReceived.direction then
                cmdText = cmdText .. " " .. lastActionReceived.direction
            end
            
            if lastActionReceived.move_direction and lastActionReceived.shoot_direction then
                cmdText = cmdText .. " (Mov: " .. lastActionReceived.move_direction .. 
                         ", Disp: " .. lastActionReceived.shoot_direction .. ")"
            end
            
            -- Mostrar en pantalla
            font:DrawString(cmdText, 50, 50, KColor(1, 1, 1, 1), 0, true)
        end
    end
end

-- Inicializar el mod
setupMod()

-- Retornar el mod para uso externo
return DEM 
