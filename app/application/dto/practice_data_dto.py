from dataclasses import dataclass

@dataclass
class PracticeDataDTO:
    uid: int
    practice_id: int
    video_route: str
    scale: str
    reps: str