from typing import List
import logging
from app.domain.entities.postural_error import PosturalError
from app.domain.entities.practice_data import PracticeData
from app.domain.repositories.i_mysql_repo import IMySQLRepo
from app.domain.repositories.i_videos_repo import IVideoRepo
from app.infrastructure.video.analyzer import process_video

logger = logging.getLogger(__name__)


class PosturalErrorService:
    """Domain service for management of postural errors"""

    def __init__(self, posture_repo: IMySQLRepo, video_repo: IVideoRepo):
        self.posture_repo = posture_repo
        self.video_repo = video_repo

    async def list_errors_by_practice(self, id_practice: int) -> List[PosturalError]:
        try:
            errors = await self.posture_repo.list_by_practice_id(id_practice)
            logger.info(
                "Fetched %d errors for practice_id=%s",
                len(errors),
                id_practice,
                extra={"practice_id": id_practice, "count": len(errors)},
            )
            return errors
        except Exception as e:
            logger.error(
                "Error fetching errors for practice_id=%s",
                id_practice,
                exc_info=True,
                extra={"practice_id": id_practice},
            )
            raise

    async def process_and_store_error(self, data: PracticeData) -> List[PosturalError]:
        uid = data.uid
        practice_id = data.practice_id
        video_route = data.video_route
        scale = data.scale
        reps = data.reps

        try:
            logger.info(
                "Processing errors for uid=%s, practice_id=%s, video=%s, scale=%s, reps=%s",
                uid,
                practice_id,
                video_route,
                scale,
                reps,
                extra={
                    "uid": uid,
                    "practice_id": practice_id,
                    "video_route": video_route,
                    "scale": scale,
                    "reps": reps,
                },
            )
            
            # Analizar el video y extraer errores
            errors = process_video(video_route, practice_id)
            
            for error in errors:
                await self.posture_repo.create(error)

            logger.info(
                "Finished processing errors for uid=%s, practice_id=%s. Stored=%d",
                uid,
                practice_id,
                len(errors),
                extra={"uid": uid, "practice_id": practice_id, "stored": len(errors)},
            )

            return errors

        except Exception as e:
            logger.error(
                "Error processing/storing errors for uid=%s, practice_id=%s",
                uid,
                practice_id,
                exc_info=True,
                extra={"uid": uid, "practice_id": practice_id},
            )
            raise
