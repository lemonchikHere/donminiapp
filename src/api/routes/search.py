from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import openai

from src.database import get_db
from src.models.property import Property
from src.models.user import Favorite, User
from src.api.dependencies import get_current_user
from src.config import settings

openai.api_key = settings.OPENAI_API_KEY

router = APIRouter(prefix="/api", tags=["Search"])

class PropertySearchRequest(BaseModel):
    transaction_type: Optional[str] = None
    property_types: Optional[List[str]] = None
    rooms: Optional[int] = None
    district: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    query_text: Optional[str] = ""

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

class SearchResponse(BaseModel):
    results: List[PropertyResponse]
    total: int

@router.post("/search", response_model=SearchResponse)
async def search_properties(
    search_request: PropertySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """
    Performs semantic search for properties using vector similarity and applies filters.
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
        query = db.query(Property, None) # No distance calculation if no text query

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

    # 4. Get total count for pagination
    total_count = query.count()

    # 5. Order by similarity, apply pagination and get results
    if query_embedding:
        results = query.order_by('distance').offset(offset).limit(limit).all()
    else:
        results = query.order_by(Property.posted_at.desc()).offset(offset).limit(limit).all()

    # 6. Format response
    properties_response = []
    user_favorites = {fav.property_id for fav in db.query(Favorite.property_id).filter(Favorite.user_id == current_user.id).all()}

    for item in results:
        prop = item[0] if isinstance(item, tuple) else item
        distance = item[1] if isinstance(item, tuple) else None

        properties_response.append(PropertyResponse(
            id=str(prop.id),
            title=f"{prop.rooms or ''}-комн {prop.property_type or ''}, {prop.area_sqm or ''}м²",
            price_usd=prop.price_usd,
            rooms=prop.rooms,
            area_sqm=prop.area_sqm,
            address=prop.address,
            description=prop.description[:200] if prop.description else "",
            photos=prop.photos,
            similarity_score=round(1 - distance, 2) if distance is not None else None,
            telegram_link=f"https://t.me/c/{prop.telegram_channel_id}/{prop.telegram_message_id}",
            is_favorite=prop.id in user_favorites
        ))

    return SearchResponse(
        results=properties_response,
        total=total_count
    )
