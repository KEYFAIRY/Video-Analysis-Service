from abc import ABC, abstractmethod
from typing import List

from app.application.dto.postural_error_dto import PosturalErrorDTO


class PosturalErrorServiceInterface(ABC):

    @abstractmethod
    async def list_errors(self, id_practice: int) -> List[PosturalErrorDTO]:
        """Lists postural errors for a specific practice."""
        pass

    @abstractmethod
    async def create_error(self, postural_error: PosturalErrorDTO) -> PosturalErrorDTO:
        """Creates a new postural error."""
        pass
