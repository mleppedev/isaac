"""
Módulo de detección de elementos en The Binding of Isaac usando visión por computadora
"""

import cv2
import numpy as np
import os
import logging
from pathlib import Path
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='vision_detector.log'
)
logger = logging.getLogger("IsaacDetector")

class GameDetector:
    """Detector de elementos del juego The Binding of Isaac"""
    
    def __init__(self, model_path=None):
        """
        Inicializa el detector de elementos
        
        Args:
            model_path: Ruta al modelo pre-entrenado (si existe)
        """
        self.model_path = model_path
        self.model = None
        self.target_size = (640, 480)  # Tamaño al que redimensionaremos las imágenes
        self.templates = {}  # Diccionario de templates para matching
        self.confidence_threshold = 0.7  # Umbral de confianza para detección
        
        # Inicializar detector
        self._init_detector()
    
    def _init_detector(self):
        """Inicializa el detector según modelo disponible"""
        # Por ahora usamos un detector basado en template matching
        # En el futuro, cargaremos un modelo de ML pre-entrenado
        
        if self.model_path and os.path.exists(self.model_path):
            try:
                # Aquí cargaríamos un modelo real (PyTorch, TensorFlow, etc.)
                logger.info(f"Cargando modelo desde {self.model_path}")
                # self.model = ... (carga del modelo)
                pass
            except Exception as e:
                logger.error(f"Error al cargar modelo: {e}")
        
        # Cargar templates para matching básico
        self._load_templates()
    
    def _load_templates(self):
        """Carga templates de elementos del juego para matching"""
        template_dir = Path("./vision_module/templates")
        
        if not template_dir.exists():
            logger.warning(f"Directorio de templates no encontrado: {template_dir}")
            template_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio de templates creado: {template_dir}")
            return
        
        for template_file in template_dir.glob("*.png"):
            try:
                template_name = template_file.stem
                template = cv2.imread(str(template_file))
                if template is not None:
                    self.templates[template_name] = template
                    logger.info(f"Template cargado: {template_name}")
                else:
                    logger.warning(f"No se pudo cargar template: {template_file}")
            except Exception as e:
                logger.error(f"Error al cargar template {template_file}: {e}")
    
    def preprocess_frame(self, frame):
        """
        Preprocesa un frame para detección
        
        Args:
            frame: Imagen capturada del juego
            
        Returns:
            Imagen preprocesada
        """
        if frame is None:
            return None
            
        # Redimensionar para procesamiento más rápido
        resized = cv2.resize(frame, self.target_size)
        
        # Convertir a escala de grises para algunos algoritmos
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        return {
            'original': frame,
            'resized': resized,
            'gray': gray
        }
    
    def detect_player(self, processed_frame):
        """
        Detecta al jugador en el frame
        
        Args:
            processed_frame: Frame preprocesado
            
        Returns:
            Diccionario con posición del jugador {x, y, w, h, confidence}
        """
        # Si tenemos un template del jugador
        if 'player' in self.templates:
            template = self.templates['player']
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            result = cv2.matchTemplate(
                processed_frame['gray'], 
                template_gray, 
                cv2.TM_CCOEFF_NORMED
            )
            
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.confidence_threshold:
                w, h = template_gray.shape[::-1]
                return {
                    'x': max_loc[0],
                    'y': max_loc[1],
                    'w': w,
                    'h': h,
                    'confidence': max_val
                }
        
        # Método alternativo: buscar por color característico del personaje
        # Implementación básica para Isaac (predominancia de piel/rosa)
        hsv = cv2.cvtColor(processed_frame['resized'], cv2.COLOR_BGR2HSV)
        
        # Rango para tonos de piel (ajustar según el personaje)
        lower_skin = np.array([0, 20, 70])
        upper_skin = np.array([20, 150, 255])
        
        # Máscara para tono de piel
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Operaciones morfológicas para limpiar la máscara
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar contornos por tamaño
        player_contour = None
        max_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 500 < area < 5000 and area > max_area:  # Ajustar según escala
                max_area = area
                player_contour = contour
        
        if player_contour is not None:
            x, y, w, h = cv2.boundingRect(player_contour)
            return {
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'confidence': 0.6  # Valor heurístico
            }
        
        return None
    
    def detect_enemies(self, processed_frame):
        """
        Detecta enemigos en el frame
        
        Args:
            processed_frame: Frame preprocesado
            
        Returns:
            Lista de enemigos detectados [{tipo, x, y, w, h, confidence}]
        """
        enemies = []
        
        # Template matching para cada tipo de enemigo
        for name, template in self.templates.items():
            if not name.startswith('enemy_'):
                continue
                
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(
                processed_frame['gray'], 
                template_gray, 
                cv2.TM_CCOEFF_NORMED
            )
            
            # Encontrar todas las coincidencias por encima del umbral
            locations = np.where(result >= self.confidence_threshold)
            w, h = template_gray.shape[::-1]
            
            for pt in zip(*locations[::-1]):
                # Evitar duplicados cercanos
                duplicate = False
                for enemy in enemies:
                    if (abs(enemy['x'] - pt[0]) < w/2 and 
                        abs(enemy['y'] - pt[1]) < h/2):
                        duplicate = True
                        break
                        
                if not duplicate:
                    enemies.append({
                        'tipo': name.replace('enemy_', ''),
                        'x': pt[0],
                        'y': pt[1],
                        'w': w,
                        'h': h,
                        'confidence': result[pt[1], pt[0]]
                    })
        
        return enemies
    
    def detect_items(self, processed_frame):
        """
        Detecta items en el frame
        
        Args:
            processed_frame: Frame preprocesado
            
        Returns:
            Lista de items detectados [{tipo, x, y, w, h, confidence}]
        """
        items = []
        
        # Template matching para cada tipo de item
        for name, template in self.templates.items():
            if not name.startswith('item_'):
                continue
                
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(
                processed_frame['gray'], 
                template_gray, 
                cv2.TM_CCOEFF_NORMED
            )
            
            # Encontrar todas las coincidencias por encima del umbral
            locations = np.where(result >= self.confidence_threshold)
            w, h = template_gray.shape[::-1]
            
            for pt in zip(*locations[::-1]):
                # Evitar duplicados cercanos
                duplicate = False
                for item in items:
                    if (abs(item['x'] - pt[0]) < w/2 and 
                        abs(item['y'] - pt[1]) < h/2):
                        duplicate = True
                        break
                        
                if not duplicate:
                    items.append({
                        'tipo': name.replace('item_', ''),
                        'x': pt[0],
                        'y': pt[1],
                        'w': w,
                        'h': h,
                        'confidence': result[pt[1], pt[0]]
                    })
        
        return items
    
    def detect_doors(self, processed_frame):
        """
        Detecta puertas en el frame
        
        Args:
            processed_frame: Frame preprocesado
            
        Returns:
            Lista de puertas detectadas [{x, y, w, h, direccion, confidence}]
        """
        doors = []
        directions = ['up', 'down', 'left', 'right']
        
        # Template matching para cada tipo de puerta
        for direction in directions:
            template_name = f'door_{direction}'
            if template_name not in self.templates:
                continue
                
            template = self.templates[template_name]
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            result = cv2.matchTemplate(
                processed_frame['gray'], 
                template_gray, 
                cv2.TM_CCOEFF_NORMED
            )
            
            # Encontrar coincidencia más fuerte
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= self.confidence_threshold:
                w, h = template_gray.shape[::-1]
                doors.append({
                    'x': max_loc[0],
                    'y': max_loc[1],
                    'w': w,
                    'h': h,
                    'direccion': direction,
                    'confidence': max_val
                })
        
        return doors
    
    def analyze_frame(self, frame):
        """
        Analiza un frame completo del juego
        
        Args:
            frame: Imagen capturada del juego
            
        Returns:
            Diccionario con toda la información detectada
        """
        start_time = time.time()
        
        # Preprocesar frame
        processed = self.preprocess_frame(frame)
        if processed is None:
            logger.warning("Frame nulo o inválido para análisis")
            return None
        
        # Detectar elementos
        player = self.detect_player(processed)
        enemies = self.detect_enemies(processed)
        items = self.detect_items(processed)
        doors = self.detect_doors(processed)
        
        # Crear resultado
        result = {
            'timestamp': time.time(),
            'frame_width': processed['resized'].shape[1],
            'frame_height': processed['resized'].shape[0],
            'player': player,
            'enemies': enemies,
            'items': items,
            'doors': doors,
            'processing_time': time.time() - start_time
        }
        
        return result


# Función auxiliar para dibujar resultados en un frame
def draw_detection_results(frame, detection_results):
    """
    Dibuja los resultados de detección en un frame para visualización
    
    Args:
        frame: Frame original
        detection_results: Resultados del detector
        
    Returns:
        Frame con anotaciones visuales
    """
    if frame is None or detection_results is None:
        return frame
        
    # Crear copia para no modificar el original
    output = frame.copy()
    
    # Redimensionar si es necesario
    if (frame.shape[1] != detection_results['frame_width'] or 
        frame.shape[0] != detection_results['frame_height']):
        scale_x = frame.shape[1] / detection_results['frame_width']
        scale_y = frame.shape[0] / detection_results['frame_height']
    else:
        scale_x, scale_y = 1.0, 1.0
    
    # Dibujar jugador
    if detection_results['player']:
        p = detection_results['player']
        x = int(p['x'] * scale_x)
        y = int(p['y'] * scale_y)
        w = int(p['w'] * scale_x)
        h = int(p['h'] * scale_y)
        cv2.rectangle(output, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(output, f"Player ({p['confidence']:.2f})", 
                   (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Dibujar enemigos
    for enemy in detection_results['enemies']:
        x = int(enemy['x'] * scale_x)
        y = int(enemy['y'] * scale_y)
        w = int(enemy['w'] * scale_x)
        h = int(enemy['h'] * scale_y)
        cv2.rectangle(output, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.putText(output, f"{enemy['tipo']} ({enemy['confidence']:.2f})", 
                   (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # Dibujar items
    for item in detection_results['items']:
        x = int(item['x'] * scale_x)
        y = int(item['y'] * scale_y)
        w = int(item['w'] * scale_x)
        h = int(item['h'] * scale_y)
        cv2.rectangle(output, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(output, f"{item['tipo']} ({item['confidence']:.2f})", 
                   (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    # Dibujar puertas
    for door in detection_results['doors']:
        x = int(door['x'] * scale_x)
        y = int(door['y'] * scale_y)
        w = int(door['w'] * scale_x)
        h = int(door['h'] * scale_y)
        cv2.rectangle(output, (x, y), (x+w, y+h), (255, 255, 0), 2)
        cv2.putText(output, f"Door {door['direccion']} ({door['confidence']:.2f})", 
                   (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    # Añadir info de tiempo de procesamiento
    cv2.putText(output, f"Time: {detection_results['processing_time']*1000:.1f}ms", 
               (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return output


# Función para prueba
def test_detector():
    """Función de prueba para el detector"""
    from .capture import GameCapture
    
    cap = GameCapture()
    detector = GameDetector()
    
    cap.start()
    
    try:
        for _ in range(100):  # Procesar 100 frames
            frame = cap.get_frame()
            if frame is not None:
                # Detectar elementos
                results = detector.analyze_frame(frame)
                
                # Visualizar resultados
                if results:
                    annotated_frame = draw_detection_results(frame, results)
                    cv2.imshow('Detección', annotated_frame)
                else:
                    cv2.imshow('Detección', frame)
                
                # Guardar un frame para verificar
                if _ == 50:
                    cv2.imwrite('deteccion_test.png', annotated_frame if results else frame)
                    print("Frame analizado guardado como 'deteccion_test.png'")
            
            # Esperar tecla ESC para salir
            if cv2.waitKey(30) == 27:
                break
            time.sleep(0.1)  # ~10 FPS para detección
    finally:
        cap.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_detector() 