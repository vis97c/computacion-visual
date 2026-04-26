import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls } from "@react-three/drei";
import "./App.css";

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas camera={{ position: [0, 2, 5], fov: 45 }}>
					<Suspense fallback={null}>
						<OrbitControls
							makeDefault
							minDistance={2}
							maxDistance={10}
							target={[0, 1, 0]}
						/>
						<Environment preset="city" />
						<gridHelper args={[20, 20, 0x333333, 0x111111]} position={[0, 0, 0]} />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
