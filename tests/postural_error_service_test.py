import sys
from unittest.mock import MagicMock

# Mock del módulo analyzer ANTES de cualquier importación
sys.modules['app.infrastructure.video.analyzer'] = MagicMock()

import pytest
from unittest.mock import AsyncMock, patch
from app.domain.entities.postural_error import PosturalError
from app.domain.entities.practice_data import PracticeData
from app.domain.services.postural_error_service import PosturalErrorService
from app.domain.repositories.i_postural_error_repo import IPosturalErrorRepo
from app.domain.repositories.i_videos_repo import IVideoRepo


@pytest.fixture
def mock_posture_repo():
    """Fixture que proporciona un repositorio de errores posturales mock"""
    return AsyncMock(spec=IPosturalErrorRepo)


@pytest.fixture
def mock_video_repo():
    """Fixture que proporciona un repositorio de videos mock"""
    return AsyncMock(spec=IVideoRepo)


@pytest.fixture
def postural_error_service(mock_posture_repo, mock_video_repo):
    """Fixture que proporciona una instancia del servicio"""
    return PosturalErrorService(mock_posture_repo, mock_video_repo)


@pytest.fixture
def valid_practice_data():
    """Fixture que proporciona datos de práctica válidos"""
    return PracticeData(
        uid=123,
        practice_id=1,
        scale="C_MAJOR",
        bpm=60,
        figure=0.25,
        octaves=1
    )


@pytest.fixture
def valid_postural_errors():
    """Fixture que proporciona una lista de errores posturales válidos"""
    return [
        PosturalError(
            min_sec_init="00:01",
            min_sec_end=2,
            frame=30,
            explication="Muñeca caída en mano izquierda",
            id_practice=1
        ),
        PosturalError(
            min_sec_init="00:03",
            min_sec_end=5,
            frame=90,
            explication="Dedos curvados en mano derecha",
            id_practice=1
        ),
        PosturalError(
            min_sec_init="00:05",
            min_sec_end=7,
            frame=150,
            explication="Postura incorrecta del pulgar",
            id_practice=1
        )
    ]


class TestProcessAndStoreError:
    """Suite de pruebas para procesar y almacenar errores posturales"""

    @pytest.mark.asyncio
    @patch('app.domain.services.postural_error_service.process_video')
    async def test_process_video_with_postural_errors(
        self,
        mock_process_video,
        postural_error_service,
        mock_video_repo,
        mock_posture_repo,
        valid_practice_data,
        valid_postural_errors
    ):
        """
        Descripción: El video para analizar contiene errores posturales
        Condiciones: Verificar que el sistema registre correctamente errores posturales
        Resultado esperado: Se retorna la lista de errores posturales identificados
        """
        # Arrange
        video_path = "/path/to/video.mp4"
        mock_video_repo.read.return_value = video_path
        mock_process_video.return_value = valid_postural_errors
        mock_posture_repo.create.return_value = None

        # Act
        result = await postural_error_service.process_and_store_error(valid_practice_data)

        # Assert
        mock_video_repo.read.assert_awaited_once_with(
            valid_practice_data.uid, 
            valid_practice_data.practice_id
        )
        mock_process_video.assert_called_once_with(
            video_path,
            valid_practice_data.practice_id,
            valid_practice_data.bpm,
            valid_practice_data.figure
        )
        
        # Verificar que se intentó crear cada error
        assert mock_posture_repo.create.await_count == len(valid_postural_errors)
        
        # Verificar que se retornaron los errores correctos
        assert len(result) == len(valid_postural_errors)
        assert result == valid_postural_errors
        assert result[0].min_sec_init == "00:01"
        assert result[0].explication == "Muñeca caída en mano izquierda"
        assert result[1].min_sec_init == "00:03"
        assert result[1].explication == "Dedos curvados en mano derecha"
        assert result[2].frame == 150


    @pytest.mark.asyncio
    @patch('app.domain.services.postural_error_service.process_video')
    async def test_process_video_without_postural_errors(
        self,
        mock_process_video,
        postural_error_service,
        mock_video_repo,
        mock_posture_repo,
        valid_practice_data
    ):
        """
        Descripción: El video para analizar no contiene errores posturales, y las manos son visibles
        Condiciones: Verificar que el sistema no registre ningún error postural
        Resultado esperado: Se retorna una lista vacía
        """
        # Arrange
        video_path = "/path/to/video.mp4"
        mock_video_repo.read.return_value = video_path
        mock_process_video.return_value = []

        # Act
        result = await postural_error_service.process_and_store_error(valid_practice_data)

        # Assert
        mock_video_repo.read.assert_awaited_once_with(
            valid_practice_data.uid, 
            valid_practice_data.practice_id
        )
        mock_process_video.assert_called_once_with(
            video_path,
            valid_practice_data.practice_id,
            valid_practice_data.bpm,
            valid_practice_data.figure
        )
        
        # Verificar que no se intentó crear ningún error
        mock_posture_repo.create.assert_not_awaited()
        
        # Verificar que se retornó una lista vacía
        assert result == []
        assert len(result) == 0


    @pytest.mark.asyncio
    @patch('app.domain.services.postural_error_service.process_video')
    async def test_process_video_without_visible_hands(
        self,
        mock_process_video,
        postural_error_service,
        mock_video_repo,
        mock_posture_repo,
        valid_practice_data
    ):
        """
        Descripción: El video para analizar no presenta manos visibles
        Condiciones: Verificar que el sistema no registre ningún error postural
        Resultado esperado: Se retorna una lista vacía
        """
        # Arrange
        video_path = "/path/to/video.mp4"
        mock_video_repo.read.return_value = video_path
        mock_process_video.return_value = []

        # Act
        result = await postural_error_service.process_and_store_error(valid_practice_data)

        # Assert
        mock_video_repo.read.assert_awaited_once_with(
            valid_practice_data.uid, 
            valid_practice_data.practice_id
        )
        mock_process_video.assert_called_once_with(
            video_path,
            valid_practice_data.practice_id,
            valid_practice_data.bpm,
            valid_practice_data.figure
        )
        
        # Verificar que no se intentó crear ningún error
        mock_posture_repo.create.assert_not_awaited()
        
        # Verificar que se retornó una lista vacía
        assert result == []
        assert len(result) == 0