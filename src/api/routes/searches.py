from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import User
from src.models.saved_search import SavedSearch
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/api/searches", tags=["Searches"])


class SavedSearchCreate(BaseModel):
    criteria: Dict[str, Any]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def save_search(
    search_in: SavedSearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Saves a user's search criteria for notifications."""

    new_saved_search = SavedSearch(user_id=current_user.id, criteria=search_in.criteria)
    db.add(new_saved_search)
    db.commit()

    return {"status": "success", "saved_search_id": new_saved_search.id}
