import { Canvas, useLoader } from "@react-three/fiber";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { Environment, OrbitControls } from "@react-three/drei";
import { Suspense, useMemo, useState } from "react";

import "./App.css";
import { Mesh, type MeshBasicMaterial, MeshStandardMaterial } from "three";

function App() {
	// Esto nos da un grupo con los objetos del modelo
	const gatoGeometry = useLoader(STLLoader, "/dist/gato.stl");
	const chimueloObject = useLoader(OBJLoader, "/dist/chimuelo.obj");
	const saddamObject = useLoader(GLTFLoader, "/dist/saddam.gltf");
	const [selectedModel, setSelectedModel] = useState<"gato" | "chimuelo" | "saddam">("gato");
	const model = useMemo(() => {
		switch (selectedModel) {
			case "gato":
				gatoGeometry.rotateY(10);

				// Clone object with new material
				const gato = new Mesh(gatoGeometry, new MeshStandardMaterial({ color: "red" }));

				gato.translateX(50);
				gato.translateY(-10);

				return gato;
			case "chimuelo":
				return chimueloObject;
			case "saddam":
				const scene = saddamObject.scene.clone();

				const child = scene.children[0].children[0];

				child.rotateY(10);

				// Change color of the mesh
				if ("material" in child && child.material) {
					(child.material as MeshBasicMaterial).color.set("red");
				}

				// Center the scene
				scene.translateY(-10);
				scene.translateX(20);
				scene.translateZ(20);

				return scene;
		}
	}, [selectedModel]);

	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas>
					<Suspense fallback={null}>
						<primitive object={model} />
						<OrbitControls />
						<Environment preset="apartment" background />
					</Suspense>
				</Canvas>
			</section>
			<ul id="canvas-options">
				<li>
					<select
						onChange={(e) =>
							setSelectedModel(e.target.value as "gato" | "chimuelo" | "saddam")
						}
					>
						<option value="gato">Gato</option>
						<option value="chimuelo">Chimuelo</option>
						<option value="saddam">Saddam</option>
					</select>
				</li>
			</ul>
		</main>
	);
}

export default App;
