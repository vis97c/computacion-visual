import { Suspense, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useControls } from "leva";
import * as THREE from "three";
import "./App.css";

function Scene() {
	const { ambientIntensity, ambientColor } = useControls("Ambient Light", {
		ambientIntensity: { value: 0.5, min: 0, max: 2, step: 0.1 },
		ambientColor: "#ffffff",
	});

	const { dirIntensity, dirColor, dirPosX, dirPosY, dirPosZ } = useControls("Directional Light", {
		dirIntensity: { value: 1, min: 0, max: 5, step: 0.1 },
		dirColor: "#ffffff",
		dirPosX: { value: 10, min: -20, max: 20 },
		dirPosY: { value: 10, min: 0, max: 20 },
		dirPosZ: { value: 10, min: -20, max: 20 },
	});

	const { pointIntensity, pointColor, pointPosX, pointPosY, pointPosZ, pointDistance } =
		useControls("Point Light", {
			pointIntensity: { value: 1.5, min: 0, max: 10, step: 0.1 },
			pointColor: "#ff0000",
			pointPosX: { value: -2, min: -10, max: 10 },
			pointPosY: { value: 3, min: 0, max: 10 },
			pointPosZ: { value: 1, min: -10, max: 10 },
			pointDistance: { value: 20, min: 0, max: 100 },
		});

	const boxRef = useRef<THREE.Mesh>(null!);
	const sphereRef = useRef<THREE.Mesh>(null!);
	const knotRef = useRef<THREE.Mesh>(null!);

	useFrame((state) => {
		const t = state.clock.getElapsedTime();
		boxRef.current.rotation.y = t * 0.4;
		sphereRef.current.position.y = 1 + Math.sin(t) * 0.5;
		knotRef.current.rotation.x = t * 0.3;
		knotRef.current.rotation.z = t * 0.2;
	});

	return (
		<>
			<color attach="background" args={["#101010"]} />
			<ambientLight intensity={ambientIntensity} color={ambientColor} />
			<directionalLight
				castShadow
				position={[dirPosX, dirPosY, dirPosZ]}
				intensity={dirIntensity}
				color={dirColor}
				shadow-mapSize={[1024, 1024]}
			/>
			<pointLight
				castShadow
				position={[pointPosX, pointPosY, pointPosZ]}
				intensity={pointIntensity}
				color={pointColor}
				distance={pointDistance}
				shadow-mapSize={[512, 512]}
			/>
			{/* Piso (Para que se vea que hay sombras) */}
			<mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, 0, 0]}>
				<planeGeometry args={[50, 50]} />
				<meshStandardMaterial color="#303030" roughness={0.8} metalness={0.2} />
			</mesh>
			{/* Objetos */}
			<mesh ref={boxRef} position={[-3, 1, 0]} castShadow receiveShadow>
				<boxGeometry args={[1.5, 1.5, 1.5]} />
				<meshStandardMaterial color="#ffcc00" roughness={0.3} metalness={0.8} />
			</mesh>
			<mesh ref={sphereRef} position={[0, 1.5, -2]} castShadow receiveShadow>
				<sphereGeometry args={[1, 32, 32]} />
				<meshStandardMaterial color="#00ddff" roughness={0.1} metalness={0.5} />
			</mesh>
			<mesh ref={knotRef} position={[3, 1.5, 2]} castShadow receiveShadow>
				<torusKnotGeometry args={[0.8, 0.3, 128, 16]} />
				<meshStandardMaterial color="#ff0088" roughness={0.1} metalness={0.8} />
			</mesh>
			<gridHelper args={[50, 50, "#444444", "#222222"]} />
		</>
	);
}

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas shadows camera={{ position: [10, 10, 10], fov: 50 }}>
					<OrbitControls makeDefault minPolarAngle={0} maxPolarAngle={Math.PI / 2.1} />
					<Suspense fallback={null}>
						<Scene />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
