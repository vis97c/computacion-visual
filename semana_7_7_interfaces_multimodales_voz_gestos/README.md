# Taller Interfaces Multimodales: Uniendo Voz y Gestos

Victor Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

Fecha de entrega: 25/04/2026

## Descripción

Fusionar gestos (detectados con MediaPipe) y comandos de voz para realizar acciones compuestas dentro de una interfaz visual. Este taller introduce los fundamentos de los sistemas de interacción multimodal, combinando dos formas de entrada humana para enriquecer la experiencia de control.

## Implementaciónes

### Python

Se utilizó jupyter notebook para la implementación, la librería `mediapipe` fue la más importante, luego `pygame` para la visualización y `speech_recognition` para el reconocimiento de voz.

```bash
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Jupyter en el editor (VS Code, Antigravity, etc.)

```bash
# Registrar el kernel para Jupyter
python -m ipykernel install --user --name semana7-interfaz-multimodal --display-name "Python (semana7-interfaz-multimodal)"
```

Abre `main.ipynb`, haz clic en el selector de kernel (arriba a la derecha) y elige **Python (semana7-interfaz-multimodal)**.

## IA

IDE, prompts y autocompletado: Antigravity

## Resultados visuales

![Video reconocimiento voz y gestos](media/week_7_7a_python.mp4)
![Video reconocimiento voz y gestos, puño cerrado](media/week_7_7b_python.mp4)
![Video reconocimiento voz y gestos, interacciones](media/week_7_7c_python.mp4)

## Prompts utilizados

Aca me ayude de Antigravity construir la escena base del sistema solar.

## Aprendizajes

Aca pude usar mediapipe para detectar gestos y comandos de voz para realizar acciones compuestas dentro de una interfaz visual. Hizo falta usar un api para la voz y un set de features de la mano para poder detectar otros gestos, pero fue muy interesante poder combinar dos formas de entrada humana para enriquecer la experiencia de control.

## Estructura del proyecto

```
semana_7_7_interfaces_multimodales_voz_gestos/
├── python/
├── media/ # Imágenes, videos, GIFs de resultados
└── README.md
```

---

## Referencias

Lista las fuentes, tutoriales, documentación o papers consultados durante el desarrollo:

- Documentación oficial de Unity: https://docs.unity3d.com/Manual/
- Tutorial de React Three Fiber: https://docs.pmnd.rs/react-three-fiber/
- Leva (React UI controls): https://leva.pmnd.rs/

---
