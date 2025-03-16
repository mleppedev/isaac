# Proyecto de Extracción de Datos de The Binding of Isaac para IA

Este proyecto consiste en un sistema para extraer datos del juego The Binding of Isaac: Rebirth, procesarlos y utilizarlos para entrenar modelos de inteligencia artificial.

## Estructura del Proyecto

El proyecto está dividido en dos componentes principales:

1. **Mod para The Binding of Isaac** (carpeta `DataExtractorMod`)
   - Extrae datos del juego en tiempo real
   - Guarda los datos localmente y/o los envía a un servidor

2. **Servidor y Procesamiento** (carpeta `server`)
   - Recibe y almacena los datos enviados por el mod
   - Procesa los datos para su uso en entrenamiento de IA
   - Entrena modelos de IA con los datos procesados

## Requisitos

### Para el Mod
- The Binding of Isaac: Rebirth (con Afterbirth+ o Repentance)
- Python 3.8+ (para el script auxiliar de envío de datos)

### Para el Servidor
- Python 3.8+
- Flask
- pandas
- scikit-learn
- matplotlib
- numpy

## Instalación

### Mod
1. Coloca la carpeta `DataExtractorMod` en el directorio de mods de The Binding of Isaac:
   - **Steam**: `{SteamInstallPath}\Steam\userdata\{tuSteamID}\250900\mods`
   - **No-Steam**: `Documentos\My Games\Binding of Isaac Rebirth\mods`
2. Configura el archivo `config.lua` con tus ajustes (copia `config.example.lua` como `config.lua`)
3. Activa el mod desde el menú de mods en el juego

### Servidor
1. Navega a la carpeta `server`
2. Crea un entorno virtual: `python -m venv venv`
3. Activa el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instala las dependencias: `pip install -r requirements.txt`
5. Configura el archivo `.env` (copia `.env.example` como `.env`)

## Uso

### Flujo de Trabajo Completo

1. **Iniciar el servidor**:
   ```
   cd server
   python app.py
   ```

2. **Jugar al juego con el mod activado**:
   - Los datos se extraerán automáticamente durante el juego
   - Se guardarán localmente en `extracted_data.txt`
   - Se prepararán para envío en `pending_data.json`

3. **Enviar datos al servidor**:
   ```
   cd DataExtractorMod
   python send_data.py
   ```

4. **Procesar los datos recibidos**:
   ```
   cd server
   python process_data.py
   ```

5. **Entrenar un modelo de IA**:
   ```
   cd server
   python train_model.py
   ```

## Personalización

### Mod
- Modifica `main.lua` para extraer datos adicionales del juego
- Ajusta la frecuencia de extracción o los eventos que la desencadenan

### Servidor
- Modifica `process_data.py` para realizar diferentes transformaciones en los datos
- Ajusta `train_model.py` para utilizar diferentes algoritmos de IA o hiperparámetros

## Solución de Problemas

### Mod
- Verifica que los archivos estén en la ubicación correcta
- Comprueba que `config.lua` esté correctamente configurado
- Revisa la consola del juego para mensajes de error (si está habilitada)

### Servidor
- Verifica que el puerto 8000 no esté en uso por otra aplicación
- Revisa los logs en `server.log` para más información sobre errores
- Asegúrate de que el firewall permita conexiones al puerto configurado

## Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:
1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Haz push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un Pull Request

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).

## Agradecimientos

- Nicalis y Edmund McMillen por crear The Binding of Isaac
- La comunidad de modding de Isaac por su documentación y ejemplos 