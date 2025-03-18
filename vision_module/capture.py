"""
Módulo de captura de pantalla para The Binding of Isaac
"""

import numpy as np
import cv2
import time
import win32gui
import win32ui
import win32con
import win32api
from threading import Thread, Event
from queue import Queue
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='vision_capture.log'
)
logger = logging.getLogger("IsaacCapture")

class GameCapture:
    """Clase para capturar la pantalla del juego The Binding of Isaac"""
    
    def __init__(self, window_title="The Binding of Isaac: Repentance", capture_rate=30):
        """
        Inicializa el capturador de pantalla
        
        Args:
            window_title: Título de la ventana del juego
            capture_rate: Frames por segundo a capturar
        """
        self.window_title = window_title
        self.capture_rate = capture_rate
        self.frame_time = 1.0 / capture_rate
        self.running = False
        self.frame_queue = Queue(maxsize=2)  # Solo mantener los frames más recientes
        self.stop_event = Event()
        self.last_frame = None
        self.window_handle = None
        
    def find_game_window(self):
        """Encuentra el handle de la ventana del juego"""
        self.window_handle = win32gui.FindWindow(None, self.window_title)
        if not self.window_handle:
            # Búsqueda parcial si no encontramos la ventana exacta
            def callback(hwnd, windows):
                if self.window_title.lower() in win32gui.GetWindowText(hwnd).lower():
                    windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(callback, windows)
            
            if windows:
                self.window_handle = windows[0]
                logger.info(f"Ventana encontrada por búsqueda parcial: {win32gui.GetWindowText(self.window_handle)}")
            else:
                logger.error(f"No se pudo encontrar la ventana del juego: {self.window_title}")
                return False
                
        logger.info(f"Ventana del juego encontrada: {self.window_handle}")
        return True
        
    def capture_window(self):
        """Captura un frame de la ventana del juego"""
        if not self.window_handle:
            if not self.find_game_window():
                return None
        
        try:
            # Obtener dimensiones de la ventana
            left, top, right, bottom = win32gui.GetClientRect(self.window_handle)
            width = right - left
            height = bottom - top
            
            # Convertir coordenadas de cliente a pantalla
            left, top = win32gui.ClientToScreen(self.window_handle, (left, top))
            right, bottom = win32gui.ClientToScreen(self.window_handle, (right, bottom))
            
            # Crear el contexto de dispositivo
            wDC = win32gui.GetWindowDC(self.window_handle)
            dcObj = win32ui.CreateDCFromHandle(wDC)
            cDC = dcObj.CreateCompatibleDC()
            
            # Crear bitmap
            dataBitmap = win32ui.CreateBitmap()
            dataBitmap.CreateCompatibleBitmap(dcObj, width, height)
            cDC.SelectObject(dataBitmap)
            
            # Copiar la pantalla al bitmap
            cDC.BitBlt((0, 0), (width, height), dcObj, (0, 0), win32con.SRCCOPY)
            
            # Convertir a numpy array
            signedIntsArray = dataBitmap.GetBitmapBits(True)
            img = np.frombuffer(signedIntsArray, dtype='uint8')
            img.shape = (height, width, 4)
            
            # Limpiar y liberar recursos
            dcObj.DeleteDC()
            cDC.DeleteDC()
            win32gui.ReleaseDC(self.window_handle, wDC)
            win32gui.DeleteObject(dataBitmap.GetHandle())
            
            # Convertir de BGRA a BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
            
        except Exception as e:
            logger.error(f"Error al capturar ventana: {e}")
            return None
    
    def capture_thread(self):
        """Thread principal para la captura continua"""
        logger.info("Iniciando thread de captura")
        last_capture_time = 0
        
        while not self.stop_event.is_set():
            current_time = time.time()
            elapsed = current_time - last_capture_time
            
            # Capturar a la tasa especificada
            if elapsed >= self.frame_time:
                frame = self.capture_window()
                if frame is not None:
                    # Actualizar cola y último frame
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame)
                    else:
                        try:
                            # Eliminar el frame más antiguo
                            _ = self.frame_queue.get_nowait()
                            self.frame_queue.put(frame)
                        except:
                            pass
                            
                    self.last_frame = frame
                last_capture_time = current_time
            
            # Pequeña pausa para no saturar la CPU
            time.sleep(0.001)
        
        logger.info("Thread de captura detenido")
    
    def start(self):
        """Inicia la captura de pantalla en un thread separado"""
        if self.running:
            return
            
        self.running = True
        self.stop_event.clear()
        self.capture_thread = Thread(target=self.capture_thread)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        logger.info("Captura iniciada")
    
    def stop(self):
        """Detiene la captura de pantalla"""
        self.stop_event.set()
        if hasattr(self, 'capture_thread') and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        self.running = False
        logger.info("Captura detenida")
    
    def get_frame(self):
        """Obtiene el último frame capturado"""
        if not self.running:
            return self.capture_window()
            
        try:
            return self.frame_queue.get_nowait()
        except:
            return self.last_frame


# Función para prueba
def test_capture():
    """Función de prueba para la captura de pantalla"""
    cap = GameCapture()
    cap.start()
    
    try:
        for _ in range(100):  # Capturar 100 frames
            frame = cap.get_frame()
            if frame is not None:
                # Mostrar la imagen
                cv2.imshow('Captura', frame)
                
                # Guardar un frame para verificar
                if _ == 50:
                    cv2.imwrite('captura_test.png', frame)
                    print("Frame guardado como 'captura_test.png'")
            
            # Esperar tecla ESC para salir
            if cv2.waitKey(30) == 27:
                break
            time.sleep(0.03)  # ~30 FPS
    finally:
        cap.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    test_capture() 