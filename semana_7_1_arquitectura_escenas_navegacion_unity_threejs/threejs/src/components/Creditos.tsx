import { Suspense, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls, Text } from "@react-three/drei";
import { Link } from "react-router-dom";
import * as THREE from "three";

function ScrollingText() {
	const textRef = useRef<THREE.Group>(null!);

	useFrame((_state, delta) => {
		if (textRef.current) {
			textRef.current.position.y += delta * 0.8;

			// Reinicia la posición si sube demasiado
			if (textRef.current.position.y > 15) {
				textRef.current.position.y = -8;
			}
		}
	});

	const lorem = `Desarrollado por: \nBlessd\n\nArte y Diseño\nEstudio Increíble\n\nAgradecimientos\nComunidad de Three.js\n\n Mi mama\n\n Mi papa\n\n Mi tia Piedad\n\n\n\n\n\nHace mucho tiempo en una galaxia muy lejana...`;

	return (
		<group ref={textRef} position={[0, -8, 0]}>
			<Text
				fontSize={0.4}
				color="white"
				anchorX="center"
				anchorY="middle"
				textAlign="center"
				maxWidth={4}
			>
				{lorem}
			</Text>
		</group>
	);
}

export default function Creditos() {
	return (
		<main id="container" className="bg-black">
			<div className="ui-overlay">
				<Link to="/" className="btn-secondary">
					Volver al Menú
				</Link>
			</div>
			<section id="canvas-container">
				<Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
					<Suspense fallback={null}>
						<OrbitControls
							makeDefault
							minDistance={2}
							maxDistance={10}
							target={[0, 0, 0]}
							enablePan={false}
							enableZoom={false}
						/>
						<Environment preset="city" />
						<ScrollingText />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}
