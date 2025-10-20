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
    set_deterministic_environment()
    yolo_model, hands_detector = ModelManager.get_models()
    validator = FrameValidator()
    error_detector = ErrorDetector()
    error_tracker = ErrorTracker()

    FRAMES_PER_SECOND_TO_PROCESS = max(1, int(((bpm * figure) / 60) * 2))
    MIN_ERROR_FRAMES = FRAMES_PER_SECOND_TO_PROCESS  # Mínimo frames consecutivos para que cuente como error

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_idx = 0
    results = []

    total_processed = 0
    discarded_frames = 0

    # Estructura: {error_type: {'frames': int, 'incident': dict, 'critical_angle': float, 'critical_frame': int, 'last_time': float, 'last_frame': int}}
    ongoing_consecutive_errors = {}
    final_incidents = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frames_interval = max(1, int(fps / FRAMES_PER_SECOND_TO_PROCESS))
        if frame_idx % frames_interval != 0:
            frame_idx += 1
            continue

        frame_data = validator.validate_frame(frame, yolo_model, hands_detector)
        total_processed += 1
        current_time = frame_idx / fps if fps > 0 else 0

        if not frame_data.is_valid:
            discarded_frames += 1
            # Si el frame no es válido, finalizar todos los errores activos
            ongoing_consecutive_errors = _finalize_all_ongoing_errors(
                ongoing_consecutive_errors, MIN_ERROR_FRAMES, final_incidents
            )
            frame_idx += 1
            continue

        detected_errors = error_detector.detect_errors(frame_data)
        
        # Actualizar errores consecutivos
        ongoing_consecutive_errors = _update_consecutive_errors(
            ongoing_consecutive_errors, detected_errors, current_time, frame_idx, 
            MIN_ERROR_FRAMES, final_incidents, error_tracker
        )

        frame_idx += 1

    cap.release()

    # Finalizar errores activos al terminar el video
    _finalize_all_ongoing_errors(ongoing_consecutive_errors, MIN_ERROR_FRAMES, final_incidents)

    # Convertir a PosturalError - solo errores con duración >= 1 segundo
    for inc in final_incidents:
        if inc['duration'] >= 1.0:
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

def _update_consecutive_errors(ongoing_errors, detected_errors, current_time, frame_idx, min_frames, final_incidents, error_tracker):
    """Actualiza errores consecutivos y finaliza los que ya no están presentes"""
    current_error_types = {e["type"] for e in detected_errors}
    error_map = {e["type"]: e for e in detected_errors}
    
    # Finalizar errores que ya no están presentes
    errors_to_remove = []
    for error_type in ongoing_errors:
        if error_type not in current_error_types:
            error = ongoing_errors[error_type]
            if error['frames'] >= min_frames:
                # Guardar incidente válido
                incident = error['incident']
                incident['end_time'] = error['last_time']
                incident['end_frame'] = error['last_frame']
                incident['duration'] = incident['end_time'] - incident['start_time']
                final_incidents.append(incident)
            errors_to_remove.append(error_type)
    
    # Remover errores finalizados
    for error_type in errors_to_remove:
        del ongoing_errors[error_type]
    
    # Procesar errores detectados en el frame actual
    for error_type in current_error_types:
        data = error_map[error_type]
        angle = data.get("angle")
        
        if error_type in ongoing_errors:
            # Continuar error existente
            err = ongoing_errors[error_type]
            err['frames'] += 1
            err['last_time'] = current_time
            err['last_frame'] = frame_idx
            
            # Actualizar frame crítico según el tipo de error
            if "wrist_rules" in error_type:
                if angle < err['critical_angle']:
                    err['critical_angle'] = angle
                    err['critical_frame'] = frame_idx
                    err['incident']['critical_frame'] = frame_idx
                    err['incident']['critical_angle'] = angle
            elif "abduction_rules" in error_type:
                if angle > err['critical_angle']:
                    err['critical_angle'] = angle
                    err['critical_frame'] = frame_idx
                    err['incident']['critical_frame'] = frame_idx
                    err['incident']['critical_angle'] = angle
        else:
            # Iniciar nuevo error
            incident = {
                'start_time': current_time,
                'start_frame': frame_idx,
                'end_time': current_time,
                'end_frame': frame_idx,
                'critical_frame': frame_idx,
                'critical_angle': angle,
                'error_type': error_type,
                'description': error_tracker._get_error_description(error_type)
            }
            ongoing_errors[error_type] = {
                'frames': 1,
                'incident': incident,
                'critical_angle': angle,
                'critical_frame': frame_idx,
                'last_time': current_time,
                'last_frame': frame_idx
            }
    
    return ongoing_errors

def _finalize_all_ongoing_errors(ongoing_errors, min_frames, final_incidents):
    """Finaliza todos los errores en curso y guarda los válidos"""
    for error_type, error in ongoing_errors.items():
        if error['frames'] >= min_frames:
            incident = error['incident']
            incident['end_time'] = error['last_time']
            incident['end_frame'] = error['last_frame']
            incident['duration'] = incident['end_time'] - incident['start_time']
            final_incidents.append(incident)
    
    return {}  # Retorna diccionario vacío