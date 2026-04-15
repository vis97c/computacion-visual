# Taller Cinemática Inversa: Haciendo que el Modelo Persiga Objetivos

Victor Saa

Fecha de entrega: 15/04/2026

## Descripción

Aplicar cinemática inversa (IK, Inverse Kinematics) para que un modelo 3D alcance un punto objetivo dinámico, como una mano intentando tocar una esfera. Este ejercicio permite comprender cómo una cadena de articulaciones puede ajustarse automáticamente para alcanzar una posición deseada usando algoritmos como CCD o FABRIK.

## Implementación

### Three.js

En three.js se implementó un brazo robótico con 3 grados de libertad, cada uno con su propia articulación y rotación. El brazo puede moverse en cualquier dirección del espacio, alcanzando cualquier punto dentro de su alcance. Se utilizó el algoritmo CCD (Cyclic Coordinate Descent) para resolver la cinemática inversa, permitiendo que el brazo alcance el objetivo deseado de manera eficiente.

## IA

IDE, prompts y autocompletado: Antigravity

## Resultados visuales

## Prompts utilizados

PROMPTS UTILIZADOS AQUI

## Aprendizajes

APRENDIZAJES AQUI

## Estructura del proyecto

```
semana_6_4_cinematica_inversa_ik/
├── threejs/
├── media/
|    ├── ARCHIVO.gif
└── README.md
```

---

## Referencias

Lista las fuentes, tutoriales, documentación o papers consultados durante el desarrollo:

- Documentación oficial de Unity: https://docs.unity3d.com/Manual/
- Tutorial de React Three Fiber: https://docs.pmnd.rs/react-three-fiber/
- Leva (React UI controls): https://leva.pmnd.rs/

---
