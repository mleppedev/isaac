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
REAL_DATA_PATH = os.path.join(ISAAC_STEAM_DIR, "data", "", "save1.dat")

# Nombre del archivo de datos de mod (para las rutas legacy)
MOD_DATA_FILE = "Data Event Manager.dat"

PROCESSED_DIR = "processed"
DATABASE_FILE = "dem_database.json"
LOG_FILE = "extract_data.log"

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
    possible_paths = []
    found_files = []
    
    # 1. Comprobar la ruta principal en Documentos
    path1 = os.path.join(ISAAC_MODS_DATA_DIR, MOD_DATA_FILE)
    possible_paths.append(("Doc principal", path1))
    
    # 2. Comprobar ruta alternativa en Documentos
    path2 = os.path.join(ISAAC_MODS_DATA_DIR_ALT, MOD_DATA_FILE)
    possible_paths.append(("Doc alternativo", path2))
    
    # 3. Comprobar en directorio data de Steam
    path3 = os.path.join(ISAAC_STEAM_DIR, "data", MOD_DATA_FILE)
    possible_paths.append(("Steam data", path3))
    
    # 4. Comprobar en directorio DEM
    path4 = os.path.join(MOD_DIR, MOD_DATA_FILE)
    possible_paths.append(("Directorio mod", path4))
    
    # 5. Comprobar en carpeta de datos del mod
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
                        size = os.path.getsize(full_path)
                        if size > 0:  # Solo incluir archivos no vacíos
                            found_files.append((full_path, size))
                            logging.info(f"Encontrado archivo en {desc}: {filename} ({size} bytes)")
            else:
                # Es un archivo específico
                size = os.path.getsize(path)
                if size > 0:  # Solo incluir archivos no vacíos
                    found_files.append((path, size))
                    logging.info(f"Encontrado archivo en {desc}: {os.path.basename(path)} ({size} bytes)")
    
    # Buscar en directorios adicionales (búsqueda recursiva, pero limitada)
    additional_dirs = [
        os.path.join(os.path.expanduser("~"), "Documents", "My Games"),
        ISAAC_STEAM_DIR
    ]
    
    for base_dir in additional_dirs:
        if os.path.exists(base_dir):
            logging.debug(f"Buscando en directorio adicional: {base_dir}")
            try:
                for root, dirs, files in os.walk(base_dir, topdown=True):
                    # Limitar profundidad para evitar búsquedas lentas
                    if root.count(os.sep) - base_dir.count(os.sep) > 3:
                        continue
                        
                    for filename in files:
                        if filename == MOD_DATA_FILE or (filename.endswith(".dat") and "DEM" in filename):
                            full_path = os.path.join(root, filename)
                            if os.path.exists(full_path):
                                size = os.path.getsize(full_path)
                                if size > 0 and full_path not in [f[0] for f in found_files]:
                                    found_files.append((full_path, size))
                                    logging.info(f"Encontrado archivo adicional: {full_path} ({size} bytes)")
            except Exception as e:
                logging.error(f"Error al buscar en {base_dir}: {e}")
    
    # Devolver los archivos encontrados ordenados por tamaño
    return sorted(found_files, key=lambda x: x[1], reverse=True)

def read_mod_data():
    """Lee el archivo de datos guardado por Isaac.SaveModData"""
    # Buscar todos los posibles archivos
    found_files = find_all_possible_data_files()
    
    if found_files:
        # Usar el archivo más grande encontrado
        largest_file, size = found_files[0]
        logging.info(f"Usando el archivo más grande: {largest_file} ({size} bytes)")
        
        try:
            with open(largest_file, 'r', errors='ignore') as f:
                data = f.read().strip()
                return data
        except Exception as e:
            logging.error(f"Error al leer el archivo {largest_file}: {e}")
            return None
    
    # Si no se encontraron archivos, intentar leer el log para obtener pistas
    log_paths = [
        os.path.join(ISAAC_MODS_DATA_DIR, "log.txt"),
        os.path.join(ISAAC_STEAM_DIR, "log.txt")
    ]
    
    for log_path in log_paths:
        if os.path.exists(log_path):
            logging.info(f"Revisando log en: {log_path}")
            try:
                with open(log_path, 'r', errors='ignore') as f:
                    lines = f.readlines()
                    dem_lines = [line for line in lines[-200:] if "DEM:" in line]
                    save_lines = [line for line in dem_lines if "guardado" in line or "Tamaño" in line]
                    
                    if save_lines:
                        logging.info("Información sobre guardado en el log:")
                        for line in save_lines:
                            logging.info(f"  {line.strip()}")
            except Exception as e:
                logging.error(f"Error al leer log: {e}")
    
    logging.warning("No se encontraron archivos de datos del mod")
    return None

def find_data_files(data_dir):
    """Encontrar todos los archivos de datos generados por el mod"""
    # Primero intentamos leer desde el archivo de datos del mod
    mod_data = read_mod_data()
    if mod_data:
        logging.info("Se encontraron datos del mod")
        return [mod_data]  # Devolvemos el contenido como un solo elemento
    
    # Si no hay datos del mod, buscamos en los directorios especificados
    logging.info(f"Buscando archivos JSON en: {data_dir}")
    pattern = os.path.join(data_dir, "*.json")
    files = glob.glob(pattern)
    
    if not files:
        # Intentar en todos los directorios posibles
        alt_dirs = [
            os.path.join(ISAAC_MODS_DATA_DIR, "mods", "DEM"),
            os.path.join(ISAAC_STEAM_DIR, "mods", "DEM"),
            os.path.join(os.getcwd(), "DEM_Data")
        ]
        
        for alt_dir in alt_dirs:
            if os.path.exists(alt_dir):
                logging.info(f"Buscando archivos JSON en carpeta alternativa: {alt_dir}")
                pattern = os.path.join(alt_dir, "*.json")
                files = glob.glob(pattern)
                if files:
                    break
    
    return files

def convert_isaac_timestamp(timestamp):
    """Convierte el timestamp basado en frames a un formato más legible"""
    # Aproximadamente 30 FPS en el juego
    seconds = timestamp / 30
    # Usamos la hora actual como base y ajustamos los segundos
    now = datetime.now()
    # Crear una marca de tiempo que tenga sentido
    processed_time = now.replace(
        hour=0, 
        minute=0, 
        second=int(seconds % 60), 
        microsecond=int((seconds * 1000000) % 1000000)
    )
    return processed_time.isoformat()

def process_data_content(content, source="mod_data"):
    """Procesar el contenido de datos"""
    try:
        if not content:
            logging.warning(f"Contenido vacío: {source}")
            return None
            
        try:
            # Verificar si comienza con [ (array)
            if content.strip().startswith('['):
                # Es un array de eventos
                logging.info("El contenido es un array de eventos JSON")
                events_array = json.loads(content)
                processed_events = []
                
                for i, event_data in enumerate(events_array):
                    # Agregar metadatos de procesamiento a cada evento
                    if "timestamp" in event_data:
                        # Agregar timestamp_original y convertir el timestamp basado en frames
                        event_data["timestamp_original"] = event_data["timestamp"]
                        event_data["timestamp_processed"] = convert_isaac_timestamp(event_data["timestamp"])
                    
                    event_data["_processing"] = {
                        "source": source,
                        "processed_at": datetime.now().isoformat(),
                        "batch_index": i,
                        "batch_size": len(events_array)
                    }
                    processed_events.append(event_data)
                
                logging.info(f"Procesados {len(processed_events)} eventos del array")
                return processed_events
            else:
                # Es un único evento JSON
                data = json.loads(content)
                
                # Convertir timestamp basado en frames si existe
                if "timestamp" in data:
                    data["timestamp_original"] = data["timestamp"]
                    data["timestamp_processed"] = convert_isaac_timestamp(data["timestamp"])
                
                # Agregar metadatos de procesamiento
                data["_processing"] = {
                    "source": source,
                    "processed_at": datetime.now().isoformat()
                }
                
                return [data]  # Devolver como lista para unificar procesamiento
                
        except json.JSONDecodeError as e:
            logging.error(f"Error de formato JSON en {source}: {e}")
            logging.debug(f"Contenido problemático: {content[:200]}...")
            return None
    
    except Exception as e:
        logging.error(f"Error al procesar contenido {source}: {e}")
        return None

def process_data_file(file_path_or_content):
    """Procesar un archivo de datos individual o contenido directo"""
    # Si es un string que parece ser un JSON, lo procesamos directamente
    if isinstance(file_path_or_content, str) and (file_path_or_content.strip().startswith('{') or file_path_or_content.strip().startswith('[')):
        return process_data_content(file_path_or_content)
    
    # Si es una ruta de archivo, leemos el archivo
    try:
        with open(file_path_or_content, 'r', errors='ignore') as f:
            content = f.read().strip()
        return process_data_content(content, os.path.basename(file_path_or_content))
    except Exception as e:
        logging.error(f"Error al procesar archivo {file_path_or_content}: {e}")
        return None

def backup_mod_data(keep_original=False):
    """Hacer copia de seguridad del archivo de datos del mod"""
    try:
        # Buscar todos los posibles archivos
        found_files = find_all_possible_data_files()
        
        if not found_files:
            logging.warning("No se encontraron archivos para hacer backup")
            return None
        
        # Usar el archivo más grande encontrado
        largest_file, size = found_files[0]
        
        backup_dir = os.path.join(os.path.dirname(largest_file), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"{timestamp}_{os.path.basename(largest_file)}")
        
        shutil.copy2(largest_file, backup_file)
        logging.info(f"Copia de seguridad creada: {backup_file}")
        
        # Borrar o vaciar el archivo original para evitar duplicados
        if not keep_original:
            with open(largest_file, 'w') as f:
                f.write("")
            
            logging.info(f"Archivo de datos del mod limpiado: {largest_file}")
        else:
            logging.info(f"Se mantiene el archivo original: {largest_file}")
            
        return backup_file
    except Exception as e:
        logging.error(f"Error al hacer copia de seguridad: {e}")
        return None

def move_to_processed(file_path, processed_dir):
    """Mover un archivo procesado a la carpeta de procesados"""
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
        
    base_name = os.path.basename(file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{timestamp}_{base_name}"
    dest_path = os.path.join(processed_dir, new_name)
    
    try:
        shutil.move(file_path, dest_path)
        logging.debug(f"Archivo movido a: {dest_path}")
        return True
    except Exception as e:
        logging.error(f"Error al mover archivo: {e}")
        return False

def extract_data(data_dir, db_file, keep_files=False):
    """Procesar todos los archivos de datos y actualizar la base de datos"""
    # Cargar base de datos existente
    database = load_database(db_file)
    initial_event_count = len(database["events"])
    
    # Encontrar archivos de datos
    data_files = find_data_files(data_dir)
    
    if isinstance(data_files, list) and len(data_files) == 1 and isinstance(data_files[0], str) and (data_files[0].strip().startswith('{') or data_files[0].strip().startswith('[')):
        # Es contenido directo del archivo de SaveModData
        logging.info("Procesando datos del archivo de mod")
        data_list = process_data_file(data_files[0])
        processed_count = 0
        
        if data_list:
            # Añadimos todos los eventos procesados a la base de datos
            for data in data_list:
                database["events"].append(data)
                processed_count += 1
            
            # Hacer backup del archivo de mod
            backup_mod_data(keep_files)
    else:
        # Son archivos normales
        logging.info(f"Encontrados {len(data_files)} archivos de datos en {data_dir}")
        
        # Procesar cada archivo
        processed_count = 0
        processed_dir = os.path.join(data_dir, PROCESSED_DIR)
        
        for file_path in data_files:
            data_list = process_data_file(file_path)
            
            if data_list:
                # Añadir cada evento a la base de datos
                for data in data_list:
                    database["events"].append(data)
                    processed_count += 1
                
                # Mover a procesados o eliminar
                if keep_files:
                    move_to_processed(file_path, processed_dir)
                else:
                    os.remove(file_path)
                    logging.debug(f"Archivo eliminado: {file_path}")
    
    # Guardar la base de datos actualizada
    if processed_count > 0:
        save_database(database, db_file)
        logging.info(f"Procesados {processed_count} eventos. Total eventos: {len(database['events'])}")
    else:
        logging.info("No se procesaron nuevos archivos")
    
    return {
        "initial_count": initial_event_count,
        "processed": processed_count,
        "current_count": len(database["events"])
    }

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Extraer datos del mod DEM")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Directorio de datos del mod")
    parser.add_argument("--db-file", default=DATABASE_FILE, help="Archivo de base de datos")
    parser.add_argument("--keep-files", action="store_true", help="Mantener archivos procesados")
    parser.add_argument("--debug", action="store_true", help="Activar modo debug")
    args = parser.parse_args()
    
    # Configurar logging
    logger = setup_logging(debug=args.debug)
    
    logger.info("=== DEM Data Extractor ===")
    logger.info(f"Directorio actual: {os.getcwd()}")
    logger.info(f"Directorio de datos principal: {ISAAC_MODS_DATA_DIR}")
    logger.info(f"Directorio de datos alternativo: {ISAAC_MODS_DATA_DIR_ALT}")
    logger.info(f"Directorio de Steam: {ISAAC_STEAM_DIR}")
    logger.info(f"Directorio del mod: {MOD_DIR}")
    logger.info(f"Directorio de datos específico: {args.data_dir}")
    logger.info(f"Archivo de base de datos: {args.db_file}")
    
    # Verificar rutas principales
    for path, label in [
        (ISAAC_MODS_DATA_DIR, "Docs principal"),
        (ISAAC_MODS_DATA_DIR_ALT, "Docs alternativo"),
        (ISAAC_STEAM_DIR, "Steam"),
        (MOD_DIR, "Directorio mod"),
        (args.data_dir, "Directorio datos")
    ]:
        if os.path.exists(path):
            logger.info(f"✓ {label} existe: {path}")
        else:
            logger.warning(f"✕ {label} NO existe: {path}")
    
    # Extraer datos
    result = extract_data(args.data_dir, args.db_file, args.keep_files)
    
    logger.info(f"=== Extracción completada: {result['processed']} eventos procesados ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 