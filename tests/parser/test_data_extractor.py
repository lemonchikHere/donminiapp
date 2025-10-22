"""
Unit tests for the PropertyDataExtractor class.

This module contains a suite of tests for the `PropertyDataExtractor` class,
which is responsible for parsing structured data from raw text and generating
embeddings. The tests cover various text formats, edge cases, and mocked
interactions with the OpenAI API.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.parser.data_extractor import PropertyDataExtractor

@pytest.fixture(autouse=True)
def mock_openai_key(monkeypatch):
    """
    A pytest fixture that automatically sets a dummy OpenAI API key for all
    tests in this module. This prevents `KeyError` exceptions when the
    `PropertyDataExtractor` is initialized.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

@pytest.fixture
def extractor():
    """
    A pytest fixture that provides a fresh instance of `PropertyDataExtractor`
    for each test function.
    """
    return PropertyDataExtractor()

def test_extract_complete_data(extractor):
    """
    Tests data extraction from a comprehensive text message that contains all
    of the expected data fields (transaction, type, rooms, area, etc.).
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
    Tests data extraction from a text message where some data fields are
    missing, ensuring the extractor returns `None` for those fields.
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
    Tests data extraction from a text message that contains no relevant
    property information, expecting all fields to be `None`.
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
    ("студия", None), # The current regex doesn't handle 'студия'
])
def test_extract_various_rooms_formats(extractor, rooms_text, expected_rooms):
    """
    Tests that the number of rooms can be extracted from various text formats
    using a parameterized test.
    """
    result = extractor.extract(rooms_text)
    assert result['rooms'] == expected_rooms

@pytest.mark.parametrize("area_text, expected_area", [
    ("Площадь: 80 м²", 80.0),
    ("Общая 45.5м2", 45.5),
    ("Размер 120 кв.м", 120.0),
])
def test_extract_various_area_formats(extractor, area_text, expected_area):
    """
    Tests that the property area can be extracted from various text formats
    (e.g., 'м²', 'м2', 'кв.м').
    """
    result = extractor.extract(area_text)
    assert result['area_sqm'] == expected_area

def test_price_conversion_rub_to_usd(extractor):
    """
    Tests that a price listed in RUB is correctly converted to USD using the
    hardcoded exchange rate.
    """
    text = "Цена 9 000 000 руб"
    result = extractor.extract(text)
    # 9,000,000 / 90.0 = 100,000.0
    assert result['price_usd'] == 100000.0

@patch('openai.resources.embeddings.Embeddings.create')
def test_generate_embedding_mocked(mock_openai_create, extractor):
    """
    Tests the embedding generation logic. This test mocks the OpenAI API call
    to verify that the correct text is sent for embedding and that the mock
    response is returned.
    """
    # Arrange
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

    # Act
    embedding = extractor.generate_embedding(property_data)

    # Assert
    expected_text = "sell apartment 3 комнат 75.0 м² ул. Ленина 1 Отличная квартира"
    mock_openai_create.assert_called_once()
    called_input = mock_openai_create.call_args.kwargs.get('input')
    assert called_input == expected_text
    assert embedding == mock_embedding

def test_generate_embedding_with_missing_data(extractor):
    """
    Tests that the `generate_embedding` method can gracefully handle cases
    where the input data dictionary is missing some keys.
    """
    property_data = {'description': 'Просто описание'}
    with patch('openai.resources.embeddings.Embeddings.create') as mock_create:
        extractor.generate_embedding(property_data)
        mock_create.assert_called_once_with(
            model="text-embedding-3-small",
            input='Просто описание'
        )

@patch('openai.resources.embeddings.Embeddings.create', side_effect=Exception("API Error"))
def test_generate_embedding_api_error(mock_openai_create, extractor):
    """
    Tests that if the OpenAI API call fails (e.g., due to a network issue or
    API error), the `generate_embedding` method catches the exception and
    returns `None`.
    """
    property_data = {'description': 'some text'}
    embedding = extractor.generate_embedding(property_data)
    assert embedding is None
