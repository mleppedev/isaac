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
import shutil
import game_manager  # Importar el módulo para gestionar acciones del juego

# Cargar configuración desde config.json
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
try:
    with open(CONFIG_FILE, 'r') as f:
        CONFIG = json.load(f)
    logging.info(f"Configuración cargada desde {CONFIG_FILE}")
except Exception as e:
    logging.error(f"Error al cargar la configuración desde {CONFIG_FILE}: {str(e)}")
    CONFIG = {}  # Configuración predeterminada

# Configuración
DATABASE_FILE = CONFIG.get('database', {}).get('file', "dem_database.json")
STATIC_FOLDER = "static"
TEMPLATE_FOLDER = "templates"
PORT = CONFIG.get('server', {}).get('port', 5000)
UPDATE_INTERVAL = CONFIG.get('server', {}).get('update_interval', 20)  # segundos entre actualizaciones automáticas
EMIT_THROTTLE = CONFIG.get('server', {}).get('emit_throttle', 5)       # segundos mínimos entre emisiones a clientes 
GAME_CHECK_INTERVAL = CONFIG.get('server', {}).get('game_check_interval', 15)  # segundos entre verificaciones de estado del juego
CAPTURE_FRAME_RATE = CONFIG.get('data_capture', {}).get('frame_rate', 5)  # capturar cada N frames
CAPTURE_KEY_EVENTS = CONFIG.get('events', {}).get('key_events', {}).get('enabled', True)  # capturar eventos clave
VERBOSE_LOGGING = CONFIG.get('advanced', {}).get('verbose_logging', True)  # aumentar detalle de logs
LOG_FILE = "server.log"
DATA_DIR = CONFIG.get('paths', {}).get('data_dir', "data")
PROCESSED_DATA_DIR = CONFIG.get('paths', {}).get('processed_data_dir', "processed_data")
RECEIVED_DATA_DIR = CONFIG.get('paths', {}).get('received_data_dir', "received_data")
LOGS_DIR = CONFIG.get('paths', {}).get('logs_dir', "logs")

# Variables globales
game_status = {"running": False, "process": None, "pid": None, "last_check": datetime.now().isoformat()}
last_emit_time = 0
check_game_status_thread = None
updating_data = False  # Flag para controlar actualizaciones simultáneas

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if VERBOSE_LOGGING else logging.INFO)

# Crear el directorio de logs si no existe
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Configurar handler para archivo
file_handler = logging.FileHandler(os.path.join(LOGS_DIR, LOG_FILE))
file_handler.setLevel(logging.DEBUG)

# Configurar handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formato de log
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Añadir handlers al logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Reducir verbosidad de loggers externos
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)

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
game_check_thread = None
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
    event_types = Counter()
    
    # Mejorar la clasificación de eventos para evitar categorías "unknown" y "other"
    for e in events:
        event_type = e.get("event_type")
        
        # Si el tipo de evento es None, desconocido o "other_event", intentar inferirlo por otros campos
        if event_type is None or event_type == "unknown" or event_type == "other_event":
            # Verificar si hay datos de jugador
            if "data" in e and "player" in e["data"]:
                # Verificar datos específicos del jugador
                player_data = e["data"]["player"]
                
                # Verificar si hay información de salud
                if player_data.get("health"):
                    event_type = "player_health"
                # Verificar si hay información de posición
                elif player_data.get("position"):
                    event_type = "player_position"
                # Verificar si hay información de velocidad
                elif player_data.get("velocity"):
                    event_type = "player_movement"
                # Verificar si hay información de estadísticas
                elif player_data.get("stats"):
                    event_type = "player_stats"
                # Verificar si hay información de inventario
                elif player_data.get("inventory") or player_data.get("items"):
                    event_type = "player_items"
                else:
                    event_type = "player_state"
            
            # Verificar si hay datos de enemigos
            elif "data" in e and "entities" in e["data"]:
                entities = e["data"]["entities"]
                if entities and any(entity and entity.get("is_enemy", False) for entity in entities):
                    # Verificar si hay información de posición de enemigos
                    if any(entity and entity.get("position") for entity in entities if entity and entity.get("is_enemy", False)):
                        event_type = "enemy_position"
                    # Verificar si hay información de salud de enemigos
                    elif any(entity and entity.get("health") for entity in entities if entity and entity.get("is_enemy", False)):
                        event_type = "enemy_health"
                    # Verificar si hay información de estado de enemigos
                    elif any(entity and entity.get("state") for entity in entities if entity and entity.get("is_enemy", False)):
                        event_type = "enemy_state"
                    else:
                        event_type = "enemy_data"
                elif entities:
                    event_type = "entity_data"
            
            # Verificar si es un evento relacionado con semillas
            elif "game_data" in e and "seed" in e["game_data"]:
                event_type = "game_seed"
            
            # Verificar si es un evento de estado de sala o nivel
            elif "data" in e:
                data = e["data"]
                # Verificar estado de sala
                if "room" in data:
                    event_type = "room_state"
                # Verificar estado de nivel
                elif "level" in data:
                    event_type = "level_state"
                # Verificar estado de juego
                elif "game_state" in data or "game" in data:
                    event_type = "game_state"
            
            # Verificar si hay información de colisiones
            elif "data" in e and "collision" in e["data"]:
                event_type = "collision_event"
            
            # Verificar si es un evento de entrada/controles
            elif "data" in e and "inputs" in e["data"]:
                event_type = "input_event"
            
            # Verificar si es un evento con datos de items o pickups
            elif "data" in e and ("items" in e["data"] or "pickups" in e["data"]):
                event_type = "item_event"
            
            # Verificar si hay datos de audio
            elif "data" in e and "audio" in e["data"]:
                event_type = "audio_event"
            
            # Verificar si hay datos de combate
            elif "data" in e and ("combat" in e["data"] or "damage" in e["data"]):
                event_type = "combat_event"
            
            # Si tiene timestamp pero no tiene clasificación
            elif "timestamp" in e:
                # Verificar si tiene otros metadatos útiles
                if "metadata" in e:
                    event_type = "metadata_event"
                elif "game_data" in e:
                    event_type = "game_metadata"
                else:
                    event_type = "timestamped_event"
            
            # Verificar si tiene ID pero no otros datos reconocibles
            elif "id" in e:
                event_type = "id_event"
            
            # Si nada más funciona, categorizar por las claves que contiene
            else:
                keys = set(e.keys())
                if "event" in keys:
                    event_type = "event_data"
                elif "message" in keys:
                    event_type = "message_event"
                elif "log" in keys:
                    event_type = "log_event"
                elif "data" in keys:
                    event_type = "general_data"
                else:
                    # Último recurso: crear un tipo basado en las claves disponibles
                    event_type = "data_" + "_".join(sorted(list(keys)[:2]))
        
        # Incrementar el contador para este tipo de evento
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
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

def check_game_status():
    """Comprueba si el juego está en ejecución y notifica a los clientes."""
    global game_status
    
    # Inicializar el estado
    game_running, process_name = game_manager.is_game_running()
    game_status = {
        'running': game_running,
        'process': process_name,
        'pid': None,
        'last_check': datetime.now().isoformat()
    }
    
    # Emitir estado inicial
    try:
        socketio.emit('game_status_change', game_status, namespace='/')
        logger.info(f"Estado inicial del juego: {'en ejecución' if game_running else 'no detectado'}")
    except Exception as e:
        logger.error(f"Error al enviar estado inicial del juego: {str(e)}")
    
    # Bucle principal de verificación
    last_check_time = time.time()
    while not thread_stop_event.is_set():
        try:
            # Control de tiempo más preciso
            current_time = time.time()
            elapsed = current_time - last_check_time
            
            # Si no ha pasado el intervalo completo, dormir solo el tiempo restante
            if elapsed < GAME_CHECK_INTERVAL:
                # Dormir en incrementos pequeños para poder responder rápidamente al evento thread_stop_event
                sleep_time = min(1.0, GAME_CHECK_INTERVAL - elapsed)
                time.sleep(sleep_time)
                continue
            
            # Registrar el momento de la verificación
            last_check_time = current_time
            logger.debug(f"Verificando estado del juego (intervalo: {GAME_CHECK_INTERVAL}s)")
            
            # Verificar si el juego está en ejecución usando game_manager
            game_running, process_name = game_manager.is_game_running()
            
            # Si el estado cambió, actualizar y notificar a los clientes
            if game_running != game_status.get('running', False):
                logger.info(f"Cambio de estado del juego detectado: {'en ejecución' if game_running else 'no detectado'}")
                
                game_status = {
                    'running': game_running,
                    'process': process_name,
                    'pid': None,
                    'last_check': datetime.now().isoformat()
                }
                
                # Enviar actualizaciones por SocketIO
                try:
                    socketio.emit('game_status_change', game_status, namespace='/')
                    logger.info(f"Estado del juego enviado a clientes")
                except Exception as e:
                    logger.error(f"Error al enviar actualización de estado del juego: {str(e)}")
            else:
                logger.debug(f"Estado del juego sin cambios: {'en ejecución' if game_running else 'no detectado'}")
                    
        except Exception as e:
            logger.error(f"Error al verificar el estado del juego: {str(e)}")
            # En caso de error, esperar un poco antes de intentar de nuevo
            time.sleep(1.0)
            
    logger.info("Hilo de verificación de estado del juego detenido")

def update_data_background():
    """Función de actualización de datos en segundo plano"""
    import subprocess
    global last_data_hash, game_status
    last_emission_time = 0  # Última vez que se emitió una actualización
    
    while not thread_stop_event.is_set():
        logger.info("Ejecutando actualización automática de datos...")
        
        try:
            # Usar el estado global del juego
            game_running = game_status.get("running", False)
            
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
                "timestamp": datetime.now().isoformat(),
                "game_running": game_running,
                "game_info": {
                    "process": game_status.get("process_name"),
                    "pid": game_status.get("pid")
                }
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
    return render_template('dashboard.html', stats=stats, page_title="Data Event Manager", active_page="dashboard")

@app.route('/analytics')
def analytics():
    """Análisis avanzado de datos"""
    return render_template('analytics.html', page_title="Análisis Avanzado", active_page="analytics")

@app.route('/config')
def config():
    """Renderiza la página de configuración."""
    return render_template('config.html', page_title="Configuración", active_page="config")

@app.route('/data')
def data():
    """Página de datos procesados"""
    database = load_database()
    stats = get_event_stats(database)
    return render_template('data.html', stats=stats, page_title="Datos Procesados", active_page="data")

@app.route('/stats')
def stats():
    """Página de estadísticas"""
    database = load_database()
    stats = get_event_stats(database)
    return render_template('stats.html', stats=stats, page_title="Estadísticas", active_page="stats")

# Ruta para la página de control del personaje
@app.route('/control')
def player_control():
    return render_template('control.html')

# API para enviar comandos de control
@app.route('/api/control', methods=['POST'])
def api_control():
    try:
        command = request.json
        
        if not command or not isinstance(command, dict) or 'type' not in command:
            return jsonify({
                'success': False,
                'error': 'Comando inválido'
            }), 400
        
        # Usar el script de control para enviar el comando
        from control_player import send_command
        result = send_command(command, wait_for_result=False)
        
        # Verificar si hubo errores
        if result and isinstance(result, dict) and 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error'],
                'description': 'Asegúrate de que el juego esté abierto y el mod DEM esté activado'
            }), 500
            
        return jsonify({
            'success': True,
            'command': command,
            'response': result
        })
    except Exception as e:
        error_msg = str(e)
        description = 'Error general en la comunicación'
        
        # Comprobar tipos específicos de errores
        if 'No such file or directory' in error_msg:
            description = 'El archivo de comunicación no existe. Asegúrate de que el juego esté abierto y el mod DEM esté activado.'
        elif 'Permission denied' in error_msg:
            description = 'Permiso denegado al acceder al archivo. Verifica los permisos o cierra y reabre el juego.'
        elif 'device or resource busy' in error_msg.lower():
            description = 'El archivo está siendo utilizado por otro proceso. Espera unos momentos y vuelve a intentarlo.'
            
        return jsonify({
            'success': False,
            'error': error_msg,
            'description': description
        }), 500

# API para enviar secuencias de comandos
@app.route('/api/control/sequence', methods=['POST'])
def api_control_sequence():
    try:
        commands = request.json
        
        if not commands or not isinstance(commands, list):
            return jsonify({
                'success': False,
                'error': 'Secuencia inválida'
            }), 400
        
        # Usar el script de control para enviar la secuencia
        from control_player import send_command
        result = send_command(commands, wait_for_result=False)
        
        # Verificar si hubo errores
        if result and isinstance(result, dict) and 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error'],
                'description': 'Asegúrate de que el juego esté abierto y el mod DEM esté activado'
            }), 500
        
        return jsonify({
            'success': True,
            'count': len(commands),
            'response': result
        })
    except Exception as e:
        error_msg = str(e)
        description = 'Error general en la comunicación'
        
        # Comprobar tipos específicos de errores
        if 'No such file or directory' in error_msg:
            description = 'El archivo de comunicación no existe. Asegúrate de que el juego esté abierto y el mod DEM esté activado.'
        elif 'Permission denied' in error_msg:
            description = 'Permiso denegado al acceder al archivo. Verifica los permisos o cierra y reabre el juego.'
        elif 'device or resource busy' in error_msg.lower():
            description = 'El archivo está siendo utilizado por otro proceso. Espera unos momentos y vuelve a intentarlo.'
            
        return jsonify({
            'success': False,
            'error': error_msg,
            'description': description
        }), 500

# Funciones para manejar la configuración
def load_configuration():
    """Carga la configuración desde el archivo"""
    config_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error al cargar configuración desde {config_file_path}: {str(e)}")
        return {
            "server": {
                "port": 5000,
                "update_interval": 20,
                "emit_throttle": 5,
                "game_check_interval": 10
            },
            "database": {
                "file": "dem_database.json",
                "backup_interval": 3600,
                "max_events": 100000
            },
            "data_capture": {
                "frame_rate": 5,
                "capture_player_data": True,
                "capture_enemy_data": True
            }
        }

def save_configuration(config_data):
    """Guarda la configuración al archivo"""
    config_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    try:
        # Hacer una copia de seguridad antes de guardar
        if os.path.exists(config_file_path):
            backup_dir = os.path.join(LOGS_DIR, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"config_{timestamp}.json")
            shutil.copy2(config_file_path, backup_file)
        
        # Guardar nueva configuración
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error al guardar configuración en {config_file_path}: {str(e)}")
        return False

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """API para obtener la configuración actual"""
    config_data = load_configuration()
    return jsonify(config_data)

@app.route('/api/config', methods=['POST'])
def api_update_config():
    """API para actualizar la configuración"""
    try:
        # Validar que sea JSON válido
        if not request.is_json:
            return jsonify({"error": "Se requiere datos JSON"}), 400
        
        config_data = request.json
        
        # Validar estructura mínima
        required_sections = ['server', 'database', 'data_capture']
        for section in required_sections:
            if section not in config_data:
                return jsonify({"error": f"Falta la sección '{section}' en la configuración"}), 400
        
        # Guardar configuración
        if save_configuration(config_data):
            logger.info("Configuración actualizada correctamente")
            # Notificar a clientes conectados
            socketio.emit('config_updated', {
                "message": "Configuración actualizada",
                "timestamp": datetime.now().isoformat()
            })
            return jsonify({"success": True, "message": "Configuración actualizada correctamente"})
        else:
            return jsonify({"error": "Error al guardar la configuración"}), 500
            
    except Exception as e:
        logger.error(f"Error en api_update_config: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/config/reload', methods=['POST'])
def api_reload_config():
    """API para recargar la configuración sin reiniciar el servidor"""
    try:
        global UPDATE_INTERVAL, EMIT_THROTTLE, GAME_CHECK_INTERVAL, CAPTURE_FRAME_RATE, CAPTURE_KEY_EVENTS, VERBOSE_LOGGING
        
        # Cargar configuración
        config_data = load_configuration()
        
        # Actualizar variables globales
        if 'server' in config_data:
            server_config = config_data['server']
            UPDATE_INTERVAL = server_config.get('update_interval', UPDATE_INTERVAL)
            EMIT_THROTTLE = server_config.get('emit_throttle', EMIT_THROTTLE)
            GAME_CHECK_INTERVAL = server_config.get('game_check_interval', GAME_CHECK_INTERVAL)
        
        if 'data_capture' in config_data:
            capture_config = config_data['data_capture']
            CAPTURE_FRAME_RATE = capture_config.get('frame_rate', CAPTURE_FRAME_RATE)
        
        if 'advanced' in config_data:
            advanced_config = config_data['advanced']
            VERBOSE_LOGGING = advanced_config.get('verbose_logging', VERBOSE_LOGGING)
        
        logger.info("Configuración recargada correctamente")
        return jsonify({"success": True, "message": "Configuración recargada correctamente"})
        
    except Exception as e:
        logger.error(f"Error al recargar configuración: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/config/defaults', methods=['GET'])
def api_get_default_config():
    """API para obtener la configuración por defecto"""
    default_config = {
        "server": {
            "port": 5000,
            "update_interval": 20,
            "emit_throttle": 5,
            "game_check_interval": 10
        },
        "database": {
            "file": "dem_database.json",
            "backup_interval": 3600,
            "max_events": 100000
        },
        "data_capture": {
            "frame_rate": 5,
            "capture_player_data": True,
            "capture_enemy_data": True,
            "capture_item_data": True,
            "capture_room_data": True,
            "capture_game_state": True,
            "capture_inputs": True,
            "capture_collisions": True,
            "capture_stats": True,
            "track_event_chains": True,
            "detailed_positions": True,
            "extract_run_metrics": True
        },
        "events": {
            "key_events": {
                "damage_taken": True,
                "damage_dealt": True,
                "item_collected": True,
                "enemy_killed": True,
                "boss_encounter": True,
                "room_cleared": True,
                "floor_changed": True,
                "run_started": True,
                "run_ended": True
            }
        },
        "advanced": {
            "verbose_logging": True,
            "debug_mode": False,
            "memory_optimization": True,
            "aggregate_similar_events": True,
            "track_gameplay_patterns": True
        },
        "paths": {
            "data_dir": "data",
            "processed_data_dir": "processed_data",
            "received_data_dir": "received_data",
            "logs_dir": "logs",
            "visualizations_dir": "static/visualizations"
        }
    }
    return jsonify(default_config)

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
    
    # Enviar estado actual del juego con el formato correcto
    socketio.emit('game_status_change', {
        "running": game_status.get("running", False),
        "process": game_status.get("process"),  # Nombre corregido del campo
        "pid": game_status.get("pid"),
        "last_check": game_status.get("last_check", datetime.now().isoformat())
    }, room=request.sid)
    
    # Enviar estadísticas
    socketio.emit('data_updated', {
        "stats": sanitize_for_json(stats), 
        "update_info": {
            "game_running": game_status.get("running", False),
            "timestamp": datetime.now().isoformat()
        }
    }, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """Gestionar desconexión de cliente WebSocket"""
    logger.info(f"Cliente desconectado: {request.sid}")

def update_data():
    """Actualiza los datos ejecutando el script extract_data.py y devuelve el resultado"""
    import subprocess
    global last_data_hash
    
    logger.info("Ejecutando actualización de datos...")
    
    try:
        # Ejecutar el script de extracción con la opción de mantener archivos originales
        result = subprocess.run(["python", "extract_data.py", "--keep-originals", "--force"], 
                               capture_output=True, text=True)
        
        update_info = {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "timestamp": datetime.now().isoformat()
        }
        
        # Si la actualización fue exitosa, verificar cambios y notificar
        if update_info["success"]:
            database = load_database()
            
            # Comprobar si los datos han cambiado
            current_hash = calculate_data_hash(database)
            data_changed = current_hash != last_data_hash
            last_data_hash = current_hash
            
            if data_changed:
                stats = get_event_stats(database)
                # Generar visualizaciones
                generate_visualizations(database)
                
                # Enviar datos actualizados a todos los clientes
                socketio.emit('data_updated', {
                    "stats": sanitize_for_json(stats),
                    "update_info": sanitize_for_json(update_info)
                })
                logger.info("Datos actualizados y enviados a clientes")
                return True
            else:
                logger.info("Actualización completada: No hay cambios en los datos")
                return False
        else:
            logger.error(f"Error en actualización de datos: {update_info['error']}")
            return False
    except Exception as e:
        logger.error(f"Error en función update_data: {str(e)}")
        return False

@socketio.on('manual_update')
def handle_manual_update(data):
    """Procesa una solicitud de actualización manual de datos."""
    try:
        global updating_data
        logger.info("Solicitud manual de actualización de datos recibida")
        
        if updating_data:
            logger.info("Ya hay una actualización en curso, ignorando solicitud")
            return {"success": False, "error": "Ya hay una actualización en curso"}
        
        # Iniciar proceso de actualización
        updating_data = True
        update_start_time = time.time()
        
        try:
            update_result = update_data()
            
            if update_result:
                logger.info(f"Actualización manual completada en {time.time() - update_start_time:.2f} segundos")
                return {"success": True}
            else:
                logger.warning("La actualización manual no encontró cambios")
                return {"success": False, "error": "No se encontraron cambios"}
        finally:
            updating_data = False
            
    except Exception as e:
        logger.error(f"Error en actualización manual: {str(e)}")
        updating_data = False
        return {"success": False, "error": str(e)}

@socketio.on('start_game')
def handle_start_game(data):
    """Maneja la solicitud para iniciar el juego."""
    try:
        logger.info("Solicitud para iniciar el juego recibida")
        result = game_manager.start_game()
        
        if result['success']:
            logger.info(f"Juego iniciado correctamente: {result.get('message', '')}")
        else:
            logger.error(f"Error al iniciar el juego: {result.get('error', 'Error desconocido')}")
            
        return result
    except Exception as e:
        logger.error(f"Error al iniciar el juego: {str(e)}")
        return {"success": False, "error": str(e)}

@socketio.on('open_game_folder')
def handle_open_game_folder(data):
    """Maneja la solicitud para abrir la carpeta del juego."""
    try:
        logger.info("Solicitud para abrir la carpeta del juego recibida")
        result = game_manager.open_game_folder()
        
        if result['success']:
            logger.info(f"Carpeta del juego abierta correctamente: {result.get('message', '')}")
        else:
            logger.error(f"Error al abrir la carpeta del juego: {result.get('error', 'Error desconocido')}")
            
        return result
    except Exception as e:
        logger.error(f"Error al abrir la carpeta del juego: {str(e)}")
        return {"success": False, "error": str(e)}

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
    
    # Iniciar thread de verificación del juego
    game_check_thread = threading.Thread(target=check_game_status)
    game_check_thread.daemon = True
    game_check_thread.start()
    
    logger.info(f"Servidor iniciado en http://localhost:{PORT}")
    socketio.run(app, host="0.0.0.0", port=PORT, debug=True, allow_unsafe_werkzeug=True) 