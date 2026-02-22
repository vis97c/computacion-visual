using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems; // Para detectar si el usuario toca la UI

public class Sliders : MonoBehaviour
{
    [Tooltip("El nodo con Rigidbody que queremos controlar.")]
    public Transform targetNode;

    [Header("UI Sliders - Posición")]
    public Slider sliderPosX;
    public Slider sliderPosY;
    public Slider sliderPosZ;

    [Header("UI Sliders - Rotación")]
    public Slider sliderRotX;
    public Slider sliderRotY;
    public Slider sliderRotZ;

    [Header("UI Sliders - Escala")]
    public Slider sliderScaleX;
    public Slider sliderScaleY;
    public Slider sliderScaleZ;

    private Rigidbody rb;
    private bool isUpdatingUI = false;

    void Start()
    {
        if (targetNode == null) targetNode = transform;
        rb = targetNode.GetComponent<Rigidbody>();

        // Configuramos rangos iniciales para evitar el salto a 0-1
        SetupInitialRanges();
        
        AddListeners();
        UpdateSlidersFromNode();
    }

    void Update()
    {
        // Solo actualizamos los sliders desde el nodo si el usuario NO está interactuando
        // Esto evita que la física y el ratón "peleen" por el control
        if (!IsUserInteracting())
        {
            UpdateSlidersFromNode();
        }
    }

    // Comprueba si el usuario tiene seleccionado algún slider
    bool IsUserInteracting()
    {
        if (EventSystem.current == null) return false;
        GameObject selected = EventSystem.current.currentSelectedGameObject;
        if (selected == null) return false;
        
        return selected.GetComponentInParent<Slider>() != null;
    }

    void SetupInitialRanges()
    {
        // Asignamos rangos generosos por defecto si están en 0-1
        Slider[] sPos = { sliderPosX, sliderPosY, sliderPosZ };
        foreach (var s in sPos) if (s && s.maxValue <= 1) { s.minValue = -100; s.maxValue = 100; }

        Slider[] sRot = { sliderRotX, sliderRotY, sliderRotZ };
        foreach (var s in sRot) if (s) { s.minValue = 0; s.maxValue = 360; }
    }

    void UpdateSlidersFromNode()
    {
        if (targetNode == null) return;
        isUpdatingUI = true;

        // Función auxiliar para actualizar slider y expandir rango si es necesario
        UpdateSliderValues(sliderPosX, targetNode.localPosition.x);
        UpdateSliderValues(sliderPosY, targetNode.localPosition.y);
        UpdateSliderValues(sliderPosZ, targetNode.localPosition.z);

        if (sliderRotX) sliderRotX.value = Mathf.Repeat(targetNode.localEulerAngles.x, 360);
        if (sliderRotY) sliderRotY.value = Mathf.Repeat(targetNode.localEulerAngles.y, 360);
        if (sliderRotZ) sliderRotZ.value = Mathf.Repeat(targetNode.localEulerAngles.z, 360);

        if (sliderScaleX) sliderScaleX.value = targetNode.localScale.x;
        if (sliderScaleY) sliderScaleY.value = targetNode.localScale.y;
        if (sliderScaleZ) sliderScaleZ.value = targetNode.localScale.z;

        isUpdatingUI = false;
    }

    void UpdateSliderValues(Slider s, float value)
    {
        if (!s) return;
        // Si el valor escapa del rango, ampliamos el rango dinámicamente
        if (value > s.maxValue) s.maxValue = value + 5;
        if (value < s.minValue) s.minValue = value - 5;
        s.value = value;
    }

    public void OnUIValueChanged(float dummy)
    {
        if (isUpdatingUI || targetNode == null) return;

        // Cuando el usuario mueve un slider, desactivamos la gravedad momentáneamente
        // para que sea más fácil de manipular
        if (rb != null) {
            rb.useGravity = false;
            rb.linearVelocity = Vector3.zero;
            rb.angularVelocity = Vector3.zero;
        }

        targetNode.localPosition = new Vector3(
            sliderPosX ? sliderPosX.value : targetNode.localPosition.x,
            sliderPosY ? sliderPosY.value : targetNode.localPosition.y,
            sliderPosZ ? sliderPosZ.value : targetNode.localPosition.z
        );

        targetNode.localEulerAngles = new Vector3(
            sliderRotX ? sliderRotX.value : targetNode.localEulerAngles.x,
            sliderRotY ? sliderRotY.value : targetNode.localEulerAngles.y,
            sliderRotZ ? sliderRotZ.value : targetNode.localEulerAngles.z
        );

        targetNode.localScale = new Vector3(
            sliderScaleX ? sliderScaleX.value : targetNode.localScale.x,
            sliderScaleY ? sliderScaleY.value : targetNode.localScale.y,
            sliderScaleZ ? sliderScaleZ.value : targetNode.localScale.z
        );

        if (rb != null) {
            rb.position = targetNode.position;
            rb.rotation = targetNode.rotation;
        }
    }

    // Se llama automáticamente cuando dejamos de tocar el slider (puedes añadir esto al EventTrigger del Slider)
    public void OnReleaseSlider()
    {
        if (rb != null) rb.useGravity = true;
    }

    void AddListeners()
    {
        Slider[] allSliders = { sliderPosX, sliderPosY, sliderPosZ, sliderRotX, sliderRotY, sliderRotZ, sliderScaleX, sliderScaleY, sliderScaleZ };
        foreach (var s in allSliders)
        {
            if (s != null) s.onValueChanged.AddListener(OnUIValueChanged);
        }
    }
}