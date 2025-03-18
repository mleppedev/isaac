#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
control_player.py - Herramienta para enviar comandos al mod DEM

Este script permite enviar comandos que controlen al personaje desde el servidor
web al juego. Utiliza el sistema de archivos para comunicarse, escribiendo
comandos en un archivo que el mod lee y procesa.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# Intentar importar tqdm para mostrar barras de progreso si está disponible
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Nota: Instala 'tqdm' para ver barras de progreso")

# Configuración predeterminada
DEFAULT_GAME_PATH = r"D:\SteamLibrary\steamapps\common\The Binding of Isaac Rebirth"
DEFAULT_MOD_NAME = "DEM"

def get_mod_data_path(game_path=None, mod_name=None):
    """Determina la ruta del archivo de datos del mod."""
    if not game_path:
        # Leer del archivo config.txt si existe
        config_path = Path("../config.txt")
        if config_path.exists():
            with open(config_path, "r") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        if key.strip() == "GAME_PATH":
                            game_path = value.strip()
                        elif key.strip() == "MOD_NAME":
                            mod_name = value.strip()
    
    if not game_path:
        game_path = DEFAULT_GAME_PATH
    
    if not mod_name:
        mod_name = DEFAULT_MOD_NAME
    
    # Determinar ruta basada en plataforma
    if sys.platform == "win32":
        # Windows
        mod_data_dir = Path(os.path.expanduser("~/Documents/My Games/Binding of Isaac Repentance+/data"))
    else:
        # Linux/Mac
        if sys.platform == "darwin":
            # macOS
            mod_data_dir = Path(os.path.expanduser("~/Library/Application Support/Binding of Isaac Repentance+/data"))
        else:
            # Linux
            mod_data_dir = Path(os.path.expanduser("~/.local/share/binding-of-isaac-repentance+/data"))
    
    return mod_data_dir / f"{mod_name}.dat"

def send_command(commands, game_path=None, mod_name=None, wait_for_result=False, timeout=5):
    """
    Envía comandos al juego escribiendo en el archivo de datos del mod.
    
    Args:
        commands: Lista de comandos o comando único a enviar
        game_path: Ruta del juego (opcional)
        mod_name: Nombre del mod (opcional)
        wait_for_result: Si True, espera y lee la respuesta
        timeout: Tiempo máximo de espera en segundos
    
    Returns:
        Dict con el resultado si wait_for_result es True, None en caso contrario
    """
    # Convertir un solo comando en lista
    if not isinstance(commands, list):
        commands = [commands]
    
    # Asignar IDs a los comandos si no los tienen
    for i, cmd in enumerate(commands):
        if "id" not in cmd:
            cmd["id"] = i + 1
    
    # Obtener ruta del archivo de datos
    mod_data_path = get_mod_data_path(game_path, mod_name)
    
    # Crear el directorio si no existe
    mod_data_dir = os.path.dirname(mod_data_path)
    if not os.path.exists(mod_data_dir):
        try:
            os.makedirs(mod_data_dir, exist_ok=True)
            print(f"Directorio creado: {mod_data_dir}")
        except Exception as e:
            print(f"Error al crear directorio: {str(e)}")
            return {"success": False, "error": f"Error al crear directorio: {str(e)}"}
    
    # Escribir comandos
    try:
        with open(mod_data_path, "w") as f:
            json.dump(commands, f)
        
        print(f"Comandos enviados a {mod_data_path}")
    except Exception as e:
        print(f"Error al escribir el archivo: {str(e)}")
        return {"success": False, "error": str(e)}
    
    # Esperar respuesta si es necesario
    if wait_for_result:
        if TQDM_AVAILABLE:
            # Usar barra de progreso si está disponible
            for _ in tqdm(range(timeout * 10), desc="Esperando respuesta", unit="0.1s"):
                time.sleep(0.1)
                try:
                    with open(mod_data_path, "r") as f:
                        response = f.read().strip()
                        if response:
                            try:
                                result = json.loads(response)
                                if isinstance(result, list) and len(result) == len(commands):
                                    return result
                            except json.JSONDecodeError:
                                pass
                except Exception:
                    pass
        else:
            # Versión simple sin barra de progreso
            end_time = time.time() + timeout
            while time.time() < end_time:
                time.sleep(0.1)
                try:
                    with open(mod_data_path, "r") as f:
                        response = f.read().strip()
                        if response:
                            try:
                                result = json.loads(response)
                                if isinstance(result, list) and len(result) == len(commands):
                                    return result
                            except json.JSONDecodeError:
                                pass
                except Exception:
                    pass
        
        print("No se recibió respuesta en el tiempo establecido")
        return None
    
    return {"success": True}

def parse_args():
    """Procesa los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Envía comandos al mod DEM para controlar al personaje")
    
    # Subcomandos para diferentes tipos de acciones
    subparsers = parser.add_subparsers(dest='command', help='Tipo de comando')
    
    # Comando de movimiento
    move_parser = subparsers.add_parser('move', help='Mover al personaje')
    move_parser.add_argument('direction', choices=['up', 'down', 'left', 'right'], 
                             help='Dirección de movimiento')
    move_parser.add_argument('--value', type=float, default=1.0, 
                             help='Valor de la acción (0.0-1.0)')
    
    # Comando de disparo
    shoot_parser = subparsers.add_parser('shoot', help='Disparar')
    shoot_parser.add_argument('direction', choices=['up', 'down', 'left', 'right'], 
                              help='Dirección de disparo')
    shoot_parser.add_argument('--value', type=float, default=1.0, 
                              help='Valor de la acción (0.0-1.0)')
    
    # Comando para alternar IA
    toggle_parser = subparsers.add_parser('toggle_ai', help='Alternar modo IA')
    
    # Comando para limpiar entradas
    clear_parser = subparsers.add_parser('clear', help='Limpiar todas las entradas')
    
    # Comando de secuencia
    sequence_parser = subparsers.add_parser('sequence', help='Ejecutar una secuencia de comandos')
    sequence_parser.add_argument('--file', type=str, required=True, 
                                 help='Archivo JSON con la secuencia de comandos')
    
    # Opciones comunes
    parser.add_argument('--game-path', type=str, 
                        help=f'Ruta del juego (predeterminado: {DEFAULT_GAME_PATH})')
    parser.add_argument('--mod-name', type=str, default=DEFAULT_MOD_NAME,
                        help=f'Nombre del mod (predeterminado: {DEFAULT_MOD_NAME})')
    parser.add_argument('--wait', action='store_true',
                        help='Esperar respuesta del juego')
    
    return parser.parse_args()

def main():
    """Función principal."""
    args = parse_args()
    
    # Crear comando según el tipo
    if args.command == 'move':
        cmd = {
            "type": "movement",
            "direction": args.direction,
            "value": max(0.0, min(1.0, args.value))
        }
    elif args.command == 'shoot':
        cmd = {
            "type": "shooting",
            "direction": args.direction,
            "value": max(0.0, min(1.0, args.value))
        }
    elif args.command == 'toggle_ai':
        cmd = {"type": "toggle_ai"}
    elif args.command == 'clear':
        cmd = {"type": "clear"}
    elif args.command == 'sequence':
        # Cargar secuencia desde archivo
        try:
            with open(args.file, 'r') as f:
                commands = json.load(f)
            
            if not isinstance(commands, list):
                commands = [commands]
                
            result = send_command(commands, args.game_path, args.mod_name, args.wait)
            
            if result:
                print(f"Resultado: {json.dumps(result, indent=2)}")
            
            return
        except Exception as e:
            print(f"Error al cargar secuencia: {str(e)}")
            return
    else:
        print("Comando no válido. Use --help para ver las opciones disponibles.")
        return
    
    # Enviar comando
    result = send_command(cmd, args.game_path, args.mod_name, args.wait)
    
    # Mostrar resultado si se recibió
    if result:
        print(f"Resultado: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    main() 