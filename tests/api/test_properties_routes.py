# tests/api/test_properties_routes.py
import pytest
from uuid import uuid4
from datetime import datetime
from src.models.property import Property
from src.models.user import Favorite, User

def test_get_property_details_success(db_session, test_user):
    user, client = test_user

    prop_id = uuid4()
    test_property = Property(
        id=prop_id, address="123 Test St", price_usd=50000,
        rooms=2, area_sqm=60, property_type="apartment",
        telegram_channel_id=12345, telegram_message_id=67890,
        posted_at=datetime.utcnow()
    )
    db_session.add(test_property)
    db_session.commit()

    response = client.get(f"/api/properties/{prop_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(prop_id)
    assert data["address"] == "123 Test St"
    assert data["is_favorite"] is False

def test_get_property_details_with_favorite(db_session, test_user):
    user, client = test_user

    prop_id = uuid4()
    test_property = Property(
        id=prop_id, address="Favorite St",
        telegram_message_id=987, telegram_channel_id=654,
        posted_at=datetime.utcnow()
    )
    db_session.add(test_property)
    db_session.commit()

    db_user = db_session.query(User).filter(User.telegram_user_id == user.telegram_user_id).one()

    favorite_link = Favorite(user_id=db_user.id, property_id=prop_id)
    db_session.add(favorite_link)
    db_session.commit()

    response = client.get(f"/api/properties/{prop_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(prop_id)
    assert data["is_favorite"] is True

def test_get_property_details_not_found(test_user):
    _, client = test_user
    non_existent_id = uuid4()
    response = client.get(f"/api/properties/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Property not found"
