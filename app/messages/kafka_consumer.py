import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.structs import TopicPartition
from app.core.config import settings
from app.application.use_cases.process_and_store_error import ProcessAndStoreErrorUseCase
from app.domain.services.metadata_practice_service import MetadataPracticeService 
from app.domain.services.postural_error_service import PosturalErrorService
from app.infrastructure.repositories.local_video_repo import LocalVideoRepository
from app.infrastructure.repositories.mongo_metadata_repo import MongoMetadataRepo
from app.application.dto.practice_data_dto import PracticeDataDTO
from app.infrastructure.repositories.mysql_postural_error_repo import MySQLPosturalErrorRepository
from app.messages.kafka_message import KafkaMessage
from app.messages.kafka_producer import KafkaProducer
from app.infrastructure.monitoring import metrics

logger = logging.getLogger(__name__)

MAX_CONCURRENT_VIDEOS = 3
semaphore = asyncio.Semaphore(MAX_CONCURRENT_VIDEOS)

async def start_kafka_consumer(kafka_producer: KafkaProducer):
    mysql_repo = MySQLPosturalErrorRepository()
    mongo_repo = MongoMetadataRepo()
    video_repo = LocalVideoRepository()

    postural_service = PosturalErrorService(mysql_repo, video_repo)
    mongo_service = MetadataPracticeService(mongo_repo)

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

        async def process_message(tp: TopicPartition, dto: PracticeDataDTO):
            async with semaphore:
                try:
                    errors = await use_case.execute(dto)

                    topic_label = getattr(tp, 'topic', settings.KAFKA_INPUT_TOPIC)
                    metrics.kafka_messages_processed.labels(
                        topic=topic_label, 
                        status='success'
                    ).inc()
                    logger.info(f"Processed KafkaMessage with {len(errors)} errors")
                    await consumer.commit()
                except Exception as e:
                    metrics.kafka_messages_processed.labels(
                        topic=topic_label, 
                        status='error'
                    ).inc()
                    logger.error(f"Error processing message in background: {e}", exc_info=True)

        async for msg in consumer:
            try:
                decoded = msg.value.decode()
                logger.info(f"Received raw message: {decoded}")

                topic_label = getattr(msg, 'topic', settings.KAFKA_INPUT_TOPIC)
                metrics.kafka_messages_polled.labels(
                    topic=topic_label
                ).inc()

                data = json.loads(decoded)
                kafka_msg = KafkaMessage(**data)

                dto = PracticeDataDTO(
                    uid=kafka_msg.uid,
                    practice_id=kafka_msg.practice_id,
                    date=kafka_msg.date,
                    time=kafka_msg.time,
                    scale=kafka_msg.scale,
                    scale_type=kafka_msg.scale_type,
                    num_postural_errors=0,  # Placeholder, actual value not in KafkaMessage
                    num_musical_errors=0,  # Placeholder, actual value not in KafkaMessage
                    duration=kafka_msg.duration,
                    bpm=kafka_msg.bpm,
                    figure=kafka_msg.figure,
                    octaves=kafka_msg.octaves,
                )

                tp = TopicPartition(msg.topic, msg.partition)

                # Crear la tarea y guardarla en la lista
                task = asyncio.create_task(process_message(tp, dto))
                tasks.append(task)

            except Exception as e:
                topic_label = getattr(msg, 'topic', settings.KAFKA_INPUT_TOPIC)
                metrics.kafka_messages_processed.labels(
                    topic=topic_label, 
                    status='error'
                ).inc()
                logger.error(f"Error processing message: {e}", exc_info=True)

    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")

        if tasks:
            logger.info("Waiting for all background tasks to finish...")
            await asyncio.gather(*tasks)  # Espera que todas las tareas terminen
            logger.info("All background tasks finished.")
