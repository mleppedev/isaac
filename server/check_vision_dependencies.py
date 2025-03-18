#!/usr/bin/env python
"""
Script para verificar las dependencias del sistema de visión por computadora
"""

import sys
import os
import importlib.util
import subprocess
import platform
import time

def check_module(module_name):
    """Verifica si un módulo está instalado y su versión"""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"❌ Módulo {module_name} no encontrado")
        return False
    
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'desconocida')
        print(f"✅ Módulo {module_name} instalado (versión: {version})")
        return True
    except ImportError:
        print(f"❌ Error al importar {module_name}")
        return False

def check_path_inclusion():
    """Verifica si el directorio del proyecto está en el path de Python"""
    script_path = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.dirname(script_path)
    
    if project_path in sys.path:
        print(f"✅ Directorio del proyecto en el path: {project_path}")
    else:
        print(f"❌ Directorio del proyecto NO está en el path: {project_path}")
        print("   Esto puede causar problemas de importación de módulos personalizados")

def check_vision_module():
    """Verifica si el módulo de visión está disponible y correctamente instalado"""
    try:
        # Intentar importar directamente
        try:
            import vision_module
            print(f"✅ Módulo vision_module importado directamente")
            return True
        except ImportError:
            print("❌ No se pudo importar vision_module directamente")
        
        # Intentar importar desde la raíz del proyecto
        script_path = os.path.dirname(os.path.abspath(__file__))
        project_path = os.path.dirname(script_path)
        
        if project_path not in sys.path:
            sys.path.append(project_path)
            print(f"✅ Directorio del proyecto añadido al path: {project_path}")
        
        try:
            import vision_module
            print(f"✅ Módulo vision_module importado después de añadir el path")
            return True
        except ImportError:
            print("❌ No se pudo importar vision_module incluso después de añadir el path")
        
        # Verificar si el directorio existe
        vision_dir = os.path.join(project_path, 'vision_module')
        if os.path.isdir(vision_dir):
            print(f"✅ Directorio vision_module encontrado: {vision_dir}")
            
            # Verificar archivos
            required_files = ['__init__.py', 'main.py', 'capture.py', 'detector.py', 'agent.py']
            missing_files = []
            
            for file in required_files:
                file_path = os.path.join(vision_dir, file)
                if not os.path.isfile(file_path):
                    missing_files.append(file)
            
            if missing_files:
                print(f"❌ Faltan archivos en el módulo: {', '.join(missing_files)}")
            else:
                print("✅ Todos los archivos requeridos están presentes")
        else:
            print(f"❌ Directorio vision_module no encontrado: {vision_dir}")
        
        return False
    except Exception as e:
        print(f"❌ Error al verificar el módulo vision_module: {str(e)}")
        return False

def check_directories():
    """Verifica si los directorios necesarios existen"""
    script_path = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.dirname(script_path)
    
    dirs_to_check = [
        os.path.join(script_path, 'static', 'img'),
        os.path.join(script_path, 'static', 'vision_output'),
        os.path.join(project_path, 'vision_module', 'templates')
    ]
    
    for dir_path in dirs_to_check:
        if os.path.isdir(dir_path):
            print(f"✅ Directorio encontrado: {dir_path}")
        else:
            print(f"❌ Directorio no encontrado: {dir_path}")
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"  ✅ Directorio creado: {dir_path}")
            except Exception as e:
                print(f"  ❌ Error al crear directorio: {str(e)}")

def check_system_info():
    """Muestra información del sistema"""
    print(f"Sistema operativo: {platform.system()} {platform.release()}")
    print(f"Versión de Python: {sys.version}")
    print(f"Directorio de trabajo: {os.getcwd()}")
    print(f"Directorio del script: {os.path.dirname(os.path.abspath(__file__))}")

def run_simple_cv_test():
    """Ejecuta una prueba simple de OpenCV"""
    try:
        import cv2
        import numpy as np
        
        # Crear una imagen simple
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        img[:] = (200, 200, 200)  # Gris claro
        
        # Dibujar un círculo
        cv2.circle(img, (150, 150), 100, (0, 0, 255), 5)
        
        # Guardar la imagen
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'vision_output')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'test_circle.jpg')
        cv2.imwrite(output_path, img)
        
        print(f"✅ Prueba de OpenCV exitosa, imagen guardada en: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error en la prueba de OpenCV: {str(e)}")
        return False

def run_direct_vision_test():
    """Intenta ejecutar una prueba directa del módulo de visión"""
    try:
        script_path = os.path.dirname(os.path.abspath(__file__))
        project_path = os.path.dirname(script_path)
        vision_module_path = os.path.join(project_path, 'vision_module', 'main.py')
        
        if os.path.exists(vision_module_path):
            print(f"Ejecutando prueba directa del módulo de visión...")
            # Ejecutar en un subproceso para no bloquear
            process = subprocess.Popen([sys.executable, vision_module_path, '--no-visualization'])
            
            # Esperar un poco para ver si se inicia
            time.sleep(3)
            
            # Verificar si el proceso aún está en ejecución
            returncode = process.poll()
            if returncode is None:
                print("✅ El módulo de visión se está ejecutando correctamente")
                # Terminarlo suavemente
                process.terminate()
                return True
            else:
                print(f"❌ El módulo de visión se detuvo con código: {returncode}")
                return False
        else:
            print(f"❌ No se encontró el archivo principal del módulo: {vision_module_path}")
            return False
    except Exception as e:
        print(f"❌ Error al ejecutar prueba directa: {str(e)}")
        return False

def main():
    """Función principal"""
    print("="*80)
    print("VERIFICACIÓN DE DEPENDENCIAS DEL SISTEMA DE VISIÓN POR COMPUTADORA")
    print("="*80)
    
    print("\n--- INFORMACIÓN DEL SISTEMA ---")
    check_system_info()
    
    print("\n--- VERIFICACIÓN DE RUTAS ---")
    check_path_inclusion()
    check_directories()
    
    print("\n--- VERIFICACIÓN DE MÓDULOS BÁSICOS ---")
    check_module('numpy')
    check_module('cv2')
    check_module('pywin32') or check_module('win32gui')
    check_module('json')
    
    print("\n--- VERIFICACIÓN DE MÓDULOS OPCIONALES ---")
    check_module('torch')
    check_module('torchvision')
    
    print("\n--- VERIFICACIÓN DEL MÓDULO DE VISIÓN ---")
    check_vision_module()
    
    print("\n--- PRUEBA SIMPLE DE OPENCV ---")
    run_simple_cv_test()
    
    print("\n--- PRUEBA DIRECTA DEL MÓDULO DE VISIÓN ---")
    # Esta prueba puede bloquear temporalmente, se comenta por defecto
    # run_direct_vision_test()
    
    print("\n="*80)
    print("VERIFICACIÓN COMPLETADA")
    print("="*80)

if __name__ == "__main__":
    main() 