# Taller Cinemática Directa: Brazo Robótico Interactivo

Juan Jose Alvarez, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

Fecha de entrega: 15/04/2026

## Descripción

Explorar los conceptos básicos de la cinemática directa aplicados a un brazo robótico articulado en 3D. El objetivo es construir una demostración interactiva que permita ajustar y visualizar la rotación de diferentes articulaciones (como el hombro y el codo) tanto de forma manual como automática, observando cómo el movimiento de la base afecta a los componentes conectados.

## Implementación

Para el desarrollo de la práctica se utilizó **React Three Fiber** (R3F) junto con **Vite** para construir un entorno 3D en el navegador de manera eficiente.

### Estructura y Jerarquía

Se definió una estructura jerárquica para el brazo robótico, compuesta por:
- **Base (Hombro)**: El punto de anclaje inicial.
- **Brazo**: El segmento conectado a la base.
- **Antebrazo (Codo)**: Adosado al brazo, demostrando la propagación de las transformaciones geométricas.

Se implementaron controles interactivos utilizando la librería **Leva**, lo que permite modificar los ángulos de rotación de cada articulación en tiempo real. 

### Interactividad y Animación

Se añadieron dos modos interactivos:
1. **Modo Manual**: A través del panel de controles (Leva), el usuario puede ajustar individualmente las articulaciones y observar cómo dichas transformaciones afectan a los segmentos descendentes (hijos) del brazo robótico debido a la cinemática directa.
2. **Modo Automático**: Se programó un ciclo de animación usando `useFrame` de R3F para rotar automáticamente las articulaciones en el tiempo, proporcionando una visualización continua del movimiento complejo.

Además, se añadió un rastro o "trail" para el "End Effector" (extremo del brazo), que dibuja la trayectoria del brazo a medida que se mueve, permitiendo visualizar claramente el espacio de trabajo del robot.

## Resultados visuales

En esta sección se evidencia la correcta aplicación de las transformaciones y la jerarquía de los objetos, así como el funcionamiento de la cinemática directa en el lienzo 3D.

![Rotación Automática y Manual](media/rotacion_automatica_y_manual.gif)
*Figura 1. El GIF muestra la rotación del brazo tanto en modo automático como en modo manual modificando los parámetros para cada articulación.*

Los controles interactivos nos permitieron aislar el movimiento de cada articulación y verificar visualmente que las rotaciones locales se transmiten correctamente a los descendientes de la jerarquía geométrica del objeto.

## Aprendizajes

A partir de esta práctica, se adquirieron conocimientos clave sobre la jerarquía clásica empleada en gráficos 3D y la cinemática directa.

En primer lugar, se comprendió cómo la creación de jerarquías de padres e hijos permite que la traslación y rotación influyan de forma lógica y predecible en todos los elementos anidados, facilitando enormemente la representación visual de sistemas mecánicos en Three.js / React Three Fiber.

Adicionalmente, se integraron controles dinámicos que permitieron una rápida experimentación interactiva, lo cual es fundamental para validar y ajustar los límites de movimiento en tiempo real.

Por último, se trabajó con la propagación continua de coordenadas y transformaciones de un marco de referencia local al de sus sucesores, reafirmando la importancia del manejo adecuado de transformaciones locales, globales y los puntos de pivote en el diseño de articulaciones mecánicas en simulaciones 3D.
