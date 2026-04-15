# Taller Animaciones por Esqueleto: Importando y Reproduciendo Animaciones

Estudiantes: Manuel Santiago Mori Ardila, Jose Arturo Herrera Rivera, Juan Jose Alvarez

Fecha de entrega: 15/04/2026

## Descripción

Trabajar con animaciones basadas en huesos (esqueleto) y reproducirlas desde archivos externos como .FBX o .GLTF. El objetivo es comprender cómo funcionan las animaciones esqueléticas, cómo importarlas correctamente y cómo integrarlas en escenas interactivas.

## Implementaciónes

### Unity

La implementación se desglosó en las siguientes fases técnicas:

Configuración del Modelo y Rig: Se importó un modelo tridimensional junto con diversos clips de animación (espera, caminar, correr y saltar) provenientes de la plataforma Mixamo. Se configuró el sistema de Rigging en modo generic para garantizar la compatibilidad de los esqueletos y se usaron los materiales propios del modelo de mixamo.

Arquitectura del Animator: Se diseñó un Animator Controller donde se definieron los estados base: Idle, Walk, Run y Jump. Se establecieron parámetros lógicos (como un Float de velocidad) para gestionar las transiciones entre estados.

Lógica de Control (C#): Se desarrolló un script encargado de emplear el método Play() para cambios directos de estado solicitados desde la interfaz.

Interfaz de Usuario (UI): Se implementó un lienzo (Canvas) con botones para pausar y reiniciar la simulación, además de un menú desplegable (Dropdown) vinculado mediante eventos dinámicos al script de control, permitiendo el cambio manual de animaciones en tiempo real.

## Resultados visuales

Como se observa en las capturas de pantalla adjuntas, se lograron los siguientes hitos visuales:

Estado de Reposo y Movimiento: El personaje respondió correctamente a los comandos de animación, manteniendo la coherencia visual en los estados de Idle (Imagen 1) y Correr (Imagen 3).

Dinámica de Salto: Se validó la ejecución de animaciones complejas como el salto y su pausa, logrando que el modelo realizara la acción física de manera fluida (Imagen 2).

Control de Interfaz: El sistema de Dropdown permitió la selección exitosa de estados (Imagen 3), mientras que el Animator gestionó los nodos de forma jerárquica (Imagen 4).

## Aprendizajes

El proceso permitió consolidar conocimientos sobre el sistema de animación de Unity, la gestión de avatares humanoides y la comunicación entre los componentes de UI y la lógica de juego.

En cuanto a las dificultades, se presentaron retos significativos en la sincronización de las coordenadas de las animaciones para evitar que el modelo flotara, lo cual se resolvió mediante el ajuste del Root Motion y el Bake into Pose. No obstante, no fue posible concretar la implementación del audio durante la animación del salto debido a complicaciones técnicas en la configuración de los Animation Events y la carga del clip de sonido en el componente AudioSource en el momento preciso de la ejecución.

## Estructura del proyecto

```
semana_6_2_animaciones_esqueleto_fbx_gltf/
├── unity/
├── media/
|    ├── ARCHIVO.gif
└── README.md
```

---

## Referencias

Lista las fuentes, tutoriales, documentación o papers consultados durante el desarrollo:

- Documentación oficial de Unity: https://docs.unity3d.com/Manual/
- Como Importar ANIMACIONES De MIXAMO a UNITY: https://youtu.be/PesrC6HcYB8?si=kPolWZwOA-yd7AX0
- Cómo agregar efectos de sonido a nuestros juegos en Unity: https://youtu.be/8c3S5SJCaRM?si=JpRiLRxVxGxf_EzY
- how to use Unity's animation events ✨sync effects with footsteps: https://youtu.be/iudHK8h_5hw?si=yXdpwTxgiN5uhtce

---
