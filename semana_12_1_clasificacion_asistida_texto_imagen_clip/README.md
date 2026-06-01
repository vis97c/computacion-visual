# Taller Clasificacion Asistida Texto Imagen Clip

**Curso:** Computación Visual  
**Estudiante:** [Nombre del Estudiante]  
**Fecha de Entrega:** 1 de Junio, 2026  

---

## 1. Descripción Breve
Este taller explora y compara el paradigma de clasificación **Zero-Shot** utilizando **OpenAI CLIP** contra el enfoque de **Transfer Learning Estático** tradicional (extracción de características con **ResNet18** preentrenada en ImageNet y clasificación mediante **SVM Lineal** y **k-NN**). 

Para evaluar de forma retadora la clasificación visual asistida por texto, elegimos el contexto de **Estilos de Arte (Art Styles)**, el cual se caracteriza por ser altamente semántico, subjetivo y abstracto (no dependiente de un único objeto físico). Evaluamos tres clases artísticas diferenciadas:
1. **Renacimiento (Renaissance)**: Retratos y figuras humanas al óleo clásicos con anatomía exacta, iluminación suave (*sfumato*) y tenebrismo.
2. **Impresionismo (Impressionism)**: Paisajes y escenas al aire libre caracterizados por pinceladas sueltas visibles, gran viveza de color y énfasis dramático en la luz y la atmósfera.
3. **Cubismo (Cubism)**: Obras abstractas y fragmentadas donde los sujetos (músicos, bodegones) se descomponen en planos y formas geométricas tridimensionales vistas desde múltiples ángulos simultáneamente.

Desarrollamos un mini-dataset sintético de **6 pinturas de altísima calidad** (2 por cada clase) generadas por IA para poner a prueba los límites de ambos paradigmas.

---

## 2. Estructura de la Carpeta del Entregable
La estructura del repositorio para este taller es la siguiente:
```
semana_12_1_clasificacion_asistida_texto_imagen_clip/
├── python/
│   ├── dataset/
│   │   ├── cubism_1.png
│   │   ├── cubism_2.png
│   │   ├── impressionism_1.png
│   │   ├── impressionism_2.png
│   │   ├── renaissance_1.png
│   │   └── renaissance_2.png
│   ├── requirements.txt
│   └── taller_clip_resnet.ipynb
├── media/
│   ├── cubism_1_clip_prediction.png
│   ├── cubism_2_clip_prediction.png
│   ├── dataset_grid.png
│   ├── impressionism_1_clip_prediction.png
│   ├── impressionism_2_clip_prediction.png
│   ├── pca_resnet_features.png
│   ├── renaissance_1_clip_prediction.png
│   └── renaissance_2_clip_prediction.png
└── README.md
```

---

## 3. Implementación en Python

La implementación consta de dos partes principales desarrolladas dentro del cuaderno de Jupyter:

### Parte 1: Clasificación con OpenAI CLIP (Zero-Shot)
Utilizamos el modelo contrastivo preentrenado `ViT-B/32` de OpenAI. En lugar de entrenar el modelo con etiquetas numéricas, tokenizamos **prompts enriquecidos semánticamente** (descripciones en inglés) para cada clase artística y los comparamos en el espacio latente compartido del modelo con las representaciones de las imágenes.

### Parte 2: Clasificador Tradicional (ResNet18 + SVM / k-NN)
Para contrastar la robustez de CLIP, diseñamos un pipeline clásico de Transfer Learning Estático:
1. Cargamos una red **ResNet18** preentrenada en ImageNet y eliminamos su capa completamente conectada final (`resnet.fc = torch.nn.Identity()`), convirtiéndola en un extractor estático de vectores de características de **512 dimensiones**.
2. Extrajimos los descriptores visuales de las 6 imágenes.
3. Entrenamos modelos de **Máquinas de Vectores de Soporte (SVM)** con kernel lineal y de **K-Vecinos Más Cercanos (k-NN)**.
4. Para obtener una validación científica rigurosa y libre de sesgo debido al diminuto tamaño de la muestra, empleamos **Validación Cruzada Leave-One-Out (LOO-CV)**.
5. Proyectamos las características tridimensionales utilizando **PCA** para inspeccionar la distribución visual de las clases.

---

## 4. Prompts Utilizados (Ingeniería de Prompts)

Diseñamos los prompts en inglés (idioma nativo en el que CLIP fue preentrenado en un corpus masivo de internet). La ingeniería de prompts consistió en dotar a cada clase de detalles estilísticos que definen las corrientes pictóricas en lugar de limitarse al nombre genérico de la clase:

*   **Clase Renaissance (Renacimiento):**  
    `"a classical renaissance oil painting of a portrait or figure, realistic proportions, soft sfumato lighting, historical fine art style"`
*   **Clase Impressionism (Impresionismo):**  
    `"an impressionist landscape painting, textured loose brush strokes, vibrant colors, outdoor setting, focusing on light and atmosphere"`
*   **Clase Cubism (Cubismo):**  
    `"a cubist portrait or abstract painting, fractured geometric shapes, multiple angles, modern art, cubism style"`

---

## 5. Código Relevante

### A. Inicialización y Clasificación Zero-Shot con CLIP
```python
import clip
import torch
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Descripciones textuales detalladas por clase
lista_de_descripciones = [
    "a classical renaissance oil painting of a portrait or figure, realistic proportions, soft sfumato lighting, historical fine art style",
    "an impressionist landscape painting, textured loose brush strokes, vibrant colors, outdoor setting, focusing on light and atmosphere",
    "a cubist portrait or abstract painting, fractured geometric shapes, multiple angles, modern art, cubism style"
]
class_names = ["Renaissance", "Impressionism", "Cubism"]

# Tokenizar prompts y cargar imagen
text_inputs = clip.tokenize(lista_de_descripciones).to(device)
image_input = preprocess(Image.open("dataset/renaissance_1.png")).unsqueeze(0).to(device)

with torch.no_grad():
    logits_per_image, _ = model(image_input, text_inputs)
    probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
    
# Obtener clase predicha
pred_class = class_names[probs.argmax()]
print(f"Predicción CLIP: {pred_class} (Confianza: {probs.max()*100:.2f}%)")
```

### B. Extracción de Características con ResNet18 y Clasificador SVM
```python
from torchvision import models, transforms
from sklearn.svm import SVC
import numpy as np

# Cargar ResNet18 y remover la última capa FC
resnet = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
resnet.fc = torch.nn.Identity()
resnet.to(device).eval()

# Preprocesamiento oficial de ImageNet
resnet_preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Extracción de características (simplificado para demostración)
def extract_features(img_path):
    img = Image.open(img_path).convert('RGB')
    tensor = resnet_preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        features = resnet(tensor).cpu().numpy().squeeze()
    return features

# Entrenar un SVM lineal sobre las características extraídas
X = np.array([extract_features(p) for p in paths])
y = np.array([0, 0, 1, 1, 2, 2]) # Mapeo numérico de clases

svm_clf = SVC(kernel='linear', C=1.0)
svm_clf.fit(X, y)
```

---

## 6. Resultados Visuales

### A. Mini-Dataset de Estilos de Arte Utilizado
A continuación se presenta la cuadrícula del mini-dataset creado sintéticamente para evaluar la precisión del taller:

![Grid del Mini-Dataset](media/dataset_grid.png)

---

### B. Resultados y Confianza de CLIP por Imagen

CLIP demostró un entendimiento semántico y conceptual sublime. A continuación se muestran los gráficos de confianza arrojados para cada obra de arte del mini-dataset:

#### 1. Renaissance (Renacimiento)
*   **Imagen 1 (Retrato de Noble):** CLIP lo clasifica correctamente como *Renaissance* con un abrumador **99.78%** de confianza.
*   **Imagen 2 (Mercader por la ventana):** Clasificación correcta como *Renaissance* con **99.64%** de confianza.

| renaissance_1.png (Predicción CLIP) | renaissance_2.png (Predicción CLIP) |
|:---:|:---:|
| ![Renaissance 1](media/renaissance_1_clip_prediction.png) | ![Renaissance 2](media/renaissance_2_clip_prediction.png) |

#### 2. Impressionism (Impresionismo)
*   **Imagen 1 (Jardín con Lirios):** Clasificación correcta como *Impressionism* con **98.81%** de confianza.
*   **Imagen 2 (Calle Parisina atardecer):** Clasificación correcta como *Impressionism* con **99.72%** de confianza.

| impressionism_1.png (Predicción CLIP) | impressionism_2.png (Predicción CLIP) |
|:---:|:---:|
| ![Impressionism 1](media/impressionism_1_clip_prediction.png) | ![Impressionism 2](media/impressionism_2_clip_prediction.png) |

#### 3. Cubism (Cubismo)
*   **Imagen 1 (Músico con Guitarra):** Clasificación correcta como *Cubism* con **99.55%** de confianza.
*   **Imagen 2 (Bodegón con Violín):** Clasificación correcta como *Cubism* con **99.98%** de confianza.

| cubism_1.png (Predicción CLIP) | cubism_2.png (Predicción CLIP) |
|:---:|:---:|
| ![Cubism 1](media/cubism_1_clip_prediction.png) | ![Cubism 2](media/cubism_2_clip_prediction.png) |

---

### C. Resultados del Clasificador Tradicional (ResNet18 + SVM)

Para analizar el comportamiento de las características visuales estáticas extraídas por ResNet18 (entrenada en ImageNet), realizamos un **Análisis de Componentes Principales (PCA)** para proyectar los vectores de características de 512 dimensiones en un espacio de 2D:

![PCA de Características ResNet18](media/pca_resnet_features.png)

#### Análisis de Métricas Tabular:
La comparación directa de exactitud en las predicciones demostró resultados sumamente interesantes:

| Imagen | Etiqueta Real | Predicción CLIP | Predicción SVM | ¿CLIP Acertó? | ¿SVM Acertó? |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **renaissance_1.png** | Renaissance | Renaissance | Renaissance | Sí | Sí |
| **renaissance_2.png** | Renaissance | Renaissance | Renaissance | Sí | Sí |
| **impressionism_1.png**| Impressionism | Impressionism | Impressionism | Sí | Sí |
| **impressionism_2.png**| Impressionism | Impressionism | Impressionism | Sí | Sí |
| **cubism_1.png** | Cubism | Cubism | Cubism | Sí | Sí |
| **cubism_2.png** | Cubism | Cubism | Cubism | Sí | Sí |

*   **Exactitud en el conjunto de entrenamiento (Train Set Accuracy):**
    *   **CLIP (Zero-Shot):** **100.0%**
    *   **SVM Lineal:** **100.0%**
*   **Exactitud General con Validación Cruzada Rigurosa (Leave-One-Out CV):**
    *   **SVM Lineal:** **66.67%** (Falla en 2 imágenes durante validación cruzada: clasifica incorrectamente una muestra de impresionismo como cubismo y una de cubismo como renacimiento).
    *   **k-NN (k=1):** **66.67%**

---

## 7. Aprendizajes y Dificultades (Reflexión Personal)

### ¿Cuándo ayuda el texto descriptivo?
El texto descriptivo enriquecido (ingeniería de prompts) es de vital importancia cuando nos enfrentamos a **conceptos semánticos abstractos, estilos, texturas y contextos globales** que no están representados por un único objeto aislado.
En este taller, "Impresionismo" no se refiere a la presencia de un árbol o de una persona, sino a la conjunción estilística de *pinceladas visibles, luz atmosférica y color vibrante*. CLIP logra alinear el texto descriptivo con la imagen porque proyecta ambos en un espacio común preentrenado de alta riqueza semántica. Al proporcionar prompts ricos y detallados en lugar de palabras sueltas, ayudamos a CLIP a guiar su atención hacia los elementos estilísticos distintivos en las imágenes de prueba.

### ¿Cuál modelo fue más robusto y por qué?
**Abrumadoramente, CLIP demostró ser el modelo más robusto.** Las razones técnicas y empíricas son:
1.  **Generalización Zero-Shot frente a Overfitting en Datos Diminutos:** En mini-datasets (como este de 6 imágenes), entrenar clasificadores tradicionales (SVM o k-NN) es sumamente inestable. Como se muestra en los resultados de Validación Cruzada (Leave-One-Out CV), el SVM tiene un rendimiento real del **66.67%**, fallando al intentar generalizar fronteras de decisión con tan solo 4-5 imágenes de entrenamiento. CLIP, por el contrario, no se entrena; tiene un conocimiento preexistente zero-shot que clasifica las imágenes con un **100%** de precisión de forma nativa.
2.  **Sesgo de Preentrenamiento en Extractores de Características:** ResNet18 está preentrenada en **ImageNet**, una base de datos diseñada para clasificar objetos reales y discretos (perros, barcos, sillas). Sus filtros convolucionales están afinados para reconocer bordes duros de objetos y formas geométricas explícitas de la vida diaria, por lo que carece de la riqueza semántica fina para discernir estilos artísticos abstractos, tal como se aprecia en el gráfico de **PCA**, donde la separación espacial de clases no es perfecta y mezcla elementos impresionistas con cubistas. CLIP, al estar entrenado de manera contrastiva en millones de pares imagen-texto del internet, comprende nociones estéticas del lenguaje humano integradas en su arquitectura visual.

---

### Dificultades Encontradas
1.  **Dimensión del Dataset:** Con 6 imágenes de estilos complejos, un clasificador tradicional entrenado desde cero es altamente inestable y propenso a sobreajustarse. El uso de **Leave-One-Out CV** fue la única herramienta científica adecuada para evaluar honestamente su desempeño.
2.  **Configuración de Entorno de Ejecución:** CLIP y PyTorch requieren pesos pesados que demandan una buena conexión de internet en la primera corrida para ser descargados y cargados en memoria. Manejar los tensores y mapear correctamente los gradientes de CLIP (`torch.no_grad()`) fue crucial para evitar cuellos de botella de computación o fugas de memoria VRAM en la GPU.
