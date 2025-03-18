"""
Agente de Reinforcement Learning para controlar Isaac
"""

import numpy as np
import json
import time
import logging
import os
from pathlib import Path
import socket
import random
from threading import Thread, Event

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='agent.log'
)
logger = logging.getLogger("IsaacAgent")

class RLAgent:
    """Agente de aprendizaje por refuerzo para The Binding of Isaac"""
    
    def __init__(self, model_path=None, exploration_rate=0.2):
        """
        Inicializa el agente RL
        
        Args:
            model_path: Ruta al modelo pre-entrenado (si existe)
            exploration_rate: Tasa de exploración (epsilon)
        """
        self.model_path = model_path
        self.model = None
        self.exploration_rate = exploration_rate
        self.last_state = None
        self.last_action = None
        self.last_reward = 0
        self.episode_rewards = []
        self.current_episode_reward = 0
        self.total_steps = 0
        self.running = False
        self.stop_event = Event()
        
        # Acciones posibles
        self.actions = [
            # Movimiento
            {"type": "move", "direction": "up"},
            {"type": "move", "direction": "down"},
            {"type": "move", "direction": "left"},
            {"type": "move", "direction": "right"},
            # Disparo
            {"type": "shoot", "direction": "up"},
            {"type": "shoot", "direction": "down"},
            {"type": "shoot", "direction": "left"},
            {"type": "shoot", "direction": "right"},
            # Combinaciones
            {"type": "move_shoot", "move_direction": "up", "shoot_direction": "up"},
            {"type": "move_shoot", "move_direction": "down", "shoot_direction": "down"},
            {"type": "move_shoot", "move_direction": "left", "shoot_direction": "left"},
            {"type": "move_shoot", "move_direction": "right", "shoot_direction": "right"},
            # Uso de items
            {"type": "use_item"},
            # No hacer nada
            {"type": "none"}
        ]
        
        # Socket para comunicarse con el mod
        self.socket = None
        self.socket_port = 12345  # Puerto por defecto
        
        # Inicializar el modelo
        self._init_model()
    
    def _init_model(self):
        """Inicializa el modelo de RL"""
        if self.model_path and os.path.exists(self.model_path):
            try:
                # Aquí cargaríamos un modelo real (PyTorch, TensorFlow, etc.)
                logger.info(f"Cargando modelo RL desde {self.model_path}")
                # self.model = ... (carga del modelo)
                pass
            except Exception as e:
                logger.error(f"Error al cargar modelo RL: {e}")
                logger.info("Usando modelo básico por defecto")
        
        # Si no hay modelo, usar un modelo simple basado en reglas
        logger.info("Usando modelo de reglas simples")
    
    def _extract_features(self, state):
        """
        Extrae características relevantes del estado para el modelo
        
        Args:
            state: Estado del juego (resultado del detector)
            
        Returns:
            Vector de características numpy
        """
        if state is None:
            return np.zeros(10)  # Vector con ceros
        
        features = []
        
        # Posición del jugador
        player = state.get('player', None)
        if player:
            player_x = player['x'] / state['frame_width']  # Normalizado
            player_y = player['y'] / state['frame_height']  # Normalizado
        else:
            player_x, player_y = 0.5, 0.5  # Centro por defecto
        
        features.extend([player_x, player_y])
        
        # Número de enemigos
        n_enemies = len(state.get('enemies', []))
        features.append(min(n_enemies / 10.0, 1.0))  # Normalizado, máximo 10
        
        # Distancia al enemigo más cercano
        min_enemy_dist = 1.0
        if n_enemies > 0:
            distances = []
            for enemy in state['enemies']:
                enemy_x = enemy['x'] / state['frame_width']
                enemy_y = enemy['y'] / state['frame_height']
                dist = np.sqrt((player_x - enemy_x)**2 + (player_y - enemy_y)**2)
                distances.append(dist)
            min_enemy_dist = min(distances)
        
        features.append(min_enemy_dist)
        
        # Número de items
        n_items = len(state.get('items', []))
        features.append(min(n_items / 5.0, 1.0))  # Normalizado, máximo 5
        
        # Distancia al item más cercano
        min_item_dist = 1.0
        if n_items > 0:
            distances = []
            for item in state['items']:
                item_x = item['x'] / state['frame_width']
                item_y = item['y'] / state['frame_height']
                dist = np.sqrt((player_x - item_x)**2 + (player_y - item_y)**2)
                distances.append(dist)
            min_item_dist = min(distances)
        
        features.append(min_item_dist)
        
        # Información sobre puertas
        n_doors = len(state.get('doors', []))
        features.append(min(n_doors / 4.0, 1.0))  # Normalizado, máximo 4
        
        # Dirección a la puerta más cercana
        door_directions = [0, 0, 0, 0]  # [up, down, left, right]
        if n_doors > 0:
            for door in state['doors']:
                if door['direccion'] == 'up':
                    door_directions[0] = 1
                elif door['direccion'] == 'down':
                    door_directions[1] = 1
                elif door['direccion'] == 'left':
                    door_directions[2] = 1
                elif door['direccion'] == 'right':
                    door_directions[3] = 1
        
        features.extend(door_directions)
        
        return np.array(features)
    
    def _calculate_reward(self, current_state, previous_state, action):
        """
        Calcula la recompensa basada en estados y acción
        
        Args:
            current_state: Estado actual
            previous_state: Estado anterior
            action: Acción tomada
            
        Returns:
            Valor de recompensa
        """
        if current_state is None or previous_state is None:
            return 0
        
        reward = 0
        
        # Recompensa por supervivencia
        reward += 0.1
        
        # Verificar si el jugador se acercó a los items (positivo)
        if 'items' in current_state and 'items' in previous_state:
            prev_min_dist = float('inf')
            curr_min_dist = float('inf')
            
            if previous_state['player'] and len(previous_state['items']) > 0:
                prev_player_x = previous_state['player']['x'] / previous_state['frame_width']
                prev_player_y = previous_state['player']['y'] / previous_state['frame_height']
                
                for item in previous_state['items']:
                    item_x = item['x'] / previous_state['frame_width']
                    item_y = item['y'] / previous_state['frame_height']
                    dist = np.sqrt((prev_player_x - item_x)**2 + (prev_player_y - item_y)**2)
                    prev_min_dist = min(prev_min_dist, dist)
            
            if current_state['player'] and len(current_state['items']) > 0:
                curr_player_x = current_state['player']['x'] / current_state['frame_width']
                curr_player_y = current_state['player']['y'] / current_state['frame_height']
                
                for item in current_state['items']:
                    item_x = item['x'] / current_state['frame_width']
                    item_y = item['y'] / current_state['frame_height']
                    dist = np.sqrt((curr_player_x - item_x)**2 + (curr_player_y - item_y)**2)
                    curr_min_dist = min(curr_min_dist, dist)
            
            # Si se acercó a los items
            if curr_min_dist < prev_min_dist:
                reward += 0.5
            
            # Si desaparecieron items (los recogió)
            if len(previous_state['items']) > len(current_state['items']):
                reward += 2.0
        
        # Verificar si el jugador se alejó de los enemigos (positivo)
        if 'enemies' in current_state and 'enemies' in previous_state:
            prev_min_dist = float('inf')
            curr_min_dist = float('inf')
            
            if previous_state['player'] and len(previous_state['enemies']) > 0:
                prev_player_x = previous_state['player']['x'] / previous_state['frame_width']
                prev_player_y = previous_state['player']['y'] / previous_state['frame_height']
                
                for enemy in previous_state['enemies']:
                    enemy_x = enemy['x'] / previous_state['frame_width']
                    enemy_y = enemy['y'] / previous_state['frame_height']
                    dist = np.sqrt((prev_player_x - enemy_x)**2 + (prev_player_y - enemy_y)**2)
                    prev_min_dist = min(prev_min_dist, dist)
            
            if current_state['player'] and len(current_state['enemies']) > 0:
                curr_player_x = current_state['player']['x'] / current_state['frame_width']
                curr_player_y = current_state['player']['y'] / current_state['frame_height']
                
                for enemy in current_state['enemies']:
                    enemy_x = enemy['x'] / current_state['frame_width']
                    enemy_y = enemy['y'] / current_state['frame_height']
                    dist = np.sqrt((curr_player_x - enemy_x)**2 + (curr_player_y - enemy_y)**2)
                    curr_min_dist = min(curr_min_dist, dist)
            
            # Si se alejó de los enemigos
            if curr_min_dist > prev_min_dist:
                reward += 0.3
            
            # Si desaparecieron enemigos (los eliminó)
            if len(previous_state['enemies']) > len(current_state['enemies']):
                reward += 1.0
        
        # Penalización por chocar contra paredes (si no se mueve)
        if 'player' in current_state and 'player' in previous_state:
            prev_x = previous_state['player']['x']
            prev_y = previous_state['player']['y']
            curr_x = current_state['player']['x']
            curr_y = current_state['player']['y']
            
            # Si la acción fue de movimiento pero no se movió
            if action and 'type' in action and 'move' in action['type']:
                if abs(curr_x - prev_x) < 2 and abs(curr_y - prev_y) < 2:
                    reward -= 0.2
        
        return reward
    
    def get_action(self, state):
        """
        Decide la próxima acción basada en el estado actual
        
        Args:
            state: Estado actual del juego
            
        Returns:
            Acción a realizar
        """
        # Exploración (epsilon-greedy)
        if np.random.random() < self.exploration_rate:
            action = random.choice(self.actions)
            logger.debug("Acción aleatoria (exploración): {}".format(action))
            return action
        
        # Explotación (usar modelo o reglas simples)
        if self.model:
            # Usar el modelo para predecir la mejor acción
            features = self._extract_features(state)
            # action_idx = self.model.predict(features)
            # action = self.actions[action_idx]
            action = self._rule_based_action(state)
        else:
            # Sistema basado en reglas simple
            action = self._rule_based_action(state)
        
        logger.debug("Acción decidida: {}".format(action))
        return action
    
    def _rule_based_action(self, state):
        """
        Sistema simple basado en reglas para tomar decisiones
        
        Args:
            state: Estado actual del juego
            
        Returns:
            Acción a realizar
        """
        if state is None or 'player' not in state:
            return {"type": "none"}
        
        player = state['player']
        player_x = player['x'] / state['frame_width']  # Normalizado
        player_y = player['y'] / state['frame_height']  # Normalizado
        
        # Prioridad 1: Alejarse del enemigo más cercano
        if state.get('enemies') and len(state['enemies']) > 0:
            # Encontrar enemigo más cercano
            closest_enemy = None
            min_dist = float('inf')
            
            for enemy in state['enemies']:
                enemy_x = enemy['x'] / state['frame_width']
                enemy_y = enemy['y'] / state['frame_height']
                dist = np.sqrt((player_x - enemy_x)**2 + (player_y - enemy_y)**2)
                
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
            
            # Si hay un enemigo cercano, disparar hacia él y alejarse
            if closest_enemy and min_dist < 0.3:
                enemy_x = closest_enemy['x'] / state['frame_width']
                enemy_y = closest_enemy['y'] / state['frame_height']
                
                # Determinar dirección para disparar
                dx = enemy_x - player_x
                dy = enemy_y - player_y
                
                # Dirección opuesta para moverse (alejarse)
                move_dx = -dx
                move_dy = -dy
                
                # Decidir dirección de disparo (la más alineada con el enemigo)
                if abs(dx) > abs(dy):  # Más horizontal que vertical
                    shoot_dir = "right" if dx > 0 else "left"
                else:  # Más vertical que horizontal
                    shoot_dir = "down" if dy > 0 else "up"
                
                # Decidir dirección de movimiento (opuesta al enemigo)
                if abs(move_dx) > abs(move_dy):  # Más horizontal que vertical
                    move_dir = "left" if move_dx < 0 else "right"
                else:  # Más vertical que horizontal
                    move_dir = "up" if move_dy < 0 else "down"
                
                return {"type": "move_shoot", "move_direction": move_dir, "shoot_direction": shoot_dir}
        
        # Prioridad 2: Acercarse a items si no hay peligro inmediato
        if state.get('items') and len(state['items']) > 0:
            # Encontrar item más cercano
            closest_item = None
            min_dist = float('inf')
            
            for item in state['items']:
                item_x = item['x'] / state['frame_width']
                item_y = item['y'] / state['frame_height']
                dist = np.sqrt((player_x - item_x)**2 + (player_y - item_y)**2)
                
                if dist < min_dist:
                    min_dist = dist
                    closest_item = item
            
            # Si hay un item, moverse hacia él
            if closest_item:
                item_x = closest_item['x'] / state['frame_width']
                item_y = closest_item['y'] / state['frame_height']
                
                # Determinar dirección
                dx = item_x - player_x
                dy = item_y - player_y
                
                # Decidir dirección basada en la mayor diferencia
                if abs(dx) > abs(dy):  # Más horizontal que vertical
                    direction = "right" if dx > 0 else "left"
                else:  # Más vertical que horizontal
                    direction = "down" if dy > 0 else "up"
                
                return {"type": "move", "direction": direction}
        
        # Prioridad 3: Explorar la habitación (ir hacia puertas)
        if state.get('doors') and len(state['doors']) > 0:
            # Elegir una puerta aleatoria
            door = random.choice(state['doors'])
            return {"type": "move", "direction": door['direccion']}
        
        # Si no hay nada que hacer, moverse aleatoriamente
        direction = random.choice(["up", "down", "left", "right"])
        return {"type": "move", "direction": direction}
    
    def update(self, state, reward=None):
        """
        Actualiza el modelo con la nueva información
        
        Args:
            state: Nuevo estado
            reward: Recompensa explícita (opcional)
        """
        if self.last_state is not None and state is not None:
            # Calcular recompensa si no se proporciona
            if reward is None:
                reward = self._calculate_reward(state, self.last_state, self.last_action)
            
            # Actualizar estadísticas
            self.last_reward = reward
            self.current_episode_reward += reward
            self.total_steps += 1
            
            # Actualizar modelo (método dependerá de la implementación)
            if self.model:
                # Ejemplo para actualización del modelo
                # self.model.update(self._extract_features(self.last_state), 
                #                  self.last_action,
                #                  reward,
                #                  self._extract_features(state))
                pass
        
        # Guardar estado actual para la próxima iteración
        self.last_state = state
    
    def connect_to_mod(self, host='localhost', port=12345):
        """
        Conecta con el mod DEM_CV para enviar comandos
        
        Args:
            host: Host del servidor del mod
            port: Puerto del servidor
            
        Returns:
            True si la conexión se realizó correctamente
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.socket_port = port
            logger.info(f"Conectado al mod DEM_CV en {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Error al conectar con el mod: {e}")
            self.socket = None
            return False
    
    def send_action(self, action):
        """
        Envía una acción al mod
        
        Args:
            action: Acción a realizar
            
        Returns:
            True si se envió correctamente
        """
        if not self.socket:
            if not self.connect_to_mod():
                return False
        
        try:
            # Convertir a JSON
            action_json = json.dumps(action)
            # Enviar al mod
            self.socket.sendall(action_json.encode('utf-8'))
            logger.debug(f"Acción enviada: {action_json}")
            
            # La acción actual es ahora la última acción
            self.last_action = action
            
            return True
        except Exception as e:
            logger.error(f"Error al enviar acción: {e}")
            # Intentar reconectar
            self.socket = None
            return False
    
    def agent_loop(self, detector, delay=0.1):
        """
        Bucle principal del agente
        
        Args:
            detector: Instancia de GameDetector
            delay: Retardo entre iteraciones
        """
        logger.info("Iniciando bucle del agente")
        
        while not self.stop_event.is_set():
            try:
                # Obtener frame del detector
                detection_results = detector.last_detection
                
                if detection_results:
                    # Decidir acción basada en el estado
                    action = self.get_action(detection_results)
                    
                    # Enviar acción al mod
                    if action:
                        self.send_action(action)
                    
                    # Actualizar el modelo
                    self.update(detection_results)
                
                # Breve pausa para no saturar
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error en bucle del agente: {e}")
                time.sleep(1)  # Pausa más larga si hay error
    
    def start(self, detector, delay=0.1):
        """
        Inicia el agente en un hilo separado
        
        Args:
            detector: Instancia de GameDetector
            delay: Retardo entre iteraciones
        """
        if self.running:
            return
            
        self.running = True
        self.stop_event.clear()
        self.agent_thread = Thread(target=self.agent_loop, args=(detector, delay))
        self.agent_thread.daemon = True
        self.agent_thread.start()
        logger.info("Agente iniciado")
    
    def stop(self):
        """Detiene el agente"""
        self.stop_event.set()
        if hasattr(self, 'agent_thread') and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=1.0)
        
        # Cerrar socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        self.running = False
        logger.info("Agente detenido")
    
    def save_model(self, path=None):
        """
        Guarda el modelo entrenado
        
        Args:
            path: Ruta donde guardar el modelo
        """
        if not self.model:
            logger.warning("No hay modelo para guardar")
            return False
            
        try:
            save_path = path or self.model_path or "agent_model.pkl"
            # Aquí guardamos el modelo según su tipo
            # self.model.save(save_path)
            logger.info(f"Modelo guardado en {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar modelo: {e}")
            return False


# Función para test
def test_agent():
    """Función de prueba para el agente"""
    from .detector import GameDetector
    from .capture import GameCapture
    
    cap = GameCapture()
    detector = GameDetector()
    agent = RLAgent()
    
    # Simular un detector con last_detection
    class MockDetector:
        def __init__(self):
            self.last_detection = None
    
    mock_detector = MockDetector()
    
    cap.start()
    
    try:
        for _ in range(100):  # Procesar 100 frames
            frame = cap.get_frame()
            if frame is not None:
                # Detectar elementos
                detection_results = detector.analyze_frame(frame)
                
                # Actualizar el detector mock
                mock_detector.last_detection = detection_results
                
                # Obtener acción del agente
                action = agent.get_action(detection_results)
                print(f"Acción: {action}")
                
                # Actualizar el agente
                agent.update(detection_results)
                
                # Simular envío de acción
                print(f"Enviando acción: {json.dumps(action)}")
                
                # Visualizar frame
                if detection_results:
                    from .detector import draw_detection_results
                    annotated_frame = draw_detection_results(frame, detection_results)
                    cv2.imshow('Agente RL', annotated_frame)
                else:
                    cv2.imshow('Agente RL', frame)
            
            # Esperar tecla ESC para salir
            if cv2.waitKey(30) == 27:
                break
            time.sleep(0.1)
    finally:
        cap.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_agent() 