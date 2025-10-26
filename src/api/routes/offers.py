import uuid
from fastapi import APIRouter, Depends, status, Form, UploadFile, File, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from src.database import get_db
from src.config import settings
from aiogram import Bot
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/offers", tags=["Offers"])

# Ensure media directory exists
MEDIA_DIRECTORY = "media"
os.makedirs(MEDIA_DIRECTORY, exist_ok=True)


async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Saves an uploaded file to a destination and returns the public path."""
    try:
        with open(destination, "wb") as buffer:
            buffer.write(await upload_file.read())
        return f"/{destination}"
    except Exception as e:
        logger.error(f"Failed to save file {upload_file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Could not save file.")


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
    Accepts a new property offer, saves uploaded files, and notifies the admin.
    """
    photo_paths = []
    for photo in photos:
        if photo and photo.filename:
            unique_filename = f"{uuid.uuid4()}_{photo.filename}"
            destination = os.path.join(MEDIA_DIRECTORY, unique_filename)
            public_path = await save_upload_file(photo, destination)
            photo_paths.append(public_path)

    video_path = None
    if video and video.filename:
        unique_filename = f"{uuid.uuid4()}_{video.filename}"
        destination = os.path.join(MEDIA_DIRECTORY, unique_filename)
        video_path = await save_upload_file(video, destination)

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
        f"**Телефон:** {phone}\n\n"
        f"**Фото:** {', '.join(photo_paths) if photo_paths else 'Нет'}\n"
        f"**Видео:** {video_path or 'Нет'}"
    )

    if settings.ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID, text=message, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
        finally:
            await bot.session.close()

    # The original task did not include saving the offer to the DB, just notifying.
    # Returning the paths for now, but a real implementation would save the offer.
    return {
        "status": "accepted",
        "saved_photos": photo_paths,
        "saved_video": video_path,
    }
