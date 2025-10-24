import cv2
from typing import NamedTuple, List, Tuple
import logging

logger = logging.getLogger(__name__)

MIN_ELBOW_CONFIDENCE = 0.5
MIN_HAND_LANDMARKS_VISIBLE = 18
MAX_HANDS_OVERLAP_RATIO = 0.5  # 50% del área de la mano más pequeña

class FrameData(NamedTuple):
    """Extracted data from a valid frame"""
    is_valid: bool
    hands_data: List[Tuple]
    elbows_data: dict
    frame_info: dict

class FrameValidator:
    
    def validate_frame(self, frame, yolo_model, hands_detector) -> FrameData:
        """Process complete frame"""
        h, w = frame.shape[:2]
        elbows = {}
        
        # ===== ELBOW DETECTION WITH YOLO =====
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
                
                if left_conf > MIN_ELBOW_CONFIDENCE and right_conf > MIN_ELBOW_CONFIDENCE:
                    elbows_detected.extend([left_elbow, right_elbow])
                    elbows["izquierda"] = left_elbow
                    elbows["derecha"] = right_elbow
                    yolo_valid = True
        
        # ===== HAND DETECTION WITH MEDIAPIPE =====
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands_detector.process(rgb)
        detected_hands = []
        hands_valid = True
        
        if res.multi_hand_landmarks:
            for hand_landmarks in res.multi_hand_landmarks:
                is_valid, num_visible, avg_conf = self._validate_hand_quality(hand_landmarks, w, h)
                
                if is_valid:
                    lm = [(int(p.x * w), int(p.y * h)) for p in hand_landmarks.landmark]
                    wrist = lm[0]
                    middle_mcp = lm[9]
                    detected_hands.append((wrist[0], wrist, middle_mcp, hand_landmarks, lm))
                else:
                    hands_valid = False
        
        # ===== ENTIRE VALIDATIONS =====
        is_valid = self._validate_all_conditions(frame, detected_hands, elbows_detected, yolo_valid, hands_valid)
        
        return FrameData(
            is_valid=is_valid,
            hands_data=detected_hands,
            elbows_data=elbows,
            frame_info={"width": w, "height": h}
        )
    
    def _validate_hand_quality(self, hand_landmarks, w, h):
        visible_landmarks = 0
        confidence_sum = 0
        
        for landmark in hand_landmarks.landmark:
            x, y = int(landmark.x * w), int(landmark.y * h)
            # Validate landmark is within frame bounds
            if 0 <= x < w and 0 <= y < h:
                # Check visibility if available
                if hasattr(landmark, 'visibility') and landmark.visibility > 0.5:
                    visible_landmarks += 1
                    confidence_sum += landmark.visibility
                else:
                    visible_landmarks += 1
        
        # Calculate average confidence
        avg_confidence = confidence_sum / visible_landmarks if visible_landmarks > 0 else 0
        is_valid = visible_landmarks >= MIN_HAND_LANDMARKS_VISIBLE
        return is_valid, visible_landmarks, avg_confidence
    
    def _validate_all_conditions(self, frame, detected_hands, elbows_detected, yolo_valid, hands_valid):
        # 1. Basic detection validations
        if len(detected_hands) != 2 or len(elbows_detected) != 2 or not yolo_valid or not hands_valid:
            return False
        
        # 2. Validación de superposición de manos
        if self._hands_are_superposed(detected_hands):
            return False
        
        return True

    def _hands_are_superposed(self, detected_hands):
        if len(detected_hands) != 2:
            return False

        # Obtener bounding boxes de cada mano usando landmarks
        def get_bbox(lm):
            xs = [p[0] for p in lm]
            ys = [p[1] for p in lm]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            return (x_min, y_min, x_max, y_max)

        bbox1 = get_bbox(detected_hands[0][4])  # lm de mano 1
        bbox2 = get_bbox(detected_hands[1][4])  # lm de mano 2

        # Calcular área de intersección
        xA = max(bbox1[0], bbox2[0])
        yA = max(bbox1[1], bbox2[1])
        xB = min(bbox1[2], bbox2[2])
        yB = min(bbox1[3], bbox2[3])

        inter_width = max(0, xB - xA)
        inter_height = max(0, yB - yA)
        inter_area = inter_width * inter_height

        # Área de la mano más pequeña
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        min_area = min(area1, area2)

        # Si el área de intersección es mayor al 50% del área de una mano, están superpuestas
        if min_area > 0 and inter_area / min_area > MAX_HANDS_OVERLAP_RATIO:
            return True
        return False