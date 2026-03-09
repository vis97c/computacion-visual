# Taller Cálculo y Visualización de Normales

Victor Saa, Juan Jose Alvarez, Jose Arturo Herrera Rivera, Juan Pablo Correa, Manuel Santiago Mori Ardila

Fecha de entrega: 09/03/2026

## Descripción

Calcular vectores normales de superficies 3D y utilizarlos para iluminación correcta. Comprender la diferencia entre normales de vértices y caras, smooth shading vs flat shading, y visualizar normales para debugging.

## Implementaciónes

### Python

La implementación en Python se enfoca en el procesamiento de mallas 3D utilizando **NumPy** para cálculos vectoriales de alto rendimiento y **Trimesh** para la carga y gestión de archivos `.obj`.

#### Detalles Técnicos:
- **Cálculo de Normales de Caras**: Se implementó manualmente mediante el producto cruz de los vectores de las aristas de cada triángulo:
  $$\vec{n} = \frac{(B-A) \times (C-A)}{\|(B-A) \times (C-A)\|}$$
- **Validación de Orientación**: Se verifica que las normales apunten hacia "afuera" comparando el producto punto entre la normal y el vector que va desde el centroide de la malla hacia el centroide de la cara.
- **Normales de Vértices**: Se calculan promediando las normales de las caras adyacentes a cada vértice, permitiendo la implementación de **Smooth Shading**.
- **Análisis Estadístico**: El script genera histogramas de la intensidad de iluminación (Lambertian) para comparar la distribución de luz entre sombreado plano (*Flat*) y suavizado (*Smooth*).

#### Snippets de Código:

```python
# Cálculo manual de normales de caras
def compute_face_normals(vertices, faces):
    A = vertices[faces[:, 0]]
    B = vertices[faces[:, 1]]
    C = vertices[faces[:, 2]]

    v1 = B - A
    v2 = C - A

    cross = np.cross(v1, v2)
    norms = np.linalg.norm(cross, axis=1, keepdims=True)
    
    # Evitar división por cero
    safe_norms = np.where(norms == 0, 1e-10, norms)
    normals = cross / safe_norms
    return normals

# Validación de orientación (hacia afuera)
def check_outward_normals(vertices, faces, face_normals):
    centroids_f = (vertices[faces[:, 0]] + vertices[faces[:, 1]] + vertices[faces[:, 2]]) / 3.0
    mesh_centroid = vertices.mean(axis=0)
    outward_vec = centroids_f - mesh_centroid
    dot = np.sum(outward_vec * face_normals, axis=1)
    return (dot > 0).sum() # Conteo de normales correctas
```


### Unity

Se implementó un componente en C# encargado de extraer los datos del MeshFilter. El núcleo del código utiliza un bucle que recorre el arreglo de vértices y transforma sus coordenadas de Espacio de Objeto a Espacio de Mundo para una representación precisa.

Para complementar la visualización de líneas, se desarrolló un Shader personalizado utilizando la herramienta visual Shader Graph de Unity. El objetivo fue crear un material de diagnóstico que permitiera inspeccionar la orientación de todas las caras del modelo de forma simultánea.

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

### Python
![Normales de Caras](media/Normales%20de%20Caras.png)
*Visualización de vectores normales calculados sobre el modelo.*

![Validación de Anomalías](media/Anomalias%20en%20normales.png)
*Mapa de calor mostrando errores de magnitud y orientación.*

![Análisis Estadístico](media/Analisis%20Estadistico%20Intensidades.png)
*Comparativa de intensidades Lambertianas: Flat vs Smooth Shading.*

### Unity
![Unity](media/week-3-3-unity.gif)

### Three.js
![Three.js](media/week-3-3-threejs.gif)



## Prompts utilizados

Aca me ayude de Antigravity para construir la escena, la geometria procedural e integrar el helper de normales.

## Aprendizajes

Aqui aprendi a trabajar con geometrias procedurales y a calcular normales en tiempo real sobre geomtrias dinamicas

## Contribuciones grupales (si aplica)

Victor Saa: Desarrollo Three.js
Juan Jose Alvarez: Desarrollo Python

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
