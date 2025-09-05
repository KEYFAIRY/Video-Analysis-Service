from fastapi import APIRouter, Depends, status
from typing import List
import logging

from app.presentation.api.v1.dependencies import list_errors_by_practice_use_case_dependency
from app.presentation.schemas.common_schema import StandardResponse
from app.application.use_cases.list_errors_by_practice import ListErrorsByPracticeUseCase
from app.presentation.schemas.postural_error_schema import PosturalErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/errors", tags=["Postural Errors"])


@router.get(
    "/practice/{practice_id}",
    response_model=StandardResponse[List[PosturalErrorResponse]],
    status_code=status.HTTP_200_OK,
    summary="List postural errors by practice",
    description="Retrieve all poastural errors detected for a given practice ID"
)
async def list_errors_by_practice(
    practice_id: int,
    use_case: ListErrorsByPracticeUseCase = Depends(list_errors_by_practice_use_case_dependency)
):
    logger.info(f"Fetching postural errors for practice_id={practice_id}")

    # Ejecutar caso de uso
    errors_dto = await use_case.execute(practice_id)

    # Mapear DTO -> Response Schema
    errors_response = [
        PosturalErrorResponse(
            min_sec=e.min_sec,
            explication=e.explication
        )
        for e in errors_dto
    ]

    logger.info(f"Found {len(errors_response)} errors for practice_id={practice_id}")
    return StandardResponse.success(
        data=errors_response,
        message=f"Found {len(errors_response)} errors"
    )