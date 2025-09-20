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
from app.infrastructure.repositories.local_video_repo import LocalVideoRepository
from app.infrastructure.repositories.mongo_metadata_repo import MongoMetadataRepo
from app.application.dto.practice_data_dto import PracticeDataDTO
from app.infrastructure.repositories.mysql_repo import MySQLPosturalErrorRepository

logger = logging.getLogger(__name__)

MAX_CONCURRENT_VIDEOS = 3
semaphore = asyncio.Semaphore(MAX_CONCURRENT_VIDEOS)

async def start_kafka_consumer(kafka_producer: KafkaProducer):
    mysql_repo = MySQLPosturalErrorRepository()
    mongo_repo = MongoMetadataRepo()
    video_repo = LocalVideoRepository()

    postural_service = PosturalErrorService(mysql_repo, video_repo)
    mongo_service = MongoPracticeService(mongo_repo)

    use_case = ProcessAndStoreErrorUseCase(
        postural_service=postural_service,
        mongo_service=mongo_service,
        kafka_producer=kafka_producer,
    )

    consumer = AIOKafkaConsumer(
        settings.KAFKA_INPUT_TOPIC,
        bootstrap_servers=settings.KAFKA_BROKER,
        enable_auto_commit=False,
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        group_id=settings.KAFKA_GROUP_ID,
    )

    await consumer.start()
    tasks = []
    try:
        logger.info("Kafka consumer started")

        async def process_message(dto: PracticeDataDTO):
            async with semaphore:
                try:
                    errors = await use_case.execute(dto)
                    logger.info(f"Processed KafkaMessage with {len(errors)} errors")
                    await consumer.commit()
                except Exception as e:
                    logger.error(f"Error processing message in background: {e}", exc_info=True)

        async for msg in consumer:
            try:
                decoded = msg.value.decode()
                logger.info(f"Received raw message: {decoded}")

                data = json.loads(decoded)
                kafka_msg = KafkaMessage(**data)

                dto = PracticeDataDTO(
                    uid=kafka_msg.uid,
                    practice_id=kafka_msg.practice_id,
                    scale=kafka_msg.scale,
                    scale_type=kafka_msg.scale_type,
                    reps=kafka_msg.reps,
                    bpm=kafka_msg.bpm,
                )

                # Crear la tarea y guardarla en la lista
                task = asyncio.create_task(process_message(dto))
                tasks.append(task)

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")

        if tasks:
            logger.info("Waiting for all background tasks to finish...")
            await asyncio.gather(*tasks)  # Espera que todas las tareas terminen
            logger.info("All background tasks finished.")
