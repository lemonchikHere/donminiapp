from unittest.mock import patch, MagicMock
import asyncio
import os
from src.api.routes.search import search_properties, PropertySearchRequest

# Set a dummy API key for testing
os.environ["OPENAI_API_KEY"] = "test"

@patch('openai.embeddings.create')
def test_search_query_with_zero_rooms(mock_openai_create):
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
    async def run_test():
        try:
            await search_properties(search_request, mock_db, mock_user)
        except Exception:
            # We expect an error because the mock_db is not fully functional.
            # We only care about the call to openai.embeddings.create.
            pass

    asyncio.run(run_test())

    # Assert
    mock_openai_create.assert_called_once()
    # The call is made with keyword arguments, so we inspect the second element of call_args
    _, kwargs = mock_openai_create.call_args
    full_query_text = kwargs['input']

    assert "0 комнат" in full_query_text, f"Expected '0 комнат' in query, but got '{full_query_text}'"
    assert "студия" in full_query_text, f"Expected 'студия' in query, but got '{full_query_text}'"
