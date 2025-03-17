from flask import Flask, request, jsonify, render_template_string
import os
import json
import glob
from datetime import datetime
import logging
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Directorios para almacenar los datos
DATA_DIR = "received_data"
PROCESSED_DIR = "processed_data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.route('/')
def home():
    """Página de inicio del servidor"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DEM Server</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            .status {
                background-color: #f0f8ff;
                border-left: 4px solid #1e90ff;
                padding: 10px 15px;
                margin: 20px 0;
            }
            .endpoints {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
            }
            code {
                background-color: #eee;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: monospace;
            }
            .menu {
                display: flex;
                gap: 10px;
                margin: 20px 0;
            }
            .menu a {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 4px;
            }
            .menu a:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>DEM - Servidor de Recepción de Datos</h1>
        
        <div class="status">
            <h2>Estado del Servidor</h2>
            <p>El servidor está funcionando correctamente y listo para recibir datos.</p>
        </div>
        
        <div class="menu">
            <a href="/view/raw">Ver Datos Extraídos</a>
            <a href="/view/processed">Ver Datos Procesados</a>
            <a href="/view/stats">Ver Estadísticas</a>
        </div>
        
        <h2>Endpoints Disponibles</h2>
        <div class="endpoints">
            <p><code>GET /</code> - Esta página de inicio</p>
            <p><code>GET /api/health</code> - Verificar el estado del servidor (devuelve JSON)</p>
            <p><code>POST /api/data</code> - Recibir datos del mod (espera JSON)</p>
            <p><code>GET /view/raw</code> - Visualizar datos extraídos</p>
            <p><code>GET /view/processed</code> - Visualizar datos procesados</p>
            <p><code>GET /view/stats</code> - Visualizar estadísticas</p>
        </div>
        
        <h2>Información de Uso</h2>
        <p>Este servidor está diseñado para recibir datos del mod DEM para The Binding of Isaac.</p>
        <p>Los datos recibidos se almacenan en la carpeta <code>received_data</code> para su posterior procesamiento.</p>
        
        <h2>Configuración del Mod</h2>
        <p>Para que el mod envíe datos a este servidor, configura el archivo <code>config.lua</code> del mod con:</p>
        <pre><code>Config.SERVER_URL = "http://localhost:8000/api/data"</code></pre>
    </body>
    </html>
    """
    return html

@app.route('/view/raw')
def view_raw_data():
    """Visualizar los datos extraídos sin procesar"""
    # Buscar todos los archivos JSON en el directorio de datos
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    
    # Cargar los datos de cada archivo
    all_data = []
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                data['source_file'] = os.path.basename(file_path)
                all_data.append(data)
        except Exception as e:
            logging.error(f"Error al cargar {file_path}: {e}")
    
    # Ordenar por timestamp si está disponible
    if all_data and 'timestamp' in all_data[0]:
        all_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Generar HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Datos Extraídos - DEM</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            .data-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
            }
            .data-card {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                width: 300px;
                background-color: #f9f9f9;
            }
            .data-card h3 {
                margin-top: 0;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }
            .menu {
                margin: 20px 0;
            }
            .menu a {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 4px;
                margin-right: 10px;
            }
            .menu a:hover {
                background-color: #45a049;
            }
            .no-data {
                background-color: #f8d7da;
                color: #721c24;
                padding: 20px;
                border-radius: 5px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>Datos Extraídos del Juego</h1>
        
        <div class="menu">
            <a href="/">Volver al Inicio</a>
            <a href="/view/processed">Ver Datos Procesados</a>
            <a href="/view/stats">Ver Estadísticas</a>
        </div>
        
        <h2>Registros Recibidos: {{ data_count }}</h2>
        
        {% if data_count == 0 %}
        <div class="no-data">
            <p>No hay datos disponibles. Juega al juego con el mod activado para recopilar datos.</p>
        </div>
        {% else %}
        <div class="data-container">
            {% for item in data %}
            <div class="data-card">
                <h3>Registro #{{ loop.index }}</h3>
                <p><strong>Archivo:</strong> {{ item.source_file }}</p>
                {% if item.timestamp %}
                <p><strong>Timestamp:</strong> {{ item.timestamp }}</p>
                {% endif %}
                {% if item.room_id %}
                <p><strong>Habitación:</strong> {{ item.room_id }}</p>
                {% endif %}
                {% if item.health %}
                <p><strong>Salud:</strong> {{ item.health }}</p>
                {% endif %}
                {% if item.position %}
                <p><strong>Posición:</strong> ({{ item.position.x }}, {{ item.position.y }})</p>
                {% endif %}
                {% if item.enemies %}
                <p><strong>Enemigos:</strong> {{ item.enemies }}</p>
                {% endif %}
                
                <!-- Mostrar otros campos si existen -->
                {% for key, value in item.items() %}
                    {% if key not in ['source_file', 'timestamp', 'room_id', 'health', 'position', 'enemies'] %}
                    <p><strong>{{ key }}:</strong> {{ value }}</p>
                    {% endif %}
                {% endfor %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(html, data=all_data, data_count=len(all_data))

@app.route('/view/processed')
def view_processed_data():
    """Visualizar los datos procesados"""
    # Buscar archivos CSV en el directorio de datos procesados
    csv_files = glob.glob(os.path.join(PROCESSED_DIR, "*.csv"))
    
    if not csv_files:
        # No hay datos procesados
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Datos Procesados - DEM</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #333;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }
                .menu {
                    margin: 20px 0;
                }
                .menu a {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 15px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-right: 10px;
                }
                .menu a:hover {
                    background-color: #45a049;
                }
                .no-data {
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 20px;
                    border-radius: 5px;
                    text-align: center;
                }
                .process-button {
                    background-color: #007bff;
                    color: white;
                    padding: 10px 15px;
                    text-decoration: none;
                    border-radius: 4px;
                    display: inline-block;
                    margin-top: 20px;
                }
                .process-button:hover {
                    background-color: #0069d9;
                }
            </style>
        </head>
        <body>
            <h1>Datos Procesados</h1>
            
            <div class="menu">
                <a href="/">Volver al Inicio</a>
                <a href="/view/raw">Ver Datos Extraídos</a>
                <a href="/view/stats">Ver Estadísticas</a>
            </div>
            
            <div class="no-data">
                <p>No hay datos procesados disponibles.</p>
                <p>Ejecuta el script de procesamiento para preparar los datos para el entrenamiento.</p>
                <a href="/process/data" class="process-button">Procesar Datos Ahora</a>
            </div>
        </body>
        </html>
        """
        return html
    
    # Cargar el CSV más reciente
    latest_csv = max(csv_files, key=os.path.getmtime)
    df = pd.read_csv(latest_csv)
    
    # Generar una tabla HTML con los datos
    table_html = df.head(50).to_html(classes='data-table', index=False)
    
    # Generar gráficos
    plots_html = ""
    if len(df) > 0:
        # Gráfico 1: Salud a lo largo del tiempo
        if 'health' in df.columns and 'timestamp' in df.columns:
            plt.figure(figsize=(10, 5))
            plt.plot(pd.to_datetime(df['timestamp']), df['health'], marker='o')
            plt.title('Salud del Jugador a lo Largo del Tiempo')
            plt.xlabel('Tiempo')
            plt.ylabel('Salud')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convertir el gráfico a base64 para mostrarlo en HTML
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            plots_html += f'<div class="plot"><h3>Salud a lo Largo del Tiempo</h3><img src="data:image/png;base64,{plot_data}" /></div>'
        
        # Gráfico 2: Distribución de enemigos por habitación
        if 'enemies' in df.columns and 'room_id' in df.columns:
            plt.figure(figsize=(10, 5))
            df.groupby('room_id')['enemies'].mean().sort_values(ascending=False).head(10).plot(kind='bar')
            plt.title('Promedio de Enemigos por Habitación (Top 10)')
            plt.xlabel('ID de Habitación')
            plt.ylabel('Promedio de Enemigos')
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            plots_html += f'<div class="plot"><h3>Promedio de Enemigos por Habitación</h3><img src="data:image/png;base64,{plot_data}" /></div>'
    
    # Generar HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Datos Procesados - DEM</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1, h2, h3 {
                color: #333;
            }
            h1 {
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            .menu {
                margin: 20px 0;
            }
            .menu a {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 4px;
                margin-right: 10px;
            }
            .menu a:hover {
                background-color: #45a049;
            }
            .data-table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }
            .data-table th, .data-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .data-table th {
                background-color: #f2f2f2;
            }
            .data-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .plots-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-top: 30px;
            }
            .plot {
                flex: 1;
                min-width: 300px;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                background-color: white;
            }
            .plot img {
                max-width: 100%;
                height: auto;
            }
            .file-info {
                background-color: #e9f7ef;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Datos Procesados</h1>
        
        <div class="menu">
            <a href="/">Volver al Inicio</a>
            <a href="/view/raw">Ver Datos Extraídos</a>
            <a href="/view/stats">Ver Estadísticas</a>
        </div>
        
        <div class="file-info">
            <p><strong>Archivo:</strong> {{ filename }}</p>
            <p><strong>Registros:</strong> {{ record_count }}</p>
            <p><strong>Columnas:</strong> {{ columns }}</p>
        </div>
        
        <h2>Vista Previa de Datos</h2>
        {{ table | safe }}
        
        <h2>Visualizaciones</h2>
        <div class="plots-container">
            {{ plots | safe }}
        </div>
    </body>
    </html>
    """
    return render_template_string(
        html, 
        filename=os.path.basename(latest_csv),
        record_count=len(df),
        columns=", ".join(df.columns),
        table=table_html,
        plots=plots_html
    )

@app.route('/view/stats')
def view_stats():
    """Visualizar estadísticas de los datos"""
    # Verificar si existe el archivo de estadísticas
    stats_file = os.path.join(PROCESSED_DIR, "statistics.json")
    
    if not os.path.exists(stats_file):
        # No hay estadísticas disponibles
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Estadísticas - DEM</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #333;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }
                .menu {
                    margin: 20px 0;
                }
                .menu a {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 15px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-right: 10px;
                }
                .menu a:hover {
                    background-color: #45a049;
                }
                .no-data {
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 20px;
                    border-radius: 5px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <h1>Estadísticas</h1>
            
            <div class="menu">
                <a href="/">Volver al Inicio</a>
                <a href="/view/raw">Ver Datos Extraídos</a>
                <a href="/view/processed">Ver Datos Procesados</a>
            </div>
            
            <div class="no-data">
                <p>No hay estadísticas disponibles.</p>
                <p>Ejecuta el script de procesamiento para generar estadísticas.</p>
            </div>
        </body>
        </html>
        """
        return html
    
    # Cargar estadísticas
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    # Generar HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Estadísticas - DEM</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            .menu {
                margin: 20px 0;
            }
            .menu a {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 4px;
                margin-right: 10px;
            }
            .menu a:hover {
                background-color: #45a049;
            }
            .stats-container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .stat-card {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 20px;
                background-color: #f9f9f9;
                text-align: center;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #2c3e50;
                margin: 10px 0;
            }
            .stat-label {
                color: #7f8c8d;
                font-size: 1.2em;
            }
            .timestamp {
                margin-top: 30px;
                color: #95a5a6;
                font-style: italic;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>Estadísticas de los Datos</h1>
        
        <div class="menu">
            <a href="/">Volver al Inicio</a>
            <a href="/view/raw">Ver Datos Extraídos</a>
            <a href="/view/processed">Ver Datos Procesados</a>
        </div>
        
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-label">Registros Totales</div>
                <div class="stat-value">{{ stats.num_records }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Habitaciones Únicas</div>
                <div class="stat-value">{{ stats.unique_rooms }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Salud Promedio</div>
                <div class="stat-value">{{ "%.2f"|format(stats.avg_health) }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Enemigos Promedio</div>
                <div class="stat-value">{{ "%.2f"|format(stats.avg_enemies) }}</div>
            </div>
        </div>
        
        <div class="timestamp">
            Última actualización: {{ stats.timestamp }}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, stats=stats)

@app.route('/process/data')
def process_data_route():
    """Procesar los datos desde la interfaz web"""
    try:
        # Importar el módulo de procesamiento
        import process_data
        
        # Ejecutar el procesamiento
        process_data.main()
        
        return """
        <html>
        <head>
            <meta http-equiv="refresh" content="3;url=/view/processed">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 100px auto;
                    text-align: center;
                    padding: 20px;
                    background-color: #f0f8ff;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #4CAF50;
                }
            </style>
        </head>
        <body>
            <h1>Datos Procesados Correctamente</h1>
            <p>Redirigiendo a la página de visualización...</p>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
        <head>
            <meta http-equiv="refresh" content="5;url=/view/processed">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 100px auto;
                    text-align: center;
                    padding: 20px;
                    background-color: #fff0f0;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #d9534f;
                }}
                .error {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h1>Error al Procesar Datos</h1>
            <div class="error">{str(e)}</div>
            <p>Redirigiendo en 5 segundos...</p>
        </body>
        </html>
        """

@app.route('/api/data', methods=['POST'])
def receive_data():
    try:
        # Obtener datos del request
        data = request.json
        
        # Registrar la recepción
        logging.info(f"Datos recibidos: {data}")
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DATA_DIR}/data_{timestamp}.json"
        
        # Guardar datos en un archivo
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"status": "success", "message": "Datos recibidos correctamente"}), 200
    
    except Exception as e:
        logging.error(f"Error al procesar datos: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "El servidor está funcionando correctamente"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) 