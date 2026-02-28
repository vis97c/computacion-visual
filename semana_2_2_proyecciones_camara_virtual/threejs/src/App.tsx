import { Canvas } from "@react-three/fiber";
import { useState } from "react";
import Scene from "./scene.tsx";

export default function App() {
	const [isPerspective, setIsPerspective] = useState(true);

	return (
		<>
			<button
				style={{ position: "absolute", zIndex: 10 }}
				onClick={() => setIsPerspective(!isPerspective)}
			>
				Cambiar Cámara
			</button>

			<div className="perspective">
				Cámara: {isPerspective ? "Perspective" : "Orthographic"}
				<br />
				{isPerspective
					? "fov: 60 | near: 0.1 | far: 100"
					: "left/right/top/bottom dinámicos"}
			</div>

			<Canvas style={{ width: "100%", height: "100%" }}>
				<Scene isPerspective={isPerspective} />
			</Canvas>
		</>
	);
}
