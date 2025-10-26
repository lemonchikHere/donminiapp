import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import patch
import os

# Set dummy environment variables FIRST
os.environ["OPENAI_API_KEY"] = "test_api_key"
os.environ["TELEGRAM_API_ID"] = "12345"
os.environ["TELEGRAM_API_HASH"] = "test_hash"

from src.database import get_db
from src.api.main import app
from src.models.user import User, Favorite
from src.api.dependencies import get_current_user
from tests.models import Base as TestBase # Import the test base

# Setup the in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    TestBase.metadata.create_all(bind=engine)
    # Also create necessary tables from the original Base
    from src.models.base import Base as AppBase
    AppBase.metadata.create_all(bind=engine, tables=[User.__table__, Favorite.__table__])

    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override the app's dependencies to use this session
    def override_get_db():
        yield session

    def override_get_current_user():
        user = session.query(User).filter(User.telegram_user_id == 123456789).first()
        if not user:
            user = User(telegram_user_id=123456789, username="testuser")
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    TestBase.metadata.drop_all(bind=engine)
    AppBase.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def mock_openai_to_none():
    """
    By default, mock the embedding creation to return None.
    This prevents vector search logic from being triggered in most tests,
    avoiding the pgvector <=> operator error with SQLite.
    """
    with patch("src.api.routes.search.openai.embeddings.create") as mock_create:
        mock_create.return_value = None
        yield mock_create

@pytest.fixture(scope="function")
def mock_openai_for_semantic_search():
    """
    A specific mock for the semantic search test that returns a valid embedding.
    """
    with patch("src.api.routes.search.openai.embeddings.create") as mock_create:
        # Create a mock Embedding object
        mock_embedding = type("Embedding", (), {"embedding": [0.1] * 1536})
        # Create a mock Response object containing the embedding data
        mock_response = type("Response", (), {"data": [mock_embedding]})
        mock_create.return_value = mock_response
        yield mock_create
