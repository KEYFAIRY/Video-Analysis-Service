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
    bpm: int
    figure: float
    octaves: int