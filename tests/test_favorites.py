"""
Tests for the favorites API endpoints.

This module contains tests to ensure that the logic for retrieving
favorite properties, such as description truncation, works correctly.
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from src.api.routes.favorites import get_favorites
from src.models.property import Property
from src.models.user import User

@pytest.mark.asyncio
async def test_get_favorites_truncates_description():
    """
    Verifies that the `get_favorites` endpoint correctly truncates long
    property descriptions.

    This test ensures that descriptions longer than 200 characters are
    shortened and appended with an ellipsis.
    """
    # Arrange
    long_description = "a" * 300
    property_id = uuid4()

    mock_prop = Property(
        id=property_id,
        description=long_description,
        rooms=1,
        property_type="квартира",
        area_sqm=50,
        telegram_channel_id=123,
        telegram_message_id=456
    )

    # Mock the database session and its query methods
    mock_db = MagicMock()
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_prop]

    mock_user = User(id=uuid4(), telegram_user_id=12345, username="testuser")

    # Act
    response = await get_favorites(mock_db, mock_user)

    # Assert
    assert len(response) == 1
    assert len(response[0].description) == 203  # 200 chars + "..."
    assert response[0].description.endswith("...")
