# tests/conftest.py
import sys
from unittest.mock import MagicMock

# Mock de módulos pesados que no necesitamos en las pruebas
sys.modules['torch'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['ultralytics'] = MagicMock()
sys.modules['app.infrastructure.video.analyzer'] = MagicMock()
sys.modules['app.infrastructure.video.models.deterministic'] = MagicMock()

# Mock de módulos de monitoreo
sys.modules['prometheus_client'] = MagicMock()
sys.modules['app.infrastructure.monitoring.metrics'] = MagicMock()