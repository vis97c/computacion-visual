import { useRef, useCallback } from "react";
import { useFrame } from "@react-three/fiber";
import { useControls, folder } from "leva";
import * as THREE from "three";
import EndEffectorTrail from "./EndEffectorTrail";

// ── Constantes del brazo ──────────────────────────
const BASE_HEIGHT = 0.6;
const BASE_RADIUS = 0.5;
const LINK_1_LENGTH = 2.0;
const LINK_2_LENGTH = 1.6;
const LINK_WIDTH = 0.28;
const JOINT_RADIUS = 0.2;

// Colores
const COLOR_BASE = "#1a2a40";
const COLOR_BASE_EMISSIVE = "#0d1520";
const COLOR_JOINT = "#2a4060";
const COLOR_JOINT_EMISSIVE = "#102040";
const COLOR_LINK1 = "#1e3d5c";
const COLOR_LINK2 = "#1a4a6c";
const COLOR_END_EFFECTOR = "#00e5ff";

export interface LevaControls {
	hombroY: number;
	hombroZ: number;
	codoZ: number;
	speed: number;
}

/**
 * RobotArm — brazo robótico de 3 grados de libertad con cinemática directa.
 *
 * Jerarquía de grupos (cada hijo rota respecto a su padre):
 *   Base (rotación Y)
 *     └── Link 1 / Hombro (rotación Z)
 *           └── Link 2 / Codo (rotación Z)
 *                 └── Link 3 / Efector Final
 *
 * Soporta dos modos:
 *   - Automático: rotaciones senoidales progresivas animadas con useFrame
 *   - Manual: sliders de Leva para ajustar cada ángulo
 */
export default function RobotArm({
	onAnglesChange,
	onEndPosChange,
	autoAnimate,
}: {
	onAnglesChange: (angles: {
		hombroY: number;
		hombroZ: number;
		codo: number;
	}) => void;
	onEndPosChange: (pos: { x: number; y: number; z: number }) => void;
	autoAnimate: boolean;
}) {
	// ── Refs de cada articulación ──────────────────
	const hombroGroupRef = useRef<THREE.Group>(null);
	const codoGroupRef = useRef<THREE.Group>(null);
	const endEffectorRef = useRef<THREE.Object3D>(null);

	// Para calcular posición del efector final
	const worldPos = useRef(new THREE.Vector3());

	// ── Controles de Leva ────────────────────────
	const controls = useControls({
		"Modo": folder({
			speed: { value: 1.0, min: 0.1, max: 3.0, step: 0.1, label: "Velocidad" },
		}),
		"Articulaciones": folder({
			hombroY: {
				value: 0,
				min: -Math.PI,
				max: Math.PI,
				step: 0.01,
				label: "θ₁ Hombro (Y)",
			},
			hombroZ: {
				value: 0,
				min: -Math.PI / 2,
				max: Math.PI / 2,
				step: 0.01,
				label: "θ₂ Hombro (Z)",
			},
			codoZ: {
				value: 0,
				min: -Math.PI / 2,
				max: Math.PI / 2,
				step: 0.01,
				label: "θ₃ Codo (Z)",
			},
		}),
	}) as LevaControls;

	// ── Función auxiliar para actualizar el HUD ───
	const updateHud = useCallback(
		(hombroY: number, hombroZ: number, codo: number) => {
			onAnglesChange({ hombroY, hombroZ, codo });
			if (endEffectorRef.current) {
				endEffectorRef.current.getWorldPosition(worldPos.current);
				onEndPosChange({
					x: worldPos.current.x,
					y: worldPos.current.y,
					z: worldPos.current.z,
				});
			}
		},
		[onAnglesChange, onEndPosChange]
	);

	// ── Animación en cada frame ────────────────────
	useFrame(({ clock }) => {
		if (!hombroGroupRef.current || !codoGroupRef.current)
			return;

		if (autoAnimate) {
			const t = clock.elapsedTime * controls.speed;

			// Rotaciones senoidales progresivas
			const homY = Math.sin(t * 0.4) * Math.PI * 0.6;
			const homZ = Math.cos(t * 0.3) * 0.5;
			const codo = Math.sin(t * 0.7 + 1.0) * 0.6 + Math.cos(t * 0.3) * 0.2;

			hombroGroupRef.current.rotation.order = "YZX";
			hombroGroupRef.current.rotation.y = homY;
			hombroGroupRef.current.rotation.z = homZ;
			codoGroupRef.current.rotation.z = codo;

			updateHud(homY, homZ, codo);
		} else {
			// Modo manual — interpolación suave hacia los valores de Leva
			const lerpFactor = 0.08;
			hombroGroupRef.current.rotation.order = "YZX";
			hombroGroupRef.current.rotation.y = THREE.MathUtils.lerp(
				hombroGroupRef.current.rotation.y,
				controls.hombroY,
				lerpFactor
			);
			hombroGroupRef.current.rotation.z = THREE.MathUtils.lerp(
				hombroGroupRef.current.rotation.z,
				controls.hombroZ,
				lerpFactor
			);
			codoGroupRef.current.rotation.z = THREE.MathUtils.lerp(
				codoGroupRef.current.rotation.z,
				controls.codoZ,
				lerpFactor
			);

			updateHud(
				hombroGroupRef.current.rotation.y,
				hombroGroupRef.current.rotation.z,
				codoGroupRef.current.rotation.z
			);
		}
	});

	return (
		<group>
			{/* ── Base ─────────────────────────────── */}
			<mesh position={[0, BASE_HEIGHT / 2, 0]} castShadow>
				<cylinderGeometry
					args={[BASE_RADIUS, BASE_RADIUS * 1.2, BASE_HEIGHT, 32]}
				/>
				<meshStandardMaterial
					color={COLOR_BASE}
					emissive={COLOR_BASE_EMISSIVE}
					emissiveIntensity={0.3}
					metalness={0.8}
					roughness={0.3}
				/>
			</mesh>

			{/* ── Grupo Hombro (rotación Y) ──────────── */}
			<group ref={hombroGroupRef} position={[0, BASE_HEIGHT, 0]}>
				{/* Articulación hombro (Esfera) */}
				<mesh castShadow>
					<sphereGeometry args={[JOINT_RADIUS, 24, 24]} />
					<meshStandardMaterial
						color={COLOR_JOINT}
						emissive={COLOR_JOINT_EMISSIVE}
						emissiveIntensity={0.5}
						metalness={0.9}
						roughness={0.2}
					/>
				</mesh>

				{/* Eslabón 1 (Brazo) - Este pertenece al Hombro, NO al Codo */}
				<mesh
					position={[0, LINK_1_LENGTH / 2, 0]}
					castShadow
				>
					<boxGeometry
						args={[LINK_WIDTH, LINK_1_LENGTH, LINK_WIDTH]}
					/>
					<meshStandardMaterial
						color={COLOR_LINK1}
						emissive={"#0a1e30"}
						emissiveIntensity={0.4}
						metalness={0.7}
						roughness={0.35}
					/>
				</mesh>

				{/* Articulación codo (Esfera visual en la base del eslabón 2) */}
				<mesh position={[0, LINK_1_LENGTH, 0]} castShadow>
					<sphereGeometry args={[JOINT_RADIUS * 0.85, 24, 24]} />
					<meshStandardMaterial
						color={COLOR_JOINT}
						emissive={COLOR_JOINT_EMISSIVE}
						emissiveIntensity={0.5}
						metalness={0.9}
						roughness={0.2}
					/>
				</mesh>

				{/* ── Grupo Codo (rotación Z) ───── */}
				{/* Se ubica al final del Eslabón 1 */}
				<group ref={codoGroupRef} position={[0, LINK_1_LENGTH, 0]}>
					{/* Eslabón 2 (Antebrazo) */}
					<mesh
						position={[0, LINK_2_LENGTH / 2, 0]}
						castShadow
					>
						<boxGeometry
							args={[
								LINK_WIDTH * 0.85,
								LINK_2_LENGTH,
								LINK_WIDTH * 0.85,
							]}
						/>
						<meshStandardMaterial
							color={COLOR_LINK2}
							emissive={"#0a2030"}
							emissiveIntensity={0.4}
							metalness={0.7}
							roughness={0.35}
						/>
					</mesh>

					{/* ── Efector Final (punta) ── */}
					<group position={[0, LINK_2_LENGTH, 0]}>
							<mesh
								ref={endEffectorRef as React.RefObject<THREE.Mesh>}
							>
								<sphereGeometry args={[0.12, 16, 16]} />
								<meshStandardMaterial
									color={COLOR_END_EFFECTOR}
									emissive={COLOR_END_EFFECTOR}
									emissiveIntensity={1.5}
									metalness={0.3}
									roughness={0.1}
								/>
							</mesh>

							{/* Halo del efector */}
							<mesh>
								<sphereGeometry args={[0.22, 12, 12]} />
								<meshBasicMaterial
									color={COLOR_END_EFFECTOR}
									transparent
									opacity={0.12}
								/>
							</mesh>
						</group>
					</group>
				</group>

			{/* ── Estela del efector final ────────── */}
			<EndEffectorTrail endEffectorRef={endEffectorRef} />
		</group>
	);
}
