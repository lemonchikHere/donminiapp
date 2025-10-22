"""
Provides a service for geocoding addresses using the Yandex Maps API.

This module defines the `GeocodingService` class, which is responsible for
converting physical addresses into geographic coordinates (latitude and longitude).
"""

import httpx
from typing import Optional, Tuple
from src.config import settings

class GeocodingService:
    """
    A service to interact with the Yandex Maps Geocoding API.
    """
    BASE_URL = "https://geocode-maps.yandex.ru/1.x/"
    """The base URL for the Yandex Geocoding API."""

    def __init__(self, api_key: str = settings.YANDEX_API_KEY):
        """
        Initializes the GeocodingService.

        Args:
            api_key: The API key for the Yandex Maps API. Defaults to the
                     value in the application settings.
        """
        self.api_key = api_key

    async def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Fetches the geographic coordinates for a given address.

        Args:
            address: The address to geocode.

        Returns:
            A tuple containing the latitude and longitude, or None if the
            address could not be geocoded or an error occurred.
        """
        if not self.api_key or not address:
            return None

        params = {
            "apikey": self.api_key,
            "geocode": address,
            "format": "json",
            "results": 1
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
"""A global instance of the GeocodingService to be used throughout the application."""
