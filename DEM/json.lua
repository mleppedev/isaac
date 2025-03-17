--[[
    JSON for Lua
    Biblioteca ligera para codificar/decodificar JSON en Lua
    Adaptada para The Binding of Isaac
]]

local json = {}

-- Caracteres que necesitan escape
local escapes = {
    ['"'] = '\\"',
    ['\\'] = '\\\\',
    ['/'] = '\\/',
    ['\b'] = '\\b',
    ['\f'] = '\\f',
    ['\n'] = '\\n',
    ['\r'] = '\\r',
    ['\t'] = '\\t'
}

-- Codifica un valor a JSON
local function encode_value(val)
    local val_type = type(val)
    
    if val_type == "nil" then
        return "null"
    elseif val_type == "boolean" then
        return val and "true" or "false"
    elseif val_type == "number" then
        -- Convertir NaN e infinito a null como en JSON estándar
        if val ~= val or val >= math.huge or val <= -math.huge then
            return "null"
        end
        return tostring(val)
    elseif val_type == "string" then
        -- Escapar caracteres especiales
        return '"' .. val:gsub('["\\/\b\f\n\r\t]', escapes) .. '"'
    elseif val_type == "table" then
        -- Comprobar si es un array (índices numéricos consecutivos)
        local is_array = true
        local max_index = 0
        for k, _ in pairs(val) do
            if type(k) ~= "number" or k < 1 or math.floor(k) ~= k then
                is_array = false
                break
            end
            max_index = math.max(max_index, k)
        end
        
        if is_array and max_index > 0 then
            -- Es un array
            local res = {}
            for i = 1, max_index do
                res[i] = encode_value(val[i] or nil)
            end
            return "[" .. table.concat(res, ",") .. "]"
        else
            -- Es un objeto
            local res = {}
            for k, v in pairs(val) do
                if type(k) == "string" and v ~= nil then
                    table.insert(res, encode_value(k) .. ":" .. encode_value(v))
                end
            end
            return "{" .. table.concat(res, ",") .. "}"
        end
    else
        -- Otros tipos no son soportados por JSON
        return "null"
    end
end

-- Función pública para codificar a JSON
function json.encode(val)
    return encode_value(val)
end

-- Funciones para decodificar JSON
local function decode_next(str, pos)
    -- Saltar espacios en blanco
    pos = str:find("[^ \t\r\n]", pos) or pos
    
    local first = str:sub(pos, pos)
    
    if first == "{" then
        -- Objeto
        local obj = {}
        local pos = pos + 1
        
        -- Saltar espacios iniciales
        pos = str:find("[^ \t\r\n]", pos) or pos
        
        -- Objeto vacío
        if str:sub(pos, pos) == "}" then
            return obj, pos + 1
        end
        
        while true do
            -- Leer clave
            local key, new_pos = decode_next(str, pos)
            if type(key) ~= "string" then
                error("Expected string key in object at position " .. pos)
            end
            
            -- Buscar los dos puntos
            pos = str:find(":", new_pos) or new_pos
            if pos ~= new_pos then
                pos = pos + 1
            else
                error("Expected ':' after key in object at position " .. new_pos)
            end
            
            -- Leer valor
            local val, new_pos = decode_next(str, pos)
            obj[key] = val
            pos = new_pos
            
            -- Buscar coma o fin del objeto
            pos = str:find("[},]", pos) or pos
            local delim = str:sub(pos, pos)
            
            if delim == "}" then
                return obj, pos + 1
            elseif delim == "," then
                pos = pos + 1
            else
                error("Expected ',' or '}' in object at position " .. pos)
            end
        end
    
    elseif first == "[" then
        -- Array
        local arr = {}
        local pos = pos + 1
        local index = 1
        
        -- Saltar espacios iniciales
        pos = str:find("[^ \t\r\n]", pos) or pos
        
        -- Array vacío
        if str:sub(pos, pos) == "]" then
            return arr, pos + 1
        end
        
        while true do
            -- Leer valor
            local val, new_pos = decode_next(str, pos)
            arr[index] = val
            index = index + 1
            pos = new_pos
            
            -- Buscar coma o fin del array
            pos = str:find("[%],]", pos) or pos
            local delim = str:sub(pos, pos)
            
            if delim == "]" then
                return arr, pos + 1
            elseif delim == "," then
                pos = pos + 1
            else
                error("Expected ',' or ']' in array at position " .. pos)
            end
        end
    
    elseif first == '"' then
        -- String
        local value, ending = str:match('"(.-)()"', pos)
        if not ending then 
            error("Unterminated string at position " .. pos)
        end
        -- Buscar la posición real del cierre de comillas
        local close_pos = pos + 1
        local escaped = false
        while close_pos <= #str do
            local c = str:sub(close_pos, close_pos)
            if c == '\\' then
                escaped = not escaped
            elseif c == '"' and not escaped then
                break
            else
                escaped = false
            end
            close_pos = close_pos + 1
        end
        local raw_str = str:sub(pos + 1, close_pos - 1)
        -- Procesar escapes
        raw_str = raw_str:gsub('\\(.)', function(c)
            if c == 'n' then return '\n'
            elseif c == 'r' then return '\r'
            elseif c == 't' then return '\t'
            elseif c == 'b' then return '\b'
            elseif c == 'f' then return '\f'
            else return c end
        end)
        return raw_str, close_pos + 1
    
    elseif str:match('^%d', pos) or str:match('^-[%d]', pos) then
        -- Número
        local num_str = str:match('^-?%d+%.?%d*[eE]?[+-]?%d*', pos)
        local val = tonumber(num_str)
        if not val then
            error("Invalid number at position " .. pos)
        end
        return val, pos + #num_str
    
    elseif str:sub(pos, pos + 3) == "true" then
        return true, pos + 4
    
    elseif str:sub(pos, pos + 4) == "false" then
        return false, pos + 5
    
    elseif str:sub(pos, pos + 3) == "null" then
        return nil, pos + 4
    
    else
        error("Unexpected character at position " .. pos .. ": " .. str:sub(pos, pos))
    end
end

-- Función pública para decodificar JSON
function json.decode(str)
    if type(str) ~= "string" then
        error("Expected string argument, got " .. type(str))
    end
    
    if str == "" then
        error("Cannot decode empty string")
    end
    
    local success, result = pcall(function()
        local val, pos = decode_next(str, 1)
        return val, pos
    end)
    
    if not success then
        error("Invalid JSON: " .. result)
    end
    
    local val, pos = result, result[2]
    
    -- Asegurarse de que no haya contenido extra después del JSON válido
    pos = str:find("[^ \t\r\n]", pos) or #str + 1
    if pos <= #str then
        error("Unexpected trailing character at position " .. pos)
    end
    
    return val
end

return json 