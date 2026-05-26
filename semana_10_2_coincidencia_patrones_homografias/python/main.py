from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

import cv2
import numpy as np


@dataclass
class StageMetrics:
    stage: str
    total_matches: int
    good_matches: int
    inliers: int
    inlier_ratio: float
    processing_ms: float
    note: str = ""


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {path}")
    return image


def ensure_image_write(path: Path, image: np.ndarray) -> None:
    ok = cv2.imwrite(str(path), image)
    if not ok:
        raise RuntimeError(f"No se pudo guardar la imagen: {path}")


def create_detector(name: str, max_features: int) -> Tuple[cv2.Feature2D, str, int, str]:
    detector_name = name.lower()
    if detector_name == "auto":
        detector_name = "sift" if hasattr(cv2, "SIFT_create") else "orb"

    if detector_name == "sift":
        if not hasattr(cv2, "SIFT_create"):
            raise RuntimeError("SIFT no esta disponible en este entorno de OpenCV.")
        detector = cv2.SIFT_create(nfeatures=max_features)
        return detector, "float", cv2.NORM_L2, "sift"

    if detector_name == "orb":
        detector = cv2.ORB_create(nfeatures=max_features)
        return detector, "binary", cv2.NORM_HAMMING, "orb"

    raise ValueError("Detector invalido. Usa: auto, sift u orb.")


def detect_and_describe(image: np.ndarray, detector: cv2.Feature2D) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    keypoints, descriptors = detector.detectAndCompute(gray, None)
    if descriptors is None or len(keypoints) == 0:
        raise RuntimeError("No se detectaron keypoints/descriptores en una de las imagenes.")
    return keypoints, descriptors


def ratio_test(knn_matches: Sequence[Sequence[cv2.DMatch]], ratio: float) -> List[cv2.DMatch]:
    good_matches: List[cv2.DMatch] = []
    for pair in knn_matches:
        if len(pair) < 2:
            continue
        m, n = pair
        if m.distance < ratio * n.distance:
            good_matches.append(m)
    good_matches.sort(key=lambda m: m.distance)
    return good_matches


def bf_match(
    des_1: np.ndarray,
    des_2: np.ndarray,
    norm_type: int,
    ratio: float,
) -> Tuple[List[Sequence[cv2.DMatch]], List[cv2.DMatch]]:
    matcher = cv2.BFMatcher(norm_type, crossCheck=False)
    knn_matches = matcher.knnMatch(des_1, des_2, k=2)
    good_matches = ratio_test(knn_matches, ratio)
    return knn_matches, good_matches


def flann_match(
    des_1: np.ndarray,
    des_2: np.ndarray,
    descriptor_type: str,
    ratio: float,
) -> Tuple[List[Sequence[cv2.DMatch]], List[cv2.DMatch]]:
    if descriptor_type == "float":
        des_1 = des_1.astype(np.float32)
        des_2 = des_2.astype(np.float32)
        index_params = dict(algorithm=1, trees=5)
    else:
        index_params = dict(algorithm=6, table_number=6, key_size=12, multi_probe_level=1)

    search_params = dict(checks=64)
    matcher = cv2.FlannBasedMatcher(index_params, search_params)
    knn_matches = matcher.knnMatch(des_1, des_2, k=2)
    good_matches = ratio_test(knn_matches, ratio)
    return knn_matches, good_matches


def compute_homography_query_to_train(
    kp_query: Sequence[cv2.KeyPoint],
    kp_train: Sequence[cv2.KeyPoint],
    matches: Sequence[cv2.DMatch],
    ransac_thresh: float,
) -> Tuple[np.ndarray, np.ndarray]:
    if len(matches) < 4:
        raise RuntimeError("No hay matches suficientes para calcular homografia (minimo 4).")

    src_pts = np.float32([kp_query[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp_train[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

    h_matrix, inlier_mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_thresh)
    if h_matrix is None or inlier_mask is None:
        raise RuntimeError("findHomography no encontro una transformacion valida.")
    return h_matrix, inlier_mask


def draw_matches(
    img_1: np.ndarray,
    kp_1: Sequence[cv2.KeyPoint],
    img_2: np.ndarray,
    kp_2: Sequence[cv2.KeyPoint],
    matches: Sequence[cv2.DMatch],
    matches_mask: np.ndarray | None = None,
    limit: int = 80,
) -> np.ndarray:
    selected = list(matches[:limit])
    draw_params = dict(flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    if matches_mask is not None:
        draw_params["matchesMask"] = matches_mask.ravel().tolist()[: len(selected)]
        draw_params["matchColor"] = (0, 255, 0)
        draw_params["singlePointColor"] = (0, 0, 255)

    return cv2.drawMatches(img_1, kp_1, img_2, kp_2, selected, None, **draw_params)


def detect_object_with_homography(
    template: np.ndarray,
    scene: np.ndarray,
    detector: cv2.Feature2D,
    descriptor_type: str,
    ratio: float,
    ransac_thresh: float,
) -> Tuple[np.ndarray, StageMetrics]:
    t_start = time.perf_counter()

    kp_t, des_t = detect_and_describe(template, detector)
    kp_s, des_s = detect_and_describe(scene, detector)
    knn, good = flann_match(des_t, des_s, descriptor_type, ratio)
    total = len(knn)

    h_matrix, inlier_mask = compute_homography_query_to_train(kp_t, kp_s, good, ransac_thresh)
    inliers = int(inlier_mask.sum())
    ratio_inliers = inliers / len(good) if good else 0.0

    h_t, w_t = template.shape[:2]
    corners = np.float32([[0, 0], [w_t, 0], [w_t, h_t], [0, h_t]]).reshape(-1, 1, 2)
    projected = cv2.perspectiveTransform(corners, h_matrix)

    output = scene.copy()
    cv2.polylines(output, [np.int32(projected)], True, (0, 255, 0), 3, cv2.LINE_AA)

    metrics = StageMetrics(
        stage="deteccion_objeto_homografia",
        total_matches=total,
        good_matches=len(good),
        inliers=inliers,
        inlier_ratio=ratio_inliers,
        processing_ms=(time.perf_counter() - t_start) * 1000.0,
    )
    return output, metrics


def feather_blend(image_a: np.ndarray, image_b: np.ndarray, sigma: float = 15.0) -> np.ndarray:
    mask_a = (image_a.sum(axis=2) > 0).astype(np.float32)
    mask_b = (image_b.sum(axis=2) > 0).astype(np.float32)

    weight_a = cv2.GaussianBlur(mask_a, (0, 0), sigmaX=sigma, sigmaY=sigma)
    weight_b = cv2.GaussianBlur(mask_b, (0, 0), sigmaX=sigma, sigmaY=sigma)
    total = weight_a + weight_b
    total[total == 0] = 1.0

    blended = (
        image_a.astype(np.float32) * weight_a[..., None]
        + image_b.astype(np.float32) * weight_b[..., None]
    ) / total[..., None]
    return np.clip(blended, 0, 255).astype(np.uint8)


def crop_non_black(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    coords = cv2.findNonZero(binary)
    if coords is None:
        return image
    x, y, w, h = cv2.boundingRect(coords)
    return image[y : y + h, x : x + w]


def stitch_pair(
    left: np.ndarray,
    right: np.ndarray,
    detector: cv2.Feature2D,
    descriptor_type: str,
    norm_type: int,
    ratio: float,
    ransac_thresh: float,
) -> Tuple[np.ndarray, np.ndarray, StageMetrics]:
    t_start = time.perf_counter()

    kp_left, des_left = detect_and_describe(left, detector)
    kp_right, des_right = detect_and_describe(right, detector)

    if descriptor_type == "float":
        knn, good = flann_match(des_left, des_right, descriptor_type, ratio)
    else:
        knn, good = bf_match(des_left, des_right, norm_type, ratio)

    if len(good) < 4:
        raise RuntimeError("No hay matches suficientes para hacer stitching (minimo 4).")

    pts_left = np.float32([kp_left[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    pts_right = np.float32([kp_right[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    h_right_to_left, inlier_mask = cv2.findHomography(pts_right, pts_left, cv2.RANSAC, ransac_thresh)
    if h_right_to_left is None or inlier_mask is None:
        raise RuntimeError("No fue posible estimar la homografia para stitching.")

    h_left, w_left = left.shape[:2]
    h_right, w_right = right.shape[:2]

    corners_left = np.float32([[0, 0], [0, h_left], [w_left, h_left], [w_left, 0]]).reshape(-1, 1, 2)
    corners_right = np.float32([[0, 0], [0, h_right], [w_right, h_right], [w_right, 0]]).reshape(-1, 1, 2)
    warped_corners_right = cv2.perspectiveTransform(corners_right, h_right_to_left)
    all_corners = np.concatenate((corners_left, warped_corners_right), axis=0)

    x_min, y_min = np.floor(all_corners.min(axis=0).ravel()).astype(int)
    x_max, y_max = np.ceil(all_corners.max(axis=0).ravel()).astype(int)

    translation = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]], dtype=np.float64)
    output_size = (int(x_max - x_min), int(y_max - y_min))

    warped_right = cv2.warpPerspective(right, translation @ h_right_to_left, output_size)
    left_canvas = np.zeros_like(warped_right)
    offset_x, offset_y = -x_min, -y_min
    left_canvas[offset_y : offset_y + h_left, offset_x : offset_x + w_left] = left

    hard_pano = warped_right.copy()
    mask_left = left_canvas.sum(axis=2) > 0
    hard_pano[mask_left] = left_canvas[mask_left]

    blended_pano = feather_blend(left_canvas, warped_right, sigma=18.0)

    inliers = int(inlier_mask.sum())
    metrics = StageMetrics(
        stage="stitching_panorama",
        total_matches=len(knn),
        good_matches=len(good),
        inliers=inliers,
        inlier_ratio=inliers / len(good),
        processing_ms=(time.perf_counter() - t_start) * 1000.0,
    )
    return crop_non_black(hard_pano), crop_non_black(blended_pano), metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Taller semana 10.2: matching de features, homografia y stitching con OpenCV."
    )
    parser.add_argument("--image-a", type=Path, required=True, help="Imagen A para matching/homografia.")
    parser.add_argument("--image-b", type=Path, required=True, help="Imagen B para matching/homografia.")
    parser.add_argument("--template", type=Path, help="Imagen template para deteccion de objeto.")
    parser.add_argument("--scene", type=Path, help="Imagen escena para deteccion de objeto.")
    parser.add_argument(
        "--panorama-images",
        type=Path,
        nargs="+",
        help="Lista de 2 o 3 imagenes con solapamiento para panorama.",
    )
    parser.add_argument("--detector", choices=["auto", "sift", "orb"], default="auto")
    parser.add_argument("--max-features", type=int, default=2000)
    parser.add_argument("--ratio-test", type=float, default=0.75)
    parser.add_argument("--ransac-thresh", type=float, default=4.0)
    parser.add_argument("--disable-bonus-blending", action="store_true")
    parser.add_argument("--output-dir", type=Path, help="Carpeta de salida; por defecto ../media.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_dir = args.output_dir or (Path(__file__).resolve().parents[1] / "media")
    output_dir.mkdir(parents=True, exist_ok=True)

    detector, descriptor_type, norm_type, detector_name = create_detector(args.detector, args.max_features)
    print(f"[INFO] Detector seleccionado: {detector_name}")

    img_a = load_image(args.image_a)
    img_b = load_image(args.image_b)
    kp_a, des_a = detect_and_describe(img_a, detector)
    kp_b, des_b = detect_and_describe(img_b, detector)

    metrics: List[StageMetrics] = []

    t_bf = time.perf_counter()
    bf_knn, bf_good = bf_match(des_a, des_b, norm_type, args.ratio_test)
    bf_visual = draw_matches(img_a, kp_a, img_b, kp_b, bf_good)
    ensure_image_write(output_dir / "python_bf_matches.jpg", bf_visual)
    metrics.append(
        StageMetrics(
            stage="matching_bf",
            total_matches=len(bf_knn),
            good_matches=len(bf_good),
            inliers=0,
            inlier_ratio=0.0,
            processing_ms=(time.perf_counter() - t_bf) * 1000.0,
        )
    )

    t_flann = time.perf_counter()
    flann_knn, flann_good = flann_match(des_a, des_b, descriptor_type, args.ratio_test)
    flann_visual = draw_matches(img_a, kp_a, img_b, kp_b, flann_good)
    ensure_image_write(output_dir / "python_flann_matches.jpg", flann_visual)
    metrics.append(
        StageMetrics(
            stage="matching_flann",
            total_matches=len(flann_knn),
            good_matches=len(flann_good),
            inliers=0,
            inlier_ratio=0.0,
            processing_ms=(time.perf_counter() - t_flann) * 1000.0,
        )
    )

    t_h = time.perf_counter()
    homography_matches = flann_good if len(flann_good) >= 4 else bf_good
    h_matrix, inlier_mask = compute_homography_query_to_train(
        kp_a, kp_b, homography_matches, args.ransac_thresh
    )
    inliers = int(inlier_mask.sum())
    homography_visual = draw_matches(img_a, kp_a, img_b, kp_b, homography_matches, inlier_mask)
    ensure_image_write(output_dir / "python_homografia_inliers.jpg", homography_visual)
    metrics.append(
        StageMetrics(
            stage="homografia_ransac",
            total_matches=len(homography_matches),
            good_matches=len(homography_matches),
            inliers=inliers,
            inlier_ratio=inliers / len(homography_matches),
            processing_ms=(time.perf_counter() - t_h) * 1000.0,
            note=f"Matriz H: {np.array2string(h_matrix, precision=4, suppress_small=True)}",
        )
    )

    if args.template and args.scene:
        template = load_image(args.template)
        scene = load_image(args.scene)
        detected_scene, object_metrics = detect_object_with_homography(
            template=template,
            scene=scene,
            detector=detector,
            descriptor_type=descriptor_type,
            ratio=args.ratio_test,
            ransac_thresh=args.ransac_thresh,
        )
        ensure_image_write(output_dir / "python_deteccion_objeto.jpg", detected_scene)
        metrics.append(object_metrics)
    else:
        metrics.append(
            StageMetrics(
                stage="deteccion_objeto_homografia",
                total_matches=0,
                good_matches=0,
                inliers=0,
                inlier_ratio=0.0,
                processing_ms=0.0,
                note="Omitido: usa --template y --scene para ejecutar esta parte.",
            )
        )

    panorama_paths = args.panorama_images if args.panorama_images else [args.image_a, args.image_b]
    if len(panorama_paths) < 2:
        raise ValueError("Para panorama se requieren al menos 2 imagenes.")

    panorama_images = [load_image(path) for path in panorama_paths]
    running_hard = panorama_images[0]
    running_blend = panorama_images[0]
    last_stage_metrics: StageMetrics | None = None

    for next_image in panorama_images[1:]:
        hard, blend, stage_metrics = stitch_pair(
            left=running_blend,
            right=next_image,
            detector=detector,
            descriptor_type=descriptor_type,
            norm_type=norm_type,
            ratio=args.ratio_test,
            ransac_thresh=args.ransac_thresh,
        )
        running_hard = hard
        running_blend = blend
        last_stage_metrics = stage_metrics

    ensure_image_write(output_dir / "python_panorama_sin_blending.jpg", running_hard)
    if not args.disable_bonus_blending:
        ensure_image_write(output_dir / "python_panorama_blending_bonus.jpg", running_blend)

    if last_stage_metrics:
        if args.disable_bonus_blending:
            last_stage_metrics.note = "Bonus desactivado: panorama sin blending suave."
        else:
            last_stage_metrics.note = "Bonus activo: panorama con feather blending."
        metrics.append(last_stage_metrics)

    metrics_payload = {
        "detector": detector_name,
        "ratio_test": args.ratio_test,
        "ransac_thresh": args.ransac_thresh,
        "stages": [asdict(stage) for stage in metrics],
    }
    metrics_path = output_dir / "python_metricas.json"
    metrics_path.write_text(json.dumps(metrics_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] Resultados guardados en: {output_dir}")
    print(f"[OK] Métricas guardadas en: {metrics_path}")


if __name__ == "__main__":
    main()
