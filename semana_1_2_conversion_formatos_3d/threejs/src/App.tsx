import { Canvas } from "@react-three/fiber";

import "./App.css";

function App() {
	return (
		<div id="canvas-container">
			<Canvas>
				<mesh />
			</Canvas>
		</div>
	);
}

export default App;
