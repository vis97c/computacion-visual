# Taller Texturizado Creativo: Materiales Dinámicos con Shaders y Datos

Juan Jose Alvarez

Jose Arturo Herrera Rivera

Fecha de entrega: 28/03/2026

## Descripción

Crear materiales que cambien en tiempo real en respuesta a entrada del usuario, paso del tiempo o sensores simulados. Además, se integrarán efectos de partículas para complementar visualmente el comportamiento del material, simulando fenómenos como fuego, agua, electricidad o portales.

## Implementaciones

### Three.js (React Three Fiber)

La implementación en Three.js se desarrolló como una aplicación web interactiva usando **React Three Fiber**, **@react-three/drei** y shaders **GLSL** personalizados para generar texturizado dinámico procedural.

#### Detalles Técnicos:

- **Escena 3D con Materiales Dinámicos**: Se implementó una `IcosahedronGeometry` de alta densidad como núcleo, recubierta de un shader customizado (`shaderMaterial` extendido) que simula plasma y energía.
- **Texturizado Procedural (FBM & Simplex Noise)**: Se utilizó Fractional Brownian Motion y ruido Simplex 3D dentro de los shaders. En el *Vertex Shader*, se usan para desplazar los vértices asíncronamente simulando un fluido turbulento. En el *Fragment Shader*, generan los patrones de intensidad cromática.
- **Interactividad (uTime, uMouse, uHover)**: 
  - La intensidad y el color transicionan dinámicamente con el paso del tiempo (`uTime`). Por ejemplo, los tintes magentas cambian cíclicamente a rojo.
  - Al pasar el cursor (`uHover`), la amplitud de desplazamiento de los vértices aumenta agresivamente y la paleta de colores central cambia bruscamente (transicionando a tonos verdes/naranjas de inestabilidad).
  - La posición del ratón (`uMouse`) proyecta un canal directo de brillo en el área impactada incrementando localmente el multiplicador lumínico.
- **Sistema de Partículas**: Se desarrollaron miles de partículas distribuidas en forma esférica (con `Points` y  `BufferGeometry`). Tienen sus propios atributos (*size*, *phase*, *color*, *life*) inyectados que se transforman mediante otro Custom Shader para interpolar transparencias de órbita paramétrica ("soft-circles").
- **Efecto de Dispersión (Click)**: Un evento de clic gatilla un pulso (controlado por el atributo `uExplosion`), mitigándose con un *decay* exponencial ajeno al framerate, forzando a las partículas ambientales y vértices del núcleo a estallar y separarse hacia afuera violentamente.
- **Renderizado Premium UI**: Se implementó Bloom (*Postprocessing*) unificado para la incandescencia emisiva, y un HUD flotante tipo *Glassmorphism* que monitorea variables de la escena  en vivo.

#### Snippets de Código:

```glsl
// Vertex Shader: Desplazamiento procedural usando FBM y estados de Click/Hover
void main() {
    // ... Creación de ruido procedural FBM
    float noiseScale = 1.5 + uHover * 0.5;
    float speed = uTime * 0.3;
    float n = fbm(position * noiseScale + speed);
    
    // El desplazamiento reacciona a interacciones (Hover & Click Explosion)
    float displaceAmount = 0.15 + uHover * 0.12;
    float explosionDisplace = uExplosion * 1.2;
    
    vec3 newPosition = position + normal * n * displaceAmount;
    newPosition += normal * explosionDisplace;
    
    gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
}
```

```glsl
// Fragment Shader: Shifting dinámico de color con Tiempo, Localización e Influencia de Ratón
void main() {
    // Patrones animados de ruido para la capa de texturizado
    float t = uTime * 0.4;
    // ... fbm evaluation ...

    // Paleta de colores variante dramáticamente por Tiempo y Hover
    vec3 colorCyan = mix(vec3(0.0, 0.898, 1.0), vec3(0.1, 1.0, 0.2), uHover);
    vec3 colorMagenta = mix(vec3(0.878, 0.251, 0.984), vec3(1.0, 0.2, 0.2), sin(uTime * 0.5) * 0.5 + 0.5);
    
    // ... mixFactor de canales y ruidos ...
    
    // Influencia de ratón: incrementamos estocásticamente el contorno uv equivalente al mouse
    float mouseInfluence = 1.0 - smoothstep(0.0, 0.5, length(vUv - uMouse));
    color += colorCyan * mouseInfluence * 0.15;
    
    gl_FragColor = vec4(color, alpha);
}
```

## IA

IDE, prompts y autocompletado: Antigravity — estructuración de código modular React, GLSL Shaders generativos matemáticos y diseño premium.

## Resultados visuales

### Three.js

*(Reemplazar o agregar imágenes/gifs representativos del funcionamiento en `media/`)*


![Partículas e Interacción](media/threejs_vid.gif)
*Video de el gatillado expansivo de partículas y disrupción del texturizado base respondiendo al evento de hover y click en simultáneo.*

## Prompts utilizados

- *"En semana_5_4_texturizado_dinamico_shaders_particulas\threejs, desarrolla Three.js con React Three Fiber – Ejemplo replicable. Crear una escena con un objeto central. Usar shaderMaterial o MeshStandardMaterial con mapas animados."*
- *"Cambiar color o intensidad con uTime, mouse o hover y Usar texturas animadas o fragment shaders para simular líquidos o energía."*
- *"Agregar un sistema de partículas básico usando points + bufferGeometry, que aparezcan cerca y varíen su tamaño y color. Agrega el efecto bonus de explosión al clic sobre el core."*

## Aprendizajes

- Inyectar *Noise procedural* interpolado (como el Simplex 3D en los shaders de vertices) deforma asíncronamente un objeto obteniendo texturas fluidas mucho más óptimas para GPU que el texturizado preconcebido estático de 2D.
- Alterar un atributo base o *bufferAttribute* iterativo (como la fase o el origen de cada partícula ambiental por separado) logra diversificar el resultado final de cientos de puntos individualizados sin depender de las físicas y CPU de Three.js puro.
- Truncar las transiciones desde React usando **Uniforms** unificados dentro de un bucle `useFrame` (`uTime`, `uMouse`, `uHover`) es una vía performante y escalable, comunicando eventos frontend a matemáticas subyacentes nativas de los Shaders en GLSL puro.

## Estructura del proyecto

```text
semana_5_4_texturizado_dinamico_shaders_particulas/
├── unity/
├── threejs/                              # Aplicación interactiva React Three Fiber
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx                      # Entry point React
│       ├── App.tsx                       # Contexto 3D de Entorno (Luces, Controles)
│       ├── App.css / index.css           # UI layout HUD
│       ├── components/                   # Instanciadores 3D
│       │   ├── EnergySphere.tsx          # Wrapper Esfera Reactiva
│       │   ├── ParticleSystem.tsx        # Geometría Multi-Puntos
│       │   ├── ExplosionParticles.tsx    # Entidad de Dispersión
│       │   └── HudOverlay.tsx            # Telemetría UI (Glassmorphism)
│       └── shaders/
│           ├── energySphere.ts           # Shaders Glsl (Vertex/Fragment) Turbulencia
│           └── particles.ts              # Custom Point Shaders de Orbes
├── media/                                # Subidas de Evidencia (screenshots/gifs para Markdown)
└── README.md
```

---

## Referencias

Lista las fuentes, tutoriales, documentación o papers consultados durante el desarrollo:

- The Book of Shaders (Simplex, Noise y Fractal Brownian Motion): https://thebookofshaders.com/
- Documentación oficial de Three.js — `ShaderMaterial` e inyecciones de GLSL: https://threejs.org/docs/#api/en/materials/ShaderMaterial
- Tutorial Core de React Three Fiber: https://docs.pmnd.rs/react-three-fiber/
- Repositorio y ejemplos interactivos de THREE.js post-processing en Drei: https://drei.docs.pmnd.rs/

---
