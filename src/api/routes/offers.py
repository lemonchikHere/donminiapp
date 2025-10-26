from fastapi import APIRouter, Depends, status, Form, UploadFile
from typing import Optional
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from src.database import get_db
from src.config import settings
from aiogram import Bot

router = APIRouter(prefix="/api/offers", tags=["Offers"])

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_offer(
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
    Accepts a new property offer from a user via a form and notifies the admin.
    """
    bot = Bot(token=settings.BOT_TOKEN)

    message = (
        f"🏠 Новое предложение объекта!\n\n"
        f"**Тип сделки:** {transactionType}\n"
        f"**Тип недвижимости:** {propertyType}\n"
        f"**Адрес:** {address}\n"
        f"**Комнат:** {rooms or 'N/A'}\n"
        f"**Площадь:** {area or 'N/A'} м²\n"
        f"**Этаж:** {floors or 'N/A'}\n"
        f"**Цена:** ${price or 'N/A'}\n\n"
        f"**Описание:**\n{description or 'Нет'}\n\n"
        f"--- Контакты ---\n"
        f"**Имя:** {name}\n"
        f"**Телефон:** {phone}"
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
