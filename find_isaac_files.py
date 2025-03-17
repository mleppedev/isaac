#!/usr/bin/env python
"""
Script para buscar archivos .dat relacionados con Isaac o DEM en el sistema
"""

import os
import glob
import time
from datetime import datetime

def main():
    print("Buscando archivos de datos de Isaac o DEM...")
    
    # Rutas a buscar
    search_paths = [
        os.path.expanduser("~\\Documents"),
        os.path.expanduser("~\\Documents\\My Games"),
        "D:\\SteamLibrary\\steamapps\\common\\The Binding of Isaac Rebirth",
        "C:\\Program Files (x86)\\Steam\\steamapps\\common\\The Binding of Isaac Rebirth",
        os.path.expanduser("~\\AppData\\Roaming\\Binding of Isaac"),
        os.path.expanduser("~\\AppData\\Local\\Binding of Isaac"),
    ]
    
    # Archivos más recientes, ordenados por fecha
    recent_files = []
    
    for base_path in search_paths:
        if not os.path.exists(base_path):
            print(f"La ruta {base_path} no existe")
            continue
            
        print(f"\nBuscando en: {base_path}")
        
        # Buscar archivos .dat recursivamente
        for root, dirs, files in os.walk(base_path):
            # Filtrar solo los archivos .dat
            dat_files = [f for f in files if f.endswith('.dat')]
            
            if dat_files:
                for dat_file in dat_files:
                    full_path = os.path.join(root, dat_file)
                    try:
                        # Obtener tamaño y fecha de modificación
                        file_size = os.path.getsize(full_path)
                        mod_time = os.path.getmtime(full_path)
                        mod_date = datetime.fromtimestamp(mod_time)
                        
                        # Solo archivos modificados en los últimos 7 días
                        if time.time() - mod_time < 7 * 24 * 60 * 60:
                            recent_files.append((full_path, file_size, mod_date))
                            
                            # Si el archivo tiene "DEM" o "Event" en el nombre, mostrarlo de inmediato
                            if "event" in dat_file.lower() or "dem" in dat_file.lower() or "data event" in dat_file.lower():
                                print(f"Posible archivo DEM: {full_path}")
                                print(f"  Tamaño: {file_size} bytes")
                                print(f"  Modificado: {mod_date}")
                                
                                # Si es pequeño, mostrar los primeros bytes
                                if file_size < 10000:
                                    try:
                                        with open(full_path, 'r', errors='ignore') as f:
                                            content = f.read(200)
                                            print(f"  Primeros caracteres: {content[:100]}")
                                            if '[' in content or '{' in content:
                                                print(f"  ¡Parece contener JSON!")
                                    except Exception as e:
                                        print(f"  Error al leer: {e}")
                    except Exception as e:
                        print(f"Error con el archivo {full_path}: {e}")
    
    # Mostrar los 10 archivos más recientes
    if recent_files:
        print("\n10 archivos .dat más recientes:")
        recent_files.sort(key=lambda x: x[2], reverse=True)
        for i, (path, size, date) in enumerate(recent_files[:10]):
            print(f"{i+1}. {path}")
            print(f"   Tamaño: {size} bytes")
            print(f"   Modificado: {date}")
            
            # Si es pequeño, mostrar los primeros bytes
            if size < 10000:
                try:
                    with open(path, 'r', errors='ignore') as f:
                        content = f.read(200)
                        print(f"   Primeros caracteres: {content[:100]}")
                except Exception as e:
                    print(f"   Error al leer: {e}")
    else:
        print("No se encontraron archivos .dat recientes")
        
if __name__ == "__main__":
    main() 