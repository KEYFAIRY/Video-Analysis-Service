from typing import List
from app.application.dto.postural_error_dto import PosturalErrorDTO
from app.core.exceptions import DatabaseConnectionException, ValidationException
import logging

from app.domain.services.postural_error_service import PosturalErrorService

logger = logging.getLogger(__name__)


class ListErrorsByPracticeUseCase:
    """Use case to list postural errors filtered by practice ID"""

    def __init__(self, posture_service: PosturalErrorService):
        self.posture_service = posture_service

    async def execute(self, id_practice: int) -> List[PosturalErrorDTO]:
        logger.debug(f"Executing use case ListErrorsByPracticeUseCase with id_practice={id_practice}")

        if not id_practice:
            logger.warning("Validation failed: id_practice was not provided")
            raise ValidationException("id_practice is required")

        try:
            errors = await self.posture_service.list_errors_by_practice(id_practice)
            logger.info(f"Retrieved {len(errors)} errors for practice id={id_practice}")

            # Map domain entities to DTOs
            return [
                PosturalErrorDTO(
                    min_sec=e.min_sec,
                    frame=e.frame,
                    explication=e.explication
                )
                for e in errors
            ]

        except Exception as e:
            logger.exception(f"Error listing postural errors for practice id={id_practice}")
            raise DatabaseConnectionException(f"Failed to list errors: {str(e)}")
