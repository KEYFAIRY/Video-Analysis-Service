from dataclasses import dataclass

@dataclass
class KafkaMessage:
    uid: str
    practice_id: int
    message: str
    scale: str
    video_route: str
    reps: str