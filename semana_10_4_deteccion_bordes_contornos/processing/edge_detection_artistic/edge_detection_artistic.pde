/**
 * Taller: Detección de Bordes y Contornos
 * Componente: Processing (Implementación manual de Sobel y Convolución)
 * 
 * Este sketch carga una imagen de prueba, realiza la convolución manual con kernels 
 * de Sobel X y Sobel Y sin usar librerías externas de visión artificial, calcula la 
 * magnitud del gradiente, y genera un efecto artístico tipo "Neon Glow" o "Boceto a Lápiz".
 * 
 * Controles de teclado:
 * '1' - Ver Imagen Original
 * '2' - Ver Bordes Sobel X (Gradiente Horizontal)
 * '3' - Ver Bordes Sobel Y (Gradiente Vertical)
 * '4' - Ver Magnitud del Gradiente (Bordes Totales)
 * '5' - Ver Efecto Artístico "Neon Sketch"
 * '+' - Aumentar Umbral de bordes
 * '-' - Disminuir Umbral de bordes
 */

PImage imgOriginal;
PImage imgSobelX;
PImage imgSobelY;
PImage imgMagnitude;
PImage imgArtistic;

// Kernels de Sobel de 3x3
float[][] kernelX = {
  { -1,  0,  1 },
  { -2,  0,  2 },
  { -1,  0,  1 }
};

float[][] kernelY = {
  { -1, -2, -1 },
  {  0,  0,  0 },
  {  1,  2,  1 }
};

int displayMode = 5; // Empezar en el modo artístico por defecto
float edgeThreshold = 60.0; // Umbral de borde ajustable por teclado

void setup() {
  size(1024, 512); // Ventana para mostrar Comparación (Original + Procesada)
  
  // Cargar imagen de prueba desde la carpeta media común
  // Usamos ruta relativa hacia la carpeta de recursos de la semana_10
  String imagePath = "../../media/natural.png";
  imgOriginal = loadImage(imagePath);
  
  if (imgOriginal == null) {
    println("Error: No se pudo cargar 'natural.png'. Creando imagen sintética de prueba...");
    // Fallback: Generar un patrón geométrico dinámico si la imagen no se encuentra
    imgOriginal = createImage(512, 512, RGB);
    imgOriginal.loadPixels();
    for (int y = 0; y < imgOriginal.height; y++) {
      for (int x = 0; x < imgOriginal.width; x++) {
        float r = 127 + 127 * sin(x * 0.05) * cos(y * 0.05);
        float g = 127 + 127 * sin((x+y)*0.02);
        float b = 200 - (x+y)*0.1;
        imgOriginal.pixels[y * imgOriginal.width + x] = color(r, g, b);
      }
    }
    imgOriginal.updatePixels();
  } else {
    // Redimensionar para un display perfecto de 512x512
    imgOriginal.resize(512, 512);
  }
  
  println("Imagen cargada con éxito: " + imgOriginal.width + "x" + imgOriginal.height);
  
  // Reservar memoria para las imágenes de salida
  imgSobelX = createImage(512, 512, GRAY);
  imgSobelY = createImage(512, 512, GRAY);
  imgMagnitude = createImage(512, 512, GRAY);
  imgArtistic = createImage(512, 512, RGB);
  
  // Ejecutar el procesamiento manual de convolución
  applyManualSobel();
  applyArtisticEffect();
}

void draw() {
  background(20);
  
  // Dibujar panel izquierdo: Siempre la imagen Original
  image(imgOriginal, 0, 0);
  fill(255);
  textSize(16);
  text("Imagen Original", 20, 30);
  
  // Dibujar panel derecho según el modo seleccionado
  PImage rightPanel = imgOriginal;
  String titleText = "Original";
  
  if (displayMode == 1) {
    rightPanel = imgOriginal;
    titleText = "Modo 1: Original";
  } else if (displayMode == 2) {
    rightPanel = imgSobelX;
    titleText = "Modo 2: Gradiente Sobel X (Horizontal)";
  } else if (displayMode == 3) {
    rightPanel = imgSobelY;
    titleText = "Modo 3: Gradiente Sobel Y (Vertical)";
  } else if (displayMode == 4) {
    rightPanel = imgMagnitude;
    titleText = "Modo 4: Magnitud de Gradiente (Sobel) - Umbral: " + round(edgeThreshold);
  } else if (displayMode == 5) {
    rightPanel = imgArtistic;
    titleText = "Modo 5: Efecto Artístico 'Neon Glow' (Fusión)";
  }
  
  image(rightPanel, 512, 0);
  
  // Dibujar títulos e info en la interfaz
  fill(0, 180, 255);
  rect(512, 0, 512, 45);
  fill(255);
  textSize(15);
  text(titleText, 532, 28);
  
  // Banner inferior instructivo
  fill(30);
  rect(0, 480, 1024, 32);
  fill(200);
  textSize(11);
  text("Controles: [1-5] Cambiar Modo | [+/-] Ajustar Umbral: " + round(edgeThreshold) + " | Convoluciones Sobel calculadas píxel a píxel", 20, 500);
}

/**
 * Aplica convolución manual sobre la imagen original usando los kernels de Sobel.
 */
void applyManualSobel() {
  imgOriginal.loadPixels();
  imgSobelX.loadPixels();
  imgSobelY.loadPixels();
  imgMagnitude.loadPixels();
  
  int w = imgOriginal.width;
  int h = imgOriginal.height;
  
  // Iterar sobre cada píxel interno (evitando los bordes externos de 1px)
  for (int y = 1; y < h - 1; y++) {
    for (int x = 1; x < w - 1; x++) {
      
      float sumX = 0.0;
      float sumY = 0.0;
      
      // Aplicar vecindad 3x3
      for (int ky = -1; ky <= 1; ky++) {
        for (int kx = -1; kx <= 1; kx++) {
          // Obtener color del píxel vecino
          int pixelColor = imgOriginal.pixels[(y + ky) * w + (x + kx)];
          // Convertir a luminosidad (escala de grises)
          float val = (red(pixelColor) + green(pixelColor) + blue(pixelColor)) / 3.0;
          
          sumX += val * kernelX[ky + 1][kx + 1];
          sumY += val * kernelY[ky + 1][kx + 1];
        }
      }
      
      // Guardar resultados parciales (valor absoluto para visualización limpia)
      float valX = abs(sumX);
      float valY = abs(sumY);
      float valMag = sqrt(sumX*sumX + sumY*sumY);
      
      // Escribir en imágenes resultantes
      imgSobelX.pixels[y * w + x] = color(constrain(valX, 0, 255));
      imgSobelY.pixels[y * w + x] = color(constrain(valY, 0, 255));
      
      // Umbralizado binario sobre la magnitud
      float binaryMag = (valMag > edgeThreshold) ? 255 : 0;
      imgMagnitude.pixels[y * w + x] = color(binaryMag);
    }
  }
  
  // Actualizar píxeles de las imágenes creadas
  imgSobelX.updatePixels();
  imgSobelY.updatePixels();
  imgMagnitude.updatePixels();
}

/**
 * Genera un efecto de fusión artística que resalta los bordes detectados en estilo Neon
 * sobrepuesto a la imagen de fondo oscurecida.
 */
void applyArtisticEffect() {
  imgOriginal.loadPixels();
  imgMagnitude.loadPixels();
  imgArtistic.loadPixels();
  
  int totalPixels = imgOriginal.width * imgOriginal.height;
  
  for (int i = 0; i < totalPixels; i++) {
    int origCol = imgOriginal.pixels[i];
    float edgeVal = red(imgMagnitude.pixels[i]); // Borde binario (0 o 255)
    
    if (edgeVal > 128) {
      // Es un píxel de borde: Ponerle un color Neón eléctrico (Cyan/Fucsia brillante)
      // Usamos una interpolación basada en la posición horizontal para crear un degradado neón
      float ratio = (float)(i % imgOriginal.width) / imgOriginal.width;
      float r = lerp(0, 255, ratio);
      float g = lerp(255, 0, ratio);
      float b = 255;
      imgArtistic.pixels[i] = color(r, g, b);
    } else {
      // Es fondo: Mostrar la imagen original oscurecida a un 25% para contraste dramático
      float r = red(origCol) * 0.25;
      float g = green(origCol) * 0.25;
      float b = blue(origCol) * 0.25;
      imgArtistic.pixels[i] = color(r, g, b);
    }
  }
  
  imgArtistic.updatePixels();
}

void keyPressed() {
  if (key >= '1' && key <= '5') {
    displayMode = int(str(key));
  }
  
  if (key == '+' || key == '=') {
    edgeThreshold = constrain(edgeThreshold + 5.0, 5.0, 200.0);
    applyManualSobel();
    applyArtisticEffect();
  }
  
  if (key == '-' || key == '_') {
    edgeThreshold = constrain(edgeThreshold - 5.0, 5.0, 200.0);
    applyManualSobel();
    applyArtisticEffect();
  }
}
