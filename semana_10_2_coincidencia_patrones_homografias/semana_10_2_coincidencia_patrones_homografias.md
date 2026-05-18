
# Taller - Coincidencia de Patrones y Homografías

## Objetivo del taller

Realizar matching (coincidencia) de características entre múltiples imágenes y calcular transformaciones homográficas para alinear imágenes, detectar objetos y crear panoramas. Aplicar algoritmos de matching robusto con RANSAC.

---

## Actividades por entorno

Este taller se desarrolla principalmente en **Python** con OpenCV.

---

### Python (OpenCV y NumPy)

**Herramientas necesarias:**
- `opencv-python`
- `opencv-contrib-python`
- `numpy`
- `matplotlib`

**Pasos a implementar:**

1. **Feature Matching con BFMatcher:**
   - Cargar dos imágenes relacionadas (mismo objeto desde diferentes ángulos)
   - Detectar keypoints y descriptores con SIFT u ORB
   - Crear BFMatcher (Brute Force Matcher)
   - Realizar matching: `bf.match()` o `bf.knnMatch()`
   - Visualizar matches con `cv2.drawMatches()`

2. **Feature Matching con FLANN:**
   - Configurar FLANN (Fast Library for Approximate Nearest Neighbors)
   - Parámetros para SIFT: index_params con algoritmo KDTREE
   - Parámetros para ORB: index_params con algoritmo LSH
   - Realizar matching y comparar velocidad con BFMatcher
   - Filtrar buenos matches con ratio test de Lowe

3. **Cálculo de Homografía:**
   - Extraer puntos de los buenos matches
   - Calcular matriz de homografía con `cv2.findHomography()`
   - Usar método RANSAC para robustez
   - Visualizar inliers vs outliers
   - Analizar la matriz H (3x3)

4. **Detección de Objetos:**
   - Definir imagen de objeto a buscar (template)
   - Buscar objeto en imagen de escena
   - Calcular homografía entre template y región detectada
   - Dibujar bounding box del objeto en la escena
   - Probar con diferentes objetos y escenas

5. **Image Stitching (Panorama):**
   - Cargar 2-3 imágenes con solapamiento
   - Detectar features en todas las imágenes
   - Hacer matching entre pares consecutivos
   - Calcular homografías para alinear imágenes
   - Aplicar warping: `cv2.warpPerspective()`
   - Combinar imágenes en un panorama

6. **Evaluación de calidad:**
   - Contar número de matches encontrados
   - Calcular porcentaje de inliers en RANSAC
   - Medir tiempo de procesamiento
   - Evaluar calidad visual del resultado

**Bonus:**
- Implementar blending suave entre imágenes en el panorama
- Crear panorama de 360 grados
- Detectar múltiples instancias del mismo objeto

---

## Entrega

Crear carpeta con el nombre: `semana_10_2_coincidencia_patrones_homografias` en tu repositorio de GitLab.

Dentro de la carpeta, crear la siguiente estructura:

```
semana_10_2_coincidencia_patrones_homografias/
├── python/
├── media/  # Imágenes, videos, GIFs de resultados
└── README.md
```

### Requisitos del README.md

El archivo `README.md` debe contener obligatoriamente:

1. **Título del taller**: Taller Coincidencia Patrones Homografias
2. **Nombre del estudiante**
3. **Fecha de entrega**
4. **Descripción breve**: Explicación del objetivo y lo desarrollado
5. **Implementaciones**: Descripción de cada implementación realizada por entorno
6. **Resultados visuales**:
   - **Imágenes, videos o GIFs** que muestren el funcionamiento
   - Deben estar en la carpeta `media/` y referenciados en el README
   - Mínimo 2 capturas/GIFs por implementación
7. **Código relevante**: Snippets importantes o enlaces al código
8. **Prompts utilizados**: Descripción de prompts usados (si aplicaron IA generativa)
9. **Aprendizajes y dificultades**: Reflexión personal sobre el proceso

### Estructura de carpetas

- Cada entorno de desarrollo debe tener su propia subcarpeta (`python/`, `unity/`, `threejs/`, etc.)
- La carpeta `media/` debe contener todos los recursos visuales (imágenes, GIFs, videos)
- Nombres de archivos en minúsculas, sin espacios (usar guiones bajos o guiones medios)

---

## Criterios de evaluación

- Cumplimiento de los objetivos del taller
- Código limpio, comentado y bien estructurado
- README.md completo con toda la información requerida
- Evidencias visuales claras (imágenes/GIFs/videos en carpeta `media/`)
- Repositorio organizado siguiendo la estructura especificada
- Commits descriptivos en inglés
- Nombre de carpeta correcto: `semana_10_2_coincidencia_patrones_homografias`
- Implementación correcta de matching con BFMatcher y FLANN
- Cálculo correcto de homografías con RANSAC
- Panorama generado con buena calidad visual
- Detección exitosa de objetos en escenas
