import { useRef, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls } from "@react-three/drei";
import { Mesh } from "three";

import "./App.css";

function AnimatedBox() {
	const meshRef = useRef<Mesh>(null!);

	useFrame((state) => {
		const time = state.clock.getElapsedTime();

		// 1. Trayectoria sinusoidal (traslación)
		// Movemos en X de forma lineal y en Y de forma sinusoidal
		meshRef.current.position.x = Math.sin(time) * 2;
		meshRef.current.position.y = Math.cos(time) * 2;

		// 2. Rotación sobre su propio eje
		meshRef.current.rotation.x += 0.01;
		meshRef.current.rotation.y += 0.01;

		// 3. Escalamiento suave
		const scale = 1 + Math.sin(time) * 0.5;
		meshRef.current.scale.set(scale, scale, scale);
	});

	return (
		<mesh ref={meshRef}>
			<boxGeometry args={[1, 1, 1]} />
			<meshStandardMaterial color="mediumpurple" />
		</mesh>
	);
}

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas camera={{ position: [0, 0, 5] }}>
					<Suspense fallback={null}>
						<ambientLight intensity={0.5} />
						<pointLight position={[10, 10, 10]} />
						<AnimatedBox />
						<OrbitControls />
						<Environment preset="apartment" background />
					</Suspense>
				</Canvas>
			</section>
			<ul id="canvas-options">
				<li>Objeto Animado: Cubo con Escala, Rotación y Traslación</li>
			</ul>
		</main>
	);
}

export default App;
