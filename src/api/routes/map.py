from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from src.database import get_db
from src.models.property import Property

router = APIRouter(prefix="/api/map", tags=["Map"])

class MapProperty(BaseModel):
    id: str
    latitude: float
    longitude: float
    price_usd: float
    title: str

@router.get("/properties", response_model=List[MapProperty])
async def get_map_properties(db: Session = Depends(get_db)):
    """
    Retrieves all active properties with coordinates for map display.
    """
    properties = db.query(Property).filter(
        Property.is_active == True,
        Property.latitude != None,
        Property.longitude != None
    ).all()

    return [
        MapProperty(
            id=str(prop.id),
            latitude=prop.latitude,
            longitude=prop.longitude,
            price_usd=prop.price_usd,
            title=f"{prop.rooms or ''}-комн {prop.property_type or ''}"
        ) for prop in properties
    ]
