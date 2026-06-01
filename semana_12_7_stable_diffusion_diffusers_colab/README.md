# Taller Reconocimiento de Postura con MediaPipe

Victor Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

Fecha de entrega: 2026-05-25

## Descripcion breve

El objetivo principal de este taller fue la exploración, configuración e implementación local del modelo de difusión generativa **Stable Diffusion v1.5**. A lo largo de la práctica, se estructuró un entorno de ejecución en Python basado en PyTorch y Hugging Face (`diffusers`) para ejecutar el pipeline de generación de imágenes por medio de aceleración por hardware (GPU). Se evaluó el impacto de los hiperparámetros fundamentales del modelo (pasos de inferencia, escala de guía de prompt y semillas de aleatoriedad), la aplicación de ingeniería de prompts (_Prompt Engineering_), el uso de prompts negativos para el control de calidad, y la resolución de problemas técnicos asociados a la precisión matemática del hardware.

## Implementaciones

La arquitectura del script se diseñó de manera modular para ejecutar consecutivamente una serie de actividades de experimentación controlada:

1. **Configuración del Entorno de Aceleración:** Se desarrolló una función automatizada para verificar la disponibilidad de CUDA, identificar la tarjeta gráfica del sistema y calcular la VRAM disponible.
2. **Optimización de Carga del Modelo:** Se implementó la carga dinámica del pipeline empleando precisión de punto flotante de 16 y 32 bits (`torch.float16` y `torch.float32`), integrando además técnicas de optimización de VRAM como `enable_attention_slicing()` para mitigar cuellos de botella en la memoria de la GPU.
3. **Control del Pipeline e Inferencia:** Se estructuró un motor de generación capaz de recibir parámetros variables de tamaño (`height`, `width`), pasos de inferencia (`steps`), escala de guía (`guidance_scale`), prompts negativos personalizados y semillas estables (`torch.Generator`).
4. **Automización por Lotes y Grillas:** Se programó un sistema de visualización matricial utilizando `matplotlib` para organizar de forma automática las imágenes resultantes de los experimentos concurrentes, facilitando el análisis comparativo inmediato de los parámetros.

## Prompts Utilizados

A lo largo de las distintas actividades del laboratorio, se estructuraron prompts orientados a evaluar la versatilidad semántica del modelo estos son algunos de los prompts:

- **Actividad 3 (Primera Generación):** \* _Prompt:_ `A surreal futuristic city in the clouds, digital art, highly detailed`
- **Actividad 4 (Exploración de Parámetros):**
  - _Prompt (Pasos):_ `A majestic lion in a savanna at sunset, photorealistic`
  - _Prompt (Guía/CFG):_ `An enchanted forest with glowing mushrooms, fantasy art`
  - _Prompt (Semillas):_ `A cozy cabin in the mountains during winter, snow falling`
- **Actividad 7 (Generación por Lotes):**
  - _Prompt 1 (Dragón):_ `A dragon flying over a medieval castle at night, fantasy art, epic`
  - _Prompt 4 (Templo):_ `Ancient Japanese temple in autumn, cherry blossoms, fog, watercolor`
- **Actividad 8 (Prompt Engineering):**
  - _Prompt Simple:_ `a cat`
  - _Prompt Elaborado:_ `a majestic tabby cat sitting on a velvet throne, royal portrait, dramatic renaissance lighting, oil painting style, ultra detailed, rich jewel tones, 8k resolution`
  - _Prompt Negativo:_ `blurry, low quality, cartoon, deformed, ugly`

## Resultados visuales

### Primera Generación — Ciudad Futurista

Se evaluó la capacidad de composición espacial inicial del modelo. Se obtuvo una obra de arte digital que muestra una metrópolis futurista suspendida entre nubes densas. El modelo interpretó correctamente la perspectiva y los planos de profundidad, destacando megaestructuras cilíndricas con una iluminación dorada y contrastes fríos muy bien definidos, lo que confirmó el correcto acoplamiento inicial de los tensores de texto a imágenes coherentes.

### Impacto de los Pasos de Inferencia

Se analizó el proceso de remoción progresiva de ruido gaussiano fijando la semilla (seed=42). A través de los resultados visuales se observó de manera nítida la evolución temporal del desempaquetado de la imagen. Con una inferencia baja (steps=10), la imagen del león quedó abstracta, carente de anatomía real y con notorios artefactos de color inconexos. Al incrementar a los pasos óptimos (steps=25), la geometría y la estructura del león y el entorno de la sabana se consolidaron por completo. Aumentar a steps=50 refinó las texturas sutiles del pelaje y el follaje del árbol bajo la luz del atardecer sin alterar la composición base, demostrando el límite de rendimiento de los pasos sobre la microtextura.

### Análisis de Prompt Engineering (Simple vs. Elaborado)

El experimento comparativo final demostró empíricamente el impacto radical que tiene refinar las instrucciones y restricciones semánticas entregadas a la red de difusión.

## Codigo relevante

A continuación se presentan los fragmentos de código cruciales diseñados para optimizar la inicialización del modelo y resolver fallas críticas de hardware durante el taller:

### Control de Precisión y Gestión de VRAM

Durante el desarrollo se identificó que ciertas arquitecturas de hardware generaban desbordamientos numéricos flotantes (`NaN`), traduciéndose en imágenes completamente negras. Se resolvió forzando el procesamiento del componente VAE en 32 bits, manteniendo el resto del pipeline optimizado en 16 bits:

```python
def cargar_modelo(device):
    # Optimización base en float16 para acelerar la inferencia
    dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"\n📥 Cargando modelo: {MODEL_ID} ...")
    pipe = StableDiffusionPipeline.from_pretrained(MODEL_ID, torch_dtype=dtype).to(device)

    # Desactivación manual del filtro de seguridad para evitar falsos positivos en entorno local
    pipe.safety_checker = None
    pipe.feature_extractor = None

    # Solución matemática para evitar cuadros negros (NaN) forzando el VAE a float32
    if device == "cuda":
        pipe.vae.to(dtype=torch.float32)

    # Segmentación de atención para reducir el uso pico de VRAM
    pipe.enable_attention_slicing()
    print("✅ Modelo listo.\n")
    return pipe
```

## Aprendizajes y dificultades

El Fenómeno de las Imágenes Negras (Error Crítico de Hardware): El obstáculo más complejo del taller se presentó cuando el script comenzó a retornar cuadros negros limpios en lugar de las imágenes generadas, sin arrojar ningún error explícito en la terminal de Jupyter. Inicialmente se teorizó que correspondía a bloqueos estrictos del filtro de contenido (Safety Checker). Sin embargo, tras desactivarlo manualmente en el pipeline, el fallo persistió. Tras una investigación técnica profunda, se descubrió que el decodificador del módulo VAE generaba desbordamientos numéricos y valores no válidos (NaN) al procesar en precisión flotante de 16 bits (float16) bajo la arquitectura de la GPU local. La dificultad se solventó modificando el código de carga para obligar exclusivamente al componente del VAE a trabajar en precisión de 32 bits (torch.float32), eliminando el error matemático de raíz sin comprometer la velocidad ni la memoria del resto del pipeline.

Gestión de Dependencias y Entornos: Al configurar el entorno virtual, surgieron conflictos de distribución debido a que el comando estándar de instalación descargaba compilaciones de PyTorch dedicadas exclusivamente a CPU. Se requirió redireccionar explícitamente el índice de descargas apuntando de forma exacta a los binarios compatibles con la arquitectura de drivers de CUDA instalada en el sistema.

Se comprobó empíricamente que un mayor número de pasos de inferencia no siempre implica una mejor imagen, existiendo un umbral de rendimiento óptimo (entre 25 y 35 pasos) donde el consumo de tiempo de cómputo adicional no justifica el cambio visual microtextural.

Se asimiló el valor crítico de la ingeniería de prompts negativos; restringir estéticas (como texturas plásticas, renders 3D burdos o estilos de dibujo infantiles) es una herramienta matemática poderosa para forzar al modelo a converger hacia resultados realistas o artísticos de alta calidad.
