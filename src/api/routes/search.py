"""
API endpoints for searching and filtering property listings.

This router provides a powerful search endpoint that combines semantic search
based on text queries with structured filtering based on property attributes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
import openai

from src.database import get_db
from src.models.property import Property
from src.models.user import Favorite, User
from src.api.dependencies import get_current_user
from src.config import settings

openai.api_key = settings.OPENAI_API_KEY

router = APIRouter(prefix="/api", tags=["Search"])

class PropertySearchRequest(BaseModel):
    """
    Pydantic model for a property search request.
    Defines the available filters for a property search.
    """
    transaction_type: Optional[str] = None
    """Filter by 'sell' or 'rent'."""
    property_types: Optional[List[str]] = None
    """A list of property types to include (e.g., ['apartment', 'house'])."""
    rooms: Optional[int] = None
    """Filter by the exact number of rooms."""
    district: Optional[str] = None
    """Text to search for in the address/description related to district."""
    budget_min: Optional[float] = None
    """The minimum price in USD."""
    budget_max: Optional[float] = None
    """The maximum price in USD."""
    query_text: Optional[str] = ""
    """A free-text query for semantic search."""

class PropertyResponse(BaseModel):
    """
    Pydantic model for a single property item in a search response.
    """
    id: UUID
    """The unique ID of the property."""
    title: str
    """A generated title for the property."""
    price_usd: Optional[float]
    """The price in USD."""
    rooms: Optional[int]
    """The number of rooms."""
    area_sqm: Optional[float]
    """The area in square meters."""
    address: Optional[str]
    """The property's address."""
    description: Optional[str]
    """A truncated description of the property."""
    photos: Optional[List[str]]
    """A list of URLs for property photos."""
    similarity_score: Optional[float]
    """The semantic similarity score (0.0 to 1.0) from the search query."""
    telegram_link: str
    """A direct link to the original Telegram message."""
    is_favorite: bool
    """Indicates if the current user has favorited this property."""

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        """Allows the model to be populated from an ORM object."""

class SearchResponse(BaseModel):
    """
    Pydantic model for the overall search response.
    """
    results: List[PropertyResponse]
    """The list of properties matching the search criteria."""
    total: int
    """The total number of results returned."""

@router.post("/search", response_model=SearchResponse)
async def search_properties(
    search_request: PropertySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Searches for properties using a combination of semantic search and filters.

    This endpoint generates a vector embedding from the search query text and
    uses it to find semantically similar properties. It then applies the
    provided structured filters (e.g., price, rooms) to the results.

    Args:
        search_request: The search criteria and filters.
        db: The database session.
        current_user: The currently authenticated user.

    Raises:
        HTTPException: 500 if the query embedding generation fails.

    Returns:
        A `SearchResponse` object containing the filtered and sorted list of
        properties.
    """
    # 1. Generate embedding for the search query
    full_query_text = (
        f"{search_request.transaction_type or ''} "
        f"{' '.join(search_request.property_types or [])} "
        f"{str(search_request.rooms) + ' комнат' if search_request.rooms else ''} "
        f"{search_request.district or ''} "
        f"{search_request.query_text or ''}"
    ).strip()

    query_embedding = None
    if full_query_text:
        try:
            response = openai.embeddings.create(model="text-embedding-3-small", input=full_query_text)
            query_embedding = response.data[0].embedding
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate query embedding: {e}")

    # 2. Base query
    if query_embedding:
        query = db.query(
            Property,
            Property.embedding.cosine_distance(query_embedding).label('distance')
        )
    else:
        # If no text query, select all properties without distance calculation
        query = db.query(Property, None)

    # 3. Apply filters
    if search_request.transaction_type:
        query = query.filter(Property.transaction_type == search_request.transaction_type)
    if search_request.property_types:
        query = query.filter(Property.property_type.in_(search_request.property_types))
    if search_request.rooms:
        query = query.filter(Property.rooms == search_request.rooms)
    if search_request.budget_min:
        query = query.filter(Property.price_usd >= search_request.budget_min)
    if search_request.budget_max:
        query = query.filter(Property.price_usd <= search_request.budget_max)

    # 4. Order by similarity or date and limit results
    if query_embedding:
        results = query.order_by('distance').limit(20).all()
    else:
        results = query.order_by(Property.posted_at.desc()).limit(20).all()

    # 5. Format response
    properties_response = []
    user_favorites_ids = {fav.property_id for fav in db.query(Favorite.property_id).filter(Favorite.user_id == current_user.id).all()}

    for item in results:
        prop = item[0] if isinstance(item, tuple) else item
        distance = item[1] if isinstance(item, tuple) else None

        properties_response.append(PropertyResponse(
            id=prop.id,
            title=f"{prop.rooms or ''}-комн {prop.property_type or ''}, {prop.area_sqm or ''}м²",
            price_usd=prop.price_usd,
            rooms=prop.rooms,
            area_sqm=prop.area_sqm,
            address=prop.address,
            description=prop.description[:200] + '...' if prop.description and len(prop.description) > 200 else prop.description,
            photos=prop.photos,
            similarity_score=round(1 - distance, 2) if distance is not None else None,
            telegram_link=f"https://t.me/c/{prop.telegram_channel_id}/{prop.telegram_message_id}",
            is_favorite=prop.id in user_favorites_ids
        ))

    return SearchResponse(
        results=properties_response,
        total=len(properties_response)
    )
