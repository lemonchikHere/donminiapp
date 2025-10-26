from fastapi import Depends, HTTPException, Header, status
from typing import Optional

from src.config import settings

def get_admin_user(x_telegram_user_id: Optional[str] = Header(None)):
    """
    Dependency to verify if the current user is an admin.
    Compares the user's Telegram ID from the header with the ADMIN_CHAT_ID.
    """
    if not x_telegram_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not provided",
        )

    # Ensure ADMIN_CHAT_ID is set and compare
    if not settings.ADMIN_CHAT_ID or int(x_telegram_user_id) != int(settings.ADMIN_CHAT_ID):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    return int(x_telegram_user_id)
