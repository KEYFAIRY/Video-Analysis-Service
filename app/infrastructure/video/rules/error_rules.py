from typing import List, Dict
from app.infrastructure.video.detection.validators import FrameData
from ..utils.math_utils import angle_between_points
import logging

logger = logging.getLogger(__name__)

class ErrorDetector:
    """Error detection"""

    def detect_errors(self, frame_data: FrameData) -> List[Dict]:
        """Detects errors"""
        if not frame_data.is_valid:
            return []

        detected_errors = []
        manos_detectadas = sorted(frame_data.hands_data, key=lambda m: m[0])

        for i, (_, wrist, middle_mcp, hand_landmarks, lm) in enumerate(manos_detectadas):
            hand_side = "izquierda" if i == 0 else "derecha"
            elbow = frame_data.elbows_data.get(hand_side, None)

            # Wrist rules
            wrist_errors = self._wrist_rules(wrist, middle_mcp, elbow, hand_side)
            detected_errors.extend(wrist_errors)

            # Abduction rules
            tip_idx = [4, 8, 12, 16, 20]
            fingers = [lm[j] for j in tip_idx]
            abduction_errors = self._abduction_rules(wrist, fingers, hand_side)
            detected_errors.extend(abduction_errors)

        return detected_errors

    def _wrist_rules(self, wrist, mid_wrist, elbow, hand_side):
        if elbow is None:
            return []
        ang = angle_between_points(elbow, wrist, mid_wrist)
        if ang < 155:
            return [{
                "type": f"wrist_rules_{hand_side.lower()}",
                "angle": ang
            }]
        return []

    def _abduction_rules(self, wrist, fingers, hand_side):
        errors = []
        for i in range(len(fingers) - 1):
            a, c = fingers[i], fingers[i + 1]
            ang = angle_between_points(a, wrist, c)
            if ang > 60:
                errors.append({
                    "type": f"abduction_rules_{hand_side.lower()}_dedos_{i}_{i+1}",
                    "angle": ang
                })
        return errors
