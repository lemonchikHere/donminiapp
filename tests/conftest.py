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

    # Override the app's dependency to use this session
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    # Teardown
    session.close()
    transaction.rollback()
    connection.close()
    # Restore original dependency
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def client():
    # This client doesn't need the user_id header anymore,
    # as the user will be created per-test by the test_user fixture
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def test_user(db_session):
    # This fixture now uses the same transactional session as the app
    user = User(telegram_user_id=123, username="testuser")
    db_session.add(user)
    db_session.commit()

    # We need to update the client header inside this fixture to match the created user
    # Or, even better, let's create a new client for each function
    client = TestClient(app)
    client.headers["X-Telegram-User-Id"] = str(user.telegram_user_id)

    return user, client
