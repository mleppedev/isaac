#!/usr/bin/env python
"""
Servidor web para visualizar los datos del mod DEM (versión básica sin WebSockets).
"""

import os
import json
import time
from datetime import datetime
from collections import Counter, defaultdict
from flask import Flask, jsonify, render_template, send_from_directory, request

# Configuración
DATABASE_FILE = "dem_database.json"
STATIC_FOLDER = "static"
TEMPLATE_FOLDER = "templates"
PORT = 8000

app = Flask(__name__, 
            static_folder=STATIC_FOLDER,
            template_folder=TEMPLATE_FOLDER)

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

@app.route('/')
def index():
    """Página principal"""
    database = load_database()
    stats = get_event_stats(database)
    return render_template('index_basic.html', stats=stats)

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
    import subprocess
    result = subprocess.run(["python", "extract_data.py", "--keep-originals"], capture_output=True, text=True)
    
    update_data = {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr,
        "timestamp": datetime.now().isoformat()
    }
    
    # Si la actualización fue exitosa, actualizar la base de datos
    if update_data["success"]:
        database = load_database()
        database["metadata"]["last_update"] = update_data["timestamp"]
        
        # Guardar metadatos actualizados
        try:
            with open(DATABASE_FILE, 'w') as f:
                json.dump(database, f, indent=2)
        except Exception as e:
            update_data["error"] = f"Error al actualizar base de datos: {str(e)}"
            update_data["success"] = False
    
    return jsonify(update_data)

if __name__ == "__main__":
    # Crear directorios si no existen
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
    
    print(f"Servidor iniciado en http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True) 