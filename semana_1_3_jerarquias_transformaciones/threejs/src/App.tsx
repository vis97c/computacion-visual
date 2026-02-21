import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls, Grid } from "@react-three/drei";
import { Suspense } from "react";
import { useControls } from "leva";
import "./App.css";

function Scene() {
	// Parent controls
	const parentParams = useControls("Parent (Group 1)", {
		position: { value: [0, 0, 0], step: 0.1 },
		rotation: { value: [0, 0, 0], step: 0.01 },
		visible: true,
	});

	// Child controls
	const childParams = useControls("Child (Group 2)", {
		position: { value: [2, 0, 0], step: 0.1 },
		rotation: { value: [0, 0, 0], step: 0.01 },
		visible: true,
	});

	// Grandchild controls
	const grandchildParams = useControls("Grandchild (Group 3)", {
		position: { value: [1.5, 0, 0], step: 0.1 },
		rotation: { value: [0, 0, 0], step: 0.01 },
		visible: true,
	});

	return (
		<>
			<OrbitControls makeDefault />
			<Grid infiniteGrid fadeDistance={50} cellColor="#444" sectionColor="#888" />
			<ambientLight intensity={0.5} />
			<pointLight position={[10, 10, 10]} intensity={1} />

			{/* Level 1: Parent */}
			<group
				position={parentParams.position}
				rotation={parentParams.rotation}
				visible={parentParams.visible}
			>
				<mesh>
					<boxGeometry args={[1, 1, 1]} />
					<meshStandardMaterial color="#3498db" />
				</mesh>

				{/* Level 2: Child (inside Parent) */}
				<group
					position={childParams.position}
					rotation={childParams.rotation}
					visible={childParams.visible}
				>
					<mesh>
						<sphereGeometry args={[0.5, 32, 32]} />
						<meshStandardMaterial color="#2ecc71" />
					</mesh>

					{/* Level 3: Grandchild (inside Child) */}
					<group
						position={grandchildParams.position}
						rotation={grandchildParams.rotation}
						visible={grandchildParams.visible}
					>
						<mesh>
							<torusGeometry args={[0.3, 0.1, 16, 100]} />
							<meshStandardMaterial color="#e74c3c" />
						</mesh>
					</group>
				</group>
			</group>
		</>
	);
}

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas camera={{ position: [5, 5, 5], fov: 50 }}>
					<Suspense fallback={null}>
						<Scene />
						<Environment preset="city" />
					</Suspense>
				</Canvas>
			</section>
			<div className="info-panel">
				<h1>Jerarquía de Transformaciones 3D</h1>
				<p>Usa los controles de la derecha para manipular los nodos.</p>
				<ul>
					<li>
						<span style={{ color: "#3498db" }}>■</span> Cubo: Padre
					</li>
					<li>
						<span style={{ color: "#2ecc71" }}>●</span> Esfera: Hijo
					</li>
					<li>
						<span style={{ color: "#e74c3c" }}>◎</span> Toro: Nieto
					</li>
				</ul>
			</div>
		</main>
	);
}

export default App;
