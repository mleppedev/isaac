#!/usr/bin/env python
"""
Script simple para leer el archivo de datos DEM desde la ubicación correcta encontrada.
"""

import os
import json
import sys

def main():
    print("DEM - Lector de Datos")
    print("======================")
    
    # Ruta exacta donde se encontró el archivo
    exact_path = "D:\\SteamLibrary\\steamapps\\common\\The Binding of Isaac Rebirth\\data\\dem\\save1.dat"
    
    print(f"Leyendo archivo: {exact_path}")
    
    if not os.path.exists(exact_path):
        print(f"ERROR: El archivo no existe en la ruta.")
        return 1
    
    # Leer el archivo
    try:
        file_size = os.path.getsize(exact_path)
        print(f"Tamaño: {file_size} bytes")
        
        with open(exact_path, 'r', errors='ignore') as f:
            content = f.read().strip()
        
        print(f"Contenido leído: {len(content)} bytes")
        
        # Analizar JSON
        if content.startswith('['):
            print("El archivo contiene un array JSON")
            data = json.loads(content)
        elif content.startswith('{'):
            print("El archivo contiene un objeto JSON")
            data = [json.loads(content)]
        else:
            print(f"Contenido no reconocible como JSON. Primeros 100 caracteres:")
            print(content[:100])
            return 1
        
        # Mostrar información
        print(f"Eventos encontrados: {len(data)}")
        
        # Tipos de eventos
        event_types = {}
        for event in data:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print("Tipos de eventos:")
        for event_type, count in sorted(event_types.items()):
            print(f"  - {event_type}: {count}")
        
        # Mostrar detalles de los primeros 3 eventos
        print("\nDetalles de los primeros eventos:")
        for i, event in enumerate(data[:3]):
            print(f"Evento {i+1}:")
            print(f"  - Tipo: {event.get('event_type')}")
            print(f"  - ID: {event.get('event_id')}")
            print(f"  - Timestamp: {event.get('timestamp')}")
            game_data = event.get('game_data', {})
            if game_data:
                print(f"  - Seed: {game_data.get('seed')}")
                print(f"  - Nivel: {game_data.get('level')}")
                print(f"  - Frame: {game_data.get('frame_count')}")
        
        # Guardar en archivo
        print("\n¿Guardar eventos en 'dem_events.json'? (s/n):")
        answer = input().lower()
        if answer.startswith('s'):
            with open('dem_events.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Datos guardados en: {os.path.abspath('dem_events.json')}")
        
        return 0
    
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 