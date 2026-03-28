// Fragment Shader: Phong / Blinn-Phong
// Soporta ambos modelos via uniform uUseBlinnPhong

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

    // Componente difusa (Lambert)
    float NdotL = max(dot(N, L), 0.0);
    vec3 diffuse = uDiffuseColor * NdotL;

    // Componente especular
    float specFactor;

    if (uUseBlinnPhong) {
        // Blinn-Phong: usa half vector H = normalize(L + V)
        vec3 H = normalize(L + V);
        float NdotH = max(dot(N, H), 0.0);
        specFactor = pow(NdotH, uShininess);
    } else {
        // Phong clásico: usa vector de reflexión R = reflect(-L, N)
        vec3 R = reflect(-L, N);
        float RdotV = max(dot(R, V), 0.0);
        specFactor = pow(RdotV, uShininess);
    }

    vec3 specular = uSpecularColor * specFactor;

    // Componente ambiente
    vec3 ambient = uAmbientColor * uDiffuseColor;

    vec3 finalColor = ambient + diffuse + specular;
    gl_FragColor = vec4(finalColor, 1.0);
}
