#!/usr/bin/env python
"""
Script mejorado para extraer datos del mod DEM.
Implementa captura de datos más detallada y frecuente.
"""

import os
import sys
import json
import time
import shutil
import hashlib
import logging
import argparse
import datetime
from pathlib import Path
from collections import defaultdict, Counter

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/extract.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar configuración desde archivo
def load_config():
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Archivo de configuración no encontrado, usando valores por defecto")
        return {
            "paths": {
                "data_dir": "data",
                "processed_data_dir": "processed_data",
                "received_data_dir": "received_data",
                "logs_dir": "logs"
            },
            "database": {
                "file": "dem_database.json"
            },
            "data_capture": {
                "frame_rate": 5,
                "detailed_positions": True
            },
            "advanced": {
                "verbose_logging": True
            }
        }
    except Exception as e:
        logger.error(f"Error al cargar configuración: {str(e)}")
        sys.exit(1)

# Inicializar desde config
config = load_config()
PATHS = config["paths"]
DATABASE_FILE = config["database"]["file"]
VERBOSE_LOGGING = config["advanced"]["verbose_logging"]

def ensure_directories_exist():
    """Asegura que existan todos los directorios necesarios"""
    for path_name, path_value in PATHS.items():
        os.makedirs(path_value, exist_ok=True)
        if VERBOSE_LOGGING:
            logger.info(f"Directorio asegurado: {path_value}")

def find_log_files():
    """Busca archivos de log del mod en el directorio de datos del juego"""
    # Ruta para Windows
    possible_locations = [
        os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance", "dem_logs"),
        os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Afterbirth+", "dem_logs"),
        os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Rebirth", "dem_logs")
    ]
    
    # Buscar logs en ubicaciones conocidas
    log_files = []
    for location in possible_locations:
        if os.path.exists(location):
            if VERBOSE_LOGGING:
                logger.info(f"Buscando logs en: {location}")
            for file in os.listdir(location):
                if file.endswith(".json"):
                    log_files.append(os.path.join(location, file))
    
    if not log_files:
        logger.warning("No se encontraron archivos de log del mod")
    else:
        logger.info(f"Se encontraron {len(log_files)} archivos de log")
    
    return log_files

def process_log_file(log_file, database, keep_originals=False):
    """Procesa un archivo de log y añade sus eventos a la base de datos"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                log_data = json.load(f)
                
                # Validar formato del log
                if not isinstance(log_data, list):
                    logger.warning(f"Formato de log inválido en {log_file}, debe ser una lista de eventos")
                    log_data = [log_data]  # Intentar convertir a lista si es un único objeto
                
                # Procesar cada evento
                processed_count = 0
                new_count = 0
                skipped_count = 0
                
                # Usar un conjunto para rastrear eventos existentes para búsqueda rápida
                existing_events = set()
                for event in database["events"]:
                    if "id" in event:
                        existing_events.add(event["id"])
                
                for event in log_data:
                    processed_count += 1
                    
                    # Mejorar los eventos con datos faltantes
                    enrich_event_data(event)
                    
                    # Asignar ID si no tiene
                    if "id" not in event:
                        event_content = json.dumps(event, sort_keys=True)
                        event["id"] = hashlib.md5(event_content.encode()).hexdigest()
                    
                    # Evitar duplicados
                    if event["id"] not in existing_events:
                        # Enriquecer con timestamp si no tiene
                        if "timestamp" not in event:
                            # Usar el timestamp del archivo como respaldo
                            event["timestamp"] = os.path.getmtime(log_file)
                        
                        database["events"].append(event)
                        existing_events.add(event["id"])
                        new_count += 1
                    else:
                        skipped_count += 1
                
                # Mover el archivo procesado a la carpeta correspondiente
                if keep_originals:
                    # Copiar en lugar de mover
                    dest_file = os.path.join(PATHS["received_data_dir"], os.path.basename(log_file))
                    shutil.copy2(log_file, dest_file)
                    if VERBOSE_LOGGING:
                        logger.info(f"Archivo copiado a {dest_file}")
                else:
                    # Mover el archivo
                    dest_file = os.path.join(PATHS["received_data_dir"], os.path.basename(log_file))
                    shutil.move(log_file, dest_file)
                    if VERBOSE_LOGGING:
                        logger.info(f"Archivo movido a {dest_file}")
                
                logger.info(f"Procesado {log_file}: {processed_count} eventos procesados, {new_count} nuevos, {skipped_count} duplicados")
                return new_count
            except json.JSONDecodeError as je:
                logger.error(f"Error al decodificar JSON en {log_file}: {str(je)}")
                return 0
    except Exception as e:
        logger.error(f"Error al procesar archivo {log_file}: {str(e)}")
        return 0

def enrich_event_data(event):
    """Enriquece un evento con datos adicionales y categorización mejorada"""
    # Determinar tipo de evento si no está definido
    if "event_type" not in event or not event["event_type"] or event["event_type"] == "unknown":
        # Inferir tipo de evento basado en contenido
        infer_event_type(event)
    
    # Asegurar que exista campo de datos
    if "data" not in event:
        event["data"] = {}
    
    # Asegurar timestamp
    if "timestamp" not in event:
        event["timestamp"] = time.time()
    
    # Añadir marcas de tiempo legibles si no existen
    if "timestamp_readable" not in event:
        try:
            timestamp = float(event["timestamp"])
            event["timestamp_readable"] = datetime.datetime.fromtimestamp(timestamp).isoformat()
        except:
            pass
    
    # Añadir información de versión del mod si no existe
    if "mod_info" not in event:
        event["mod_info"] = {
            "version": "1.0",
            "name": "DEM"
        }
    
    # Mejorar información del jugador
    if "data" in event and "player" in event["data"]:
        player_data = event["data"]["player"]
        
        # Asegurar que existan campos de posición detallados
        if "position" in player_data and player_data["position"] and config["data_capture"]["detailed_positions"]:
            pos = player_data["position"]
            if isinstance(pos, dict) and "x" in pos and "y" in pos:
                # Añadir coordenadas de cuadrícula/sala si no existen
                if "grid_x" not in pos or "grid_y" not in pos:
                    pos["grid_x"] = int(pos["x"] / 40)  # Valores aproximados, ajustar según el juego
                    pos["grid_y"] = int(pos["y"] / 40)
    
    # Enriquecer datos de enemigos
    if "data" in event and "entities" in event["data"]:
        entities = event["data"]["entities"]
        if entities:
            for entity in entities:
                if entity and entity.get("is_enemy", False):
                    # Añadir posición de cuadrícula si es necesario
                    if "position" in entity and entity["position"] and config["data_capture"]["detailed_positions"]:
                        pos = entity["position"]
                        if isinstance(pos, dict) and "x" in pos and "y" in pos:
                            if "grid_x" not in pos or "grid_y" not in pos:
                                pos["grid_x"] = int(pos["x"] / 40)
                                pos["grid_y"] = int(pos["y"] / 40)

def infer_event_type(event):
    """Infiere el tipo de evento basado en su contenido"""
    # Verificar si hay datos de jugador
    if "data" in event and "player" in event["data"]:
        player_data = event["data"]["player"]
        
        # Verificar si hay información de salud
        if player_data.get("health"):
            event["event_type"] = "player_health"
        # Verificar si hay información de posición
        elif player_data.get("position"):
            event["event_type"] = "player_position"
        # Verificar si hay información de velocidad
        elif player_data.get("velocity"):
            event["event_type"] = "player_movement"
        # Verificar si hay información de estadísticas
        elif player_data.get("stats"):
            event["event_type"] = "player_stats"
        # Verificar si hay información de inventario
        elif player_data.get("inventory") or player_data.get("items"):
            event["event_type"] = "player_items"
        else:
            event["event_type"] = "player_state"
    
    # Verificar si hay datos de enemigos
    elif "data" in event and "entities" in event["data"]:
        entities = event["data"]["entities"]
        if entities and any(entity and entity.get("is_enemy", False) for entity in entities):
            # Verificar si hay información de posición de enemigos
            if any(entity and entity.get("position") for entity in entities if entity and entity.get("is_enemy", False)):
                event["event_type"] = "enemy_position"
            # Verificar si hay información de salud de enemigos
            elif any(entity and entity.get("health") for entity in entities if entity and entity.get("is_enemy", False)):
                event["event_type"] = "enemy_health"
            else:
                event["event_type"] = "enemy_data"
        elif entities:
            event["event_type"] = "entity_data"
    
    # Verificar si hay datos de sala
    elif "data" in event and "room" in event["data"]:
        event["event_type"] = "room_state"
    
    # Verificar si hay datos de nivel
    elif "data" in event and "level" in event["data"]:
        event["event_type"] = "level_state"
    
    # Verificar si hay datos de juego
    elif "game_data" in event or ("data" in event and "game_state" in event["data"]):
        event["event_type"] = "game_state"
    
    # Si nada más funciona, usar un tipo genérico
    else:
        event["event_type"] = "general_event"

def backup_database(database_file):
    """Crea una copia de seguridad de la base de datos"""
    if os.path.exists(database_file):
        backup_dir = os.path.join(PATHS["data_dir"], "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"dem_database_{timestamp}.json")
        
        try:
            shutil.copy2(database_file, backup_file)
            logger.info(f"Copia de seguridad creada: {backup_file}")
            
            # Limitar número de copias (mantener últimas 5)
            backup_files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)])
            if len(backup_files) > 5:
                for old_file in backup_files[:-5]:
                    os.remove(old_file)
                    if VERBOSE_LOGGING:
                        logger.info(f"Eliminada copia de seguridad antigua: {old_file}")
                
        except Exception as e:
            logger.error(f"Error al crear copia de seguridad: {str(e)}")

def save_database(database, database_file):
    """Guarda la base de datos"""
    # Actualizar metadatos
    database["metadata"]["last_update"] = datetime.datetime.now().isoformat()
    database["metadata"]["total_events"] = len(database["events"])
    
    try:
        # Crear backup antes de guardar
        backup_database(database_file)
        
        # Guardar base de datos
        with open(database_file, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2)
        
        logger.info(f"Base de datos guardada: {len(database['events'])} eventos")
        return True
    except Exception as e:
        logger.error(f"Error al guardar base de datos: {str(e)}")
        return False

def load_database(database_file):
    """Carga la base de datos"""
    if not os.path.exists(database_file):
        logger.warning(f"Base de datos {database_file} no encontrada, creando una nueva")
        return {
            "events": [],
            "metadata": {
                "last_update": datetime.datetime.now().isoformat(),
                "total_events": 0,
                "version": "1.0"
            }
        }
    
    try:
        with open(database_file, 'r', encoding='utf-8') as f:
            database = json.load(f)
            logger.info(f"Base de datos cargada: {len(database.get('events', []))} eventos")
            return database
    except Exception as e:
        logger.error(f"Error al cargar la base de datos: {str(e)}")
        return {
            "events": [],
            "metadata": {
                "last_update": datetime.datetime.now().isoformat(),
                "total_events": 0,
                "version": "1.0",
                "error": str(e)
            }
        }

def check_game_running():
    """Verifica si el juego está en ejecución"""
    # Lista de posibles procesos del juego en Windows
    game_processes = ["isaac-ng.exe", "isaac.exe", "Rebirth.exe", "Afterbirth.exe", "AfterbirthPlus.exe", "RepentanceDX11.exe", "RepentanceDX9.exe"]
    
    try:
        import subprocess
        
        # Intentar con wmic
        try:
            process_list = subprocess.run(['wmic', 'process', 'get', 'name'], 
                                         capture_output=True, text=True, encoding='cp850')
            
            process_output = process_list.stdout.lower()
            
            for process in game_processes:
                if process.lower() in process_output:
                    logger.info(f"Juego detectado: {process}")
                    return True
        except:
            # Intentar con tasklist como plan B
            for process in game_processes:
                try:
                    result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process}'], 
                                           capture_output=True, text=True, encoding='cp850')
                    if process in result.stdout:
                        logger.info(f"Juego detectado con tasklist: {process}")
                        return True
                except:
                    pass
    except:
        logger.warning("No se pudo verificar si el juego está en ejecución")
    
    logger.info("Juego no detectado en ejecución")
    return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Extrae datos del mod DEM')
    parser.add_argument('--keep-originals', action='store_true', help='Mantener archivos originales')
    parser.add_argument('--force', action='store_true', help='Forzar extracción incluso si el juego no está en ejecución')
    args = parser.parse_args()
    
    # Asegurar que existan directorios
    ensure_directories_exist()
    
    # Verificar si el juego está en ejecución (a menos que se fuerce)
    if not args.force and not check_game_running():
        logger.warning("El juego no está en ejecución. Use --force para extraer datos de todos modos.")
        return
    
    # Cargar base de datos
    database_file = os.path.join(os.getcwd(), DATABASE_FILE)
    database = load_database(database_file)
    
    # Buscar archivos de log
    log_files = find_log_files()
    
    if not log_files:
        logger.warning("No se encontraron archivos de log para procesar")
        return
    
    # Procesar cada archivo de log
    total_new_events = 0
    for log_file in log_files:
        new_events = process_log_file(log_file, database, args.keep_originals)
        total_new_events += new_events
    
    if total_new_events > 0:
        # Guardar base de datos actualizada
        save_database(database, database_file)
        logger.info(f"Extracción completada: {total_new_events} nuevos eventos añadidos")
    else:
        logger.info("Extracción completada: No se encontraron nuevos eventos")

if __name__ == "__main__":
    main() 