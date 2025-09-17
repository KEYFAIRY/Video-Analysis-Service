import numpy as np

def angle_between_points(a, b, c):
    """Cálculo de ángulo más preciso y consistente."""
    a, b, c = map(lambda p: np.array(p, dtype=np.float64), (a, b, c))
    ba, bc = a - b, c - b
    
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    
    if norm_ba < 1e-10 or norm_bc < 1e-10:
        return 0.0
    
    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    
    # Redondeo para consistencia numérica
    angle = np.degrees(np.arccos(cos_angle))
    return round(angle, 2)

def distance_between_points(p1, p2):
    """Distancia con precisión consistente."""
    dist = np.linalg.norm(np.array(p1, dtype=np.float64) - np.array(p2, dtype=np.float64))
    return round(dist, 2)