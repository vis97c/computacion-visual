/**
 * HudOverlay — interfaz superpuesta con información del brazo robótico,
 * controles de modo y visualización de ángulos articulares.
 */
export default function HudOverlay({
	angles,
	endPos,
	autoAnimate,
	onToggleMode,
}: {
	angles: { hombroY: number; hombroZ: number; codo: number };
	endPos: { x: number; y: number; z: number };
	autoAnimate: boolean;
	onToggleMode: () => void;
}) {
	const toDeg = (rad: number) => ((rad * 180) / Math.PI).toFixed(1);

	return (
		<div className="hud-overlay">
			{/* Título principal */}
			<div className="hud-title">
				<h1>Cinemática Directa</h1>
				<p>Brazo Robótico 3-DOF · Forward Kinematics</p>
			</div>

			{/* Botón de modo */}
			<div className="mode-toggle">
				<button
					className={autoAnimate ? "active-auto" : "active-manual"}
					onClick={onToggleMode}
				>
					{autoAnimate ? "⟳ Auto" : "✦ Manual"}
				</button>
			</div>

			{/* Panel de ángulos articulares */}
			<div className="hud-panel hud-panel-bottom-left">
				<div className="panel-label">Ángulos Articulares</div>
				<div className="panel-row">
					<span>θ₁ Hombro Y</span>
					<span className="val-cyan">{toDeg(angles.hombroY)}°</span>
				</div>
				<div className="panel-row">
					<span>θ₂ Hombro Z</span>
					<span className="val-blue">{toDeg(angles.hombroZ)}°</span>
				</div>
				<div className="panel-row">
					<span>θ₃ Codo Z</span>
					<span className="val-orange">{toDeg(angles.codo)}°</span>
				</div>
			</div>

			{/* Panel de posición del efector final */}
			<div className="hud-panel hud-panel-bottom-right">
				<div className="panel-label">Efector Final</div>
				<div className="panel-row">
					<span>X</span>
					<span className="val-cyan">{endPos.x.toFixed(2)}</span>
				</div>
				<div className="panel-row">
					<span>Y</span>
					<span className="val-blue">{endPos.y.toFixed(2)}</span>
				</div>
				<div className="panel-row">
					<span>Z</span>
					<span className="val-orange">{endPos.z.toFixed(2)}</span>
				</div>
			</div>

			{/* Hint */}
			<div className="hud-hint">
				{autoAnimate
					? "Modo automático · Presiona el botón para control manual con Leva"
					: "Usa los sliders de Leva para ajustar cada articulación"}
			</div>
		</div>
	);
}
