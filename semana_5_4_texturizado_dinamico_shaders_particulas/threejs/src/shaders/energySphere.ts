import * as THREE from "three";
import { shaderMaterial } from "@react-three/drei";

/**
 * Material shader personalizado que simula una esfera de energía/plasma.
 * Utiliza ruido Simplex y FBM para crear patrones animados similares a fluidos.
 * Responde a eventos de hover (pasar el ratón) y click.
 */

const vertexShader = /* glsl */ `
  uniform float uTime;
  uniform float uHover;
  uniform float uExplosion;
  
  varying vec2 vUv;
  varying vec3 vPosition;
  varying vec3 vNormal;
  varying float vDisplacement;

  //
  // Ruido Simplex 3D (GLSL)
  //
  vec4 permute(vec4 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
  vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

  float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

    vec3 i  = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);

    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);

    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;

    i = mod(i, 289.0);
    vec4 p = permute(permute(permute(
              i.z + vec4(0.0, i1.z, i2.z, 1.0))
            + i.y + vec4(0.0, i1.y, i2.y, 1.0))
            + i.x + vec4(0.0, i1.x, i2.x, 1.0));

    float n_ = 1.0/7.0;
    vec3  ns = n_ * D.wyz - D.xzx;

    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);

    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);

    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);

    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);

    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));

    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;

    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);

    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x;
    p1 *= norm.y;
    p2 *= norm.z;
    p3 *= norm.w;

    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }

  float fbm(vec3 p) {
    float sum = 0.0;
    float amp = 1.0;
    float freq = 1.0;
    for(int i = 0; i < 4; i++) {
      sum += amp * snoise(p * freq);
      freq *= 2.0;
      amp *= 0.5;
    }
    return sum;
  }

  void main() {
    vUv = uv;
    vNormal = normal;
    vPosition = position;

    // Crear desplazamiento animado usando ruido FBM
    float noiseScale = 1.5 + uHover * 0.5;
    float speed = uTime * 0.3;
    float n = fbm(position * noiseScale + speed);
    
    // Desplazamiento más fuerte en hover
    float displaceAmount = 0.15 + uHover * 0.12;
    
    // Efecto de explosión: expandir hacia afuera
    float explosionDisplace = uExplosion * 1.2;
    
    vec3 newPosition = position + normal * n * displaceAmount;
    newPosition += normal * explosionDisplace;
    
    vDisplacement = n;

    gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  uniform float uTime;
  uniform float uHover;
  uniform float uExplosion;
  uniform vec2 uMouse;
  
  varying vec2 vUv;
  varying vec3 vPosition;
  varying vec3 vNormal;
  varying float vDisplacement;

  // Ruido Simplex para el fragmento
  vec4 permute(vec4 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
  vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

  float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i  = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod(i, 289.0);
    vec4 p = permute(permute(permute(
              i.z + vec4(0.0, i1.z, i2.z, 1.0))
            + i.y + vec4(0.0, i1.y, i2.y, 1.0))
            + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 1.0/7.0;
    vec3  ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }

  void main() {
    // Patrones animados de ruido para el efecto de energía
    float t = uTime * 0.4;
    
    vec3 pos = vPosition * 2.0;
    float n1 = snoise(pos + t);
    float n2 = snoise(pos * 2.0 - t * 0.7);
    float n3 = snoise(pos * 4.0 + t * 0.3);
    
    float pattern = n1 * 0.5 + n2 * 0.3 + n3 * 0.2;

    // La paleta de colores cambia drásticamente con uHover y uTime
    vec3 colorCyan = mix(vec3(0.0, 0.898, 1.0), vec3(0.1, 1.0, 0.2), uHover);
    vec3 colorMagenta = mix(vec3(0.878, 0.251, 0.984), vec3(1.0, 0.2, 0.2), sin(uTime * 0.5) * 0.5 + 0.5);
    vec3 colorGold = mix(vec3(1.0, 0.843, 0.251), vec3(1.0, 0.5, 0.0), uHover);
    vec3 colorDeep = vec3(0.05, 0.0, 0.15);

    // Mezclar colores basado en el ruido y desplazamiento
    float mixFactor = smoothstep(-0.5, 0.8, pattern + vDisplacement * 0.5);
    vec3 color = mix(colorDeep, colorCyan, mixFactor);
    color = mix(color, colorMagenta, smoothstep(0.3, 0.7, pattern));
    
    // Añadir reflejos dorados en los picos
    float highlight = smoothstep(0.5, 0.9, pattern + vDisplacement);
    color = mix(color, colorGold, highlight * 0.6);

    // Influencia del ratón: iluminar cerca de la posición del ratón
    float mouseInfluence = 1.0 - smoothstep(0.0, 0.5, length(vUv - uMouse));
    color += colorCyan * mouseInfluence * 0.15;

    // Resplandor hover: aumentar intensidad
    float hoverGlow = uHover * 0.4;
    color += colorCyan * hoverGlow * (0.5 + 0.5 * sin(uTime * 3.0));

    // Destello de explosión
    color += vec3(1.0, 0.9, 0.7) * uExplosion * 0.8;

    // Iluminación de borde estilo Fresnel
    vec3 viewDir = normalize(cameraPosition - vPosition);
    float fresnel = pow(1.0 - max(dot(viewDir, vNormal), 0.0), 3.0);
    color += colorCyan * fresnel * (0.4 + uHover * 0.3);

    // Venas de energía
    float veins = smoothstep(0.02, 0.0, abs(pattern - 0.1));
    veins += smoothstep(0.02, 0.0, abs(pattern + 0.3));
    color += colorCyan * veins * 1.5;

    // Brillo global
    float brightness = 0.8 + uHover * 0.2 + uExplosion * 0.5;
    color *= brightness;

    // Alpha para desvanecimiento de explosión
    float alpha = 1.0 - uExplosion * 0.3;

    gl_FragColor = vec4(color, alpha);
  }
`;

/**
 * EnergySphereShaderMaterial — extiende shaderMaterial de drei.
 * Uniforms:
 *   uTime      – tiempo transcurrido para la animación
 *   uHover     – 0..1 intensidad del hover
 *   uExplosion – 0..1 intensidad de la explosión
 *   uMouse     – UV normalizado del ratón
 */
const EnergySphereMaterial = shaderMaterial(
  {
    uTime: 0,
    uHover: 0,
    uExplosion: 0,
    uMouse: new THREE.Vector2(0.5, 0.5),
  },
  vertexShader,
  fragmentShader
);

export { EnergySphereMaterial };
