Shader "Custom/DepthVisualizer"
{
    Properties
    {
        // No necesitamos texturas para este experimento
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 100

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
            };

            struct v2f
            {
                float4 vertex : SV_POSITION;
                float depth : TEXCOORD0; 
            };

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                
                // Calculamos la profundidad lineal aquí para pasarla al fragment
                // UNITY_Z_0_FAR_FROM_CLIPSPACE requiere la Z del espacio de clip
                o.depth = UNITY_Z_0_FAR_FROM_CLIPSPACE(o.vertex.z);
                return o;
            }

            // Cambiamos fixed4 por float4 para evitar el error de identificador
            float4 frag (v2f i) : SV_Target
            {
                float d = i.depth;
                // Retornamos el valor de profundidad como color (R,G,B)
                return float4(d, d, d, 1.0);
            }
            ENDCG
        }
    }
}