from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from unittest.mock import patch, MagicMock

from tests.models import TestProperty as Property  # Use the test model


# Helper function to create test properties
def create_test_properties(db_session: Session):
    prop1 = Property(
        id=uuid4(),
        telegram_message_id=1,
        telegram_channel_id=123,
        posted_at=datetime(2024, 1, 1),
        transaction_type="sell",
        property_type="apartment",
        rooms=2,
        price_usd=100000,
        is_active=True,
        address="Центр города, ул. Пушкина",
        photos='["photo1.jpg"]',
    )
    prop2 = Property(
        id=uuid4(),
        telegram_message_id=2,
        telegram_channel_id=123,
        posted_at=datetime(2024, 1, 2),
        transaction_type="rent",
        property_type="house",
        rooms=4,
        price_usd=2000,
        is_active=True,
        address="Тихий район, ул. Есенина",
        photos='["photo2.jpg"]',
    )
    prop3 = Property(
        id=uuid4(),
        telegram_message_id=3,
        telegram_channel_id=123,
        posted_at=datetime(2024, 1, 3),
        transaction_type="sell",
        property_type="apartment",
        rooms=3,
        price_usd=150000,
        is_active=True,
        address="Новостройка на набережной",
        photos='["photo3.jpg"]',
    )
    db_session.add_all([prop1, prop2, prop3])
    db_session.commit()
    return [prop1, prop2, prop3]


def test_search_no_filters(client: TestClient, db_session: Session):
    """Test searching for properties without any filters, should return all active."""
    create_test_properties(db_session)
    response = client.post("/api/search", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["results"]) == 3


def test_search_with_transaction_type_filter(client: TestClient, db_session: Session):
    """Test filtering by transaction type 'rent'."""
    create_test_properties(db_session)
    response = client.post("/api/search", json={"transaction_type": "rent"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["price_usd"] == 2000


def test_search_with_rooms_filter(client: TestClient, db_session: Session):
    """Test filtering by number of rooms."""
    create_test_properties(db_session)
    response = client.post("/api/search", json={"rooms": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["price_usd"] == 150000


def test_search_with_budget_filter(client: TestClient, db_session: Session):
    """Test filtering by a price range."""
    create_test_properties(db_session)
    response = client.post(
        "/api/search", json={"budget_min": 90000, "budget_max": 110000}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["price_usd"] == 100000


def test_search_pagination(client: TestClient, db_session: Session):
    """Test pagination using limit and offset."""
    create_test_properties(db_session)
    # Request first page with 2 items
    response = client.post("/api/search?limit=2&offset=0", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["results"]) == 2

    # Request second page with 1 item
    response = client.post("/api/search?limit=2&offset=2", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["results"]) == 1


def test_search_semantic_query(
    client: TestClient, db_session: Session, mock_openai_for_semantic_search
):
    """Test semantic search with a text query. Mocks the DB call to avoid SQLite errors."""
    # Create a mock query object that will be returned by db_session.query()
    mock_query = MagicMock()
    # Mock the chained methods
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query

    # Configure the final return values
    mock_query.count.return_value = 1
    # Create a fake property object that can be serialized by Pydantic
    fake_property = Property(
        id=uuid4(),
        telegram_message_id=99,
        telegram_channel_id=123,
        posted_at=datetime.now(),
        transaction_type="sell",
        property_type="apartment",
        rooms=2,
        price_usd=123456,
        is_active=True,
        address="Mocked Address",
        photos="[]",
    )
    # The query in the route returns tuples of (Property, distance)
    mock_query.all.return_value = [(fake_property, 0.123)]

    # Patch the `query` method of the specific session object used in the test
    with patch.object(db_session, "query", return_value=mock_query) as mock_db_query:
        response = client.post("/api/search", json={"query_text": "квартира в центре"})

        # Assert that the request was successful
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["address"] == "Mocked Address"

        # Assert that OpenAI mock was called
        mock_openai_for_semantic_search.assert_called_once()
        call_args, call_kwargs = mock_openai_for_semantic_search.call_args
        assert "квартира в центре" in call_kwargs["input"]

        # Assert that the db query was constructed for vector search
        # Assert that the db query was constructed for vector search
        mock_db_query.assert_called()
        # Check that order_by was called with the correct distance metric
        mock_query.order_by.assert_called_once()
        args, kwargs = mock_query.order_by.call_args
        assert "distance" in args[0]
