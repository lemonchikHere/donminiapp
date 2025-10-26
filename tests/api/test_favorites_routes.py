# tests/api/test_favorites_routes.py
import pytest
from uuid import uuid4
from datetime import datetime
from src.models.property import Property

def create_test_property(session, address_suffix):
    prop = Property(
        id=uuid4(),
        address=f"123 {address_suffix} St",
        telegram_message_id=int(uuid4().int % 100000),
        telegram_channel_id=12345,
        posted_at=datetime.utcnow()
    )
    session.add(prop)
    session.commit()
    return prop

def test_add_to_favorites_success(db_session, test_user):
    user, client = test_user
    prop = create_test_property(db_session, "Favorite")
    response = client.post("/api/favorites/", json={"property_id": str(prop.id)})
    assert response.status_code == 201

def test_add_to_favorites_property_not_found(test_user):
    _, client = test_user
    response = client.post("/api/favorites/", json={"property_id": str(uuid4())})
    assert response.status_code == 404

def test_add_to_favorites_already_exists(db_session, test_user):
    user, client = test_user
    prop = create_test_property(db_session, "AlreadyFavorited")
    client.post("/api/favorites/", json={"property_id": str(prop.id)})
    response = client.post("/api/favorites/", json={"property_id": str(prop.id)})
    assert response.status_code == 409

def test_get_favorites(db_session, test_user):
    user, client = test_user
    prop1 = create_test_property(db_session, "Fav 1")
    prop2 = create_test_property(db_session, "Fav 2")
    client.post("/api/favorites/", json={"property_id": str(prop1.id)})
    client.post("/api/favorites/", json={"property_id": str(prop2.id)})

    response = client.get("/api/favorites/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {p["address"] for p in data} == {prop1.address, prop2.address}

def test_remove_from_favorites_success(db_session, test_user):
    user, client = test_user
    prop = create_test_property(db_session, "ToBeRemoved")
    client.post("/api/favorites/", json={"property_id": str(prop.id)})

    response = client.delete(f"/api/favorites/{prop.id}")
    assert response.status_code == 204

    get_response = client.get("/api/favorites/")
    assert len(get_response.json()) == 0

def test_remove_from_favorites_not_found(test_user):
    _, client = test_user
    response = client.delete(f"/api/favorites/{uuid4()}")
    assert response.status_code == 404
