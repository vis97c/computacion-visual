import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls } from "@react-three/drei";

import "./App.css";

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas>
					<Suspense fallback={null}>
						<OrbitControls makeDefault />
						<Environment preset="apartment" />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
