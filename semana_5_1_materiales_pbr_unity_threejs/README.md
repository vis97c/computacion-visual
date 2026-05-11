# Taller Materiales Realistas: Introducción a PBR en Unity y Three.js

Jose Arturo Herrera Rivera, Juan Jose Alvarez

Fecha de entrega: 28/03/2026

## Descripción

Comprender los principios del renderizado basado en física (PBR, Physically-Based Rendering) y aplicarlos a modelos 3D para mejorar su realismo visual. Este taller permite comparar cómo la luz interactúa con diferentes tipos de materiales y cómo las texturas afectan el resultado visual final.

## Implementaciónes

### Unity

Se implementaron 3 materiales PBR para comparar visualmente las diferencias entre materiales tradicionales y materiales PBR.

Se desarrolló una escena 3D que incluyó:

Fila superior con objetos con materiales básicos (solo color base/albedo)

Fila inferior con objetos con materiales PBR completos

Esta disposición permitió observar inmediatamente las diferencias entre los materiales.

Se crearon dos tipos de materiales para comparación:

1. Material PBR: Utiliza el shader Standard de Unity con todos los mapas de textura configurados
2. Material Simple: Solo color base sin mapas, para demostrar las limitaciones del renderizado tradicional

Tambien se implementaron 2 sliders que permiten modificar en tiempo real la textura de la esfera con material PBR:

1. Valor de Metallic
2. Valor de Smoothness

## Resultados

Las imagenes de las texturas PBR y No PBR se adjuntaron en la carpeta /media, tambien se adjuntó un video de la implementación.

La implementación de PBR marcó una diferencia sustancial en la fidelidad visual de los materiales frente a los métodos de sombreado convencionales. En superficies como la textura de ladrillos, el uso de normal mapping y parámetros de rugosidad eliminó la apariencia plana, otorgando una profundidad real en las juntas y reflejos especulares más naturales. Este incremento en la tridimensionalidad se extendió al patrón de rayas, donde la respuesta lumínica permitió transiciones de brillo dinámicas.

Finalmente, en las texturas orgánicas de musgo y roca, el modelo PBR sobresalió al capturar la complejidad de las irregularidades de la superficie; la simulación de humedad mediante reflejos realistas y la riqueza en las variaciones de color generaron un contraste y una respuesta a la iluminación que resultaron notablemente superiores a la iluminación básica.

## Aprendizajes

El aprendizaje más significativo fue comprender que el realismo en PBR no depende únicamente de la calidad de las texturas, sino de su configuración técnica correcta dentro del motor, destacando la importancia crítica de la gestión del espacio de color (sRGB) y la tipificación de los mapas en el motor.

La implementación demostró que el renderizado PBR es una aplicación de principios ópticos reales, donde herramientas nativas como el Default shader de Unity, combinadas con una interfaz interactiva para ajustar parámetros en tiempo real, permiten lograr resultados realistas sin necesidad de shaders complejos. Finalmente, la comparación directa entre materiales simples y PBR validó que la diferencia radica en la coherencia física de la luz y el relieve.
