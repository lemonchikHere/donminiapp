from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from src.services.ai_assistant_service import (
    get_ai_assistant_service,
    AIAssistantService,
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


class PropertyInChat(BaseModel):
    id: UUID
    title: str
    address: Optional[str] = None
    price_usd: Optional[float] = None
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    type: str
    content: Optional[str] = None
    summary: Optional[str] = None
    properties: Optional[List[PropertyInChat]] = []

    class Config:
        from_attributes = True


@router.post("/")
async def handle_chat_message(
    chat_request: ChatRequest,
    ai_assistant: AIAssistantService = Depends(get_ai_assistant_service),
) -> ChatResponse:
    """
    Receives a message from the Mini App chat interface,
    processes it with the AI assistant, and returns the response.
    """
    if not chat_request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response = await ai_assistant.get_response(chat_request.message)
    return response
