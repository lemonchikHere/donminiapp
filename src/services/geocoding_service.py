import httpx
from typing import Optional, Tuple
from src.config import settings


class GeocodingService:
    BASE_URL = "https://geocode-maps.yandex.ru/1.x/"

    def __init__(self, api_key: str = settings.YANDEX_API_KEY):
        self.api_key = api_key

    async def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        if not self.api_key or not address:
            return None

        params = {
            "apikey": self.api_key,
            "geocode": address,
            "format": "json",
            "results": 1,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                geo_objects = data["response"]["GeoObjectCollection"]["featureMember"]
                if not geo_objects:
                    return None

                point = geo_objects[0]["GeoObject"]["Point"]["pos"]
                longitude, latitude = map(float, point.split())

                return latitude, longitude
            except (httpx.RequestError, KeyError, IndexError) as e:
                print(f"Failed to geocode address '{address}': {e}")
                return None


geocoding_service = GeocodingService()
