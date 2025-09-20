from abc import ABC, abstractmethod

class IVideoRepo(ABC):

    @abstractmethod
    async def read(self, path: str, uid: str, practice_id: str) -> str:
        """Reads the video content and return the content. Currently returns a string because of openCV implementations."""
        pass