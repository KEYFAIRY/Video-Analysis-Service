import asyncio
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor
from app.domain.entities.postural_error import PosturalError
from app.domain.entities.practice_data import PracticeData
from app.domain.repositories.i_postural_error_repo import IPosturalErrorRepo
from app.domain.repositories.i_videos_repo import IVideoRepo
from app.infrastructure.video.analyzer import process_video

logger = logging.getLogger(__name__)

class PosturalErrorService:
    """Domain service for management of postural errors"""

    def __init__(self, posture_repo: IPosturalErrorRepo, video_repo: IVideoRepo):
        self.posture_repo = posture_repo
        self.video_repo = video_repo
        # Keep original thread pool for video processing
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="video_processing")

    async def process_and_store_error(self, data: PracticeData) -> List[PosturalError]:
        """Processes video to detect postural errors and stores them in the database."""
        uid = data.uid
        practice_id = data.practice_id
        scale = data.scale
        reps = data.reps
        bpm = data.bpm

        try:
            logger.info(
                "Processing errors for uid=%s, practice_id=%s, scale=%s, reps=%s, bpm=%s",
                uid,
                practice_id,
                scale,
                reps,
                bpm,
                extra={"uid": uid, "practice_id": practice_id, "scale": scale, "reps": reps, "bpm": bpm}
            )
            
            # 1. Read video (currently, returns just the path, because of opencv implementation)
            video_path = await self.video_repo.read(uid, practice_id)
            
            # 2. Analyze video in thread pool
            logger.debug(f"Starting video analysis for practice_id={practice_id}")
            loop = asyncio.get_event_loop()
            errors = await loop.run_in_executor(
                self._executor, 
                process_video,
                video_path, 
                practice_id,
                bpm,
            )
            logger.debug(f"Video analysis completed for practice_id={practice_id}, found {len(errors)} errors")

            # 3. Store errors in batches for better performance
            if errors:
                await self._store_errors_batch(errors, practice_id)
            else:
                logger.info(f"No errors found for practice_id={practice_id}")

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

    async def _store_errors_batch(self, errors: List[PosturalError], practice_id: int):
        """Stores errors in batches to optimize database writes."""
        batch_size = 5
        total_errors = len(errors)
        
        logger.debug(f"Storing {total_errors} errors in batches of {batch_size} for practice_id={practice_id}")
        
        for i in range(0, total_errors, batch_size):
            batch = errors[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_errors + batch_size - 1) // batch_size
            
            logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch)} errors)")
            
            tasks = []
            for error in batch:
                task = asyncio.create_task(self.posture_repo.create(error))
                tasks.append(task)
                await asyncio.sleep(0.01)  # 10ms
            
            try:
                await asyncio.gather(*tasks)
                logger.debug(f"Batch {batch_num}/{total_batches} completed successfully")
            except Exception as e:
                logger.error(f"Error in batch {batch_num}/{total_batches}: {e}")
                raise
            
            if i + batch_size < total_errors:
                await asyncio.sleep(0.05)  # 50ms

    def __del__(self):
        """Cleanup del thread pool."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)