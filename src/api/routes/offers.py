from fastapi import (
    APIRouter,
    Depends,
    status,
    UploadFile,
    File,
    Form,
    HTTPException,
)
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.database import get_db
from src.services.offer_service import OfferService
from src.services.notification_service import NotificationService
from src.config import settings
from aiogram import Bot

router = APIRouter(prefix="/api/offers", tags=["Offers"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_offer_with_upload(
    transactionType: str = Form(...),
    propertyType: str = Form(...),
    address: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    area: Optional[str] = Form(None),
    floors: Optional[str] = Form(None),
    rooms: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    photos: List[UploadFile] = File([]),
    video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Accepts a new property offer with file uploads from a user.
    Creates a property record with 'moderation' status and notifies the admin.
    """
    offer_service = OfferService(db)

    form_data = locals()

    try:
        new_property = await offer_service.create_offer_property(
            offer_data=form_data, photos=photos, video=video
        )
    except Exception as e:
        # Basic error handling
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create offer: {e}",
        )

    # Notify admin
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        message = (
            f"🏠 Новая заявка на модерацию!\n\n"
            f"**ID объекта:** `{new_property.id}`\n"
            f"**Тип сделки:** {transactionType}\n"
            f"**Тип недвижимости:** {propertyType}\n"
            f"**Адрес:** {address}\n"
            f"**Комнат:** {rooms or 'N/A'}\n"
            f"**Цена:** ${price or 'N/A'}\n\n"
            f"**Загружено фото:** {len(new_property.photos)}\n"
            f"**Загружено видео:** {'Да' if new_property.video_url else 'Нет'}\n\n"
            f"--- Контакты ---\n"
            f"**Имя:** {name}\n"
            f"**Телефон:** {phone}"
        )
        if settings.ADMIN_CHAT_ID:
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID, text=message, parse_mode="Markdown"
            )
    finally:
        await bot.session.close()

    return {"status": "pending_moderation", "property_id": new_property.id}
