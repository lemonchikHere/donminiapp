import pytest
from unittest.mock import patch, MagicMock
import openai
from src.parser.data_extractor import PropertyDataExtractor

@pytest.fixture(autouse=True)
def mock_openai_key(monkeypatch):
    """Set a dummy OpenAI API key to prevent initialization errors during tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

@pytest.fixture
def extractor():
    """Provides a PropertyDataExtractor instance for tests."""
    return PropertyDataExtractor()

def test_extract_complete_data(extractor):
    """
    Tests extraction from a message containing all expected data fields.
    """
    text = """
    Продам 3-комнатную квартиру в центре.
    Площадь: 75.5 м²
    Этаж: 5/9
    Цена: 120 000 $
    Адрес: ул. Пушкина, д. 10
    Отличное состояние, свежий ремонт.
    """
    result = extractor.extract(text)

    assert result['transaction_type'] == 'sell'
    assert result['property_type'] == 'apartment'
    assert result['rooms'] == 3
    assert result['area_sqm'] == 75.5
    assert result['floor'] == '5/9'
    assert result['price_usd'] == 120000.0
    assert 'ул. Пушкина' in result['address']
    assert 'Отличное состояние' in result['description']

def test_extract_partial_data(extractor):
    """
    Tests extraction from a message with some data missing.
    """
    text = "Сдаю квартиру, 50 м2. Цена 500 USD."
    result = extractor.extract(text)

    assert result['transaction_type'] == 'rent'
    assert result['property_type'] == 'apartment'
    assert result['rooms'] is None
    assert result['area_sqm'] == 50.0
    assert result['floor'] is None
    assert result['price_usd'] == 500.0
    assert result['address'] is None

def test_extract_no_relevant_data(extractor):
    """
    Tests extraction from a message with no relevant property data.
    """
    text = "Простое текстовое сообщение без какой-либо информации о недвижимости."
    result = extractor.extract(text)

    assert result['transaction_type'] is None
    assert result['property_type'] is None
    assert result['rooms'] is None
    assert result['area_sqm'] is None
    assert result['floor'] is None
    assert result['price_usd'] is None
    assert result['address'] is None

@pytest.mark.parametrize("rooms_text, expected_rooms", [
    ("Продам 2-комн. квартиру", 2),
    ("Сдаю 1-к. апартаменты", 1),
    ("4 bedroom house for sale", 4),
    ("студия", None), # Current regex doesn't handle 'студия'
])
def test_extract_various_rooms_formats(extractor, rooms_text, expected_rooms):
    """Tests different text formats for room numbers."""
    result = extractor.extract(rooms_text)
    assert result['rooms'] == expected_rooms

@pytest.mark.parametrize("area_text, expected_area", [
    ("Площадь: 80 м²", 80.0),
    ("Общая 45.5м2", 45.5),
    ("Размер 120 кв.м", 120.0),
])
def test_extract_various_area_formats(extractor, area_text, expected_area):
    """Tests different text formats for square meters."""
    result = extractor.extract(area_text)
    assert result['area_sqm'] == expected_area

def test_price_conversion_rub_to_usd(extractor):
    """Tests the conversion of price from RUB to USD."""
    text = "Цена 9 000 000 руб"
    result = extractor.extract(text)
    # 9,000,000 / 90.0 = 100,000.0
    assert result['price_usd'] == 100000.0

@patch('openai.resources.embeddings.Embeddings.create')
def test_generate_embedding_mocked(mock_openai_create, extractor):
    """
    Tests the embedding generation logic, ensuring OpenAI API is called correctly.
    """
    mock_embedding = [0.1, 0.2, 0.3]
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = mock_embedding
    mock_openai_create.return_value = mock_response

    property_data = {
        'transaction_type': 'sell',
        'property_type': 'apartment',
        'rooms': 3,
        'area_sqm': 75.0,
        'address': 'ул. Ленина 1',
        'description': 'Отличная квартира'
    }
    embedding = extractor.generate_embedding(property_data)

    expected_text = "sell apartment 3 комнат 75.0 м² ул. Ленина 1 Отличная квартира"
    mock_openai_create.assert_called_once()
    called_input = mock_openai_create.call_args.kwargs.get('input')
    assert called_input == expected_text
    assert embedding == mock_embedding

def test_generate_embedding_with_missing_data(extractor):
    """
    Tests that embedding generation handles missing data gracefully.
    """
    property_data = {
        'description': 'Просто описание'
    }
    with patch('openai.resources.embeddings.Embeddings.create') as mock_create:
        extractor.generate_embedding(property_data)
        mock_create.assert_called_once_with(
            model="text-embedding-3-small",
            input='Просто описание'
        )

@patch('time.sleep', return_value=None)
@patch('openai.resources.embeddings.Embeddings.create', side_effect=openai.RateLimitError("Rate limit exceeded", response=MagicMock(), body=None))
def test_generate_embedding_rate_limit_retry(mock_openai_create, mock_sleep, extractor):
    """
    Tests that the function retries on RateLimitError.
    """
    property_data = {'description': 'some text'}
    embedding = extractor.generate_embedding(property_data, max_retries=3)

    assert mock_openai_create.call_count == 3
    assert embedding is None

@patch('time.sleep', return_value=None)
@patch('openai.resources.embeddings.Embeddings.create')
def test_generate_embedding_retry_success(mock_openai_create, mock_sleep, extractor):
    """
    Tests that the function succeeds on a retry attempt.
    """
    mock_embedding = [0.1, 0.2, 0.3]
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = mock_embedding

    # Fail on the first call, succeed on the second
    mock_openai_create.side_effect = [
        openai.RateLimitError("Rate limit exceeded", response=MagicMock(), body=None),
        mock_response
    ]

    property_data = {'description': 'some text'}
    embedding = extractor.generate_embedding(property_data, max_retries=3)

    assert mock_openai_create.call_count == 2
    assert embedding == mock_embedding
