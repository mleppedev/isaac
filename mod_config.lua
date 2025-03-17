--[[
Configuración del mod DEM (Data Extraction Mod)
Este archivo controla el comportamiento de captura de datos del mod.
]]

local DEM_Config = {
    -- Configuración general
    enabled = true,
    debug_mode = false,
    
    -- Frecuencia de captura (frames)
    capture_interval = 5,          -- Capturar datos cada X frames (menor = más datos)
    combat_capture_interval = 2,   -- Intervalo durante combate (más frecuente)
    boss_capture_interval = 1,     -- Intervalo durante combate con jefes (aún más frecuente)
    
    -- Opciones de captura de datos
    capture = {
        player_position = true,    -- Posición del jugador
        player_velocity = true,    -- Velocidad del jugador
        player_health = true,      -- Salud del jugador
        player_stats = true,       -- Estadísticas del jugador
        player_items = true,       -- Items del jugador
        player_familiars = true,   -- Familiares del jugador
        player_collectibles = true, -- Coleccionables del jugador
        player_trinkets = true,    -- Trinkets del jugador
        player_cards = true,       -- Cartas del jugador
        player_pills = true,       -- Píldoras del jugador
        
        entities = true,           -- Entidades en la sala
        enemy_data = true,         -- Datos de enemigos
        enemy_positions = true,    -- Posiciones de enemigos
        enemy_health = true,       -- Salud de enemigos
        enemy_target = true,       -- Objetivo de ataque de enemigos
        
        inputs = true,             -- Entradas del jugador
        room_layout = true,        -- Disposición de la sala
        room_type = true,          -- Tipo de sala
        room_items = true,         -- Items en la sala
        room_grid = true,          -- Rejilla de la sala
        
        level_data = true,         -- Datos del nivel
        game_data = true,          -- Datos del juego
        
        projectiles = true,        -- Proyectiles
        tears = true,              -- Lágrimas
        lasers = true,             -- Láseres
        explosions = true,         -- Explosiones
    },
    
    -- Eventos específicos a capturar (independiente del intervalo regular)
    events = {
        -- Jugador
        damage_taken = true,       -- Daño recibido
        damage_dealt = true,       -- Daño causado
        item_collected = true,     -- Item recogido
        item_used = true,          -- Item usado
        pickup_collected = true,   -- Pickup recogido
        pill_used = true,          -- Píldora usada
        card_used = true,          -- Carta usada
        
        -- Sala y nivel
        room_enter = true,         -- Entrar a una sala
        room_clear = true,         -- Sala limpiada
        room_exit = true,          -- Salir de una sala
        door_entered = true,       -- Entrar por una puerta
        trap_triggered = true,     -- Trampa activada
        secret_found = true,       -- Secreto encontrado
        level_start = true,        -- Inicio de nivel
        level_complete = true,     -- Nivel completado
        
        -- Enemigos
        enemy_spawn = true,        -- Enemigo aparece
        enemy_killed = true,       -- Enemigo eliminado
        boss_encounter = true,     -- Encuentro con jefe
        boss_defeated = true,      -- Jefe derrotado
        
        -- Juego
        game_start = true,         -- Inicio de juego
        game_exit = true,          -- Salida de juego
        run_victory = true,        -- Victoria de run
        run_defeat = true,         -- Derrota de run
    },
    
    -- Opciones avanzadas
    advanced = {
        track_combat_metrics = true,   -- Métricas detalladas de combate
        track_room_metrics = true,     -- Métricas detalladas de salas
        detailed_entity_tracking = true, -- Seguimiento detallado de entidades
        save_interval = 30,           -- Guardar datos cada X segundos
        max_entities_per_capture = 100, -- Límite de entidades por captura
        compress_data = false,        -- Comprimir datos (reduce tamaño pero aumenta CPU)
        include_entity_sprites = false, -- Incluir datos de sprites (aumenta mucho el tamaño)
        buffer_size = 1000,           -- Tamaño del buffer antes de escribir a disco
        flush_on_level_change = true, -- Vaciar buffer al cambiar de nivel
        add_timestamps = true,        -- Añadir timestamps precisos
        track_frame_time = true,      -- Rastrear tiempo por frame para análisis de rendimiento
    },
    
    -- Directorios y archivos
    file = {
        log_directory = "dem_logs",   -- Directorio para logs
        file_prefix = "dem_data_",    -- Prefijo de archivos
        use_date_in_filename = true,  -- Usar fecha en nombre de archivo
        use_seed_in_filename = true,  -- Usar seed en nombre de archivo
        split_files_by_level = true,  -- Dividir archivos por nivel
        use_json_format = true,       -- Usar formato JSON
    }
}

return DEM_Config 