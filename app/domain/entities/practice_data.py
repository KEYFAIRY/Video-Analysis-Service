from dataclasses import dataclass

@dataclass
class PracticeData:
    uid: int
    practice_id: int
    scale: str
    bpm: int
    figure: float
    octaves: int