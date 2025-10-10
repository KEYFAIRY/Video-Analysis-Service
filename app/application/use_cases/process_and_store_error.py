from typing import List
from app.application.dto.postural_error_dto import PosturalErrorDTO
from app.application.dto.practice_data_dto import PracticeDataDTO
from app.domain.entities.practice_data import PracticeData
from app.domain.services.metadata_practice_service import MetadataPracticeService 
from app.domain.services.postural_error_service import PosturalErrorService
from app.infrastructure.kafka.kafka_message import KafkaMessage
from app.core.exceptions import DatabaseConnectionException, ValidationException
from app.infrastructure.kafka.kafka_producer import KafkaProducer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ProcessAndStoreErrorUseCase:
    """Use case to process a practice video, store MySQL errors, update Mongo, publish Kafka"""

    def __init__(
        self, 
        postural_service: PosturalErrorService,
        mongo_service: MetadataPracticeService,
        kafka_producer: KafkaProducer
    ):
        self.postural_service = postural_service
        self.mongo_service = mongo_service
        self.kafka_producer = kafka_producer

    async def execute(self, data: PracticeDataDTO) -> List[PosturalErrorDTO]:
        if not data.uid or not data.practice_id:
            logger.warning(
                "Validation failed: uid=%s, practice_id=%s",
                data.uid, data.practice_id
            )
            raise ValidationException("uid and practice_id are required")

        try:
            # 1️ Process and store errors in MySQL
            practice_data = PracticeData(
                uid=data.uid,
                practice_id=data.practice_id,
                scale=data.scale,
                bpm=data.bpm,
                figure=data.figure,
                octaves=data.octaves,
            )
            errors = await self.postural_service.process_and_store_error(practice_data)
            logger.info("Stored %d errors for practice_id=%s", len(errors), data.practice_id)

            # 2️ Update metadata in Mongo
            await self.mongo_service.mark_video_done(uid=str(data.uid), id_practice=data.practice_id)
            logger.info("Marked video as done in Mongo for uid=%s, practice_id=%s", data.uid, data.practice_id)

            # 3️ Publish message to kafka topic
            kafka_message = KafkaMessage(
                uid=data.uid,
                practice_id=data.practice_id,
                date=data.date,
                time=data.time,
                message="video_done",
                scale=data.scale,
                scale_type=data.scale_type,
                duration=data.duration,
                bpm=data.bpm,
                figure=data.figure,
                octaves=data.octaves,
            )
            
            logger.info("Prepared Kafka message: %s", kafka_message)
            
            await self.kafka_producer.publish_message(topic=settings.KAFKA_OUTPUT_TOPIC, message=kafka_message)

            # 4️ Map to DTOs
            return [
                PosturalErrorDTO(
                    min_sec_init=e.min_sec_init,
                    min_sec_end=e.min_sec_end,
                    frame=e.frame,
                    explication=e.explication
                ) for e in errors
            ]

        except Exception as e:
            logger.error("Error processing and storing practice", exc_info=True)
            raise DatabaseConnectionException(f"Failed to process practice: {str(e)}")
