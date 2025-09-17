import os
import time
import logging
from typing import Tuple
from app.infrastructure.video.models.deterministic import set_deterministic_environment
import mediapipe as mp
from ultralytics import YOLO

logger = logging.getLogger(__name__)

# Configuración
YOLO_WEIGHTS = "yolo11m-pose.pt"
MIN_HAND_CONFIDENCE = 0.85

class ModelManager:
    """Gestor singleton para modelos de ML"""
    
    _instance = None
    _yolo_model = None
    _hands_detector = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_models(cls) -> Tuple:
        """Obtiene las instancias de los modelos (singleton pattern)."""
        instance = cls()
        if instance._yolo_model is None or instance._hands_detector is None:
            instance._initialize_models()
        return instance._yolo_model, instance._hands_detector
    
    def _initialize_models(self):
        """Inicializa modelos con configuración determinista."""
        set_deterministic_environment()
        
        # YOLO con carga segura
        self._yolo_model = self._safe_load_yolo_model(YOLO_WEIGHTS)
        
        # MediaPipe
        mp_hands = mp.solutions.hands
        self._hands_detector = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=MIN_HAND_CONFIDENCE,
            min_tracking_confidence=MIN_HAND_CONFIDENCE,
        )
        
        logger.info("All models initialized successfully")
    
    def _safe_load_yolo_model(self, weights_path: str, max_retries: int = 3):
        """Carga segura del modelo YOLO con validación y reintentos."""
        for attempt in range(max_retries):
            try:
                if os.path.exists(weights_path):
                    file_size = os.path.getsize(weights_path)
                    if file_size < 1000000:
                        logger.warning(f"Model file {weights_path} appears corrupted. Removing...")
                        os.remove(weights_path)
                
                logger.info(f"Loading YOLO model (attempt {attempt + 1}/{max_retries})")
                yolo_model = YOLO(weights_path)
                
                if hasattr(yolo_model.model, 'eval'):
                    yolo_model.model.eval()
                
                logger.info("YOLO model loaded successfully")
                return yolo_model
                
            except Exception as e:
                logger.error(f"Failed to load YOLO model (attempt {attempt + 1}): {e}")
                
                if os.path.exists(weights_path):
                    try:
                        os.remove(weights_path)
                    except Exception:
                        pass
                
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to load YOLO model after {max_retries} attempts: {e}")
                
                time.sleep(2 ** attempt)
        
        raise RuntimeError("Unable to load YOLO model")