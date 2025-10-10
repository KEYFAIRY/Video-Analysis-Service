from app.domain.entities.postural_error import PosturalError
from app.infrastructure.video.models.deterministic import set_deterministic_environment
from .models.model_manager import ModelManager
from .detection.validators import FrameValidator
from .rules.error_rules import ErrorDetector
from .rules.error_tracker import ErrorTracker
from .utils.time_utils import format_seconds_to_mmss
import cv2
import logging

logger = logging.getLogger(__name__)

def process_video(video_path: str, practice_id: int, bpm: int, figure: float) -> list[PosturalError]:

    # Re-establecer semillas antes de cada procesamiento
    set_deterministic_environment()
    
    # Obtener modelos inicializados
    yolo_model, hands_detector = ModelManager.get_models()
    
    # Inicializar componentes
    validator = FrameValidator()
    error_detector = ErrorDetector()
    error_tracker = ErrorTracker()
    
    # Configuración
    FRAMES_PER_SECOND_TO_PROCESS = max(1, int(((bpm*figure) / 60) * 2))
    MIN_ERROR_DURATION = 1.0
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_idx = 0
    results = []
    
    # Estadísticas
    total_processed = 0
    discarded_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            # Finalizar todos los errores pendientes
            incidents = error_tracker.finalize_all_errors()
            break

        # Procesar solo ciertos frames
        frames_interval = max(1, int(fps / FRAMES_PER_SECOND_TO_PROCESS))
        if frame_idx % frames_interval != 0:
            frame_idx += 1
            continue

        # Validar frame
        frame_data = validator.validate_frame(frame, yolo_model, hands_detector)
        total_processed += 1
        
        if not frame_data.is_valid:
            discarded_frames += 1
            frame_idx += 1
            continue

        # Detectar errores
        detected_errors = error_detector.detect_errors(frame_data)
        
        # Actualizar tracker
        current_time = frame_idx / fps if fps > 0 else 0
        incidents = error_tracker.update_errors(detected_errors, current_time, frame_idx)

        frame_idx += 1

    cap.release()

    # Convertir a PosturalError
    for inc in incidents:
        if inc and inc['duration'] >= MIN_ERROR_DURATION:
            min_sec_init = format_seconds_to_mmss(inc['start_time'])
            min_sec_end = format_seconds_to_mmss(inc['end_time'])

            results.append(
                PosturalError(
                    min_sec_init=min_sec_init,
                    min_sec_end=min_sec_end,
                    frame=inc['critical_frame'],
                    explication=inc['description'],
                    id_practice=practice_id
                )
            )


    logger.info(f"Video {video_path}: processed {total_processed} frames, discarded {discarded_frames}, found {len(results)} errors")
    return results