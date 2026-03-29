# Taller UV Mapping: Texturas que Encajan

Jose Arturo Herrera Rivera

Fecha de entrega: 28/03/2026

## Descripción

Explorar el mapeo UV como técnica fundamental para aplicar correctamente texturas 2D sobre modelos 3D sin distorsión. El objetivo es entender cómo se proyectan las texturas y cómo se pueden ajustar las coordenadas UV para mejorar el resultado visual.

## Implementaciónes

### Unity

Para el desarrollo de la práctica se utilizó Blender como herramienta principal de modelado y mapeo UV, junto con Unity como entorno de visualización final del modelo.

Inicialmente, se procedió a la creación de un modelo 3D básico dentro de Blender. Una vez definido el modelo, se realizó un proceso de UV Unwrapping automático, con el objetivo de obtener una primera proyección de las coordenadas UV sobre una textura bidimensional.

Posteriormente, se aplicó un patrón de ajedrez (checker map) como textura de prueba. Esta técnica permitió identificar visualmente posibles distorsiones, estiramientos o inconsistencias en la distribución de las coordenadas UV sobre la superficie del modelo.

A partir de este análisis, se llevó a cabo una mejora del mapeo mediante la definición manual de cortes (seams) en zonas estratégicas del modelo. Estos cortes facilitaron una mejor distribución de las islas UV, reduciendo la distorsión de la textura y optimizando el aprovechamiento del espacio en el mapa UV.

Una vez finalizado el ajuste del mapeo, el modelo fue exportado en un formato compatible y posteriormente importado en Unity, donde se verificó su correcta visualización y aplicación de la textura dentro de un entorno en tiempo real.

## Resultados visuales

Como resultado del proceso, se logró evidenciar la importancia del mapeo UV en la correcta aplicación de texturas sobre modelos 3D.

En una primera etapa, el uso del unwrap automático generó ciertas distorsiones visibles en el patrón de ajedrez, lo cual indicó problemas en la distribución de las coordenadas UV. Sin embargo, tras la implementación de cortes manuales y la reorganización de las islas UV, se obtuvo una mejora significativa en la uniformidad del patrón, reduciendo los estiramientos y logrando una representación más fiel de la textura.

Durante la importación en Unity, se identificaron algunos detalles adicionales en la geometría del modelo que afectan la calidad del resultado final, como irregularidades en la topología. Esto evidenció que, aunque el mapeo UV puede optimizarse, la calidad del modelo base también influye directamente en el resultado visual.

En general, el modelo final presentó una correcta aplicación de la textura, aunque con oportunidades de mejora relacionadas con la estructura geométrica.

Figura 1. Visualización del modelo en Unity
Se observa el modelo importado en Unity con la textura aplicada. El patrón de ajedrez permite identificar la distribución general de la textura sobre la superficie del objeto. Aunque la textura se visualiza correctamente, se evidencian ligeras irregularidades en algunas zonas curvas, lo que indica problemas en el mapeo UV inicial.

Figura 2. Mapeo UV inicial en Blender
En esta etapa, el unwrap presenta una distribución continua pero poco optimizada. La malla UV se encuentra comprimida en ciertas áreas, lo que genera distorsión en la textura, especialmente en zonas con cambios de curvatura.

Figura 3. Aplicación del patrón de prueba (checker map)
Al aplicar el patrón de ajedrez, se evidencian claramente los problemas de estiramiento en la textura. Algunas casillas no mantienen una proporción uniforme, lo cual confirma la necesidad de ajustar el mapeo UV manualmente.

Posteriormente, se realizaron cortes estratégicos en la geometría del modelo para mejorar la distribución del mapeo.

Figura 4. Nuevo mapeo UV con cortes (seams)
Se observa una reorganización de las islas UV, donde las distintas partes del modelo han sido separadas y distribuidas de manera más eficiente dentro del espacio UV. Esto permite reducir la distorsión y mejorar el aprovechamiento del área disponible.

Figura 5. Resultado final con textura ajustada
Tras la optimización del mapeo UV, el patrón de ajedrez presenta una distribución mucho más uniforme sobre la superficie del modelo. Las casillas mantienen proporciones más consistentes, lo que indica una mejora significativa en la calidad del mapeo.

A pesar de estas mejoras, se identificó que algunas imperfecciones persisten debido a la topología del modelo, lo que sugiere la necesidad de aplicar técnicas adicionales como la retopología para alcanzar un resultado óptimo.

## Aprendizajes

A partir de esta práctica, se adquirieron varios conocimientos clave relacionados con el mapeo UV y su impacto en el desarrollo de gráficos 3D.

En primer lugar, se comprendió que el UV mapping es un proceso fundamental para evitar distorsiones en las texturas, y que un unwrap automático no siempre produce resultados óptimos, siendo necesario realizar ajustes manuales.

También se aprendió la utilidad del uso de texturas de prueba, como el patrón de ajedrez, para detectar errores de forma rápida y visual, lo cual facilita el proceso de corrección.

Adicionalmente, se evidenció la importancia de definir correctamente los seams, ya que estos determinan cómo se “despliega” la superficie del modelo en el espacio 2D.

Finalmente, se identificó que la calidad del mapeo UV está estrechamente relacionada con la topología del modelo, y que en algunos casos es necesario aplicar procesos como la retopología para obtener mejores resultados. Esto resalta la importancia de una buena planificación del modelado desde etapas tempranas del desarrollo.
