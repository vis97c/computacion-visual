import { Suspense, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls, Line } from "@react-three/drei";
import { useControls } from "leva";
import * as THREE from "three";
import "./App.css";

const startPoint = new THREE.Vector3(-4, 0, 0);
const endPoint = new THREE.Vector3(4, 0, 0);
const controlPoint1 = new THREE.Vector3(-1, 4, 3); // First control point
const controlPoint2 = new THREE.Vector3(2, -3, 2); // Second control point for cubic curve

const startRot = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, 0));
const endRot = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI, Math.PI, Math.PI / 2));

function Scene() {
	const { t, showLinear, showCurve, curveType } = useControls({
		t: { value: 0, min: 0, max: 1, step: 0.01, label: "Time (t)" },
		curveType: { options: ["Quadratic", "Cubic"], label: "Curve Type" },
		showLinear: { value: true, label: "Show Linear" },
		showCurve: { value: true, label: "Show Curve" },
	});

	const linearMeshRef = useRef<THREE.Mesh>(null);
	const curvedMeshRef = useRef<THREE.Mesh>(null);

	const curve = useMemo(() => {
		if (curveType === "Cubic") {
			return new THREE.CubicBezierCurve3(startPoint, controlPoint1, controlPoint2, endPoint);
		}
		return new THREE.QuadraticBezierCurve3(startPoint, controlPoint1, endPoint);
	}, [curveType]);

	// Points to draw the lines guiding the paths
	const curvePoints = useMemo(() => curve.getPoints(50), [curve]);
	const linearPoints = useMemo(() => [startPoint, endPoint], []);

	useFrame(() => {
		if (linearMeshRef.current && showLinear) {
			// Linear Interpolation (Position)
			linearMeshRef.current.position.lerpVectors(startPoint, endPoint, t);
			// Rotation Interpolation with Slerp
			linearMeshRef.current.quaternion.slerpQuaternions(startRot, endRot, t);
		}

		if (curvedMeshRef.current && showCurve) {
			// Bezier Curve Interpolation (Position)
			curve.getPoint(t, curvedMeshRef.current.position);
			// Rotation Interpolation with Slerp
			curvedMeshRef.current.quaternion.slerpQuaternions(startRot, endRot, t);
		}
	});

	return (
		<>
			<OrbitControls makeDefault />
			<Environment preset="city" />

			{/* Start Point (Green) */}
			<mesh position={startPoint}>
				<sphereGeometry args={[0.2, 16, 16]} />
				<meshStandardMaterial color="green" />
			</mesh>

			{/* End Point (Red) */}
			<mesh position={endPoint}>
				<sphereGeometry args={[0.2, 16, 16]} />
				<meshStandardMaterial color="red" />
			</mesh>

			{/* Visual Paths */}
			{showLinear && <Line points={linearPoints} color="blue" lineWidth={2} />}
			{showCurve && <Line points={curvePoints} color="orange" lineWidth={2} />}

			{/* Moving Objects */}
			{showLinear && (
				<mesh ref={linearMeshRef}>
					<boxGeometry args={[0.8, 0.8, 0.8]} />
					<meshStandardMaterial color="blue" />
				</mesh>
			)}

			{showCurve && (
				<mesh ref={curvedMeshRef}>
					<boxGeometry args={[0.8, 0.8, 0.8]} />
					<meshStandardMaterial color="orange" />
				</mesh>
			)}
		</>
	);
}

function App() {
	return (
		<main id="container" style={{ width: "100%", height: "100vh" }}>
			<Canvas camera={{ position: [0, 5, 10] }}>
				<Suspense fallback={null}>
					<Scene />
				</Suspense>
			</Canvas>
		</main>
	);
}

export default App;
