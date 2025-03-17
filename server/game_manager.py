import os
import subprocess
import platform
import json
import logging

logger = logging.getLogger(__name__)

# Definir función para leer la ruta del juego desde config.json
def get_game_path():
    """
    Lee la ruta del juego desde los archivos de configuración.
    Primero intenta leer config.json, y si no está disponible,
    intenta leer el formato antiguo de config.txt.
    Retorna la ruta al ejecutable y la ruta a la carpeta del juego.
    """
    # Primero intentar con config.json
    config_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    
    if os.path.exists(config_json_path):
        try:
            with open(config_json_path, 'r') as f:
                config_data = json.load(f)
                
            # Verificar que existan las claves necesarias
            if 'game' in config_data and 'path' in config_data['game']:
                game_path = config_data['game']['path']
                executable = config_data['game'].get('executable')
                
                # Verificar que la ruta exista
                if not os.path.exists(game_path):
                    logger.error(f"La ruta del juego no existe: {game_path}")
                else:
                    # Si se especificó un ejecutable, construir la ruta completa
                    if executable:
                        executable_path = os.path.join(game_path, executable)
                        # Verificar si el ejecutable existe
                        if os.path.exists(executable_path):
                            logger.info(f"Usando ejecutable especificado en config.json: {executable_path}")
                            return executable_path, game_path
                        else:
                            logger.warning(f"Ejecutable especificado no encontrado: {executable_path}")
                    
                    # Si no se encontró un ejecutable específico, buscar en la carpeta
                    if os.path.isdir(game_path):
                        # Es un directorio, buscar el ejecutable
                        possible_executable = None
                        if platform.system() == 'Windows':
                            # Buscar archivos .exe en el directorio
                            for file in os.listdir(game_path):
                                if file.lower().endswith('.exe'):
                                    logger.debug(f"Encontrado ejecutable en carpeta: {file}")
                                    # Si encontramos el ejecutable específico, usarlo de inmediato
                                    if executable and file.lower() == executable.lower():
                                        full_path = os.path.join(game_path, file)
                                        logger.info(f"Usando ejecutable que coincide con config.json: {full_path}")
                                        return full_path, game_path
                                    # De lo contrario, guardamos el primer .exe como respaldo
                                    if not possible_executable:
                                        possible_executable = os.path.join(game_path, file)
                        else:
                            # En Linux/Mac, podemos buscar archivos ejecutables
                            for file in os.listdir(game_path):
                                file_path = os.path.join(game_path, file)
                                if os.access(file_path, os.X_OK) and os.path.isfile(file_path):
                                    logger.debug(f"Encontrado ejecutable en carpeta: {file}")
                                    possible_executable = file_path
                                    break
                        
                        if possible_executable:
                            logger.info(f"Usando ejecutable encontrado en carpeta: {possible_executable}")
                            return possible_executable, game_path
                        else:
                            logger.error(f"No se encontró ningún ejecutable en {game_path}")
                    else:
                        # Es un archivo, asumimos que es el ejecutable
                        logger.info(f"La ruta del juego es un archivo, asumiendo que es el ejecutable: {game_path}")
                        directory = os.path.dirname(game_path)
                        return game_path, directory
        except json.JSONDecodeError:
            logger.error("Error al decodificar el archivo config.json como JSON")
        except Exception as e:
            logger.error(f"Error al leer la configuración del juego desde config.json: {str(e)}")
    
    # Si llegamos aquí, es que no pudimos obtener la ruta desde config.json
    # Intentar con el formato antiguo de config.txt
    config_txt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.txt')
    
    if os.path.exists(config_txt_path):
        try:
            logger.info("Intentando leer configuración desde config.txt (formato antiguo)")
            game_path = None
            exe_name = None
            
            with open(config_txt_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GAME_PATH='):
                        game_path = line[len('GAME_PATH='):].strip()
                    elif line.startswith('GAME_EXE='):
                        exe_name = line[len('GAME_EXE='):].strip()
            
            if game_path:
                logger.info(f"Encontrada ruta del juego en config.txt: {game_path}")
                if not os.path.exists(game_path):
                    logger.error(f"La ruta del juego no existe: {game_path}")
                    return None, None
                
                # Si tenemos el nombre del ejecutable, construir la ruta completa
                if exe_name:
                    full_path = os.path.join(game_path, exe_name)
                    if os.path.exists(full_path):
                        logger.info(f"Usando ejecutable especificado en config.txt: {full_path}")
                        return full_path, game_path
                    else:
                        logger.warning(f"Ejecutable especificado no encontrado: {full_path}")
                
                # Intentar encontrar un ejecutable en la carpeta
                if os.path.isdir(game_path):
                    possible_executable = None
                    if platform.system() == 'Windows':
                        for file in os.listdir(game_path):
                            if file.lower().endswith('.exe'):
                                logger.debug(f"Encontrado ejecutable en carpeta: {file}")
                                possible_executable = os.path.join(game_path, file)
                                break
                    else:
                        for file in os.listdir(game_path):
                            file_path = os.path.join(game_path, file)
                            if os.access(file_path, os.X_OK) and os.path.isfile(file_path):
                                logger.debug(f"Encontrado ejecutable en carpeta: {file}")
                                possible_executable = file_path
                                break
                    
                    if possible_executable:
                        logger.info(f"Usando ejecutable encontrado en carpeta: {possible_executable}")
                        return possible_executable, game_path
                    else:
                        logger.error(f"No se encontró ningún ejecutable en {game_path}")
                        return None, game_path
                else:
                    # Es un archivo, asumimos que es el ejecutable
                    logger.info(f"La ruta del juego es un archivo, asumiendo que es el ejecutable: {game_path}")
                    directory = os.path.dirname(game_path)
                    return game_path, directory
        except Exception as e:
            logger.error(f"Error al leer la configuración del juego desde config.txt: {str(e)}")
    
    # Si llegamos aquí, no pudimos obtener la ruta del juego
    logger.error("No se pudo determinar la ruta del juego. Verifique su configuración.")
    return None, None

def start_game():
    """
    Inicia el juego utilizando la ruta especificada en config.json.
    Retorna un diccionario con el resultado de la operación.
    """
    game_exe, game_dir = get_game_path()
    
    if not game_exe:
        if not game_dir:
            return {
                'success': False,
                'error': 'No se pudo encontrar la ruta del juego. Verifique su configuración en config.json'
            }
        else:
            return {
                'success': False,
                'error': f'No se encontró un ejecutable en la carpeta del juego: {game_dir}. Verifique la configuración en config.json'
            }
    
    if not os.path.exists(game_exe):
        return {
            'success': False,
            'error': f'El ejecutable del juego no existe: {game_exe}. Verifique la configuración en config.json'
        }
    
    try:
        logger.info(f"Intentando iniciar el juego: {game_exe}")
        
        # Iniciar el juego como un proceso separado
        if platform.system() == 'Windows':
            subprocess.Popen([game_exe], shell=True)
        else:
            subprocess.Popen([game_exe], shell=False)
            
        return {
            'success': True,
            'message': f'Juego iniciado: {game_exe}'
        }
    except Exception as e:
        logger.error(f"Error al iniciar el juego: {str(e)}")
        return {
            'success': False,
            'error': f'Error al iniciar el juego: {str(e)}'
        }

def open_game_folder():
    """
    Abre la carpeta del juego en el explorador de archivos.
    Retorna un diccionario con el resultado de la operación.
    """
    _, game_dir = get_game_path()
    
    if not game_dir:
        return {
            'success': False,
            'error': 'No se pudo encontrar la carpeta del juego. Verifique su configuración en config.json'
        }
    
    if not os.path.exists(game_dir):
        return {
            'success': False,
            'error': f'La carpeta del juego no existe: {game_dir}. Verifique la configuración en config.json'
        }
    
    try:
        logger.info(f"Intentando abrir la carpeta del juego: {game_dir}")
        
        # Abrir la carpeta del juego según el sistema operativo
        if platform.system() == 'Windows':
            os.startfile(game_dir)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', game_dir])
        else:  # Linux
            subprocess.Popen(['xdg-open', game_dir])
            
        return {
            'success': True,
            'message': f'Carpeta abierta: {game_dir}'
        }
    except Exception as e:
        logger.error(f"Error al abrir la carpeta del juego: {str(e)}")
        return {
            'success': False,
            'error': f'Error al abrir la carpeta del juego: {str(e)}'
        }

def is_game_running():
    """
    Verifica si el juego está en ejecución.
    Retorna una tupla (bool, str) donde bool indica si está en ejecución
    y str es el nombre del proceso.
    """
    # Esta implementación es básica y debería adaptarse a cada juego específico
    game_exe, _ = get_game_path()
    
    if not game_exe:
        logger.warning("No se pudo obtener la ruta del ejecutable para verificar si el juego está en ejecución")
        return False, None
        
    exe_name = os.path.basename(game_exe)
    logger.debug(f"Verificando si el juego está en ejecución: {exe_name}")
    
    try:
        if platform.system() == 'Windows':
            # Usar tasklist en Windows
            cmd = f'tasklist /FI "IMAGENAME eq {exe_name}"'
            logger.debug(f"Ejecutando comando: {cmd}")
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            
            is_running = exe_name.lower() in output.lower()
            logger.debug(f"Resultado de la verificación: {'en ejecución' if is_running else 'no detectado'}")
            return is_running, exe_name
        else:
            # Usar ps en sistemas Unix
            cmd = 'ps -A'
            logger.debug(f"Ejecutando comando: {cmd}")
            output = subprocess.check_output(['ps', '-A']).decode('utf-8')
            
            is_running = exe_name in output
            logger.debug(f"Resultado de la verificación: {'en ejecución' if is_running else 'no detectado'}")
            return is_running, exe_name
    except Exception as e:
        logger.error(f"Error al verificar si el juego está en ejecución: {str(e)}")
        return False, None 