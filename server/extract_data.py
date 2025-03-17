#!/usr/bin/env python
"""
Script para extraer datos del mod DEM y cargarlos en el servidor.
Esta es la versión simplificada que lee directamente los archivos JSON.
"""

import os
import sys
import json
import glob
import shutil
import logging
import argparse
from datetime import datetime
import subprocess

# Configuración - Rutas según el log
# Ubicación donde Isaac guarda los datos de los mods - Documentos del usuario
ISAAC_MODS_DATA_DIR = os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance+")

# Ubicación alternativa por si acaso (la antigua ruta)
ISAAC_MODS_DATA_DIR_ALT = os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance Mods")

# Ubicación directa de Steam
ISAAC_STEAM_DIR = os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth")

# Ubicación del mod
MOD_DIR = os.path.join(ISAAC_STEAM_DIR, "mods", "DEM")

# Ubicación por si existen archivos individuales (legacy)
DEFAULT_DATA_DIR = os.path.join(MOD_DIR, "DEM_Data")

# Ubicación real del archivo de datos (ruta encontrada)
REAL_DATA_PATH = "D:\\SteamLibrary\\steamapps\\common\\The Binding of Isaac Rebirth\\data\\dem\\save1.dat"

# Nombre del archivo de datos de mod (para las rutas legacy)
MOD_DATA_FILE = "Data Event Manager.dat"

PROCESSED_DIR = "processed"
DATABASE_FILE = "dem_database.json"
LOG_FILE = "extract_data.log"

# Variables globales para control de verificaciones
check_game_running = True
check_file_timestamp = True

def setup_logging(log_file=LOG_FILE, debug=False):
    """Configurar el registro de eventos"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # También mostrar en consola
    console = logging.StreamHandler()
    console.setLevel(log_level)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    return logging.getLogger('')

def load_database(db_file=DATABASE_FILE):
    """Cargar la base de datos existente o crear una nueva"""
    if os.path.exists(db_file):
        try:
            with open(db_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"Error al cargar la base de datos {db_file}. Creando una nueva.")
    
    # Crear estructura de base de datos vacía
    return {
        "events": [],
        "metadata": {
            "last_update": datetime.now().isoformat(),
            "total_events": 0,
            "version": "1.0"
        }
    }

def save_database(database, db_file=DATABASE_FILE):
    """Guardar la base de datos actualizada"""
    # Actualizar metadatos
    database["metadata"]["last_update"] = datetime.now().isoformat()
    database["metadata"]["total_events"] = len(database["events"])
    
    # Guardar
    try:
        with open(db_file, 'w') as f:
            json.dump(database, f, indent=2)
        logging.info(f"Base de datos guardada: {len(database['events'])} eventos en total")
        return True
    except Exception as e:
        logging.error(f"Error al guardar la base de datos: {e}")
        return False

def find_all_possible_data_files():
    """Encuentra todas las posibles ubicaciones de archivos de datos"""
    global check_game_running, check_file_timestamp
    possible_paths = []
    found_files = []
    
    # Verificar si el juego está en ejecución (solo si check_game_running es True)
    if check_game_running:
        try:
            # Verificar si Isaac está en ejecución (Windows)
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq isaac-ng.exe'], 
                                   capture_output=True, text=True)
            game_running = 'isaac-ng.exe' in result.stdout
            
            if not game_running:
                logging.warning("El juego no está en ejecución. No se procesarán datos.")
                return []
        except Exception as e:
            logging.error(f"Error al verificar si el juego está en ejecución: {e}")
            # Si hay error al verificar, continuar normalmente
    else:
        logging.info("Verificación de ejecución del juego desactivada. Se procesarán los datos independientemente.")
    
    # Obtener información de la última modificación del archivo de base de datos (solo si check_file_timestamp es True)
    last_modified = None
    if check_file_timestamp and os.path.exists(DATABASE_FILE):
        last_modified = os.path.getmtime(DATABASE_FILE)
        logging.info(f"Última modificación de la base de datos: {datetime.fromtimestamp(last_modified)}")
    
    # 1. Verificar la ubicación real encontrada (PRINCIPAL)
    if os.path.exists(REAL_DATA_PATH):
        file_modified = os.path.getmtime(REAL_DATA_PATH)
        size = os.path.getsize(REAL_DATA_PATH)
        
        # Verificar si el archivo ha cambiado desde la última vez (solo si check_file_timestamp es True)
        if check_file_timestamp and last_modified and file_modified <= last_modified:
            logging.info(f"Archivo {REAL_DATA_PATH} no ha cambiado desde la última actualización. Se omitirá.")
        else:
            found_files.append((REAL_DATA_PATH, size))
            logging.info(f"Archivo encontrado en ubicación real: {REAL_DATA_PATH} ({size} bytes)")
    else:
        logging.warning(f"No se encontró el archivo en la ubicación real: {REAL_DATA_PATH}")
        
        # 2. Comprobar la ruta principal en Documentos
        path1 = os.path.join(ISAAC_MODS_DATA_DIR, MOD_DATA_FILE)
        possible_paths.append(("Doc principal", path1))
        
        # 3. Comprobar ruta alternativa en Documentos
        path2 = os.path.join(ISAAC_MODS_DATA_DIR_ALT, MOD_DATA_FILE)
        possible_paths.append(("Doc alternativo", path2))
        
        # 4. Comprobar en directorio data de Steam
        path3 = os.path.join(ISAAC_STEAM_DIR, "data", MOD_DATA_FILE)
        possible_paths.append(("Steam data", path3))
        
        # 5. Comprobar en directorio DEM
        path4 = os.path.join(MOD_DIR, MOD_DATA_FILE)
        possible_paths.append(("Directorio mod", path4))
        
        # 6. Comprobar en carpeta de datos del mod
        path5 = DEFAULT_DATA_DIR
        possible_paths.append(("Directorio datos mod", path5))
        
        # Verificar cada ruta y guardar los archivos encontrados
        for desc, path in possible_paths:
            if os.path.exists(path):
                if os.path.isdir(path):
                    # Si es un directorio, buscar archivos .dat y .json
                    for filename in os.listdir(path):
                        if filename.endswith((".dat", ".json")):
                            full_path = os.path.join(path, filename)
                            
                            # Verificar si el archivo ha cambiado desde la última vez
                            if check_file_timestamp:
                                file_modified = os.path.getmtime(full_path)
                                if last_modified and file_modified <= last_modified:
                                    logging.info(f"Archivo {full_path} no ha cambiado desde la última actualización. Se omitirá.")
                                    continue
                                
                            size = os.path.getsize(full_path)
                            if size > 0:  # Solo incluir archivos no vacíos
                                found_files.append((full_path, size))
                                logging.info(f"Encontrado archivo en {desc}: {filename} ({size} bytes)")
                else:
                    # Es un archivo específico
                    # Verificar si el archivo ha cambiado desde la última vez
                    if os.path.exists(path):
                        if check_file_timestamp:
                            file_modified = os.path.getmtime(path)
                            if last_modified and file_modified <= last_modified:
                                logging.info(f"Archivo {path} no ha cambiado desde la última actualización. Se omitirá.")
                                continue
                            
                        size = os.path.getsize(path)
                        if size > 0:  # Solo incluir archivos no vacíos
                            found_files.append((path, size))
                            logging.info(f"Encontrado archivo en {desc}: {os.path.basename(path)} ({size} bytes)")
    
    # Si no se encontraron archivos en las rutas principales, buscar en directorios adicionales
    if not found_files:
        if check_file_timestamp:
            logging.warning("No se encontraron archivos en rutas principales o no han cambiado desde la última actualización.")
        else:
            logging.warning("No se encontraron archivos en rutas principales.")
            
    return found_files

def backup_mod_data(file_path, keep_original=False):
    """Hace una copia de seguridad del archivo de datos del mod"""
    if not os.path.exists(file_path):
        logging.warning(f"No se puede hacer backup: el archivo {file_path} no existe")
        return False
    
    # Crear directorio de respaldos si no existe
    backup_dir = os.path.join(os.path.dirname(file_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nombre del archivo de respaldo (con fecha)
    backup_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Copiar archivo
        shutil.copy2(file_path, backup_path)
        logging.info(f"Backup creado: {backup_path}")
        
        # Eliminar original si es necesario
        if not keep_original:
            os.remove(file_path)
            logging.info(f"Archivo original eliminado: {file_path}")
        
        return True
    except Exception as e:
        logging.error(f"Error al hacer backup: {e}")
        return False

def process_data_content(content):
    """Procesa el contenido del archivo de datos"""
    # Verificar si es un JSON válido
    try:
        # Si comienza con '[', es un array de eventos
        if content.strip().startswith('['):
            events = json.loads(content)
            logging.info(f"Contenido JSON válido: {len(events)} eventos")
        else:
            # Si no, asumimos que es un solo evento
            event = json.loads(content)
            events = [event]
            logging.info("Contenido JSON válido: 1 evento")
        
        # Agregar metadatos de procesamiento a cada evento
        processed_events = []
        for event in events:
            # Agregar timestamp de procesamiento
            event["processed_timestamp"] = datetime.now().isoformat()
            processed_events.append(event)
        
        return processed_events, len(processed_events)
    
    except json.JSONDecodeError as e:
        logging.error(f"Error al decodificar JSON: {e}")
        if len(content) > 100:
            logging.error(f"Primeros 100 caracteres: {content[:100]}")
        else:
            logging.error(f"Contenido completo: {content}")
        return None, 0

def process_data_file(file_path):
    """Procesa un archivo de datos del mod"""
    logging.info(f"Procesando archivo: {file_path}")
    
    try:
        # Leer archivo
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
        
        # Verificar tamaño
        if not content:
            logging.warning(f"Archivo vacío: {file_path}")
            return None, 0
        
        file_size = os.path.getsize(file_path)
        logging.info(f"Tamaño del archivo: {file_size} bytes")
        logging.info(f"Primeros 100 caracteres: {content[:100]}")
        
        # Procesar contenido
        return process_data_content(content)
    
    except Exception as e:
        logging.error(f"Error al procesar archivo {file_path}: {e}")
        return None, 0

def process_all_files(found_files, db_file=DATABASE_FILE, backup=True, keep_originals=False):
    """Procesa todos los archivos encontrados"""
    # Cargar base de datos existente
    database = load_database(db_file)
    total_processed = 0
    
    for file_path, size in found_files:
        logging.info(f"Procesando {file_path} ({size} bytes)")
        
        # Procesar archivo
        events, count = process_data_file(file_path)
        
        if events and count > 0:
            # Añadir eventos a la base de datos
            existing_event_ids = {event.get("event_id") for event in database["events"]}
            new_events = []
            
            for event in events:
                # Verificar si el evento ya existe
                if "event_id" in event and event["event_id"] in existing_event_ids:
                    logging.debug(f"Evento ya existe: {event['event_id']}")
                else:
                    new_events.append(event)
                    if "event_id" in event:
                        existing_event_ids.add(event["event_id"])
            
            # Añadir nuevos eventos
            if new_events:
                database["events"].extend(new_events)
                logging.info(f"Añadidos {len(new_events)} eventos nuevos de {file_path}")
                total_processed += len(new_events)
            else:
                logging.info(f"No se encontraron eventos nuevos en {file_path}")
            
            # Hacer backup del archivo original
            if backup:
                backup_mod_data(file_path, keep_original=keep_originals)
        else:
            logging.warning(f"No se pudieron extraer eventos de {file_path}")
    
    # Guardar base de datos actualizada
    if total_processed > 0:
        save_database(database, db_file)
        logging.info(f"Total eventos procesados: {total_processed}")
    else:
        logging.info("No se procesaron nuevos eventos")
    
    return total_processed

def extract_data(backup=True, keep_originals=False, db_file=DATABASE_FILE, debug=False, force_processing=False, ignore_timestamp=False):
    """Función principal para extraer datos"""
    global check_game_running, check_file_timestamp
    
    # Configurar variables de control de verificación
    check_game_running = not force_processing
    check_file_timestamp = not ignore_timestamp
    
    # Configurar logging
    logger = setup_logging(debug=debug)
    logger.info("=== Iniciando extracción de datos ===")
    
    # Encontrar archivos
    found_files = find_all_possible_data_files()
    
    if not found_files:
        logger.warning("No se encontraron archivos de datos para procesar")
        return 0
    
    # Procesar archivos
    total_processed = process_all_files(
        found_files, 
        db_file=db_file, 
        backup=backup, 
        keep_originals=keep_originals
    )
    
    logger.info(f"=== Extracción completada: {total_processed} eventos procesados ===")
    return total_processed

if __name__ == "__main__":
    # Configurar los argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Extraer datos del mod DEM')
    parser.add_argument('--no-backup', action='store_true', help='No hacer backup de los archivos originales')
    parser.add_argument('--keep-originals', action='store_true', help='Mantener archivos originales después del procesamiento')
    parser.add_argument('--db', default=DATABASE_FILE, help=f'Archivo de base de datos (default: {DATABASE_FILE})')
    parser.add_argument('--debug', action='store_true', help='Activar mensajes de depuración')
    parser.add_argument('--force', action='store_true', help='Forzar procesamiento aunque el juego no esté en ejecución')
    parser.add_argument('--ignore-timestamp', action='store_true', help='Ignorar verificación de timestamp y procesar aunque no haya cambios')
    
    args = parser.parse_args()
    
    if args.force:
        print("AVISO: Se ha forzado el procesamiento aunque el juego no esté en ejecución.")
    
    if args.ignore_timestamp:
        print("AVISO: Se ignorará la verificación de timestamps, todos los archivos serán procesados.")
    
    # Ejecutar la extracción de datos
    extract_data(
        backup=not args.no_backup,
        keep_originals=args.keep_originals,
        db_file=args.db,
        debug=args.debug,
        force_processing=args.force,
        ignore_timestamp=args.ignore_timestamp
    ) 