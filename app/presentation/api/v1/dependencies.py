from functools import lru_cache
from app.domain.services.postural_error_service import PosturalErrorService
from app.application.use_cases.list_errors_by_practice import ListErrorsByPracticeUseCase
from app.infrastructure.repositories.mysql_repo import MySQLPosturalErrorRepository

# Repositories
@lru_cache()
def get_postural_error_repository() -> MySQLPosturalErrorRepository:
    """Get instance of the postural error repository"""
    return MySQLPosturalErrorRepository()

# Services
@lru_cache()
def get_postural_error_service() -> PosturalErrorService:
    """Get instance of the postural error domain service"""
    repo = get_postural_error_repository()
    return PosturalErrorService(repo)

# Use Cases
@lru_cache()
def get_list_errors_by_practice_use_case() -> ListErrorsByPracticeUseCase:
    """Get instance of the use case to list postural errors by practice"""
    service = get_postural_error_service()
    return ListErrorsByPracticeUseCase(service)

# Dependency for FastAPI
def list_errors_by_practice_use_case_dependency():
    """Dependency to inject use case for listing postural errors"""
    return get_list_errors_by_practice_use_case()
