import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import "./App.css";

type ConnectionStatus = "connecting" | "open" | "closed" | "error";

interface WsPayload {
	x: number;
	y: number;
	color: string;
}

const WS_URL = "ws://localhost:8765";
const POSITION_LIMIT = 5;
const FALLBACK_COLOR = "#f59f00";
const COLOR_MAP: Record<string, string> = {
	red: "#ff4d4f",
	green: "#2fcd73",
	blue: "#4c6fff",
};

function clamp(value: number, min: number, max: number): number {
	return Math.min(max, Math.max(min, value));
}

function parsePayload(rawMessage: string): WsPayload | null {
	let parsed: unknown;
	try {
		parsed = JSON.parse(rawMessage);
	} catch {
		return null;
	}

	if (
		typeof parsed !== "object" ||
		parsed === null ||
		!("x" in parsed) ||
		!("y" in parsed) ||
		!("color" in parsed)
	) {
		return null;
	}

	const x = Number((parsed as { x: unknown }).x);
	const y = Number((parsed as { y: unknown }).y);
	const color = String((parsed as { color: unknown }).color).toLowerCase();

	if (!Number.isFinite(x) || !Number.isFinite(y)) {
		return null;
	}

	return { x, y, color };
}

function LiveObject({
	target,
	color,
}: {
	target: THREE.Vector3;
	color: string;
}) {
	const meshRef = useRef<THREE.Mesh>(null);
	const materialRef = useRef<THREE.MeshStandardMaterial>(null);
	const targetRef = useRef(target.clone());

	useEffect(() => {
		targetRef.current.copy(target);
	}, [target]);

	useEffect(() => {
		if (materialRef.current) {
			materialRef.current.color.set(color);
		}
	}, [color]);

	useFrame((_, delta) => {
		if (!meshRef.current) return;
		const alpha = Math.min(1, delta * 4.5);
		meshRef.current.position.lerp(targetRef.current, alpha);
	});

	return (
		<mesh ref={meshRef} position={[0, 0, 0]}>
			<sphereGeometry args={[0.6, 32, 32]} />
			<meshStandardMaterial ref={materialRef} color={FALLBACK_COLOR} />
		</mesh>
	);
}

function App() {
	const [status, setStatus] = useState<ConnectionStatus>("connecting");
	const [lastData, setLastData] = useState<WsPayload | null>(null);
	const [targetPosition, setTargetPosition] = useState(
		() => new THREE.Vector3(0, 0, 0)
	);
	const [objectColor, setObjectColor] = useState(FALLBACK_COLOR);
	const wsRef = useRef<WebSocket | null>(null);

	useEffect(() => {
		const socket = new WebSocket(WS_URL);
		wsRef.current = socket;
		setStatus("connecting");

		socket.onopen = () => {
			setStatus("open");
		};

		socket.onmessage = (event) => {
			const payload = parsePayload(event.data);
			if (!payload) return;

			const x = clamp(payload.x, -POSITION_LIMIT, POSITION_LIMIT);
			const y = clamp(payload.y, -POSITION_LIMIT, POSITION_LIMIT);
			setLastData(payload);
			setTargetPosition(new THREE.Vector3(x, y, 0));
			setObjectColor(COLOR_MAP[payload.color] ?? FALLBACK_COLOR);
		};

		socket.onerror = () => {
			setStatus("error");
		};

		socket.onclose = () => {
			setStatus("closed");
		};

		return () => {
			if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
				wsRef.current.close();
			}
		};
	}, []);

	const statusLabel = useMemo(() => {
		switch (status) {
			case "connecting":
				return "Conectando...";
			case "open":
				return "Conectado";
			case "closed":
				return "Desconectado";
			default:
				return "Error de conexion";
		}
	}, [status]);

	return (
		<main id="app">
			<section id="hud">
				<p>
					<strong>WebSocket:</strong> {statusLabel}
				</p>
				<p>
					<strong>x:</strong> {lastData ? lastData.x.toFixed(2) : "0.00"} |{" "}
					<strong>y:</strong> {lastData ? lastData.y.toFixed(2) : "0.00"}
				</p>
				<p>
					<strong>color:</strong> {lastData ? lastData.color : "sin datos"}
				</p>
				<p id="hint">Servidor esperado en ws://localhost:8765</p>
			</section>

			<Canvas camera={{ position: [0, 0, 11], fov: 50 }}>
				<ambientLight intensity={0.45} />
				<directionalLight position={[2, 4, 3]} intensity={1.1} />
				<gridHelper args={[12, 12, "#2d3258", "#1f2238"]} />
				<axesHelper args={[3.5]} />
				<LiveObject target={targetPosition} color={objectColor} />
				<OrbitControls makeDefault />
			</Canvas>
		</main>
	);
}

export default App;
