# tests/api/test_map_routes.py
import pytest
from uuid import uuid4
from datetime import datetime
from src.models.property import Property

def create_map_property(session, lat, lon, is_active):
    prop = Property(
        id=uuid4(), latitude=lat, longitude=lon, is_active=is_active,
        price_usd=150000, rooms=2, property_type="apartment",
        telegram_message_id=int(uuid4().int % 100000),
        telegram_channel_id=12345,
        posted_at=datetime.utcnow()
    )
    session.add(prop)
    return prop

def test_get_map_properties(db_session, test_user):
    user, client = test_user

    prop1 = create_map_property(db_session, 47.22, 39.72, True)
    prop2 = create_map_property(db_session, 47.23, 39.74, False) # Inactive
    prop3 = create_map_property(db_session, None, None, True)   # No coords
    prop4 = create_map_property(db_session, 47.25, 39.75, True)
    db_session.commit()

    response = client.get("/api/map/properties")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    returned_ids = {item['id'] for item in data}
    assert str(prop1.id) in returned_ids
    assert str(prop4.id) in returned_ids
