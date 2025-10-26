from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional
from src.config import settings

router = APIRouter(prefix="/api/config", tags=["Config"])

class ClientConfig(BaseModel):
    yandex_maps_api_key: str
    is_admin: bool = False

@router.get("/", response_model=ClientConfig)
async def get_client_config(x_telegram_user_id: Optional[str] = Header(None)):
    """
    Provides public configuration variables to the client.
    Includes an `is_admin` flag if the user's ID matches the admin ID.
    """
    is_admin = False
    if settings.ADMIN_CHAT_ID and x_telegram_user_id:
        try:
            if int(x_telegram_user_id) == int(settings.ADMIN_CHAT_ID):
                is_admin = True
        except (ValueError, TypeError):
            # Ignore if header value is not a valid integer
            pass

    return ClientConfig(
        yandex_maps_api_key=settings.YANDEX_API_KEY,
        is_admin=is_admin
    )
