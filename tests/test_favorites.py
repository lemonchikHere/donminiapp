import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from src.api.routes.favorites import get_favorites
from src.models.property import Property
from src.models.user import User
from src.api.routes.search import PropertyResponse

@pytest.mark.asyncio
async def test_get_favorites_truncates_description():
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

    mock_db = MagicMock()
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_prop]

    mock_user = User(id=uuid4(), telegram_user_id=12345, username="testuser")

    # Act
    response = await get_favorites(mock_db, mock_user)

    # Assert
    assert len(response) == 1
    assert len(response[0].description) <= 203
    assert response[0].description.endswith("...")
