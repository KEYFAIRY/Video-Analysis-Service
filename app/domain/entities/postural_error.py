from dataclasses import dataclass
from typing import Optional

@dataclass
class PosturalError:
    id: Optional[int] = None
    min_sec: str
    explication: str
    id_practice: int