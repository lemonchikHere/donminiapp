from fastapi import APIRouter
from pydantic import BaseModel
from src.config import settings

router = APIRouter(prefix="/api/config", tags=["Config"])


class ClientConfig(BaseModel):
    yandex_maps_api_key: str


@router.get("/", response_model=ClientConfig)
async def get_client_config():
    """
    Provides public configuration variables to the client.
    """
    return ClientConfig(yandex_maps_api_key=settings.YANDEX_API_KEY)
