# Taller Dashboards Visuales 3D: Sliders y Botones para Controlar Escenas

Victor Saa, Juan Jose Alvarez, Jose Arturo Herrera Rivera, Juan Pablo Correa, Manuel Santiago Mori Ardila

Fecha de entrega: 25/04/2026

## Descripción

Se construyó una interfaz gráfica 3D interactiva en Unity que permitió al usuario controlar en tiempo real los elementos de una escena: las transformaciones de un objeto, su color y el estado de la iluminación. El objetivo fue conectar entradas de usuario (sliders, dropdown y botones) con la modificación directa de un cubo en la escena, demostrando cómo el sistema de UI de Unity puede comunicarse con los componentes de los objetos 3D.

## Implementación

### Unity

Se creó una escena con un cubo centrado y una luz direccional. Usando el sistema Canvas de Unity, se construyó un panel de control con los siguientes elementos:

- **Dropdown de color**: permitió seleccionar entre varios colores predefinidos (Blanco, Rojo, Verde, Azul, Amarillo, Cyan, Magenta) para cambiar el material del cubo en tiempo real.
- **Slider de rotación Y**: controló el ángulo de rotación del cubo sobre su eje vertical, con un rango de 0° a 360°.
- **Slider de escala**: modificó el tamaño uniforme del cubo en los tres ejes, con un rango de 0.3x a 3x.
- **Botón de Animación**: activó y desactivó una rotación automática continua del cubo.
- **Botón de Luz**: encendió y apagó la luz direccional de la escena.
- **Texto de estado**: mostró en pantalla los valores actuales de escala, rotación y estado de la luz (Luz: ON / Luz: OFF).

Se escribió un script en C# (`DashboardController.cs`) que registró los listeners de cada elemento UI y aplicó los cambios directamente sobre el `transform` del cubo y el componente `Renderer` de su material.

El snippet principal de conexión entre UI y escena fue el siguiente:

```csharp
void Start()
{
    sliderEscala.onValueChanged.AddListener(OnEscalaChanged);
    sliderRotacion.onValueChanged.AddListener(OnRotacionChanged);
    botonLuz.onClick.AddListener(ToggleLuz);
    botonAnimacion.onClick.AddListener(ToggleAnimacion);
    dropdownColor.onValueChanged.AddListener(OnColorChanged);
}

void OnEscalaChanged(float valor)
{
    cubo.localScale = new Vector3(valor, valor, valor);
    textoEscala.text = "Escala: " + valor.ToString("F2");
}

void OnColorChanged(int indice)
{
    cuboRenderer.material.color = colores[indice];
}

void ToggleLuz()
{
    luzActiva = !luzActiva;
    luzDireccional.enabled = luzActiva;
    textoEstadoLuz.text = "Luz: " + (luzActiva ? "ON" : "OFF");
}
```

## Resultados visuales

Las capturas muestran el panel funcionando en Play Mode con distintas configuraciones activas.

### Luz apagada, color Rojo

Se observó el cubo con el color Rojo seleccionado en el Dropdown y la luz direccional apagada (Luz: OFF). El cubo pierde el sombreado lateral y se ve plano, lo que evidenció el efecto de la luz sobre el material. Los sliders muestran Rot Y: 86° y Escala: 2.85.

### Luz encendida, color Rojo

Con la luz activada (Luz: ON) y el mismo color Rojo, el cubo recuperó su apariencia tridimensional con sombras visibles en sus caras. La rotación fue de 225° y la escala de 2.85, lo que permitió apreciar el volumen del objeto desde un ángulo lateral.

### Luz encendida, color Blanco, escala reducida

Se cambió el color a Blanco y se redujo la escala a 1.00, con rotación en 321°. El cubo apareció pequeño al fondo de la escena, demostrando cómo la combinación de sliders y dropdown permitió explorar configuraciones muy distintas sin salir del Play Mode.

## Prompts utilizados

Para el desarrollo de este taller se utilizó IA generativa (Claude) como apoyo en la resolución de errores de configuración en el Inspector de Unity. Los prompts principales que se usaron fueron:

- _"¿Cómo configuro el On Value Changed de un Dropdown para cambiar el color del material de un objeto?"_
- _"¿Por qué mo cambia el color con el Dropdown?"_

## Aprendizajes y dificultades

El proceso permitió entender de manera práctica cómo funciona el sistema de eventos de Unity. Uno de los puntos más importantes fue comprender que los listeners de los elementos UI deben registrarse en el método `Start()` para que estén activos desde el primer frame.

La mayor dificultad fue la configuración inicial del Inspector: asignar correctamente cada referencia (cubo, luz, sliders, botones, textos) al script sin omitir ningún campo. En particular, el campo `Cube Renderer` generó confusión al inicio porque Unity acepta el GameObject directamente y extrae el componente `Renderer` automáticamente.

También se identificó que al crear un `new Material(Shader.Find("Standard"))` en tiempo de ejecución, Unity puede no encontrar el shader y mostrar el objeto en color rosado. La solución fue modificar directamente el `material` que `CreatePrimitive()` asigna por defecto, sin reemplazarlo.
