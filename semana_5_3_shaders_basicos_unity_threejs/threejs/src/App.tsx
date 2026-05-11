import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls, ContactShadows } from "@react-three/drei";
import { VisualObject } from "./VisualObject";
import "./App.css";

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
					<color attach="background" args={["#111111"]} />
					<Suspense fallback={null}>
						<VisualObject />
						<ContactShadows position={[0, -2, 0]} opacity={0.4} scale={10} blur={2.5} far={4} />
						<OrbitControls makeDefault autoRotate autoRotateSpeed={0.5} />
						<Environment preset="night" />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
