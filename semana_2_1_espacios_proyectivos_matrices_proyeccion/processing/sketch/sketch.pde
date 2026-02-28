boolean usarPerspectiva = true;
float angulo = 0;

void setup() {
  size(800, 600, P3D);
}

void draw() {
  background(30);
  
  if (usarPerspectiva) {
    float fov = PI/3.0;
    float aspect = float(width)/float(height);
    perspective(fov, aspect, 1, 1000);
  } else {
    ortho(-width/2, width/2, -height/2, height/2, 1, 1000);
  }

  lights();
  
  translate(width/2, height/2);
  rotateY(angulo);
  angulo += 0.01;

  // Cubo cercano
  pushMatrix();
  translate(-150, 0, -100);
  fill(255, 0, 0);
  box(80);
  popMatrix();

  // Cubo medio
  pushMatrix();
  translate(0, 0, -300);
  fill(0, 255, 0);
  box(80);
  popMatrix();

  // Cubo lejano
  pushMatrix();
  translate(150, 0, -500);
  fill(0, 0, 255);
  box(80);
  popMatrix();
}

void keyPressed() {
  if (key == ' ') {
    usarPerspectiva = !usarPerspectiva;
  }
}
