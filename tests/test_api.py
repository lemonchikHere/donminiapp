from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.models.property import Property
from datetime import datetime
import uuid

def test_search_for_studio_apartment(client: TestClient, db_session: Session):
    # Arrange: Create test data
    studio = Property(
        id=uuid.uuid4(),
        rooms=0,
        address="Studio, Test City",
        posted_at=datetime.utcnow(),
        transaction_type="sell",
        property_type="apartment",
        status="active"
    )
    one_room = Property(
        id=uuid.uuid4(),
        rooms=1,
        address="One Room, Test City",
        posted_at=datetime.utcnow(),
        transaction_type="sell",
        property_type="apartment",
        status="active"
    )
    db_session.add_all([studio, one_room])
    db_session.commit()

    # Act: Perform the search
    response = client.post("/api/search", json={"rooms": 0})

    # Assert: Check the results
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["rooms"] == 0
    assert data["results"][0]["address"] == "Studio, Test City"
