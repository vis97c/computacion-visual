using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.UI;

public class EscenaParametrica : MonoBehaviour
{
    [System.Serializable]
    public class DatoObjeto
    {
        public float x, y, z;
        public float escala = 1f;
        public string tipo = "Sphere";  // "Sphere" | "Cube" | "Cylinder"
    }

    [Header("Configuracion de la escena")]
    public int cantidadObjetos = 12;
    [Range(0.1f, 2f)]
    public float escalaBase = 0.8f;
    public float rangoX = 5f;
    public float rangoZ = 5f;

    public enum ModoTipo { Mix, SoloEsferas, SoloCubos, SoloCilindros }
    public ModoTipo modoTipo = ModoTipo.Mix;

    public enum ModoColor { PorTipo, PorAltura, Aleatorio }
    public ModoColor modoColor = ModoColor.PorTipo;

    [Header("UI")]
    public Button botonRegenerar;
    public Text textoInfo;


    private List<GameObject> objetosActivos = new List<GameObject>();
    private List<DatoObjeto> datosEscena = new List<DatoObjeto>();

    // Colores por tipo
    private Color colorEsfera = new Color(0.29f, 0.60f, 1.00f);
    private Color colorCubo = new Color(1.00f, 0.42f, 0.42f);
    private Color colorCilindro = new Color(0.32f, 0.85f, 0.55f);

    void Start()
    {
        if (botonRegenerar) botonRegenerar.onClick.AddListener(GenerarEscena);
        GenerarEscena();
    }


    public void GenerarEscena()
    {
        LimpiarEscena();
        datosEscena.Clear();

        List<DatoObjeto> datos;

        datos = GenerarDatosAleatorios();

        // Bucle principal de instanciacion
        for (int i = 0; i < datos.Count; i++)
        {
            DatoObjeto d = datos[i];

            // Condicional: elegir tipo de primitiva
            PrimitiveType tipo = ElegirTipo(i);

            // Crear objeto en tiempo de ejecucion
            GameObject obj = GameObject.CreatePrimitive(tipo);
            obj.name = $"{tipo}_{i:D3}";
            obj.transform.parent = this.transform;

            // Aplicar posicion
            float escala = escalaBase * Random.Range(0.7f, 1.3f);
            obj.transform.position = new Vector3(d.x, d.y + escala * 0.5f, d.z);
            obj.transform.localScale = Vector3.one * escala;

            // Aplicar color
            Renderer rend = obj.GetComponent<Renderer>();
            rend.material.color = ElegirColor(tipo, d.y, i);

            objetosActivos.Add(obj);
            d.tipo = tipo.ToString();
            d.escala = escala;
            datosEscena.Add(d);
        }

        if (textoInfo)
            textoInfo.text = $"Objetos: {objetosActivos.Count} | Modo: {modoTipo}";

        Debug.Log($"[EscenaParametrica] {objetosActivos.Count} objetos generados.");
    }


    List<DatoObjeto> GenerarDatosAleatorios()
    {
        var lista = new List<DatoObjeto>();
        for (int i = 0; i < cantidadObjetos; i++)
        {
            lista.Add(new DatoObjeto
            {
                x = Random.Range(-rangoX, rangoX),
                y = Random.Range(0f, 3f),
                z = Random.Range(-rangoZ, rangoZ)
            });
        }
        return lista;
    }


    PrimitiveType ElegirTipo(int indice)
    {
        switch (modoTipo)
        {
            case ModoTipo.SoloEsferas: return PrimitiveType.Sphere;
            case ModoTipo.SoloCubos: return PrimitiveType.Cube;
            case ModoTipo.SoloCilindros: return PrimitiveType.Cylinder;
            default:  // Mix: ciclo entre los tres tipos
                int mod = indice % 3;
                if (mod == 0) return PrimitiveType.Sphere;
                if (mod == 1) return PrimitiveType.Cube;
                return PrimitiveType.Cylinder;
        }
    }


    Color ElegirColor(PrimitiveType tipo, float y, int indice)
    {
        switch (modoColor)
        {
            case ModoColor.PorTipo:
                if (tipo == PrimitiveType.Sphere) return colorEsfera;
                if (tipo == PrimitiveType.Cube) return colorCubo;
                return colorCilindro;
            case ModoColor.PorAltura:
                float t = Mathf.Clamp01((y + 5f) / 10f);
                return Color.Lerp(Color.blue, Color.red, t);
            default:  // Aleatorio
                return new Color(Random.value, Random.value, Random.value);
        }
    }


    void LimpiarEscena()
    {
        foreach (GameObject obj in objetosActivos)
            Destroy(obj);
        objetosActivos.Clear();
    }
}