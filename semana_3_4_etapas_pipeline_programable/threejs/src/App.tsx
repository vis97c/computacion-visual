import { Suspense, useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, OrbitControls } from "@react-three/drei";
import { Bloom, EffectComposer, Noise, Vignette } from "@react-three/postprocessing";
import * as THREE from "three";
import { useControls } from "leva";
import "./App.css";

const vertexShader = `
varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vViewPosition;
uniform float uTime;
uniform float uWaveAmplitude;
uniform float uWaveFrequency;

void main() {
    vUv = uv;
    vNormal = normalize(normalMatrix * normal);
    
    vec3 pos = position;
    // Deformación con onda
    pos.z += sin(pos.x * uWaveFrequency + uTime) * uWaveAmplitude;
    pos.y += cos(pos.z * uWaveFrequency * 0.5 + uTime) * uWaveAmplitude * 0.5;

    vec4 modelViewPosition = modelViewMatrix * vec4(pos, 1.0);
    vViewPosition = -modelViewPosition.xyz;
    gl_Position = projectionMatrix * modelViewPosition;
}
`;

const fragmentShader = `
varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vViewPosition;
uniform float uTime;
uniform vec2 uResolution;
uniform vec3 uColor;
uniform float uFresnelPower;
uniform float uRimPower;
uniform float uNoiseIntensity;

float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

void main() {
    vec3 normal = normalize(vNormal);
    vec3 viewDir = normalize(vViewPosition);

    // Fresnel Effect
    float fresnel = pow(1.0 - dot(normal, viewDir), uFresnelPower);
    
    // Rim Lighting
    float rim = pow(1.0 - max(dot(normal, viewDir), 0.0), uRimPower);

    // Procedural Noise
    float noise = random(vUv + uTime * 0.1) * uNoiseIntensity;

    // Base Color using UV and dot product lighting
    vec3 baseColor = uColor;
    baseColor += vec3(vUv, 0.5) * 0.2;
    
    // Simple Diffuse Lighting
    float diffuse = dot(normal, vec3(0.5, 0.5, 1.0)) * 0.5 + 0.5;
    
    vec3 finalColor = baseColor * diffuse;
    
    // Add Fresnel and Rim
    finalColor += vec3(0.5, 0.8, 1.0) * fresnel;
    finalColor += vec3(1.0) * rim;
    
    // Apply Noise
    finalColor += noise;

    gl_FragColor = vec4(finalColor, 1.0);
}
`;

function ShaderMesh() {
	const meshRef = useRef<THREE.Mesh>(null);

	const { amplitude, frequency, fresnelPower, rimPower, noiseIntensity, color } = useControls({
		amplitude: { value: 0.1, min: 0, max: 0.5 },
		frequency: { value: 5.0, min: 0, max: 20.0 },
		fresnelPower: { value: 2.0, min: 0.1, max: 10.0 },
		rimPower: { value: 4.0, min: 0.1, max: 10.0 },
		noiseIntensity: { value: 0.05, min: 0, max: 0.2 },
		color: "#4a90e2",
	});

	const uniforms = useMemo(
		() => ({
			uTime: { value: 0 },
			uResolution: { value: new THREE.Vector2() },
			uWaveAmplitude: { value: amplitude },
			uWaveFrequency: { value: frequency },
			uFresnelPower: { value: fresnelPower },
			uRimPower: { value: rimPower },
			uNoiseIntensity: { value: noiseIntensity },
			uColor: { value: new THREE.Color(color) },
		}),
		[]
	);

	useFrame((state) => {
		if (meshRef.current) {
			const material = meshRef.current.material as THREE.ShaderMaterial;
			material.uniforms.uTime.value = state.clock.getElapsedTime();
			material.uniforms.uResolution.value.set(state.size.width, state.size.height);
			material.uniforms.uWaveAmplitude.value = amplitude;
			material.uniforms.uWaveFrequency.value = frequency;
			material.uniforms.uFresnelPower.value = fresnelPower;
			material.uniforms.uRimPower.value = rimPower;
			material.uniforms.uNoiseIntensity.value = noiseIntensity;
			material.uniforms.uColor.value.set(color);
		}
	});

	return (
		<mesh ref={meshRef}>
			<sphereGeometry args={[1, 64, 64]} />
			<shaderMaterial
				vertexShader={vertexShader}
				fragmentShader={fragmentShader}
				uniforms={uniforms}
			/>
		</mesh>
	);
}

function App() {
	return (
		<main id="container">
			<section id="canvas-container">
				<Canvas camera={{ position: [0, 0, 4], fov: 45 }}>
					<Suspense fallback={null}>
						<ShaderMesh />
						<OrbitControls makeDefault />
						<Environment preset="city" />

						<EffectComposer>
							<Bloom intensity={1.5} luminanceThreshold={0.9} />
							<Noise opacity={0.02} />
							<Vignette eskil={false} offset={0.1} darkness={1.1} />
						</EffectComposer>
					</Suspense>
				</Canvas>
			</section>
		</main>
	);
}

export default App;
