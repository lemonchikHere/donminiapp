"""
Tests for the property search API endpoint.

This module contains tests for the `search_properties` function, ensuring
that key functionalities like description truncation and integration with the
OpenAI API (mocked) work as expected.
"""

import pytest
import os
from unittest.mock import MagicMock, patch
from uuid import uuid4
from src.api.routes.search import search_properties, PropertySearchRequest
from src.models.property import Property
from src.models.user import User

# Set a dummy OpenAI API key to prevent errors during test initialization.
os.environ["OPENAI_API_KEY"] = "test_api_key"

@pytest.mark.asyncio
@patch('openai.embeddings.create')
async def test_search_properties_truncates_description(mock_openai_create):
    """
    Verifies that the `search_properties` endpoint correctly truncates long
    property descriptions in its results.
    """
    # Arrange
    # Mock the OpenAI client's response for generating query embeddings.
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
        embedding=[0.1] * 1536  # Mock embedding for the property
    )

    # Mock the database session and the complex query chain for search.
    mock_db = MagicMock()
    mock_query_result = [(mock_prop, 0.1)] # (Property, distance)
    mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_query_result
    # Also mock the favorites query to return an empty set
    mock_db.query.return_value.filter.return_value.all.return_value = []


    mock_user = User(id=uuid4(), telegram_user_id=12345, username="testuser")

    search_request = PropertySearchRequest(query_text="test")

    # Act
    response = await search_properties(search_request, mock_db, mock_user)

    # Assert
    assert len(response.results) == 1
    assert len(response.results[0].description) == 203 # 200 chars + "..."
    assert response.results[0].description.endswith("...")
