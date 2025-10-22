import pytest
import os
from unittest.mock import MagicMock, patch
from uuid import uuid4
from src.api.routes.search import search_properties, PropertySearchRequest
from src.models.property import Property
from src.models.user import User

# Set a dummy API key for testing
os.environ["OPENAI_API_KEY"] = "test"

@pytest.mark.asyncio
@patch('openai.embeddings.create')
async def test_search_properties_truncates_description(mock_openai_create):
    # Arrange
    mock_response = MagicMock()
    mock_embedding = [0.1] * 1536
    mock_response.data = [MagicMock(embedding=mock_embedding)]
    mock_openai_create.return_value = mock_response

    long_description = "a" * 300
    property_id = uuid4()

    mock_prop = Property(
        id=property_id,
        description=long_description,
        rooms=1,
        property_type="квартира",
        area_sqm=50,
        telegram_channel_id=123,
        telegram_message_id=456,
        embedding=[0.1] * 1536
    )

    mock_db = MagicMock()
    # Mock the query for the property and the distance calculation
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [(mock_prop, 0.1)]

    mock_user = User(id=uuid4(), telegram_user_id=12345, username="testuser")

    search_request = PropertySearchRequest(query_text="test")

    # Act
    response = await search_properties(search_request, mock_db, mock_user)

    # Assert
    assert len(response.results) == 1
    assert len(response.results[0].description) <= 203
    assert response.results[0].description.endswith("...")
