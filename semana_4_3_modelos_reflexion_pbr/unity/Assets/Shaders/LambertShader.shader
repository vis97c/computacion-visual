Shader "Custom/LambertShader"
{
    Properties
    {
        _DiffuseColor ("Diffuse Color", Color) = (0.75, 0.75, 0.75, 1)
        _AmbientColor ("Ambient Color", Color) = (0.1, 0.1, 0.12, 1)
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
                half4 _AmbientColor;
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

                return output;
            }

            // ------------------------------------------------
            // Fragment Shader: Lambert Diffuse
            // I_diffuse = I_light * k_d * max(N · L, 0)
            // ------------------------------------------------
            half4 frag(Varyings input) : SV_Target
            {
                Light mainLight = GetMainLight();

                half3 N = normalize(input.normalWS);
                half3 L = normalize(mainLight.direction);

                // Componente difusa: Lambert
                half NdotL = max(dot(N, L), 0.0);
                half3 diffuse = mainLight.color.rgb * _DiffuseColor.rgb * NdotL;

                // Componente ambiente
                half3 ambient = _AmbientColor.rgb * _DiffuseColor.rgb;

                half3 finalColor = ambient + diffuse;
                return half4(finalColor, 1.0);
            }

            ENDHLSL
        }
    }

    FallBack "Universal Render Pipeline/Lit"
}
