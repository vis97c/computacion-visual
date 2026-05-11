import { Suspense, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls, PivotControls, Line, Html } from "@react-three/drei";
import { Vector3, Group } from "three";
import { useControls } from "leva";
import "./App.css";

const segmentLengths = [2, 1.5, 1]; // Lengths of each arm segment

function Arm({ targetPos }: { targetPos: Vector3 }) {
	const group0 = useRef<Group>(null!);
	const group1 = useRef<Group>(null!);
	const group2 = useRef<Group>(null!);
	const endEffector = useRef<Group>(null!);

	const [ikData, setIkData] = useState({ distance: 0, iterations: 0 });

	const joints = [group0, group1, group2];

	// IK Settings, enableIK, maxIterations, tolerance
	const { enableIK, maxIterations, tolerance } = useControls("IK Settings", {
		enableIK: true,
		maxIterations: { value: 10, min: 1, max: 50, step: 1 },
		tolerance: { value: 0.05, min: 0.001, max: 0.5, step: 0.001 },
	});

	// For visualization lines
	const [linePoints, setLinePoints] = useState<Vector3[]>([new Vector3(), new Vector3()]);

	useFrame(() => {
		if (!enableIK) return;

		let iterationsCompleted = 0;
		let distance = 0;

		const endPos = new Vector3();
		const jointPos = new Vector3();
		const targetVec = new Vector3();
		const endVec = new Vector3();
		const axis = new Vector3();

		// Check initial distance to avoid unnecessarily running IK if already close enough
		endEffector.current.getWorldPosition(endPos);
		distance = endPos.distanceTo(targetPos);

		if (distance >= tolerance) {
			for (let iter = 0; iter < maxIterations; iter++) {
				iterationsCompleted++;

				endEffector.current.getWorldPosition(endPos);
				distance = endPos.distanceTo(targetPos);
				if (distance < tolerance) break;

				for (let i = joints.length - 1; i >= 0; i--) {
					const joint = joints[i].current;

					endEffector.current.getWorldPosition(endPos);
					joint.getWorldPosition(jointPos);

					// Vector from joint to target
					targetVec.subVectors(targetPos, jointPos).normalize();
					// Vector from joint to end effector
					endVec.subVectors(endPos, jointPos).normalize();

					// Calculate angle and axis to rotate
					const dot = endVec.dot(targetVec);
					const angle = Math.acos(Math.max(-1, Math.min(1, dot)));

					// Damped / clamped angle to avoid excessive overshooting
					// Before this it was going wild
					const clampedAngle = Math.min(angle, 0.1);

					if (clampedAngle > 0.0001) {
						axis.crossVectors(endVec, targetVec);
						// Safety check to avoid division by zero when normalizing
						if (axis.lengthSq() > 0.000001) {
							axis.normalize();
							// Apply rotation in world space
							joint.rotateOnWorldAxis(axis, clampedAngle);
						}
					}
				}
			}
		}

		// Update debug text
		setIkData({ distance, iterations: iterationsCompleted });

		// Update line points
		const basePos = new Vector3();
		joints[0].current.getWorldPosition(basePos);
		setLinePoints([basePos.clone(), targetPos.clone()]);
	});

	return (
		<>
			<group position={[0, -2, 0]} ref={group0}>
				{/* Segment 0 */}
				<mesh position={[segmentLengths[0] / 2, 0, 0]}>
					<boxGeometry args={[segmentLengths[0], 0.4, 0.4]} />
					<meshStandardMaterial color="#ff5555" />
				</mesh>
				<group position={[segmentLengths[0], 0, 0]} ref={group1}>
					{/* Segment 1 */}
					<mesh position={[segmentLengths[1] / 2, 0, 0]}>
						<boxGeometry args={[segmentLengths[1], 0.3, 0.3]} />
						<meshStandardMaterial color="#55ff55" />
					</mesh>
					<group position={[segmentLengths[1], 0, 0]} ref={group2}>
						{/* Segment 2 */}
						<mesh position={[segmentLengths[2] / 2, 0, 0]}>
							<boxGeometry args={[segmentLengths[2], 0.2, 0.2]} />
							<meshStandardMaterial color="#5555ff" />
						</mesh>
						<group position={[segmentLengths[2], 0, 0]} ref={endEffector}>
							{/* End effector */}
							<mesh>
								<boxGeometry args={[0.1, 0.4, 0.4]} />
								<meshStandardMaterial color="yellow" />
							</mesh>
						</group>
					</group>
				</group>
			</group>

			{/* Line from base to target */}
			<Line points={linePoints} color="white" dashed />

			{/* Distance from end effector to target */}
			<Html position={[0, 3, 0]}>
				<div
					style={{
						background: "rgba(0,0,0,0.7)",
						color: "white",
						padding: "10px",
						borderRadius: "5px",
						width: "220px",
					}}
				>
					<h4>IK Status</h4>
					<p>Distance: {ikData.distance.toFixed(4)}</p>
					<p>Iterations: {ikData.iterations}</p>
				</div>
			</Html>
		</>
	);
}

function Scene() {
	const defaultTargetPos = new Vector3(2, 2, 0);
	const targetGroup = useRef<Group>(null!);
	const [targetPos, setTargetPos] = useState(defaultTargetPos);

	useFrame(() => {
		if (targetGroup.current) {
			const pos = new Vector3();
			targetGroup.current.getWorldPosition(pos);
			setTargetPos(pos);
		}
	});

	return (
		<>
			{/* Grid and floor */}
			<gridHelper args={[20, 20]} />
			<mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.1, 0]}>
				<planeGeometry args={[20, 20]} />
				<meshStandardMaterial color="#333" />
			</mesh>

			{/* Draggable Target */}
			<PivotControls scale={1} activeAxes={[true, true, true]} depthTest={false}>
				<group position={defaultTargetPos} ref={targetGroup}>
					<mesh>
						<sphereGeometry args={[0.3, 16, 16]} />
						<meshStandardMaterial color="hotpink" />
					</mesh>
				</group>
			</PivotControls>

			<Arm targetPos={targetPos} />
		</>
	);
}

function App() {
	return (
		<main id="container">
			<section id="canvas-container" style={{ width: "100w", height: "100vh" }}>
				<Canvas camera={{ position: [0, 2, 8], fov: 50 }}>
					<Suspense fallback={null}>
						<OrbitControls makeDefault />
						<Environment preset="city" />
						<directionalLight position={[5, 5, 5]} intensity={1} />
						<ambientLight intensity={0.5} />
						<Scene />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
