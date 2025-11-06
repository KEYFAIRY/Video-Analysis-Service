import logging
from app.domain.repositories.i_metadata_repo import IMetadataRepo
from app.infrastructure.monitoring import metrics

logger = logging.getLogger(__name__)

class MetadataPracticeService:
    """Domain service for operations on practices in MongoDB"""

    def __init__(self, mongo_repo: IMetadataRepo):
        self.mongo_repo = mongo_repo

    async def mark_video_done(self, uid: str, id_practice: int) -> bool:
        try:
            updated = await self.mongo_repo.mark_practice_video_done(uid, id_practice)
            if not updated:
                logger.warning(
                    "Mongo update failed",
                    extra={"uid": uid, "practice_id": id_practice}
                )
            else:
                metrics.db_operations.labels(
                        operation='Update', 
                        database='Mongo',
                        status = 'success'
                    ).inc()
                logger.info(
                    "Mongo update successful",
                    extra={"uid": uid, "practice_id": id_practice}
                )
            return updated
        except Exception as e:
            metrics.db_operations.labels(
                        operation='Update', 
                        database='Mongo',
                        status = 'error'
                    ).inc()
            logger.error(
                "Error updating video_done in Mongo",
                exc_info=True,
                extra={"uid": uid, "practice_id": id_practice}
            )
            raise
