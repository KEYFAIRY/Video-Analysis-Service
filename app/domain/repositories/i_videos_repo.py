from abc import ABC, abstractmethod

class IVideoRepo(ABC):
    """Abstract repository interface for reading videos."""

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """
        Reads the video content and return the content.
        """
        pass
