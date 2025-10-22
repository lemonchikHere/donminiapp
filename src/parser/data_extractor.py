"""
Extracts structured property data from raw text using regular expressions
and generates vector embeddings for semantic search.
"""

import re
from typing import Dict, Optional
import openai
from src.config import settings

openai.api_key = settings.OPENAI_API_KEY

class PropertyDataExtractor:
    """
    A class for extracting structured real estate data from unstructured text.

    This class uses a series of regular expressions to find and parse key
    information like transaction type, property type, price, area, etc., from
    a given text string. It also provides a method to generate a vector

    embedding from the extracted data using OpenAI's API.
    """

    TRANSACTION_PATTERNS = {
        'sell': re.compile(r'(продам|продаю|продается|продажа)', re.IGNORECASE),
        'rent': re.compile(r'(сдам|сдаю|сдается|аренда|снять)', re.IGNORECASE)
    }
    """Regex patterns to identify the transaction type (sell or rent)."""

    PROPERTY_PATTERNS = {
        'apartment': re.compile(r'(квартир|кв\.|apartment)', re.IGNORECASE),
        'house': re.compile(r'(дом|house|коттедж)', re.IGNORECASE),
        'commercial': re.compile(r'(коммерч|офис|магазин|торгов)', re.IGNORECASE)
    }
    """Regex patterns to identify the property type."""

    ROOMS_PATTERNS = [
        re.compile(r'(\d+)[-\s]?комн', re.IGNORECASE),
        re.compile(r'(\d+)[-\s]?к\.', re.IGNORECASE),
        re.compile(r'(\d+)[-\s]?bedroom', re.IGNORECASE)
    ]
    """Regex patterns to extract the number of rooms."""

    AREA_PATTERN = re.compile(r'(\d+[\.,]?\d*)\s*(?:м²|м2|кв\.м)', re.IGNORECASE)
    """Regex pattern to extract the property area in square meters."""

    FLOOR_PATTERN = re.compile(r'(?:этаж|эт\.?)\s*:?\s*(\d+/\d+)', re.IGNORECASE)
    """Regex pattern to extract floor information (e.g., '3/9')."""

    PRICE_USD_PATTERN = re.compile(r'(\d[\d\s,]*)s*(?:\$|USD)', re.IGNORECASE)
    """Regex pattern for prices listed in USD."""

    PRICE_RUB_PATTERN = re.compile(r'(\d[\d\s,]*)\s*(?:₽|RUB|руб)', re.IGNORECASE)
    """Regex pattern for prices listed in RUB."""

    def extract(self, text: str) -> Dict:
        """
        Extracts structured data from a raw text string.

        Args:
            text: The raw text from a property listing message.

        Returns:
            A dictionary containing the extracted property data.
        """
        data = {
            'raw_text': text,
            'transaction_type': self._extract_enum(text, self.TRANSACTION_PATTERNS),
            'property_type': self._extract_enum(text, self.PROPERTY_PATTERNS),
            'rooms': self._extract_rooms(text),
            'area_sqm': self._extract_area(text),
            'floor': self._extract_floor(text),
            'price_usd': self._extract_price(text),
            'address': self._extract_address(text),
            'description': self._clean_description(text)
        }
        return data

    def _extract_enum(self, text: str, patterns: Dict) -> Optional[str]:
        """
        A helper function to find a match in a dictionary of regex patterns.

        Args:
            text: The text to search within.
            patterns: A dictionary where keys are the return values and values
                      are the compiled regex patterns.

        Returns:
            The key of the first matching pattern, or None if no match is found.
        """
        for key, pattern in patterns.items():
            if pattern.search(text):
                return key
        return None

    def _extract_rooms(self, text: str) -> Optional[int]:
        """
        Extracts the number of rooms from the text.

        Args:
            text: The text to search within.

        Returns:
            The number of rooms as an integer, or None if not found.
        """
        for pattern in self.ROOMS_PATTERNS:
            match = pattern.search(text)
            if match:
                return int(match.group(1))
        return None

    def _extract_area(self, text: str) -> Optional[float]:
        """
        Extracts the property area from the text.

        Args:
            text: The text to search within.

        Returns:
            The area in square meters as a float, or None if not found.
        """
        match = self.AREA_PATTERN.search(text)
        if match:
            return float(match.group(1).replace(',', '.'))
        return None

    def _extract_floor(self, text: str) -> Optional[str]:
        """
        Extracts floor information from the text.

        Args:
            text: The text to search within.

        Returns:
            A string representing the floor (e.g., '3/9'), or None if not found.
        """
        match = self.FLOOR_PATTERN.search(text)
        if match:
            return match.group(1)
        return None

    def _extract_price(self, text: str) -> Optional[float]:
        """
        Extracts the price from the text and converts it to USD if necessary.

        Args:
            text: The text to search within.

        Returns:
            The price in USD as a float, or None if not found.
        """
        match = self.PRICE_USD_PATTERN.search(text)
        if match:
            price_str = match.group(1).replace(',', '').replace(' ', '')
            return float(price_str)

        match = self.PRICE_RUB_PATTERN.search(text)
        if match:
            price_rub = float(match.group(1).replace(',', '').replace(' ', ''))
            # TODO: Use a real-time exchange rate API
            return round(price_rub / 90.0, 2)

        return None

    def _extract_address(self, text: str) -> Optional[str]:
        """
        Extracts a potential address from the text.

        Note: This is a simplistic implementation and may not be accurate.
              A more sophisticated NLP/NER model would be better.

        Args:
            text: The text to search within.

        Returns:
            The extracted address string, or None if not found.
        """
        match = re.search(r'(ул\.|улица|район|р-н)\s*([\w\s\.]+)', text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
        return None

    def _clean_description(self, text: str) -> str:
        """
        Cleans the description text.

        Note: This is currently a placeholder and just strips whitespace.

        Args:
            text: The text to clean.

        Returns:
            The cleaned text.
        """
        return text.strip()

    def generate_embedding(self, property_data: Dict) -> Optional[list]:
        """
        Generates a vector embedding for a property using OpenAI's API.

        The embedding is created from a consolidated string of key property
        attributes for use in semantic search.

        Args:
            property_data: A dictionary of extracted property data.

        Returns:
            A list of floats representing the vector embedding, or None if
            the embedding could not be generated.
        """
        text_parts = [
            property_data.get('transaction_type'),
            property_data.get('property_type'),
            f"{property_data.get('rooms')} комнат" if property_data.get('rooms') else None,
            f"{property_data.get('area_sqm')} м²" if property_data.get('area_sqm') else None,
            property_data.get('address'),
            property_data.get('description')
        ]

        text_to_embed = " ".join(filter(None, text_parts)).strip()

        if not text_to_embed:
            return None

        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text_to_embed
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
