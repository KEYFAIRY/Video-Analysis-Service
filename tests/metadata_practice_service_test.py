import pytest
from unittest.mock import AsyncMock, patch
from app.domain.services.metadata_practice_service import MetadataPracticeService
from app.domain.repositories.i_metadata_repo import IMetadataRepo


@pytest.fixture
def mock_metadata_repo():
    """Fixture que proporciona un repositorio de metadatos mock"""
    return AsyncMock(spec=IMetadataRepo)


@pytest.fixture
def metadata_practice_service(mock_metadata_repo):
    """Fixture que proporciona una instancia del servicio"""
    return MetadataPracticeService(mock_metadata_repo)


class TestMarkVideoDone:
    """Suite de pruebas para marcar video como procesado"""

    @pytest.mark.asyncio
    @patch('app.domain.services.metadata_practice_service.metrics')
    async def test_mark_video_done_with_existing_practice(
        self,
        mock_metrics,
        metadata_practice_service,
        mock_metadata_repo
    ):
        """
        Descripción: Existe el registro de la práctica en la base de datos de metadatos
        Condiciones: Verificar que el sistema actualice el campo de análisis de video correctamente
        Resultado esperado: Se retorna true
        """
        # Arrange
        uid = "test-uid-123"
        id_practice = 1
        mock_metadata_repo.mark_practice_video_done.return_value = True

        # Act
        result = await metadata_practice_service.mark_video_done(uid, id_practice)

        # Assert
        mock_metadata_repo.mark_practice_video_done.assert_awaited_once_with(uid, id_practice)
        
        # Verificar que se registró la métrica de éxito
        mock_metrics.db_operations.labels.assert_called_with(
            operation='Update',
            database='Mongo',
            status='success'
        )
        mock_metrics.db_operations.labels().inc.assert_called_once()
        
        # Verificar que se retorna True
        assert result is True


    @pytest.mark.asyncio
    @patch('app.domain.services.metadata_practice_service.metrics')
    async def test_mark_video_done_with_nonexistent_practice(
        self,
        mock_metrics,
        metadata_practice_service,
        mock_metadata_repo
    ):
        """
        Descripción: No existe el registro de la práctica en la base de datos de metadatos
        Condiciones: Verificar que el sistema no modifique nada en la base de datos de metadatos
        Resultado esperado: Se retorna false
        """
        # Arrange
        uid = "test-uid-456"
        id_practice = 999
        mock_metadata_repo.mark_practice_video_done.return_value = False

        # Act
        result = await metadata_practice_service.mark_video_done(uid, id_practice)

        # Assert
        mock_metadata_repo.mark_practice_video_done.assert_awaited_once_with(uid, id_practice)
        
        # Verificar que NO se registró la métrica de éxito
        mock_metrics.db_operations.labels.assert_not_called()
        
        # Verificar que se retorna False
        assert result is False