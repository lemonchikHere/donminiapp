from unittest.mock import patch, MagicMock
import pytest
from src.api.routes.search import search_properties, PropertySearchRequest
import os

# Set a dummy API key for testing
os.environ["OPENAI_API_KEY"] = "test"

@pytest.mark.asyncio
@patch('openai.embeddings.create')
async def test_search_query_with_zero_rooms(mock_openai_create):
    # Arrange
    mock_response = MagicMock()
    mock_embedding = [0.1] * 1536
    mock_response.data = [MagicMock(embedding=mock_embedding)]
    mock_openai_create.return_value = mock_response

    search_request = PropertySearchRequest(
        rooms=0,
        query_text="студия"
    )
    mock_db = MagicMock()
    mock_user = MagicMock()

    # Act
    # We are calling the function directly, not via the test client
    await search_properties(search_request, mock_db, mock_user)

    # Assert
    mock_openai_create.assert_called_once()
    _, kwargs = mock_openai_create.call_args
    full_query_text = kwargs['input']

    assert "0 комнат" in full_query_text
    assert "студия" in full_query_text
