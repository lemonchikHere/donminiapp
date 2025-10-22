from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from src.api.schemas import PropertyResponse, SearchResponse
from src.database import get_db
from src.models.property import Property
from src.models.user import Favorite, User
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/api/properties", tags=["Properties"])

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property_details(
    property_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves full details for a single property.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    is_favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.property_id == prop.id
    ).first() is not None

    return PropertyResponse(
        id=str(prop.id),
        title=f"{prop.rooms or ''}-комн {prop.property_type or ''}, {prop.area_sqm or ''}м²",
        price_usd=prop.price_usd,
        rooms=prop.rooms,
        area_sqm=prop.area_sqm,
        address=prop.address,
        description=prop.description[:200] + '...' if prop.description and len(prop.description) > 200 else prop.description,
        photos=prop.photos,
        similarity_score=None,
        telegram_link=f"https://t.me/c/{prop.telegram_channel_id}/{prop.telegram_message_id}",
        is_favorite=is_favorite
    )

@router.get("/similar/{property_id}", response_model=SearchResponse)
async def get_similar_properties(
    property_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finds properties with similar embeddings.
    """
    source_prop = db.query(Property).filter(Property.id == property_id).first()
    if not source_prop or not source_prop.embedding:
        raise HTTPException(status_code=404, detail="Source property or its embedding not found")

    # Perform a vector similarity search
    results = db.query(
        Property,
        Property.embedding.cosine_distance(source_prop.embedding).label('distance')
    ).filter(Property.id != property_id).order_by('distance').limit(10).all()

    # Format response
    properties_response = []
    user_favorites = {fav.property_id for fav in db.query(Favorite.property_id).filter(Favorite.user_id == current_user.id).all()}

    for prop, distance in results:
        properties_response.append(PropertyResponse(
            id=str(prop.id),
            title=f"{prop.rooms or ''}-комн {prop.property_type or ''}, {prop.area_sqm or ''}м²",
            price_usd=prop.price_usd,
            rooms=prop.rooms,
            area_sqm=prop.area_sqm,
            address=prop.address,
            description=prop.description[:200] if prop.description else "",
            photos=prop.photos,
            similarity_score=round(1 - distance, 2),
            telegram_link=f"https://t.me/c/{prop.telegram_channel_id}/{prop.telegram_message_id}",
            is_favorite=prop.id in user_favorites
        ))

    return SearchResponse(
        results=properties_response,
        total=len(properties_response)
    )
