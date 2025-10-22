from typing import List, Optional
from pydantic import BaseModel, validator
from src.config import settings

class PropertyResponse(BaseModel):
    id: str
    title: str
    price_usd: Optional[float]
    rooms: Optional[int]
    area_sqm: Optional[float]
    address: Optional[str]
    description: Optional[str]
    photos: Optional[List[str]]
    similarity_score: Optional[float]
    telegram_link: str
    is_favorite: bool

    @validator("photos", pre=True, each_item=True)
    def convert_photo_paths_to_urls(cls, v):
        if v and isinstance(v, str):
            # Prepend the base URL, ensuring no double slashes
            return f"{settings.API_BASE_URL.strip('/')}/{v.lstrip('/')}"
        return v

class SearchResponse(BaseModel):
    results: List[PropertyResponse]
    total: int
