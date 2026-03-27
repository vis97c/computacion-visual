/* ────────────────────────────────────────────────────────────
   App.tsx  –  Modelos de Color y Percepción Visual
   –  Escena 3D con múltiples objetos y materiales
   –  Post-processing para simulación de visión / color models
   –  Controles Leva para interacción en tiempo real
   ──────────────────────────────────────────────────────────── */

import { Suspense, useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame, extend, useThree } from "@react-three/fiber";
import {
	Environment,
	OrbitControls,
	Float,
	Text,
	RoundedBox,
} from "@react-three/drei";
import * as THREE from "three";
import { useControls } from "leva";
import "./App.css";

/* ═══════════════════════════════════════════════════════════
   Custom ShaderPass for color vision post-processing
   ═══════════════════════════════════════════════════════════ */

const colorVisionFragmentShader = /* glsl */ `
uniform sampler2D tDiffuse;
uniform int uColorModel;
uniform int uChannel;
uniform int uCvdType;
uniform float uCvdStrength;
uniform float uTemperature;
uniform float uSaturation;
uniform float uBrightness;
uniform float uInvert;
uniform float uGrayscale;
varying vec2 vUv;

vec3 srgbToLinear(vec3 c) {
    return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c));
}
vec3 linearToSrgb(vec3 c) {
    return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c));
}

vec3 rgbToHsv(vec3 c) {
    float cMax = max(c.r, max(c.g, c.b));
    float cMin = min(c.r, min(c.g, c.b));
    float delta = cMax - cMin;
    float h = 0.0;
    if (delta > 0.00001) {
        if (cMax == c.r) h = mod((c.g - c.b) / delta, 6.0);
        else if (cMax == c.g) h = (c.b - c.r) / delta + 2.0;
        else h = (c.r - c.g) / delta + 4.0;
        h /= 6.0;
        if (h < 0.0) h += 1.0;
    }
    float s = (cMax > 0.0) ? delta / cMax : 0.0;
    return vec3(h, s, cMax);
}

vec3 hsvToRgb(vec3 c) {
    float h = c.x * 6.0;
    float s = c.y;
    float v = c.z;
    float f = h - floor(h);
    float p = v * (1.0 - s);
    float q = v * (1.0 - s * f);
    float t = v * (1.0 - s * (1.0 - f));
    int hi = int(mod(floor(h), 6.0));
    if (hi == 0) return vec3(v, t, p);
    if (hi == 1) return vec3(q, v, p);
    if (hi == 2) return vec3(p, v, t);
    if (hi == 3) return vec3(p, q, v);
    if (hi == 4) return vec3(t, p, v);
    return vec3(v, p, q);
}

vec3 rgbToLab(vec3 rgb) {
    vec3 lin = srgbToLinear(rgb);
    float x = lin.r * 0.4124564 + lin.g * 0.3575761 + lin.b * 0.1804375;
    float y = lin.r * 0.2126729 + lin.g * 0.7151522 + lin.b * 0.0721750;
    float z = lin.r * 0.0193339 + lin.g * 0.1191920 + lin.b * 0.9503041;
    x /= 0.95047; z /= 1.08883;
    float eps = 0.008856;
    float kap = 903.3;
    x = (x > eps) ? pow(x, 1.0/3.0) : (kap * x + 16.0) / 116.0;
    y = (y > eps) ? pow(y, 1.0/3.0) : (kap * y + 16.0) / 116.0;
    z = (z > eps) ? pow(z, 1.0/3.0) : (kap * z + 16.0) / 116.0;
    return vec3((116.0 * y - 16.0) / 100.0, (500.0 * (x - y) + 128.0) / 256.0, (200.0 * (y - z) + 128.0) / 256.0);
}

mat3 getProtanopia() {
    return mat3(
        0.152286,  1.052583, -0.204868,
        0.114503,  0.786281,  0.099216,
       -0.003882, -0.048116,  1.051998
    );
}
mat3 getDeuteranopia() {
    return mat3(
        0.367322,  0.860646, -0.227968,
        0.280085,  0.672501,  0.047413,
       -0.011820,  0.042940,  0.968881
    );
}
mat3 getTritanopia() {
    return mat3(
        1.255528, -0.076749, -0.178779,
        0.078411,  0.930809, -0.009220,
        0.004733, -0.691367,  1.686634
    );
}

void main() {
    vec4 texel = texture2D(tDiffuse, vUv);
    vec3 col = texel.rgb;

    // 1. CVD simulation
    if (uCvdType > 0) {
        vec3 lin = srgbToLinear(col);
        mat3 cvd;
        if (uCvdType == 1) cvd = getProtanopia();
        else if (uCvdType == 2) cvd = getDeuteranopia();
        else cvd = getTritanopia();
        lin = mix(lin, cvd * lin, uCvdStrength);
        col = linearToSrgb(clamp(lin, 0.0, 1.0));
    }

    // 2. Temperature
    col.r += uTemperature * 0.1;
    col.b -= uTemperature * 0.1;
    col = clamp(col, 0.0, 1.0);

    // 3. Saturation
    vec3 hsv = rgbToHsv(col);
    hsv.y *= uSaturation;
    hsv.y = clamp(hsv.y, 0.0, 1.0);
    col = hsvToRgb(hsv);

    // 4. Brightness
    col *= uBrightness;
    col = clamp(col, 0.0, 1.0);

    // 5. Grayscale
    if (uGrayscale > 0.5) {
        float lum = dot(col, vec3(0.2126, 0.7152, 0.0722));
        col = vec3(lum);
    }

    // 6. Invert
    if (uInvert > 0.5) col = 1.0 - col;

    // 7. Color model vis
    if (uColorModel == 1) {
        vec3 h = rgbToHsv(col);
        if (uChannel == 0) col = vec3(h.x);
        else if (uChannel == 1) col = vec3(h.y);
        else if (uChannel == 2) col = vec3(h.z);
        else col = h;
    } else if (uColorModel == 2) {
        vec3 lab = rgbToLab(col);
        if (uChannel == 0) col = vec3(lab.x);
        else if (uChannel == 1) col = vec3(lab.y);
        else if (uChannel == 2) col = vec3(lab.z);
        else col = lab;
    } else {
        if (uChannel == 0) col = vec3(col.r, 0.0, 0.0);
        else if (uChannel == 1) col = vec3(0.0, col.g, 0.0);
        else if (uChannel == 2) col = vec3(0.0, 0.0, col.b);
    }

    gl_FragColor = vec4(col, texel.a);
}
`;

const colorVisionVertexShader = /* glsl */ `
varying vec2 vUv;
void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

/**
 * FullscreenQuad post-processing component using a manual render-to-texture approach.
 * This avoids all compatibility issues with the postprocessing library.
 */
function ColorVisionPostProcess(props: {
	colorModel: number;
	channel: number;
	cvdType: number;
	cvdStrength: number;
	temperature: number;
	saturation: number;
	brightness: number;
	invert: number;
	grayscale: number;
}) {
	const { gl, scene, camera, size } = useThree();
	const renderTarget = useMemo(
		() =>
			new THREE.WebGLRenderTarget(size.width, size.height, {
				minFilter: THREE.LinearFilter,
				magFilter: THREE.LinearFilter,
				format: THREE.RGBAFormat,
			}),
		[]
	);

	const quadScene = useMemo(() => new THREE.Scene(), []);
	const quadCamera = useMemo(
		() => new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1),
		[]
	);

	const material = useMemo(
		() =>
			new THREE.ShaderMaterial({
				vertexShader: colorVisionVertexShader,
				fragmentShader: colorVisionFragmentShader,
				uniforms: {
					tDiffuse: { value: null },
					uColorModel: { value: 0 },
					uChannel: { value: -1 },
					uCvdType: { value: 0 },
					uCvdStrength: { value: 1.0 },
					uTemperature: { value: 0.0 },
					uSaturation: { value: 1.0 },
					uBrightness: { value: 1.0 },
					uInvert: { value: 0.0 },
					uGrayscale: { value: 0.0 },
				},
			}),
		[]
	);

	const quad = useMemo(() => {
		const geo = new THREE.PlaneGeometry(2, 2);
		const mesh = new THREE.Mesh(geo, material);
		return mesh;
	}, [material]);

	useEffect(() => {
		quadScene.add(quad);
		return () => {
			quadScene.remove(quad);
		};
	}, [quadScene, quad]);

	// Resize render target
	useEffect(() => {
		renderTarget.setSize(size.width, size.height);
	}, [size, renderTarget]);

	useFrame(() => {
		// Update uniforms
		material.uniforms.uColorModel.value = props.colorModel;
		material.uniforms.uChannel.value = props.channel;
		material.uniforms.uCvdType.value = props.cvdType;
		material.uniforms.uCvdStrength.value = props.cvdStrength;
		material.uniforms.uTemperature.value = props.temperature;
		material.uniforms.uSaturation.value = props.saturation;
		material.uniforms.uBrightness.value = props.brightness;
		material.uniforms.uInvert.value = props.invert;
		material.uniforms.uGrayscale.value = props.grayscale;

		// Render scene to texture
		gl.setRenderTarget(renderTarget);
		gl.render(scene, camera);

		// Render quad with post-processing to screen
		material.uniforms.tDiffuse.value = renderTarget.texture;
		gl.setRenderTarget(null);
		gl.render(quadScene, quadCamera);
	}, 1);

	return null;
}

/* ═══════════════════════════════════════════════════════════
   Animated geometry components
   ═══════════════════════════════════════════════════════════ */

function ColorCube({
	position,
	color,
	size = 0.9,
	speed = 0.3,
}: {
	position: [number, number, number];
	color: string;
	size?: number;
	speed?: number;
}) {
	const ref = useRef<THREE.Mesh>(null);
	useFrame((_, delta) => {
		if (ref.current) {
			ref.current.rotation.x += delta * speed;
			ref.current.rotation.y += delta * speed * 0.7;
		}
	});
	return (
		<Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.4}>
			<RoundedBox
				ref={ref}
				args={[size, size, size]}
				radius={0.08}
				smoothness={4}
				position={position}
				castShadow
				receiveShadow
			>
				<meshPhysicalMaterial
					color={color}
					roughness={0.15}
					metalness={0.1}
					clearcoat={0.8}
					clearcoatRoughness={0.2}
				/>
			</RoundedBox>
		</Float>
	);
}

function ColorSphere({
	position,
	color,
	radius = 0.55,
}: {
	position: [number, number, number];
	color: string;
	radius?: number;
}) {
	const ref = useRef<THREE.Mesh>(null);
	useFrame((state) => {
		if (ref.current) {
			ref.current.position.y =
				position[1] + Math.sin(state.clock.elapsedTime * 1.2) * 0.15;
		}
	});
	return (
		<mesh ref={ref} position={position} castShadow receiveShadow>
			<sphereGeometry args={[radius, 64, 64]} />
			<meshPhysicalMaterial
				color={color}
				roughness={0.05}
				metalness={0.4}
				clearcoat={1}
				clearcoatRoughness={0.05}
				envMapIntensity={1.5}
			/>
		</mesh>
	);
}

function GlassTorus({
	position,
	color,
}: {
	position: [number, number, number];
	color: string;
}) {
	const ref = useRef<THREE.Mesh>(null);
	useFrame((_, delta) => {
		if (ref.current) {
			ref.current.rotation.x += delta * 0.4;
			ref.current.rotation.z += delta * 0.2;
		}
	});
	return (
		<Float speed={2} rotationIntensity={0.5} floatIntensity={0.6}>
			<mesh ref={ref} position={position} castShadow>
				<torusGeometry args={[0.5, 0.2, 32, 64]} />
				<meshPhysicalMaterial
					color={color}
					roughness={0.05}
					metalness={0.8}
					clearcoat={1.0}
					clearcoatRoughness={0.0}
					transmission={0.6}
					thickness={1.5}
					ior={1.5}
				/>
			</mesh>
		</Float>
	);
}

function GlowIcosahedron({
	position,
	color,
}: {
	position: [number, number, number];
	color: string;
}) {
	const ref = useRef<THREE.Mesh>(null);
	useFrame((_, delta) => {
		if (ref.current) {
			ref.current.rotation.y += delta * 0.5;
			ref.current.rotation.z += delta * 0.3;
		}
	});
	return (
		<Float speed={1} rotationIntensity={0.6} floatIntensity={0.5}>
			<mesh ref={ref} position={position} castShadow>
				<icosahedronGeometry args={[0.45, 1]} />
				<meshPhysicalMaterial
					color={color}
					emissive={color}
					emissiveIntensity={0.6}
					roughness={0.2}
					metalness={0.6}
					clearcoat={0.5}
				/>
			</mesh>
		</Float>
	);
}

function Ground() {
	return (
		<mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.6, 0]} receiveShadow>
			<planeGeometry args={[30, 30]} />
			<meshStandardMaterial color="#0e0e14" roughness={0.9} metalness={0.1} />
		</mesh>
	);
}

function Label({
	text,
	position,
}: {
	text: string;
	position: [number, number, number];
}) {
	return (
		<Text
			position={position}
			fontSize={0.18}
			color="#8888a0"
			anchorX="center"
			anchorY="middle"
		>
			{text}
		</Text>
	);
}

/* ═══════════════════════════════════════════════════════════
   Scene (only 3D content, no controls)
   ═══════════════════════════════════════════════════════════ */
function SceneContent({
	cubeColor,
	sphereColor,
	torusColor,
	icoColor,
}: {
	cubeColor: string;
	sphereColor: string;
	torusColor: string;
	icoColor: string;
}) {
	return (
		<>
			{/* Lights */}
			<ambientLight intensity={0.35} />
			<directionalLight
				position={[5, 8, 5]}
				intensity={1.8}
				castShadow
				shadow-mapSize-width={2048}
				shadow-mapSize-height={2048}
			/>
			<pointLight position={[-3, 3, -3]} intensity={0.6} color="#6c5ce7" />
			<pointLight position={[3, 2, 3]} intensity={0.4} color="#fd79a8" />

			{/* Front row */}
			<ColorCube position={[-2, 0, 0]} color={cubeColor} />
			<ColorSphere position={[-0.5, 0, 0.5]} color={sphereColor} />
			<GlassTorus position={[1, 0, 0]} color={torusColor} />
			<GlowIcosahedron position={[2.5, 0, -0.3]} color={icoColor} />

			{/* Labels */}
			<Label text="Cubo" position={[-2, -1.2, 0]} />
			<Label text="Esfera" position={[-0.5, -1.2, 0.5]} />
			<Label text="Toro" position={[1, -1.2, 0]} />
			<Label text="Icosaedro" position={[2.5, -1.2, -0.3]} />

			{/* Back row */}
			<ColorSphere position={[-1.8, 0, -2]} color="#e056a0" radius={0.4} />
			<ColorCube position={[0, 0, -2.2]} color="#00cec9" size={0.7} />
			<GlowIcosahedron position={[1.8, 0, -2]} color="#a29bfe" />

			<Ground />
			<Environment preset="night" />
			<OrbitControls
				makeDefault
				enableDamping
				dampingFactor={0.05}
				minPolarAngle={0.3}
				maxPolarAngle={Math.PI / 2 - 0.05}
			/>
		</>
	);
}

/* ═══════════════════════════════════════════════════════════
   App  –  Canvas + Controls
   ═══════════════════════════════════════════════════════════ */
function App() {
	// ── Object colours ─────────────────────────────────────
	const { cubeColor, sphereColor, torusColor, icoColor } = useControls(
		"🎨 Colores de Objetos",
		{
			cubeColor: { label: "Cubo", value: "#e74c3c" },
			sphereColor: { label: "Esfera", value: "#2ecc71" },
			torusColor: { label: "Toro", value: "#3498db" },
			icoColor: { label: "Icosaedro", value: "#f39c12" },
		}
	);

	// ── Colour model ───────────────────────────────────────
	const { colorModelSel, channelSel } = useControls("🔬 Modelo de Color", {
		colorModelSel: {
			label: "Espacio",
			value: 0,
			options: { RGB: 0, HSV: 1, "CIE Lab": 2 },
		},
		channelSel: {
			label: "Canal",
			value: -1,
			options: { Todos: -1, "Canal 0": 0, "Canal 1": 1, "Canal 2": 2 },
		},
	});

	// ── CVD simulation ─────────────────────────────────────
	const { cvdTypeSel, cvdStrength } = useControls("👁️ Simulación de Visión", {
		cvdTypeSel: {
			label: "Tipo",
			value: 0,
			options: {
				Normal: 0,
				"Protanopía": 1,
				"Deuteranopía": 2,
				"Tritanopía": 3,
			},
		},
		cvdStrength: {
			label: "Intensidad",
			value: 1.0,
			min: 0,
			max: 1,
			step: 0.01,
		},
	});

	// ── Creative filters ───────────────────────────────────
	const { temperature, saturation, brightness, invert, grayscale } =
		useControls("✨ Filtros Creativos", {
			temperature: {
				label: "Temperatura",
				value: 0,
				min: -1,
				max: 1,
				step: 0.01,
			},
			saturation: {
				label: "Saturación",
				value: 1.0,
				min: 0,
				max: 3,
				step: 0.01,
			},
			brightness: {
				label: "Brillo",
				value: 1.0,
				min: 0.1,
				max: 2,
				step: 0.01,
			},
			invert: { label: "Invertir", value: false },
			grayscale: { label: "Escala de grises", value: false },
		});

	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas
					camera={{ position: [0, 2, 6], fov: 50 }}
					shadows
					dpr={[1, 2]}
					gl={{
						antialias: true,
						toneMapping: THREE.ACESFilmicToneMapping,
						toneMappingExposure: 1.2,
					}}
				>
					<Suspense fallback={null}>
						<SceneContent
							cubeColor={cubeColor}
							sphereColor={sphereColor}
							torusColor={torusColor}
							icoColor={icoColor}
						/>
						<ColorVisionPostProcess
							colorModel={colorModelSel}
							channel={channelSel}
							cvdType={cvdTypeSel}
							cvdStrength={cvdStrength}
							temperature={temperature}
							saturation={saturation}
							brightness={brightness}
							invert={invert ? 1 : 0}
							grayscale={grayscale ? 1 : 0}
						/>
					</Suspense>
				</Canvas>
			</section>

			{/* Info overlay */}
			<div id="info-overlay">
				<h1>Modelos de Color y Percepción</h1>
				<p>
					Usa el panel de controles para explorar espacios de color, simular
					daltonismo y aplicar filtros creativos en tiempo real.
				</p>
			</div>
		</main>
	);
}

export default App;
