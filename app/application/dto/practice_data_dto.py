from dataclasses import dataclass

@dataclass
class PracticeDataDTO:
    uid: int
    practice_id: int
    video_route: str
    scale: str
    scale_type: str
    reps: str
    bpm: int