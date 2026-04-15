import { useRef, useMemo, useCallback } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

const MAX_TRAIL_POINTS = 600;

/**
 * EndEffectorTrail — visualiza la trayectoria del extremo del brazo robótico.
 * Almacena las posiciones mundiales del efector final y las dibuja como una
 * línea con degradado de color. Solo se actualiza cuando autoAnimate está activo.
 */
export default function EndEffectorTrail({
	endEffectorRef,
}: {
	endEffectorRef: React.RefObject<THREE.Object3D | null>;
}) {
	const positionsRef = useRef<Float32Array>(
		new Float32Array(MAX_TRAIL_POINTS * 3)
	);
	const colorsRef = useRef<Float32Array>(
		new Float32Array(MAX_TRAIL_POINTS * 3)
	);
	const countRef = useRef(0);
	const worldPos = useMemo(() => new THREE.Vector3(), []);
	const frameCounter = useRef(0);

	// Crear el objeto THREE.Line de forma imperativa para evitar conflictos JSX con SVG <line>
	const { lineObj, geometry } = useMemo(() => {
		const geom = new THREE.BufferGeometry();
		const mat = new THREE.LineBasicMaterial({
			vertexColors: true,
			transparent: true,
			opacity: 0.8,
			linewidth: 1,
		});
		const obj = new THREE.Line(geom, mat);
		obj.frustumCulled = false;
		return { lineObj: obj, geometry: geom, material: mat };
	}, []);

	// Color de la estela: Violeta → Cyan
	const getTrailColor = useCallback(
		(t: number): [number, number, number] => {
			// t = 0 → más viejo (violeta), t = 1 → más nuevo (cyan)
			const r = THREE.MathUtils.lerp(0.69, 0.0, t);
			const g = THREE.MathUtils.lerp(0.42, 0.9, t);
			const b = THREE.MathUtils.lerp(1.0, 1.0, t);
			return [r, g, b];
		},
		[]
	);

	useFrame(() => {
		if (!endEffectorRef.current) return;

		frameCounter.current++;
		// Solo registra cada 2 frames para suavizar la estela
		if (frameCounter.current % 2 !== 0) return;

		endEffectorRef.current.getWorldPosition(worldPos);

		const positions = positionsRef.current;
		const colors = colorsRef.current;
		const count = countRef.current;

		if (count < MAX_TRAIL_POINTS) {
			// Agregar nueva posición
			const idx = count * 3;
			positions[idx] = worldPos.x;
			positions[idx + 1] = worldPos.y;
			positions[idx + 2] = worldPos.z;
			countRef.current = count + 1;
		} else {
			// Desplazar y agregar al final
			positions.copyWithin(0, 3);
			const last = (MAX_TRAIL_POINTS - 1) * 3;
			positions[last] = worldPos.x;
			positions[last + 1] = worldPos.y;
			positions[last + 2] = worldPos.z;
		}

		// Actualizar colores con degradado
		const total = countRef.current;
		for (let i = 0; i < total; i++) {
			const t = i / Math.max(total - 1, 1);
			const [r, g, b] = getTrailColor(t);
			colors[i * 3] = r;
			colors[i * 3 + 1] = g;
			colors[i * 3 + 2] = b;
		}

		geometry.setAttribute(
			"position",
			new THREE.BufferAttribute(positions.slice(0, total * 3), 3)
		);
		geometry.setAttribute(
			"color",
			new THREE.BufferAttribute(colors.slice(0, total * 3), 3)
		);
		geometry.computeBoundingSphere();
	});

	return <primitive object={lineObj} />;
}
