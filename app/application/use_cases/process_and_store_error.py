from typing import List
from app.application.dto.postural_error_dto import PosturalErrorDTO
from app.application.dto.practice_data_dto import PracticeDataDTO
from app.domain.services.mongo_practice_service import MongoPracticeService
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
        mongo_service: MongoPracticeService,
        kafka_producer: KafkaProducer
    ):
        self.postural_service = postural_service
        self.mongo_service = mongo_service
        self.kafka_producer = kafka_producer

    async def execute(self, data: PracticeDataDTO) -> List[PosturalErrorDTO]:
        if not data.uid or not data.practice_id or not data.video_route:
            logger.warning(
                "Validation failed: uid=%s, practice_id=%s, video_route=%s",
                data.uid, data.practice_id, data.video_route
            )
            raise ValidationException("uid, practice_id, and video_route are required")
        
        try:
            # 1️ Procesar y almacenar errores en MySQL
            errors = await self.postural_service.process_and_store_error(data)
            logger.info("Stored %d errors for practice_id=%s", len(errors), data.practice_id)

            # 2️ Actualizar Mongo usando el servicio
            await self.mongo_service.mark_video_done(uid=str(data.uid), id_practice=data.practice_id)
            logger.info("Marked video as done in Mongo for uid=%s, practice_id=%s", data.uid, data.practice_id)

            # 3️ Publicar mensaje en Kafka (si el producer está habilitado)
            kafka_message = KafkaMessage(
                uid=data.uid,
                practice_id=data.practice_id,
                message="audio_done",
                scale=data.scale,
                video_route=data.video_route,
                reps=data.reps,
            )
            
            logger.debug("Prepared Kafka message: %s", kafka_message)
            
            await self.kafka_producer.publish_message(topic=settings.KAFKA_OUTPUT_TOPIC, message=kafka_message)

            # 4️ Mapear a DTOs
            return [
                PosturalErrorDTO(
                    min_sec=e.min_sec,
                    explication=e.explication
                ) for e in errors
            ]

        except Exception as e:
            logger.error("Error processing and storing practice", exc_info=True)
            raise DatabaseConnectionException(f"Failed to process practice: {str(e)}")
