Shader "Custom/Semana03_VertexFragment"
{
    Properties
    {
        _BaseMap ("Base Map", 2D) = "white" {}
        _BaseColor ("Base Color", Color) = (1,1,1,1)
        _GradientA ("Gradient A", Color) = (0.1, 0.4, 1.0, 1.0)
        _GradientB ("Gradient B", Color) = (1.0, 0.4, 0.2, 1.0)
        _WaveAmplitude ("Wave Amplitude", Range(0,1)) = 0.15
        _WaveFrequency ("Wave Frequency", Range(0,20)) = 4.0
        _PatternScale ("Pattern Scale", Range(1,100)) = 20.0
        _DebugMode ("Debug Mode (0 Final, 1 Normal, 2 UV, 3 World, 4 View, 5 Clip, 6 Lambert)", Float) = 0
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }

        Pass
        {
            Name "UniversalForward"
            Tags { "LightMode"="UniversalForward" }

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_BaseMap);
            SAMPLER(sampler_BaseMap);

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                half4 _BaseColor;
                half4 _GradientA;
                half4 _GradientB;
                float _WaveAmplitude;
                float _WaveFrequency;
                float _PatternScale;
                float _DebugMode;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float2 uv         : TEXCOORD0;
                float4 color      : COLOR;
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float3 positionWS  : TEXCOORD1;
                float3 positionVS  : TEXCOORD2;
                float4 positionCS  : TEXCOORD3;
                float3 normalWS    : TEXCOORD4;
                float2 uv          : TEXCOORD0;
                float4 color       : COLOR;
            };

            Varyings vert(Attributes input)
            {
                Varyings output;

                // Object/Model Space: deformación sinusoidal
                float3 deformedOS = input.positionOS.xyz;
                deformedOS.y += sin(deformedOS.x * _WaveFrequency + _Time.y) * _WaveAmplitude;

                // Transformaciones Object -> World / View / Clip
                VertexPositionInputs posInputs = GetVertexPositionInputs(deformedOS);
                VertexNormalInputs normalInputs = GetVertexNormalInputs(input.normalOS);

                output.positionHCS = posInputs.positionCS;
                output.positionWS  = posInputs.positionWS;
                output.positionVS  = posInputs.positionVS;
                output.positionCS  = posInputs.positionCS;
                output.normalWS    = normalize(normalInputs.normalWS);
                output.uv          = TRANSFORM_TEX(input.uv, _BaseMap);
                output.color       = input.color;

                return output;
            }

            half4 frag(Varyings input) : SV_Target
            {
                Light mainLight = GetMainLight();

                half3 N = normalize(input.normalWS);
                half3 L = normalize(mainLight.direction);
                half lambert = saturate(dot(N, L));

                half4 texColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv);

                half gradientMask = saturate(input.uv.y);
                half3 gradient = lerp(_GradientA.rgb, _GradientB.rgb, gradientMask);

                half stripes = 0.5h + 0.5h * sin(input.uv.x * _PatternScale + _Time.y * 2.0h);
                half3 procedural = lerp(gradient, gradient * stripes, 0.4h);

                half3 finalColor = texColor.rgb * _BaseColor.rgb * procedural;
                finalColor *= (0.2h + lambert * mainLight.color.rgb);
                finalColor *= input.color.rgb;

                // Debug modes
                if (_DebugMode < 0.5) return half4(finalColor, 1.0);                                  // Final
                if (_DebugMode < 1.5) return half4(N * 0.5h + 0.5h, 1.0);                             // Normal
                if (_DebugMode < 2.5) return half4(input.uv, 0.0h, 1.0h);                             // UV
                if (_DebugMode < 3.5) return half4(saturate(input.positionWS * 0.1h + 0.5h), 1.0h);  // World
                if (_DebugMode < 4.5) return half4(saturate(input.positionVS * 0.05h + 0.5h), 1.0h); // View
                if (_DebugMode < 5.5) return half4(saturate(input.positionCS.xyz / max(0.0001h, input.positionCS.w) * 0.5h + 0.5h), 1.0h); // Clip/NDC aprox
                return half4(lambert.xxx, 1.0);                                                       // Lambert
            }
            ENDHLSL
        }
    }
}