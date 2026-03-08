import { Suspense, useMemo } from "react";
import { Canvas, extend } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, shaderMaterial } from "@react-three/drei";
import { useControls } from "leva";

import "./App.css";

// 1. Custom Depth Shader Material
const CustomDepthMaterial = shaderMaterial(
	{},
	// Vertex shader
	`
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
  `,
	// Fragment shader
	`
  void main() {
    // gl_FragCoord.z represents the depth value [0.0 - 1.0]
    gl_FragColor = vec4(vec3(gl_FragCoord.z), 1.0);
  }
  `
);

// Register the custom shader material so it can be used as <customDepthMaterial />
extend({ CustomDepthMaterial });

function App() {
	const { near, far, depthTest, materialType } = useControls({
		near: { value: 0.1, min: 0.1, max: 10, step: 0.1 },
		far: { value: 20, min: 5, max: 100, step: 1 },
		depthTest: true,
		materialType: {
			value: "Standard",
			options: ["Standard", "ThreeDepth", "CustomDepth"],
		},
	});

	const objects = useMemo(() => {
		return [
			{ position: [0, 0, 0] as [number, number, number], color: "red" },
			{ position: [1.5, 0, -5] as [number, number, number], color: "green" },
			{ position: [-1.5, 0, -10] as [number, number, number], color: "blue" },
			{ position: [0, 1.5, -15] as [number, number, number], color: "yellow" },
		];
	}, []);

	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas>
					<Suspense fallback={null}>
						<PerspectiveCamera makeDefault position={[0, 2, 5]} near={near} far={far} />
						<OrbitControls makeDefault />

						<ambientLight intensity={0.5} />
						<pointLight position={[10, 10, 10]} />

						{objects.map((obj, i) => (
							<mesh key={i} position={obj.position}>
								<boxGeometry args={[1, 1, 1]} />
								{materialType === "Standard" && (
									<meshStandardMaterial color={obj.color} depthTest={depthTest} />
								)}
								{materialType === "ThreeDepth" && (
									<meshDepthMaterial depthTest={depthTest} />
								)}
								{materialType === "CustomDepth" && (
									// @ts-ignore
									<customDepthMaterial depthTest={depthTest} />
								)}
							</mesh>
						))}

						{/* Grid to help visualize depth */}
						<gridHelper args={[20, 20]} />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
