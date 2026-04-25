import { Suspense, useState, useEffect, useCallback } from "react";
import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls, ContactShadows } from "@react-three/drei";
import { Girl } from "./Girl";
import "./App.css";

function App() {
	const [currentAnim, setCurrentAnim] = useState("idle");
	const [isThrillerCycle, setIsThrillerCycle] = useState(false);
	const [audio] = useState(() => new Audio("/thriller.mp3"));

	// Sync audio with thriller cycle
	useEffect(() => {
		if (isThrillerCycle) {
			audio.currentTime = 0;
			audio.play().catch((err) => console.warn("Audio playback failed:", err));
		} else {
			audio.pause();
			audio.currentTime = 0;
		}

		return () => {
			audio.pause();
		};
	}, [isThrillerCycle, audio]);

	// Start a specific animation and stop the thriller cycle if active
	const playAnim = useCallback((name: string) => {
		setIsThrillerCycle(false);
		setCurrentAnim(name);
	}, []);

	// Start the thriller sequence
	const startThrillerCycle = () => {
		setIsThrillerCycle(true);
		setCurrentAnim("thriller1");
	};

	// Handle sequence transitions
	const handleAnimationEnd = (name: string) => {
		if (isThrillerCycle) {
			if (name === "thriller1") setCurrentAnim("thriller2");
			else if (name === "thriller2") setCurrentAnim("thriller3");
			else if (name === "thriller3") setCurrentAnim("thriller4");
			else if (name === "thriller4") {
				setIsThrillerCycle(false);
				setCurrentAnim("idle");
			}
		} else if (name === "wave" || name === "jump") {
			// Return to idle after one-shot animations
			setCurrentAnim("idle");
		}
	};

	// Keyboard events
	useEffect(() => {
		const handleKeyDown = (e: KeyboardEvent) => {
			if (e.code === "Space") {
				playAnim("jump");
			} else if (e.code === "KeyW" || e.code === "ArrowUp") {
				playAnim("run");
			}
		};

		const handleKeyUp = (e: KeyboardEvent) => {
			if (e.code === "KeyW" || e.code === "ArrowUp") {
				if (currentAnim === "run") {
					setCurrentAnim("idle");
				}
			}
		};

		window.addEventListener("keydown", handleKeyDown);
		window.addEventListener("keyup", handleKeyUp);
		return () => {
			window.removeEventListener("keydown", handleKeyDown);
			window.removeEventListener("keyup", handleKeyUp);
		};
	}, [playAnim, currentAnim]);

	return (
		<main id="container">
			<div className="overlay">
				<h1>Motion Design Interactivo</h1>
				<p>Click: Saludo | Hover: Idle | Espacio: Salto | W: Correr</p>
			</div>

			<section id="canvas-container">
				<Canvas camera={{ position: [0, 2, 5], fov: 45 }}>
					<Suspense fallback={null}>
						<OrbitControls makeDefault minDistance={2} maxDistance={10} target={[0, 1, 0]} />
						<Environment preset="city" />
						<ambientLight intensity={0.5} />
						<spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} />
						
						<Girl 
							animation={currentAnim} 
							onAnimationEnd={handleAnimationEnd}
							position={[0, 0, 0]}
							scale={1.5}
							onClick={() => playAnim("wave")}
							onPointerOver={() => {
								if (currentAnim !== "wave" && currentAnim !== "jump" && !isThrillerCycle) {
									setCurrentAnim("idle");
								}
							}}
						/>

						<ContactShadows 
							position={[0, 0, 0]} 
							opacity={0.4} 
							scale={10} 
							blur={2.5} 
							far={4} 
						/>
						<gridHelper args={[20, 20, 0x333333, 0x111111]} position={[0, 0, 0]} />
					</Suspense>
				</Canvas>
			</section>

			<div className="matrix-panel">
				<span className="label">CONTROLES DE ANIMACIÓN</span>
				<div className="matrix-grid">
					<button className="matrix-cell" onClick={() => playAnim("idle")}>Idle</button>
					<button className="matrix-cell" onClick={() => playAnim("wave")}>Saludo</button>
					<button className="matrix-cell" onClick={() => playAnim("run")}>Correr</button>
					<button className="matrix-cell" onClick={() => playAnim("jump")}>Salto</button>
				</div>
				<button 
					className="matrix-cell thriller-btn" 
					style={{ width: '100%', marginTop: '0.5rem', background: 'linear-gradient(45deg, #ff0055, #8800ff)', color: 'white', fontWeight: 'bold' }}
					onClick={startThrillerCycle}
				>
					INICIAR CICLO THRILLER
				</button>
				<div style={{ marginTop: '0.5rem', fontSize: '0.7rem', color: '#888' }}>
					Estado: <span style={{ color: '#fff' }}>{isThrillerCycle ? "Ciclo Thriller" : currentAnim}</span>
				</div>
			</div>
		</main>
	);
}

export default App;
