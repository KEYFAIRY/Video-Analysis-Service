from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.postural_error import PosturalError


class IMySQLRepo(ABC):
    
    # TODO: This method is for reports service
    @abstractmethod
    async def list_by_practice_id(self, id_practice: int) -> List[PosturalError]:
        """Lists postural errors by practice ID."""
        pass

    @abstractmethod
    async def create(self, postural_error: PosturalError) -> PosturalError:
        """Creates a new postural error."""
        pass
