from dataclasses import dataclass
from typing import Optional

@dataclass
class PosturalError:
    min_sec: str
    explication: str
    id_practice: int
    id: Optional[int] = None