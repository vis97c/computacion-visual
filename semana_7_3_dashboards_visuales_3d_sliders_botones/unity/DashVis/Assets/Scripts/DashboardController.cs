using UnityEngine;
using UnityEngine.UI;

public class DashboardController : MonoBehaviour
{
    // ── Referencias a objetos de la escena ──────────────
    [Header("Objeto 3D")]
    public Transform cubo;           // Arrastra el Cube aqui
    public Renderer cuboRenderer;    // Renderer del Cube

    [Header("Luz Direccional")]
    public Light luzDireccional;     // Arrastra la Directional Light

    // ── Referencias a elementos UI ───────────────────────
    [Header("UI - Sliders")]
    public Slider sliderEscala;      // Slider de escala
    public Slider sliderRotacion;    // Slider de rotacion Y

    [Header("UI - Botones")]
    public Button botonLuz;          // Toggle ON/OFF de la luz
    public Button botonAnimacion;    // Toggle animacion

    [Header("UI - Textos")]
    public Text textoEscala;         // Muestra valor de escala
    public Text textoRotacion;       // Muestra grados de rotacion
    public Text textoEstadoLuz;      // Muestra ON / OFF

    // ── Color Picker (Dropdown) ──────────────────────────
    [Header("Color Picker")]
    public Dropdown dropdownColor;
    private Color[] colores = {
        Color.white, Color.red, Color.green, Color.blue,
        Color.yellow, Color.cyan, Color.magenta
    };

    // ── Estado interno ───────────────────────────────────
    private bool luzActiva = true;
    private bool animActiva = false;
    private float velocidadAnim = 60f; // grados/segundo

    // ────────────────────────────────────────────────────
    void Start()
    {
        // Registrar listeners de sliders
        sliderEscala.onValueChanged.AddListener(OnEscalaChanged);
        sliderRotacion.onValueChanged.AddListener(OnRotacionChanged);

        // Registrar listeners de botones
        botonLuz.onClick.AddListener(ToggleLuz);
        botonAnimacion.onClick.AddListener(ToggleAnimacion);

        // Registrar listener de dropdown
        dropdownColor.onValueChanged.AddListener(OnColorChanged);

        // Inicializar textos con valores por defecto
        ActualizarTextos();
    }

    // ── Slider: Escala ────────────────────────────────────
    void OnEscalaChanged(float valor)
    {
        cubo.localScale = new Vector3(valor, valor, valor);
        textoEscala.text = "Escala: " + valor.ToString("F2");
    }

    // ── Slider: Rotacion Y ────────────────────────────────
    void OnRotacionChanged(float grados)
    {
        cubo.rotation = Quaternion.Euler(0f, grados, 0f);
        textoRotacion.text = "Rot Y: " + Mathf.RoundToInt(grados) + "°";
    }

    // ── Boton: Toggle Luz ─────────────────────────────────
    void ToggleLuz()
    {
        luzActiva = !luzActiva;
        luzDireccional.enabled = luzActiva;
        textoEstadoLuz.text = "Luz: " + (luzActiva ? "ON" : "OFF");
    }

    // ── Boton: Toggle Animacion ───────────────────────────
    void ToggleAnimacion()
    {
        animActiva = !animActiva;
    }

    // ── Dropdown: Color ───────────────────────────────────
    public void OnColorChanged(int indice)
    {
        if (indice < colores.Length)
        {
            cuboRenderer.material.color = colores[indice];
        }
    }

    // ── Update: logica por fotograma ──────────────────────
    void Update()
    {
        if (animActiva)
        {
            cubo.Rotate(Vector3.up, velocidadAnim * Time.deltaTime);
            // Sincronizar slider con rotacion actual
            float angulo = cubo.eulerAngles.y;
            sliderRotacion.SetValueWithoutNotify(angulo);
            textoRotacion.text = "Rot Y: " + Mathf.RoundToInt(angulo) + "°";
        }
    }

    // ── Helpers ───────────────────────────────────────────
    void ActualizarTextos()
    {
        textoEscala.text = "Escala: " + sliderEscala.value.ToString("F2");
        textoRotacion.text = "Rot Y: 0°";
        textoEstadoLuz.text = "Luz: ON";
    }
}
