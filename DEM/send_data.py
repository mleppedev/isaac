#!/usr/bin/env python
"""
Script para enviar datos pendientes del mod DataExtractorMod al servidor.
Este script debe ejecutarse periódicamente mientras se juega.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Configuración
MOD_DIR = os.path.dirname(os.path.abspath(__file__))
PENDING_FILE = os.path.join(MOD_DIR, "pending_data.json")
SERVER_URL = "http://localhost:8000/api/data"  # Cambiar según configuración
API_KEY = "default_key"  # Cambiar según configuración
LOG_FILE = os.path.join(MOD_DIR, "send_data.log")

def setup_logging():
    """Configurar el registro de eventos"""
    import logging
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_config():
    """Cargar configuración desde config.lua"""
    config = {
        "SERVER_URL": SERVER_URL,
        "API_KEY": API_KEY
    }
    
    # Intentar leer config.lua
    try:
        with open(os.path.join(MOD_DIR, "config.lua"), "r") as f:
            for line in f:
                if "SERVER_URL" in line and "=" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        url = parts[1].strip().strip('"\'')
                        if url:
                            config["SERVER_URL"] = url
                elif "API_KEY" in line and "=" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        key = parts[1].strip().strip('"\'')
                        if key:
                            config["API_KEY"] = key
    except Exception as e:
        logger.error(f"Error al leer config.lua: {e}")
    
    return config

def send_data_to_server(data, config):
    """Enviar datos al servidor"""
    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": config["API_KEY"]
        }
        
        response = requests.post(
            config["SERVER_URL"],
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Datos enviados correctamente: {data.get('room_id', 'unknown')}")
            return True
        else:
            logger.error(f"Error al enviar datos: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Excepción al enviar datos: {e}")
        return False

def process_pending_data():
    """Procesar datos pendientes"""
    if not os.path.exists(PENDING_FILE):
        logger.info("No hay archivo de datos pendientes")
        return
    
    try:
        # Leer y procesar el archivo
        with open(PENDING_FILE, "r") as f:
            lines = f.readlines()
        
        if not lines:
            logger.info("No hay datos pendientes para enviar")
            return
        
        # Cargar configuración
        config = load_config()
        
        # Procesar cada línea (cada línea es un objeto JSON)
        successful_sends = 0
        failed_sends = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                # Convertir la línea a un objeto Python
                data = json.loads(line)
                
                # Enviar al servidor
                if send_data_to_server(data, config):
                    successful_sends += 1
                else:
                    failed_sends += 1
            
            except json.JSONDecodeError:
                logger.error(f"Error al decodificar JSON: {line}")
                failed_sends += 1
        
        # Si todos los envíos fueron exitosos, borrar el archivo
        if failed_sends == 0 and successful_sends > 0:
            os.remove(PENDING_FILE)
            logger.info(f"Todos los datos enviados correctamente ({successful_sends} registros)")
        else:
            # Guardar solo los que fallaron (implementación simplificada)
            logger.info(f"Enviados: {successful_sends}, Fallidos: {failed_sends}")
            # En una implementación real, guardaríamos solo los que fallaron
    
    except Exception as e:
        logger.error(f"Error al procesar datos pendientes: {e}")

if __name__ == "__main__":
    # Configurar logging
    logger = setup_logging()
    
    logger.info("Iniciando envío de datos pendientes")
    
    # Procesar datos pendientes
    process_pending_data()
    
    logger.info("Proceso completado") 