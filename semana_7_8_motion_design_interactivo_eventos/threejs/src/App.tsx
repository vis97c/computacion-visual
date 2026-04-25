import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls } from "@react-three/drei";

import "./App.css";

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas camera={{ position: [8, 8, 8], fov: 45 }}>
					<Suspense fallback={null}>
						<OrbitControls makeDefault />
						<Environment preset="night" />
						<gridHelper args={[20, 20, 0x333333, 0x111111]} position={[0, -2, 0]} />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
