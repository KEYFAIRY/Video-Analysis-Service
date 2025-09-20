from abc import ABC, abstractmethod


class IMetadataRepo(ABC):
    
    @abstractmethod
    async def mark_practice_video_done(self, uid: str, id_practice: int) -> bool:
        """Marks the video as done for a specific practice of a user."""
        pass