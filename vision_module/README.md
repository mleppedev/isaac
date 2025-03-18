# Módulo de Visión por Computadora para The Binding of Isaac

Este módulo proporciona un sistema de visión por computadora integrado con reinforcement learning para controlar el juego The Binding of Isaac de forma autónoma.

## Características

- **Captura de pantalla en tiempo real**: Detecta la ventana del juego y captura frames a alta frecuencia.
- **Detección de elementos**: Reconoce al jugador, enemigos, items y puertas en la pantalla.
- **Agente de RL**: Toma decisiones basadas en lo que "ve" en pantalla utilizando un sistema basado en reglas o un modelo entrenado.
- **Entrenamiento interactivo**: Interfaz para capturar templates y entrenar el sistema de detección.
- **Integración con el mod DEM_CV**: Envía comandos directamente al juego para controlarlo.

## Requisitos

- Python 3.8 o superior
- OpenCV
- PyTorch (para el modelo de RL)
- PyWin32 (para captura de pantalla en Windows)
- The Binding of Isaac: Repentance con el mod DEM_CV instalado

## Instalación

1. Asegúrate de tener instalado el mod DEM_CV en tu juego.
2. Instala las dependencias con pip:
   ```
   pip install -r server/requirements.txt
   ```

## Uso

### Modo Interfaz Web

El sistema se integra con la aplicación web existente. Para utilizarlo:

1. Inicia el servidor con `python server/app.py`
2. Abre un navegador y navega a `http://localhost:5000`
3. Ve a la sección "Control del Personaje"
4. Utiliza el panel "Sistema de Visión por Computadora" para:
   - Iniciar/detener el sistema
   - Ajustar la tasa de exploración
   - Capturar templates para entrenar el detector

### Modo Línea de Comandos

También puedes usar el sistema directamente desde la línea de comandos:

```
python -m vision_module.main [opciones]
```

Opciones disponibles:
- `--no-visualization`: Desactiva la ventana de visualización
- `--training`: Ejecuta en modo entrenamiento
- `--frequency <valor>`: Establece la frecuencia de detección en segundos
- `--exploration <valor>`: Establece la tasa de exploración del agente
- `--model <ruta>`: Especifica la ruta a un modelo pre-entrenado

## Entrenamiento del Sistema

Para mejorar la precisión del detector:

1. Inicia el juego y el sistema de visión
2. Usa la función "Capturar" en la interfaz web para guardar templates de:
   - Jugador: Captura al personaje en diferentes poses
   - Enemigos: Captura cada tipo de enemigo
   - Items: Captura diferentes tipos de items
   - Puertas: Captura puertas en las cuatro direcciones

## Estructura del Módulo

- `capture.py`: Sistema de captura de pantalla
- `detector.py`: Sistema de detección de elementos
- `agent.py`: Agente de reinforcement learning
- `main.py`: Integración de todos los componentes
- `templates/`: Directorio que almacena templates para la detección

## Funcionamiento Técnico

El sistema funciona siguiendo estos pasos:

1. La clase `GameCapture` captura frames continuamente de la ventana del juego
2. El `GameDetector` analiza cada frame para identificar elementos
3. El `RLAgent` toma decisiones basadas en los elementos detectados
4. Las decisiones se convierten en comandos enviados al mod DEM_CV
5. El mod aplica estos comandos directamente como inputs al juego

## Solución de Problemas

- **No se detecta la ventana del juego**: Asegúrate de que el juego esté en ejecución y visible
- **Errores de captura**: Verifica que estés ejecutando el sistema con permisos adecuados
- **Baja precisión de detección**: Añade más templates o ajusta el umbral de confianza en `detector.py`
- **El mod no recibe comandos**: Verifica que el mod DEM_CV esté instalado correctamente

## Diferencias con el Mod DEM Original

El mod DEM original está diseñado para recopilar datos del juego, mientras que DEM_CV está optimizado para recibir comandos desde el sistema de visión por computadora.

## Limitaciones Actuales

- La detección se basa principalmente en template matching, lo que puede ser sensible a cambios visuales
- El agente base utiliza un sistema de reglas simple, el modelo completo de RL requiere entrenamiento
- La identificación de enemigos específicos requiere templates para cada tipo 