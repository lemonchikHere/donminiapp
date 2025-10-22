from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from src.database import get_db
from src.models.user import Favorite, User
from src.models.property import Property
from src.api.dependencies import get_current_user
from src.api.schemas import PropertyResponse

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])

class FavoriteCreate(BaseModel):
    property_id: UUID
    notes: Optional[str] = None

@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    favorite_in: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adds a property to the user's favorites."""
    # Check if property exists
    prop = db.query(Property).filter(Property.id == favorite_in.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check if already in favorites
    existing_fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.property_id == favorite_in.property_id
    ).first()
    if existing_fav:
        raise HTTPException(status_code=409, detail="Property already in favorites")

    new_fav = Favorite(
        user_id=current_user.id,
        property_id=favorite_in.property_id,
        notes=favorite_in.notes
    )
    db.add(new_fav)
    db.commit()
    return {"status": "success", "favorite_id": new_fav.id}

@router.get("/", response_model=List[PropertyResponse])
async def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all properties from the user's favorites."""
    user_favorites = db.query(Property).join(Favorite).filter(Favorite.user_id == current_user.id).all()

    return [
        PropertyResponse(
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
            is_favorite=True
        ) for prop in user_favorites
    ]

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    property_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Removes a property from the user's favorites."""
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.property_id == property_id
    ).first()

    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(fav)
    db.commit()
    return
