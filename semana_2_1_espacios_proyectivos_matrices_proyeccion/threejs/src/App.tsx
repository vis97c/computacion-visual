import { Suspense, useState } from "react";
import { Canvas } from "@react-three/fiber";
import {
	PerspectiveCamera,
	OrthographicCamera,
	OrbitControls,
	Environment,
	ContactShadows,
	Float,
} from "@react-three/drei";

import "./App.css";

function CustomScene() {
	return (
		<group>
			{/* Objeto 1: Cerca (Profundidad positiva) */}
			<Float speed={2} rotationIntensity={1} floatIntensity={1}>
				<mesh position={[0, 0, 2]}>
					<sphereGeometry args={[0.6, 32, 32]} />
					<meshStandardMaterial color="#ff4d4d" roughness={0.1} metalness={0.8} />
				</mesh>
			</Float>

			{/* Objeto 2: Centro (Profundidad cero) */}
			<Float speed={1.5} rotationIntensity={0.5} floatIntensity={0.5}>
				<mesh position={[2, 0, 0]}>
					<boxGeometry args={[1, 1, 1]} />
					<meshStandardMaterial color="#4d79ff" roughness={0.2} metalness={0.5} />
				</mesh>
			</Float>

			{/* Objeto 3: Lejos (Profundidad negativa) */}
			<Float speed={2.5} rotationIntensity={1.5} floatIntensity={1.2}>
				<mesh position={[-2, 0, -2]}>
					<torusKnotGeometry args={[0.5, 0.15, 128, 16]} />
					<meshStandardMaterial color="#4dff88" roughness={0.3} metalness={0.6} />
				</mesh>
			</Float>

			{/* Piso para referencia de profundidad */}
			<gridHelper args={[20, 20, 0x888888, 0x444444]} position={[0, -1, 0]} />
			<ContactShadows position={[0, -1, 0]} opacity={0.4} scale={20} blur={24} far={4.5} />
		</group>
	);
}

function App() {
	const [cameraType, setCameraType] = useState<"perspective" | "orthographic">("perspective");

	return (
		<main id="container">
			<div className="ui-overlay">
				<h1>Exploración de Proyecciones</h1>
				<p>Observa cómo cambia la percepción de profundidad entre cámaras.</p>

				<div className="controls">
					<button
						className={cameraType === "perspective" ? "active" : ""}
						onClick={() => setCameraType("perspective")}
					>
						Perspectiva
					</button>
					<button
						className={cameraType === "orthographic" ? "active" : ""}
						onClick={() => setCameraType("orthographic")}
					>
						Ortográfica
					</button>
				</div>

				<div className="info-box">
					{cameraType === "perspective" ? (
						<p>
							<strong>Cámara de Perspectiva:</strong> Los objetos más alejados se ven
							más pequeños (punto de fuga). Imita la visión humana.
						</p>
					) : (
						<p>
							<strong>Cámara Ortográfica:</strong> El tamaño de los objetos es
							constante sin importar la distancia. Las líneas paralelas se mantienen
							paralelas.
						</p>
					)}
				</div>
			</div>

			<section id="canvas-container">
				<Canvas>
					<Suspense fallback={null}>
						{/* Cámara Perspectiva */}
						{cameraType === "perspective" && (
							<PerspectiveCamera makeDefault position={[5, 3, 5]} fov={50} />
						)}
						{/* Cámara Ortográfica */}
						{cameraType === "orthographic" && (
							<OrthographicCamera
								makeDefault
								position={[5, 5, 5]}
								zoom={80}
								near={0.1}
								far={1000}
							/>
						)}
						<CustomScene />
						<OrbitControls />
						<Environment preset="city" />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
