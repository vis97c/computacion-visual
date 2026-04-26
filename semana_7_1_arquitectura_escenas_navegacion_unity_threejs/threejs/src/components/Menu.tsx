import { Link } from "react-router-dom";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls, Stars } from "@react-three/drei";
import { Suspense, useRef } from "react";
import * as THREE from "three";

function RotatingGroup() {
	const groupRef = useRef<THREE.Group>(null!);

	useFrame((_, delta) => {
		if (groupRef.current) {
			groupRef.current.rotation.y += delta * 0.1;
			groupRef.current.rotation.x += delta * 0.05;
		}
	});

	// Creamos un arreglo de octaedros flotantes con colores neón
	return (
		<group ref={groupRef}>
			{Array.from({ length: 40 }).map((_, i) => (
				<mesh
					key={i}
					position={[
						(Math.random() - 0.5) * 15,
						(Math.random() - 0.5) * 15,
						(Math.random() - 0.5) * 15,
					]}
				>
					<octahedronGeometry args={[Math.random() * 0.4 + 0.1]} />
					<meshStandardMaterial
						color={new THREE.Color().setHSL(Math.random(), 0.8, 0.6)}
						wireframe
					/>
				</mesh>
			))}
		</group>
	);
}

export default function Menu() {
	return (
		<main id="container" className="bg-black">
			{/* Fondo 3D interactivo */}
			<section className="canvas-background">
				<Canvas camera={{ position: [0, 0, 8], fov: 60 }}>
					<Suspense fallback={null}>
						<ambientLight intensity={0.2} />
						<pointLight position={[10, 10, 10]} intensity={1.5} />
						<Stars
							radius={100}
							depth={50}
							count={3000}
							factor={4}
							saturation={0}
							fade
							speed={1}
						/>
						<RotatingGroup />
						<Environment preset="city" />
						<OrbitControls
							autoRotate
							autoRotateSpeed={0.5}
							enableZoom={false}
							enablePan={false}
						/>
					</Suspense>
				</Canvas>
			</section>

			{/* Tarjeta de interfaz superpuesta con Glassmorphism */}
			<div className="menu-overlay">
				<div className="menu-card">
					<h1 className="menu-title">The game</h1>
					<p className="menu-subtitle">Electric Boogaloo</p>

					<div className="menu-options-container">
						<Link to="/juego" className="btn-primary btn-game-start">
							Iniciar Juego
						</Link>
						<Link to="/creditos" className="btn-secondary">
							Créditos
						</Link>
					</div>
				</div>
			</div>
		</main>
	);
}
