import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { shaderMaterial } from "@react-three/drei";
import { extend } from "@react-three/fiber";
import { useControls } from "leva";
import * as THREE from "three";

// Definición del shader
const CustomShaderMaterial = shaderMaterial(
	{
		uTime: 0,
		uColorTop: new THREE.Color("#00ffea"), // Cyan
		uColorBottom: new THREE.Color("#ff0077"), // Fucsia
	},
	// Vertex Shader
	`
  varying vec2 vUv;
  varying vec3 vPosition;
  varying vec3 vNormal;
  varying vec3 vViewDir;
  uniform float uTime;

  void main() {
    vUv = uv;
    vNormal = normalize(normalMatrix * normal);
    vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
    vViewDir = normalize(-vPosition); // Vector towards the camera
    
    // Wave deformation
    vec3 pos = position;
    float wave = sin(pos.y * 2.0 + uTime) * 0.1;
    pos += normal * wave; // Push along normal for better effect
    
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
  `,
	// Fragment Shader
	`
  varying vec2 vUv;
  varying vec3 vNormal;
  varying vec3 vViewDir;
  uniform float uTime;
  uniform vec3 uColorTop;
  uniform vec3 uColorBottom;

  void main() {
    // 1. Vertical Gradient
    vec3 gradient = mix(uColorBottom, uColorTop, vUv.y);
    
    // 2. Animated brightness
    float pulse = sin(uTime * 1.5) * 0.1 + 0.9;
    
    // 3. Toon Shading (Light & Shadow Quantization)
    vec3 lightDir = normalize(vec3(5.0, 5.0, 5.0)); // Top-right-front
    float dotNL = dot(vNormal, lightDir);
    
    // Smooth toon steps
    float toon = smoothstep(0.0, 0.05, dotNL) * 0.4 + 
                 smoothstep(0.4, 0.45, dotNL) * 0.4 + 
                 0.2; // Ambient base
    
    // 4. Fresnel / Rim Light (Edge Glow)
    float fresnel = pow(1.0 - dot(vViewDir, vNormal), 3.0);
    vec3 rimColor = vec3(1.0, 1.0, 1.0) * fresnel * 0.5;

    // 5. Simple Wireframe Grid using UVs
    vec2 gridUv = fract(vUv * 20.0);
    float line = smoothstep(0.0, 0.02, min(gridUv.x, gridUv.y)) * 
                 smoothstep(1.0, 0.98, max(gridUv.x, gridUv.y));
    float gridMask = 1.0 - line;

    // Combine everything
    vec3 color = (gradient * toon * pulse) + rimColor;
    color = mix(color, vec3(1.0, 1.0, 1.0), gridMask * 0.2); // Add subtle grid

    gl_FragColor = vec4(color, 1.0);
  }
  `
);

// Extiende R3F para que <customShaderMaterial /> exista
extend({ CustomShaderMaterial });

// Declara tipos para elementos personalizados
declare module "@react-three/fiber" {
	interface ThreeElements {
		customShaderMaterial: any;
	}
}

export const VisualObject = () => {
	const shaderRef = useRef<any>(null);

	// Toggle control with Leva
	const { showShader } = useControls({
		showShader: { value: true, label: "Activar Shader" },
	});

	useFrame((state) => {
		if (shaderRef.current) {
			shaderRef.current.uTime = state.clock.elapsedTime;
		}
	});

	return (
		<mesh>
			<torusKnotGeometry args={[1, 0.35, 128, 32]} />
			{showShader ? (
				<customShaderMaterial ref={shaderRef} transparent />
			) : (
				<meshStandardMaterial color="#00ffea" roughness={0.1} metalness={0.8} />
			)}
		</mesh>
	);
};
