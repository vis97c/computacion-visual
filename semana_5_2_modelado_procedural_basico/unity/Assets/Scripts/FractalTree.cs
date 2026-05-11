using UnityEngine;

/// <summary>
/// Genera un árbol fractal recursivo con cilindros como ramas
/// y esferas como hojas en los extremos.
/// 
/// USO: Adjuntar este script a un GameObject vacío en la escena.
/// </summary>
public class FractalTree : MonoBehaviour
{
    [Header("Configuración del Árbol")]
    [SerializeField] private int maxDepth = 4;
    [SerializeField] private float trunkLength = 2f;
    [SerializeField] private float trunkRadius = 0.15f;
    [SerializeField] private float lengthMultiplier = 0.7f;
    [SerializeField] private float radiusMultiplier = 0.7f;
    [SerializeField] private float branchAngle = 30f;

    [Header("Materiales")]
    [SerializeField] private Material branchMaterial;
    [SerializeField] private Material leafMaterial;

    [Header("Animación")]
    [SerializeField] private float swaySpeed = 1f;
    [SerializeField] private float swayAmount = 5f;

    private GameObject treeRoot;

    void Start()
    {
        GenerateTree();
    }

    void Update()
    {
        // Animación suave de balanceo
        if (treeRoot != null)
        {
            float sway = Mathf.Sin(Time.time * swaySpeed) * swayAmount;
            treeRoot.transform.rotation = Quaternion.Euler(sway * 0.3f, 0f, sway * 0.2f);
        }
    }

    /// <summary>
    /// Inicia la generación del árbol fractal
    /// </summary>
    void GenerateTree()
    {
        treeRoot = new GameObject("FractalTree_Root");
        treeRoot.transform.position = new Vector3(0f, -3f, -8f);
        
        CreateBranch(treeRoot.transform, trunkLength, trunkRadius, 0);
    }

    /// <summary>
    /// Crea una rama recursivamente
    /// </summary>
    void CreateBranch(Transform parent, float length, float radius, int depth)
    {
        if (depth > maxDepth) return;

        // Crear cilindro para la rama
        GameObject branch = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        branch.name = $"Branch_Depth{depth}";
        branch.transform.parent = parent;
        branch.transform.localPosition = Vector3.up * length * 0.5f;
        branch.transform.localScale = new Vector3(radius * 2f, length * 0.5f, radius * 2f);

        // Aplicar material o color basado en profundidad
        Renderer renderer = branch.GetComponent<Renderer>();
        if (branchMaterial != null)
        {
            renderer.material = branchMaterial;
        }
        else
        {
            float hue = 0.08f + (float)depth / maxDepth * 0.1f;
            renderer.material.color = Color.HSVToRGB(hue, 0.6f, 0.4f - depth * 0.05f);
        }

        // Si llegamos al final, agregar hojas
        if (depth == maxDepth)
        {
            CreateLeaf(branch.transform, length);
            return;
        }

        // Crear punto de ramificación
        GameObject branchPoint = new GameObject($"BranchPoint_{depth}");
        branchPoint.transform.parent = branch.transform;
        branchPoint.transform.localPosition = Vector3.up * 1f;

        float nextLength = length * lengthMultiplier;
        float nextRadius = radius * radiusMultiplier;

        // Crear 4 ramas hijas en diferentes direcciones
        for (int i = 0; i < 4; i++)
        {
            GameObject childBranch = new GameObject($"ChildBranch_{depth}_{i}");
            childBranch.transform.parent = branchPoint.transform;
            childBranch.transform.localPosition = Vector3.zero;

            float yRotation = i * 90f + (depth * 45f);
            childBranch.transform.localRotation = Quaternion.Euler(branchAngle, yRotation, 0f);

            CreateBranch(childBranch.transform, nextLength, nextRadius, depth + 1);
        }
    }

    /// <summary>
    /// Crea una hoja (esfera) en el extremo de una rama
    /// </summary>
    void CreateLeaf(Transform parent, float size)
    {
        GameObject leaf = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        leaf.name = "Leaf";
        leaf.transform.parent = parent;
        leaf.transform.localPosition = Vector3.up * 1.2f;
        leaf.transform.localScale = Vector3.one * size * 0.3f;

        Renderer renderer = leaf.GetComponent<Renderer>();
        if (leafMaterial != null)
        {
            renderer.material = leafMaterial;
        }
        else
        {
            renderer.material.color = new Color(0.2f, 0.8f, 0.3f);
        }
    }

    /// <summary>
    /// Regenera el árbol (útil para cambios en el inspector)
    /// </summary>
    [ContextMenu("Regenerate Tree")]
    void RegenerateTree()
    {
        if (treeRoot != null)
        {
            DestroyImmediate(treeRoot);
        }
        GenerateTree();
    }
}
