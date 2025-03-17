--[[
    DEM - Data Event Manager
    Mod simplificado para recolectar datos de eventos del juego.
    Esta versión solo guarda datos localmente usando Isaac.SaveModData.
    
    NOTA IMPORTANTE:
    1. Los datos se guardan en: Documents/My Games/Binding of Isaac Repentance+/Data Event Manager.dat
    2. No se pueden crear archivos individuales por cada evento debido a restricciones del juego
    3. El mod acumula varios eventos y los guarda juntos en un array JSON
]]

-- Cargar el administrador de datos
local DataManager = require("data_manager")

-- Registrar el mod
local DEM = RegisterMod("Data Event Manager", 1)

-- Obtener referencia al Game()
local game = Game()

-- Variable para evitar duplicar algunos eventos
local eventsRegistered = {}

-- Debug inicial para verificar carga correcta
Isaac.DebugString("DEM: -------------------------------")
Isaac.DebugString("DEM: Mod inicializado correctamente")
Isaac.DebugString("DEM: Los datos se guardarán en el archivo 'Data Event Manager.dat'")
Isaac.DebugString("DEM: En: Documents/My Games/Binding of Isaac Repentance+/")
Isaac.DebugString("DEM: -------------------------------")

-- Callback para cuando el jugador recoge un ítem
function DEM:onPickupCollected(pickup, player)
    -- Solo nos interesan los coleccionables
    if pickup.Variant == PickupVariant.PICKUP_COLLECTIBLE then
        -- Verificamos que tenemos acceso al item config
        local itemConfig = Isaac.GetItemConfig()
        local itemName = "Unknown"
        
        if itemConfig and itemConfig:GetCollectible(pickup.SubType) then
            itemName = itemConfig:GetCollectible(pickup.SubType).Name
        end
        
        -- Registrar el evento de recolección de ítem
        DataManager.recordEvent("item_collected", {
            item_id = pickup.SubType,
            player_index = player.ControllerIndex,
            item_name = itemName
        })
    end
end

-- Callback para cuando el jugador recibe daño
function DEM:onPlayerDamage(entity, amount, flags, source)
    -- Asegurarse de que es un jugador
    if entity and entity:ToPlayer() then
        local player = entity:ToPlayer()
        
        -- Registrar evento de daño
        DataManager.recordEvent("player_damage", {
            player_index = player.ControllerIndex,
            damage_amount = amount,
            damage_flags = flags,
            source_type = source and source.Type or -1,
            hp_after = player:GetHearts(),
            soul_hearts_after = player:GetSoulHearts()
        })
    end
    
    -- No modificamos el comportamiento del juego
    return nil
end

-- Callback para cuando se derrota a un enemigo
function DEM:onNPCDeath(npc)
    -- Solo nos interesan enemigos reales (no efectos o similares)
    if npc:IsEnemy() and not npc:IsDead() then
        -- Registrar evento de muerte del enemigo
        DataManager.recordEvent("enemy_killed", {
            enemy_type = npc.Type,
            enemy_variant = npc.Variant,
            boss = npc:IsBoss(),
            room_id = game:GetLevel():GetCurrentRoomDesc().SafeGridIndex
        })
    end
end

-- Probar carga y guardado de datos al inicio
function DEM:onGameStart(continued)
    -- Generar un evento importante al inicio del juego
    Isaac.DebugString("DEM: Generando evento de inicio de juego")
    
    -- Registrar evento de inicio de juego
    DataManager.recordEvent("game_start_detailed", {
        continued = continued,
        player_type = Isaac.GetPlayer(0):GetPlayerType(),
        hard_mode = Game().Difficulty == Difficulty.DIFFICULTY_HARD,
        seed = Game():GetSeeds():GetStartSeed(),
        version = "1.0",
        timestamp = Game():GetFrameCount()
    })
    
    -- Generar un evento extra solo para testing
    for i = 1, 3 do
        DataManager.recordEvent("test_event", {
            test_number = i,
            message = "Evento de prueba " .. i .. " generado al iniciar"
        })
    end
    
    -- Forzar guardado del buffer para verificar que funciona correctamente
    DataManager.saveEvents()
    Isaac.DebugString("DEM: Eventos iniciales generados y guardados")
end

-- Prueba manual de guardado de datos durante el juego
function DEM:onRender()
    -- Solo lo ejecutamos cada cierto tiempo
    local frame = game:GetFrameCount()
    
    -- Cada 300 frames (aprox. 10 segundos a 30 FPS) generamos un evento de prueba
    if frame % 300 == 0 and frame > 0 then
        -- Generar un evento único (no habría problema con duplicados, solo para simplificar logs)
        local eventId = "frame_" .. frame
        if not eventsRegistered[eventId] then
            eventsRegistered[eventId] = true
            
            Isaac.DebugString("DEM: Generando evento de prueba en frame " .. frame)
            
            -- Obtenemos el número de enemigos de forma segura
            local numEnemies = 0
            local room = game:GetRoom()
            if room then
                for i = 0, room:GetGridSize() do
                    local entity = Isaac.GetRoomEntities()[i]
                    if entity and entity:IsEnemy() then
                        numEnemies = numEnemies + 1
                    end
                end
            end
            
            DataManager.recordEvent("gameplay_snapshot", {
                frame = frame,
                player_position = {
                    x = Isaac.GetPlayer().Position.X,
                    y = Isaac.GetPlayer().Position.Y
                },
                room_id = game:GetLevel():GetCurrentRoomDesc().SafeGridIndex,
                enemies = numEnemies
            })
            
            -- Forzar guardado del buffer cada 900 frames (aprox. 30 segundos)
            if frame % 900 == 0 then
                Isaac.DebugString("DEM: Guardando buffer cada 30 segundos (frame " .. frame .. ")")
                DataManager.saveEvents()
            end
        end
    end
end

-- Registrar callbacks adicionales (no registrados en data_manager)
DEM:AddCallback(ModCallbacks.MC_PRE_PICKUP_COLLISION, DEM.onPickupCollected)
DEM:AddCallback(ModCallbacks.MC_ENTITY_TAKE_DMG, DEM.onPlayerDamage, EntityType.ENTITY_PLAYER)
DEM:AddCallback(ModCallbacks.MC_POST_NPC_DEATH, DEM.onNPCDeath)
DEM:AddCallback(ModCallbacks.MC_POST_RENDER, DEM.onRender)
DEM:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, DEM.onGameStart)

-- Mensaje de inicio
Isaac.DebugString("DEM: Data Event Manager iniciado (Versión simplificada con buffer)")

-- Devolver el mod (útil para pruebas)
return DEM 
