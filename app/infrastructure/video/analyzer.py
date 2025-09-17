# analyzer.py - Versión determinista enfocada en la aleatoriedad de modelos

from app.domain.entities.postural_error import PosturalError
import cv2
import numpy as np
import mediapipe as mp
from ultralytics import YOLO
from datetime import timedelta
from typing import List
import logging
import os
import random
import torch

logger = logging.getLogger(__name__)

# -----------------------
# Configuración
# -----------------------
YOLO_WEIGHTS = "yolo11m-pose.pt"
MIN_HAND_DISTANCE = 100
MIN_HAND_CONFIDENCE = 0.85
MIN_ELBOW_CONFIDENCE = 0.5
MIN_HAND_LANDMARKS_VISIBLE = 18
MIN_ERROR_DURATION = 1.0  # segundos

# SEMILLA DETERMINÍSTICA
RANDOM_SEED = 42

def set_deterministic_environment():
    """Configura entorno determinista para los modelos."""
    # Python random
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    os.environ['PYTHONHASHSEED'] = str(RANDOM_SEED)
    
    # PyTorch (YOLO)
    torch.manual_seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(RANDOM_SEED)
        torch.cuda.manual_seed_all(RANDOM_SEED)
        # CRÍTICO: Forzar comportamiento determinista
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    # Variables de entorno para TensorFlow (MediaPipe)
    os.environ['TF_DETERMINISTIC_OPS'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# -----------------------
# Helpers matemáticos (más robustos)
# -----------------------
def angle_between_points(a, b, c):
    """Cálculo de ángulo más preciso y consistente."""
    a, b, c = map(lambda p: np.array(p, dtype=np.float64), (a, b, c))
    ba, bc = a - b, c - b
    
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    
    if norm_ba < 1e-10 or norm_bc < 1e-10:
        return 0.0
    
    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    
    # Redondeo para consistencia numérica
    angle = np.degrees(np.arccos(cos_angle))
    return round(angle, 2)

def distance_between_points(p1, p2):
    """Distancia con precisión consistente."""
    dist = np.linalg.norm(np.array(p1, dtype=np.float64) - np.array(p2, dtype=np.float64))
    return round(dist, 2)

def format_seconds_to_mmss(seconds):
    td = timedelta(seconds=int(seconds))
    mm, ss = divmod(td.seconds, 60)
    return f"{mm:02}:{ss:02}"

# -----------------------
# Funciones de validación (idénticas al Código 1)
# -----------------------
def validate_hand_quality(hand_landmarks, w, h):
    visible_landmarks = 0
    confidence_sum = 0

    for landmark in hand_landmarks.landmark:
        x, y = int(landmark.x * w), int(landmark.y * h)
        if 0 <= x < w and 0 <= y < h:
            if hasattr(landmark, 'visibility') and landmark.visibility > 0.5:
                visible_landmarks += 1
                confidence_sum += landmark.visibility
            else:
                visible_landmarks += 1

    avg_confidence = confidence_sum / visible_landmarks if visible_landmarks > 0 else 0
    is_valid = visible_landmarks >= MIN_HAND_LANDMARKS_VISIBLE
    return is_valid, visible_landmarks, avg_confidence

def detect_obstruction_in_regions(frame, elbows_detected, manos_detectadas):
    """Detecta obstrucciones en regiones críticas - IMPLEMENTACIÓN COMPLETA DEL CÓDIGO 1"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    regions_of_interest = []

    # Regiones de manos
    for _, wrist, _, _, _ in manos_detectadas:
        x, y = wrist
        x1, y1 = max(0, x-50), max(0, y-50)
        x2, y2 = min(frame.shape[1], x+50), min(frame.shape[0], y+50)
        regions_of_interest.append((x1, y1, x2, y2, "mano"))

    # Regiones de codos
    for elbow in elbows_detected:
        x, y = elbow
        x1, y1 = max(0, x-40), max(0, y-40)
        x2, y2 = min(frame.shape[1], x+40), min(frame.shape[0], y+40)
        regions_of_interest.append((x1, y1, x2, y2, "codo"))

    # Análisis de obstrucciones
    for x1, y1, x2, y2, region_type in regions_of_interest:
        roi = gray[y1:y2, x1:x2]
        if roi.size == 0:
            continue

        edges = cv2.Canny(roi, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if region_type == "mano" and area > 500:
                return True
            elif region_type == "codo" and area > 300:
                return True

    return False

def validate_hands_positioning(manos_detectadas):
    """Validación completa de posicionamiento - DEL CÓDIGO 1"""
    if len(manos_detectadas) != 2:
        return False

    manos_sorted = sorted(manos_detectadas, key=lambda m: m[0])
    mano_izq, mano_der = manos_sorted

    dist_horizontal = abs(mano_der[0] - mano_izq[0])
    if dist_horizontal < MIN_HAND_DISTANCE:
        return False

    dist_vertical = abs(mano_der[1][1] - mano_izq[1][1])
    if dist_vertical > 80:
        return False

    return True

# -----------------------
# Reglas de detección de errores (del Código 1)
# -----------------------
def wrist_rules(wrist, mid_wrist, elbow, hand_side):
    if elbow is None:
        return []
    ang = angle_between_points(elbow, wrist, mid_wrist)
    if ang < 155:
        return [f"wrist_rules_{hand_side.lower()}"]
    return []

def abduction_rules(wrist, fingers, hand_side):
    errors = []
    for i in range(len(fingers) - 1):
        a, c = fingers[i], fingers[i + 1]
        ang = angle_between_points(a, wrist, c)
        if ang > 60:
            errors.append(f"abduction_rules_{hand_side.lower()}_dedos_{i}_{i+1}")
    return errors

def get_error_description(error_type: str) -> str:
    """Descripción legible de errores - MEJORADA"""
    if "wrist_rules" in error_type:
        hand = "izquierda" if "izquierda" in error_type else "derecha"
        return f"Flexión radial/cubital en mano {hand}"
    elif "abduction_rules" in error_type:
        hand = "izquierda" if "izquierda" in error_type else "derecha"
        if "dedos_" in error_type:
            parts = error_type.split("_")
            if len(parts) >= 4:
                finger1, finger2 = parts[-2], parts[-1]
                return f"Ángulo excesivo entre dedos {finger1}-{finger2} en mano {hand}"
        return f"Error de abducción en mano {hand}"
    return error_type

# -----------------------
# Inicialización determinística de modelos
# -----------------------
def safe_load_yolo_model(weights_path: str, max_retries: int = 3):
    """Carga segura del modelo YOLO con validación y reintentos."""
    for attempt in range(max_retries):
        try:
            # Verificar si el archivo existe y es válido
            if os.path.exists(weights_path):
                file_size = os.path.getsize(weights_path)
                # Verificar que el archivo no esté vacío o corrupto
                if file_size < 1000000:  # Menos de 1MB indica archivo corrupto
                    logger.warning(f"Model file {weights_path} appears corrupted (size: {file_size}). Removing...")
                    os.remove(weights_path)
            
            # Intentar cargar el modelo
            logger.info(f"Loading YOLO model from {weights_path} (attempt {attempt + 1}/{max_retries})")
            yolo_model = YOLO(weights_path)
            
            # Forzar modo eval para deshabilitar dropout y comportamientos aleatorios
            if hasattr(yolo_model.model, 'eval'):
                yolo_model.model.eval()
            
            logger.info("YOLO model loaded successfully")
            return yolo_model
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model (attempt {attempt + 1}/{max_retries}): {e}")
            
            # Si el archivo existe pero está corrupto, eliminarlo
            if os.path.exists(weights_path):
                try:
                    os.remove(weights_path)
                    logger.info(f"Removed corrupted model file: {weights_path}")
                except Exception as rm_e:
                    logger.error(f"Failed to remove corrupted file: {rm_e}")
            
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to load YOLO model after {max_retries} attempts: {e}")
            
            # Esperar antes del siguiente intento
            import time
            time.sleep(2 ** attempt)  # Backoff exponencial
    
    raise RuntimeError("Unable to load YOLO model")

def initialize_models():
    """Inicializa modelos con configuración determinista."""
    set_deterministic_environment()
    
    # YOLO con carga segura y configuración determinista
    yolo_model = safe_load_yolo_model(YOLO_WEIGHTS)
    
    # MediaPipe con configuración más estricta
    mp_hands = mp.solutions.hands
    hands_detector = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=MIN_HAND_CONFIDENCE,
        min_tracking_confidence=MIN_HAND_CONFIDENCE,
    )
    
    return yolo_model, hands_detector

# Variables globales de modelos (inicializadas una sola vez)
_yolo_model = None
_hands_detector = None

def get_models():
    """Obtiene las instancias de los modelos (singleton pattern)."""
    global _yolo_model, _hands_detector
    if _yolo_model is None or _hands_detector is None:
        _yolo_model, _hands_detector = initialize_models()
    return _yolo_model, _hands_detector

# -----------------------
# Función principal de procesamiento DETERMINÍSTICA
# -----------------------
def process_video(video_path: str, practice_id: int, bpm: int) -> list['PosturalError']:
    """
    Procesamiento determinista de video - MISMA LÓGICA DEL CÓDIGO 1
    """
    # CRÍTICO: Re-establecer semillas antes de cada procesamiento
    set_deterministic_environment()
    
    # Obtener modelos inicializados
    yolo_model, hands_detector = get_models()
    
    # Calcular frames por segundo basado en BPM
    FRAMES_PER_SECOND_TO_PROCESS = max(1, int((bpm / 60) * 2))
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_idx = 0
    results = []
    
    # Sistema de seguimiento de errores (del Código 1)
    ongoing_errors = {}
    incidents = []
    
    # Estadísticas
    total_processed = 0
    discarded_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            # Finalizar todos los errores pendientes
            _finalize_all_ongoing_errors(ongoing_errors, incidents)
            break

        # Procesar solo ciertos frames por segundo (del Código 1)
        frames_interval = max(1, int(fps / FRAMES_PER_SECOND_TO_PROCESS))
        if frame_idx % frames_interval != 0:
            frame_idx += 1
            continue

        # PROCESAMIENTO COMPLETO DEL FRAME (lógica del Código 1)
        h, w = frame.shape[:2]
        detected_errors = []
        elbows = {}

        # ===== DETECCIÓN DE CODOS CON YOLO (lógica completa) =====
        results_yolo = yolo_model.predict(frame, imgsz=640, conf=MIN_ELBOW_CONFIDENCE, verbose=False)
        elbows_detected = []
        yolo_valid = False

        for r in results_yolo:
            if r.keypoints is None:
                continue
            kpts = r.keypoints.xy.cpu().numpy()
            confs = r.keypoints.conf.cpu().numpy() if hasattr(r.keypoints, 'conf') else None

            for person_idx, person in enumerate(kpts):
                left_elbow = tuple(map(int, person[7]))
                right_elbow = tuple(map(int, person[8]))

                left_conf = confs[person_idx][7] if confs is not None else 1.0
                right_conf = confs[person_idx][8] if confs is not None else 1.0

                # VALIDACIÓN COMPLETA DE CONFIANZA (del Código 1)
                if left_conf > MIN_ELBOW_CONFIDENCE and right_conf > MIN_ELBOW_CONFIDENCE:
                    elbows_detected.extend([left_elbow, right_elbow])
                    elbows["izquierda"] = left_elbow
                    elbows["derecha"] = right_elbow
                    yolo_valid = True

        # ===== DETECCIÓN DE MANOS CON MEDIAPIPE (lógica completa) =====
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands_detector.process(rgb)
        manos_detectadas = []
        hands_valid = True

        if res.multi_hand_landmarks:
            for hand_landmarks in res.multi_hand_landmarks:
                is_valid, num_visible, avg_conf = validate_hand_quality(hand_landmarks, w, h)

                if is_valid:
                    lm = [(int(p.x * w), int(p.y * h)) for p in hand_landmarks.landmark]
                    wrist = lm[0]
                    middle_mcp = lm[9]
                    manos_detectadas.append((wrist[0], wrist, middle_mcp, hand_landmarks, lm))
                else:
                    hands_valid = False

        total_processed += 1

        # ===== VALIDACIONES COMPLETAS (todas del Código 1) =====
        
        # 1. Validación básica de detecciones
        if len(manos_detectadas) != 2 or len(elbows_detected) != 2 or not yolo_valid or not hands_valid:
            discarded_frames += 1
            frame_idx += 1
            continue

        # 2. Validación de posicionamiento
        if not validate_hands_positioning(manos_detectadas):
            discarded_frames += 1
            frame_idx += 1
            continue

        # 3. Validación de obstrucciones
        if detect_obstruction_in_regions(frame, elbows_detected, manos_detectadas):
            discarded_frames += 1
            frame_idx += 1
            continue

        # 4. Validación de distancia entre muñecas
        wrist1 = manos_detectadas[0][1]
        wrist2 = manos_detectadas[1][1]
        dist = distance_between_points(wrist1, wrist2)
        if dist < MIN_HAND_DISTANCE:
            discarded_frames += 1
            frame_idx += 1
            continue

        # ===== ANÁLISIS DE ERRORES (del Código 1) =====
        manos_detectadas.sort(key=lambda m: m[0])

        for i, (_, wrist, middle_mcp, hand_landmarks, lm) in enumerate(manos_detectadas):
            hand_side = "izquierda" if i == 0 else "derecha"
            elbow = elbows.get(hand_side, None)
            
            # Detectar errores de muñeca
            wrist_errors = wrist_rules(wrist, middle_mcp, elbow, hand_side)
            detected_errors.extend(wrist_errors)

            # Detectar errores de abducción
            tip_idx = [4, 8, 12, 16, 20]
            fingers = [lm[j] for j in tip_idx]
            abduction_errors = abduction_rules(wrist, fingers, hand_side)
            detected_errors.extend(abduction_errors)

        # ===== MANEJO DE INCIDENTES (lógica completa del Código 1) =====
        current_time = frame_idx / fps if fps > 0 else 0
        current_error_set = set(detected_errors)

        # Finalizar errores que ya no están presentes
        errors_to_finalize = []
        for error_type in ongoing_errors:
            if error_type not in current_error_set:
                errors_to_finalize.append(error_type)

        for error_type in errors_to_finalize:
            incident = _finalize_error(error_type, ongoing_errors)
            if incident:
                incidents.append(incident)

        # Procesar errores actuales
        for error_type in current_error_set:
            if error_type in ongoing_errors:
                # Continuar error existente
                ongoing_errors[error_type]['end_time'] = current_time
                ongoing_errors[error_type]['end_frame'] = frame_idx
            else:
                # Iniciar nuevo error
                ongoing_errors[error_type] = {
                    'start_time': current_time,
                    'end_time': current_time,
                    'start_frame': frame_idx,
                    'end_frame': frame_idx,
                    'type': error_type
                }

        frame_idx += 1

    cap.release()

    # ===== CONVERSIÓN A PosturalError (solo errores válidos) =====
    for inc in incidents:
        if inc and inc['duration'] >= MIN_ERROR_DURATION:
            min_sec_init = format_seconds_to_mmss(inc['start_time'])
            min_sec_end = format_seconds_to_mmss(inc['end_time'])
            
            results.append(
                PosturalError(
                    min_sec_init=min_sec_init,
                    min_sec_end=min_sec_end,
                    explication=inc['description'],
                    id_practice=practice_id
                )
            )

    logger.info(f"Video {video_path}: processed {total_processed} frames, discarded {discarded_frames}, found {len(results)} errors")
    return results

# -----------------------
# Funciones auxiliares de finalización (del Código 1)
# -----------------------
def _finalize_error(error_type, ongoing_errors):
    """Finaliza un error específico - SOLO ANÁLISIS DE DATOS"""
    if error_type not in ongoing_errors:
        return None

    error_info = ongoing_errors[error_type]
    duration = error_info['end_time'] - error_info['start_time']
    description = get_error_description(error_type)

    incident = {
        'start_time': error_info['start_time'],
        'end_time': error_info['end_time'],
        'start_frame': error_info['start_frame'],
        'end_frame': error_info['end_frame'],
        'duration': duration,
        'error_type': error_type,
        'description': description
    }

    # Remover del diccionario
    del ongoing_errors[error_type]
    
    return incident

def _finalize_all_ongoing_errors(ongoing_errors, incidents):
    """Finaliza todos los errores en curso - DEL CÓDIGO 1"""
    error_types = list(ongoing_errors.keys())
    for error_type in error_types:
        incident = _finalize_error(error_type, ongoing_errors)
        if incident:
            incidents.append(incident)