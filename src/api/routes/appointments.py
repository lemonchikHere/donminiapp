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
# from src.services.notification_service import send_telegram_notification # To be created

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

class AppointmentCreate(BaseModel):
    property_id: UUID
    requested_datetime: datetime
    user_phone: str
    user_name: str
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: UUID
    property_id: UUID
    requested_datetime: datetime
    status: str
    user_name: str
    notes: Optional[str] = None

    class Config:
        orm_mode = True

async def send_telegram_notification(chat_id: int, message: str):
    # This is a placeholder for the actual notification logic using aiogram
    print(f"--- SENDING NOTIFICATION TO {chat_id} ---")
    print(message)
    print("-----------------------------------------")
    # In a real app:
    # bot = Bot(token=settings.BOT_TOKEN)
    # await bot.send_message(chat_id=chat_id, text=message)
    pass

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Books a viewing appointment and notifies the admin."""
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
    """Gets all appointments for the current user."""
    appointments = db.query(Appointment).filter(Appointment.user_id == current_user.id).all()
    return appointments

@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancels an appointment."""
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
