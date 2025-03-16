from flask import Flask, request, jsonify
import os
import json
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Directorio para almacenar los datos recibidos
DATA_DIR = "received_data"
os.makedirs(DATA_DIR, exist_ok=True)

@app.route('/api/data', methods=['POST'])
def receive_data():
    try:
        # Obtener datos del request
        data = request.json
        
        # Registrar la recepción
        logging.info(f"Datos recibidos: {data}")
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DATA_DIR}/data_{timestamp}.json"
        
        # Guardar datos en un archivo
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"status": "success", "message": "Datos recibidos correctamente"}), 200
    
    except Exception as e:
        logging.error(f"Error al procesar datos: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "El servidor está funcionando correctamente"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) 