import { Suspense, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls, Stars } from "@react-three/drei";
import { Link } from "react-router-dom";
import * as THREE from "three";

function AnimatedShapes() {
	const cubeRef = useRef<THREE.Mesh>(null!);
	const sphereRef = useRef<THREE.Mesh>(null!);

	useFrame((state, delta) => {
		if (cubeRef.current) {
			cubeRef.current.rotation.x += delta * 0.5;
			cubeRef.current.rotation.y += delta * 0.5;
		}
		if (sphereRef.current) {
			sphereRef.current.position.y = Math.sin(state.clock.elapsedTime) * 0.5 + 1;
		}
	});

	return (
		<>
			<mesh ref={cubeRef} position={[-2, 1, 0]}>
				<boxGeometry args={[1, 1, 1]} />
				<meshStandardMaterial color="hotpink" />
			</mesh>
			<mesh ref={sphereRef} position={[2, 1, 0]}>
				<sphereGeometry args={[0.7, 32, 32]} />
				<meshStandardMaterial color="cyan" />
			</mesh>
		</>
	);
}

export default function Juego() {
	return (
		<main id="container" className="bg-black">
			<div className="ui-overlay">
				<Link to="/" className="btn-secondary">Volver al Menú</Link>
				<Link to="/creditos" className="btn-primary">Finalizar Juego</Link>
			</div>
			<section id="canvas-container">
				<Canvas camera={{ position: [0, 2, 5], fov: 45 }}>
					<Suspense fallback={null}>
						<OrbitControls
							makeDefault
							minDistance={2}
							maxDistance={10}
							target={[0, 1, 0]}
						/>
						<Environment preset="city" />
						<Stars
							radius={100}
							depth={50}
							count={3000}
							factor={4}
							saturation={0}
							fade
							speed={1}
						/>
						<gridHelper args={[20, 20, 0x333333, 0x111111]} position={[0, 0, 0]} />
						<AnimatedShapes />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}
