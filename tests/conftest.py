import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Загружаем переменные окружения для тестов
load_dotenv(".env.test")

# Устанавливаем переменную окружения, чтобы приложение знало, что оно в тестовом режиме
os.environ["TESTING"] = "1"

# Перезагружаем модуль config, чтобы он подхватил тестовые переменные
# Это важно, так как DATABASE_URL используется при инициализации модуля
from src import config
import importlib
importlib.reload(config)

from src.api.main import app
from src.database import get_db, Base


# Создаем тестовый движок и сессию для БД
engine_test = create_engine(config.settings.database_url)
SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# --- Фикстуры ---

@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Фикстура для создания и очистки сессии БД для каждого теста.
    """
    Base.metadata.create_all(bind=engine_test)
    db = SessionTest()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine_test)


from httpx import AsyncClient, ASGITransport

@pytest_asyncio.fixture(scope="function")
async def test_client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """
    Фикстура для создания тестового клиента API.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # Очищаем переопределение после теста
    app.dependency_overrides.clear()
