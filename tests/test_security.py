import pytest
import os
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
import importlib

# Set dummy environment variables *before* any application imports
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['YANDEX_API_KEY'] = 'test-key'
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

# Reload the config module to ensure it picks up the test environment variables
from src import config
importlib.reload(config)

from src.api import dependencies
from src.database import get_db
from src.models.user import User
from src.api.main import app

# 1. Create a mock database session and user
mock_db_session = MagicMock()
mock_user = User(id=uuid.uuid4(), telegram_user_id=12345, username="testuser")

# 2. Create override functions for dependencies
def override_get_db():
    try:
        yield mock_db_session
    finally:
        pass

def override_get_current_user():
    return mock_user

# 3. Apply the overrides to the app
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[dependencies.get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.mark.asyncio
async def test_rate_limiter():
    """
    Tests that the rate limiter blocks requests after the limit is exceeded.
    """
    endpoint = "/api/config/"
    headers = {"X-Telegram-User-Id": "test-user-rate-limit"}

    for i in range(100):
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 200, f"Request {i+1} failed"

    # The 101st request should be blocked
    response = client.get(endpoint, headers=headers)
    assert response.status_code == 429

    # slowapi's default response is plain text, not JSON with a 'detail' key.
    # Let's check the content of the text response.
    assert "Rate limit exceeded" in response.text


@pytest.mark.asyncio
@patch('openai.embeddings.create')
async def test_input_sanitization(mock_openai_create: MagicMock):
    """
    Tests that user input is properly sanitized before being processed.
    """
    mock_openai_create.return_value = MagicMock(data=[MagicMock(embedding=[0.1, 0.2])])
    mock_db_session.query.return_value.filter.return_value.all.return_value = []

    malicious_payload = {
        "query_text": "find me a house <script>alert('XSS');</script>",
        "district": "downtown <b>bold</b>"
    }

    expected_sanitized_input = "downtown bold find me a house alert('XSS');"
    headers = {"X-Telegram-User-Id": "test-user-sanitization"}

    response = client.post("/api/search", json=malicious_payload, headers=headers)

    assert response.status_code == 200, f"Sanitization test failed: {response.text}"

    mock_openai_create.assert_called_once()
    call_args, call_kwargs = mock_openai_create.call_args
    assert call_kwargs['input'].strip() == expected_sanitized_input
