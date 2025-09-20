import logging
import os
from app.domain.repositories.i_videos_repo import IVideoRepo

logger = logging.getLogger(__name__)

class LocalVideoRepository(IVideoRepo):
    """Concrete implementation of IVideoRepo using local filesystem."""
    
    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or os.getenv("CONTAINER_VIDEO_PATH", "/app/storage")

    async def read(self, uid: str, practice_id: str) -> str:
        # currently, returns just the path, because of opencv implementation
        return self.base_dir + f"/{uid}/videos/practice_{practice_id}.mp4"