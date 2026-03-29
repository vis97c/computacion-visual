import { shaderMaterial } from "@react-three/drei";

/**
 * Material shader de partículas personalizado.
 * Renderiza sprites de puntos con tamaño, color y alfa animado.
 */

const vertexShader = /* glsl */ `
  uniform float uTime;
  uniform float uExplosion;
  uniform float uPixelRatio;

  attribute float aSize;
  attribute float aPhase;
  attribute vec3 aColor;
  attribute float aLife;

  varying vec3 vColor;
  varying float vAlpha;

  void main() {
    vColor = aColor;

    vec3 pos = position;

    // Movimiento orbital
    float angle = uTime * 0.5 + aPhase;
    float radius = length(pos.xz);
    pos.x += sin(angle) * 0.08;
    pos.z += cos(angle) * 0.08;
    pos.y += sin(uTime * 0.7 + aPhase * 3.0) * 0.1;

    // Explosión: empujar hacia afuera desde el centro
    if (uExplosion > 0.0) {
      vec3 dir = normalize(pos);
      float force = uExplosion * (2.0 + sin(aPhase * 10.0) * 1.5);
      pos += dir * force;
    }

    // Alfa pulsante basado en vida/fase
    float pulse = 0.6 + 0.4 * sin(uTime * 2.0 + aPhase * 6.28);
    vAlpha = pulse * (1.0 - uExplosion * 0.6);

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);

    // Atenuación del tamaño
    float sizeBase = aSize * (80.0 + uExplosion * 40.0);
    gl_PointSize = sizeBase * uPixelRatio * (1.0 / -mvPosition.z);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const fragmentShader = /* glsl */ `
  varying vec3 vColor;
  varying float vAlpha;

  void main() {
    // Círculo suave con resplandor
    float dist = length(gl_PointCoord - vec2(0.5));
    if (dist > 0.5) discard;
    
    float alpha = smoothstep(0.5, 0.1, dist) * vAlpha;
    
    // Resplandor interior
    float glow = smoothstep(0.5, 0.0, dist);
    vec3 color = vColor + vec3(1.0) * glow * 0.3;

    gl_FragColor = vec4(color, alpha);
  }
`;

const ParticlesMaterial = shaderMaterial(
  {
    uTime: 0,
    uExplosion: 0,
    uPixelRatio: 1,
  },
  vertexShader,
  fragmentShader
);

export { ParticlesMaterial };
