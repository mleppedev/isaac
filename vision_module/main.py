"""
Sistema principal para control de The Binding of Isaac mediante visión por computadora
"""

import os
import sys
import time
import logging
import json
import argparse
import threading
import cv2
import numpy as np
from pathlib import Path

# Ajustar rutas para importaciones
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importar componentes del módulo
try:
    from capture import GameCapture
    from detector import GameDetector, draw_detection_results
    from agent import RLAgent
except ImportError:
    # Intentar importar con nombre de paquete completo
    from vision_module.capture import GameCapture
    from vision_module.detector import GameDetector, draw_detection_results
    from vision_module.agent import RLAgent

# Configurar logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'isaac_vision_system.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file
)
logger = logging.getLogger("IsaacVision")

class IsaacVisionSystem:
    """Sistema principal para visión por computadora y control de Isaac"""
    
    def __init__(self, config=None):
        """
        Inicializa el sistema de visión por computadora
        
        Args:
            config: Configuración personalizada (opcional)
        """
        # Cargar configuración
        self.config = config or self._load_default_config()
        
        # Componentes
        self.capture = None
        self.detector = None
        self.agent = None
        
        # Estado del sistema
        self.running = False
        self.visualize = self.config.get('visualize', True)
        self.training_mode = self.config.get('training_mode', False)
        self.detection_frequency = self.config.get('detection_frequency', 0.1)  # segundos
        self.last_detection = None
        self.last_detection_time = 0
        self.frame_counter = 0  # Contador de frames procesados
        
        # Ruta para guardar frames para la interfaz web
        self.web_output_dir = self.config.get('web_output_dir', './server/static/vision_output')
        os.makedirs(self.web_output_dir, exist_ok=True)
        
        # Archivo para el último frame y datos de detección
        self.web_frame_path = os.path.join(self.web_output_dir, 'current_frame.jpg')
        self.web_data_path = os.path.join(self.web_output_dir, 'detection_data.json')
        
        # Crear directorio de templates si no existe
        templates_dir = Path("./vision_module/templates")
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio de templates creado: {templates_dir}")
        
        # Inicializar componentes
        self._init_components()
        
        logger.info("Sistema de visión inicializado")
    
    def _load_default_config(self):
        """Carga configuración por defecto"""
        return {
            'capture_rate': 30,  # FPS para captura
            'visualize': True,   # Mostrar visualización
            'training_mode': False,  # Modo entrenamiento vs. inferencia
            'detection_frequency': 0.1,  # Segundos entre detecciones
            'web_output_dir': './server/static/vision_output',  # Directorio para salida web
            'agent': {
                'exploration_rate': 0.2,  # Tasa de exploración del agente
                'model_path': None  # Ruta al modelo pre-entrenado
            },
            'detector': {
                'model_path': None  # Ruta al modelo del detector
            },
            'mod_connection': {
                'host': 'localhost',
                'port': 12345
            }
        }
    
    def _init_components(self):
        """Inicializa los componentes del sistema"""
        try:
            # Inicializar captura
            self.capture = GameCapture(
                capture_rate=self.config.get('capture_rate', 30)
            )
            logger.info("Captura inicializada")
            
            # Inicializar detector
            self.detector = GameDetector(
                model_path=self.config.get('detector', {}).get('model_path')
            )
            self.detector.last_detection = None  # Añadir atributo para el último resultado
            logger.info("Detector inicializado")
            
            # Inicializar agente
            self.agent = RLAgent(
                model_path=self.config.get('agent', {}).get('model_path'),
                exploration_rate=self.config.get('agent', {}).get('exploration_rate', 0.2)
            )
            logger.info("Agente RL inicializado")
            
        except Exception as e:
            logger.error(f"Error al inicializar componentes: {e}")
            raise
    
    def capture_and_detect(self):
        """Captura un frame y detecta elementos del juego"""
        # Capturar frame
        frame = self.capture.get_frame()
        if frame is None:
            logger.warning("No se pudo capturar frame")
            return None
        
        # Detectar elementos solo si ha pasado el tiempo mínimo desde la última detección
        current_time = time.time()
        if current_time - self.last_detection_time >= self.detection_frequency:
            # Detectar elementos en el frame
            detection_results = self.detector.analyze_frame(frame)
            
            if detection_results:
                # Incrementar contador de frames
                self.frame_counter += 1
                
                # Añadir ID de frame a los resultados
                detection_results['frame_id'] = self.frame_counter
                
                # Actualizar última detección
                self.last_detection = detection_results
                self.detector.last_detection = detection_results
                self.last_detection_time = current_time
                
                # Guardar frame y datos para la interfaz web
                self._save_web_output(frame, detection_results)
                
                # Visualizar resultados si está habilitado
                if self.visualize:
                    annotated_frame = draw_detection_results(frame, detection_results)
                    cv2.imshow('Isaac Vision System', annotated_frame)
                    cv2.waitKey(1)  # Mostrar por 1ms
            else:
                # Si no se detectaron elementos pero queremos visualizar
                if self.visualize:
                    cv2.imshow('Isaac Vision System', frame)
                    cv2.waitKey(1)
                
                # Guardar frame sin anotaciones para la interfaz web
                self._save_web_output(frame, None)
            
            return detection_results
        
        # Si no es momento de detectar pero queremos visualizar
        if self.visualize:
            # Mostrar última detección si existe
            if self.last_detection:
                annotated_frame = draw_detection_results(frame, self.last_detection)
                cv2.imshow('Isaac Vision System', annotated_frame)
            else:
                cv2.imshow('Isaac Vision System', frame)
            cv2.waitKey(1)
        
        # Guardar frame para la interfaz web incluso si no es momento de detección
        self._save_web_output(frame, self.last_detection)
        
        return None
    
    def _save_web_output(self, frame, detection_results):
        """
        Guarda frame y datos de detección para la interfaz web
        
        Args:
            frame: Frame capturado
            detection_results: Resultados de la detección (puede ser None)
        """
        try:
            # Guardar frame (con anotaciones si hay resultados)
            if detection_results:
                annotated_frame = draw_detection_results(frame, detection_results)
                cv2.imwrite(self.web_frame_path, annotated_frame)
                
                # Guardar datos de detección como JSON
                web_data = {
                    'frame_id': detection_results.get('frame_id', 0),
                    'timestamp': time.strftime("%H:%M:%S"),
                    'player': detection_results.get('player'),
                    'enemies': detection_results.get('enemies', []),
                    'items': detection_results.get('items', []),
                    'doors': detection_results.get('doors', []),
                    'processing_time': detection_results.get('processing_time', 0)
                }
                
                with open(self.web_data_path, 'w') as f:
                    json.dump(web_data, f)
            else:
                # Guardar frame sin anotaciones
                cv2.imwrite(self.web_frame_path, frame)
        except Exception as e:
            logger.error(f"Error al guardar salida web: {e}")
    
    def main_loop(self):
        """Bucle principal del sistema de visión"""
        logger.info("Iniciando bucle principal del sistema de visión")
        
        try:
            while self.running:
                # Capturar y detectar
                detection_results = self.capture_and_detect()
                
                # Esperar tecla ESC para salir
                key = cv2.waitKey(1)
                if key == 27:  # ESC
                    logger.info("Tecla ESC presionada, deteniendo sistema")
                    break
                
                # Pequeña pausa para no saturar CPU
                time.sleep(0.01)
        except Exception as e:
            logger.error(f"Error en bucle principal: {e}")
        finally:
            self.stop()
    
    def start(self):
        """Inicia el sistema completo"""
        if self.running:
            logger.warning("El sistema ya está en ejecución")
            return False
        
        try:
            # Crear directorio de salida web si no existe
            os.makedirs(self.web_output_dir, exist_ok=True)
            
            # Iniciar captura
            self.capture.start()
            
            # Iniciar agente
            self.agent.start(self.detector)
            
            # Marcar como en ejecución
            self.running = True
            
            # Iniciar bucle principal en un hilo
            self.main_thread = threading.Thread(target=self.main_loop)
            self.main_thread.daemon = True
            self.main_thread.start()
            
            logger.info("Sistema iniciado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar sistema: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Detiene el sistema completo"""
        logger.info("Deteniendo sistema...")
        
        # Detener componentes
        if self.agent and hasattr(self.agent, 'running') and self.agent.running:
            self.agent.stop()
        
        if self.capture and hasattr(self.capture, 'running') and self.capture.running:
            self.capture.stop()
        
        # Cerrar ventanas de visualización
        if self.visualize:
            cv2.destroyAllWindows()
        
        # Marcar como detenido
        self.running = False
        logger.info("Sistema detenido")
    
    def save_templates(self, frame, template_type, name, rect=None):
        """
        Guarda un template para uso futuro en detección
        
        Args:
            frame: Frame completo capturado
            template_type: Tipo de template (player, enemy, item, door)
            name: Nombre del template
            rect: Rectángulo con la región a guardar (x, y, w, h)
        
        Returns:
            Ruta al archivo guardado
        """
        if frame is None:
            logger.error("No se puede guardar template: frame nulo")
            return None
        
        # Definir nombre del archivo
        prefix = ""
        if template_type == "enemy":
            prefix = "enemy_"
        elif template_type == "item":
            prefix = "item_"
        elif template_type == "door":
            prefix = "door_"
        
        filename = f"{prefix}{name}.png"
        filepath = os.path.join("vision_module/templates", filename)
        
        try:
            # Si se especificó un rectángulo, recortar la imagen
            if rect and len(rect) == 4:
                x, y, w, h = rect
                template = frame[y:y+h, x:x+w]
            else:
                template = frame
            
            # Guardar imagen
            cv2.imwrite(filepath, template)
            logger.info(f"Template guardado: {filepath}")
            
            return filepath
        except Exception as e:
            logger.error(f"Error al guardar template: {e}")
            return None
    
    def get_latest_detection(self):
        """
        Obtiene la última detección para la API
        
        Returns:
            Datos de la última detección
        """
        if self.last_detection:
            return {
                'frame_id': self.frame_counter,
                'timestamp': time.strftime("%H:%M:%S"),
                'player': self.last_detection.get('player'),
                'enemies': self.last_detection.get('enemies', []),
                'items': self.last_detection.get('items', []),
                'doors': self.last_detection.get('doors', []),
                'processing_time': self.last_detection.get('processing_time', 0)
            }
        return None

def parse_arguments():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Sistema de visión por computadora para The Binding of Isaac')
    parser.add_argument('--no-visualization', action='store_true', help='Desactivar visualización')
    parser.add_argument('--training', action='store_true', help='Ejecutar en modo entrenamiento')
    parser.add_argument('--frequency', type=float, default=0.1, help='Frecuencia de detección en segundos')
    parser.add_argument('--exploration', type=float, default=0.2, help='Tasa de exploración del agente')
    parser.add_argument('--model', type=str, help='Ruta al modelo pre-entrenado')
    
    return parser.parse_args()

def main():
    """Función principal para ejecutar el sistema"""
    # Parsear argumentos
    args = parse_arguments()
    
    # Crear configuración basada en argumentos
    config = {
        'visualize': not args.no_visualization,
        'training_mode': args.training,
        'detection_frequency': args.frequency,
        'agent': {
            'exploration_rate': args.exploration,
            'model_path': args.model
        }
    }
    
    # Crear y ejecutar sistema
    system = IsaacVisionSystem(config)
    
    try:
        # Iniciar sistema
        if system.start():
            # En modo línea de comandos, mantener ejecución hasta Ctrl+C
            print("Sistema de visión en ejecución. Presione Ctrl+C para detener.")
            while system.running:
                time.sleep(0.1)
        else:
            print("No se pudo iniciar el sistema de visión.")
    except KeyboardInterrupt:
        print("\nDetención solicitada por usuario.")
    finally:
        system.stop()
        print("Sistema detenido.")

if __name__ == "__main__":
    main() 