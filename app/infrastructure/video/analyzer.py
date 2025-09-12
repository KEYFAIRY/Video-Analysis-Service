from app.domain.entities.postural_error import PosturalError
import cv2
import mediapipe as mp
import numpy as np
from ultralytics import YOLO
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Configuración
YOLO_WEIGHTS = "yolo11m-pose.pt"
FRAMES_PER_SECOND_TO_PROCESS = 10

# Cargar modelo YOLO pose una sola vez
yolo_model = YOLO(YOLO_WEIGHTS)

mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def angle_between_points(a, b, c):
    a, b, c = map(lambda p: np.array(p, dtype=np.float32), (a, b, c))
    ba, bc = a - b, c - b
    if np.linalg.norm(ba) == 0 or np.linalg.norm(bc) == 0:
        return 0.0
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))

def format_seconds_to_mmss(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    mm, ss = divmod(td.seconds, 60)
    return f"{mm:02}:{ss:02}"

def wrist_rules(wrist, mid_wrist, elbow, hand_side):
    if elbow is None:
        return None
    ang = angle_between_points(elbow, wrist, mid_wrist)
    if ang < 155:
        return f"Mano {hand_side}: Flexión radial/cubital ({ang:.1f}° <155°)"
    return None

def abduction_rules(wrist, fingers, hand_side):
    events = []
    for i in range(len(fingers) - 1):
        a, c = fingers[i], fingers[i + 1]
        ang = angle_between_points(a, wrist, c)
        if ang > 60:
            events.append(f"Mano {hand_side}: Ángulo dedos {i}-{i+1} ({ang:.1f}° >60°)")
    return events

def process_video(video_path: str, practice_id: int) -> list[PosturalError]:
    """
    Process a video and return a list of detected postural errors.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_idx = 0
    results = []
    last_second = -1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frames_interval = int(fps / FRAMES_PER_SECOND_TO_PROCESS) if FRAMES_PER_SECOND_TO_PROCESS > 0 else int(fps)
        if frame_idx % frames_interval != 0:
            frame_idx += 1
            continue

        h, w = frame.shape[:2]
        elbows = {}
        events = []

        # YOLO pose → codos
        yolo_res = yolo_model.predict(frame, imgsz=640, conf=0.5, verbose=False)
        for r in yolo_res:
            if r.keypoints is None:
                continue
            kpts = r.keypoints.xy.cpu().numpy()
            for person in kpts:
                elbows["Izquierda"] = tuple(map(int, person[7]))
                elbows["Derecha"] = tuple(map(int, person[8]))

        # MediaPipe hands → manos
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands_detector.process(rgb)
        if res.multi_hand_landmarks:
            for hand_landmarks in res.multi_hand_landmarks:
                lm = [(int(p.x * w), int(p.y * h)) for p in hand_landmarks.landmark]
                wrist, middle_mcp = lm[0], lm[9]
                mid_wrist = ((wrist[0]+middle_mcp[0])//2, (wrist[1]+middle_mcp[1])//2)

                hand_side = "Izquierda" if wrist[0] < w/2 else "Derecha"

                elbow = elbows.get(hand_side, None)
                wr = wrist_rules(wrist, mid_wrist, elbow, hand_side)
                if wr:
                    events.append(wr)

                tip_idx = [4,8,12,16,20]
                fingers = [lm[i] for i in tip_idx]
                events.extend(abduction_rules(wrist, fingers, hand_side))

        time_s = frame_idx / fps if fps > 0 else 0
        second = int(time_s)

        if events and second != last_second:
            mmss = format_seconds_to_mmss(time_s)
            error = PosturalError(
                min_sec=mmss,
                frame=frame_idx,
                explication=events[0],
                id_practice=practice_id
            )
            results.append(error)
            last_second = second

        frame_idx += 1

    cap.release()
    return results