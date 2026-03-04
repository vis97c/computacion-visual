import { useRef, useState, useMemo, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls } from "@react-three/drei";
import { Matrix4, Mesh, Group } from "three";

import "./App.css";

function SolarSystem({
	setActiveMatrix,
}: {
	activeMatrix: Matrix4;
	setActiveMatrix: (matrix: Matrix4) => void;
}) {
	const sunRef = useRef<Group>(null!);
	const earthPivotRef = useRef<Group>(null!);
	const earthSystemRef = useRef<Mesh>(null!);
	const moonPivotRef = useRef<Group>(null!);
	const moonRef = useRef<Mesh>(null!);
	const earthRef = useRef<Mesh>(null!);

	useFrame((state) => {
		const time = state.clock.getElapsedTime();

		// matrices temporales para cálculos manuales
		const mTranslate = new Matrix4();
		const mRotate = new Matrix4();

		// 1. Transformación del Sol (Rotación sobre sí mismo)
		sunRef.current.matrixAutoUpdate = false;
		sunRef.current.matrix.copy(mRotate.makeRotationY(time * 0.2));
		sunRef.current.updateMatrixWorld();

		// 2.1. Transformación del Pivote de la Tierra (Traslación + Rotación = Orbita)
		earthPivotRef.current.matrixAutoUpdate = false;
		earthPivotRef.current.matrix.copy(mRotate.makeRotationY(time * 0.1));
		earthPivotRef.current.updateMatrixWorld();

		// 2.2. Transformación de la Tierra (Posición local respecto al Sol)
		earthSystemRef.current.matrixAutoUpdate = false;
		// Radio de órbita, composición de matrices
		earthSystemRef.current.matrix
			.copy(mTranslate.makeTranslation(5, 0, 0)) // Radio de órbita
			.multiply(mRotate.makeRotationY(time * 2)); // Rotación sobre su propio eje
		earthSystemRef.current.updateMatrixWorld();

		// 2.3. Rotación de la Tierra (Local)
		earthRef.current.matrixAutoUpdate = false;
		earthRef.current.matrix.copy(mRotate.makeRotationY(time * 0.7));
		earthRef.current.updateMatrixWorld();

		// 3.1. Transformación del Pivote de la Luna (Sigue a la Tierra)
		// La luna tiene bloqueo de marea respecto a la Tierra
		moonPivotRef.current.matrixAutoUpdate = false;
		moonPivotRef.current.matrix.copy(mRotate.makeRotationY(time * 0.1));
		moonPivotRef.current.updateMatrixWorld();

		// 3.2. Transformación de la Luna (Traslación local respecto a la Tierra)
		moonRef.current.matrixAutoUpdate = false;
		// Radio de órbita, composición de matrices
		moonRef.current.matrix
			.copy(mTranslate.makeTranslation(1.5, 0, 0)) // Distancia a la Tierra
			.multiply(mRotate.makeRotationY(time * 0.1)); // Rotación sobre su propio eje, bloqueo de marea
		moonRef.current.updateMatrixWorld();

		// Actualizar matriz visualizada (Mundo de la Luna)
		const worldMatrix = new Matrix4();

		moonRef.current.applyMatrix4(worldMatrix);
		setActiveMatrix(worldMatrix.clone());
	});

	return (
		<group ref={sunRef}>
			{/* Sol */}
			<mesh>
				<sphereGeometry args={[1.5, 32, 32]} />
				<meshStandardMaterial color="#fbbf24" emissive="#f59e0b" emissiveIntensity={2} />
			</mesh>

			{/* Sistema Tierra (Hijo del Sol) */}
			<group ref={earthPivotRef}>
				<group ref={earthSystemRef}>
					{/* Tierra */}
					<group ref={earthRef}>
						<mesh>
							<sphereGeometry args={[0.5, 32, 32]} />
							<meshStandardMaterial color="#3b82f6" roughness={0.3} />
						</mesh>
						<axesHelper args={[1.5]} />
					</group>

					{/* Sistema Luna (Hijo de la Tierra) */}
					<group ref={moonPivotRef}>
						<group ref={moonRef}>
							<mesh>
								{/* Luna */}
								<sphereGeometry args={[0.25, 16, 16]} />
								<meshStandardMaterial color="#94a3b8" />
							</mesh>
							<axesHelper args={[0.5]} />
						</group>
					</group>
				</group>
			</group>
			<axesHelper args={[3]} />
		</group>
	);
}

function App() {
	const [activeMatrix, setActiveMatrix] = useState<Matrix4>(new Matrix4());
	const elements = useMemo(() => activeMatrix.elements, [activeMatrix]);

	return (
		<main id="container">
			<div className="overlay">
				<h1>Sistemas de Coordenadas y Matrices</h1>
				<p>Jerarquía: Sol → Tierra → Luna</p>
			</div>

			<section id="canvas-container">
				<Canvas camera={{ position: [8, 8, 8], fov: 45 }}>
					<Suspense fallback={null}>
						<pointLight position={[0, 0, 0]} intensity={20} color="#fff176" />

						<SolarSystem
							activeMatrix={activeMatrix}
							setActiveMatrix={setActiveMatrix}
						/>

						<OrbitControls makeDefault />
						<Environment preset="night" />
						<gridHelper args={[20, 20, 0x333333, 0x111111]} position={[0, -2, 0]} />
					</Suspense>
				</Canvas>
				<div className="matrix-panel">
					<div className="label">Matriz de Transformación (Mundo)</div>
					<div className="matrix-grid">
						{Array.from(elements).map((val, i) => (
							<span key={i} className="matrix-cell">
								{val.toFixed(2)}
							</span>
						))}
					</div>
				</div>
			</section>

			<ul id="canvas-options">
				<li>Transformaciones Manuales (Matrix4)</li>
				<li>Jerarquía Anidada: World vs Local</li>
				<li>Composición: T * R * S</li>
			</ul>
		</main>
	);
}

export default App;
