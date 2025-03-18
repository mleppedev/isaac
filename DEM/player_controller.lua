--[[
    player_controller.lua
    Sistema de control para permitir tomar el control del personaje,
    inicialmente para pruebas manuales y posteriormente para IA.
    
    Este módulo permite:
    1. Interceptar entradas del usuario
    2. Simular entradas programáticamente 
    3. Tomar el control del personaje
    4. Alternar entre control manual y automático
]]

local PlayerController = {}

-- Configuración del controlador
PlayerController.config = {
    enabled = false,             -- Si el controlador está activo
    ai_control = false,          -- Si la IA está controlando al personaje
    override_inputs = true,      -- Si se deben anular las entradas reales del usuario cuando en modo IA
    debug_mode = true,           -- Mostrar información de depuración
    movement_keys = {            -- Teclas de movimiento WASD
        up = Keyboard.KEY_W,
        down = Keyboard.KEY_S, 
        left = Keyboard.KEY_A,
        right = Keyboard.KEY_D
    },
    shoot_keys = {               -- Teclas de disparo (flechas)
        up = Keyboard.KEY_UP,
        down = Keyboard.KEY_DOWN,
        left = Keyboard.KEY_LEFT,
        right = Keyboard.KEY_RIGHT
    }
}

-- Estado actual de las entradas virtuales
PlayerController.virtual_inputs = {
    movement = {
        up = 0,
        down = 0,
        left = 0,
        right = 0
    },
    shooting = {
        up = 0,
        down = 0,
        left = 0,
        right = 0
    }
}

-- Diccionario de mapeo entre acciones y botones de control
PlayerController.action_mapping = {
    [ButtonAction.ACTION_UP] = "movement.up",
    [ButtonAction.ACTION_DOWN] = "movement.down",
    [ButtonAction.ACTION_LEFT] = "movement.left",
    [ButtonAction.ACTION_RIGHT] = "movement.right",
    [ButtonAction.ACTION_SHOOTUP] = "shooting.up",
    [ButtonAction.ACTION_SHOOTDOWN] = "shooting.down",
    [ButtonAction.ACTION_SHOOTLEFT] = "shooting.left",
    [ButtonAction.ACTION_SHOOTRIGHT] = "shooting.right"
}

-- Función auxiliar para establecer un valor anidado
local function set_nested_value(tbl, key_path, value)
    local keys = {}
    for k in string.gmatch(key_path, "[^%.]+") do
        table.insert(keys, k)
    end
    
    local current = tbl
    for i = 1, #keys - 1 do
        current = current[keys[i]]
    end
    
    current[keys[#keys]] = value
end

-- Función auxiliar para obtener un valor anidado
local function get_nested_value(tbl, key_path)
    local keys = {}
    for k in string.gmatch(key_path, "[^%.]+") do
        table.insert(keys, k)
    end
    
    local current = tbl
    for i = 1, #keys do
        if current == nil then return nil end
        current = current[keys[i]]
    end
    
    return current
end

-- Inicializar el controlador
function PlayerController:init(mod)
    self.mod = mod
    
    -- Registrar callback para interceptar entradas
    if mod then
        mod:AddCallback(ModCallbacks.MC_INPUT_ACTION, function(_, entity, input_hook, button_action)
            return self:onInputAction(entity, input_hook, button_action)
        end)
        
        mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
            self:onRender()
        end)
        
        -- Agregar un callback para teclado si necesitamos detectar teclas adicionales
        mod:AddCallback(ModCallbacks.MC_POST_UPDATE, function()
            self:onUpdate()
        end)
    end
    
    -- Iniciar en estado desactivado
    self.config.enabled = false
    self.config.ai_control = false
    
    return self
end

-- Función para activar/desactivar el controlador
function PlayerController:toggle()
    self.config.enabled = not self.config.enabled
    
    if self.config.debug_mode then
        if self.config.enabled then
            Isaac.DebugString("PlayerController: Activado")
        else
            Isaac.DebugString("PlayerController: Desactivado")
        end
    end
    
    return self.config.enabled
end

-- Función para activar/desactivar el control de IA
function PlayerController:toggleAI()
    self.config.ai_control = not self.config.ai_control
    
    if self.config.debug_mode then
        if self.config.ai_control then
            Isaac.DebugString("PlayerController: Modo IA activado")
        else
            Isaac.DebugString("PlayerController: Modo IA desactivado")
        end
    end
    
    return self.config.ai_control
end

-- Procesar entrada del usuario y determinar si la interceptamos
function PlayerController:onInputAction(entity, input_hook, button_action)
    -- Si el controlador no está activado, no interceptamos nada
    if not self.config.enabled then
        return nil
    end
    
    -- Verificar si esta acción es una que queremos controlar
    local action_path = self.action_mapping[button_action]
    if not action_path then
        return nil -- No es una acción que queramos interceptar
    end
    
    -- Si está en modo IA y queremos anular las entradas reales
    if self.config.ai_control and self.config.override_inputs then
        local virtual_value = get_nested_value(self.virtual_inputs, action_path) or 0
        
        -- Si estamos en modo AI y hay un valor virtual, lo usamos
        if virtual_value > 0 then
            return virtual_value
        else
            return 0 -- Anular entrada real si no hay virtual
        end
    end
    
    -- En otros casos, no interferimos con la entrada
    return nil
end

-- Actualización por frame para detectar teclas adicionales
function PlayerController:onUpdate()
    if not self.config.enabled then
        return
    end
    
    -- Verificar tecla de activación/desactivación (Tab por defecto)
    if Input.IsButtonTriggered(Keyboard.KEY_TAB, 0) then
        self:toggleAI()
    end
    
    -- Si no está en modo IA, verificar entradas WASD y flechas
    if not self.config.ai_control then
        -- Movimiento WASD
        self.virtual_inputs.movement.up = Input.IsButtonPressed(self.config.movement_keys.up, 0) and 1 or 0
        self.virtual_inputs.movement.down = Input.IsButtonPressed(self.config.movement_keys.down, 0) and 1 or 0
        self.virtual_inputs.movement.left = Input.IsButtonPressed(self.config.movement_keys.left, 0) and 1 or 0
        self.virtual_inputs.movement.right = Input.IsButtonPressed(self.config.movement_keys.right, 0) and 1 or 0
        
        -- Disparo flechas
        self.virtual_inputs.shooting.up = Input.IsButtonPressed(self.config.shoot_keys.up, 0) and 1 or 0
        self.virtual_inputs.shooting.down = Input.IsButtonPressed(self.config.shoot_keys.down, 0) and 1 or 0
        self.virtual_inputs.shooting.left = Input.IsButtonPressed(self.config.shoot_keys.left, 0) and 1 or 0
        self.virtual_inputs.shooting.right = Input.IsButtonPressed(self.config.shoot_keys.right, 0) and 1 or 0
    end
end

-- Renderizar información de depuración
function PlayerController:onRender()
    if not self.config.enabled or not self.config.debug_mode then
        return
    end
    
    -- Mostrar estado actual en pantalla
    local text = ""
    if self.config.ai_control then
        text = "Modo: IA"
    else
        text = "Modo: Manual (WASD + Flechas)"
    end
    
    -- Mostrar valores de entrada virtuales
    local y_pos = 50
    Isaac.RenderText(text, 50, y_pos, 1, 1, 1, 1)
    y_pos = y_pos + 15
    
    -- Mostrar estados de teclas
    for section, inputs in pairs(self.virtual_inputs) do
        Isaac.RenderText(section .. ":", 50, y_pos, 1, 1, 1, 1)
        y_pos = y_pos + 12
        
        for dir, value in pairs(inputs) do
            local color = value > 0 and "1,0,0" or "0.5,0.5,0.5"
            Isaac.RenderText("  " .. dir .. ": " .. value, 50, y_pos, 1, 1, 1, 1)
            y_pos = y_pos + 10
        end
        y_pos = y_pos + 5
    end
end

-- Establecer una acción de movimiento o disparo programáticamente (para IA)
function PlayerController:setAction(action_type, direction, value)
    if not self.virtual_inputs[action_type] then
        return false
    end
    
    if not self.virtual_inputs[action_type][direction] then
        return false
    end
    
    -- Limitar valor entre 0 y 1
    value = math.max(0, math.min(1, value))
    
    -- Establecer el valor
    self.virtual_inputs[action_type][direction] = value
    
    return true
end

-- Mover en una dirección específica (función de ayuda para IA)
function PlayerController:move(direction, value)
    return self:setAction("movement", direction, value)
end

-- Disparar en una dirección específica (función de ayuda para IA)
function PlayerController:shoot(direction, value)
    return self:setAction("shooting", direction, value)
end

-- Limpiar todas las entradas (útil para resetear estado)
function PlayerController:clearInputs()
    for action_type, directions in pairs(self.virtual_inputs) do
        for direction, _ in pairs(directions) do
            self.virtual_inputs[action_type][direction] = 0
        end
    end
end

return PlayerController 