#!/usr/bin/env python
"""
Script para visualizar los datos guardados en la base de datos DEM
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from collections import Counter, defaultdict

# Constantes
DATABASE_FILE = "dem_database.json"
OUTPUT_DIR = "reports"

def setup_logging(debug=False):
    """Configurar el registro de eventos"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Configuración básica
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    return logging.getLogger('')

def load_database(db_file=DATABASE_FILE):
    """Cargar la base de datos DEM"""
    if not os.path.exists(db_file):
        logging.error(f"Error: No se encontró el archivo de base de datos {db_file}")
        return None
    
    try:
        with open(db_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Error al decodificar la base de datos: {e}")
        return None
    except Exception as e:
        logging.error(f"Error al cargar la base de datos: {e}")
        return None

def print_summary(database):
    """Imprimir un resumen de los datos"""
    if not database or "events" not in database or not database["events"]:
        logging.warning("No hay eventos en la base de datos")
        return
    
    events = database["events"]
    metadata = database.get("metadata", {})
    
    print("\n===== RESUMEN DE DATOS DEM =====")
    print(f"Total de eventos: {len(events)}")
    print(f"Última actualización: {metadata.get('last_update', 'Desconocida')}")
    print(f"Versión de la base de datos: {metadata.get('version', 'Desconocida')}")
    
    # Contar tipos de eventos
    event_types = Counter(event.get("event_type", "unknown") for event in events)
    print("\n--- TIPOS DE EVENTOS ---")
    for event_type, count in event_types.most_common():
        print(f"  - {event_type}: {count} eventos")
    
    # Estadísticas de partidas
    game_seeds = set(event.get("game_data", {}).get("seed", 0) for event in events if event.get("game_data"))
    print(f"\n--- ESTADÍSTICAS DE PARTIDAS ---")
    print(f"  - Partidas (seeds) únicas: {len(game_seeds)}")
    
    # Rango de timestamps
    timestamps = sorted([event.get("timestamp", 0) for event in events])
    if timestamps:
        print(f"\n--- RANGO DE TIEMPO ---")
        print(f"  - Primer evento: Frame {timestamps[0]}")
        print(f"  - Último evento: Frame {timestamps[-1]}")
        print(f"  - Duración aproximada: {(timestamps[-1] - timestamps[0]) / 30:.2f} segundos")
    
    # Eventos por partida
    print("\n--- EVENTOS POR PARTIDA ---")
    events_by_seed = defaultdict(list)
    for event in events:
        seed = event.get("game_data", {}).get("seed", 0)
        if seed:
            events_by_seed[seed].append(event)
    
    for seed, seed_events in sorted(events_by_seed.items(), key=lambda x: len(x[1]), reverse=True):
        event_types_in_seed = Counter(event.get("event_type", "unknown") for event in seed_events)
        print(f"  - Partida {seed}: {len(seed_events)} eventos")
        top_events = event_types_in_seed.most_common(3)
        print(f"    Top eventos: {', '.join(f'{et} ({count})' for et, count in top_events)}")

def list_events(database, limit=10, event_type=None, seed=None):
    """Listar eventos específicos con detalles"""
    if not database or "events" not in database or not database["events"]:
        logging.warning("No hay eventos en la base de datos")
        return
    
    events = database["events"]
    
    # Filtrar por tipo de evento si se especifica
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    
    # Filtrar por seed si se especifica
    if seed:
        events = [e for e in events if e.get("game_data", {}).get("seed") == seed]
    
    # Ordenar por timestamp
    events = sorted(events, key=lambda x: x.get("timestamp", 0))
    
    # Limitar cantidad
    if limit and limit > 0:
        events = events[:limit]
    
    print(f"\n===== LISTADO DE EVENTOS ({len(events)}) =====")
    
    for i, event in enumerate(events):
        print(f"\n--- Evento {i+1} ---")
        print(f"ID: {event.get('event_id', 'Sin ID')}")
        print(f"Tipo: {event.get('event_type', 'Desconocido')}")
        print(f"Timestamp: {event.get('timestamp', 0)}")
        
        # Datos del juego
        game_data = event.get("game_data", {})
        if game_data:
            print(f"Seed: {game_data.get('seed', 'Desconocido')}")
            print(f"Nivel: {game_data.get('level', 'Desconocido')}")
            print(f"Frame: {game_data.get('frame_count', 'Desconocido')}")
        
        # Datos específicos del evento
        event_data = event.get("data", {})
        if event_data:
            print("Datos específicos:")
            for key, value in event_data.items():
                print(f"  - {key}: {value}")

def generate_report(database, output_file=None):
    """Generar un informe HTML con los datos"""
    if not database or "events" not in database or not database["events"]:
        logging.warning("No hay eventos en la base de datos para generar un informe")
        return
    
    # Crear directorio de salida si no existe
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Nombre de archivo por defecto con timestamp
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"dem_report_{timestamp}.html")
    
    events = database["events"]
    metadata = database.get("metadata", {})
    
    # Contar tipos de eventos
    event_types = Counter(event.get("event_type", "unknown") for event in events)
    
    # Eventos por partida
    events_by_seed = defaultdict(list)
    for event in events:
        seed = event.get("game_data", {}).get("seed", 0)
        if seed:
            events_by_seed[seed].append(event)
    
    # Generar HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Informe de Datos DEM</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .events-table {{ width: 100%; border-collapse: collapse; }}
            .events-table th, .events-table td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            .events-table th {{ background-color: #f2f2f2; }}
            .chart-container {{ display: flex; justify-content: space-between; margin: 20px 0; }}
            .chart {{ flex: 1; margin: 0 10px; background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Informe de Datos del Mod Data Event Manager</h1>
            <p>Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <div class="summary">
                <h2>Resumen</h2>
                <p>Total de eventos: <strong>{len(events)}</strong></p>
                <p>Última actualización: <strong>{metadata.get('last_update', 'Desconocida')}</strong></p>
                <p>Versión de la base de datos: <strong>{metadata.get('version', 'Desconocida')}</strong></p>
                <p>Partidas (seeds) únicas: <strong>{len(events_by_seed)}</strong></p>
            </div>
            
            <div class="chart-container">
                <div class="chart">
                    <h2>Tipos de Eventos</h2>
                    <table class="events-table">
                        <tr>
                            <th>Tipo de Evento</th>
                            <th>Cantidad</th>
                            <th>Porcentaje</th>
                        </tr>
    """
    
    # Añadir filas de tipos de eventos
    for event_type, count in event_types.most_common():
        percentage = (count / len(events)) * 100
        html += f"""
                        <tr>
                            <td>{event_type}</td>
                            <td>{count}</td>
                            <td>{percentage:.1f}%</td>
                        </tr>
        """
    
    html += """
                    </table>
                </div>
            </div>
            
            <h2>Eventos por Partida</h2>
    """
    
    # Añadir sección de eventos por partida
    for seed, seed_events in sorted(events_by_seed.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        event_types_in_seed = Counter(event.get("event_type", "unknown") for event in seed_events)
        timestamps = sorted([event.get("timestamp", 0) for event in seed_events])
        duration = "N/A"
        if len(timestamps) > 1:
            duration = f"{(timestamps[-1] - timestamps[0]) / 30:.2f} segundos"
        
        html += f"""
            <div class="summary">
                <h3>Partida: Seed {seed}</h3>
                <p>Total de eventos: <strong>{len(seed_events)}</strong></p>
                <p>Duración aproximada: <strong>{duration}</strong></p>
                
                <h4>Tipos de eventos:</h4>
                <table class="events-table">
                    <tr>
                        <th>Tipo</th>
                        <th>Cantidad</th>
                    </tr>
        """
        
        for event_type, count in event_types_in_seed.most_common():
            html += f"""
                    <tr>
                        <td>{event_type}</td>
                        <td>{count}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        """
    
    html += """
            <h2>Eventos Recientes</h2>
            <table class="events-table">
                <tr>
                    <th>ID</th>
                    <th>Tipo</th>
                    <th>Timestamp</th>
                    <th>Seed</th>
                    <th>Nivel</th>
                    <th>Datos</th>
                </tr>
    """
    
    # Añadir los eventos más recientes
    for event in sorted(events, key=lambda x: x.get("timestamp", 0), reverse=True)[:20]:
        event_id = event.get("event_id", "Sin ID")
        event_type = event.get("event_type", "Desconocido")
        timestamp = event.get("timestamp", 0)
        seed = event.get("game_data", {}).get("seed", "N/A")
        level = event.get("game_data", {}).get("level", "N/A")
        
        data_str = json.dumps(event.get("data", {}), ensure_ascii=False)
        if len(data_str) > 50:
            data_str = data_str[:50] + "..."
        
        html += f"""
                <tr>
                    <td>{event_id}</td>
                    <td>{event_type}</td>
                    <td>{timestamp}</td>
                    <td>{seed}</td>
                    <td>{level}</td>
                    <td>{data_str}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
    </body>
    </html>
    """
    
    # Guardar archivo HTML
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        logging.info(f"Informe generado: {output_file}")
        return output_file
    except Exception as e:
        logging.error(f"Error al generar el informe: {e}")
        return None

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Visualizar datos del mod DEM")
    parser.add_argument("--db-file", default=DATABASE_FILE, help="Archivo de base de datos")
    parser.add_argument("--report", action="store_true", help="Generar informe HTML")
    parser.add_argument("--output", help="Archivo de salida para el informe")
    parser.add_argument("--list", action="store_true", help="Listar eventos detallados")
    parser.add_argument("--limit", type=int, default=10, help="Límite de eventos a listar")
    parser.add_argument("--type", help="Filtrar por tipo de evento")
    parser.add_argument("--seed", help="Filtrar por seed de partida")
    parser.add_argument("--debug", action="store_true", help="Activar modo debug")
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(debug=args.debug)
    
    # Cargar base de datos
    database = load_database(args.db_file)
    if not database:
        return 1
    
    # Mostrar resumen básico siempre
    print_summary(database)
    
    # Generar informe si se solicita
    if args.report:
        report_file = generate_report(database, args.output)
        if report_file:
            print(f"\nInforme generado: {os.path.abspath(report_file)}")
    
    # Listar eventos si se solicita
    if args.list:
        list_events(database, args.limit, args.type, args.seed)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 