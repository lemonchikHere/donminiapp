import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from src.api.routes.properties import get_property_details
from src.models.property import Property
from src.models.user import User

@pytest.mark.asyncio
async def test_get_property_details_truncates_description():
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
    mock_db.query.return_value.filter.return_value.first.return_value = mock_prop

    mock_user = User(id=uuid4(), telegram_user_id=12345, username="testuser")

    # Act
    response = await get_property_details(property_id, mock_db, mock_user)

    # Assert
    assert len(response.description) <= 203
    assert response.description.endswith("...")
