from dataclasses import dataclass

@dataclass
class PosturalError:
    id: int
    min_sec: str
    explication: str
    id_practice: int