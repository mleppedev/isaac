#!/usr/bin/env python
"""
Servidor web para visualizar los datos del mod DEM.
"""

import os
import json
import time
import threading
import hashlib
from datetime import datetime
from collections import Counter, defaultdict
from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_socketio import SocketIO

# Configuración
DATABASE_FILE = "dem_database.json"
STATIC_FOLDER = "static"
TEMPLATE_FOLDER = "templates"
PORT = 5000
UPDATE_INTERVAL = 60  # segundos entre actualizaciones automáticas (aumentado a 60 segundos)
EMIT_THROTTLE = 10    # segundos mínimos entre emisiones a clientes

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
        return {
            "events": [],
            "metadata": {
                "last_update": datetime.now().isoformat(),
                "total_events": 0,
                "version": "1.0"
            }
        }
    
    try:
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "events": [],
            "metadata": {
                "last_update": datetime.now().isoformat(),
                "total_events": 0,
                "version": "1.0"
            }
        }

def get_event_stats(database):
    """Obtener estadísticas de eventos"""
    events = database.get("events", [])
    
    if not events:
        return {
            "total": 0,
            "types": [],
            "seeds": [],
            "latest_update": None
        }
    
    # Contar tipos de eventos
    event_types = Counter(event.get("event_type", "unknown") for event in events)
    event_type_stats = [
        {"type": event_type, "count": count, "percentage": (count / len(events)) * 100}
        for event_type, count in event_types.most_common()
    ]
    
    # Eventos por partida
    events_by_seed = defaultdict(list)
    for event in events:
        seed = event.get("game_data", {}).get("seed", 0)
        if seed:
            events_by_seed[seed].append(event)
    
    seed_stats = [
        {
            "seed": seed,
            "count": len(seed_events),
            "types": Counter(event.get("event_type", "unknown") for event in seed_events).most_common(3)
        }
        for seed, seed_events in sorted(events_by_seed.items(), key=lambda x: len(x[1]), reverse=True)
    ]
    
    return {
        "total": len(events),
        "types": event_type_stats,
        "seeds": seed_stats,
        "latest_update": database.get("metadata", {}).get("last_update")
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
        print(f"[{datetime.now().isoformat()}] Ejecutando actualización automática de datos...")
        result = subprocess.run(["python", "extract_data.py", "--keep-originals"], capture_output=True, text=True)
        
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
                
                # Obtener estadísticas y enviar a clientes
                stats = get_event_stats(database)
                socketio.emit('data_updated', {
                    "stats": stats,
                    "update_info": update_data
                })
                print(f"[{datetime.now().isoformat()}] Datos actualizados y enviados a clientes conectados")
            elif current_hash != last_data_hash:
                print(f"[{datetime.now().isoformat()}] Datos actualizados pero throttling activo, esperando {EMIT_THROTTLE - time_since_last_emission:.1f}s más")
                # Actualizar el hash pero no emitir todavía
                last_data_hash = current_hash
            else:
                print(f"[{datetime.now().isoformat()}] No hay cambios en los datos, omitiendo actualización")
        else:
            socketio.emit('update_error', update_data)
            print(f"[{datetime.now().isoformat()}] Error al actualizar datos: {update_data['error']}")
        
        # Esperar para la próxima actualización
        thread_stop_event.wait(UPDATE_INTERVAL)

@app.route('/')
def index():
    """Página principal"""
    database = load_database()
    stats = get_event_stats(database)
    return render_template('index.html', stats=stats)

@app.route('/data')
def data():
    """Página de datos"""
    database = load_database()
    stats = get_event_stats(database)
    return render_template('data.html', stats=stats)

@app.route('/stats')
def stats():
    """Página de estadísticas"""
    database = load_database()
    stats = get_event_stats(database)
    return render_template('stats.html', stats=stats)

@app.route('/api/events')
def api_events():
    """API para obtener todos los eventos"""
    database = load_database()
    return jsonify(database.get("events", []))

@app.route('/api/stats')
def api_stats():
    """API para obtener estadísticas"""
    database = load_database()
    stats = get_event_stats(database)
    return jsonify(stats)

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

@app.route('/api/refresh')
def api_refresh():
    """API para refrescar los datos (ejecuta extract_data.py)"""
    global last_data_hash
    import subprocess
    result = subprocess.run(["python", "extract_data.py", "--keep-originals"], capture_output=True, text=True)
    
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
            # Enviar datos completos
            socketio.emit('data_updated', {
                "stats": stats,
                "update_info": update_data
            })
            print(f"[{datetime.now().isoformat()}] Datos actualizados manualmente y enviados a clientes")
        else:
            print(f"[{datetime.now().isoformat()}] Actualización manual: No hay cambios en los datos")
    
    return jsonify(update_data)

@socketio.on('connect')
def handle_connect():
    """Manejador de conexión de cliente"""
    client_id = request.sid
    print(f"[{datetime.now().isoformat()}] Cliente conectado: {client_id}")
    
    # Iniciar thread de actualización si no está en ejecución
    global update_thread, last_data_hash
    if update_thread is None or not update_thread.is_alive():
        thread_stop_event.clear()
        update_thread = threading.Thread(target=update_data_background)
        update_thread.daemon = True
        update_thread.start()
        print(f"[{datetime.now().isoformat()}] Thread de actualización automática iniciado")
    
    # Enviar datos actualizados al cliente recién conectado, respetando el throttling
    try:
        # No necesitamos aplicar throttling para clientes nuevos, siempre enviar datos iniciales
        database = load_database()
        
        # Actualizar el hash si es necesario
        if last_data_hash is None:
            last_data_hash = calculate_data_hash(database)
            
        stats = get_event_stats(database)
        
        # Enviar los datos al cliente que se acaba de conectar
        socketio.emit('data_updated', {
            "stats": stats,
            "update_info": {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Datos iniciales cargados",
                "is_initial_load": True  # Indicador para que el cliente sepa que es carga inicial
            }
        }, room=client_id)  # Solo enviar al cliente recién conectado
        
        print(f"[{datetime.now().isoformat()}] Datos iniciales enviados a cliente: {client_id}")
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error al enviar datos iniciales: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Manejador de desconexión de cliente"""
    print(f"[{datetime.now().isoformat()}] Cliente desconectado: {request.sid}")

@socketio.on('manual_refresh')
def handle_manual_refresh():
    """Manejador de solicitud manual de actualización"""
    print(f"[{datetime.now().isoformat()}] Solicitud manual de actualización recibida")
    return api_refresh()

if __name__ == "__main__":
    # Crear directorios si no existen
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
    
    print(f"Servidor iniciado en http://localhost:{PORT}")
    socketio.run(app, host="0.0.0.0", port=PORT, debug=True, allow_unsafe_werkzeug=True) 