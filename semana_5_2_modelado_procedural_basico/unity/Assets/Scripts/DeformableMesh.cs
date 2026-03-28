using UnityEngine;

/// <summary>
/// Deforma dinámicamente los vértices de una esfera
/// utilizando manipulación directa de Mesh.vertices
/// 
/// USO: Adjuntar este script a un GameObject vacío con MeshFilter y MeshRenderer,
/// o el script los agregará automáticamente.
/// </summary>
[RequireComponent(typeof(MeshFilter))]
[RequireComponent(typeof(MeshRenderer))]
public class DeformableMesh : MonoBehaviour
{
    [Header("Configuración de Deformación")]
    [SerializeField] private float deformIntensity = 0.3f;
    [SerializeField] private float noiseScale = 2f;
    [SerializeField] private float noiseSpeed = 1.5f;

    [Header("Configuración de Esfera")]
    [SerializeField] private float sphereRadius = 2f;

    private Mesh mesh;
    private Vector3[] originalVertices;
    private Vector3[] modifiedVertices;

    void Start()
    {
        CreateSphere();
    }

    void Update()
    {
        DeformVertices();
    }

    /// <summary>
    /// Crea una esfera procedural
    /// </summary>
    void CreateSphere()
    {
        MeshFilter meshFilter = GetComponent<MeshFilter>();
        
        // Usar esfera primitiva y obtener su mesh
        GameObject tempSphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        mesh = Instantiate(tempSphere.GetComponent<MeshFilter>().sharedMesh);
        DestroyImmediate(tempSphere);

        // Escalar los vértices
        Vector3[] vertices = mesh.vertices;
        for (int i = 0; i < vertices.Length; i++)
        {
            vertices[i] *= sphereRadius;
        }
        mesh.vertices = vertices;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        meshFilter.mesh = mesh;

        // Guardar vértices originales
        originalVertices = mesh.vertices;
        modifiedVertices = new Vector3[originalVertices.Length];

        // Configurar material
        MeshRenderer renderer = GetComponent<MeshRenderer>();
        if (renderer.sharedMaterial == null)
        {
            renderer.material = new Material(Shader.Find("Standard"));
        }
        renderer.material.color = new Color(1f, 0.44f, 0.26f); // Naranja
    }

    /// <summary>
    /// Deforma los vértices usando funciones sinusoidales como ruido
    /// </summary>
    void DeformVertices()
    {
        if (mesh == null || originalVertices == null) return;

        float time = Time.time;

        for (int i = 0; i < originalVertices.Length; i++)
        {
            Vector3 original = originalVertices[i];

            // Calcular ruido basado en posición y tiempo
            float noise = Mathf.Sin(original.x * noiseScale + time * noiseSpeed) *
                          Mathf.Cos(original.y * noiseScale + time * noiseSpeed) *
                          Mathf.Sin(original.z * noiseScale + time * noiseSpeed * 0.7f);

            // Calcular dirección normal (desde centro hacia vértice)
            Vector3 normal = original.normalized;

            // Aplicar deformación en dirección de la normal
            modifiedVertices[i] = original + normal * noise * deformIntensity;
        }

        // Actualizar mesh
        mesh.vertices = modifiedVertices;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
    }

    /// <summary>
    /// Restaura la esfera a su forma original
    /// </summary>
    [ContextMenu("Reset Deformation")]
    void ResetDeformation()
    {
        if (mesh != null && originalVertices != null)
        {
            mesh.vertices = originalVertices;
            mesh.RecalculateNormals();
        }
    }
}
