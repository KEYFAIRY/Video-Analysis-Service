from dataclasses import dataclass

@dataclass
class KafkaMessage:
    uid: str
    practice_id: int
    message: str
    scale: str
    scale_type: str
    reps: str
    bpm: int