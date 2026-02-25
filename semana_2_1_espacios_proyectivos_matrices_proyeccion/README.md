# Taller Transformaciones

Victor Saa

Fecha de entrega: 20/02/2026

## Descripción

Este proyecto es una aplicación para transformar y analizar modelos 3D.

## Implementaciónes

### Python

Se utilizó jupyter notebook para la implementación. Se carga el objeto y se extrae la geometría, vertices y caras. Se utiliza matplotlib para la visualización.

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
python -m ipykernel install --user --name semana4-visual --display-name "Python (semana4-visual)"
```

Abre `main.ipynb`, haz clic en el selector de kernel (arriba a la derecha) y elige **Python (semana4-visual)**.

### Three.js

Se utilizó three.js para la implementación. Se carga el objeto y se extrae la geometría, vertices y caras. Se utiliza three fiber para la visualización.

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

![Python](media/python-week-1.4.gif)
![Three.js](media/threejs-week-1.4.gif)

## Prompts utilizados

Aca me ayude de Antigravity para crear los frames del gif y la escena del cubo en threejs.

## Aprendizajes

Siento que aca hice algo de uso de lo que aprendi en algebra lineal, aunque solo fue aplicar las formulas de traslacion, rotacion y escala. Tambien familiarizarme mas con como operar con matrices en python.
