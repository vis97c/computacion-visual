using UnityEngine;
using UnityEngine.UI;
using TMPro;

// ═══════════════════════════════════════════════════════════
// ProyeccionCamaraController
// Controla el modo de proyección de la cámara (perspectiva /
// ortográfica) y expone parámetros ajustables desde la UI.
//
// Se adjunta a un GameObject vacío llamado "GameController".
// ═══════════════════════════════════════════════════════════
public class ProyeccionCamaraController : MonoBehaviour
{
    // ── Referencia a la cámara ───────────────────────────────
    [Header("Cámara")]
    [Tooltip("Arrastra la Main Camera aquí")]
    public Camera camara;

    // ── Parámetros de perspectiva ────────────────────────────
    [Header("Perspectiva")]
    [Range(10f, 120f)]
    public float campoPVision = 60f;   // Field of View

    // ── Parámetros de ortográfica ────────────────────────────
    [Header("Ortográfica")]
    [Range(1f, 20f)]
    public float tamanoOrtografico = 5f;   // Orthographic Size

    // ── Estado actual ────────────────────────────────────────
    private bool esPerspectiva = true;

    // ── Referencias UI — Sliders ─────────────────────────────
    [Header("UI — Sliders")]
    public Slider sliderFOV;
    public Slider sliderOrtSize;

    // ── Referencias UI — Textos TMP ──────────────────────────
    [Header("UI — Textos")]
    public TMP_Text textoModo;
    public TMP_Text textoFOV;
    public TMP_Text textoOrtSize;
    public TMP_Text textoMatriz;

    // ────────────────────────────────────────────────────────
    // Start
    // ────────────────────────────────────────────────────────
    void Start()
    {
        if (camara == null)
            camara = Camera.main;

        // Aplicamos valores iniciales
        camara.orthographic     = false;
        camara.fieldOfView      = campoPVision;
        camara.orthographicSize = tamanoOrtografico;

        InicializarSliders();
        ActualizarUI();
    }

    // ────────────────────────────────────────────────────────
    // Update
    // ────────────────────────────────────────────────────────
    void Update()
    {
        LeerSliders();

        // Aplicamos parámetros a la cámara según el modo activo
        if (esPerspectiva)
        {
            camara.orthographic = false;
            camara.fieldOfView  = campoPVision;
        }
        else
        {
            camara.orthographic     = true;
            camara.orthographicSize = tamanoOrtografico;
        }

        ActualizarUI();
    }

    // ────────────────────────────────────────────────────────
    // Llamado por el botón "Cambiar Modo"
    // ────────────────────────────────────────────────────────
    public void CambiarModo()
    {
        esPerspectiva = !esPerspectiva;

        // Imprimimos la matriz de proyección en consola (Opcional)
        Debug.Log("════════════════════════════════════════");
        Debug.Log($"Modo: {(esPerspectiva ? "PERSPECTIVA" : "ORTOGRÁFICA")}");
        Debug.Log("Matriz de proyección:");
        Debug.Log(camara.projectionMatrix);
        Debug.Log("════════════════════════════════════════");
    }

    // ────────────────────────────────────────────────────────
    // Inicializa los sliders con los valores por defecto
    // ────────────────────────────────────────────────────────
    void InicializarSliders()
    {
        if (sliderFOV     != null) sliderFOV.value     = campoPVision;
        if (sliderOrtSize != null) sliderOrtSize.value = tamanoOrtografico;
    }

    // ────────────────────────────────────────────────────────
    // Lee los valores de los sliders cada frame
    // ────────────────────────────────────────────────────────
    void LeerSliders()
    {
        if (sliderFOV     != null) campoPVision        = sliderFOV.value;
        if (sliderOrtSize != null) tamanoOrtografico   = sliderOrtSize.value;
    }

    // ────────────────────────────────────────────────────────
    // Actualiza todos los textos de la UI
    // ────────────────────────────────────────────────────────
    void ActualizarUI()
    {
        if (textoModo != null)
            textoModo.text = esPerspectiva ? "PERSPECTIVA" : "ORTOGRÁFICA";

        if (textoFOV != null)
            textoFOV.text = $"FOV: {campoPVision:F0}°";

        if (textoOrtSize != null)
            textoOrtSize.text = $"Ortho Size: {tamanoOrtografico:F1}";

        // Mostramos la matriz de proyección actual en pantalla
        if (textoMatriz != null)
        {
            Matrix4x4 m = camara.projectionMatrix;
            textoMatriz.text =
                $"Matriz de proyección:\n" +
                $"[{m[0,0]:F2}  {m[0,1]:F2}  {m[0,2]:F2}  {m[0,3]:F2}]\n" +
                $"[{m[1,0]:F2}  {m[1,1]:F2}  {m[1,2]:F2}  {m[1,3]:F2}]\n" +
                $"[{m[2,0]:F2}  {m[2,1]:F2}  {m[2,2]:F2}  {m[2,3]:F2}]\n" +
                $"[{m[3,0]:F2}  {m[3,1]:F2}  {m[3,2]:F2}  {m[3,3]:F2}]";
        }
    }
}