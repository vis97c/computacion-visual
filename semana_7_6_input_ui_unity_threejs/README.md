# Taller Three.js + React (React Three Fiber) - Input y HTML UI

## Nombres de los estudiantes

Victor Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

## Fecha de entrega

`2026-04-25`

---

## Descripción breve

Este taller implementa un sistema interactivo en la web utilizando **React Three Fiber (R3F)**, uniendo la potencia de renderizado de **Three.js** con la arquitectura basada en componentes y el manejo de estado de **React**. La aplicación está diseñada para gestionar múltiples tipos de entradas del usuario (inputs) y superponer de forma limpia interfaces gráficas (UI) HTML sobre el entorno 3D.

El entorno dibuja un objeto 3D que responde físicamente a los clics del usuario (`onClick`) para iniciar o detener su animación gestionada dinámicamente mediante el hook `useFrame`. La manipulación de la cámara está optimizada utilizando `OrbitControls`, y se capturan eventos globales de teclado (`useEffect` con `keydown`) para reiniciar la vista. La interfaz de usuario combina componentes 3D flotantes de `@react-three/drei` (Html), paneles de control en tiempo real mediante **Leva**, y capas globales construidas con `react-dom` tradicional.

---

## Implementaciones

### React Three Fiber y Three.js

El motor central del renderizado corre sobre un componente `<Canvas>`, el cual maneja la inicialización de WebGL de forma declarativa. Las luces físicas (`ambientLight`, `spotLight`) y el entorno visual interactúan con las propiedades de los materiales (`meshPhysicalMaterial`) para proveer sombras en tiempo real y estética *glassmorphism*.

### Captura de Entradas (Inputs)

Se procesan tres mecanismos de control de usuario de manera transparente:
1. **Clicks en Objetos 3D**: Aprovechando el sistema de *Raycasting* automático de R3F, el objeto atiende a la propiedad `onClick` para alterar el estado de React y definir si el objeto debe rotar o no, además de usar `onPointerOver/Out` para modificar el cursor.
2. **Entradas del Mouse y Arrastre**: Usando `OrbitControls` y `useThree().events`, el movimiento del ratón se traduce en rotación polar y azimutal suave (amortiguada) alrededor de la escena 3D.
3. **Eventos Globales (Teclado)**: Se usa un `useEffect` nativo de React unido al ciclo de vida del componente para registrar un *listener* global. Al presionar la tecla **R**, se reestablece la cámara, el centro del *OrbitControls* y las coordenadas de transformación del objeto.

### Interfaces Gráficas Híbridas (Html, Leva, DOM)

El sistema superpone la interfaz sin bloquear el lienzo tridimensional:
- **Leva**: Se integró un hook `useControls` para exponer variables reactivas como *Sliders* (escala, velocidad, intensidad) y paletas de colores en tiempo real.
- **@react-three/drei (Html)**: Un componente anclado a las coordenadas 3D locales del objeto (`position={[0, 1.2, 0]}`). Rota y se escala según la posición de la cámara pero sigue procesándose mediante el DOM.
- **UI de React tradicional (`react-dom`)**: Capas globales que usan `position: absolute` encima del *Canvas* para menús generales, asegurando que los eventos de click traspasen usando `pointer-events: none` y `auto`.

---

## Resultados visuales

### Interfaz Web y Controles

![Funcionamiento UI](./media/funcionamiento_app.gif)
*(Muestra el estado dinámico y la UI superpuesta en el navegador)*

---

## Código relevante

### Animación Continua y Componentes JSX 3D

```jsx
// Animación por frame vinculada al estado reactivo 'active'
useFrame((state, delta) => {
  if (active && objectRef.current) {
    objectRef.current.rotation.x += delta * speed;
    objectRef.current.rotation.y += delta * speed * 0.8;
  }
});

return (
  <mesh
    ref={objectRef}
    scale={scale}
    onClick={(e) => {
      e.stopPropagation();
      setActive(!active); // Interacción directa
    }}
    onPointerOver={() => document.body.style.cursor = 'pointer'}
    onPointerOut={() => document.body.style.cursor = 'auto'}
  >
    <boxGeometry args={[1, 1, 1]} />
    <meshPhysicalMaterial color={active ? color : '#555555'} />
    
    {/* Interfaz anclada en coordenadas 3D locales */}
    <Html position={[0, 1.2, 0]} center distanceFactor={10}>
        <div>Estado: {active ? 'ROTANDO' : 'PAUSADO'}</div>
    </Html>
  </mesh>
);
```

### Reset del Escenario vía Listeners Globales

```jsx
useEffect(() => {
  const handleKeyDown = (e) => {
    if (e.key.toLowerCase() === 'r') {
      // 1. Reset cámara global
      camera.position.set(0, 0, 5);
      camera.lookAt(0, 0, 0);
      
      // 2. Reset OrbitControls target
      if (orbitRef.current) {
        orbitRef.current.target.set(0, 0, 0);
        orbitRef.current.update();
      }

      // 3. Reset Posición/Rotación del Objeto
      if (objectRef.current) {
        objectRef.current.position.set(0, 0, 0);
        objectRef.current.rotation.set(0, 0, 0);
      }
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [camera, orbitRef, objectRef]);
```

---

## Prompts utilizados

```
"En semana_7_6_input_ui_unity_threejs\threejs: Crea un proyecto con Three.js + React (React Three Fiber)"

"Agregar UI con librerías como: @react-three/drei (Html), leva o drei panel para sliders y botones, react-dom para superponer UI."

"Al presionar R no pasa nada y al usar la funcionalidad de arrastrar para rotar el objeto el cubo se desaparece al soltar el click"

```

---

## Aprendizajes y dificultades

### Aprendizajes

La integración de herramientas como `@react-three/drei` simplifica enormemente las lógicas matemáticas complejas que el Three.js estándar requiere para ciertas interacciones visuales (por ejemplo, proyectar un `<Html>` 2D en unas coordenadas 3D específicas y lograr que cambie su perspectiva si movemos la cámara). Además, el manejo de estados de React simplifica la reactividad frente a la manipulación directa del DOM o variables dispersas. 

### Dificultades

**Físicas y Cámaras Reactivas**: Inicialmente se experimentó con el componente `PresentationControls` el cual gestionaba sus propias físicas de rebote y retorno. Dicho componente poseía conflictos con el reseteo manual de posiciones debido a la acumulación de la tensión del "resorte", lo cual lanzaba los objetos fuera del campo visual al reiniciarse o al hacer *drag*. Se solucionó sustituyendo y centralizando el manejo de la cámara en el robusto estándar de `OrbitControls`.

---

## Contribuciones grupales

Taller realizado de forma individual.

---

## Estructura del proyecto

```
semana_7_6_input_ui_unity_threejs/
├── threejs/
│   ├── src/
│   │   ├── App.jsx           # Lógica principal 3D, UI superpuesta y listeners
│   │   ├── index.css         # Estilos globales y reset full-screen
│   │   └── main.jsx          # Punto de entrada de React DOM
│   ├── index.html            # Plantilla web principal
│   ├── package.json          # Listado de dependencias (Fiber, Drei, Leva, etc.)
│   └── vite.config.js        # Compilador y Dev Server optimizado
└── README.md                 # Documentación principal estandarizada de taller
```

---

## Referencias

- React Three Fiber Documentation: https://docs.pmnd.rs/react-three-fiber
- Drei Helper Components: https://github.com/pmndrs/drei
- Leva UI GUI: https://github.com/pmndrs/leva
- Documentación de Three.js: https://threejs.org/docs/

---

