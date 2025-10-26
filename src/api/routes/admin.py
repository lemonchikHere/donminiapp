from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from src.database import get_db
from src.models.property import Property
from src.api.dependencies import get_admin_user
from src.api.schemas.property import PropertySummary # Assuming a schema exists, will create if not

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(get_admin_user)]
)

@router.get("/moderation-queue", response_model=List[PropertySummary])
async def get_moderation_queue(db: Session = Depends(get_db)):
    """
    Retrieves all properties with the 'moderation' status.
    """
    properties = db.query(Property).filter(Property.status == 'moderation').all()
    return properties

@router.post("/properties/{property_id}/approve", status_code=status.HTTP_200_OK)
async def approve_property(property_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Approves a property by changing its status to 'active'.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if prop.status != 'moderation':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Property is not pending moderation")

    prop.status = 'active'
    db.commit()

    return {"status": "approved", "property_id": prop.id}

@router.delete("/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def reject_and_delete_property(property_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Rejects a property by deleting it from the database.
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    db.delete(prop)
    db.commit()

    return
