#!/usr/bin/env python
"""
Script simple para probar la lectura del archivo de datos del mod DEM.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Posibles ubicaciones del archivo de datos
DATA_PATHS = [
    # Ruta principal actual
    os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance+", "Data Event Manager.dat"),
    # Ruta alternativa (antigua)
    os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance Mods", "Data Event Manager.dat"),
    # Ruta Steam
    os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth", "data", "Data Event Manager.dat"),
    # Rutas directas al mod
    os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth", "mods", "DEM", "Data Event Manager.dat"),
    os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth", "mods", "DEM", "DEM_Data"),
    # Rutas de copia de seguridad
    os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance+", "backups"),
    os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance Mods", "backups")
]

def setup_logging():
    """Configurar logging básico"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger()

def find_data_files():
    """Buscar todos los archivos de datos posibles"""
    found_files = []
    checked_paths = []
    
    # Primero buscar el archivo principal
    for path in DATA_PATHS:
        checked_paths.append(path)
        if os.path.isdir(path):
            # Si es un directorio, buscar archivos .dat y .json
            logging.info(f"Buscando en directorio: {path}")
            if os.path.exists(path):
                for filename in os.listdir(path):
                    if filename.endswith((".dat", ".json")):
                        full_path = os.path.join(path, filename)
                        size = os.path.getsize(full_path)
                        found_files.append((full_path, size))
                        logging.info(f"  Encontrado: {filename} ({size} bytes)")
        else:
            # Es un archivo específico
            if os.path.exists(path):
                size = os.path.getsize(path)
                found_files.append((path, size))
                logging.info(f"Encontrado archivo: {path} ({size} bytes)")
    
    # Buscar en directorios adicionales
    additional_dirs = [
        # Directorio principal de usuario
        os.path.join(os.path.expanduser("~"), "Documents", "My Games"),
        # Directorio de mods de Steam
        os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth"),
        # Directorio actual
        os.getcwd()
    ]
    
    for base_dir in additional_dirs:
        if os.path.exists(base_dir):
            logging.info(f"Buscando en directorio adicional: {base_dir}")
            # Hacer búsqueda recursiva para encontrar archivos Data Event Manager.dat
            for root, dirs, files in os.walk(base_dir, topdown=True):
                # Limitar profundidad de búsqueda para evitar búsquedas muy largas
                if root.count(os.sep) - base_dir.count(os.sep) > 3:
                    continue
                
                for filename in files:
                    if filename == "Data Event Manager.dat" or (filename.endswith(".dat") and "DEM" in filename):
                        full_path = os.path.join(root, filename)
                        if os.path.exists(full_path):
                            size = os.path.getsize(full_path)
                            if size > 0:  # Solo incluir archivos no vacíos
                                found_files.append((full_path, size))
                                logging.info(f"  Encontrado: {full_path} ({size} bytes)")
    
    # Ordenar por tamaño (mayor primero)
    found_files.sort(key=lambda x: x[1], reverse=True)
    
    # Si no se encontraron archivos, mostrar todas las rutas verificadas
    if not found_files:
        logging.warning("No se encontraron archivos. Rutas verificadas:")
        for path in checked_paths:
            exists = os.path.exists(path)
            logging.warning(f"  - {path} (Existe: {exists})")
        
        # Verificar si existe el log.txt y mostrar su ubicación
        log_paths = [
            os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance+", "log.txt"),
            os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth", "log.txt")
        ]
        
        for log_path in log_paths:
            if os.path.exists(log_path):
                logging.info(f"Log del juego encontrado en: {log_path}")
                # Mostrar las últimas líneas del log que tengan 'DEM:'
                try:
                    with open(log_path, 'r', errors='ignore') as f:
                        lines = f.readlines()
                        dem_lines = [line for line in lines[-200:] if "DEM:" in line]
                        if dem_lines:
                            logging.info("Últimas líneas de log relevantes:")
                            for line in dem_lines[-10:]:
                                logging.info(f"  {line.strip()}")
                except Exception as e:
                    logging.error(f"Error al leer log: {e}")
    
    return found_files

def convert_isaac_timestamp(timestamp):
    """Convierte el timestamp basado en frames a un formato más legible"""
    # Aproximadamente 30 FPS en el juego
    seconds = timestamp / 30
    # Calcular minutos y segundos
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    # Devolver formato legible
    return f"{minutes}m {secs}s (frame {timestamp})"

def read_data_file(file_path):
    """Leer e interpretar un archivo de datos"""
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read().strip()
        
        if not content:
            logging.warning(f"Archivo vacío: {file_path}")
            return None
        
        # Determinar el tipo de contenido
        if content.startswith('['):
            logging.info(f"El archivo contiene un array JSON")
            data = json.loads(content)
            return data
        elif content.startswith('{'):
            logging.info(f"El archivo contiene un objeto JSON")
            data = json.loads(content)
            return [data]
        else:
            logging.warning(f"Contenido no reconocido: {content[:50]}...")
            return None
            
    except Exception as e:
        logging.error(f"Error al leer archivo {file_path}: {e}")
        return None

def analyze_events(events):
    """Analizar eventos para mostrar información básica"""
    if not events:
        return
    
    event_types = {}
    timestamps = []
    
    for event in events:
        # Contar tipos de eventos
        event_type = event.get("event_type", "unknown")
        event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Recopilar timestamps
        if "timestamp" in event:
            timestamps.append(event["timestamp"])
    
    logging.info(f"Tipos de eventos encontrados:")
    for event_type, count in event_types.items():
        logging.info(f"  - {event_type}: {count} eventos")
    
    if timestamps:
        # Convertir los timestamps basados en frames a formato legible
        min_ts = min(timestamps)
        max_ts = max(timestamps)
        min_ts_readable = convert_isaac_timestamp(min_ts)
        max_ts_readable = convert_isaac_timestamp(max_ts)
        duration_frames = max_ts - min_ts
        duration_secs = duration_frames / 30  # Aproximadamente 30 FPS
        
        logging.info(f"Rango de tiempo de juego: desde {min_ts_readable} hasta {max_ts_readable}")
        logging.info(f"Duración total: aproximadamente {int(duration_secs)} segundos ({duration_frames} frames)")

def main():
    """Función principal"""
    logger = setup_logging()
    logger.info("DEM - Test de lectura de datos")
    
    # Mostrar información de sistema
    logger.info(f"Directorio actual: {os.getcwd()}")
    
    # Buscar archivos de datos
    data_files = find_data_files()
    
    if not data_files:
        logger.warning("No se encontraron archivos de datos en las rutas especificadas")
        return 1
    
    logger.info(f"Encontrados {len(data_files)} archivos de datos:")
    for i, (path, size) in enumerate(data_files):
        logger.info(f"{i+1}. {path} - {size} bytes")
    
    # Analizar el archivo más grande
    largest_file = data_files[0][0]
    logger.info(f"Analizando el archivo más grande: {largest_file}")
    
    events = read_data_file(largest_file)
    if events:
        logger.info(f"Encontrados {len(events)} eventos en el archivo")
        analyze_events(events)
        
        # Mostrar un ejemplo de evento
        if events:
            logger.info("Ejemplo de evento:")
            example = events[0]
            
            # Si hay timestamp, mostrar versión legible
            if "timestamp" in example:
                example["timestamp_readable"] = convert_isaac_timestamp(example["timestamp"])
                
            logger.info(json.dumps(example, indent=2))
    else:
        logger.warning("No se pudieron leer eventos del archivo")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 