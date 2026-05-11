Shader "Custom/BlinnPhongShader"
{
    Properties
    {
        _DiffuseColor  ("Diffuse Color", Color)  = (0.75, 0.75, 0.75, 1)
        _SpecularColor ("Specular Color", Color) = (1, 1, 1, 1)
        _AmbientColor  ("Ambient Color", Color)  = (0.1, 0.1, 0.12, 1)
        _Shininess     ("Shininess", Range(1, 256)) = 64
    }

    SubShader
    {
        Tags
        {
            "RenderType" = "Opaque"
            "RenderPipeline" = "UniversalPipeline"
            "Queue" = "Geometry"
        }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            // ------------------------------------------------
            // Properties
            // ------------------------------------------------
            CBUFFER_START(UnityPerMaterial)
                half4 _DiffuseColor;
                half4 _SpecularColor;
                half4 _AmbientColor;
                half  _Shininess;
            CBUFFER_END

            // ------------------------------------------------
            // Structs
            // ------------------------------------------------
            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float3 normalWS    : TEXCOORD0;
                float3 positionWS  : TEXCOORD1;
            };

            // ------------------------------------------------
            // Vertex Shader
            // ------------------------------------------------
            Varyings vert(Attributes input)
            {
                Varyings output;

                VertexPositionInputs posInputs = GetVertexPositionInputs(input.positionOS.xyz);
                VertexNormalInputs normalInputs = GetVertexNormalInputs(input.normalOS);

                output.positionHCS = posInputs.positionCS;
                output.normalWS    = normalize(normalInputs.normalWS);
                output.positionWS  = posInputs.positionWS;

                return output;
            }

            // ------------------------------------------------
            // Fragment Shader: Blinn-Phong
            // Usa half vector H = normalize(L + V) en lugar de R
            // I_specular = I_light * k_s * max(N · H, 0)^shininess
            // ------------------------------------------------
            half4 frag(Varyings input) : SV_Target
            {
                Light mainLight = GetMainLight();

                half3 N = normalize(input.normalWS);
                half3 L = normalize(mainLight.direction);
                half3 V = normalize(_WorldSpaceCameraPos - input.positionWS);

                // Half vector: optimización respecto al vector de reflexión
                half3 H = normalize(L + V);

                // Componente difusa
                half NdotL = max(dot(N, L), 0.0);
                half3 diffuse = mainLight.color.rgb * _DiffuseColor.rgb * NdotL;

                // Componente especular: Blinn-Phong con half vector
                half NdotH = max(dot(N, H), 0.0);
                half3 specular = mainLight.color.rgb * _SpecularColor.rgb * pow(NdotH, _Shininess);

                // Componente ambiente
                half3 ambient = _AmbientColor.rgb * _DiffuseColor.rgb;

                half3 finalColor = ambient + diffuse + specular;
                return half4(finalColor, 1.0);
            }

            ENDHLSL
        }
    }

    FallBack "Universal Render Pipeline/Lit"
}
