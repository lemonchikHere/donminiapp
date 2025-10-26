import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from src.models.property import Property
from src.models.user import User
import uuid
from datetime import datetime
from unittest.mock import MagicMock

# Используем фикстуры test_client и db_session из conftest.py
pytestmark = pytest.mark.asyncio

# --- Вспомогательные данные ---
TEST_USER_ID = "12345"

@pytest.fixture(scope="function", autouse=True)
def test_user(db_session: Session):
    """Создаем тестового пользователя перед каждым тестом."""
    user = db_session.query(User).filter(User.telegram_user_id == int(TEST_USER_ID)).first()
    if not user:
        user = User(telegram_user_id=int(TEST_USER_ID), username="testuser")
        db_session.add(user)
        db_session.commit()
    return user

@pytest.fixture
def mock_openai(mocker):
    """Мокаем API OpenAI, чтобы избежать реальных вызовов."""
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1] * 1536

    mock_response = MagicMock()
    mock_response.data = [mock_embedding]

    # Мокаем сам метод .create()
    mocker.patch("openai.embeddings.create", return_value=mock_response)


async def test_search_properties_by_text(test_client: AsyncClient, db_session: Session, mock_openai):
    # --- Подготовка данных ---
    prop1 = Property(
        telegram_message_id=1, telegram_channel_id=1, posted_at=datetime.utcnow(),
        description="Отличная квартира в центре города", raw_text="Продам квартиру в центре",
        is_active=True, price_usd=50000,
        embedding=[0.1] * 1536
    )
    prop2 = Property(
        telegram_message_id=2, telegram_channel_id=1, posted_at=datetime.utcnow(),
        description="Просторный дом у моря", raw_text="Продам дом у моря",
        is_active=True, price_usd=150000,
        embedding=[0.9] * 1536
    )
    db_session.add_all([prop1, prop2])
    db_session.commit()

    # --- Выполнение запроса ---
    search_payload = {"query_text": "квартира"}
    response = await test_client.post(
        "/api/search",
        json=search_payload,
        headers={"x-telegram-user-id": TEST_USER_ID}
    )

    # --- Проверка результата ---
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert any(p["description"] == "Отличная квартира в центре города" for p in data["results"])


async def test_search_properties_no_results(test_client: AsyncClient, mock_openai):
    search_payload = {"query_text": "несуществующий запрос"}
    response = await test_client.post(
        "/api/search",
        json=search_payload,
        headers={"x-telegram-user-id": TEST_USER_ID}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


async def test_get_map_properties(test_client: AsyncClient, db_session: Session):
    # --- Подготовка данных ---
    prop1 = Property(
        telegram_message_id=10, telegram_channel_id=1, posted_at=datetime.utcnow(),
        latitude=48.0159, longitude=37.8028, # Донецк
        description="Квартира на карте", raw_text="квартира", is_active=True,
        price_usd=60000
    )
    db_session.add(prop1)
    db_session.commit()

    # --- Выполнение запроса ---
    response = await test_client.get("/api/map/properties")

    # --- Проверка результата ---
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["latitude"] == 48.0159
    assert data[0]["longitude"] == 37.8028
    assert data[0]["price_usd"] == 60000
