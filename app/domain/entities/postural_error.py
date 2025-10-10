from dataclasses import dataclass
from typing import Optional

@dataclass
class PosturalError:
    min_sec_init: str
    min_sec_end: int
    frame: int
    explication: str
    id_practice: int
    id: Optional[int] = None