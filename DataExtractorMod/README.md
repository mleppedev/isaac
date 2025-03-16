# DataExtractorMod

Mod para The Binding of Isaac: Rebirth que extrae datos relevantes del juego para entrenar una IA.

## Instalación

1. Coloca esta carpeta en el directorio de mods de The Binding of Isaac:
   - **Steam**: `{SteamInstallPath}\Steam\userdata\{tuSteamID}\250900\mods`
   - **No-Steam**: `Documentos\My Games\Binding of Isaac Rebirth\mods`

2. Activa el mod desde el menú de mods en el juego.

## Configuración de Variables de Entorno

Para proteger información sensible, este mod utiliza un sistema de variables de entorno:

1. El archivo `config.example.lua` muestra la estructura de configuración necesaria.
2. Copia `config.example.lua` como `config.lua` y edita los valores según tus necesidades:
   ```lua
   Config.API_KEY = "tu_api_key_aquí"
   Config.SERVER_URL = "url_de_tu_servidor_aquí"
   Config.USER_ID = "tu_id_de_usuario_aquí"
   ```
3. El archivo `config.lua` está incluido en `.gitignore` para evitar subir información sensible al repositorio.

## Funcionamiento

El mod recopila información durante el juego:
- Salud del jugador
- Posición del jugador
- Número de enemigos en la habitación
- Otros datos relevantes

Esta información se guarda en un archivo de texto (`extracted_data.txt`) y opcionalmente se envía a un servidor si está configurado.

## Personalización

Puedes modificar `main.lua` para recopilar datos adicionales según tus necesidades específicas de entrenamiento de IA.

## Solución de Problemas

Si encuentras algún problema con el mod:
1. Verifica que los archivos estén en la ubicación correcta
2. Comprueba que `config.lua` esté correctamente configurado
3. Revisa la consola del juego para mensajes de error (si está habilitada)

## Nota Importante

Este mod está diseñado para fines educativos y de investigación. Úsalo de manera responsable y respeta los términos de servicio del juego. 