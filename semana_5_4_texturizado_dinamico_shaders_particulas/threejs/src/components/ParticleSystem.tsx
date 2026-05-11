import { useRef, useMemo } from "react";
import { useFrame, extend, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { ParticlesMaterial } from "../shaders/particles";

// Registrar el material personalizado con R3F
extend({ ParticlesMaterial });

declare global {
  namespace JSX {
    interface IntrinsicElements {
      particlesMaterial: any;
    }
  }
}

interface ParticleSystemProps {
  count?: number;
  explosionIntensity: number;
}

/**
 * ParticleSystem — Partículas orbitando alrededor de la esfera central.
 *
 * Usa un material shader personalizado con:
 * - Atributos por partícula: tamaño, fase, color, vida
 * - Animación orbital en el vertex shader
 * - Renderizado de círculos suaves en el fragment shader
 * - Soporte para dispersión por explosión
 *
 * Las partículas se distribuyen en una capa alrededor de la esfera
 * con diferentes radios, tamaños y colores de la paleta de energía.
 */
export default function ParticleSystem({
  count = 2000,
  explosionIntensity,
}: ParticleSystemProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const matRef = useRef<any>(null);
  const { gl } = useThree();

  const { positions, sizes, phases, colors, lives } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const phases = new Float32Array(count);
    const colors = new Float32Array(count * 3);
    const lives = new Float32Array(count);

    // Paleta de colores
    const palette = [
      new THREE.Color("#00e5ff"), // cyan
      new THREE.Color("#e040fb"), // magenta
      new THREE.Color("#ffd740"), // gold
      new THREE.Color("#7c4dff"), // purple
      new THREE.Color("#00e676"), // green
    ];

    for (let i = 0; i < count; i++) {
      // Distribuir partículas en una capa alrededor de la esfera (radio 1.6 - 3.5)
      const radius = 1.6 + Math.random() * 1.9;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      // Tamaños aleatorios (las partículas pequeñas son más comunes)
      sizes[i] = Math.pow(Math.random(), 2) * 0.8 + 0.1;

      // Fase aleatoria para el desfase de la animación
      phases[i] = Math.random() * Math.PI * 2;

      // Escoger un color de la paleta con algo de mezcla aleatoria
      const c1 = palette[Math.floor(Math.random() * palette.length)];
      const c2 = palette[Math.floor(Math.random() * palette.length)];
      const mix = Math.random();
      const finalColor = new THREE.Color().lerpColors(c1, c2, mix);

      colors[i * 3] = finalColor.r;
      colors[i * 3 + 1] = finalColor.g;
      colors[i * 3 + 2] = finalColor.b;

      lives[i] = Math.random();
    }

    return { positions, sizes, phases, colors, lives };
  }, [count]);

  useFrame((state) => {
    if (!matRef.current) return;
    matRef.current.uTime = state.clock.elapsedTime;
    matRef.current.uExplosion = explosionIntensity;
    matRef.current.uPixelRatio = gl.getPixelRatio();

    // Rotación lenta de todo el sistema de partículas
    if (pointsRef.current) {
      pointsRef.current.rotation.y = state.clock.elapsedTime * 0.08;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-aSize"
          args={[sizes, 1]}
        />
        <bufferAttribute
          attach="attributes-aPhase"
          args={[phases, 1]}
        />
        <bufferAttribute
          attach="attributes-aColor"
          args={[colors, 3]}
        />
        <bufferAttribute
          attach="attributes-aLife"
          args={[lives, 1]}
        />
      </bufferGeometry>
      <particlesMaterial
        ref={matRef}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}
