import { useState, useEffect } from "react";

interface HudOverlayProps {
  particleCount: number;
  explosionCount: number;
  isHovered: boolean;
}

/**
 * HudOverlay — Capa superpuesta de UI estilo Glassmorphism con información de la escena,
 * mostrando estadísticas en tiempo real y pistas de interacción.
 */
export default function HudOverlay({
  particleCount,
  explosionCount,
}: HudOverlayProps) {
  const [fps, setFps] = useState(60);

  useEffect(() => {
    let frames = 0;
    let lastTime = performance.now();
    const interval = setInterval(() => {
      const now = performance.now();
      const delta = now - lastTime;
      setFps(Math.round((frames * 1000) / delta));
      frames = 0;
      lastTime = now;
    }, 1000);

    const tick = () => {
      frames++;
      requestAnimationFrame(tick);
    };
    const raf = requestAnimationFrame(tick);

    return () => {
      clearInterval(interval);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className="hud-overlay">
      {/* Título */}
      <div className="hud-title">
        <h1>Energy Sphere</h1>
        <p>Texturizado Dinámico · Shaders · Partículas</p>
      </div>

      {/* Panel izquierdo: Estadísticas de la escena */}
      <div className="hud-panel hud-panel-left">
        <div className="panel-label">Escena</div>
        <div className="panel-row">
          <span>Partículas</span>
          <span className="val-cyan">{particleCount.toLocaleString()}</span>
        </div>
        <div className="panel-row">
          <span>Explosiones</span>
          <span className="val-magenta">{explosionCount}</span>
        </div>
        <div className="panel-row">
          <span>FPS</span>
          <span className="val-gold">{fps}</span>
        </div>
      </div>

      {/* Panel derecho: Ayuda de controles */}
      <div className="hud-panel hud-panel-right">
        <div className="panel-label">Controles</div>
        <div className="panel-row">
          <span>Orbitar</span>
          <span>Click + Arrastrar</span>
        </div>
        <div className="panel-row">
          <span>Zoom</span>
          <span>Rueda del mouse</span>
        </div>
        <div className="panel-row">
          <span>Explosión</span>
          <span className="val-magenta">Click en esfera</span>
        </div>
      </div>

      {/* Pista inferior */}
      <div className="hud-hint">
        ✦ Haz clic en la esfera para detonar una explosión ✦
      </div>
    </div>
  );
}
