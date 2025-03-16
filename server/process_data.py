#!/usr/bin/env python
"""
Script para procesar los datos recibidos del mod y prepararlos para entrenar una IA.
"""

import os
import json
import glob
import pandas as pd
import numpy as np
from datetime import datetime

# Configuración
DATA_DIR = "received_data"
OUTPUT_DIR = "processed_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_all_data():
    """Cargar todos los archivos de datos recibidos"""
    all_data = []
    
    # Buscar todos los archivos JSON en el directorio de datos
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Añadir el nombre del archivo como referencia
                data['source_file'] = os.path.basename(file_path)
                
                all_data.append(data)
        except Exception as e:
            print(f"Error al cargar {file_path}: {e}")
    
    print(f"Cargados {len(all_data)} registros de datos")
    return all_data

def convert_to_dataframe(data_list):
    """Convertir la lista de datos a un DataFrame de pandas"""
    # Crear un DataFrame vacío
    df = pd.DataFrame()
    
    # Procesar cada registro
    for data in data_list:
        # Extraer campos anidados
        if 'position' in data:
            data['position_x'] = data['position'].get('x')
            data['position_y'] = data['position'].get('y')
            del data['position']
        
        # Añadir al DataFrame
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    
    return df

def preprocess_data(df):
    """Preprocesar los datos para el entrenamiento"""
    # Convertir timestamp a datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Extraer características de tiempo
        df['hour'] = df['timestamp'].dt.hour
        df['minute'] = df['timestamp'].dt.minute
        df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # Normalizar valores numéricos
    numeric_cols = ['health', 'position_x', 'position_y', 'enemies']
    for col in numeric_cols:
        if col in df.columns:
            df[f'{col}_normalized'] = (df[col] - df[col].min()) / (df[col].max() - df[col].min() + 1e-8)
    
    # Codificar variables categóricas si las hay
    # (en este ejemplo no tenemos, pero se podría añadir)
    
    return df

def save_processed_data(df):
    """Guardar los datos procesados"""
    # Crear nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Guardar en diferentes formatos
    csv_path = os.path.join(OUTPUT_DIR, f"processed_data_{timestamp}.csv")
    df.to_csv(csv_path, index=False)
    
    # También guardar en formato pickle para preservar tipos de datos
    pickle_path = os.path.join(OUTPUT_DIR, f"processed_data_{timestamp}.pkl")
    df.to_pickle(pickle_path)
    
    print(f"Datos guardados en {csv_path} y {pickle_path}")
    
    return csv_path, pickle_path

def generate_statistics(df):
    """Generar estadísticas básicas de los datos"""
    stats = {
        "num_records": len(df),
        "unique_rooms": df['room_id'].nunique() if 'room_id' in df.columns else 0,
        "avg_health": df['health'].mean() if 'health' in df.columns else 0,
        "avg_enemies": df['enemies'].mean() if 'enemies' in df.columns else 0,
        "timestamp": datetime.now().isoformat()
    }
    
    # Guardar estadísticas
    stats_path = os.path.join(OUTPUT_DIR, "statistics.json")
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Estadísticas guardadas en {stats_path}")
    return stats

def main():
    """Función principal"""
    print("Iniciando procesamiento de datos...")
    
    # Cargar todos los datos
    data_list = load_all_data()
    
    if not data_list:
        print("No hay datos para procesar")
        return
    
    # Convertir a DataFrame
    df = convert_to_dataframe(data_list)
    
    # Preprocesar datos
    df_processed = preprocess_data(df)
    
    # Guardar datos procesados
    csv_path, pickle_path = save_processed_data(df_processed)
    
    # Generar estadísticas
    stats = generate_statistics(df_processed)
    
    print("Procesamiento completado")
    print(f"Registros procesados: {stats['num_records']}")
    print(f"Habitaciones únicas: {stats['unique_rooms']}")

if __name__ == "__main__":
    main() 