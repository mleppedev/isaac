#!/usr/bin/env python
"""
Servidor web para visualizar los datos del mod DEM.
Proporciona visualización en tiempo real, análisis estadístico y preprocesamiento para ML.
"""

import os
import json
import time
import threading
import hashlib
import logging
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Usar backend sin GUI
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter, defaultdict
from flask import Flask, jsonify, render_template, send_from_directory, request, Response
from flask_socketio import SocketIO

# Configuración
DATABASE_FILE = "dem_database.json"
STATIC_FOLDER = "static"
TEMPLATE_FOLDER = "templates"
PORT = 5000
UPDATE_INTERVAL = 60  # segundos entre actualizaciones automáticas
EMIT_THROTTLE = 10    # segundos mínimos entre emisiones a clientes
LOG_FILE = "server.log"
DATA_DIR = "data"
PROCESSED_DATA_DIR = "processed_data"
RECEIVED_DATA_DIR = "received_data"
LOGS_DIR = "logs"

# Configurar logging
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, LOG_FILE)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Asegurar que existan los directorios necesarios
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(RECEIVED_DATA_DIR, exist_ok=True)

app = Flask(__name__, 
            static_folder=STATIC_FOLDER,
            template_folder=TEMPLATE_FOLDER)
socketio = SocketIO(app, cors_allowed_origins="*")

# Variable para controlar el thread de actualización
update_thread = None
thread_stop_event = threading.Event()
last_data_hash = None  # Hash para verificar si los datos han cambiado

def load_database():
    """Cargar la base de datos"""
    if not os.path.exists(DATABASE_FILE):
        logger.warning(f"Base de datos {DATABASE_FILE} no encontrada, creando una nueva")
        return {
            "events": [],
            "metadata": {
                "last_update": datetime.now().isoformat(),
                "total_events": 0,
                "version": "1.0"
            }
        }
    
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            database = json.load(f)
            logger.info(f"Base de datos cargada: {len(database.get('events', []))} eventos")
            return database
    except Exception as e:
        logger.error(f"Error al cargar la base de datos: {str(e)}")
        return {
            "events": [],
            "metadata": {
                "last_update": datetime.now().isoformat(),
                "total_events": 0,
                "version": "1.0",
                "error": str(e)
            }
        }

def get_event_stats(database):
    """Obtener estadísticas de eventos"""
    events = database.get("events", [])
    
    # Contar tipos de eventos
    event_types = Counter([e.get("event_type", "unknown") for e in events])
    
    # Estadísticas temporales
    timestamps = [e.get("timestamp") for e in events if "timestamp" in e and e.get("timestamp") is not None]
    time_range = {
        "min": min(timestamps) if timestamps else 0,
        "max": max(timestamps) if timestamps else 0
    }
    
    # Estadísticas de jugador
    player_positions = []
    player_health = []
    
    for event in events:
        if event.get("event_type") == "frame_state" and "data" in event:
            player_data = event.get("data", {}).get("player", {})
            if "position" in player_data and player_data["position"] is not None:
                player_positions.append(player_data["position"])
            if "health" in player_data and player_data["health"] is not None:
                player_health.append(player_data["health"])
    
    # Estadísticas de enemigos
    enemy_count = 0
    enemy_positions = []
    
    for event in events:
        if event.get("event_type") == "frame_state" and "data" in event:
            entities = event.get("data", {}).get("entities", [])
            for entity in entities:
                if entity and entity.get("is_enemy", False):
                    enemy_count += 1
                    if "position" in entity and entity["position"] is not None:
                        enemy_positions.append(entity["position"])
    
    # Semillas de juego únicas
    seeds = set()
    for event in events:
        game_data = event.get("game_data", {})
        if "seed" in game_data and game_data["seed"] is not None:
            seeds.add(game_data["seed"])
    
    # Crear diccionario de tipos de eventos (asegurarse de que todas las claves sean strings)
    event_types_dict = {}
    for event_type, count in dict(event_types).items():
        if event_type is not None:
            event_types_dict[str(event_type)] = count
    
    return {
        "total_events": len(events),
        "event_types": event_types_dict,
        "time_range": time_range,
        "player_stats": {
            "positions_captured": len(player_positions),
            "health_records": len(player_health)
        },
        "enemy_stats": {
            "total_enemies": enemy_count,
            "positions_captured": len(enemy_positions)
        },
        "unique_seeds": len(seeds),
        "last_update": database.get("metadata", {}).get("last_update", datetime.now().isoformat())
    }

def calculate_data_hash(database):
    """Calcular hash de los datos para detectar cambios"""
    # Usar solo los metadatos de última actualización y número total de eventos
    data_to_hash = {
        "total_events": len(database.get("events", [])),
        "last_update": database.get("metadata", {}).get("last_update", "")
    }
    hash_str = json.dumps(data_to_hash, sort_keys=True)
    return hashlib.md5(hash_str.encode()).hexdigest()

def update_data_background():
    """Función de actualización de datos en segundo plano"""
    import subprocess
    global last_data_hash
    last_emission_time = 0  # Última vez que se emitió una actualización
    
    while not thread_stop_event.is_set():
        logger.info("Ejecutando actualización automática de datos...")
        
        try:
            # Verificar si Isaac está en ejecución (Windows)
            game_check = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq isaac-ng.exe'], 
                                   capture_output=True, text=True)
            game_running = 'isaac-ng.exe' in game_check.stdout
            
            if game_running:
                logger.info("Juego en ejecución detectado. Realizando actualización normal.")
                result = subprocess.run(["python", "extract_data.py", "--keep-originals"], 
                                       capture_output=True, text=True)
            else:
                logger.info("Juego no detectado en ejecución. Se omitirá la actualización automática.")
                # No actualizar nada si el juego no está corriendo
                time.sleep(UPDATE_INTERVAL)
                continue
                
            update_data = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            if update_data["success"]:
                # Cargar base de datos actualizada
                database = load_database()
                
                # Comprobar si los datos han cambiado usando hash
                current_hash = calculate_data_hash(database)
                current_time = time.time()
                time_since_last_emission = current_time - last_emission_time
                
                # Solo emitir si los datos cambiaron Y ha pasado suficiente tiempo desde la última emisión
                if current_hash != last_data_hash and time_since_last_emission >= EMIT_THROTTLE:
                    # Actualizar el hash y el tiempo de emisión
                    last_data_hash = current_hash
                    last_emission_time = current_time
                    
                    try:
                        # Obtener estadísticas y enviar a clientes - asegurar que sean serializables
                        stats = get_event_stats(database)
                        sanitized_stats = sanitize_for_json(stats)
                        sanitized_update = sanitize_for_json(update_data)
                        
                        socketio.emit('data_updated', {
                            "stats": sanitized_stats,
                            "update_info": sanitized_update
                        })
                        logger.info("Datos actualizados y enviados a clientes conectados")
                        
                        # Generar visualizaciones actualizadas
                        generate_visualizations(database)
                    except Exception as e:
                        logger.error(f"Error al emitir datos actualizados: {str(e)}")
                        logger.exception("Detalles del error:")
                elif current_hash != last_data_hash:
                    logger.info("Datos actualizados pero no enviados (throttling)")
                    last_data_hash = current_hash
                else:
                    logger.info("No hay cambios en los datos")
            else:
                logger.error(f"Error en actualización automática: {update_data['error']}")
                
        except Exception as e:
            logger.error(f"Error en thread de actualización: {str(e)}")
            logger.exception("Detalles del error:")
        
        # Esperar hasta la siguiente actualización
        for _ in range(UPDATE_INTERVAL):
            if thread_stop_event.is_set():
                break
            time.sleep(1)

def generate_visualizations(database):
    """Genera visualizaciones basadas en los datos actuales"""
    events = database.get("events", [])
    if not events:
        logger.warning("No hay eventos para generar visualizaciones")
        return

    try:
        # Crear directorio para visualizaciones (asegurarse de que exista la ruta completa)
        vis_dir = os.path.join(STATIC_FOLDER, "visualizations")
        os.makedirs(vis_dir, exist_ok=True)
        
        # Verificar y registrar las rutas para debug
        abs_vis_dir = os.path.abspath(vis_dir)
        logger.info(f"Directorio de visualizaciones: {abs_vis_dir}")
        
        # Generar un archivo de prueba para verificar permisos
        test_file = os.path.join(vis_dir, 'test.txt')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            logger.info(f"Archivo de prueba creado: {test_file}")
            os.remove(test_file)
        except Exception as e:
            logger.error(f"Error al crear archivo de prueba: {str(e)}")
        
        # 1. Mapa de calor de posiciones del jugador
        player_positions = []
        for event in events:
            if event.get("event_type") == "frame_state" and "data" in event:
                player_data = event.get("data", {}).get("player", {})
                if "position" in player_data and player_data["position"] is not None:
                    pos = player_data["position"]
                    if pos is not None and "x" in pos and "y" in pos and pos["x"] is not None and pos["y"] is not None:
                        player_positions.append((pos.get("x", 0), pos.get("y", 0)))
        
        if player_positions:
            plt.figure(figsize=(10, 8))
            positions = np.array(player_positions)
            plt.hist2d(positions[:, 0], positions[:, 1], bins=50, cmap='hot')
            plt.colorbar(label='Frecuencia')
            plt.title('Mapa de Calor - Posiciones del Jugador')
            plt.xlabel('Posición X')
            plt.ylabel('Posición Y')
            plt.tight_layout()
            
            # Guardar con ruta absoluta y manejar errores
            heatmap_path = os.path.join(abs_vis_dir, 'player_heatmap.png')
            try:
                plt.savefig(heatmap_path)
                logger.info(f"Mapa de calor guardado: {heatmap_path}")
            except Exception as e:
                logger.error(f"Error al guardar mapa de calor: {str(e)}")
                
            plt.close()
            
        else:
            logger.warning("No hay suficientes posiciones de jugador para generar el mapa de calor")
        
        # 2. Distribución de tipos de eventos
        event_types = Counter([str(e.get("event_type")) for e in events if e.get("event_type") is not None])
        if event_types:
            plt.figure(figsize=(12, 6))
            types = list(event_types.keys())
            counts = list(event_types.values())
            plt.bar(types, counts)
            plt.title('Distribución de Tipos de Eventos')
            plt.xlabel('Tipo de Evento')
            plt.ylabel('Cantidad')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            distribution_path = os.path.join(abs_vis_dir, 'event_distribution.png')
            try:
                plt.savefig(distribution_path)
                logger.info(f"Distribución de eventos guardada: {distribution_path}")
            except Exception as e:
                logger.error(f"Error al guardar distribución: {str(e)}")
                
            plt.close()
            logger.info("Distribución de eventos generada")
        else:
            logger.warning("No hay suficientes tipos de eventos para generar la distribución")
        
        # 3. Preprocesamiento para ML
        frame_states = [e for e in events if e.get("event_type") == "frame_state"]
        if len(frame_states) > 10:
            # Crear conjunto de datos mínimo para ML
            ml_data = []
            for state in frame_states[:1000]:  # Limitar a 1000 estados para el ejemplo
                data = state.get("data", {})
                player = data.get("player", {})
                inputs = data.get("inputs", {})
                player_position = player.get("position", {})
                player_velocity = player.get("velocity", {})
                player_health = player.get("health", {})
                
                # Extraer características relevantes con validación de None
                features = {
                    "frame_count": data.get("frame_count", 0),
                    "player_x": player_position.get("x", 0) if player_position is not None else 0,
                    "player_y": player_position.get("y", 0) if player_position is not None else 0,
                    "player_vx": player_velocity.get("x", 0) if player_velocity is not None else 0,
                    "player_vy": player_velocity.get("y", 0) if player_velocity is not None else 0,
                    "player_health": player_health.get("hearts", 0) if player_health is not None else 0,
                    "input_left": inputs.get("LEFT", 0) if inputs is not None else 0,
                    "input_right": inputs.get("RIGHT", 0) if inputs is not None else 0,
                    "input_up": inputs.get("UP", 0) if inputs is not None else 0,
                    "input_down": inputs.get("DOWN", 0) if inputs is not None else 0,
                    "shoot_left": inputs.get("SHOOT_LEFT", 0) if inputs is not None else 0,
                    "shoot_right": inputs.get("SHOOT_RIGHT", 0) if inputs is not None else 0,
                    "shoot_up": inputs.get("SHOOT_UP", 0) if inputs is not None else 0,
                    "shoot_down": inputs.get("SHOOT_DOWN", 0) if inputs is not None else 0,
                    "timestamp": state.get("timestamp", 0)
                }
                ml_data.append(features)
            
            if ml_data:
                # Convertir a DataFrame
                df = pd.DataFrame(ml_data)
                # Asegurar que existe el directorio
                os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
                ml_file = os.path.join(PROCESSED_DATA_DIR, "ml_features.csv")
                df.to_csv(ml_file, index=False)
                logger.info(f"Datos para ML generados: {len(ml_data)} registros")
                
                # Crear gráfico de algunas características
                plt.figure(figsize=(12, 6))
                plt.plot(df["timestamp"], df["player_x"], label="Posición X")
                plt.plot(df["timestamp"], df["player_y"], label="Posición Y")
                plt.title('Trayectoria del Jugador')
                plt.xlabel('Timestamp')
                plt.ylabel('Coordenadas')
                plt.legend()
                plt.tight_layout()
                
                trajectory_path = os.path.join(abs_vis_dir, 'player_trajectory.png')
                try:
                    plt.savefig(trajectory_path)
                    logger.info(f"Trayectoria guardada: {trajectory_path}")
                except Exception as e:
                    logger.error(f"Error al guardar trayectoria: {str(e)}")
                    
                plt.close()
        else:
            logger.warning("No hay suficientes estados para generar la trayectoria")
    
    except Exception as e:
        logger.error(f"Error al generar visualizaciones: {str(e)}")
        logger.exception("Detalles del error:")

# Rutas web

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard con visualizaciones"""
    database = load_database()
    stats = get_event_stats(database)
    return render_template('dashboard.html', stats=stats)

@app.route('/analytics')
def analytics():
    """Análisis avanzado de datos"""
    return render_template('analytics.html')

# Función de sanitización para JSON que debe definirse antes de su uso
def sanitize_for_json(obj):
    """Asegura que todos los objetos sean serializables a JSON"""
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items() 
                if k is not None and v is not None}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj if item is not None]
    elif obj is None:
        return ""
    elif isinstance(obj, (int, float, str, bool)):
        return obj
    elif hasattr(obj, 'to_dict'):  # Para objetos que implementan to_dict
        return sanitize_for_json(obj.to_dict())
    else:
        return str(obj)  # Convertir otros tipos a string

@app.route('/api/stats')
def api_stats():
    """API para obtener estadísticas"""
    try:
        database = load_database()
        stats = get_event_stats(database)
        
        # Verificar que todos los valores sean serializables
        sanitized_stats = sanitize_for_json(stats)
        return jsonify(sanitized_stats)
    except Exception as e:
        logger.error(f"Error en api_stats: {str(e)}")
        return jsonify({
            "error": str(e),
            "total_events": 0,
            "event_types": {},
            "time_range": {"min": 0, "max": 0},
            "player_stats": {"positions_captured": 0, "health_records": 0},
            "enemy_stats": {"total_enemies": 0, "positions_captured": 0},
            "unique_seeds": 0,
            "last_update": datetime.now().isoformat()
        })

@app.route('/api/events')
def api_events():
    """API para obtener todos los eventos (con paginación)"""
    database = load_database()
    
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    
    # Limitar per_page a un máximo razonable
    per_page = min(per_page, 1000)
    
    events = database.get("events", [])
    total = len(events)
    
    # Calcular índices para la paginación
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Obtener eventos para la página actual
    page_events = events[start_idx:end_idx]
    
    return jsonify({
        "events": page_events,
        "metadata": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    })

@app.route('/api/events/<event_type>')
def api_events_by_type(event_type):
    """API para obtener eventos por tipo"""
    database = load_database()
    events = [e for e in database.get("events", []) if e.get("event_type") == event_type]
    return jsonify(events)

@app.route('/api/events/seed/<seed>')
def api_events_by_seed(seed):
    """API para obtener eventos por seed"""
    database = load_database()
    events = [e for e in database.get("events", []) if e.get("game_data", {}).get("seed") == int(seed)]
    return jsonify(events)

@app.route('/api/ml/features')
def api_ml_features():
    """API para obtener características procesadas para ML"""
    ml_file = os.path.join(PROCESSED_DATA_DIR, "ml_features.csv")
    
    if not os.path.exists(ml_file):
        return jsonify({"error": "No hay datos de ML disponibles"}), 404
    
    try:
        df = pd.read_csv(ml_file)
        # Convertir a formato JSON
        records = df.to_dict(orient='records')
        return jsonify({
            "features": records,
            "metadata": {
                "columns": list(df.columns),
                "shape": df.shape
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ml/download')
def api_ml_download():
    """API para descargar el conjunto de datos ML completo"""
    ml_file = os.path.join(PROCESSED_DATA_DIR, "ml_features.csv")
    
    if not os.path.exists(ml_file):
        return jsonify({"error": "No hay datos de ML disponibles"}), 404
    
    return send_from_directory(
        PROCESSED_DATA_DIR, 
        "ml_features.csv", 
        as_attachment=True
    )

@app.route('/api/refresh')
def api_refresh():
    """API para refrescar los datos (ejecuta extract_data.py)"""
    global last_data_hash
    import subprocess
    
    # Ejecutar con forzado para que no verifique si el juego está en ejecución
    result = subprocess.run(["python", "extract_data.py", "--keep-originals", "--force"], capture_output=True, text=True)
    
    update_data = {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr,
        "timestamp": datetime.now().isoformat()
    }
    
    # Si la actualización fue exitosa, notificar a los clientes
    if update_data["success"]:
        database = load_database()
        
        # Comprobar si los datos han cambiado
        current_hash = calculate_data_hash(database)
        data_changed = current_hash != last_data_hash
        last_data_hash = current_hash
        
        stats = get_event_stats(database)
        
        # Solo enviar notificación si los datos han cambiado
        if data_changed:
            # Generar visualizaciones
            generate_visualizations(database)
            
            # Enviar datos sanitizados
            sanitized_stats = sanitize_for_json(stats)
            sanitized_update = sanitize_for_json(update_data)
            
            socketio.emit('data_updated', {
                "stats": sanitized_stats,
                "update_info": sanitized_update
            })
            logger.info("Datos actualizados manualmente y enviados a clientes")
        else:
            logger.info("Actualización manual: No hay cambios en los datos")
    else:
        logger.error(f"Error en actualización manual: {update_data['error']}")
    
    return jsonify(sanitize_for_json(update_data))

@socketio.on('connect')
def handle_connect():
    """Gestionar conexión de cliente WebSocket"""
    logger.info(f"Cliente conectado: {request.sid}")
    # Enviar estadísticas actuales al cliente que se conecta
    database = load_database()
    stats = get_event_stats(database)
    socketio.emit('data_updated', {"stats": stats}, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """Gestionar desconexión de cliente WebSocket"""
    logger.info(f"Cliente desconectado: {request.sid}")

@socketio.on('manual_update')
def handle_manual_update(data):
    """Gestionar actualización manual solicitada por cliente"""
    logger.info(f"Actualización manual solicitada por {request.sid}")
    # Ejecutar actualización pero no devolver directamente la respuesta
    try:
        # Importar aquí para evitar dependencias circulares
        import subprocess
        global last_data_hash
        
        # Verificar si el juego está en ejecución
        game_check = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq isaac-ng.exe'], 
                                capture_output=True, text=True)
        game_running = 'isaac-ng.exe' in game_check.stdout
        
        # Preparar mensaje informativo sobre el estado del juego
        game_status_message = ""
        if not game_running:
            game_status_message = "El juego no está en ejecución. Se usará la opción --force para actualizar datos."
            logger.info(game_status_message)
        
        # Ejecutar con forzado para que no verifique si el juego está en ejecución
        result = subprocess.run(["python", "extract_data.py", "--keep-originals", "--force"], capture_output=True, text=True)
        
        update_data = {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "timestamp": datetime.now().isoformat(),
            "game_running": game_running,
            "game_status_message": game_status_message
        }
        
        # Si la actualización fue exitosa, notificar a los clientes
        if update_data["success"]:
            database = load_database()
            
            # Comprobar si los datos han cambiado
            current_hash = calculate_data_hash(database)
            data_changed = current_hash != last_data_hash
            last_data_hash = current_hash
            
            # Sanitizar stats antes de enviarlos
            stats = sanitize_for_json(get_event_stats(database))
            update_data = sanitize_for_json(update_data)
            
            # Solo enviar notificación si los datos han cambiado
            if data_changed:
                # Generar visualizaciones
                generate_visualizations(database)
                
                # Enviar datos completos
                socketio.emit('data_updated', {
                    "stats": stats,
                    "update_info": update_data
                })
                logger.info("Datos actualizados manualmente y enviados a clientes")
            else:
                logger.info("Actualización manual: No hay cambios en los datos")
                
                # Mensajes según el estado del juego
                status_message = "No hay cambios en los datos"
                if not game_running:
                    status_message += ". El juego no está en ejecución actualmente."
                
                # Enviar confirmación sólo al cliente que solicitó la actualización
                socketio.emit('update_status', {
                    "status": "success",
                    "message": status_message,
                    "update_info": update_data
                }, room=request.sid)
        else:
            logger.error(f"Error en actualización manual: {update_data['error']}")
            # Enviar mensaje de error al cliente
            error_message = "Error al actualizar los datos"
            if not game_running:
                error_message += ". El juego no está en ejecución actualmente."
                
            socketio.emit('update_status', {
                "status": "error",
                "message": error_message,
                "update_info": update_data
            }, room=request.sid)
    except Exception as e:
        logger.error(f"Error en handle_manual_update: {str(e)}")
        logger.exception("Detalles del error:")
        # Enviar mensaje de error al cliente
        socketio.emit('update_status', {
            "status": "error",
            "message": f"Error inesperado: {str(e)}"
        }, room=request.sid)

@app.route('/api/metadata')
def api_metadata():
    """API para obtener metadatos del sistema"""
    database = load_database()
    metadata = database.get("metadata", {})
    
    # Información del sistema
    system_info = {
        "server_version": "2.0",
        "python_version": os.popen('python --version').read().strip(),
        "database_file": os.path.abspath(DATABASE_FILE),
        "server_start_time": datetime.now().isoformat(),
        "available_endpoints": [
            "/api/stats",
            "/api/events",
            "/api/events/<event_type>",
            "/api/events/seed/<seed>",
            "/api/ml/features",
            "/api/ml/download",
            "/api/refresh",
            "/api/metadata"
        ]
    }
    
    return jsonify({
        "database_metadata": metadata,
        "system_info": system_info
    })

if __name__ == "__main__":
    # Crear directorios si no existen
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
    
    # Iniciar thread de actualización automática
    thread_stop_event.clear()
    update_thread = threading.Thread(target=update_data_background)
    update_thread.daemon = True
    update_thread.start()
    
    logger.info(f"Servidor iniciado en http://localhost:{PORT}")
    socketio.run(app, host="0.0.0.0", port=PORT, debug=True, allow_unsafe_werkzeug=True) 