import { Canvas, useLoader } from "@react-three/fiber";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { Environment, OrbitControls } from "@react-three/drei";
import { Suspense } from "react";

import "./App.css";

/**
 * Carga un modelo 3D
 * @see https://r3f.docs.pmnd.rs/tutorials/loading-models
 */

function Model() {
	const obj = useLoader(OBJLoader, "/cube.obj");

	return <primitive object={obj} />;
}

function App() {
	return (
		<div id="canvas-container">
			<Canvas>
				<Suspense fallback={null}>
					<Model />
					<OrbitControls />
					<Environment preset="sunset" background />
				</Suspense>
			</Canvas>
		</div>
	);
}

export default App;
