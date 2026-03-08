# Taller Etapas del Pipeline Programable

Victor Saa y

Fecha de entrega: 09/03/2026

## Descripción

Explorar las etapas programables del pipeline gráfico moderno (vertex shader, fragment shader, geometry shader), comprender su funcionamiento y crear shaders personalizados para cada etapa. Comparar con el pipeline de función fija y aprender técnicas de debugging.

## Implementaciónes

### Unity

DESCRIBIR IMPLEMENTACIÓN EN UNITY

### Three.js

Se utilizó three.js para la implementación. Se generó una escena con una esfera. Se implementaron shaders personalizados (vertex shader, fragment shader, geometry shader) y post-procesado. Se utilizó leva para controlar los parámetros de la escena.

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

![Unity](media/unity-week-3.4.gif)
![Three.js](media/week-3-4-threejs.gif)

## Prompts utilizados

Aca me ayude de Antigravity construir la escena base del sistema solar.

## Aprendizajes

No conocia el lenguaje GLSL, tambien amplie mas mi percepcion de como los shaders pueden llegar a modificar la percepcion de los objetos en una escena 3D.

## Contribuciones grupales (si aplica)

Victor Saa: Desarrollo Three.js

## Estructura del proyecto

```
semana_3_4_etapas_pipeline_programable/
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
