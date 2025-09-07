import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.application.use_cases.process_and_store_error import ProcessAndStoreErrorUseCase
from app.domain.services.mongo_practice_service import MongoPracticeService
from app.domain.services.postural_error_service import PosturalErrorService
from app.infrastructure.kafka.kafka_message import KafkaMessage
from app.infrastructure.kafka.kafka_producer import KafkaProducer
from app.infrastructure.repositories.mongo_repo import MongoRepo
from app.application.dto.practice_data_dto import PracticeDataDTO
from app.infrastructure.repositories.mysql_repo import MySQLPosturalErrorRepository

logger = logging.getLogger(__name__)


async def start_kafka_consumer(kafka_producer: KafkaProducer):
    # Inicializar dependencias
    mysql_repo = MySQLPosturalErrorRepository()
    mongo_repo = MongoRepo()

    postural_service = PosturalErrorService(mysql_repo)
    mongo_service = MongoPracticeService(mongo_repo)

    use_case = ProcessAndStoreErrorUseCase(
        postural_service=postural_service,
        mongo_service=mongo_service,
        kafka_producer=kafka_producer,
    )

    consumer = AIOKafkaConsumer(
        settings.KAFKA_INPUT_TOPIC,
        bootstrap_servers=settings.KAFKA_BROKER,
        enable_auto_commit=True,
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        group_id=None,
    )

    await consumer.start()
    try:
        logger.info("Kafka consumer started")
        async for msg in consumer:
            try:
                decoded = msg.value.decode()
                logger.info(f"Received raw message: {decoded}")

                # JSON → KafkaMessage
                data = json.loads(decoded)
                kafka_msg = KafkaMessage(**data) 
                
                dto = PracticeDataDTO(
                    uid=kafka_msg.uid,
                    practice_id=kafka_msg.practice_id,
                    video_route=kafka_msg.video_route,
                    scale=kafka_msg.scale,
                    reps=kafka_msg.reps,
                )

                # Ejecutar caso de uso
                errors = await use_case.execute(dto)
                logger.info(f"Processed KafkaMessage with {len(errors)} errors")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")
