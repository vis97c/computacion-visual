import { useRef, useCallback, useState } from "react";
import { useFrame, extend } from "@react-three/fiber";
import * as THREE from "three";
import { EnergySphereMaterial } from "../shaders/energySphere";

// Registrar el material personalizado con R3F
extend({ EnergySphereMaterial });

// Extender ThreeElements para TypeScript (R3F > 8)
declare module "@react-three/fiber" {
  interface ThreeElements {
    energySphereMaterial: any;
  }
}

interface EnergySphereProps {
  onExplosion: () => void;
  explosionIntensity: number;
}

/**
 * EnergySphere — El objeto central de la escena.
 * Una esfera de alta poligonización usando un material shader GLSL personalizado
 * para simular plasma/energía con desplazamiento animado de ruido FBM.
 *
 * Interactividad:
 * - Hover: aumenta la intensidad del resplandor y la amplitud del desplazamiento
 * - Movimiento del ratón: desplaza los reflejos de color hacia el cursor
 * - Click: dispara el callback de explosión
 */
export default function EnergySphere({
  onExplosion,
  explosionIntensity,
}: EnergySphereProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const matRef = useRef<any>(null);
  const [hovered, setHovered] = useState(false);
  const hoverRef = useRef(0);
  const mouseRef = useRef(new THREE.Vector2(0.5, 0.5));

  // Interpolación suave del hover
  useFrame((state, delta) => {
    if (!matRef.current) return;

    // Actualizar tiempo
    matRef.current.uTime = state.clock.elapsedTime;

    // Hover suave
    const targetHover = hovered ? 1.0 : 0.0;
    hoverRef.current = THREE.MathUtils.lerp(
      hoverRef.current,
      targetHover,
      delta * 4
    );
    matRef.current.uHover = hoverRef.current;

    // Explosión
    matRef.current.uExplosion = explosionIntensity;

    // UV del ratón
    const { x, y } = state.pointer;
    mouseRef.current.set(x * 0.5 + 0.5, y * 0.5 + 0.5);
    matRef.current.uMouse = mouseRef.current;

    // Rotación suave
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.15;
      meshRef.current.rotation.x += delta * 0.05;
    }
  });

  const handlePointerOver = useCallback(() => {
    setHovered(true);
    document.body.style.cursor = "pointer";
  }, []);

  const handlePointerOut = useCallback(() => {
    setHovered(false);
    document.body.style.cursor = "default";
  }, []);

  const handleClick = useCallback(() => {
    onExplosion();
  }, [onExplosion]);

  return (
    <mesh
      ref={meshRef}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
      onClick={handleClick}
    >
      <icosahedronGeometry args={[1.4, 64]} />
      <energySphereMaterial
        ref={matRef}
        transparent
        depthWrite={false}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}
