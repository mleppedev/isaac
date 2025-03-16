#!/usr/bin/env python
"""
Script para entrenar un modelo de IA con los datos procesados del juego.
Este es un ejemplo básico que utiliza un modelo de regresión para predecir la salud del jugador.
"""

import os
import glob
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Configuración
PROCESSED_DATA_DIR = "processed_data"
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

def load_latest_data():
    """Cargar el conjunto de datos procesados más reciente"""
    # Buscar el archivo pickle más reciente
    pickle_files = glob.glob(os.path.join(PROCESSED_DATA_DIR, "*.pkl"))
    
    if not pickle_files:
        print("No se encontraron datos procesados")
        return None
    
    # Ordenar por fecha de modificación (más reciente primero)
    latest_file = max(pickle_files, key=os.path.getmtime)
    print(f"Cargando datos desde: {latest_file}")
    
    # Cargar el DataFrame
    df = pd.read_pickle(latest_file)
    return df

def prepare_features_and_target(df, target_col='health'):
    """Preparar características y variable objetivo"""
    # Verificar que el DataFrame tenga datos
    if df is None or len(df) == 0:
        print("No hay datos para entrenar el modelo")
        return None, None, None, None
    
    # Verificar que la columna objetivo exista
    if target_col not in df.columns:
        print(f"La columna objetivo '{target_col}' no existe en los datos")
        return None, None, None, None
    
    # Seleccionar características (excluyendo columnas no numéricas y la objetivo)
    exclude_cols = ['timestamp', 'source_file', target_col, 'room_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    print(f"Características seleccionadas: {feature_cols}")
    
    # Dividir en conjuntos de entrenamiento y prueba
    X = df[feature_cols]
    y = df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Conjunto de entrenamiento: {X_train.shape[0]} muestras")
    print(f"Conjunto de prueba: {X_test.shape[0]} muestras")
    
    return X_train, X_test, y_train, y_test

def train_model(X_train, y_train):
    """Entrenar un modelo de regresión"""
    # Verificar que haya datos de entrenamiento
    if X_train is None or y_train is None:
        return None
    
    # Crear y entrenar el modelo
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    print("Modelo entrenado correctamente")
    return model

def evaluate_model(model, X_test, y_test):
    """Evaluar el rendimiento del modelo"""
    if model is None or X_test is None or y_test is None:
        return
    
    # Hacer predicciones
    y_pred = model.predict(X_test)
    
    # Calcular métricas
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Error cuadrático medio (MSE): {mse:.4f}")
    print(f"Coeficiente de determinación (R²): {r2:.4f}")
    
    # Visualizar resultados
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
    plt.xlabel('Valores reales')
    plt.ylabel('Predicciones')
    plt.title('Comparación entre valores reales y predicciones')
    
    # Guardar gráfico
    plt.savefig(os.path.join(MODELS_DIR, "prediction_results.png"))
    plt.close()
    
    return mse, r2

def save_model(model, feature_names):
    """Guardar el modelo entrenado"""
    if model is None:
        return
    
    # Crear nombre de archivo con timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = os.path.join(MODELS_DIR, f"model_{timestamp}.pkl")
    
    # Guardar el modelo
    with open(model_path, 'wb') as f:
        pickle.dump({'model': model, 'features': feature_names}, f)
    
    print(f"Modelo guardado en: {model_path}")
    return model_path

def main():
    """Función principal"""
    print("Iniciando entrenamiento del modelo...")
    
    # Cargar datos
    df = load_latest_data()
    
    if df is None:
        print("No se pudieron cargar los datos. Abortando.")
        return
    
    # Preparar características y variable objetivo
    X_train, X_test, y_train, y_test = prepare_features_and_target(df, target_col='health')
    
    if X_train is None:
        return
    
    # Entrenar modelo
    model = train_model(X_train, y_train)
    
    # Evaluar modelo
    evaluate_model(model, X_test, y_test)
    
    # Guardar modelo
    save_model(model, X_train.columns.tolist())
    
    print("Entrenamiento completado")

if __name__ == "__main__":
    main() 