from dataclasses import dataclass

@dataclass
class PracticeDataDTO:
    uid: int
    practice_id: int
    scale: str
    scale_type: str
    reps: str
    bpm: int