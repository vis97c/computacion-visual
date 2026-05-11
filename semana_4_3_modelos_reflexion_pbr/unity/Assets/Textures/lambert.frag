// Fragment Shader: Lambert (Difuso)
// I_diffuse = k_d * max(N · L, 0)

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
