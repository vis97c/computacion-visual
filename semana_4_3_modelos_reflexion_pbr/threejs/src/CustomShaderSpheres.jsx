import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

// Inline shaders para evitar dependencias de carga de archivos

const lambertVert = `
varying vec3 vNormal;
void main() {
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

const lambertFrag = `
uniform vec3 uLightDir;
uniform vec3 uDiffuseColor;
uniform vec3 uAmbientColor;
varying vec3 vNormal;
void main() {
    vec3 N = normalize(vNormal);
    vec3 L = normalize(uLightDir);
    float NdotL = max(dot(N, L), 0.0);
    vec3 diffuse = uDiffuseColor * NdotL;
    vec3 ambient = uAmbientColor * uDiffuseColor;
    gl_FragColor = vec4(ambient + diffuse, 1.0);
}
`

const phongVert = `
varying vec3 vNormal;
varying vec3 vWorldPosition;
void main() {
    vNormal = normalize(normalMatrix * normal);
    vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

const phongFrag = `
uniform vec3  uLightDir;
uniform vec3  uCameraPos;
uniform vec3  uDiffuseColor;
uniform vec3  uSpecularColor;
uniform vec3  uAmbientColor;
uniform float uShininess;
uniform bool  uUseBlinnPhong;
varying vec3 vNormal;
varying vec3 vWorldPosition;

void main() {
    vec3 N = normalize(vNormal);
    vec3 L = normalize(uLightDir);
    vec3 V = normalize(uCameraPos - vWorldPosition);

    float NdotL = max(dot(N, L), 0.0);
    vec3 diffuse = uDiffuseColor * NdotL;

    float specFactor;
    if (uUseBlinnPhong) {
        vec3 H = normalize(L + V);
        specFactor = pow(max(dot(N, H), 0.0), uShininess);
    } else {
        vec3 R = reflect(-L, N);
        specFactor = pow(max(dot(R, V), 0.0), uShininess);
    }

    vec3 specular = uSpecularColor * specFactor;
    vec3 ambient = uAmbientColor * uDiffuseColor;
    gl_FragColor = vec4(ambient + diffuse + specular, 1.0);
}
`

/**
 * Esfera con shader Lambert custom.
 */
export function LambertSphere({ position, lightDir, color }) {
  const uniforms = useMemo(() => ({
    uLightDir:     { value: new THREE.Vector3(...lightDir) },
    uDiffuseColor: { value: new THREE.Color(color) },
    uAmbientColor: { value: new THREE.Color(0.08, 0.08, 0.1) },
  }), [])

  // Actualizar dirección de luz en cada frame
  useFrame(() => {
    uniforms.uLightDir.value.set(...lightDir)
  })

  return (
    <mesh position={position}>
      <sphereGeometry args={[1, 64, 64]} />
      <shaderMaterial
        vertexShader={lambertVert}
        fragmentShader={lambertFrag}
        uniforms={uniforms}
      />
    </mesh>
  )
}

/**
 * Esfera con shader Phong/Blinn-Phong custom.
 */
export function PhongSphere({ position, lightDir, color, shininess, useBlinnPhong = false }) {
  const ref = useRef()

  const uniforms = useMemo(() => ({
    uLightDir:       { value: new THREE.Vector3(...lightDir) },
    uCameraPos:      { value: new THREE.Vector3(0, 0, 5) },
    uDiffuseColor:   { value: new THREE.Color(color) },
    uSpecularColor:  { value: new THREE.Color(1, 1, 1) },
    uAmbientColor:   { value: new THREE.Color(0.08, 0.08, 0.1) },
    uShininess:      { value: shininess },
    uUseBlinnPhong:  { value: useBlinnPhong },
  }), [])

  useFrame(({ camera }) => {
    uniforms.uLightDir.value.set(...lightDir)
    uniforms.uCameraPos.value.copy(camera.position)
    uniforms.uShininess.value = shininess
    uniforms.uUseBlinnPhong.value = useBlinnPhong
  })

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[1, 64, 64]} />
      <shaderMaterial
        vertexShader={phongVert}
        fragmentShader={phongFrag}
        uniforms={uniforms}
      />
    </mesh>
  )
}
