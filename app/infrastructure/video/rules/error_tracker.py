from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ErrorTracker:
    """Temporal tracking"""

    def __init__(self):
        self.ongoing_errors: Dict = {}
        self.incidents: List = []

    def update_errors(self, detected_errors: List[Dict], current_time: float, frame_idx: int) -> List:
        current_error_types = {e["type"] for e in detected_errors}
        error_map = {e["type"]: e for e in detected_errors}

        # Finalizar errores que ya no están presentes
        errors_to_finalize = []
        for error_type in self.ongoing_errors:
            if error_type not in current_error_types:
                errors_to_finalize.append(error_type)

        for error_type in errors_to_finalize:
            incident = self._finalize_error(error_type)
            if incident:
                self.incidents.append(incident)

        # Procesar los errores actuales
        for error_type in current_error_types:
            data = error_map[error_type]
            angle = data.get("angle")

            if error_type in self.ongoing_errors:
                err = self.ongoing_errors[error_type]
                err['end_time'] = current_time
                err['end_frame'] = frame_idx

                # Actualizar frame crítico
                if "wrist_rules" in error_type:
                    # Guardar el frame donde el ángulo fue menor
                    if angle < err['critical_angle']:
                        err['critical_angle'] = angle
                        err['critical_frame'] = frame_idx
                elif "abduction_rules" in error_type:
                    # Guardar el frame donde el ángulo fue mayor
                    if angle > err['critical_angle']:
                        err['critical_angle'] = angle
                        err['critical_frame'] = frame_idx
            else:
                # Crear nuevo error
                self.ongoing_errors[error_type] = {
                    'start_time': current_time,
                    'end_time': current_time,
                    'start_frame': frame_idx,
                    'end_frame': frame_idx,
                    'critical_frame': frame_idx,
                    'critical_angle': angle,
                    'type': error_type
                }

        return self.incidents.copy()

    def finalize_all_errors(self) -> List:
        error_types = list(self.ongoing_errors.keys())
        for error_type in error_types:
            incident = self._finalize_error(error_type)
            if incident:
                self.incidents.append(incident)
        return self.incidents.copy()

    def _finalize_error(self, error_type: str) -> Optional[Dict]:
        if error_type not in self.ongoing_errors:
            return None

        error_info = self.ongoing_errors[error_type]
        duration = error_info['end_time'] - error_info['start_time']
        description = self._get_error_description(error_type)

        incident = {
            'start_time': error_info['start_time'],
            'end_time': error_info['end_time'],
            'start_frame': error_info['start_frame'],
            'end_frame': error_info['end_frame'],
            'critical_frame': error_info['critical_frame'],
            'duration': duration,
            'error_type': error_type,
            'description': description
        }

        del self.ongoing_errors[error_type]
        return incident

    def _get_error_description(self, error_type: str) -> str:
        if "wrist_rules" in error_type:
            hand = "izquierda" if "izquierda" in error_type else "derecha"
            return f"Flexión radial/cubital menor a 155° en mano {hand}"
        elif "abduction_rules" in error_type:
            hand = "izquierda" if "izquierda" in error_type else "derecha"
            if "dedos_" in error_type:
                parts = error_type.split("_")
                if len(parts) >= 4:
                    finger1, finger2 = parts[-2], parts[-1]
                    return f"Ángulo excesivo (>60°) entre dedos {finger1}-{finger2} en mano {hand}"
            return f"Error de abducción en mano {hand}"
        return error_type
