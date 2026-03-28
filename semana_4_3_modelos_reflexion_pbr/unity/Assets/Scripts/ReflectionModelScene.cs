using UnityEngine;

/// <summary>
/// Configura la escena de comparación de modelos de iluminación.
/// Crea esferas con Lambert, Phong, Blinn-Phong y PBR Standard,
/// dispuestas en fila para comparación directa.
/// </summary>
public class ReflectionModelScene : MonoBehaviour
{
    [Header("Shaders Personalizados")]
    [SerializeField] private Shader lambertShader;
    [SerializeField] private Shader phongShader;
    [SerializeField] private Shader blinnPhongShader;

    [Header("Configuración de Escena")]
    [SerializeField] private float sphereSpacing = 3.0f;
    [SerializeField] private int sphereSegments = 64;

    [Header("Parámetros de Material")]
    [SerializeField] private Color diffuseColor = new Color(0.75f, 0.75f, 0.75f, 1f);
    [SerializeField] private Color specularColor = Color.white;
    [SerializeField] private Color ambientColor = new Color(0.1f, 0.1f, 0.12f, 1f);

    [SerializeField, Range(1, 256)]
    private float phongShininess = 32f;

    [SerializeField, Range(1, 256)]
    private float blinnPhongShininess = 64f;

    [Header("Parámetros PBR")]
    [SerializeField, Range(0, 1)] private float pbrMetalness = 0.5f;
    [SerializeField, Range(0, 1)] private float pbrRoughness = 0.35f;

    private Material lambertMat;
    private Material phongMat;
    private Material blinnPhongMat;
    private Material pbrMat;

    private GameObject[] spheres;

    void Start()
    {
        CreateMaterials();
        CreateScene();
    }

    void Update()
    {
        // Actualizar parámetros en tiempo real desde el Inspector
        UpdateMaterialProperties();
    }

    /// <summary>
    /// Crea los materiales para cada modelo de iluminación.
    /// </summary>
    private void CreateMaterials()
    {
        // Lambert
        if (lambertShader != null)
        {
            lambertMat = new Material(lambertShader);
            lambertMat.name = "Lambert Material";
        }
        else
        {
            Debug.LogWarning("Lambert shader not assigned. Using default.");
            lambertMat = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
        }

        // Phong
        if (phongShader != null)
        {
            phongMat = new Material(phongShader);
            phongMat.name = "Phong Material";
        }
        else
        {
            Debug.LogWarning("Phong shader not assigned. Using default.");
            phongMat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
        }

        // Blinn-Phong
        if (blinnPhongShader != null)
        {
            blinnPhongMat = new Material(blinnPhongShader);
            blinnPhongMat.name = "Blinn-Phong Material";
        }
        else
        {
            Debug.LogWarning("Blinn-Phong shader not assigned. Using default.");
            blinnPhongMat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
        }

        // PBR Standard (URP Lit)
        pbrMat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
        pbrMat.name = "PBR Standard Material";

        UpdateMaterialProperties();
    }

    /// <summary>
    /// Crea la escena con 4 esferas, una por modelo, más etiquetas.
    /// </summary>
    private void CreateScene()
    {
        string[] names = { "Lambert", "Phong", "Blinn-Phong", "PBR Standard" };
        Material[] mats = { lambertMat, phongMat, blinnPhongMat, pbrMat };
        spheres = new GameObject[4];

        float startX = -1.5f * sphereSpacing;

        for (int i = 0; i < 4; i++)
        {
            // Crear esfera
            GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            sphere.name = $"Sphere_{names[i]}";
            sphere.transform.position = new Vector3(startX + i * sphereSpacing, 1f, 0f);
            sphere.transform.localScale = Vector3.one * 1.8f;
            sphere.GetComponent<MeshRenderer>().material = mats[i];

            // Aumentar resolución de la malla
            // (Unity usa esferas de baja poly por defecto)
            spheres[i] = sphere;
        }

        // Plano de piso
        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.transform.position = Vector3.zero;
        floor.transform.localScale = new Vector3(3f, 1f, 2f);
        floor.GetComponent<MeshRenderer>().material =
            new Material(Shader.Find("Universal Render Pipeline/Lit"))
            {
                color = new Color(0.7f, 0.7f, 0.72f)
            };
    }

    /// <summary>
    /// Actualiza las propiedades de los materiales desde el Inspector.
    /// Permite ajustar parámetros en tiempo real durante Play mode.
    /// </summary>
    private void UpdateMaterialProperties()
    {
        // Lambert
        if (lambertMat != null)
        {
            lambertMat.SetColor("_DiffuseColor", diffuseColor);
            lambertMat.SetColor("_AmbientColor", ambientColor);
        }

        // Phong
        if (phongMat != null)
        {
            phongMat.SetColor("_DiffuseColor", diffuseColor);
            phongMat.SetColor("_SpecularColor", specularColor);
            phongMat.SetColor("_AmbientColor", ambientColor);
            phongMat.SetFloat("_Shininess", phongShininess);
        }

        // Blinn-Phong
        if (blinnPhongMat != null)
        {
            blinnPhongMat.SetColor("_DiffuseColor", diffuseColor);
            blinnPhongMat.SetColor("_SpecularColor", specularColor);
            blinnPhongMat.SetColor("_AmbientColor", ambientColor);
            blinnPhongMat.SetFloat("_Shininess", blinnPhongShininess);
        }

        // PBR Standard
        if (pbrMat != null)
        {
            pbrMat.SetColor("_BaseColor", diffuseColor);
            pbrMat.SetFloat("_Metallic", pbrMetalness);
            pbrMat.SetFloat("_Smoothness", 1f - pbrRoughness);
        }
    }

    private void OnDestroy()
    {
        // Limpiar materiales creados en runtime
        if (lambertMat != null) Destroy(lambertMat);
        if (phongMat != null) Destroy(phongMat);
        if (blinnPhongMat != null) Destroy(blinnPhongMat);
        if (pbrMat != null) Destroy(pbrMat);
    }
}
