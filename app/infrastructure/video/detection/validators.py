import cv2
import numpy as np
from typing import NamedTuple, List, Tuple
from ..utils.math_utils import distance_between_points
import logging

logger = logging.getLogger(__name__)

# Configuration
MIN_HAND_DISTANCE = 100
MIN_ELBOW_CONFIDENCE = 0.5
MIN_HAND_LANDMARKS_VISIBLE = 18

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
        
        # 2. Positional validation of hands
        if not self._validate_hands_positioning(detected_hands):
            return False
        
        # 3. Obstruction validation
        if self._detect_obstruction_in_regions(frame, elbows_detected, detected_hands):
            return False
        
        # 4. Validation of minimum distance between wrists
        wrist1 = detected_hands[0][1]
        wrist2 = detected_hands[1][1]
        dist = distance_between_points(wrist1, wrist2)
        if dist < MIN_HAND_DISTANCE:
            return False
        
        return True
    
    def _validate_hands_positioning(self, detected_hands):
        if len(detected_hands) != 2:
            return False
        
        sorted_hands = sorted(detected_hands, key=lambda m: m[0])
        left, right = sorted_hands
        
        dist_horizontal = abs(right[0] - left[0])
        if dist_horizontal < MIN_HAND_DISTANCE:
            return False
        
        dist_vertical = abs(right[1][1] - left[1][1])
        if dist_vertical > 80:
            return False
        
        return True
    
    def _detect_obstruction_in_regions(self, frame, elbows_detected, detected_hands):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        regions_of_interest = []
        
        # Hand regions
        for _, wrist, _, _, _ in detected_hands:
            x, y = wrist
            x1, y1 = max(0, x-50), max(0, y-50)
            x2, y2 = min(frame.shape[1], x+50), min(frame.shape[0], y+50)
            regions_of_interest.append((x1, y1, x2, y2, "mano"))
        
        # Elbow regions
        for elbow in elbows_detected:
            x, y = elbow
            x1, y1 = max(0, x-40), max(0, y-40)
            x2, y2 = min(frame.shape[1], x+40), min(frame.shape[0], y+40)
            regions_of_interest.append((x1, y1, x2, y2, "codo"))
        
        # Obstruction detection using contours
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