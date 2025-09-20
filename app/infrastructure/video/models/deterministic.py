import os
import random
import torch
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Deterministic seed
RANDOM_SEED = 42

def set_deterministic_environment():
    """Configures deterministic environment for models."""
    # Python random
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    os.environ['PYTHONHASHSEED'] = str(RANDOM_SEED)
    
    # PyTorch (YOLO)
    torch.manual_seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(RANDOM_SEED)
        torch.cuda.manual_seed_all(RANDOM_SEED)
        # Force deterministic behavior
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Environment variables for TensorFlow (MediaPipe)
    os.environ['TF_DETERMINISTIC_OPS'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'