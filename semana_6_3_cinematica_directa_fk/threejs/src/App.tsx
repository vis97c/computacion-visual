import { Suspense, useState, useCallback } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import RobotArm from "./components/RobotArm";
import GridFloor from "./components/GridFloor";
import HudOverlay from "./components/HudOverlay";
import "./App.css";

function App() {
	const [angles, setAngles] = useState({ hombroY: 0, hombroZ: 0, codo: 0 });
	const [endPos, setEndPos] = useState({ x: 0, y: 0, z: 0 });
	const [autoAnimate, setAutoAnimate] = useState(true);

	const handleAnglesChange = useCallback(
		(a: { hombroY: number; hombroZ: number; codo: number }) => {
			setAngles(a);
		},
		[]
	);

	const handleEndPosChange = useCallback(
		(p: { x: number; y: number; z: number }) => {
			setEndPos(p);
		},
		[]
	);

	const handleToggleMode = useCallback(() => {
		setAutoAnimate((prev) => !prev);
	}, []);

	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas
					camera={{ position: [6, 5, 6], fov: 50 }}
					gl={{
						antialias: true,
						toneMapping: THREE.ACESFilmicToneMapping,
						toneMappingExposure: 1.3,
					}}
					dpr={[1, 2]}
					shadows
				>
					<Suspense fallback={null}>
						{/* ── Iluminación ─────────────── */}
						<ambientLight intensity={0.2} color="#c0d0ff" />

						<directionalLight
							position={[8, 12, 6]}
							intensity={1.0}
							color="#e8f0ff"
							castShadow
							shadow-mapSize-width={2048}
							shadow-mapSize-height={2048}
							shadow-camera-left={-8}
							shadow-camera-right={8}
							shadow-camera-top={8}
							shadow-camera-bottom={-8}
						/>

						<pointLight
							position={[-4, 6, -3]}
							intensity={0.4}
							color="#4d8aff"
						/>
						<pointLight
							position={[3, 2, 5]}
							intensity={0.3}
							color="#00e5ff"
						/>
						<pointLight
							position={[0, 8, 0]}
							intensity={0.2}
							color="#b06aff"
						/>

						{/* ── Suelo ──────────────────── */}
						<GridFloor />

						{/* ── Brazo robótico ─────────── */}
						<RobotArm
							onAnglesChange={handleAnglesChange}
							onEndPosChange={handleEndPosChange}
							autoAnimate={autoAnimate}
						/>

						{/* ── Controles de órbita ────── */}
						<OrbitControls
							makeDefault
							enableDamping
							dampingFactor={0.06}
							minDistance={4}
							maxDistance={18}
							target={[0, 2.2, 0]}
						/>
					</Suspense>
				</Canvas>
			</section>

			{/* ── HUD Superpuesto ─────────────────── */}
			<HudOverlay
				angles={angles}
				endPos={endPos}
				autoAnimate={autoAnimate}
				onToggleMode={handleToggleMode}
			/>
		</main>
	);
}

export default App;
