from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.postural_error import PosturalError


class IPosturalErrorRepo(ABC):

    @abstractmethod
    async def create(self, postural_error: PosturalError) -> PosturalError:
        """Creates a new postural error."""
        pass
