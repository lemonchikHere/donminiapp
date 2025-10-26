from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class PropertySummary(BaseModel):
    id: uuid.UUID
    transaction_type: Optional[str] = None
    property_type: Optional[str] = None
    rooms: Optional[int] = None
    area_sqm: Optional[float] = None
    floor: Optional[str] = None
    price_usd: Optional[float] = None
    address: Optional[str] = None
    description: Optional[str] = None
    photos: Optional[List[str]] = []
    video_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
