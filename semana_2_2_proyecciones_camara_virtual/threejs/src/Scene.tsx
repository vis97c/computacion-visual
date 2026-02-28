import { PerspectiveCamera, OrthographicCamera, OrbitControls } from "@react-three/drei";
import { useThree, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";

type Props = {
  isPerspective: boolean;
};

export default function Scene({ isPerspective }: Props) {
  const { size } = useThree();
  const aspect = size.width / size.height;

  const perspectiveRef = useRef<THREE.PerspectiveCamera>(null!);
  const orthoRef = useRef<THREE.OrthographicCamera>(null!);

  // Bonus: proyectar punto
  useFrame(() => {
    const camera = isPerspective ? perspectiveRef.current : orthoRef.current;
    const point = new THREE.Vector3(0, 0, 0);
    point.project(camera);
    console.log("Proyección 2D:", point);
  });

  return (
    <>
      {isPerspective ? (
        <PerspectiveCamera
          ref={perspectiveRef}
          makeDefault
          position={[0, 2, 8]}
          fov={60}
          near={0.1}
          far={100}
        />
      ) : (
        <OrthographicCamera
          ref={orthoRef}
          makeDefault
          position={[0, 2, 8]}
          left={-5 * aspect}
          right={5 * aspect}
          top={5}
          bottom={-5}
          near={0.1}
          far={100}
        />
      )}

      <OrbitControls />

      {/* Luces */}
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />

      {/* Objetos distribuidos */}
      <Box position={[-3, 0, 0]}/>
      <Box position={[0, 0, -5]} />
      <Sphere position={[3, 0, -10]} />
    </>
  );
}

function Box({ position }: { position: [number, number, number] }) {
  return (
    <mesh position={position}>
      <boxGeometry />
      <meshStandardMaterial color="orange" />
    </mesh>
  );
}

function Sphere({ position }: { position: [number, number, number] }) {
  return (
    <mesh position={position}>
      <sphereGeometry />
      <meshStandardMaterial color="skyblue" />
    </mesh>
  );
}