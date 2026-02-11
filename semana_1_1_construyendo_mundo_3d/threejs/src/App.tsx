import type { BufferGeometry } from "three";
import { Canvas, useLoader } from "@react-three/fiber";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { Environment, OrbitControls, Edges } from "@react-three/drei";
import { Suspense, useState } from "react";

import "./App.css";

/**
 * Carga un modelo 3D
 * @see https://r3f.docs.pmnd.rs/tutorials/loading-models
 */

function getGeometry() {
	let vertices = 0;
	let faces = 0;
	let geometry: BufferGeometry | undefined = undefined;

	// Esto nos da un grupo con los objetos del modelo
	const obj = useLoader(OBJLoader, "/cube.obj");

	obj.traverse((child) => {
		if (child.isObject3D && "geometry" in child) {
			// Extraer la geometria del modelo
			geometry = child.geometry as BufferGeometry;

			// Conteo de vertices
			vertices = geometry?.attributes.position.count || 0;

			// Conteo de caras
			if (geometry?.index !== null) {
				faces = (geometry?.index.count || 0) / 3;
			} else {
				faces = geometry.attributes.position.count / 3 || 0;
			}
		}
	});

	// Renderizamos un mesh con la geometria extraida
	// Usamos edges para dibujar las aristas
	return { geometry, vertices, faces };
}

function App() {
	const [showEdges, setShowEdges] = useState(false);
	const { geometry, vertices, faces } = getGeometry();

	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas>
					<Suspense fallback={null}>
						<mesh geometry={geometry}>
							<meshBasicMaterial color="red" />
							{showEdges && (
								<Edges linewidth={4} scale={1} threshold={15} color="yellow" />
							)}
						</mesh>
						<OrbitControls />
						<Environment preset="apartment" background />
					</Suspense>
				</Canvas>
			</section>
			<ul id="canvas-options">
				<li>
					<button onClick={() => setShowEdges(!showEdges)}>Alternar aristas</button>
				</li>
				<li>Vertices: {vertices}</li>
				<li>Caras: {faces}</li>
			</ul>
		</main>
	);
}

export default App;
