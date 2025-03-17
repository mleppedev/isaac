#!/usr/bin/env python
"""
Script simple para encontrar y mostrar los datos del mod DEM
buscando específicamente en la ubicación correcta.
"""

import os
import sys
import json
import glob
import logging
from datetime import datetime

def setup_logging():
    """Configurar logging básico"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger()

def find_isaac_data_file():
    """Busca específicamente el archivo de datos de DEM en las ubicaciones correctas"""
    # Definir posibles ubicaciones, priorizando la ubicación mencionada en los logs
    possible_paths = [
        # Windows - Ruta principal (según logs)
        os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance+", "Data Event Manager.dat"),
        # Windows - Comprobando variantes de la ruta principal
        os.path.join(os.path.expanduser("~"), "Documentos", "My Games", "Binding of Isaac Repentance+", "Data Event Manager.dat"),
        os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance Plus", "Data Event Manager.dat"),
        os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance+", "data", "Data Event Manager.dat"),
        os.path.join("C:", "Users", os.getlogin(), "Documents", "My Games", "Binding of Isaac Repentance+", "Data Event Manager.dat"),
        # Windows - Ruta alternativa 
        os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Repentance Mods", "Data Event Manager.dat"),
        # Windows - OneDrive (algunos usuarios usan OneDrive para Documents)
        os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "My Games", "Binding of Isaac Repentance+", "Data Event Manager.dat"),
        # Steam Cloud
        os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth", "data", "Data Event Manager.dat"),
        # Ruta mod directa
        os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth", "mods", "DEM", "Data Event Manager.dat"),
    ]
    
    # Imprimir información del sistema para depuración
    logging.info(f"Usuario: {os.getlogin()}")
    logging.info(f"Directorio de usuario: {os.path.expanduser('~')}")
    
    # Comprobar si existe la carpeta My Games
    my_games_dir = os.path.join(os.path.expanduser("~"), "Documents", "My Games")
    if os.path.exists(my_games_dir):
        logging.info(f"Carpeta 'My Games' encontrada en: {my_games_dir}")
        my_games_contents = os.listdir(my_games_dir)
        logging.info(f"Contenido de 'My Games': {my_games_contents}")
        
        # Buscar carpetas específicas de Isaac
        isaac_folders = [folder for folder in my_games_contents if "isaac" in folder.lower() or "rebirth" in folder.lower()]
        if isaac_folders:
            logging.info(f"Carpetas de Isaac encontradas: {isaac_folders}")
            for folder in isaac_folders:
                isaac_path = os.path.join(my_games_dir, folder)
                possible_paths.append(os.path.join(isaac_path, "Data Event Manager.dat"))
    
    # Revisar cada ruta
    for path in possible_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size > 0:  # Asegurarse que no esté vacío
                logging.info(f"¡Encontrado archivo de datos! Ruta: {path}")
                logging.info(f"Tamaño: {size} bytes")
                return path
        else:
            logging.info(f"No existe: {path}")
    
    # Buscar archivos .dat en documentos de forma recursiva
    logging.info("Buscando archivos .dat en Documents...")
    docs_dir = os.path.join(os.path.expanduser("~"), "Documents")
    if os.path.exists(docs_dir):
        dat_files = []
        for root, dirs, files in os.walk(docs_dir):
            for file in files:
                if file.endswith(".dat") and len(dat_files) < 20:  # Limitar a 20 archivos para no sobrecargar el log
                    dat_path = os.path.join(root, file)
                    dat_files.append((dat_path, os.path.getsize(dat_path)))
        
        # Ordenar por tamaño e imprimir los 5 más grandes
        dat_files.sort(key=lambda x: x[1], reverse=True)
        logging.info(f"Archivos .dat encontrados en Documents (mostrando los 5 más grandes):")
        for path, size in dat_files[:5]:
            logging.info(f"  {path} - {size} bytes")
    
    # Buscar también en la carpeta del juego
    game_dirs = [
        os.path.join("D:", "SteamLibrary", "steamapps", "common", "The Binding of Isaac Rebirth"),
        os.path.join("C:", "Program Files (x86)", "Steam", "steamapps", "common", "The Binding of Isaac Rebirth"),
        os.path.join("C:", "Program Files", "Steam", "steamapps", "common", "The Binding of Isaac Rebirth"),
    ]
    
    for game_dir in game_dirs:
        if os.path.exists(game_dir):
            logging.info(f"Carpeta del juego encontrada: {game_dir}")
            # Buscar el archivo de datos
            for root, dirs, files in os.walk(game_dir):
                if "Data Event Manager.dat" in files:
                    path = os.path.join(root, "Data Event Manager.dat")
                    if os.path.getsize(path) > 0:
                        logging.info(f"¡Encontrado archivo de datos en carpeta del juego! {path}")
                        return path
            
            # Buscar archivos .dat recientes
            dat_files = []
            for root, dirs, files in os.walk(game_dir):
                for file in files:
                    if file.endswith(".dat"):
                        full_path = os.path.join(root, file)
                        # Obtener fecha de modificación
                        try:
                            mtime = os.path.getmtime(full_path)
                            dat_files.append((full_path, os.path.getsize(full_path), mtime))
                        except:
                            pass
            
            # Ordenar por fecha (más recientes primero)
            dat_files.sort(key=lambda x: x[2], reverse=True)
            logging.info(f"Archivos .dat recientes en carpeta del juego (mostrando los 3 más recientes):")
            for path, size, mtime in dat_files[:3]:
                mod_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                logging.info(f"  {path} - {size} bytes - Modificado: {mod_time}")
    
    # Buscar en el directorio actual por si acaso
    current_dir_dat = glob.glob("*.dat")
    if current_dir_dat:
        logging.info(f"Archivos .dat en el directorio actual: {current_dir_dat}")
        for file in current_dir_dat:
            if "data" in file.lower() or "event" in file.lower() or "dem" in file.lower():
                if os.path.getsize(file) > 0:
                    logging.info(f"Posible archivo de datos en directorio actual: {file}")
                    return file
    
    return None

def convert_isaac_timestamp(timestamp):
    """Convierte el timestamp basado en frames a un formato más legible"""
    # Aproximadamente 30 FPS en el juego
    seconds = timestamp / 30
    # Calcular minutos y segundos
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    # Devolver formato legible
    return f"{minutes}m {secs}s (frame {timestamp})"

def read_and_parse_data(file_path):
    """Lee y muestra el contenido del archivo de datos"""
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read().strip()
        
        if not content:
            logging.warning(f"Archivo vacío: {file_path}")
            return None
        
        # Imprimir información de tamaño y primeros bytes
        logging.info(f"Tamaño del contenido: {len(content)} bytes")
        logging.info(f"Primeros 50 caracteres: {content[:50]}")
        
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
            logging.warning(f"Contenido no reconocido: {content[:100]}...")
            
            # Intentar reparar JSON por si acaso
            if '[' in content and ']' in content:
                try:
                    json_str = content[content.find('['):content.rfind(']')+1]
                    logging.info("Intentando reparar JSON...")
                    data = json.loads(json_str)
                    logging.info("¡JSON reparado exitosamente!")
                    return data
                except:
                    logging.error("No se pudo reparar el JSON")
            
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
    logger.info("DEM - Buscador de Datos")
    
    # Mostrar información de sistema
    logger.info(f"Directorio actual: {os.getcwd()}")
    
    # Buscar el archivo de datos
    data_file = find_isaac_data_file()
    
    if not data_file:
        logger.error("No se encontró el archivo de datos de DEM en ninguna ubicación conocida.")
        logger.info("Asegúrate de ejecutar el juego con el mod activado antes de usar este script.")
        logger.info("Recuerda que el archivo debe estar en: Documents/My Games/Binding of Isaac Repentance+/Data Event Manager.dat")
        
        # Ofrecer un archivo manual
        logger.info("¿Quieres especificar la ruta manualmente? (s/n):")
        answer = input().lower()
        if answer == 's' or answer == 'si':
            logger.info("Introduce la ruta completa al archivo:")
            data_file = input().strip()
            if not os.path.exists(data_file):
                logger.error(f"El archivo no existe: {data_file}")
                return 1
        else:
            return 1
    
    # Leer y analizar el archivo
    events = read_and_parse_data(data_file)
    
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
    
    # Preguntar al usuario si quiere copiar los datos a demdata.json
    if events:
        logger.info("¿Quieres guardar los datos en 'demdata.json'? (s/n):")
        answer = input().lower()
        if answer == 's' or answer == 'si':
            try:
                with open('demdata.json', 'w') as f:
                    json.dump(events, f, indent=2)
                logger.info(f"Datos guardados en demdata.json ({os.path.join(os.getcwd(), 'demdata.json')})")
            except Exception as e:
                logger.error(f"Error al guardar el archivo: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 