import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

/**
 * GridFloor — suelo estilizado con grilla y reflejo sutil.
 * Usa un plano semi-transparente con una textura de grilla generada
 * proceduralmente para darle un look cyberpunk futurista.
 */
export default function GridFloor() {
	const meshRef = useRef<THREE.Mesh>(null);

	// Generar textura de grilla
	const gridTexture = useMemo(() => {
		const size = 512;
		const canvas = document.createElement("canvas");
		canvas.width = size;
		canvas.height = size;
		const ctx = canvas.getContext("2d")!;

		// Fondo
		ctx.fillStyle = "rgba(0,0,0,0)";
		ctx.fillRect(0, 0, size, size);

		// Líneas de grilla
		const divisions = 20;
		const step = size / divisions;

		ctx.strokeStyle = "rgba(77, 138, 255, 0.15)";
		ctx.lineWidth = 1;

		for (let i = 0; i <= divisions; i++) {
			const pos = i * step;
			ctx.beginPath();
			ctx.moveTo(pos, 0);
			ctx.lineTo(pos, size);
			ctx.stroke();
			ctx.beginPath();
			ctx.moveTo(0, pos);
			ctx.lineTo(size, pos);
			ctx.stroke();
		}

		// Líneas centrales más brillantes
		ctx.strokeStyle = "rgba(0, 229, 255, 0.25)";
		ctx.lineWidth = 2;
		const center = size / 2;
		ctx.beginPath();
		ctx.moveTo(center, 0);
		ctx.lineTo(center, size);
		ctx.stroke();
		ctx.beginPath();
		ctx.moveTo(0, center);
		ctx.lineTo(size, center);
		ctx.stroke();

		const texture = new THREE.CanvasTexture(canvas);
		texture.wrapS = THREE.RepeatWrapping;
		texture.wrapT = THREE.RepeatWrapping;
		texture.repeat.set(3, 3);
		return texture;
	}, []);

	useFrame(({ clock }) => {
		if (!meshRef.current) return;
		const mat = meshRef.current.material as THREE.MeshStandardMaterial;
		mat.opacity = 0.4 + Math.sin(clock.elapsedTime * 0.5) * 0.05;
	});

	return (
		<mesh
			ref={meshRef}
			rotation={[-Math.PI / 2, 0, 0]}
			position={[0, -0.01, 0]}
			receiveShadow
		>
			<planeGeometry args={[30, 30]} />
			<meshStandardMaterial
				map={gridTexture}
				transparent
				opacity={0.4}
				side={THREE.DoubleSide}
				depthWrite={false}
			/>
		</mesh>
	);
}
