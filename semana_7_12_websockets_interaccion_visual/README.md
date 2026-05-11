# Taller Websockets Interaccion Visual

**Nombre de los estudiantes:**  
Victor Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

**Fecha de entrega:**  
24/04/2026

## Descripcion breve

En esta actividad se implemento comunicacion en tiempo real con **WebSockets** entre un servidor Python y un cliente Three.js (React Three Fiber).  
El servidor emite datos JSON cada 0.5 segundos con posicion (`x`, `y`) y color, y el cliente actualiza una esfera 3D en vivo.

> Nota: la implementacion en Unity no se incluye porque en la guia era opcional.

## Implementaciones

### Python (servidor WebSocket)

Archivo principal: `python/server.py`

1. Escucha conexiones en `ws://localhost:8765`.
2. Genera datos aleatorios para `x`, `y` y `color`.
3. Envia mensajes JSON de forma continua cada 0.5 segundos.

### Three.js (cliente visual en tiempo real)

Archivo principal: `threejs/src/App.tsx`

1. Se conecta al servidor WebSocket.
2. Valida y parsea cada mensaje recibido.
3. Actualiza posicion y color del objeto 3D en tiempo real.

## Resultados visuales

<!-- Placeholders minimos requeridos: 2 evidencias por implementacion realizada -->

### Evidencias Python

![python-evidencia-1](media/python_evidencia_1.gif)
![python-evidencia-2](media/python_evidencia_2.png)

### Evidencias Three.js

![threejs-evidencia-1](media/threejs_evidencia_1.gif)
![threejs-evidencia-2](media/threejs_evidencia_2.png)

## Codigo relevante

Servidor WebSocket (Python):

```python
async def handler(websocket):
    while True:
        payload = {
            "x": random.uniform(-5.0, 5.0),
            "y": random.uniform(-5.0, 5.0),
            "color": random.choice(["red", "green", "blue"]),
        }
        await websocket.send(json.dumps(payload))
        await asyncio.sleep(0.5)
```

Cliente WebSocket + actualizacion visual (React Three Fiber):

```tsx
socket.onmessage = (event) => {
	const payload = parsePayload(event.data);
	if (!payload) return;
	setTargetPosition(new THREE.Vector3(payload.x, payload.y, 0));
	setObjectColor(COLOR_MAP[payload.color] ?? FALLBACK_COLOR);
};

useFrame((_, delta) => {
	meshRef.current?.position.lerp(targetRef.current, Math.min(1, delta * 4.5));
});
```

Ejecucion del proyecto (usar 2 terminales):

```bash
# Terminal 1: servidor Python
cd semana_7_12_websockets_interaccion_visual/python
pip install -r requirements.txt
python server.py --host localhost --port 8765 --interval 0.5
```

```bash
# Terminal 2: cliente Three.js
cd semana_7_12_websockets_interaccion_visual/threejs
npm install
npm run dev
```

## Prompts utilizados

1. "Como valido en TypeScript que un mensaje `socket.onmessage` tenga exactamente `x`, `y` y `color` antes de actualizar la escena de React Three Fiber?"
2. "En un servidor Python con `websockets`, cual es la forma mas limpia de parametrizar host, puerto e intervalo de envio por linea de comandos?"

## Aprendizajes y dificultades

Se reforzo la integracion de datos en tiempo real con visualizacion 3D y la separacion entre logica de red y render.  
La principal dificultad fue mantener movimiento fluido con datos variables; se resolvio con interpolacion (`lerp`) por frame.

## Estructura del proyecto

```text
semana_7_12_websockets_interaccion_visual/
├── python/
│   ├── server.py
│   └── requirements.txt
├── unity/
├── threejs/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── media/
├── README.md
└── semana_07_12_websockets_interaccion_visual.md
```
