# Servidor para DataExtractorMod

Este es un servidor simple desarrollado en Flask para recibir y almacenar los datos enviados por el mod DataExtractorMod para The Binding of Isaac.

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Flask
- pandas
- matplotlib
- numpy
- scikit-learn

## Instalación

1. Clona este repositorio o descarga los archivos
2. Crea un entorno virtual (recomendado):
   ```
   python -m venv venv
   ```
3. Activa el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
5. Copia `.env.example` a `.env` y configura las variables según tus necesidades:
   ```
   cp .env.example .env
   ```

## Uso

1. Inicia el servidor:
   ```
   python app.py
   ```
2. El servidor estará disponible en `http://localhost:8000`

## Endpoints API

- `GET /api/health` - Comprueba si el servidor está funcionando
- `POST /api/data` - Recibe datos del mod

## Interfaz Web de Visualización

El servidor incluye una interfaz web para visualizar los datos extraídos y procesados:

1. **Página principal**: http://localhost:8000/
   - Muestra información general sobre el servidor
   - Proporciona enlaces a todas las secciones de visualización

2. **Datos extraídos**: http://localhost:8000/view/raw
   - Muestra todos los datos extraídos del juego en formato de tarjetas
   - Organiza la información de manera clara y legible

3. **Datos procesados**: http://localhost:8000/view/processed
   - Muestra una tabla con los datos procesados
   - Incluye visualizaciones gráficas como:
     - Gráfico de salud a lo largo del tiempo
     - Distribución de enemigos por habitación
   - Permite procesar los datos directamente desde la interfaz

4. **Estadísticas**: http://localhost:8000/view/stats
   - Muestra estadísticas generales sobre los datos
   - Incluye métricas como número de registros, habitaciones únicas, salud promedio, etc.

5. **Procesamiento de datos**: http://localhost:8000/process/data
   - Procesa los datos recibidos y genera archivos CSV y estadísticas
   - Redirige automáticamente a la página de visualización de datos procesados

## Estructura de datos

El servidor espera recibir datos en formato JSON. Un ejemplo de la estructura esperada:

```json
{
  "room_id": 12345,
  "health": 6,
  "position": {
    "x": 123.45,
    "y": 67.89
  },
  "enemies": 5,
  "timestamp": "2023-03-16T12:34:56"
}
```

## Almacenamiento

- **Datos recibidos**: Se almacenan en la carpeta `received_data` en archivos JSON individuales con nombres basados en timestamps.
- **Datos procesados**: Se almacenan en la carpeta `processed_data` en formato CSV y pickle.
- **Estadísticas**: Se guardan en `processed_data/statistics.json`.

## Configuración del mod

Para que el mod envíe datos a este servidor, configura el archivo `config.lua` del mod con:

```lua
Config.SERVER_URL = "http://localhost:8000/api/data"
```

## Solución de problemas

- Si el servidor no inicia, verifica que el puerto 8000 no esté en uso
- Revisa los logs en `server.log` para más información sobre errores
- Asegúrate de que el firewall permita conexiones al puerto configurado
- Si aparece el error "No module named 'pandas'" u otro similar, ejecuta `pip install -r requirements.txt` para instalar las dependencias faltantes 