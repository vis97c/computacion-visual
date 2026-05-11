# Taller Escenas Paramétricas: Creación de Objetos desde Datos

Victor Saa, Juan Jose Alvarez, Jose Arturo Herrera Rivera, Juan Pablo Correa, Manuel Santiago Mori Ardila

Fecha de entrega: 25/04/2026

## Descripción

Se generaron objetos 3D de manera programada a partir de listas de coordenadas y datos estructurados. El objetivo fue demostrar cómo crear geometría en tiempo real y de forma flexible mediante código, usando bucles y estructuras condicionales para variar parámetros como el tipo de primitiva, el tamaño y el color de los objetos instanciados. La implementación se realizó en Unity usando C# con `GameObject.CreatePrimitive()`, y se exploró además la exportación y lectura de datos en formato JSON en python (Jupyter).

## Implementación

### Unity (LTS)

Se creó un script en C# (`EscenaParametrica.cs`) que generó múltiples objetos 3D en tiempo de ejecución a partir de listas de coordenadas. La escena incluyó los siguientes elementos:

- **Generación paramétrica**: un bucle `for` recorrió una lista de datos con posiciones `[x, y, z]` e instanció una primitiva (`Sphere`, `Cube` o `Cylinder`) por cada entrada usando `GameObject.CreatePrimitive()`.
- **Condicionales de tipo**: se implementó un enum `ModoTipo` con cuatro opciones: Mix (ciclo entre los tres tipos por índice), SoloEsferas, SoloCubos y SoloCilindros.
- **Condicionales de color**: se implementó un enum `ModoColor` con tres modos: PorTipo (color fijo por tipo de primitiva), PorAltura (gradiente interpolado según la posición Y del objeto) y Aleatorio.
- **Regeneración en tiempo real**: un botón en el Canvas ejecutó `GenerarEscena()`, que destruyó todos los objetos existentes y generó una nueva escena con los parámetros configurados en el Inspector.

El snippet principal del bucle de instanciación fue el siguiente:

```csharp
for (int i = 0; i < datos.Count; i++)
{
    DatoObjeto d = datos[i];

    PrimitiveType tipo = ElegirTipo(i);
    GameObject obj = GameObject.CreatePrimitive(tipo);
    obj.transform.parent = this.transform;

    float escala = escalaBase * Random.Range(0.7f, 1.3f);
    obj.transform.position = new Vector3(d.x, d.y + escala * 0.5f, d.z);
    obj.transform.localScale = Vector3.one * escala;

    Renderer rend = obj.GetComponent<Renderer>();
    rend.material.color = ElegirColor(tipo, d.y, i);

    objetosActivos.Add(obj);
}
```

Una dificultad encontrada fue que al asignar `new Material(Shader.Find("Standard"))`, Unity mostraba los objetos en color rosado porque el shader no se resolvía correctamente en Play Mode. La solución fue modificar directamente el material que `CreatePrimitive()` asigna por defecto, sin reemplazarlo.

### Python (Colab / Jupyter Notebook)

Se implementó un script en Python (`taller2_escenas_parametricas.py`) usando las librerías `trimesh` y `numpy` para generar primitivas 3D a partir de listas de coordenadas y exportar la escena resultante a un archivo `.glb`.

El flujo de trabajo fue el siguiente:

- **Coordenadas de entrada**: se definieron coordenadas manualmente como lista de puntos `[x, y, z]`, y también se generaron coordenadas aleatorias usando `numpy.random.uniform()`.
- **Creación de primitivas**: se usaron las funciones `trimesh.creation.icosphere()`, `trimesh.creation.box()` y `trimesh.creation.cylinder()` para crear esferas, cubos y cilindros respectivamente.
- **Bucles y condicionales**: un bucle `for` recorrió la lista de coordenadas. Dentro del bucle, una condición basada en el índice (`i % 3`) determinó el tipo de objeto a crear en cada posición, replicando la lógica del modo Mix de Unity.
- **Variación de color**: el color de cada objeto se asignó según el tipo de primitiva mediante `mesh.visual.face_colors`, usando valores RGBA.
- **Exportación**: la escena completa se exportó como `escena.glb` usando `trimesh.Scene.export()`, y se generó además un archivo `registro.json` con los metadatos de cada objeto (tipo, posición, escala).

El snippet principal de generación y exportación fue el siguiente:

```python
tipos_ciclo = ['esfera', 'cubo', 'cilindro']

for i, coord in enumerate(coordenadas):
    x, y, z = coord
    tipo = tipos_ciclo[i % 3]
    escala = escala_base * (0.7 + np.random.uniform(0, 0.4))
    mesh = crear_objeto(tipo, [x, y + escala * 0.5, z], escala)
    meshes.append(mesh)

escena = trimesh.Scene()
for i, m in enumerate(meshes):
    escena.add_geometry(m, node_name=f'obj_{i:03d}')

escena.export('exportados/escena.glb')
```

## Resultados visuales

### Escena exportada como .glb abierta en Visor 3D de Windows

Se abrió el archivo `escena.glb` exportado por el script de Python en el Visor 3D de Windows. Se observaron esferas en azul claro, cubos en rosa/salmón y un cilindro en verde, distribuidos en el espacio según las coordenadas definidas en el script. La escena confirmó que la exportación con `trimesh` generó correctamente la geometría y los colores de cada primitiva, y que el archivo era compatible con visores estándar sin necesidad de importarlo a un motor 3D.

### Modo Mix, color aleatorio, 1500 objetos

Se generaron 1500 objetos con el modo Mix activado y color aleatorio, lo que produjo una escena muy densa con esferas, cubos y cilindros distribuidos aleatoriamente. El contador en pantalla mostró "Objetos: 1500". La escena evidenció la capacidad del sistema para manejar grandes cantidades de primitivas instanciadas en tiempo de ejecución.

### Modo SoloEsferas, color aleatorio, 50 objetos

Con el modo SoloEsferas y 50 objetos se observó una nube de esferas de distintos tamaños y colores dispersas en el espacio. Esta configuración permitió verificar que el condicional de tipo funcionaba correctamente y que la variación de escala aleatoria generaba diversidad visual incluso con una sola forma.

### Modo Mix, color por tipo, 25 objetos

Con 25 objetos en modo Mix y color por tipo se pudo apreciar claramente la distinción visual entre primitivas: esferas en azul, cubos en rojo/salmón y cilindros en verde. Esta configuración fue la más útil para validar la lógica condicional de tipo y la asignación de colores, ya que el bajo número de objetos permitió identificar cada instancia individualmente.

## Prompts utilizados

Para el desarrollo de este taller se utilizó IA generativa (Claude) como apoyo en la estructuración del script C# y en la resolución del problema del material rosado. Los prompts principales fueron:

- _"Todos los objetos son rosados tipo sin textura, ¿cómo lo soluciono?"_
- _"A este codigo agrega un botón para regenerar la escena_

## Aprendizajes y dificultades

El taller permitió comprender cómo Unity maneja la instanciación dinámica de objetos en tiempo de ejecución y la importancia de la gestión de memoria al destruir y recrear objetos. El método `Destroy()` sobre cada elemento de la lista antes de regenerar fue clave para evitar que los objetos se acumularan entre generaciones.

La dificultad principal fue el problema del material rosado al intentar asignar un nuevo `Material` con `Shader.Find("Standard")`. Se aprendió que `CreatePrimitive()` ya asigna un material válido, por lo que basta con modificar su `.color` directamente sin reemplazar el material completo.

Otro aprendizaje importante fue la diferencia entre coordenadas generadas aleatoriamente y coordenadas leídas desde un archivo externo: la segunda opción da mucho más control sobre la distribución espacial de los objetos y abre la puerta a escenas generadas desde datos reales.
