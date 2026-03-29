import { Suspense, useState, useCallback, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import * as THREE from "three";
import EnergySphere from "./components/EnergySphere";
import ParticleSystem from "./components/ParticleSystem";
import ExplosionParticles from "./components/ExplosionParticles";
import HudOverlay from "./components/HudOverlay";
import "./App.css";

const PARTICLE_COUNT = 2000;

/**
 * ExplosionController — maneja el estado de la animación de explosión
 * dentro del ciclo de renderizado de R3F. Disminuye la intensidad suavemente.
 */
function ExplosionController({
  explosionRef,
}: {
  explosionRef: React.MutableRefObject<number>;
}) {
  useFrame((_, delta) => {
    if (explosionRef.current > 0) {
      explosionRef.current = Math.max(0, explosionRef.current - delta * 1.2);
    }
  });
  return null;
}

/**
 * SceneContent — todo el contenido 3D envuelto junto,
 * leyendo la intensidad de la explosión desde una referencia para sincronización perfecta de frames.
 */
function SceneContent({
  explosionRef,
  onExplosion,
}: {
  explosionRef: React.MutableRefObject<number>;
  onExplosion: () => void;
}) {
  const [intensity, setIntensity] = useState(0);

  useFrame(() => {
    setIntensity(explosionRef.current);
  });

  return (
    <>
      <EnergySphere
        onExplosion={onExplosion}
        explosionIntensity={intensity}
      />
      <ParticleSystem
        count={PARTICLE_COUNT}
        explosionIntensity={intensity}
      />
      <ExplosionParticles
        active={intensity > 0.01}
        intensity={intensity}
      />
    </>
  );
}

function App() {
  const [explosionCount, setExplosionCount] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const explosionRef = useRef(0);

  const handleExplosion = useCallback(() => {
    explosionRef.current = 1.0;
    setExplosionCount((c) => c + 1);
  }, []);

  return (
    <main id="container">
      <section id="canvas-container">
        <Canvas
          camera={{ position: [0, 0, 5.5], fov: 55 }}
          gl={{
            antialias: true,
            toneMapping: THREE.ACESFilmicToneMapping,
            toneMappingExposure: 1.2,
          }}
          dpr={[1, 2]}
        >
          <Suspense fallback={null}>
            {/* Iluminación */}
            <ambientLight intensity={0.15} />
            <pointLight
              position={[5, 5, 5]}
              intensity={0.5}
              color="#00e5ff"
            />
            <pointLight
              position={[-5, -3, -5]}
              intensity={0.3}
              color="#e040fb"
            />

            {/* Estrellas de fondo */}
            <Stars
              radius={50}
              depth={80}
              count={3000}
              factor={3}
              saturation={0.2}
              fade
              speed={0.5}
            />

            {/* Controles */}
            <OrbitControls
              makeDefault
              enableDamping
              dampingFactor={0.05}
              minDistance={3}
              maxDistance={12}
              autoRotate
              autoRotateSpeed={0.3}
            />

            {/* Controlador de explosión */}
            <ExplosionController explosionRef={explosionRef} />

            {/* Contenido principal de la escena */}
            <SceneContent
              explosionRef={explosionRef}
              onExplosion={handleExplosion}
            />

            {/* Post-procesamiento bloom */}
            <EffectComposer>
              <Bloom
                intensity={0.8}
                luminanceThreshold={0.2}
                luminanceSmoothing={0.9}
                mipmapBlur
              />
            </EffectComposer>
          </Suspense>
        </Canvas>
      </section>

      {/* Interfaz Gráfica (HUD) */}
      <HudOverlay
        particleCount={PARTICLE_COUNT + 800}
        explosionCount={explosionCount}
        isHovered={isHovered}
      />
    </main>
  );
}

export default App;
