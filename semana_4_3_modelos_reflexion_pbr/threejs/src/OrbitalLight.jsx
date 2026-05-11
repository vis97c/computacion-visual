import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'

/**
 * Luz direccional que orbita alrededor de la escena.
 * Expone la dirección actual de la luz via callback.
 */
export function OrbitalLight({ speed = 0.5, radius = 5, height = 3, onUpdate }) {
  const lightRef = useRef()

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime() * speed
    const x = Math.cos(t) * radius
    const z = Math.sin(t) * radius

    if (lightRef.current) {
      lightRef.current.position.set(x, height, z)
    }

    // Notificar la dirección normalizada de la luz
    if (onUpdate) {
      const len = Math.sqrt(x * x + height * height + z * z)
      onUpdate([x / len, height / len, z / len])
    }
  })

  return (
    <>
      <directionalLight
        ref={lightRef}
        intensity={1.2}
        color="#ffffff"
        castShadow
      />
      {/* Indicador visual de la posición de la luz */}
      <mesh ref={(mesh) => {
        if (mesh && lightRef.current) {
          mesh.position.copy(lightRef.current.position)
        }
      }}>
        <sphereGeometry args={[0.1, 16, 16]} />
        <meshBasicMaterial color="#ffdd44" />
      </mesh>
    </>
  )
}
