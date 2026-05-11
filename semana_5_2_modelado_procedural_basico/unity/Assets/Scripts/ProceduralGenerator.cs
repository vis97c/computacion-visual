using UnityEngine;

/// <summary>
/// Generador de geometría procedural que crea:
/// - Rejilla de cubos con animación de ola
/// - Espiral de cilindros rotativa
/// - Malla personalizada (pirámide) con Mesh, Vector3[] y int[]
/// 
/// USO: Adjuntar este script a un GameObject vacío en la escena.
/// </summary>
public class ProceduralGenerator : MonoBehaviour
{
    [Header("Configuración de Rejilla")]
    [SerializeField] private int gridSize = 5;
    [SerializeField] private float gridSpacing = 1.5f;
    [SerializeField] private float cubeScale = 0.5f;
    [SerializeField] private Material cubeMaterial;

    [Header("Configuración de Espiral")]
    [SerializeField] private int spiralElements = 20;
    [SerializeField] private float spiralRadius = 3f;
    [SerializeField] private float spiralHeight = 8f;
    [SerializeField] private float cylinderScale = 0.3f;
    [SerializeField] private Material cylinderMaterial;

    [Header("Configuración de Pirámide")]
    [SerializeField] private float pyramidSize = 2f;
    [SerializeField] private Material pyramidMaterial;

    [Header("Animación")]
    [SerializeField] private float waveSpeed = 2f;
    [SerializeField] private float waveAmplitude = 0.5f;

    private GameObject[] gridCubes;
    private GameObject spiralParent;
    private GameObject pyramidObject;

    void Start()
    {
        GenerateGrid();
        GenerateSpiral();
        GenerateCustomMesh();
    }

    void Update()
    {
        AnimateGrid();
        AnimateSpiral();
    }

    /// <summary>
    /// Genera una rejilla de cubos usando GameObject.CreatePrimitive
    /// </summary>
    void GenerateGrid()
    {
        GameObject gridParent = new GameObject("Grid_Parent");
        gridParent.transform.position = new Vector3(-8f, 0f, 0f);
        gridCubes = new GameObject[gridSize * gridSize];

        int index = 0;
        for (int x = 0; x < gridSize; x++)
        {
            for (int z = 0; z < gridSize; z++)
            {
                GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
                cube.name = $"Cube_{x}_{z}";
                cube.transform.parent = gridParent.transform;
                
                float posX = (x - gridSize / 2f) * gridSpacing;
                float posZ = (z - gridSize / 2f) * gridSpacing;
                cube.transform.localPosition = new Vector3(posX, 0f, posZ);
                cube.transform.localScale = Vector3.one * cubeScale;

                if (cubeMaterial != null)
                    cube.GetComponent<Renderer>().material = cubeMaterial;
                else
                    cube.GetComponent<Renderer>().material.color = Color.HSVToRGB(
                        (float)(x * gridSize + z) / (gridSize * gridSize), 0.7f, 0.9f);

                gridCubes[index++] = cube;
            }
        }
    }

    /// <summary>
    /// Genera una espiral de cilindros
    /// </summary>
    void GenerateSpiral()
    {
        spiralParent = new GameObject("Spiral_Parent");
        spiralParent.transform.position = new Vector3(0f, 0f, 0f);

        for (int i = 0; i < spiralElements; i++)
        {
            GameObject cylinder = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            cylinder.name = $"Cylinder_{i}";
            cylinder.transform.parent = spiralParent.transform;

            float t = (float)i / spiralElements;
            float angle = t * Mathf.PI * 4f; // 2 vueltas completas
            float y = t * spiralHeight - spiralHeight / 2f;
            float x = Mathf.Cos(angle) * spiralRadius;
            float z = Mathf.Sin(angle) * spiralRadius;

            cylinder.transform.localPosition = new Vector3(x, y, z);
            cylinder.transform.localScale = Vector3.one * cylinderScale;
            
            // Orientar cilindro hacia el centro
            cylinder.transform.LookAt(spiralParent.transform.position + Vector3.up * y);

            if (cylinderMaterial != null)
                cylinder.GetComponent<Renderer>().material = cylinderMaterial;
            else
                cylinder.GetComponent<Renderer>().material.color = Color.HSVToRGB(t, 0.8f, 0.9f);
        }
    }

    /// <summary>
    /// Genera una malla personalizada (pirámide) usando Mesh, Vector3[] y int[]
    /// </summary>
    void GenerateCustomMesh()
    {
        pyramidObject = new GameObject("Custom_Pyramid");
        pyramidObject.transform.position = new Vector3(8f, 0f, 0f);

        MeshFilter meshFilter = pyramidObject.AddComponent<MeshFilter>();
        MeshRenderer meshRenderer = pyramidObject.AddComponent<MeshRenderer>();

        Mesh mesh = new Mesh();
        mesh.name = "Procedural_Pyramid";

        float h = pyramidSize;
        float s = pyramidSize * 0.5f;

        // Definir vértices de la pirámide
        Vector3[] vertices = new Vector3[]
        {
            // Base (4 vértices)
            new Vector3(-s, 0, -s),  // 0
            new Vector3(s, 0, -s),   // 1
            new Vector3(s, 0, s),    // 2
            new Vector3(-s, 0, s),   // 3
            // Punta
            new Vector3(0, h, 0),    // 4
            // Vértices duplicados para normales correctas
            new Vector3(-s, 0, -s),  // 5
            new Vector3(s, 0, -s),   // 6
            new Vector3(s, 0, s),    // 7
            new Vector3(-s, 0, s),   // 8
            new Vector3(0, h, 0),    // 9
            new Vector3(0, h, 0),    // 10
            new Vector3(0, h, 0),    // 11
            new Vector3(0, h, 0),    // 12
        };

        // Definir triángulos (índices de vértices)
        int[] triangles = new int[]
        {
            // Base (2 triángulos)
            0, 2, 1,
            0, 3, 2,
            // Cara frontal
            5, 9, 6,
            // Cara derecha
            6, 10, 7,
            // Cara trasera
            7, 11, 8,
            // Cara izquierda
            8, 12, 5
        };

        // Colores por vértice
        Color[] colors = new Color[vertices.Length];
        colors[0] = colors[1] = colors[2] = colors[3] = Color.yellow;
        for (int i = 4; i < colors.Length; i++)
            colors[i] = Color.red;

        mesh.vertices = vertices;
        mesh.triangles = triangles;
        mesh.colors = colors;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        meshFilter.mesh = mesh;

        if (pyramidMaterial != null)
            meshRenderer.material = pyramidMaterial;
        else
        {
            meshRenderer.material = new Material(Shader.Find("Standard"));
            meshRenderer.material.color = new Color(1f, 0.5f, 0f);
        }
    }

    /// <summary>
    /// Anima la rejilla de cubos con efecto de ola
    /// </summary>
    void AnimateGrid()
    {
        if (gridCubes == null) return;

        float time = Time.time;
        int index = 0;

        for (int x = 0; x < gridSize; x++)
        {
            for (int z = 0; z < gridSize; z++)
            {
                if (gridCubes[index] != null)
                {
                    Vector3 pos = gridCubes[index].transform.localPosition;
                    float posX = (x - gridSize / 2f) * gridSpacing;
                    float posZ = (z - gridSize / 2f) * gridSpacing;
                    
                    // Efecto de ola sinusoidal
                    float y = Mathf.Sin(posX * 0.5f + time * waveSpeed) * 
                              Mathf.Cos(posZ * 0.5f + time * waveSpeed) * waveAmplitude;
                    
                    gridCubes[index].transform.localPosition = new Vector3(pos.x, y, pos.z);
                    gridCubes[index].transform.Rotate(Vector3.up, Time.deltaTime * 30f);
                }
                index++;
            }
        }
    }

    /// <summary>
    /// Anima la espiral rotándola
    /// </summary>
    void AnimateSpiral()
    {
        if (spiralParent != null)
        {
            spiralParent.transform.Rotate(Vector3.up, Time.deltaTime * 20f);
        }
    }
}
