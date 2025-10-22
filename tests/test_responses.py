import pytest
from src.api.routes.search import PropertyResponse
from src.config import settings

def test_property_response_photo_url_conversion():
    # Arrange
    settings.API_BASE_URL = "http://testserver"
    local_photo_path = "media/photo1.jpg"

    prop_data = {
        "id": "123",
        "title": "Test Property",
        "price_usd": 100000,
        "rooms": 2,
        "area_sqm": 50,
        "address": "123 Test St",
        "description": "A test property.",
        "photos": [local_photo_path],
        "similarity_score": None,
        "telegram_link": "https://t.me/c/123/456",
        "is_favorite": False,
    }

    # Act
    response = PropertyResponse(**prop_data)

    # Assert
    assert len(response.photos) == 1
    assert response.photos[0] == f"{settings.API_BASE_URL}/{local_photo_path}"
