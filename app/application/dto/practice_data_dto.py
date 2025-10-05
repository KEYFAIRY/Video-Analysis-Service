from dataclasses import dataclass

@dataclass
class PracticeDataDTO:
    uid: int
    practice_id: int
    date: str
    time: str
    scale: str
    scale_type: str
    num_postural_errors: int
    num_musical_errors: int
    duration: int
    bpm: int
    figure: float
    octaves: int