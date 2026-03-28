import { Suspense, useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls } from "@react-three/drei";
import { useControls, folder } from "leva";
import * as THREE from "three";
import "./App.css";

// Grid of cubes with animated deformation
function AnimatedGrid() {
	const meshRef = useRef<THREE.InstancedMesh>(null);
	const gridSize = 8;
	const spacing = 1.2;

	const { waveAmplitude, waveSpeed, cubeScale } = useControls("Cuadrícula", {
		waveAmplitude: { value: 0.5, min: 0, max: 2, step: 0.1 },
		waveSpeed: { value: 2, min: 0.5, max: 5, step: 0.1 },
		cubeScale: { value: 0.4, min: 0.1, max: 1, step: 0.05 },
	});

	const count = gridSize * gridSize;
	const dummy = useMemo(() => new THREE.Object3D(), []);

	useFrame(({ clock }) => {
		if (!meshRef.current) return;
		const time = clock.getElapsedTime();

		let i = 0;
		for (let x = 0; x < gridSize; x++) {
			for (let z = 0; z < gridSize; z++) {
				const posX = (x - gridSize / 2) * spacing;
				const posZ = (z - gridSize / 2) * spacing;
				// Wave animation on Y axis
				const posY =
					Math.sin(posX * 0.5 + time * waveSpeed) *
					Math.cos(posZ * 0.5 + time * waveSpeed) *
					waveAmplitude;

				dummy.position.set(posX, posY, posZ);
				dummy.rotation.set(time * 0.5, time * 0.3, 0);
				dummy.scale.setScalar(cubeScale);
				dummy.updateMatrix();
				meshRef.current.setMatrixAt(i, dummy.matrix);
				i++;
			}
		}
		meshRef.current.instanceMatrix.needsUpdate = true;
	});

	return (
		<instancedMesh ref={meshRef} args={[undefined, undefined, count]} position={[-8, 0, 0]}>
			<boxGeometry args={[1, 1, 1]} />
			<meshStandardMaterial color="#4fc3f7" metalness={0.3} roughness={0.4} />
		</instancedMesh>
	);
}

// Spiral of spheres
function Spiral() {
	const groupRef = useRef<THREE.Group>(null);

	const { spiralTurns, spheresPerTurn, spiralHeight, sphereRadius } = useControls("Espiral", {
		spiralTurns: { value: 3, min: 1, max: 6, step: 1 },
		spheresPerTurn: { value: 12, min: 6, max: 24, step: 1 },
		spiralHeight: { value: 8, min: 2, max: 15, step: 0.5 },
		sphereRadius: { value: 0.25, min: 0.1, max: 0.5, step: 0.05 },
	});

	const spheres = useMemo(() => {
		const items = [];
		const totalSpheres = spiralTurns * spheresPerTurn;
		const radius = 2;

		for (let i = 0; i < totalSpheres; i++) {
			const angle = (i / spheresPerTurn) * Math.PI * 2;
			const y = (i / totalSpheres) * spiralHeight - spiralHeight / 2;
			const x = Math.cos(angle) * radius;
			const z = Math.sin(angle) * radius;
			const hue = i / totalSpheres;

			items.push({ position: [x, y, z] as [number, number, number], hue });
		}
		return items;
	}, [spiralTurns, spheresPerTurn, spiralHeight]);

	useFrame(({ clock }) => {
		if (groupRef.current) {
			groupRef.current.rotation.y = clock.getElapsedTime() * 0.3;
		}
	});

	return (
		<group ref={groupRef} position={[0, 0, 0]}>
			{spheres.map((sphere, i) => (
				<mesh key={i} position={sphere.position}>
					<sphereGeometry args={[sphereRadius, 16, 16]} />
					<meshStandardMaterial
						color={new THREE.Color().setHSL(sphere.hue, 0.8, 0.5)}
						metalness={0.5}
						roughness={0.3}
					/>
				</mesh>
			))}
		</group>
	);
}

// Deformable geometry with vertex manipulation
function DeformableSphere() {
	const meshRef = useRef<THREE.Mesh>(null);
	const originalPositions = useRef<Float32Array | null>(null);

	const { deformIntensity, noiseScale, noiseSpeed } = useControls("Deformación", {
		deformIntensity: { value: 0.3, min: 0, max: 1, step: 0.05 },
		noiseScale: { value: 2, min: 0.5, max: 5, step: 0.1 },
		noiseSpeed: { value: 1.5, min: 0.5, max: 4, step: 0.1 },
	});

	useFrame(({ clock }) => {
		if (!meshRef.current) return;

		const geometry = meshRef.current.geometry as THREE.BufferGeometry;
		const positions = geometry.attributes.position.array as Float32Array;

		// Store original positions on first frame
		if (!originalPositions.current) {
			originalPositions.current = new Float32Array(positions);
		}

		const time = clock.getElapsedTime();

		// Modify vertices dynamically
		for (let i = 0; i < positions.length; i += 3) {
			const ox = originalPositions.current[i];
			const oy = originalPositions.current[i + 1];
			const oz = originalPositions.current[i + 2];

			// Simple noise-like deformation
			const noise =
				Math.sin(ox * noiseScale + time * noiseSpeed) *
				Math.cos(oy * noiseScale + time * noiseSpeed) *
				Math.sin(oz * noiseScale + time * noiseSpeed * 0.7);

			const length = Math.sqrt(ox * ox + oy * oy + oz * oz);
			const nx = ox / length;
			const ny = oy / length;
			const nz = oz / length;

			positions[i] = ox + nx * noise * deformIntensity;
			positions[i + 1] = oy + ny * noise * deformIntensity;
			positions[i + 2] = oz + nz * noise * deformIntensity;
		}

		geometry.attributes.position.needsUpdate = true;
		geometry.computeVertexNormals();
	});

	return (
		<mesh ref={meshRef} position={[8, 0, 0]}>
			<sphereGeometry args={[2, 32, 32]} />
			<meshStandardMaterial color="#ff7043" metalness={0.4} roughness={0.3} />
		</mesh>
	);
}

// Recursive fractal tree
interface BranchProps {
	position: [number, number, number];
	rotation: [number, number, number];
	length: number;
	depth: number;
	maxDepth: number;
	branchAngle: number;
}

function Branch({ position, rotation, length, depth, maxDepth, branchAngle }: BranchProps) {
	const groupRef = useRef<THREE.Group>(null);

	useFrame(({ clock }) => {
		if (groupRef.current && depth === 0) {
			groupRef.current.rotation.y = Math.sin(clock.getElapsedTime() * 0.3) * 0.1;
		}
	});

	if (depth > maxDepth) return null;

	const thickness = 0.08 * Math.pow(0.7, depth);
	const nextLength = length * 0.7;
	const hue = depth / maxDepth;

	return (
		<group ref={groupRef} position={position} rotation={rotation}>
			{/* Branch cylinder */}
			<mesh position={[0, length / 2, 0]}>
				<cylinderGeometry args={[thickness * 0.7, thickness, length, 8]} />
				<meshStandardMaterial
					color={new THREE.Color().setHSL(0.1 + hue * 0.2, 0.6, 0.35)}
					roughness={0.8}
				/>
			</mesh>

			{/* Child branches */}
			{depth < maxDepth && (
				<>
					<Branch
						position={[0, length, 0]}
						rotation={[branchAngle, 0, 0]}
						length={nextLength}
						depth={depth + 1}
						maxDepth={maxDepth}
						branchAngle={branchAngle}
					/>
					<Branch
						position={[0, length, 0]}
						rotation={[-branchAngle, 0, 0]}
						length={nextLength}
						depth={depth + 1}
						maxDepth={maxDepth}
						branchAngle={branchAngle}
					/>
					<Branch
						position={[0, length, 0]}
						rotation={[0, 0, branchAngle]}
						length={nextLength}
						depth={depth + 1}
						maxDepth={maxDepth}
						branchAngle={branchAngle}
					/>
					<Branch
						position={[0, length, 0]}
						rotation={[0, 0, -branchAngle]}
						length={nextLength}
						depth={depth + 1}
						maxDepth={maxDepth}
						branchAngle={branchAngle}
					/>
				</>
			)}

			{/* Leaves at the end */}
			{depth === maxDepth && (
				<mesh position={[0, length, 0]}>
					<sphereGeometry args={[0.15, 8, 8]} />
					<meshStandardMaterial color="#66bb6a" roughness={0.6} />
				</mesh>
			)}
		</group>
	);
}

function FractalTree() {
	const { treeDepth, branchAngle, trunkLength } = useControls("Árbol Fractal", {
		treeDepth: { value: 4, min: 1, max: 6, step: 1 },
		branchAngle: { value: 0.5, min: 0.2, max: 1, step: 0.05 },
		trunkLength: { value: 1.5, min: 0.5, max: 3, step: 0.1 },
	});

	return (
		<group position={[0, -5, -10]}>
			<Branch
				position={[0, 0, 0]}
				rotation={[0, 0, 0]}
				length={trunkLength}
				depth={0}
				maxDepth={treeDepth}
				branchAngle={branchAngle}
			/>
		</group>
	);
}

function Scene() {
	return (
		<>
			<AnimatedGrid />
			<Spiral />
			<DeformableSphere />
			<FractalTree />

			{/* Floor */}
			<mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -5, 0]} receiveShadow>
				<planeGeometry args={[50, 50]} />
				<meshStandardMaterial color="#1a1a2e" metalness={0.2} roughness={0.8} />
			</mesh>

			{/* Lights */}
			<ambientLight intensity={0.4} />
			<directionalLight position={[10, 15, 10]} intensity={1} castShadow />
			<pointLight position={[-10, 5, -10]} intensity={0.5} color="#ff9800" />
		</>
	);
}

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas camera={{ position: [0, 5, 20], fov: 60 }}>
					<Suspense fallback={null}>
						<OrbitControls makeDefault />
						<Environment preset="city" />
						<Scene />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
