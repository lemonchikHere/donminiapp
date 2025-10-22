"""
API endpoints for managing property viewing appointments.

This router provides endpoints for creating, retrieving, and canceling
appointments for users to view properties.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from src.database import get_db
from src.models.appointment import Appointment
from src.models.user import User
from src.models.property import Property
from src.api.dependencies import get_current_user
from src.config import settings

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

class AppointmentCreate(BaseModel):
    """
    Pydantic model for creating a new appointment.
    """
    property_id: UUID
    """The ID of the property for the appointment."""
    requested_datetime: datetime
    """The desired date and time for the viewing."""
    user_phone: str
    """The user's contact phone number."""
    user_name: str
    """The user's name."""
    notes: Optional[str] = None
    """Optional notes from the user."""

class AppointmentResponse(BaseModel):
    """
    Pydantic model for returning appointment data.
    """
    id: UUID
    """The unique ID of the appointment."""
    property_id: UUID
    """The ID of the property for the appointment."""
    requested_datetime: datetime
    """The scheduled date and time for the viewing."""
    status: str
    """The current status of the appointment (e.g., 'pending')."""
    user_name: str
    """The user's name."""
    notes: Optional[str] = None
    """Optional notes from the user."""

    class Config:
        """Pydantic configuration."""
        orm_mode = True
        """Allows the model to be populated from an ORM object."""

async def send_telegram_notification(chat_id: str, message: str):
    """
    Sends a notification message to a Telegram chat.

    Note: This is a placeholder implementation. In a real application,
          this would integrate with an `aiogram` bot instance.

    Args:
        chat_id: The target Telegram chat ID.
        message: The message text to send.
    """
    print(f"--- SENDING NOTIFICATION TO {chat_id} ---")
    print(message)
    print("-----------------------------------------")
    pass

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new appointment to view a property.

    This endpoint books a viewing for the current user for a specified property.
    On successful creation, it also sends a notification to the admin.

    Args:
        appointment_in: The appointment creation data.
        db: The database session.
        current_user: The currently authenticated user.

    Raises:
        HTTPException: 404 if the property is not found.

    Returns:
        The newly created appointment details.
    """
    prop = db.query(Property).filter(Property.id == appointment_in.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    new_appointment = Appointment(
        user_id=current_user.id,
        property_id=appointment_in.property_id,
        requested_datetime=appointment_in.requested_datetime,
        user_phone=appointment_in.user_phone,
        user_name=appointment_in.user_name,
        notes=appointment_in.notes,
        status='pending'
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    # Send notification
    if settings.ADMIN_CHAT_ID:
        message = (
            f"🔔 Новая запись на просмотр!\n\n"
            f"Объект: {prop.address or 'N/A'}\n"
            f"Цена: ${prop.price_usd or 'N/A'}\n\n"
            f"Клиент: {appointment_in.user_name}\n"
            f"Телефон: {appointment_in.user_phone}\n"
            f"Дата: {appointment_in.requested_datetime.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Примечания: {appointment_in.notes or 'Нет'}"
        )
        await send_telegram_notification(chat_id=settings.ADMIN_CHAT_ID, message=message)

    return new_appointment

@router.get("/", response_model=List[AppointmentResponse])
async def get_user_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all appointments for the current user.

    Args:
        db: The database session.
        current_user: The currently authenticated user.

    Returns:
        A list of the user's appointments.
    """
    appointments = db.query(Appointment).filter(Appointment.user_id == current_user.id).all()
    return appointments

@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancels an existing appointment for the current user.

    The appointment status is set to 'cancelled'. Appointments that are already
    completed or cancelled cannot be modified.

    Args:
        appointment_id: The ID of the appointment to cancel.
        db: The database session.
        current_user: The currently authenticated user.

    Raises:
        HTTPException: 404 if the appointment is not found.
        HTTPException: 400 if the appointment cannot be cancelled due to its
                       current status.

    Returns:
        The updated appointment with the 'cancelled' status.
    """
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.user_id == current_user.id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status not in ['pending', 'confirmed']:
         raise HTTPException(status_code=400, detail="Cannot cancel an appointment that is already completed or cancelled.")

    appointment.status = 'cancelled'
    db.commit()
    db.refresh(appointment)
    return appointment
