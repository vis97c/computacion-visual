using UnityEngine;

/// <summary>
/// Genera una grilla de esferas PBR variando metalness y roughness
/// para crear una biblioteca visual de materiales.
/// Eje X: metalness (0 → 1), Eje Z: roughness (0.1 → 0.9)
/// </summary>
public class PBRMaterialGrid : MonoBehaviour
{
    [Header("Configuración de Grilla")]
    [SerializeField] private int gridSize = 5;
    [SerializeField] private float spacing = 2.5f;
    [SerializeField] private Color baseColor = new Color(0.9f, 0.55f, 0.2f, 1f);

    [Header("Rangos de Parámetros")]
    [SerializeField] private float minMetalness = 0f;
    [SerializeField] private float maxMetalness = 1f;
    [SerializeField] private float minRoughness = 0.1f;
    [SerializeField] private float maxRoughness = 0.9f;

    private GameObject[,] sphereGrid;
    private Material[,] materialGrid;

    void Start()
    {
        CreateGrid();
    }

    /// <summary>
    /// Crea la grilla de esferas con materiales PBR.
    /// Cada esfera tiene valores únicos de metalness y roughness.
    /// </summary>
    private void CreateGrid()
    {
        sphereGrid = new GameObject[gridSize, gridSize];
        materialGrid = new Material[gridSize, gridSize];

        float offsetX = -(gridSize - 1) * spacing / 2f;
        float offsetZ = -(gridSize - 1) * spacing / 2f;

        for (int row = 0; row < gridSize; row++)
        {
            // roughness varía por fila
            float roughness = Mathf.Lerp(minRoughness, maxRoughness, (float)row / (gridSize - 1));

            for (int col = 0; col < gridSize; col++)
            {
                // metalness varía por columna
                float metalness = Mathf.Lerp(minMetalness, maxMetalness, (float)col / (gridSize - 1));

                // Crear esfera
                GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                sphere.name = $"PBR_M{metalness:F2}_R{roughness:F2}";
                sphere.transform.parent = transform;
                sphere.transform.position = new Vector3(
                    offsetX + col * spacing,
                    1f,
                    offsetZ + row * spacing
                );

                // Crear material PBR
                Material mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                mat.name = $"PBR M={metalness:F2} R={roughness:F2}";
                mat.SetColor("_BaseColor", baseColor);
                mat.SetFloat("_Metallic", metalness);
                mat.SetFloat("_Smoothness", 1f - roughness);

                sphere.GetComponent<MeshRenderer>().material = mat;

                sphereGrid[row, col] = sphere;
                materialGrid[row, col] = mat;
            }
        }

        Debug.Log($"PBR Grid created: {gridSize}x{gridSize} spheres");
        Debug.Log($"Metalness: {minMetalness} → {maxMetalness} (columns)");
        Debug.Log($"Roughness: {minRoughness} → {maxRoughness} (rows)");
    }

    private void OnDestroy()
    {
        if (materialGrid == null) return;
        for (int r = 0; r < gridSize; r++)
            for (int c = 0; c < gridSize; c++)
                if (materialGrid[r, c] != null)
                    Destroy(materialGrid[r, c]);
    }
}
