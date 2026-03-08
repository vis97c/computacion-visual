import { Suspense, useMemo, useRef, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls, useHelper, Html } from "@react-three/drei";
import * as THREE from "three";
import { useControls } from "leva";
// @ts-ignore
import { VertexNormalsHelper } from "three/examples/jsm/helpers/VertexNormalsHelper.js";

import "./App.css";

/**
 * Shader para colorear según dirección de normal
 */
const NormalShader = {
	uniforms: {
		uTime: { value: 0 },
	},
	vertexShader: `
    varying vec3 vNormal;
    void main() {
      vNormal = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
	fragmentShader: `
    varying vec3 vNormal;
    void main() {
      vec3 color = vNormal * 0.5 + 0.5;
      gl_FragColor = vec4(color, 1.0);
    }
  `,
};

function ProceduralGeometryShowcase() {
	const meshRef = useRef<THREE.Mesh>(null!);
	const materialRef = useRef<THREE.ShaderMaterial>(null!);

	const { shadingMode, amplitude, frequency, helpers } = useControls({
		shadingMode: {
			value: "smooth",
			options: { Manual: "manual", Smooth: "smooth", Flat: "flat" },
		},
		amplitude: { value: 0.4, min: 0, max: 1, step: 0.01 },
		frequency: { value: 2.0, min: 0, max: 10, step: 0.1 },
		helpers: true,
	});

	/**
	 * Geometría base (indexada)
	 */
	const baseGeometry = useMemo(() => {
		const geo = new THREE.BufferGeometry();
		const width = 4;
		const height = 4;
		const segments = 20;
		const vertices: number[] = [];
		const indices: number[] = [];

		for (let i = 0; i <= segments; i++) {
			for (let j = 0; j <= segments; j++) {
				const x = (i / segments - 0.5) * width;
				const y = (j / segments - 0.5) * height;
				vertices.push(x, y, 0);
			}
		}

		for (let i = 0; i < segments; i++) {
			for (let j = 0; j < segments; j++) {
				const a = i * (segments + 1) + j;
				const b = (i + 1) * (segments + 1) + j;
				const c = (i + 1) * (segments + 1) + (j + 1);
				const d = i * (segments + 1) + (j + 1);
				indices.push(a, b, d);
				indices.push(b, c, d);
			}
		}

		geo.setIndex(indices);
		geo.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
		// Inicializar normales para evitar errores de undefined
		geo.setAttribute("normal", new THREE.Float32BufferAttribute(new Float32Array(vertices.length), 3));
		geo.computeVertexNormals();

		return geo;
	}, []);

	// Sincronizar geometría según el modo
	useEffect(() => {
		if (shadingMode === "flat") {
			const nonIndexed = baseGeometry.toNonIndexed();
			nonIndexed.computeVertexNormals();
			meshRef.current.geometry = nonIndexed;
		} else {
			meshRef.current.geometry = baseGeometry;
		}
	}, [shadingMode, baseGeometry]);

	useFrame(({ clock }) => {
		if (!meshRef.current) return;

		const time = clock.getElapsedTime();
		if (materialRef.current) materialRef.current.uniforms.uTime.value = time;

		// IMPORTANTE: Trabajar siempre sobre la geometría ACTIVA del mesh
		const geo = meshRef.current.geometry;
		const posAttribute = geo.getAttribute("position");

		/**
		 * Modificar vértices en tiempo real
		 */
		for (let i = 0; i < posAttribute.count; i++) {
			const x = posAttribute.getX(i);
			const y = posAttribute.getY(i);
			const z = Math.sin(x * frequency + time) * Math.cos(y * frequency + time) * amplitude;
			posAttribute.setZ(i, z);
		}
		posAttribute.needsUpdate = true;

		/**
		 * Recalcular normales según el modo para que el helper y el shader se actualicen
		 */
		if (shadingMode !== "manual") {
			geo.computeVertexNormals();
		}
	});

	// Visualizar normales con VertexNormalsHelper
	// Usamos helpers && meshRef.current?.geometry?.attributes?.normal para seguridad extra
	const canShowHelper = helpers && meshRef.current?.geometry?.attributes?.normal;
	useHelper(canShowHelper ? meshRef : null, VertexNormalsHelper, 0.3, 0x00ff00);

	return (
		<group>
			<mesh ref={meshRef}>
				<shaderMaterial
					ref={materialRef}
					attach="material"
					{...NormalShader}
					side={THREE.DoubleSide}
				/>
			</mesh>

			<Html position={[0, 2.8, 0]} center>
				<div
					style={{
						color: "white",
						textAlign: "center",
						textShadow: "0 2px 4px black",
						pointerEvents: "none",
						width: "500px",
					}}
				>
					<h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>Cálculo de Normales</h1>
					<p style={{ opacity: 0.8 }}>Geometría Procedural + Non-Indexed Shading</p>
				</div>
			</Html>
		</group>
	);
}

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas camera={{ position: [4, 4, 4] }}>
					<Suspense fallback={null}>
						<ProceduralGeometryShowcase />
						<OrbitControls makeDefault />
						<Environment preset="city" />
						<gridHelper args={[10, 10]} rotation={[0, 0, 0]} />
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;

