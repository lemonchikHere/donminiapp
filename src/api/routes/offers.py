from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.notification_service import NotificationService # We can reuse this
from src.config import settings
from src.api.schemas import SanitizedString
from aiogram import Bot

router = APIRouter(prefix="/api/offers", tags=["Offers"])

class OfferCreate(BaseModel):
    transactionType: SanitizedString
    propertyType: SanitizedString
    address: SanitizedString
    area: Optional[SanitizedString] = None
    floors: Optional[SanitizedString] = None
    rooms: Optional[SanitizedString] = None
    price: Optional[SanitizedString] = None
    description: Optional[SanitizedString] = None
    name: SanitizedString
    phone: SanitizedString

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_offer(
    offer_in: OfferCreate,
    db: Session = Depends(get_db)
):
    """
    Accepts a new property offer from a user and notifies the admin.
    """
    bot = Bot(token=settings.BOT_TOKEN)

    message = (
        f"🏠 Новое предложение объекта!\n\n"
        f"**Тип сделки:** {offer_in.transactionType}\n"
        f"**Тип недвижимости:** {offer_in.propertyType}\n"
        f"**Адрес:** {offer_in.address}\n"
        f"**Комнат:** {offer_in.rooms or 'N/A'}\n"
        f"**Площадь:** {offer_in.area or 'N/A'} м²\n"
        f"**Этаж:** {offer_in.floors or 'N/A'}\n"
        f"**Цена:** ${offer_in.price or 'N/A'}\n\n"
        f"**Описание:**\n{offer_in.description or 'Нет'}\n\n"
        f"--- Контакты ---\n"
        f"**Имя:** {offer_in.name}\n"
        f"**Телефон:** {offer_in.phone}"
    )

    if settings.ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )
        finally:
            await bot.session.close()


    return {"status": "accepted"}
