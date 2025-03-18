"""
Módulo de Visión por Computadora para The Binding of Isaac
=========================================================

Este módulo proporciona herramientas para:
1. Capturar la pantalla del juego
2. Procesar las imágenes para detectar elementos
3. Extraer características para entrenamiento
4. Enviar comandos al mod DEM_CV
"""

import os
import sys

# Añadir el directorio actual al path para facilitar importaciones
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importar componentes principales para facilitar acceso
try:
    from .main import IsaacVisionSystem
    from .capture import GameCapture
    from .detector import GameDetector, draw_detection_results
    from .agent import RLAgent
except ImportError:
    # En caso de importación directa
    pass

__version__ = '0.1.0' 