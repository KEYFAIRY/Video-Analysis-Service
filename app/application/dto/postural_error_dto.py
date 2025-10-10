from dataclasses import dataclass

@dataclass
class PosturalErrorDTO:
    min_sec_init: str
    min_sec_end: int
    frame: int
    explication: str