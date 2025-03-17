--[[
    DEM - Data Event Manager
    Mod avanzado para recolectar datos detallados del juego para entrenar IA.
    Esta versión captura datos granulares en cada frame incluyendo:
    - Posición precisa de todas las entidades
    - Mapeo de habitaciones
    - Estado completo del jugador
    - Vectores de movimiento y trayectorias
    - Entradas del usuario
    
    Diseñado específicamente para ML/IA: El dataset resultante permitirá
    entrenar modelos que puedan jugar a The Binding of Isaac.
]]

-- Cargar el administrador de datos
local DataManager = require("data_manager")
local json = require("json")

-- Registrar el mod
local DEM = RegisterMod("Data Event Manager", 1)

-- Obtener referencia al Game()
local game = Game()

-- Variables para el seguimiento detallado
local currentRoomLayout = {}
local lastFrameProcessed = 0
local processingFrequency = 1  -- Cada cuántos frames capturar datos (1 = cada frame)
local lastInputState = {}
local roomsExplored = {}
local entityTracking = {}
local gameTicks = 0
local dataCollectionEnabled = true
local lastPlayerPosition = Vector(0, 0)
local playerVelocity = Vector(0, 0)

-- Debug inicial para verificar carga correcta
Isaac.DebugString("DEM: -------------------------------")
Isaac.DebugString("DEM: Mod mejorado para ML/IA inicializado")
Isaac.DebugString("DEM: Recopilando datos granulares para entrenamiento")
Isaac.DebugString("DEM: -------------------------------")

-- Función para capturar el mapa de la habitación actual
function DEM:mapCurrentRoom()
    local room = game:GetRoom()
    local layout = {
        shape = room:GetRoomShape(),
        width = room:GetGridWidth(),
        height = room:GetGridHeight(),
        gridSize = room:GetGridSize(),
        obstacles = {},
        doors = {},
        walkableAreas = {}
    }
    
    -- Mapear cada celda de la cuadrícula
    for i = 0, layout.gridSize - 1 do
        local gridEntity = room:GetGridEntity(i)
        local position = room:GetGridPosition(i)
        local cellType = "walkable"
        
        -- Verificar si hay una entidad de cuadrícula en esta celda
        if gridEntity then
            local entityType = gridEntity.Desc.Type
            
            if entityType == GridEntityType.GRID_WALL then
                cellType = "wall"
            elseif entityType == GridEntityType.GRID_ROCK or entityType == GridEntityType.GRID_ROCK_ALT or 
                   entityType == GridEntityType.GRID_ROCK_SS or entityType == GridEntityType.GRID_ROCK_SPIKED or
                   entityType == GridEntityType.GRID_ROCK_ALT2 or entityType == GridEntityType.GRID_ROCK_GOLD then
                cellType = "rock"
            elseif entityType == GridEntityType.GRID_PIT then
                cellType = "pit"
            elseif entityType == GridEntityType.GRID_SPIKES or entityType == GridEntityType.GRID_SPIKES_ONOFF then
                cellType = "spikes"
            elseif entityType == GridEntityType.GRID_TNT then
                cellType = "tnt"
            elseif entityType == GridEntityType.GRID_POOP then
                cellType = "poop"
            elseif entityType == GridEntityType.GRID_DOOR then
                cellType = "door"
                table.insert(layout.doors, {
                    index = i,
                    x = position.X,
                    y = position.Y,
                    doorSlot = gridEntity:ToDoor() and gridEntity:ToDoor().Slot or -1,
                    open = gridEntity:ToDoor() and gridEntity:ToDoor():IsOpen() or false
                })
            end
            
            -- Sólo añadir obstáculos a la lista específica
            if cellType ~= "walkable" and cellType ~= "door" then
                table.insert(layout.obstacles, {
                    index = i,
                    type = cellType,
                    x = position.X,
                    y = position.Y
                })
            end
        end
        
        -- Si la celda es caminable, añadirla a las áreas transitables
        if cellType == "walkable" then
            table.insert(layout.walkableAreas, {
                index = i,
                x = position.X,
                y = position.Y
            })
        end
    end
    
    -- Detectar el tipo de habitación y características especiales
    layout.roomType = room:GetType()
    layout.difficulty = room:GetRoomConfigDifficulty()
    layout.roomVariant = room:GetAltRockIdx() -- Da un valor que representa la variante de la habitación
    layout.isFirstVisit = not room:IsFirstVisit()
    
    return layout
end

-- Capturar datos detallados del jugador
function DEM:capturePlayerState(player)
    if not player then return {} end
    
    local playerData = {
        position = {
            x = player.Position.X,
            y = player.Position.Y
        },
        velocity = {
            x = player.Velocity.X,
            y = player.Velocity.Y
        },
        health = {
            hearts = player:GetHearts(),
            max_hearts = player:GetMaxHearts(),
            soul_hearts = player:GetSoulHearts(),
            black_hearts = player:GetBlackHearts(),
            bone_hearts = player:GetBoneHearts(),
            eternal_hearts = player:GetEternalHearts(),
            golden_hearts = player:GetGoldenHearts()
        },
        stats = {
            speed = player.MoveSpeed,
            tears = player.MaxFireDelay,
            damage = player.Damage,
            range = player.TearHeight,
            shot_speed = player.ShotSpeed,
            luck = player.Luck
        },
        effects = {
            is_flying = player.CanFly,
            has_spectral = player.TearFlags & TearFlags.TEAR_SPECTRAL > 0,
            has_homing = player.TearFlags & TearFlags.TEAR_HOMING > 0,
            -- Más efectos según sea necesario
        },
        tear_flags = player.TearFlags,
        player_type = player:GetPlayerType(),
        items = {}
    }
    
    -- Obtener coleccionables actuales
    for i = 1, CollectibleType.NUM_COLLECTIBLES do
        local count = player:GetCollectibleNum(i)
        if count > 0 then
            local itemConfig = Isaac.GetItemConfig():GetCollectible(i)
            local name = itemConfig and itemConfig.Name or "Unknown Item " .. i
            
            table.insert(playerData.items, {
                id = i,
                name = name,
                count = count
            })
        end
    end
    
    -- Capturar objetos activos
    for slot = 0, ActiveSlot.SLOT_POCKET do
        local activeItem = player:GetActiveItem(slot)
        if activeItem > 0 then
            local itemConfig = Isaac.GetItemConfig():GetCollectible(activeItem)
            local name = itemConfig and itemConfig.Name or "Unknown Active " .. activeItem
            
            playerData.active_items = playerData.active_items or {}
            playerData.active_items[slot] = {
                id = activeItem,
                name = name,
                charge = player:GetActiveCharge(slot),
                max_charge = itemConfig and itemConfig.MaxCharges or 0
            }
        end
    end
    
    return playerData
end

-- Capturar entidades en la habitación
function DEM:captureEntities()
    local entities = {}
    local room = game:GetRoom()
    
    -- Obtener todas las entidades en la habitación
    for _, entity in ipairs(Isaac.GetRoomEntities()) do
        if entity and entity:Exists() then
            local entData = {
                type = entity.Type,
                variant = entity.Variant,
                subtype = entity.SubType,
                position = {
                    x = entity.Position.X,
                    y = entity.Position.Y
                },
                velocity = {
                    x = entity.Velocity.X,
                    y = entity.Velocity.Y
                },
                hp = entity.HitPoints or 0,
                max_hp = entity.MaxHitPoints or 0,
                entity_flags = entity.EntityFlags,
                frame = entity.FrameCount
            }
            
            -- Agregar información específica por tipo de entidad
            if entity:IsEnemy() then
                local npc = entity:ToNPC()
                if npc then
                    entData.ai_state = npc.State
                    entData.i1 = npc.I1
                    entData.i2 = npc.I2
                    entData.is_champion = npc:IsChampion()
                    entData.is_boss = npc:IsBoss()
                    entData.champion_color_idx = npc.ChampionColorIdx
                    
                    -- Obtener el objetivo del enemigo si está disponible
                    local target = npc:GetPlayerTarget()
                    if target then
                        entData.target = {
                            x = target.Position.X,
                            y = target.Position.Y
                        }
                    end
                end
            elseif entity.Type == EntityType.ENTITY_TEAR then
                local tear = entity:ToTear()
                if tear then
                    entData.tear_flags = tear.TearFlags
                    entData.damage = tear.CollisionDamage
                    entData.scale = tear.Scale
                    entData.height = tear.Height
                    entData.fallspeed = tear.FallingSpeed
                    entData.fallaccel = tear.FallingAcceleration
                end
            elseif entity.Type == EntityType.ENTITY_PROJECTILE then
                local projectile = entity:ToProjectile()
                if projectile then
                    entData.damage = projectile.ProjectileDamage
                    entData.scale = projectile.ProjectileScale
                    entData.height = projectile.Height
                    entData.acceleration = projectile.Acceleration
                    entData.fallspeed = projectile.FallingSpeed
                    entData.fallaccel = projectile.FallingAccel
                    entData.is_enemy_proj = not projectile:IsFlippedHorizontally()
                end
            elseif entity.Type == EntityType.ENTITY_PICKUP then
                local pickup = entity:ToPickup()
                if pickup then
                    entData.price = pickup.Price
                    entData.is_Shop_Item = pickup.IsShopItem
                    entData.wait_frames = pickup.FrameCount
                    
                    -- Si es un coleccionable, obtener su nombre
                    if pickup.Variant == PickupVariant.PICKUP_COLLECTIBLE then
                        local itemConfig = Isaac.GetItemConfig():GetCollectible(pickup.SubType)
                        if itemConfig then
                            entData.item_name = itemConfig.Name
                            entData.item_desc = itemConfig.Description
                            entData.item_quality = itemConfig.Quality
                        end
                    end
                end
            end
            
            -- Generar un ID único para cada entidad para seguimiento
            local entityId = entity.Index .. "_" .. entity.InitSeed
            
            -- Guardar datos en el tracking para cálculos de velocidad/aceleración
            local prevData = entityTracking[entityId]
            if prevData then
                -- Calcular cambios entre frames
                entData.velocity_change = {
                    x = entity.Velocity.X - prevData.velocity.x,
                    y = entity.Velocity.Y - prevData.velocity.y
                }
                
                entData.position_delta = {
                    x = entity.Position.X - prevData.position.x,
                    y = entity.Position.Y - prevData.position.y
                }
                
                -- Calcular tiempo en habitación
                entData.time_in_room = prevData.time_in_room + 1
            else
                entData.velocity_change = { x = 0, y = 0 }
                entData.position_delta = { x = 0, y = 0 }
                entData.time_in_room = 0
            end
            
            -- Actualizar el tracking
            entityTracking[entityId] = {
                position = { x = entity.Position.X, y = entity.Position.Y },
                velocity = { x = entity.Velocity.X, y = entity.Velocity.Y },
                time_in_room = entData.time_in_room
            }
            
            -- Añadir a la lista de entidades
            table.insert(entities, entData)
        end
    end
    
    return entities
end

-- Capturar las entradas del jugador
function DEM:captureInputs()
    local inputs = {}
    
    -- Comprobar todas las acciones de botón
    for i = 0, ButtonAction.NUM_BUTTON_ACTIONS - 1 do
        local action = i -- ButtonAction value
        local value = Input.GetActionValue(action, 0) -- Controlador 0 (principal)
        
        if value > 0 then
            local actionName = "UNKNOWN_ACTION_" .. action
            
            -- Mapear acciones a nombres legibles
            if action == ButtonAction.ACTION_LEFT then actionName = "LEFT"
            elseif action == ButtonAction.ACTION_RIGHT then actionName = "RIGHT"
            elseif action == ButtonAction.ACTION_UP then actionName = "UP"
            elseif action == ButtonAction.ACTION_DOWN then actionName = "DOWN"
            elseif action == ButtonAction.ACTION_SHOOTLEFT then actionName = "SHOOT_LEFT"
            elseif action == ButtonAction.ACTION_SHOOTRIGHT then actionName = "SHOOT_RIGHT"
            elseif action == ButtonAction.ACTION_SHOOTUP then actionName = "SHOOT_UP"
            elseif action == ButtonAction.ACTION_SHOOTDOWN then actionName = "SHOOT_DOWN"
            elseif action == ButtonAction.ACTION_BOMB then actionName = "BOMB"
            elseif action == ButtonAction.ACTION_ITEM then actionName = "ITEM"
            elseif action == ButtonAction.ACTION_PILLCARD then actionName = "PILL_CARD"
            elseif action == ButtonAction.ACTION_DROP then actionName = "DROP"
            elseif action == ButtonAction.ACTION_MAP then actionName = "MAP"
            elseif action == ButtonAction.ACTION_PAUSE then actionName = "PAUSE"
            elseif action == ButtonAction.ACTION_MENUCONFIRM then actionName = "MENU_CONFIRM"
            elseif action == ButtonAction.ACTION_MENUBACK then actionName = "MENU_BACK"
            end
            
            inputs[actionName] = value
            
            -- Detectar cambios en el estado de entrada
            if not lastInputState[actionName] or lastInputState[actionName] ~= value then
                -- Registrar el evento de cambio de entrada
                if value > 0 then
                    DataManager.recordEvent("input_change", {
                        action = actionName,
                        value = value,
                        pressed = true
                    })
                end
            end
        end
    end
    
    -- Actualizar el último estado de entrada
    lastInputState = inputs
    
    return inputs
end

-- Función para calcular la velocidad del jugador
function DEM:calculatePlayerVelocity(player)
    local currentPosition = player.Position
    
    -- Si tenemos una posición anterior, calcular la velocidad
    if lastPlayerPosition.X ~= 0 or lastPlayerPosition.Y ~= 0 then
        playerVelocity = Vector(
            currentPosition.X - lastPlayerPosition.X,
            currentPosition.Y - lastPlayerPosition.Y
        )
    end
    
    -- Actualizar la última posición
    lastPlayerPosition = Vector(currentPosition.X, currentPosition.Y)
    
    return playerVelocity
end

-- Actualización por frame para capturar datos continuos
function DEM:onUpdate()
    -- Solo procesar cada ciertos frames para no sobrecargarse
    if not dataCollectionEnabled then return end
    
    local currentFrame = game:GetFrameCount()
    if currentFrame - lastFrameProcessed < processingFrequency then
        return
    end
    
    lastFrameProcessed = currentFrame
    gameTicks = gameTicks + 1
    
    local player = Isaac.GetPlayer(0)
    if not player then return end
    
    -- Capturar estado completo por frame
    local frameData = {
        frame_count = currentFrame,
        game_tick = gameTicks,
        room_id = game:GetLevel():GetCurrentRoomDesc().SafeGridIndex,
        player = self:capturePlayerState(player),
        entities = self:captureEntities(),
        inputs = self:captureInputs(),
        calculated_velocity = {
            x = playerVelocity.X,
            y = playerVelocity.Y
        }
    }
    
    -- Calcular la velocidad del jugador
    self:calculatePlayerVelocity(player)
    
    -- Registrar el estado de juego cada frame
    DataManager.recordEvent("frame_state", frameData)
    
    -- Guardar datos cada 60 frames (aproximadamente 2 segundos)
    if currentFrame % 60 == 0 then
        DataManager.saveEvents()
    end
end

-- Cuando el jugador entra en una nueva habitación
function DEM:onNewRoom()
    -- Mapear la habitación al entrar
    currentRoomLayout = self:mapCurrentRoom()
    
    local level = game:GetLevel()
    local roomDesc = level:GetCurrentRoomDesc()
    local roomID = roomDesc.SafeGridIndex
    
    -- Limpiar el tracking de entidades
    entityTracking = {}
    
    -- Reiniciar la última posición del jugador
    lastPlayerPosition = Vector(0, 0)
    playerVelocity = Vector(0, 0)
    
    -- Verificar si ya hemos explorado esta habitación
    local isNewRoom = not roomsExplored[roomID]
    
    -- Marcar como explorada
    roomsExplored[roomID] = true
    
    -- Registrar evento detallado de entrada a habitación
    DataManager.recordEvent("room_detailed", {
        room_id = roomID,
        is_new_room = isNewRoom,
        room_layout = currentRoomLayout,
        stage = level:GetStage(),
        stage_type = level:GetStageType()
    })
    
    -- Forzar guardado al cambiar de habitación
    DataManager.saveEvents()
end

-- Callback para cuando el jugador recoge un ítem
function DEM:onPickupCollected(pickup, player)
    -- Solo nos interesan los coleccionables
    if pickup.Variant == PickupVariant.PICKUP_COLLECTIBLE then
        -- Verificamos que tenemos acceso al item config
        local itemConfig = Isaac.GetItemConfig()
        local itemName = "Unknown"
        local itemDesc = ""
        local itemQuality = 0
        
        if itemConfig and itemConfig:GetCollectible(pickup.SubType) then
            local item = itemConfig:GetCollectible(pickup.SubType)
            itemName = item.Name
            itemDesc = item.Description
            itemQuality = item.Quality
        end
        
        -- Capturar estado del jugador antes y después
        local playerStateBefore = self:capturePlayerState(player)
        
        -- Registrar el evento de recolección de ítem con datos completos
        DataManager.recordEvent("item_collected_detailed", {
            item_id = pickup.SubType,
            player_index = player.ControllerIndex,
            item_name = itemName,
            item_desc = itemDesc,
            item_quality = itemQuality,
            position = {
                x = pickup.Position.X,
                y = pickup.Position.Y
            },
            player_state_before = playerStateBefore
        })
        
        -- Forzar guardado para no perder estos datos importantes
        DataManager.saveEvents()
    end
end

-- Callback para cuando el jugador recibe daño
function DEM:onPlayerDamage(entity, amount, flags, source)
    -- Asegurarse de que es un jugador
    if entity and entity:ToPlayer() then
        local player = entity:ToPlayer()
        
        -- Obtener información sobre la fuente de daño
        local sourceInfo = {
            type = source and source.Type or -1,
            variant = source and source.Variant or -1,
            entity_type = "Unknown"
        }
        
        -- Determinar el tipo de entidad fuente
        if source then
            if source.Type == EntityType.ENTITY_PROJECTILE then
                sourceInfo.entity_type = "Projectile"
            elseif source.Type == EntityType.ENTITY_TEAR then
                sourceInfo.entity_type = "Tear"
            elseif source.Type == EntityType.ENTITY_BOMBDROP then
                sourceInfo.entity_type = "Bomb"
            elseif source.Type == EntityType.ENTITY_LASER then
                sourceInfo.entity_type = "Laser"
            elseif source.Type >= EntityType.ENTITY_SPIDER and source.Type <= EntityType.ENTITY_BIGHORN then
                sourceInfo.entity_type = "Enemy"
            end
        end
        
        -- Registrar evento de daño con datos completos
        DataManager.recordEvent("player_damage_detailed", {
            player_index = player.ControllerIndex,
            damage_amount = amount,
            damage_flags = flags,
            source = sourceInfo,
            hp_before = player:GetHearts() + amount,
            hp_after = player:GetHearts(),
            soul_hearts_before = player:GetSoulHearts(),
            soul_hearts_after = player:GetSoulHearts(),
            player_position = {
                x = player.Position.X,
                y = player.Position.Y
            },
            player_velocity = {
                x = player.Velocity.X,
                y = player.Velocity.Y
            },
            frame_count = game:GetFrameCount(),
            room_id = game:GetLevel():GetCurrentRoomDesc().SafeGridIndex,
            invincibility_frames = player.FrameCount
        })
    end
    
    -- No modificamos el comportamiento del juego
    return nil
end

-- Callback para cuando se derrota a un enemigo
function DEM:onNPCDeath(npc)
    -- Solo nos interesan enemigos reales (no efectos o similares)
    if npc:IsEnemy() and not npc:IsDead() then
        local player = Isaac.GetPlayer(0)
        
        -- Registrar evento de muerte del enemigo con posición y estado completo
        DataManager.recordEvent("enemy_killed_detailed", {
            enemy_type = npc.Type,
            enemy_variant = npc.Variant,
            boss = npc:IsBoss(),
            champion = npc:IsChampion(),
            champion_color = npc.ChampionColorIdx,
            room_id = game:GetLevel():GetCurrentRoomDesc().SafeGridIndex,
            position = {
                x = npc.Position.X,
                y = npc.Position.Y
            },
            player_distance = player and math.sqrt(
                (player.Position.X - npc.Position.X)^2 + 
                (player.Position.Y - npc.Position.Y)^2
            ) or -1,
            frame_count = game:GetFrameCount(),
            enemy_hp_max = npc.MaxHitPoints,
            killed_by_player = true  -- Asumimos que lo mató el jugador directamente
        })
    end
end

-- Probar carga y guardado de datos al inicio
function DEM:onGameStart(continued)
    -- Inicializar estado
    roomsExplored = {}
    entityTracking = {}
    gameTicks = 0
    lastFrameProcessed = 0
    lastPlayerPosition = Vector(0, 0)
    playerVelocity = Vector(0, 0)
    
    -- Verificar configuración de machine learning
    dataCollectionEnabled = true
    processingFrequency = 1  -- Coleccionar datos cada frame
    
    -- Generar un evento importante al inicio del juego
    Isaac.DebugString("DEM: Iniciando recopilación de datos ML")
    
    -- Capturar seed y otros datos del juego
    local seedInfo = game:GetSeeds()
    local seedString = seedInfo:GetStartSeedString()
    
    -- Registrar evento de inicio de juego
    DataManager.recordEvent("game_start_ml", {
        continued = continued,
        player_type = Isaac.GetPlayer(0):GetPlayerType(),
        hard_mode = Game().Difficulty == Difficulty.DIFFICULTY_HARD,
        seed = seedString,
        raw_seed = game:GetSeeds():GetStartSeed(),
        version = "2.0",
        timestamp = Game():GetFrameCount(),
        ml_enabled = true,
        processing_frequency = processingFrequency,
        data_types = {
            "player_state", "entity_tracking", "room_mapping", 
            "input_tracking", "physics_calculation"
        }
    })
    
    -- Forzar guardado del buffer para verificar que funciona correctamente
    DataManager.saveEvents()
    Isaac.DebugString("DEM: Inicio de recopilación ML configurado")
    
    -- Mapear la habitación inicial
    self:onNewRoom()
end

-- Registrar callbacks adicionales (no registrados en data_manager)
DEM:AddCallback(ModCallbacks.MC_PRE_PICKUP_COLLISION, DEM.onPickupCollected)
DEM:AddCallback(ModCallbacks.MC_ENTITY_TAKE_DMG, DEM.onPlayerDamage, EntityType.ENTITY_PLAYER)
DEM:AddCallback(ModCallbacks.MC_POST_NPC_DEATH, DEM.onNPCDeath)
DEM:AddCallback(ModCallbacks.MC_POST_RENDER, DEM.onUpdate)
DEM:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, DEM.onGameStart)
DEM:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, DEM.onNewRoom)

-- Mensaje de inicio
Isaac.DebugString("DEM: Mod para Machine Learning inicializado")

-- Devolver el mod (útil para pruebas)
return DEM 
