using UnityEngine;

public class NormalVisualizer : MonoBehaviour
{
    public bool showNormals = true; // El "botón" en el Inspector
    public float lineLength = 0.2f;

    // Esto se ve en la ventana Scene (Editor)
    void OnDrawGizmos()
    {
        if (showNormals) DrawNormals();
    }

    // Esto se ve en la ventana Game (Ejecución)
    void OnPostRender()
    {
        if (showNormals) DrawNormalsGL();
    }

    void DrawNormals()
    {
        MeshFilter mf = GetComponent<MeshFilter>();
        if (!mf || !mf.sharedMesh) return;

        Mesh mesh = mf.sharedMesh;
        for (int i = 0; i < mesh.vertexCount; i++)
        {
            Vector3 worldPos = transform.TransformPoint(mesh.vertices[i]);
            Vector3 worldNormal = transform.TransformDirection(mesh.normals[i]);
            Gizmos.color = Color.yellow;
            Gizmos.DrawLine(worldPos, worldPos + worldNormal * lineLength);
        }
    }

    // Método para dibujar en la ventana de Game
    void DrawNormalsGL()
    {
        MeshFilter mf = GetComponent<MeshFilter>();
        Mesh mesh = mf.sharedMesh;

        GL.Begin(GL.LINES);
        GL.Color(Color.yellow);
        for (int i = 0; i < mesh.vertexCount; i++)
        {
            Vector3 v = transform.TransformPoint(mesh.vertices[i]);
            Vector3 n = transform.TransformDirection(mesh.normals[i]);
            GL.Vertex(v);
            GL.Vertex(v + n * lineLength);
        }
        GL.End();
    }
}