from dataclasses import dataclass

@dataclass
class PracticeData:
    uid: int
    practice_id: int
    video_route: str
    scale: str
    reps: str