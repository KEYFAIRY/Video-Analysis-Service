from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ErrorTracker:
    """Simplified error tracker focused on description generation"""

    def __init__(self):
        # Map finger indices to names
        self.finger_names = {
            "0": "pulgar",
            "1": "índice", 
            "2": "medio",
            "3": "anular",
            "4": "meñique"
        }

    def _get_error_description(self, error_type: str) -> str:
        """Generate error description based on error type"""
        if "wrist_rules" in error_type:
            hand = "izquierda" if "izquierda" in error_type else "derecha"
            return f"Flexión radial/cubital reducida (<155°) en la muñeca {hand} (movimiento lateral hacia el pulgar o el meñique)."
        elif "abduction_rules" in error_type:
            hand = "izquierda" if "izquierda" in error_type else "derecha"
            if "dedos_" in error_type:
                parts = error_type.split("_")
                if len(parts) >= 4:
                    finger1, finger2 = parts[-2], parts[-1]
                    finger1_name = self.finger_names.get(finger1, finger1)
                    finger2_name = self.finger_names.get(finger2, finger2)
                    return f"Ángulo excesivo (>60°) entre dedos {finger1_name}-{finger2_name} en mano {hand}"
            return f"Error de abducción en mano {hand}"
        return error_type