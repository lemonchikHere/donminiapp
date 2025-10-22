"""
API endpoints for providing data to the map interface.

This router serves data specifically formatted for displaying properties
on an interactive map in the frontend.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from src.database import get_db
from src.models.property import Property

router = APIRouter(prefix="/api/map", tags=["Map"])

class MapProperty(BaseModel):
    """
    Pydantic model for representing a property on the map.

    This model contains a minimal set of data needed to plot a pin on the map
    and show a brief summary.
    """
    id: UUID
    """The unique ID of the property."""
    latitude: float
    """The geographic latitude of the property."""
    longitude: float
    """The geographic longitude of the property."""
    price_usd: Optional[float]
    """The price of the property in USD."""
    title: str
    """A short title for the property (e.g., '2-комн квартира')."""

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        """Allows the model to be populated from an ORM object."""

@router.get("/properties", response_model=List[MapProperty])
async def get_map_properties(db: Session = Depends(get_db)):
    """
    Retrieves all active properties that have geographic coordinates.

    This endpoint is designed to efficiently provide the necessary data for
    populating the main property map in the user interface.

    Args:
        db: The database session.

    Returns:
        A list of `MapProperty` objects.
    """
    properties = db.query(Property).filter(
        Property.is_active == True,
        Property.latitude != None,
        Property.longitude != None
    ).all()

    # The conversion to MapProperty happens automatically by FastAPI,
    # but doing it manually allows for custom field creation like `title`.
    response_data = []
    for prop in properties:
        response_data.append(
             MapProperty(
                id=prop.id,
                latitude=prop.latitude,
                longitude=prop.longitude,
                price_usd=prop.price_usd,
                title=f"{prop.rooms or ''}-комн {prop.property_type or ''}"
            )
        )
    return response_data
