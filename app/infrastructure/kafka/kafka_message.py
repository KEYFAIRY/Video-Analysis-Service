from dataclasses import dataclass

@dataclass
class KafkaMessage:
    uid: str
    practice_id: int
    date: str
    time: str
    message: str
    scale: str
    scale_type: str
    duration: int
    reps: int
    bpm: int