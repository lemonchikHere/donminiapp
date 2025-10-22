import pytest
from src.parser.data_extractor import PropertyDataExtractor

@pytest.fixture
def extractor():
    return PropertyDataExtractor()

@pytest.mark.parametrize("text, expected_rooms", [
    ("Сдам 1-комн квартиру", 1),
    ("Продается 2-к. апартамент", 2),
    ("Аренда 3 bedroom flat", 3),
    ("Предлагается студия", 0),
    ("Уютная однокомнатная квартира", 1),
    ("Просторная двухкомнатная", 2),
    ("Трехкомнатная квартира в центре", 3),
    ("Четырехкомнатная квартира с видом", 4),
    ("Продам квартиру, 5 комнат", 5),
])
def test_extract_rooms(extractor, text, expected_rooms):
    assert extractor._extract_rooms(text) == expected_rooms
