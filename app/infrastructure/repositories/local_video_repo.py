import aiofiles
import logging
import os

from app.domain.repositories.i_videos_repo import IVideoRepo

logger = logging.getLogger(__name__)

class LocalVideoRepository(IVideoRepo):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or os.getenv("CONTAINER_VIDEO_PATH", "/app/storage/videos")

    async def read(self, path: str) -> bytes:
        """
        Reads video from container path (mounted from host).
        """
        abs_path = os.path.abspath(path)

        if not abs_path.startswith(self.base_dir):
            raise ValueError(f"Access denied outside of storage dir: {abs_path}")

        try:
            async with aiofiles.open(abs_path, "rb") as f:
                content = await f.read()
            logger.info(f"Video read successfully: {abs_path}")
            return content
        except FileNotFoundError:
            logger.error(f"Video not found at {abs_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading video {abs_path}: {e}", exc_info=True)
            raise
