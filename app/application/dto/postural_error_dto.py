from dataclasses import dataclass

@dataclass
class PosturalErrorDTO:
    min_sec: str
    frame: int
    explication: str