# Referencias para el Desarrollo

## API Principales
- **Game**: Controla el estado general del juego
  - Constructor: `local game = Game()`
  - Funciones clave: 
    - `GetRoom()`: Obtiene la habitación actual
    - `IsPaused()`: Comprueba si el juego está pausado
    - `AddPixelation(int Duration)`: Aplica efecto de pixelación
    - `GetPlayer()`: Obtiene el jugador activo

- **Isaac**: Funciones globales para interactuar con el juego
  - Tabla global que no requiere instanciación
  - Uso: `Isaac.NombreFuncion()` (usar punto, no dos puntos)
  - Funciones clave:
    - `GetPlayer()`: Obtiene el jugador principal
    - `AddCallback(modRef, callbackId, callbackFn, entityId)`: Registra callbacks
    - `ConsoleOutput(string text)`: Imprime texto en la consola de depuración

- **EntityPlayer**: Manipulación y control del jugador
  - Acceso: `local player = Isaac.GetPlayer()`
  - Funciones clave:
    - `AddBlackHearts(int BlackHearts)`: Añade corazones negros (2 = 1 corazón completo)
    - `AddBlueFlies(int Amount, Vector Position, Entity Target)`: Añade moscas azules
    - `AddCollectible(int Type, int Charge, bool AddConsumables)`: Añade objetos coleccionables

- **Entity**: Base para todas las entidades del juego
  - Métodos para convertir: `ToPlayer()`, `ToNPC()`, `ToFamiliar()`, etc.
  - Propiedades importantes: `Position`, `Velocity`, `HitPoints`, `Visible`
  - Métodos para manipulación: `Remove()`, `Kill()`, `Update()`

- **Room**: Manipulación de habitaciones
  - Acceso: `local room = Game():GetRoom()`
  - Funciones clave:
    - `CheckLine(Vector Pos1, Vector Pos2, LinecheckMode)`: Verifica colisiones entre dos puntos
    - `GetGridEntity(int Index)`: Obtiene entidades de la cuadrícula
    - `SpawnGridEntity(int Type, int Variant, int Seed, int Index)`: Genera entidades en la cuadrícula

- **Level**: Control del nivel actual
  - Acceso: `local level = Game():GetLevel()`
  - Propiedades importantes: `Stage`, `StageType`, `CursorIndex`
  - Métodos para manipulación: `GetCurrentRoom()`, `GetCurrentRoomIndex()`

## Entidades
- **EntityNPC**: NPCs y enemigos
  - Hereda de Entity
  - Propiedades específicas: `State`, `StateFrame`, `Target`, `CanShutDoors`
  - Métodos importantes: `MakeChampion()`, `Morph()`

- **EntityFamiliar**: Familiares que siguen al jugador
  - Hereda de Entity
  - Propiedad clave: `Player` para acceder al jugador propietario
  - Métodos importantes: `PickEnemyTarget()`, `MoveDiagonally()`

- **EntityPickup**: Objetos recogibles
  - Hereda de Entity
  - Propiedades específicas: `Timeout`, `Price`, `OptionsPickupIndex`
  - Métodos importantes: `IsShopItem()`, `CanReroll()`

- **EntityTear**: Lágrimas disparadas
  - Hereda de Entity
  - Propiedades específicas: `TearFlags`, `Scale`, `FallingSpeed`, `FallingAcceleration`
  - Métodos importantes: `ChangeVariant()`, `SetColor()`

- **EntityLaser**: Rayos láser
  - Hereda de Entity
  - Tipos: `LaserVariant.THIN_RED`, `LaserVariant.BRIMSTONE`, etc.
  - Métodos importantes: `SetTimeout()`, `SetBlackHpDropChance()`

- **EntityBomb**: Bombas
  - Hereda de Entity
  - Propiedades específicas: `IsFetus`, `ExplosionDamage`, `Flags`
  - Métodos importantes: `SetExplosionCountdown()`, `AddTearFlags()`

- **EntityEffect**: Efectos visuales
  - Hereda de Entity
  - Sin colisión, principalmente visuales
  - Variantes comunes: `EffectVariant.BLOOD`, `EffectVariant.EXPLOSION`

- **EntityProjectile**: Proyectiles
  - Hereda de Entity
  - Propiedades específicas: `ProjectileFlags`, `ChangeTimeout`, `ChangeVelocity`
  - Métodos importantes: `AddProjectileFlags()`, `AddFallingAccel()`

## Utilidades
- **Vector**: Manipulación de posiciones y velocidades
  - Constructor: `Vector(float X, float Y)`
  - Operaciones matemáticas: suma, resta, multiplicación, división
  - Métodos importantes: `Length()`, `Normalized()`, `Rotated()`

- **Color/KColor**: Manejo de colores
  - Color: Constructor `Color(float R, float G, float B, float A, float RO, float GO, float BO)`
  - KColor: Constructor `KColor(float R, float G, float B, float A)`
  - Diferencia: Color acepta valores de saturación (tint overlay)

- **RNG**: Generación de números aleatorios
  - Constructor: `RNG()`
  - Métodos importantes: `SetSeed()`, `Next()`, `RandomInt()`, `RandomFloat()`
  - Uso típico para reproducibilidad: `rng:SetSeed(seed)`

- **Sprite**: Renderizado de gráficos
  - Constructor: `Sprite()`
  - Métodos importantes: `Load()`, `Play()`, `Render()`, `IsFinished()`
  - Carga de archivos ANM2: `sprite:Load("gfx/effects.anm2", true)`

- **Font**: Renderizado de texto
  - Método global: `Font()`
  - Métodos importantes: `DrawString()`, `DrawStringUTF8()`, `GetStringWidth()`
  - Configuración: `FontRenderSettings` para color, escala, etc.

- **Input**: Control de entrada del usuario
  - Acceso: `Input`
  - Métodos importantes: `IsActionPressed()`, `IsButtonPressed()`, `IsActionTriggered()`
  - Constantes: `ButtonAction`, `Keyboard`, `Controller`

## Configuración
- **ItemConfig**: Información sobre objetos
  - Acceso: `Isaac.GetItemConfig()`
  - Métodos importantes: `GetCollectible()`, `GetCard()`, `GetPillEffect()`
  - Datos disponibles: nombre, descripción, estadísticas, tipo

- **ItemPool**: Manipulación de pools de objetos
  - Acceso: `Game():GetItemPool()`
  - Métodos importantes: `AddRoomBlacklist()`, `GetCard()`, `RemoveCollectible()`
  - Pools: `ItemPoolType.POOL_TREASURE`, `POOL_BOSS`, etc.

- **Options**: Opciones del juego
  - Acceso: `Options`
  - Propiedades: `ChargeBars`, `ScreenShake`, `Filter`, `HUDOffset`
  - Valores guardados: controla opciones de juego persistentes

- **SFXManager**: Efectos de sonido
  - Acceso: `SFXManager()`
  - Métodos importantes: `Play()`, `Stop()`, `AdjustVolume()`, `AdjustPitch()`
  - Identificadores: `SoundEffect.SOUND_*`

- **MusicManager**: Música del juego
  - Acceso: `MusicManager()`
  - Métodos importantes: `Play()`, `Fadein()`, `Fadeout()`, `Crossfade()`
  - Identificadores: `Music.MUSIC_*`

## Elementos de Habitación
- **GridEntity**: Entidades de cuadrícula base
  - Acceso: `room:GetGridEntity(index)`
  - Tipos: `GridEntityType.GRID_*`
  - Métodos importantes: `Update()`, `Destroy()`, `ToRock()`

- **GridEntityRock**: Rocas
  - Hereda de GridEntity
  - Tipos: `RockVariant.*`
  - Métodos específicos: `SetRockType()`, `Destroy()`

- **GridEntityPit**: Pozos
  - Hereda de GridEntity
  - Variantes: `PitVariant.*`
  - Métodos específicos: `MakeBridge()`, `SetLadder()`

- **GridEntityDoor**: Puertas
  - Hereda de GridEntity
  - Estados: `DoorState.STATE_*` (cerrado, abierto, etc.)
  - Métodos específicos: `Open()`, `Close()`, `IsOpen()`

- **GridEntityTNT**: TNT
  - Hereda de GridEntity
  - Propiedades: `FrameCount`, `State`
  - Métodos específicos: `Explode()`, `SetAnimation()`

- **GridEntityPoop**: Caca
  - Hereda de GridEntity
  - Variantes: `PoopVariant.*` (normal, dorada, etc.)
  - Métodos específicos: `SetPoopState()`, `Destroy()`

- **GridEntityPressurePlate**: Placas de presión
  - Hereda de GridEntity
  - Propiedades: `Pressed`, `TimerBeforeReset`
  - Métodos específicos: `Press()`, `Reset()`

## Tutoriales Útiles
- **CustomCallbacks**: Creación de callbacks personalizados
  - Define identificadores únicos: `mod.NOMBRE_CALLBACK = Isaac.GetCallbackIdentifier("NombreUnico")`
  - Registra listeners: `mod:AddCallback(mod.NOMBRE_CALLBACK, función)`
  - Dispara callbacks: `mod:TriggerCallback(mod.NOMBRE_CALLBACK, ...)`

- **GoodPractices**: Buenas prácticas para el desarrollo
  - Evitar micro-optimizaciones prematuras
  - Uso de "local" para variables
  - Organización modular del código
  - Evitar tablas globales

- **Using-Additional-Lua-Files**: Organización de archivos Lua
  - Estructura recomendada: main.lua como punto de entrada
  - Inclusión de archivos: `include("carpeta.archivo")`
  - Uso de require: `local modulo = require("modulo")`

- **FunctionsInLua**: Uso de funciones en Lua
  - Funciones locales vs métodos
  - Uso de colon (:) vs punto (.)
  - Funciones anónimas y closures
  - Argumentos con valores por defecto

- **MathAndLuaTips**: Consejos para matemáticas y Lua
  - Funciones matemáticas: `math.abs()`, `math.sin()`, etc.
  - Manejo de números aleatorios
  - Optimización de cálculos repetitivos
  - Interpolación lineal: `Lerp(a, b, t)`

- **Tutorial-Rendertext**: Renderizado de texto
  - Uso de fuentes: `font:LoadFont()`, `font:DrawString()`
  - Formato de texto: colores, tamaños, alineación
  - Optimización de renderizado
  - Localización y texto multi-idioma

## Nuevos Descubrimientos: Renderización de Texto

### Fuentes del Juego Disponibles
Las siguientes fuentes están incluidas en el juego y pueden ser utilizadas:

- **upheaval.fnt**: Fuente de títulos y streaks (textos animados). Muy grande y en negrita.
- **teammeatfont16.fnt**: Fuente de menús, tamaño grande. Buena legibilidad.
- **teammeatfont12.fnt**: Versión más pequeña de la fuente de menús.
- **pftempestasevencondensed.fnt**: Fuente usada en el HUD para contadores de items.
- **terminus.fnt**: Fuente de consola, más compacta y técnica.
- **droid.fnt**: Fuente usada para información de depuración.
- **luamini.fnt**: (Repentance) Fuente para estadísticas del HUD.

### Uso de la Clase Font

```lua
-- Inicialización y carga de fuente
local myFont = Font() -- Crear objeto Font
myFont:Load("font/upheaval.fnt") -- Cargar una fuente específica

-- Verificación de carga
if myFont:IsLoaded() then
  -- La fuente se cargó correctamente
end

-- Renderizado de texto
-- Método básico:
myFont:DrawString("Texto de ejemplo", 100, 100, KColor(1, 1, 1, 1), 0, true)

-- Renderizado con escalado (para texto más pequeño):
local scaleX = 0.5 -- Factor de escala horizontal
local scaleY = 0.5 -- Factor de escala vertical
myFont:DrawStringScaled("Texto de ejemplo", 100, 100, scaleX, scaleY, KColor(1, 1, 1, 1), 0, true)
```

### Centrado de Texto

Para centrar texto correctamente, especialmente cuando se usa escalado:

```lua
-- Obtener dimensiones de pantalla
local screenWidth = Isaac.GetScreenWidth() or 960

-- Calcular ancho del texto (considerando escalado)
local text = "Texto a centrar"
local scale = 0.5
local textWidth = myFont:GetStringWidth(text) * scale

-- Calcular posición centrada
local centerX = (screenWidth / 2) - (textWidth / 2)

-- Renderizar texto centrado
myFont:DrawStringScaled(text, centerX, 100, scale, scale, KColor(1, 1, 1, 1), 0, true)
```

### Colores con KColor

KColor es la clase recomendada para definir colores en el renderizado de texto:

```lua
-- Definición de colores usando KColor(R, G, B, A)
local whiteColor = KColor(1, 1, 1, 1)
local redColor = KColor(1, 0, 0, 1)
local greenColor = KColor(0, 1, 0, 1)
local blueColor = KColor(0, 0, 1, 1)
local grayColor = KColor(0.7, 0.7, 0.7, 0.8) -- Semitransparente
```

### Notas Importantes

- El método `IsLoaded()` debe usarse para verificar que la fuente se cargó correctamente.
- Para alinear texto, usar el parámetro `BoxWidth` (0 para desactivar) y `Center` (true/false).
- `GetStringWidth()` es esencial para cálculos de centrado precisos.
- Los textos escalados con `DrawStringScaled()` conservan buena calidad visual.
- El renderizado de texto debe realizarse en el callback `MC_POST_RENDER`.

### Cargar Fuentes Personalizadas
Para cargar fuentes personalizadas desde tu mod:

```lua
local MOD_FOLDER_NAME = "mymod" -- Nombre de tu carpeta del mod
local CUSTOM_FONT_FILE_PATH = "font/mifuente.fnt" -- Ruta relativa a resources

local myFont = Font()
myFont:Load("mods/" .. MOD_FOLDER_NAME .. "/resources/" .. CUSTOM_FONT_FILE_PATH)
```

## Herramientas
- **DebugConsole**: Depuración del juego
  - Comandos disponibles: `luamod`, `spawn`, `goto`
  - Depuración visual: `debug [índice]`
  - Depuración de colisiones: `debug 3`
  - Registro de comandos personalizados: `Isaac.RegisterConsoleCommand()`

- **Tools**: Herramientas de desarrollo disponibles
  - Debug Console: depuración en tiempo real
  - Anm2Explorer: edición de animaciones
  - Basement Renovator: editor de salas
  - XML Validator: validación de archivos XML

- **AnimationEditor**: Editor de animaciones
  - Formato ANM2
  - Elementos: frames, capas, eventos
  - Integración con sprites
  - Técnicas para crear animaciones fluidas

- **ItemPoolEditor**: Editor de pools de objetos
  - Edición de pesos y rareza de objetos
  - Personalización de pools por nivel
  - Configuración de paquetes de objetos
  - Bloqueo y desbloqueo de objetos

## Estructuras de Datos
- **CppContainer_Vector**: Contenedores de tipo vector
  - Similar a tablas de Lua
  - Acceso: `vector:Get(index)` (1-indexed)
  - Recorrido: `for i=0, vector:Size()-1 do`
  - Operaciones: `vector:Add()`, `vector:Remove()`

- **CppContainer_EntityList**: Lista de entidades
  - Recorrido: `for _, entity in ipairs(list)`
  - Filtrado por tipo: `list:CountEntities(Type, Variant, SubType)`
  - Operaciones: `list:Add()`, `list:Remove()`

- **BitSet128**: Conjunto de bits
  - Constructor: `BitSet128(Low, High)`
  - Operaciones: `HasBit()`, `SetBit()`, `ClearBit()`
  - Operadores: `&` (AND), `|` (OR), `~` (NOT)

## Almacenamiento de Datos
- **directories-and-save-files**: Información sobre directorios y archivos de guardado
  - Directorios disponibles: documentos, mods, etc.
  - Rutas específicas para datos guardados
  - Persistencia entre sesiones de juego
  - Uso de `Isaac.SaveModData()` y `Isaac.LoadModData()`

- **storing-data**: Métodos para almacenar datos
  - Datos globales vs locales
  - Serialización (JSON)
  - Persistencia entre partidas
  - Límites y restricciones

Esta lista representa los elementos principales que pueden ser útiles para el desarrollo del proyecto, basados en la documentación disponible en docs-local/IsaacDocs-main, con detalles técnicos específicos para cada componente.
