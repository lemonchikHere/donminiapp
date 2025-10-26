import os
import pytest
from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import ARRAY, TypeDecorator
from fastapi.testclient import TestClient

# --- Set dummy env vars BEFORE any other imports ---
os.environ.update({
    "YANDEX_API_KEY": "test_yandex_key",
    "OPENAI_API_KEY": "test_openai_key",
    "TELEGRAM_BOT_TOKEN": "test_bot_token",
    "POSTGRES_USER": "testuser",
    "POSTGRES_PASSWORD": "testpass",
    "POSTGRES_DB": "testdb",
    "POSTGRES_HOST": "localhost",
    "ADMIN_CHAT_ID": "12345"
})

# --- Import all models to register them with Base ---
from src.models.base import Base
from src.models.user import User, Favorite
from src.models.property import Property
from src.models.appointment import Appointment

# --- Now, import the app and dependencies ---
from src.api.main import app
from src.api.dependencies import get_db

# --- Custom compilers for PostgreSQL types on SQLite ---
from pgvector.sqlalchemy import Vector

@compiles(ARRAY, 'sqlite')
def compile_array_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(Vector, 'sqlite')
def compile_vector_sqlite(type_, compiler, **kw):
    # It renders as a JSON field, and we'll insert JSON-nulls for embeddings
    return "JSON"

# --- Test DB Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# --- Dependency Overrides & Fixtures ---

# This single fixture provides a transactional scope around each test.
@pytest.fixture(scope="function")
def db_session():
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
