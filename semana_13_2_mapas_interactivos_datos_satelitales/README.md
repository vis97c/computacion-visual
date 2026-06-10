# Taller Mapas Interactivos con Datos Satelitales Abiertos

Victor Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

Fecha de entrega: 2026-06-10

## Descripcion breve

El objetivo principal de este taller fue la exploración e implementación de un pipeline completo de visualización geoespacial interactiva usando datos satelitales abiertos. A lo largo de la práctica, se configuró un entorno de trabajo en Python basado en `rasterio`, `folium` y `geopandas` para leer, procesar y visualizar imágenes satelitales en formato GeoTIFF sobre mapas base interactivos. Se evaluó el manejo de sistemas de referencia de coordenadas (CRS), la normalización de bandas espectrales mediante estiramiento por percentiles, el cálculo del índice de vegetación NDVI y la integración de capas vectoriales y raster dentro de un mismo entorno de visualización web.

## Implementaciones

La arquitectura del script se diseñó de forma modular, cubriendo desde la descarga automática de datos hasta la exportación de mapas interactivos listos para usar en el navegador:

1. **Descarga y lectura de datos satelitales:** Se automatizó la descarga de un GeoTIFF real desde el repositorio oficial de `rasterio` (imagen Landsat recortada del Caribe, proyección UTM zona 18N / EPSG:32618) y de una capa vectorial de países en formato GeoJSON. Se implementó la lectura de metadatos del archivo con `rasterio.open()`, incluyendo CRS, dimensiones, resolución espacial y transformación de bounds a WGS84 mediante `transform_bounds`.

2. **Procesamiento y visualización de bandas espectrales:** Se extrajeron las tres bandas del GeoTIFF y se aplicó un estiramiento de contraste por percentiles 2–98 para normalizar las reflectancias. Se generó una visualización comparativa con `matplotlib` que incluyó cada banda individual, la composición color real (RGB), el histograma de densidad por banda y un mapa de luminancia ponderada en escala de calor.

3. **Cálculo del NDVI:** Se simuló una imagen Landsat 8 de Colombia con zonas representativas de distintas coberturas terrestres (selva amazónica, cordillera andina, área urbana, ríos y páramo), y se calculó el NDVI mediante la fórmula estándar `(NIR - Red) / (NIR + Red)`. Se generó una clasificación discreta de cobertura en cinco categorías y un análisis estadístico comparativo por zona mediante boxplots y barras de media con barras de error.

4. **Mapas interactivos con `folium`:** Se construyeron múltiples mapas interactivos con cambio de capas base (OpenStreetMap, CartoDB, ESRI Satellite, Google Hybrid), overlay de la imagen GeoTIFF como `ImageOverlay` con canal alpha para transparencia en píxeles negros, overlay del mapa NDVI sobre Colombia, y capas vectoriales de ciudades con popups informativos al hacer clic. Se integraron plugins como `Fullscreen`, `MiniMap` y `MousePosition` para enriquecer la experiencia de navegación.

5. **Mapa integrado final:** Se consolidaron todas las capas en un único mapa con control de visibilidad independiente por capa, incluyendo cuatro capas base, contorno vectorial de Colombia, overlay satelital RGB, overlay NDVI, marcadores de ciudades y puntos de muestreo NDVI.

## Prompts de IA utilizados

Durante el desarrollo del taller se utilizaron prompts dirigidos a Claude para resolver dudas técnicas específicas y generar fragmentos de código:

- _"¿Cómo transformo los bounds de un GeoTIFF en proyección UTM a coordenadas WGS84 usando rasterio?"_
- _"¿Cómo convierto un array NumPy con un colormap de matplotlib a imagen base64 para usarla como ImageOverlay en folium?"_
- _"¿Cómo aplico un estiramiento de contraste por percentiles a bandas satelitales en Python?"_
- _"¿Cómo agrego canal alpha a una imagen RGB para hacer transparentes los píxeles sin datos en un overlay de folium?"_
- _"¿Cómo calculo NDVI evitando divisiones por cero con np.where?"_

## Resultados visuales

### Análisis de Bandas Espectrales — Imagen Landsat


Se analizó la imagen satelital GeoTIFF descargada desde el repositorio oficial de `rasterio`, correspondiente a una escena Landsat del Caribe. La figura generada presentó seis paneles: las tres bandas espectrales individuales (rojo, verde y azul) normalizadas con estiramiento percentil 2–98, la composición color real RGB, el histograma de densidad por banda y el mapa de luminancia ponderada en escala de calor.

En la composición RGB se distinguió claramente la masa terrestre con cobertura vegetal oscura en la zona central de la imagen, franjas costeras de aguas claras en tonos turquesa y cian hacia el borde inferior, y una acumulación de nubes densas en la esquina superior derecha con valores de reflectancia cercanos a 1.0 en las tres bandas. El histograma de bandas confirmó que la distribución de la banda roja presentó la mayor concentración de valores bajos (pico pronunciado entre 0.0 y 0.1), mientras que la banda azul mostró una distribución más dispersa con un pico secundario notable en el extremo superior, asociado a la reflectancia atmosférica y a los píxeles de nubes. La luminancia ponderada resaltó las nubes como las zonas de mayor brillo, mientras que la vegetación densa quedó representada con valores bajos en la escala inferno.

### Mapa NDVI — Clasificación de Cobertura Vegetal

Se calculó el NDVI sobre una escena sintética representativa de Colombia, modelando cinco zonas de cobertura con reflectancias Landsat 8 realistas. Los valores resultantes cubrieron el rango de –0.30 a 0.90, con una media global de 0.35 y una desviación estándar de 0.20. La zona de selva amazónica registró los valores más altos (media ≈ 0.72), seguida por la cordillera andina (media ≈ 0.48) y los páramos (media ≈ 0.22). El área urbana presentó los valores más bajos de la categoría terrestre (media ≈ 0.08), mientras que los cuerpos de agua mostraron NDVI negativo como se esperaba (media ≈ –0.15), confirmando el correcto comportamiento del índice ante distintas coberturas.

## Codigo relevante

A continuación se presentan los fragmentos más relevantes del pipeline, orientados a la normalización de bandas, el cálculo del NDVI y la generación de overlays interactivos.

### Normalización de Bandas por Percentil y Composición RGB

La técnica de estiramiento por percentiles 2–98 permitió mejorar el contraste visual de la imagen satelital sin saturar los valores extremos causados por nubes o sombras:

```python
def normalizar_banda(banda):
    """Estiramiento de contraste por percentiles 2-98 (técnica estándar en teledetección)."""
    mascara = banda > 0
    if mascara.sum() == 0:
        return np.zeros_like(banda)
    p2, p98 = np.percentile(banda[mascara], [2, 98])
    return np.clip((banda - p2) / (p98 - p2 + 1e-9), 0, 1)

r_norm = normalizar_banda(banda_r)
g_norm = normalizar_banda(banda_g)
b_norm = normalizar_banda(banda_b)
imagen_rgb = np.dstack([r_norm, g_norm, b_norm])
```

### Cálculo del NDVI con Manejo de Valores Inválidos

Se empleó `np.where` para evitar divisiones por cero en píxeles sin datos, asignando `NaN` donde la suma de bandas fuera nula:

```python
with np.errstate(divide='ignore', invalid='ignore'):
    ndvi = np.where(
        (banda_NIR + banda_RED) > 0,
        (banda_NIR - banda_RED) / (banda_NIR + banda_RED),
        np.nan
    )
```

### Conversión de GeoTIFF a Overlay Base64 para Folium

La función principal del pipeline convirtió el array raster a una imagen PNG con canal alpha, codificada en base64 para incrustarse directamente en el HTML del mapa sin requerir servidor de archivos:

```python
def geotiff_a_base64_png(ruta_tiff):
    with rasterio.open(ruta_tiff) as src:
        wgs84 = CRS.from_epsg(4326)
        left, bottom, right, top = transform_bounds(
            src.crs, wgs84,
            src.bounds.left, src.bounds.bottom,
            src.bounds.right, src.bounds.top
        )
        bandas = [src.read(i).astype(np.float32) for i in range(1, src.count + 1)]

    # Canal alpha: transparente en píxeles sin datos
    alpha = np.where(np.max(imagen_rgb, axis=2) > 0.01, 255, 0).astype(np.uint8)
    img_rgba = np.dstack([(imagen_rgb * 255).astype(np.uint8), alpha])

    pil_img = Image.fromarray(img_rgba, mode="RGBA")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}", [bottom, left], [top, right]
```

## Aprendizajes y dificultades

**Manejo de Sistemas de Referencia de Coordenadas (CRS):** El mayor reto inicial fue que el GeoTIFF venía en proyección UTM (EPSG:32618) y folium trabaja exclusivamente en WGS84 (EPSG:4326). Fue necesario transformar los bounds del archivo usando `transform_bounds` de `rasterio.warp` antes de poder posicionar el overlay correctamente sobre el mapa. Sin esta transformación, la imagen aparecía desplazada cientos de kilómetros respecto a su posición real.

**Píxeles sin datos (NoData) en el overlay:** Al convertir el GeoTIFF a imagen para el overlay, los píxeles fuera del área de captura quedaban en negro por tener reflectancia cero, lo que se veía como un recuadro negro opaco sobre el mapa. Se resolvió generando un canal alpha que asignaba transparencia completa a los píxeles con valores menores a 0.01 en todas las bandas, permitiendo ver el mapa base debajo de la imagen.

**Limitación de datos para NDVI real:** La imagen GeoTIFF de ejemplo solo contenía tres bandas en el espectro visible (RGB), sin incluir la banda infrarroja cercana (NIR) indispensable para calcular el NDVI real. En un contexto productivo, este índice requeriría descargar escenas Landsat 8 completas desde USGS EarthExplorer o imágenes Sentinel-2 desde Copernicus Open Access Hub, ambas gratuitas pero que requieren registro. Para el taller se optó por simular reflectancias Landsat 8 realistas que permitieran demostrar el pipeline completo de cálculo y visualización.

Se verificó que `folium.LayerControl()` permite activar y desactivar capas raster y vectoriales de forma independiente, lo cual es clave para el análisis comparativo de coberturas en aplicaciones geoespaciales reales. También se comprobó que incrustar imágenes raster directamente como base64 en el HTML genera archivos pesados pero completamente portables, sin dependencia de servidores externos.
