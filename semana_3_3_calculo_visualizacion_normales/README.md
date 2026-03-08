# Taller Cálculo y Visualización de Normales

Victor Saa y

Fecha de entrega: 09/03/2026

## Descripción

Calcular vectores normales de superficies 3D y utilizarlos para iluminación correcta. Comprender la diferencia entre normales de vértices y caras, smooth shading vs flat shading, y visualizar normales para debugging.

## Implementaciónes

### Python

DESCRIBIR IMPLEMENTACIÓN EN PYTHON

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
python -m ipykernel install --user --name semana3-3-visual --display-name "Python (semana3-3-visual)"
```

Abre `main.ipynb`, haz clic en el selector de kernel (arriba a la derecha) y elige **Python (semana3-3-visual)**.

### Unity

DESCRIBIR IMPLEMENTACIÓN EN UNITY

### Three.js

Se utilizó three.js para la implementación. Se generó una geometría procedural y se calcularon las normales en tiempo real. Se uso un helper para visualizar las normales y leva para controlar los parámetros de la escena.

```bash
cd threejs

# Con yarn
yarn install
yarn dev

# Con npm
npm install
npm run dev
```

## IA

IDE, prompts y autocompletado: Antigravity

## Resultados visuales

![Python](media/python-week-3.3.gif)
![Unity](media/unity-week-3.3.gif)
![Three.js](media/week-3-3-threejs.gif)

## Prompts utilizados

Aca me ayude de Antigravity para construir la escena, la geometria procedural e integrar el helper de normales.

## Aprendizajes

Aqui aprendi a trabajar con geometrias procedurales y a calcular normales en tiempo real sobre geomtrias dinamicas

## Contribuciones grupales (si aplica)

Victor Saa: Desarrollo Three.js

## Estructura del proyecto

```
semana_3_3_calculo_visualizacion_normales/
├── python/
├── unity/
├── threejs/
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
