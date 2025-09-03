import json
import logging
from aiokafka import AIOKafkaProducer
from app.infrastructure.kafka.kafka_message import KafkaMessage


logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self, bootstrap_servers: str):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    async def start(self):
        logger.info("Starting Kafka Producer...")
        await self._producer.start()

    async def stop(self):
        logger.info("Stopping Kafka Producer...")
        await self._producer.stop()

    async def publish_message(self, topic: str, message: KafkaMessage):
        """
        Publica un KafkaMessage en un topic
        """
        try:
            payload = message.__dict__  # convertir dataclass → dict
            await self._producer.send_and_wait(topic, payload)
            logger.info("Message published to %s: %s", topic, payload)
        except Exception:
            logger.error("Failed to publish Kafka message", exc_info=True)
            raise
