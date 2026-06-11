import React, { useState, useEffect, useRef } from "react";
import {
	Upload,
	Activity,
	Sparkles,
	RefreshCw,
	FileImage,
	Grid,
	AlertCircle,
	CheckCircle2,
	BarChart3,
	Trash2,
	FileSpreadsheet,
	Hourglass,
} from "lucide-react";
import "./App.css";

const API_BASE_URL = "http://localhost:5000";

function App() {
	const [activeTab, setActiveTab] = useState("dashboard");

	// Predict States for Batch Upload
	const [batchResults, setBatchResults] = useState([]);
	const [currentFileIndex, setCurrentFileIndex] = useState(null);
	const [isUploading, setIsUploading] = useState(false);
	const [selectedParticle, setSelectedParticle] = useState(null);
	const [error, setError] = useState(null);

	// Model States
	const [selectedModel, setSelectedModel] = useState("ceroplastic");
	const [metricsModel, setMetricsModel] = useState("ceroplastic");
	const [modelInfo, setModelInfo] = useState(null);
	const [isTraining, setIsTraining] = useState(false);

	const fileInputRef = useRef(null);
	const viewerContainerRef = useRef(null);
	const processSessionIdRef = useRef(0);

	// Interactive Bounding Box Editing & Custom Drawing States
	const [imageDimensions, setImageDimensions] = useState({
		displayWidth: 0,
		displayHeight: 0,
		naturalWidth: 1,
		naturalHeight: 1,
	});
	const [selectedParticleForEdit, setSelectedParticleForEdit] = useState(null);

	// Drawing box states
	const [isDrawing, setIsDrawing] = useState(false);
	const [drawStart, setDrawStart] = useState({ x: 0, y: 0 });
	const [drawCurrent, setDrawCurrent] = useState({ x: 0, y: 0 });

	// Resize listener to recalculate scale factors
	useEffect(() => {
		const handleResize = () => {
			const imgEl = document.querySelector(".viewer-image");

			if (imgEl) {
				setImageDimensions({
					displayWidth: imgEl.clientWidth,
					displayHeight: imgEl.clientHeight,
					naturalWidth: imgEl.naturalWidth,
					naturalHeight: imgEl.naturalHeight,
				});
			}
		};

		window.addEventListener("resize", handleResize);

		return () => window.removeEventListener("resize", handleResize);
	}, [currentFileIndex, batchResults]);

	// Trigger resize calculation when activeTab or currentFileIndex changes
	useEffect(() => {
		setTimeout(() => {
			const imgEl = document.querySelector(".viewer-image");

			if (imgEl) {
				setImageDimensions({
					displayWidth: imgEl.clientWidth,
					displayHeight: imgEl.clientHeight,
					naturalWidth: imgEl.naturalWidth,
					naturalHeight: imgEl.naturalHeight,
				});
			}
		}, 100);
	}, [currentFileIndex, activeTab]);

	const updateCurrentItemParticles = (newParticles) => {
		setBatchResults((prev) => {
			return prev.map((item, idx) => {
				if (idx !== currentFileIndex) return item;

				const newCounts = {
					Pellet: 0,
					Fibra: 0,
					Fragmento: 0,
					Pelicula: 0,
					Espuma: 0,
					"No Microplastico": 0,
				};

				newParticles.forEach((p) => {
					if (p.class in newCounts) {
						newCounts[p.class]++;
					}
				});

				const totalMicroplastics = Object.entries(newCounts)
					.filter(([cls]) => cls !== "No Microplastico")
					.reduce((sum, [, count]) => sum + count, 0);

				return {
					...item,
					hasUnsavedCorrections: true,
					result: {
						...item.result,
						particles: newParticles,
						counts: newCounts,
						total_detected: newParticles.length,
						total_microplastics: totalMicroplastics,
					},
				};
			});
		});
	};

	const handleImageLoad = (e) => {
		const imgEl = e.target;

		setImageDimensions({
			displayWidth: imgEl.clientWidth,
			displayHeight: imgEl.clientHeight,
			naturalWidth: imgEl.naturalWidth,
			naturalHeight: imgEl.naturalHeight,
		});
	};

	const handleMouseDown = (e) => {
		if (
			e.target.tagName === "rect" ||
			e.target.tagName === "text" ||
			e.target.closest(".edit-popover")
		) {
			return;
		}

		const currentItem = currentFileIndex !== null ? batchResults[currentFileIndex] : null;

		if (!currentItem || !currentItem.isDone || !currentItem.result) return;

		const rect = e.currentTarget.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;

		setIsDrawing(true);
		setDrawStart({ x, y });
		setDrawCurrent({ x, y });
		setSelectedParticleForEdit(null); // Close popover
	};

	const handleMouseMove = (e) => {
		if (!isDrawing) return;

		const rect = e.currentTarget.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;

		const clampedX = Math.max(0, Math.min(x, rect.width));
		const clampedY = Math.max(0, Math.min(y, rect.height));

		setDrawCurrent({ x: clampedX, y: clampedY });
	};

	const handleMouseUp = () => {
		if (!isDrawing) return;

		setIsDrawing(false);

		const x1 = Math.min(drawStart.x, drawCurrent.x);
		const y1 = Math.min(drawStart.y, drawCurrent.y);
		const x2 = Math.max(drawStart.x, drawCurrent.x);
		const y2 = Math.max(drawStart.y, drawCurrent.y);

		const w_disp = x2 - x1;
		const h_disp = y2 - y1;

		if (w_disp < 8 || h_disp < 8) return;

		const scaleX = imageDimensions.displayWidth / imageDimensions.naturalWidth;
		const scaleY = imageDimensions.displayHeight / imageDimensions.naturalHeight;

		const currentItem = batchResults[currentFileIndex];
		const newId =
			currentItem.result.particles.length > 0
				? Math.max(...currentItem.result.particles.map((p) => p.id)) + 1
				: 0;

		const newParticle = {
			id: newId,
			x: Math.round(x1 / scaleX),
			y: Math.round(y1 / scaleY),
			w: Math.round(w_disp / scaleX),
			h: Math.round(h_disp / scaleY),
			area: (w_disp / scaleX) * (h_disp / scaleY),
			circularity: 1.0,
			class: "Fragmento",
			isNew: true,
		};

		updateCurrentItemParticles([...currentItem.result.particles, newParticle]);
		setSelectedParticleForEdit(newParticle);
	};

	const handleSaveCorrections = async () => {
		const currentItem = batchResults[currentFileIndex];

		if (!currentItem || !currentItem.result) return;

		const payload = {
			filename: currentItem.fileName,
			particles: currentItem.result.particles.map((p) => ({
				x: p.x,
				y: p.y,
				w: p.w,
				h: p.h,
				class: p.class,
			})),
		};

		try {
			const res = await fetch(`${API_BASE_URL}/api/correct`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(payload),
			});

			if (!res.ok) {
				throw new Error("Failed to save corrections");
			}

			setBatchResults((prev) =>
				prev.map((item, idx) =>
					idx === currentFileIndex ? { ...item, hasUnsavedCorrections: false } : item
				)
			);

			alert("¡Correcciones guardadas con éxito!");
		} catch (err) {
			alert(`Error al guardar correcciones: ${err.message}`);
		}
	};

	const handleChangeParticleClass = (particleId, newClass) => {
		const currentItem = batchResults[currentFileIndex];

		if (!currentItem || !currentItem.result) return;

		const updatedParticles = currentItem.result.particles.map((p) =>
			p.id === particleId ? { ...p, class: newClass } : p
		);

		updateCurrentItemParticles(updatedParticles);

		if (newClass === "No Microplastico") {
			setSelectedParticleForEdit(null);
		} else {
			setSelectedParticleForEdit((prev) =>
				prev && prev.id === particleId ? { ...prev, class: newClass } : prev
			);
		}
	};

	const handleDeleteParticle = (particleId) => {
		const currentItem = batchResults[currentFileIndex];

		if (!currentItem || !currentItem.result) return;

		const updatedParticles = currentItem.result.particles.filter((p) => p.id !== particleId);

		updateCurrentItemParticles(updatedParticles);
		setSelectedParticleForEdit(null);
	};

	// Fetch model info on load or model change
	useEffect(() => {
		const fetchModelInfo = async (model = metricsModel) => {
			try {
				const res = await fetch(`${API_BASE_URL}/api/model-info?model=${model}`);

				if (res.ok) {
					const data = await res.json();

					setModelInfo(data);
				}
			} catch (err) {
				console.error("Error fetching model info:", err);
			}
		};

		fetchModelInfo(metricsModel);
	}, [metricsModel]);

	const handleFilesSelected = (selectedFiles) => {
		if (!selectedFiles || selectedFiles.length === 0) return;

		setError(null);
		setSelectedParticle(null);

		const newResults = Array.from(selectedFiles).map((file) => {
			const filename = file.name.toLowerCase();
			const isTiffFile = filename.endsWith(".tif") || filename.endsWith(".tiff");

			return {
				file,
				fileName: file.name,
				isTiff: isTiffFile,
				previewUrl: isTiffFile ? null : URL.createObjectURL(file),
				isProcessing: false,
				isDone: false,
				error: null,
				result: null,
			};
		});

		setBatchResults((prev) => {
			const updated = [...prev, ...newResults];

			if (currentFileIndex === null && updated.length > 0) {
				setCurrentFileIndex(0);
			}

			return updated;
		});
	};

	const handleFileChange = (e) => {
		handleFilesSelected(e.target.files);
	};

	const handleDragOver = (e) => {
		e.preventDefault();
	};

	const handleDrop = (e) => {
		e.preventDefault();
		handleFilesSelected(e.dataTransfer.files);
	};

	const handleProcessBatch = async (forcedList = null, forcedModel = null) => {
		const isForced = Array.isArray(forcedList);
		const listToProcess = isForced ? forcedList : batchResults;
		const modelToUse = typeof forcedModel === "string" ? forcedModel : selectedModel;

		if (listToProcess.length === 0) return;

		processSessionIdRef.current += 1;

		const sessionId = processSessionIdRef.current;

		setIsUploading(true);
		setError(null);

		// Process each file sequentially
		for (let i = 0; i < listToProcess.length; i++) {
			if (processSessionIdRef.current !== sessionId) return;

			const item = listToProcess[i];

			if (item.isDone && !isForced) continue; // Skip already processed files unless forced

			// Mark this file as processing and select it to show in viewer
			setBatchResults((prev) =>
				prev.map((r, idx) => (idx === i ? { ...r, isProcessing: true, error: null } : r))
			);
			setCurrentFileIndex(i);

			const formData = new FormData();

			formData.append("file", item.file);

			try {
				const res = await fetch(`${API_BASE_URL}/api/predict?model=${modelToUse}`, {
					method: "POST",
					body: formData,
				});

				if (processSessionIdRef.current !== sessionId) return;

				if (!res.ok) {
					const errData = await res.json();

					throw new Error(errData.error || "Failed to analyze image");
				}

				const data = await res.json();

				if (processSessionIdRef.current !== sessionId) return;

				setBatchResults((prev) =>
					prev.map((r, idx) =>
						idx === i ? { ...r, isProcessing: false, isDone: true, result: data } : r
					)
				);
			} catch (err) {
				console.error(`Error processing file ${item.fileName}:`, err);

				if (processSessionIdRef.current !== sessionId) return;

				setBatchResults((prev) =>
					prev.map((r, idx) =>
						idx === i
							? { ...r, isProcessing: false, isDone: false, error: err.message }
							: r
					)
				);
			}
		}

		if (processSessionIdRef.current === sessionId) {
			setIsUploading(false);
		}
	};

	// Auto-reprocess batch when model changes
	useEffect(() => {
		if (batchResults.length === 0) return;

		// Check if the batch has already been processed or is processing or has errors
		const hasAttempted = batchResults.some(
			(item) => item.isDone || item.isProcessing || item.error !== null
		);

		if (hasAttempted) {
			// Reset all items to unprocessed state
			const resetList = batchResults.map((item) => ({
				...item,
				isProcessing: false,
				isDone: false,
				error: null,
				result: null,
			}));

			setBatchResults(resetList);
			handleProcessBatch(resetList, selectedModel);
		}
	}, [selectedModel]);

	const handleExportCSV = () => {
		const processedItems = batchResults.filter((r) => r.isDone && r.result);

		if (processedItems.length === 0) return;

		const headers = [
			"Imagen",
			"Contiene Microplastico",
			"Tipo Dominante",
			"Total Particulas",
			"Pellets",
			"Fibras",
			"Fragmentos",
			"Peliculas",
			"Espumas",
			"No-Microplasticos",
		];

		const rows = processedItems.map((r) => {
			const res = r.result;
			const hasMicroplastic = res.total_microplastics > 0 ? "Si" : "No";

			// Determine dominant type
			let dominantType = "No Microplastico";
			let maxCount = 0;

			Object.entries(res.counts).forEach(([cls, count]) => {
				if (cls !== "No Microplastico" && count > maxCount) {
					maxCount = count;
					dominantType = cls;
				}
			});

			if (res.total_microplastics === 0) {
				dominantType = "No Microplastico";
			}

			return [
				r.fileName,
				hasMicroplastic,
				dominantType,
				res.total_detected,
				res.counts.Pellet,
				res.counts.Fibra,
				res.counts.Fragmento,
				res.counts.Pelicula,
				res.counts.Espuma,
				res.counts["No Microplastico"],
			];
		});

		// Construct CSV String
		const csvContent = [
			headers.join(","),
			...rows.map((row) =>
				row.map((val) => `"${String(val).replace(/"/g, '""')}"`).join(",")
			),
		].join("\n");

		// Create download link
		const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
		const url = URL.createObjectURL(blob);
		const link = document.createElement("a");

		link.setAttribute("href", url);
		link.setAttribute(
			"download",
			`microplasticos_analisis_${new Date().toISOString().slice(0, 10)}.csv`
		);
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	};

	const handleClearBatch = () => {
		processSessionIdRef.current += 1;
		setBatchResults([]);
		setCurrentFileIndex(null);
		setSelectedParticle(null);
		setError(null);
		setIsUploading(false);
	};

	const handleTrainModel = async () => {
		setIsTraining(true);
		setError(null);

		try {
			const res = await fetch(`${API_BASE_URL}/api/train?model=${metricsModel}`, {
				method: "POST",
			});

			if (!res.ok) {
				const errData = await res.json();

				throw new Error(errData.error || "Training failed");
			}

			const data = await res.json();

			setModelInfo(data);
			alert("Model trained successfully!");
		} catch (err) {
			setError(err.message);
		} finally {
			setIsTraining(false);
		}
	};

	const getClassColorCss = (cls) => {
		const colors = {
			Pellet: "var(--color-pellet)",
			Fibra: "var(--color-fibra)",
			Fragmento: "var(--color-fragmento)",
			Pelicula: "var(--color-pelicula)",
			Espuma: "var(--color-espuma)",
			"No Microplastico": "var(--color-no-plastic)",
		};

		return colors[cls] || "#ffffff";
	};

	// SVG Gauge calculations
	const radius = 50;
	const circumference = 2 * Math.PI * radius;
	const accuracyPct = modelInfo ? modelInfo.mean_accuracy * 100 : 0;
	const strokeDashoffset = circumference - (accuracyPct / 100) * circumference;

	const currentItem = currentFileIndex !== null ? batchResults[currentFileIndex] : null;
	const isBatchDone = batchResults.length > 0 && batchResults.every((r) => r.isDone);
	const processedCount = batchResults.filter((r) => r.isDone).length;

	return (
		<div className="dashboard-container">
			{/* Header */}
			<header className="app-header animate-fade">
				<div className="brand">
					<div
						className="stat-icon-wrapper"
						style={{ background: "var(--primary-glow)", color: "var(--primary)" }}
					>
						<Sparkles size={28} />
					</div>
					<div>
						<h1>Cero Plastic AI</h1>
						<p>Computación Visual para Clasificación de Microplásticos</p>
					</div>
				</div>

				{/* Tab Selection */}
				<nav className="tab-navigation">
					<button
						className={`tab-btn ${activeTab === "dashboard" ? "active" : ""}`}
						onClick={() => setActiveTab("dashboard")}
					>
						<Grid size={16} /> Dashboard
					</button>
					<button
						className={`tab-btn ${activeTab === "metrics" ? "active" : ""}`}
						onClick={() => setActiveTab("metrics")}
					>
						<Activity size={16} /> Métricas de IA
					</button>
				</nav>
			</header>

			{/* Main Content Areas */}
			<main>
				{error && (
					<div
						className="glass-panel animate-fade"
						style={{
							borderColor: "var(--color-fibra)",
							padding: "16px",
							marginBottom: "24px",
							display: "flex",
							alignItems: "center",
							gap: "12px",
							background: "hsla(354, 70%, 54%, 0.05)",
						}}
					>
						<AlertCircle size={20} style={{ color: "var(--color-fibra)" }} />
						<span style={{ color: "var(--text-primary)", fontSize: "0.9rem" }}>
							{error}
						</span>
					</div>
				)}

				{/* Tab 1: Dashboard */}
				{activeTab === "dashboard" && (
					<div className="panel-grid animate-fade">
						{/* Left Column: Upload and Batch File Control */}
						<div className="glass-panel panel-card">
							<h2>
								<Upload size={18} style={{ color: "var(--primary)" }} /> Lote de
								Muestras
							</h2>

							{/* Selector de Modelo en Dashboard */}
							<div
								className="model-selector-wrapper animate-fade"
								style={{
									marginBottom: "16px",
									background: "rgba(255,255,255,0.02)",
									padding: "12px",
									borderRadius: "8px",
									border: "1px solid var(--border-color)",
								}}
							>
								<label
									htmlFor="model-select"
									style={{
										fontSize: "0.8rem",
										color: "var(--text-secondary)",
										display: "block",
										marginBottom: "6px",
										fontWeight: 600,
									}}
								>
									Modelo de Clasificación:
								</label>
								<select
									id="model-select"
									value={selectedModel}
									onChange={(e) => setSelectedModel(e.target.value)}
									style={{
										width: "100%",
										padding: "8px 12px",
										borderRadius: "6px",
										background: "var(--bg-card)",
										color: "var(--text-primary)",
										border: "1px solid var(--border-color)",
										fontSize: "0.85rem",
										cursor: "pointer",
										outline: "none",
										fontFamily: "inherit",
									}}
								>
									<option value="ceroplastic">
										Original (Ceroplastic Consenso)
									</option>
									<option value="valerio">
										Valerio Dataset (Mejores Labels)
									</option>
									<option value="ceroplastic_valerio">
										Fusion Model (CeroPlastic + Valerio)
									</option>
								</select>
							</div>

							{batchResults.length === 0 ? (
								<div
									className="upload-zone"
									onDragOver={handleDragOver}
									onDrop={handleDrop}
									onClick={() => fileInputRef.current.click()}
								>
									<input
										type="file"
										ref={fileInputRef}
										style={{ display: "none" }}
										onChange={handleFileChange}
										accept=".tif,.tiff,.png,.jpg,.jpeg"
										multiple
									/>
									<div className="upload-icon">
										<FileImage size={48} />
									</div>
									<h3>Arrastra o selecciona fotos</h3>
									<p>Soporta carga múltiple: TIFF, PNG, JPG</p>
								</div>
							) : (
								<div
									style={{
										display: "flex",
										flexDirection: "column",
										gap: "16px",
									}}
								>
									{/* File List Manager */}
									<div className="file-list">
										{batchResults.map((item, idx) => (
											<div
												key={idx}
												className={`file-item ${currentFileIndex === idx ? "active" : ""}`}
												onClick={() => {
													if (!isUploading) {
														setCurrentFileIndex(idx);
														setSelectedParticle(null);
													}
												}}
											>
												<div className="file-item-info">
													<FileImage
														size={14}
														style={{ color: "var(--text-secondary)" }}
													/>
													<span
														className="file-item-name"
														title={item.fileName}
													>
														{item.fileName}
													</span>
												</div>
												<div className="file-item-status">
													{item.isProcessing && (
														<RefreshCw size={12} className="spinner" />
													)}
													{item.isDone && (
														<CheckCircle2
															size={12}
															style={{ color: "var(--color-pellet)" }}
														/>
													)}
													{item.error && (
														<AlertCircle
															size={12}
															style={{ color: "var(--color-fibra)" }}
														/>
													)}
													{!item.isDone &&
														!item.isProcessing &&
														!item.error && (
															<Hourglass
																size={12}
																style={{
																	color: "var(--text-muted)",
																}}
															/>
														)}
												</div>
											</div>
										))}
									</div>

									{/* Actions for Batch */}
									<div
										style={{
											display: "flex",
											flexDirection: "column",
											gap: "10px",
										}}
									>
										<button
											className="btn-primary"
											onClick={handleProcessBatch}
											disabled={isUploading || isBatchDone}
										>
											{isUploading ? (
												<>
													<RefreshCw size={16} className="spinner" />{" "}
													Procesando Lote ({processedCount}/
													{batchResults.length})...
												</>
											) : (
												<>
													<Sparkles size={16} /> Procesar Lote
												</>
											)}
										</button>

										<div className="btn-group">
											<button
												className="btn-outline"
												onClick={handleExportCSV}
												disabled={processedCount === 0 || isUploading}
											>
												<FileSpreadsheet size={14} /> Exportar CSV
											</button>
											<button
												className="btn-outline"
												onClick={handleClearBatch}
												disabled={isUploading}
												style={{ color: "var(--color-fibra)" }}
											>
												<Trash2 size={14} /> Limpiar Lote
											</button>
										</div>
									</div>
								</div>
							)}

							{/* Selected file results summary */}
							{currentItem && currentItem.isDone && currentItem.result && (
								<div
									className="animate-fade"
									style={{
										display: "flex",
										flexDirection: "column",
										gap: "16px",
										marginTop: "10px",
										borderTop: "1px solid var(--border-color)",
										paddingTop: "16px",
									}}
								>
									<div>
										<h3
											style={{
												fontSize: "0.9rem",
												marginBottom: "12px",
												color: "var(--text-secondary)",
											}}
										>
											Resumen del Archivo Seleccionado
										</h3>
										<div
											style={{
												display: "flex",
												flexDirection: "column",
												gap: "10px",
											}}
										>
											<div
												className="progress-header"
												style={{ fontSize: "0.85rem" }}
											>
												<span>Partículas Detectadas:</span>
												<strong style={{ color: "var(--text-primary)" }}>
													{currentItem.result.total_detected}
												</strong>
											</div>
											<div
												className="progress-header"
												style={{ fontSize: "0.85rem" }}
											>
												<span>Microplásticos Confirmados:</span>
												<strong style={{ color: "var(--primary)" }}>
													{currentItem.result.total_microplastics}
												</strong>
											</div>
										</div>
									</div>

									{/* Class distribution for current image */}
									<div>
										<h4
											style={{
												fontSize: "0.8rem",
												color: "var(--text-muted)",
												marginBottom: "8px",
											}}
										>
											Distribución de Clases
										</h4>
										<div
											style={{
												display: "flex",
												flexDirection: "column",
												gap: "8px",
											}}
										>
											{Object.entries(currentItem.result.counts).map(
												([cls, val]) => (
													<div key={cls} className="custom-progress-bar">
														<div className="progress-header">
															<span>{cls}</span>
															<strong>{val}</strong>
														</div>
														<div className="progress-track">
															<div
																className="progress-bar-fill"
																style={{
																	width: `${currentItem.result.total_detected > 0 ? (val / currentItem.result.total_detected) * 100 : 0}%`,
																	backgroundColor:
																		getClassColorCss(cls),
																}}
															/>
														</div>
													</div>
												)
											)}
										</div>
									</div>
								</div>
							)}
						</div>

						{/* Right Column: Interactive Image Viewer & Details */}
						<div className="glass-panel viewer-card">
							<div className="viewer-header">
								<h2>Visor de Detección por IA</h2>
								<div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
									{currentItem && currentItem.hasUnsavedCorrections && (
										<button
											className="btn-primary animate-fade"
											onClick={handleSaveCorrections}
											style={{
												background: "var(--color-espuma)",
												color: "#000",
												padding: "6px 12px",
												fontSize: "0.8rem",
												height: "auto",
												width: "auto",
												boxShadow: "none",
												fontWeight: "bold",
											}}
										>
											Guardar Correcciones
										</button>
									)}
									{currentItem && (
										<span className="badge badge-No-Microplastico">
											{currentItem.fileName}
										</span>
									)}
								</div>
							</div>

							<div className="viewer-content">
								{!currentItem ? (
									<div
										style={{ color: "var(--text-muted)", textAlign: "center" }}
									>
										<AlertCircle
											size={40}
											style={{ margin: "0 auto 12px", opacity: 0.4 }}
										/>
										<p>
											Carga fotos del microscopio para iniciar el análisis en
											lote
										</p>
									</div>
								) : currentItem.isProcessing ? (
									<div
										style={{
											display: "flex",
											flexDirection: "column",
											alignItems: "center",
											gap: "16px",
										}}
									>
										<RefreshCw
											size={48}
											className="spinner"
											style={{ color: "var(--primary)" }}
										/>
										<p style={{ color: "var(--text-secondary)" }}>
											Segmentando y Clasificando Partículas...
										</p>
									</div>
								) : currentItem.error ? (
									<div
										style={{
											color: "var(--color-fibra)",
											textAlign: "center",
											padding: "20px",
										}}
									>
										<AlertCircle
											size={40}
											style={{ margin: "0 auto 12px", opacity: 0.8 }}
										/>
										<p style={{ fontWeight: 600 }}>
											Error al procesar la imagen
										</p>
										<p
											style={{
												fontSize: "0.8rem",
												marginTop: "6px",
												color: "var(--text-secondary)",
											}}
										>
											{currentItem.error}
										</p>
									</div>
								) : currentItem.result ? (
									<div
										className="interactive-viewer-container animate-fade"
										ref={viewerContainerRef}
										onMouseDown={handleMouseDown}
										onMouseMove={handleMouseMove}
										onMouseUp={handleMouseUp}
									>
										<img
											src={`data:image/jpeg;base64,${currentItem.result.original_image}`}
											className="viewer-image"
											alt="Original microscopical content"
											onLoad={handleImageLoad}
										/>

										{/* SVG Bounding Boxes Overlay */}
										<svg className="svg-box-overlay">
											{/* Bounding Boxes */}
											{imageDimensions.displayWidth > 0 &&
												currentItem.result.particles
													.filter((p) => p.class !== "No Microplastico")
													.map((p) => {
														const scaleX =
															imageDimensions.displayWidth /
															imageDimensions.naturalWidth;
														const scaleY =
															imageDimensions.displayHeight /
															imageDimensions.naturalHeight;
														const rx = p.x * scaleX;
														const ry = p.y * scaleY;
														const rw = p.w * scaleX;
														const rh = p.h * scaleY;
														const color = getClassColorCss(p.class);

														return (
															<g key={p.id}>
																<rect
																	x={rx}
																	y={ry}
																	width={rw}
																	height={rh}
																	className="svg-rect"
																	style={{
																		stroke: color,
																		strokeWidth:
																			selectedParticle?.id ===
																			p.id
																				? 3
																				: 2,
																		fill:
																			selectedParticle?.id ===
																			p.id
																				? "rgba(255,255,255,0.1)"
																				: "transparent",
																		cursor: "pointer",
																	}}
																	onClick={(e) => {
																		e.stopPropagation();
																		setSelectedParticleForEdit(
																			p
																		);
																	}}
																	onMouseEnter={() =>
																		setSelectedParticle(p)
																	}
																	onMouseLeave={() =>
																		setSelectedParticle(null)
																	}
																/>
																<text
																	x={rx}
																	y={ry - 5 > 12 ? ry - 5 : 12}
																	fill={color}
																	fontSize="11px"
																	fontWeight="bold"
																	style={{
																		pointerEvents: "none",
																		userSelect: "none",
																	}}
																>
																	{`P${p.id}: ${p.class}`}
																</text>
															</g>
														);
													})}

											{/* Drawing Preview Rectangle */}
											{isDrawing && (
												<rect
													x={Math.min(drawStart.x, drawCurrent.x)}
													y={Math.min(drawStart.y, drawCurrent.y)}
													width={Math.abs(drawStart.x - drawCurrent.x)}
													height={Math.abs(drawStart.y - drawCurrent.y)}
													style={{
														stroke: "var(--primary)",
														strokeWidth: 2,
														strokeDasharray: "4,4",
														fill: "rgba(37, 99, 235, 0.15)",
														pointerEvents: "none",
													}}
												/>
											)}
										</svg>

										{/* Edit Popover Tooltip */}
										{selectedParticleForEdit && (
											<div
												className="edit-popover animate-fade"
												style={{
													left: `${Math.max(10, Math.min(imageDimensions.displayWidth - 220, (selectedParticleForEdit.x + selectedParticleForEdit.w / 2) * (imageDimensions.displayWidth / imageDimensions.naturalWidth) - 105))}px`,
													top: `${
														(selectedParticleForEdit.y +
															selectedParticleForEdit.h) *
															(imageDimensions.displayHeight /
																imageDimensions.naturalHeight) >
														imageDimensions.displayHeight - 140
															? selectedParticleForEdit.y *
																	(imageDimensions.displayHeight /
																		imageDimensions.naturalHeight) -
																145
															: (selectedParticleForEdit.y +
																	selectedParticleForEdit.h) *
																	(imageDimensions.displayHeight /
																		imageDimensions.naturalHeight) +
																10
													}px`,
												}}
											>
												<h4>
													Editar Partícula P{selectedParticleForEdit.id}
												</h4>
												<div className="popover-grid">
													{[
														"Pellet",
														"Fibra",
														"Fragmento",
														"Pelicula",
														"Espuma",
														"No Microplastico",
													].map((cls) => (
														<button
															key={cls}
															className={`popover-btn ${selectedParticleForEdit.class === cls ? "active" : ""}`}
															onClick={() =>
																handleChangeParticleClass(
																	selectedParticleForEdit.id,
																	cls
																)
															}
														>
															{cls}
														</button>
													))}
												</div>
												<button
													className="popover-delete-btn"
													onClick={() =>
														handleDeleteParticle(
															selectedParticleForEdit.id
														)
													}
												>
													<Trash2 size={12} /> Eliminar
												</button>
											</div>
										)}
									</div>
								) : currentItem.previewUrl ? (
									<div className="image-canvas-wrapper animate-fade">
										<img
											src={currentItem.previewUrl}
											className="viewer-image"
											alt="Preview"
										/>
									</div>
								) : (
									<div className="tiff-placeholder animate-fade">
										<FileImage
											size={64}
											style={{ color: "var(--primary)", opacity: 0.6 }}
										/>
										<div style={{ textAlign: "center" }}>
											<p
												style={{
													fontWeight: 600,
													color: "var(--text-primary)",
												}}
											>
												Microscopio TIFF en Cola
											</p>
											<p style={{ fontSize: "0.8rem", marginTop: "4px" }}>
												El formato .tif no se puede previsualizar en el
												navegador nativamente.
											</p>
											<p style={{ fontSize: "0.8rem" }}>
												Haz clic en &quot;Procesar Lote&quot; para ver el
												resultado JPG.
											</p>
										</div>
									</div>
								)}
							</div>

							{/* Table of segmented elements below the image */}
							{currentItem &&
								currentItem.isDone &&
								currentItem.result &&
								currentItem.result.particles.filter(
									(p) => p.class !== "No Microplastico"
								).length > 0 && (
									<div
										style={{
											padding: "24px",
											borderTop: "1px solid var(--border-color)",
										}}
									>
										<h3
											style={{
												fontSize: "1rem",
												marginBottom: "12px",
												display: "flex",
												alignItems: "center",
												gap: "8px",
											}}
										>
											<BarChart3 size={16} /> Lista de Partículas Segmentadas
										</h3>
										<div className="table-wrapper">
											<table className="custom-table">
												<thead>
													<tr>
														<th>ID</th>
														<th>Coordenadas (x, y)</th>
														<th>Ancho x Alto</th>
														<th>Área (px)</th>
														<th>Circularidad</th>
														<th>Clase Detectada</th>
													</tr>
												</thead>
												<tbody>
													{currentItem.result.particles
														.filter(
															(p) => p.class !== "No Microplastico"
														)
														.map((p) => (
															<tr
																key={p.id}
																className={
																	selectedParticle?.id === p.id
																		? "selected"
																		: ""
																}
																onMouseEnter={() =>
																	setSelectedParticle(p)
																}
																onMouseLeave={() =>
																	setSelectedParticle(null)
																}
															>
																<td>
																	<strong>{p.id}</strong>
																</td>
																<td>
																	{p.x}, {p.y}
																</td>
																<td>
																	{p.w} x {p.h}
																</td>
																<td>{p.area.toFixed(0)}</td>
																<td>{p.circularity.toFixed(3)}</td>
																<td>
																	<span
																		className={`badge badge-${p.class.replace(" ", "-")}`}
																	>
																		{p.class}
																	</span>
																</td>
															</tr>
														))}
												</tbody>
											</table>
										</div>
									</div>
								)}
						</div>
					</div>
				)}

				{/* Tab 2: Metrics */}
				{activeTab === "metrics" && (
					<div
						className="animate-fade"
						style={{ display: "flex", flexDirection: "column", gap: "24px" }}
					>
						{/* Selector de Modelo en pestaña de Métricas */}
						<div
							className="glass-panel"
							style={{
								padding: "16px 20px",
								display: "flex",
								flexWrap: "wrap",
								alignItems: "center",
								justifyContent: "space-between",
								gap: "16px",
							}}
						>
							<div style={{ display: "flex", flexDirection: "column" }}>
								<h3
									style={{
										fontSize: "1.05rem",
										margin: 0,
										color: "var(--text-primary)",
									}}
								>
									Modelo de Métricas
								</h3>
								<p
									style={{
										fontSize: "0.75rem",
										color: "var(--text-muted)",
										margin: "4px 0 0",
									}}
								>
									Visualiza los resultados de validación cruzada y re-entrena cada
									modelo por separado.
								</p>
							</div>
							<div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
								{[
									{ key: "ceroplastic", label: "Ceroplastic (Original)" },
									{ key: "valerio", label: "Valerio Dataset" },
									{
										key: "ceroplastic_valerio",
										label: "Fusion (CeroPlastic + Valerio)",
									},
								].map((m) => (
									<button
										key={m.key}
										className={`tab-btn ${metricsModel === m.key ? "active" : ""}`}
										onClick={() => setMetricsModel(m.key)}
										style={{
											height: "34px",
											padding: "0 16px",
											fontSize: "0.8rem",
											borderRadius: "6px",
											background:
												metricsModel === m.key
													? "var(--primary)"
													: "rgba(255,255,255,0.03)",
											color:
												metricsModel === m.key
													? "#fff"
													: "var(--text-secondary)",
											border: "1px solid var(--border-color)",
											cursor: "pointer",
											fontWeight: 600,
											transition: "all 0.2s ease",
										}}
									>
										{m.label}
									</button>
								))}
							</div>
						</div>

						<div className="metrics-grid">
							{/* Circular Gauge Card */}
							<div
								className="glass-panel panel-card"
								style={{ justifyContent: "center" }}
							>
								<h2>Rendimiento Global</h2>
								<div className="gauge-wrapper">
									<svg width="120" height="120" className="gauge-svg">
										<circle
											cx="60"
											cy="60"
											r={radius}
											className="gauge-bg"
											strokeWidth="8"
										/>
										<circle
											cx="60"
											cy="60"
											r={radius}
											className="gauge-fill"
											strokeWidth="8"
											strokeDasharray={circumference}
											strokeDashoffset={strokeDashoffset}
										/>
										<text
											x="60"
											y="60"
											className="gauge-text"
											dominantBaseline="middle"
											textAnchor="middle"
										>
											{accuracyPct.toFixed(1)}%
										</text>
									</svg>
									<div style={{ textAlign: "center" }}>
										<p style={{ fontWeight: 600, fontSize: "0.9rem" }}>
											Exactitud de Validación (CV)
										</p>
										<p
											style={{
												fontSize: "0.75rem",
												color: "var(--text-muted)",
												marginTop: "4px",
												maxWidth: "240px",
											}}
										>
											Métricas estimadas sobre validación cruzada
											estratificada de 5 pliegues.
										</p>
									</div>
								</div>

								<button
									className="btn-outline"
									onClick={handleTrainModel}
									disabled={isTraining}
									style={{ marginTop: "10px" }}
								>
									{isTraining ? (
										<>
											<RefreshCw size={14} className="spinner" />{" "}
											Entrenando...
										</>
									) : (
										<>
											<RefreshCw size={14} /> Re-entrenar Modelo
										</>
									)}
								</button>
							</div>

							{/* Feature Importance Card */}
							<div className="glass-panel panel-card">
								<h2>Importancia de Descriptores de Imagen</h2>
								<p
									style={{
										fontSize: "0.8rem",
										color: "var(--text-secondary)",
										marginTop: "-10px",
										marginBottom: "10px",
									}}
								>
									Determina qué descriptores morfológicos o cromáticos extraídos
									por OpenCV influyen más en las decisiones del clasificador.
								</p>
								{modelInfo ? (
									<div className="importance-chart">
										{modelInfo.feature_importances.map((item) => (
											<div key={item.feature} className="importance-row">
												<span className="feat-name">{item.feature}</span>
												<div className="bar-wrapper">
													<div
														className="bar-fill"
														style={{
															width: `${item.importance * 100 * 5.5}%`,
														}} // Multiply to scale visually
													/>
												</div>
												<span className="feat-val">
													{(item.importance * 100).toFixed(2)}%
												</span>
											</div>
										))}
									</div>
								) : (
									<div
										style={{ textAlign: "center", color: "var(--text-muted)" }}
									>
										Cargando métricas...
									</div>
								)}
							</div>
						</div>

						{/* Confusion Matrix Card */}
						{modelInfo && (
							<div className="glass-panel panel-card">
								<h2>Matriz de Confusión del Modelo</h2>
								<p
									style={{
										fontSize: "0.8rem",
										color: "var(--text-secondary)",
										marginTop: "-10px",
									}}
								>
									Matriz de comparación cruzada que muestra cuántas veces una
									clase física real fue predicha en otras categorías por la IA.
								</p>
								<div className="matrix-container">
									<div className="matrix-grid">
										{/* Header empty space */}
										<div
											className="matrix-col-label"
											style={{ visibility: "hidden" }}
										>
											Labels
										</div>
										{/* Columns labels */}
										{modelInfo.classes.map((cls) => (
											<div key={cls} className="matrix-col-label">
												{cls}
											</div>
										))}

										{/* Rows */}
										{modelInfo.classes.map((rowCls, rIdx) => (
											<React.Fragment key={rowCls}>
												{/* Row Header */}
												<div className="matrix-label">{rowCls}</div>
												{/* Cells */}
												{modelInfo.classes.map((colCls, cIdx) => {
													const val =
														modelInfo.confusion_matrix[rIdx][cIdx];
													const rowSum = modelInfo.confusion_matrix[
														rIdx
													].reduce((a, b) => a + b, 0);
													const pct =
														rowSum > 0 ? (val / rowSum) * 100 : 0;

													// Darken cell background based on percentage matching
													const opacity =
														rowSum > 0
															? (val / rowSum) * 0.7 + 0.05
															: 0.05;
													const bgStyle =
														rIdx === cIdx
															? `rgba(16, 185, 129, ${opacity})` // Green for true positives
															: `rgba(239, 68, 68, ${opacity})`; // Red for errors

													return (
														<div
															key={colCls}
															className="matrix-cell"
															style={{ backgroundColor: bgStyle }}
															title={`Real: ${rowCls}, Predicho: ${colCls}\nConteo: ${val} (${pct.toFixed(1)}%)`}
														>
															<span className="matrix-cell-val">
																{val}
															</span>
															<span className="matrix-cell-pct">
																{pct.toFixed(0)}%
															</span>
														</div>
													);
												})}
											</React.Fragment>
										))}
									</div>
									<div
										style={{
											display: "flex",
											gap: "20px",
											fontSize: "0.75rem",
											color: "var(--text-secondary)",
											marginTop: "8px",
										}}
									>
										<div
											style={{
												display: "flex",
												alignItems: "center",
												gap: "6px",
											}}
										>
											<div
												style={{
													width: "12px",
													height: "12px",
													background: "rgba(16, 185, 129, 0.5)",
													borderRadius: "2px",
												}}
											/>
											<span>Predicciones Correctas (Diagonal)</span>
										</div>
										<div
											style={{
												display: "flex",
												alignItems: "center",
												gap: "6px",
											}}
										>
											<div
												style={{
													width: "12px",
													height: "12px",
													background: "rgba(239, 68, 68, 0.5)",
													borderRadius: "2px",
												}}
											/>
											<span>Falsas Clasificaciones / Confusiones</span>
										</div>
									</div>
								</div>
							</div>
						)}
					</div>
				)}
			</main>

			<footer
				style={{
					textAlign: "center",
					color: "var(--text-muted)",
					fontSize: "0.75rem",
					padding: "40px 0 20px",
					borderTop: "1px solid var(--border-color)",
					marginTop: "40px",
				}}
			>
				<p>
					Proyecto Pipeline Microplásticos - Asignatura: Computación Visual - Universidad
					Nacional de Colombia
				</p>
				<p style={{ marginTop: "4px" }}>
					Desarrollado por: Victor Ivan Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose
					Arturo Rivera, Manuel Santiago Mori
				</p>
			</footer>
		</div>
	);
}

export default App;
