using UnityEngine;
using UnityEngine.UI;

public class MaterialController : MonoBehaviour
{
    public Material materialPBR;
    public Slider metallicSlider;
    public Slider smoothnessSlider;
    
    void Start()
    {
        // Configurar rangos de los sliders
        metallicSlider.minValue = 0f;
        metallicSlider.maxValue = 1f;
        smoothnessSlider.minValue = 0f;
        smoothnessSlider.maxValue = 1f;
        
        // Configurar valores iniciales
        metallicSlider.value = materialPBR.GetFloat("_MetallicGlossMap");
        smoothnessSlider.value = materialPBR.GetFloat("_Glossiness");
        
        // Agregar listeners
        metallicSlider.onValueChanged.AddListener(ChangeMetallic);
        smoothnessSlider.onValueChanged.AddListener(ChangeSmoothness);
    }
    
    void ChangeMetallic(float value)
    {
        materialPBR.SetFloat("_Metallic", value);
    }
    
    void ChangeSmoothness(float value)
    {
        materialPBR.SetFloat("_Glossiness", value);
    }
}