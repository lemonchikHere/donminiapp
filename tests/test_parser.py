import pytest
from src.parser.data_extractor import PropertyDataExtractor as DataExtractor

extractor = DataExtractor()

# --- Тесты для извлечения цены ---

@pytest.mark.parametrize("text, expected", [
    ("Продам за 55000$.", 55000.0),
    ("Цена 55 000 $", 55000.0),
    ("Стоимость 4 500 000 рублей", 50000.0), # 4500000 / 90
    ("4500000руб.", 50000.0),
    ("Никакой цены тут нет.", None),
])
def test_extract_price(text, expected):
    result = extractor._extract_price(text)
    assert result == expected

# --- Тесты для извлечения количества комнат ---

@pytest.mark.parametrize("text, expected", [
    ("Продам 2-комнатную квартиру.", 2),
    ("3 комнаты.", 3),
    ("Однокомнатная квартира", None), # Паттерн не найдет
    ("Продается студия.", None),
    ("Просто текст без комнат.", None),
])
def test_extract_rooms(text, expected):
    result = extractor._extract_rooms(text)
    assert result == expected

# --- Тесты для извлечения площади ---

@pytest.mark.parametrize("text, expected", [
    ("Площадь 50 м2.", 50.0),
    ("Общая площадь 75.5 кв.м.", 75.5),
    ("Просто 100 метров.", None),
])
def test_extract_area(text, expected):
    result = extractor._extract_area(text)
    assert result == expected

# --- Тесты для извлечения этажа ---

@pytest.mark.parametrize("text, expected", [
    ("Этаж 5/9.", "5/9"),
    ("Расположена на 3 этаже 5-этажного дома.", None), # Паттерн не найдет
    ("на 1 этаже.", None),
    ("Просто дом в 9 этажей.", None),
    ("Текст без этажей.", None),
])
def test_extract_floor(text, expected):
    result = extractor._extract_floor(text)
    assert result == expected


# --- Комплексные тесты для extract ---

def test_extract_full_data():
    text = """
    Продажа 3-комнатной квартиры!
    Адрес: г. Донецк, ул. Артема, 123.
    Этаж 7/9. Площадь 72.5 м2.
    Цена: 65000$. Не упустите свой шанс!
    """
    data = extractor.extract(text)

    assert data["price_usd"] == 65000.0
    assert data["rooms"] == 3
    assert data["area_sqm"] == 72.5
    assert data["floor"] == "7/9"
    assert data["address"] is not None
    assert data["transaction_type"] == "sell"
    assert data["property_type"] == "apartment"

def test_extract_partial_data():
    text = "Продам студию 25 кв.м. Цена 2.100.000 руб"
    data = extractor.extract(text)

    assert data["price_usd"] == 23333.33 # 2100000 / 90
    assert data["rooms"] is None
    assert data["area_sqm"] == 25.0
    assert data["floor"] is None
    assert data["address"] is None
    assert data["transaction_type"] == "sell"
    assert data["property_type"] is None
