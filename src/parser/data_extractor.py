import re
from typing import Dict, Optional
import openai
from src.config import settings

openai.api_key = settings.OPENAI_API_KEY


class PropertyDataExtractor:
    TRANSACTION_PATTERNS = {
        "sell": re.compile(r"(продам|продаю|продается|продажа)", re.IGNORECASE),
        "rent": re.compile(r"(сдам|сдаю|сдается|аренда|снять)", re.IGNORECASE),
    }

    PROPERTY_PATTERNS = {
        "apartment": re.compile(r"(квартир|кв\.|apartment)", re.IGNORECASE),
        "house": re.compile(r"(дом|house|коттедж)", re.IGNORECASE),
        "commercial": re.compile(r"(коммерч|офис|магазин|торгов)", re.IGNORECASE),
    }

    ROOMS_PATTERNS = [
        re.compile(r"(\d+)[-\s]?комн", re.IGNORECASE),
        re.compile(r"(\d+)[-\s]?к\.", re.IGNORECASE),
        re.compile(r"(\d+)[-\s]?bedroom", re.IGNORECASE),
    ]

    AREA_PATTERN = re.compile(r"(\d+[\.,]?\d*)\s*(м²|м2|кв\.м)", re.IGNORECASE)
    FLOOR_PATTERN = re.compile(r"(\d+/\d+)\s*эт", re.IGNORECASE)
    PRICE_USD_PATTERN = re.compile(r"(\d+[\s,]?\d*)\s*[\$|USD]", re.IGNORECASE)
    PRICE_RUB_PATTERN = re.compile(r"(\d+[\s,]?\d*)\s*[₽|RUB|руб]", re.IGNORECASE)

    def extract(self, text: str) -> Dict:
        """Extracts structured data from message text."""
        data = {
            "raw_text": text,
            "transaction_type": self._extract_enum(text, self.TRANSACTION_PATTERNS),
            "property_type": self._extract_enum(text, self.PROPERTY_PATTERNS),
            "rooms": self._extract_rooms(text),
            "area_sqm": self._extract_area(text),
            "floor": self._extract_floor(text),
            "price_usd": self._extract_price(text),
            "address": self._extract_address(text),
            "description": self._clean_description(text),
        }
        return data

    def _extract_enum(self, text: str, patterns: Dict) -> Optional[str]:
        for key, pattern in patterns.items():
            if pattern.search(text):
                return key
        return None

    def _extract_rooms(self, text: str) -> Optional[int]:
        """Extracts the number of rooms."""
        for pattern in self.ROOMS_PATTERNS:
            match = pattern.search(text)
            if match:
                return int(match.group(1))
        return None

    def _extract_area(self, text: str) -> Optional[float]:
        match = self.AREA_PATTERN.search(text)
        if match:
            return float(match.group(1).replace(",", "."))
        return None

    def _extract_floor(self, text: str) -> Optional[str]:
        match = self.FLOOR_PATTERN.search(text)
        if match:
            return match.group(1)
        return None

    def _extract_price(self, text: str) -> Optional[float]:
        """Extracts price and converts to USD."""
        match = self.PRICE_USD_PATTERN.search(text)
        if match:
            price_str = match.group(1).replace(",", "").replace(" ", "")
            return float(price_str)

        match = self.PRICE_RUB_PATTERN.search(text)
        if match:
            price_rub = float(match.group(1).replace(",", "").replace(" ", ""))
            # TODO: Use a real-time exchange rate API
            return round(price_rub / 90.0, 2)

        return None

    def _extract_address(self, text: str) -> Optional[str]:
        # This is a placeholder. A more sophisticated NLP/NER model would be better.
        # For now, let's look for common address-related keywords.
        match = re.search(r"(ул\.|улица|район|р-н)\s*([\w\s\.]+)", text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
        return None

    def _clean_description(self, text: str) -> str:
        # Placeholder for description cleaning logic
        return text.strip()

    def generate_embedding(self, property_data: Dict) -> list:
        """Generates a vector embedding for semantic search."""
        text_parts = [
            property_data.get("transaction_type", ""),
            property_data.get("property_type", ""),
            f"{property_data.get('rooms', '')} комнат",
            f"{property_data.get('area_sqm', '')} м²",
            property_data.get("address", ""),
            property_data.get("description", ""),
        ]

        text_to_embed = " ".join(filter(None, text_parts)).strip()

        if not text_to_embed:
            return None

        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small", input=text_to_embed
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
