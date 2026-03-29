import { useRef, useMemo } from "react";
import { useFrame, extend } from "@react-three/fiber";
import * as THREE from "three";
import { ParticlesMaterial } from "../shaders/particles";

extend({ ParticlesMaterial });

// Extend ThreeElements for TypeScript
declare module "@react-three/fiber" {
  interface ThreeElements {
    particlesMaterial: any;
  }
}

interface ExplosionParticlesProps {
  active: boolean;
  intensity: number;
}

/**
 * ExplosionParticles — Partículas de ráfaga que aparecen al hacer clic.
 *
 * Estas partículas son más densas y están más cerca de la superficie de la esfera,
 * creando un efecto de ráfaga radial impulsado por el uniform de explosión.
 * Utiliza colores más brillantes y cálidos para el destello de la explosión.
 */
export default function ExplosionParticles({
  active,
  intensity,
}: ExplosionParticlesProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const matRef = useRef<any>(null);

  const count = 800;

  const { positions, sizes, phases, colors, lives } = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const phases = new Float32Array(count);
    const colors = new Float32Array(count * 3);
    const lives = new Float32Array(count);

    const palette = [
      new THREE.Color("#ffffff"),
      new THREE.Color("#ffd740"),
      new THREE.Color("#ff6e40"),
      new THREE.Color("#00e5ff"),
      new THREE.Color("#e040fb"),
    ];

    for (let i = 0; i < count; i++) {
      // Capa ajustada en la superficie de la esfera
      const radius = 1.3 + Math.random() * 0.4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      sizes[i] = Math.pow(Math.random(), 1.5) * 1.2 + 0.3;
      phases[i] = Math.random() * Math.PI * 2;

      const c = palette[Math.floor(Math.random() * palette.length)];
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;

      lives[i] = Math.random();
    }

    return { positions, sizes, phases, colors, lives };
  }, []);

  useFrame((state) => {
    if (!matRef.current) return;
    matRef.current.uTime = state.clock.elapsedTime;
    matRef.current.uExplosion = intensity;
    matRef.current.uPixelRatio = state.gl.getPixelRatio();
  });

  if (!active && intensity < 0.01) return null;

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-aSize" args={[sizes, 1]} />
        <bufferAttribute attach="attributes-aPhase" args={[phases, 1]} />
        <bufferAttribute attach="attributes-aColor" args={[colors, 3]} />
        <bufferAttribute attach="attributes-aLife" args={[lives, 1]} />
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
