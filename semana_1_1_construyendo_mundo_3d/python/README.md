# Visualización de malla 3D con Python

Carga un archivo `.obj` y lo visualiza en 3D usando `matplotlib`, diferenciando con colores los vértices, aristas y caras. También muestra información estructural del modelo (número de vértices, aristas y caras).

## Configuración del entorno

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
python -m ipykernel install --user --name semana1-visual --display-name "Python (semana1-visual)"
```

Abre `main.ipynb`, haz clic en el selector de kernel (arriba a la derecha) y elige **Python (semana1-visual)**.
