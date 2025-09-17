import cv2
import numpy as np
from typing import NamedTuple, List, Tuple
from ..utils.math_utils import distance_between_points
import logging

logger = logging.getLogger(__name__)

# Configuración
MIN_HAND_DISTANCE = 100
MIN_ELBOW_CONFIDENCE = 0.5
MIN_HAND_LANDMARKS_VISIBLE = 18

class FrameData(NamedTuple):
    """Datos extraídos de un frame válido"""
    is_valid: bool
    hands_data: List[Tuple]
    elbows_data: dict
    frame_info: dict

class FrameValidator:
    
    def validate_frame(self, frame, yolo_model, hands_detector) -> FrameData:
        """Procesa frame completo"""
        h, w = frame.shape[:2]
        detected_errors = []
        elbows = {}
        
        # ===== DETECCIÓN DE CODOS CON YOLO =====
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
        
        # ===== DETECCIÓN DE MANOS CON MEDIAPIPE =====
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands_detector.process(rgb)
        manos_detectadas = []
        hands_valid = True
        
        if res.multi_hand_landmarks:
            for hand_landmarks in res.multi_hand_landmarks:
                is_valid, num_visible, avg_conf = self._validate_hand_quality(hand_landmarks, w, h)
                
                if is_valid:
                    lm = [(int(p.x * w), int(p.y * h)) for p in hand_landmarks.landmark]
                    wrist = lm[0]
                    middle_mcp = lm[9]
                    manos_detectadas.append((wrist[0], wrist, middle_mcp, hand_landmarks, lm))
                else:
                    hands_valid = False
        
        # ===== VALIDACIONES COMPLETAS =====
        is_valid = self._validate_all_conditions(frame, manos_detectadas, elbows_detected, yolo_valid, hands_valid)
        
        return FrameData(
            is_valid=is_valid,
            hands_data=manos_detectadas,
            elbows_data=elbows,
            frame_info={"width": w, "height": h}
        )
    
    def _validate_hand_quality(self, hand_landmarks, w, h):
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
    
    def _validate_all_conditions(self, frame, manos_detectadas, elbows_detected, yolo_valid, hands_valid):
        # 1. Validación básica de detecciones
        if len(manos_detectadas) != 2 or len(elbows_detected) != 2 or not yolo_valid or not hands_valid:
            return False
        
        # 2. Validación de posicionamiento
        if not self._validate_hands_positioning(manos_detectadas):
            return False
        
        # 3. Validación de obstrucciones
        if self._detect_obstruction_in_regions(frame, elbows_detected, manos_detectadas):
            return False
        
        # 4. Validación de distancia entre muñecas
        wrist1 = manos_detectadas[0][1]
        wrist2 = manos_detectadas[1][1]
        dist = distance_between_points(wrist1, wrist2)
        if dist < MIN_HAND_DISTANCE:
            return False
        
        return True
    
    def _validate_hands_positioning(self, manos_detectadas):
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
    
    def _detect_obstruction_in_regions(self, frame, elbows_detected, manos_detectadas):
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