import { useState, useRef, useCallback } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text } from '@react-three/drei'
import { useControls, folder } from 'leva'
import * as THREE from 'three'
import { LambertSphere, PhongSphere } from './components/CustomShaderSpheres'

// ============================================================
// Escena de comparación de modelos de iluminación
// ============================================================

/**
 * Esfera con material built-in de Three.js.
 * Soporta Lambert, Phong y PBR Standard.
 */
function BuiltinSphere({ position, type, color, shininess, metalness, roughness }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[1, 64, 64]} />
      {type === 'lambert' && (
        <meshLambertMaterial color={color} />
      )}
      {type === 'phong' && (
        <meshPhongMaterial color={color} shininess={shininess} />
      )}
      {type === 'standard' && (
        <meshStandardMaterial
          color={color}
          metalness={metalness}
          roughness={roughness}
        />
      )}
    </mesh>
  )
}

/**
 * Etiqueta de texto debajo de cada esfera.
 */
function SphereLabel({ position, text }) {
  return (
    <Text
      position={[position[0], position[1] - 1.6, position[2]]}
      fontSize={0.22}
      color="#8cbfff"
      anchorX="center"
      anchorY="top"
      font={undefined}
    >
      {text}
    </Text>
  )
}

/**
 * Luz orbital que rota alrededor de la escena.
 * Actualiza su posición cada frame y expone la dirección normalizada.
 */
function OrbitalLight({ speed, radius, height, onDirectionChange }) {
  const lightRef = useRef()
  const indicatorRef = useRef()

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime() * speed
    const x = Math.cos(t) * radius
    const z = Math.sin(t) * radius

    if (lightRef.current) {
      lightRef.current.position.set(x, height, z)
    }
    if (indicatorRef.current) {
      indicatorRef.current.position.set(x, height, z)
    }

    // Pasar dirección normalizada a los shaders custom
    const len = Math.sqrt(x * x + height * height + z * z)
    onDirectionChange([x / len, height / len, z / len])
  })

  return (
    <>
      <directionalLight ref={lightRef} intensity={1.2} color="#ffffff" />
      <mesh ref={indicatorRef}>
        <sphereGeometry args={[0.08, 12, 12]} />
        <meshBasicMaterial color="#ffdd44" />
      </mesh>
    </>
  )
}

/**
 * Plano de piso con sombra suave.
 */
function Floor() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.2, 0]} receiveShadow>
      <planeGeometry args={[30, 30]} />
      <meshStandardMaterial color="#1a1a22" roughness={0.9} metalness={0} />
    </mesh>
  )
}

/**
 * Escena principal: fila de esferas con modelos built-in de Three.js
 * + controles interactivos con leva.
 */
function BuiltinComparison() {
  const {
    shininess,
    metalness,
    roughness,
    color,
    lightSpeed,
    lightRadius,
  } = useControls({
    'Material': folder({
      color: '#c8663c',
      shininess: { value: 48, min: 1, max: 256, step: 1 },
      metalness: { value: 0.4, min: 0, max: 1, step: 0.01 },
      roughness: { value: 0.35, min: 0, max: 1, step: 0.01 },
    }),
    'Luz Orbital': folder({
      lightSpeed: { value: 0.5, min: 0.1, max: 2.0, step: 0.1 },
      lightRadius: { value: 6, min: 2, max: 12, step: 0.5 },
    }),
  })

  const [lightDir, setLightDir] = useState([0.5, 0.5, 0.9])

  const handleLightChange = useCallback((dir) => {
    setLightDir(dir)
  }, [])

  const spacing = 3.5
  const y = 0

  return (
    <>
      {/* Luz orbital */}
      <OrbitalLight
        speed={lightSpeed}
        radius={lightRadius}
        height={4}
        onDirectionChange={handleLightChange}
      />

      {/* Luz ambiente tenue */}
      <ambientLight intensity={0.08} />

      {/* --- Fila de materiales built-in --- */}

      {/* MeshLambertMaterial */}
      <BuiltinSphere
        position={[-spacing, y, 0]}
        type="lambert"
        color={color}
      />
      <SphereLabel position={[-spacing, y, 0]} text="MeshLambertMaterial" />

      {/* MeshPhongMaterial */}
      <BuiltinSphere
        position={[0, y, 0]}
        type="phong"
        color={color}
        shininess={shininess}
      />
      <SphereLabel position={[0, y, 0]} text={`MeshPhongMaterial (shine=${shininess})`} />

      {/* MeshStandardMaterial (PBR) */}
      <BuiltinSphere
        position={[spacing, y, 0]}
        type="standard"
        color={color}
        metalness={metalness}
        roughness={roughness}
      />
      <SphereLabel
        position={[spacing, y, 0]}
        text={`MeshStandardMaterial (M=${metalness} R=${roughness})`}
      />

      {/* --- Fila de shaders custom (detrás) --- */}

      {/* Lambert custom */}
      <LambertSphere
        position={[-spacing * 0.75, y, -spacing]}
        lightDir={lightDir}
        color={color}
      />
      <SphereLabel position={[-spacing * 0.75, y, -spacing]} text="Custom Lambert (GLSL)" />

      {/* Phong custom */}
      <PhongSphere
        position={[0, y, -spacing]}
        lightDir={lightDir}
        color={color}
        shininess={shininess}
        useBlinnPhong={false}
      />
      <SphereLabel position={[0, y, -spacing]} text="Custom Phong (GLSL)" />

      {/* Blinn-Phong custom */}
      <PhongSphere
        position={[spacing * 0.75, y, -spacing]}
        lightDir={lightDir}
        color={color}
        shininess={shininess}
        useBlinnPhong={true}
      />
      <SphereLabel position={[spacing * 0.75, y, -spacing]} text="Custom Blinn-Phong (GLSL)" />

      <Floor />
    </>
  )
}

// ============================================================
// App principal
// ============================================================

export default function App() {
  return (
    <Canvas
      camera={{ position: [0, 2, 10], fov: 50 }}
      style={{ background: '#121216' }}
    >
      <BuiltinComparison />
      <OrbitControls
        enableDamping
        dampingFactor={0.08}
        minDistance={4}
        maxDistance={20}
      />
    </Canvas>
  )
}
