"""
Defines FastAPI dependencies for handling common API logic.

This module contains functions that can be injected into API route handlers
to perform tasks like authenticating users, managing database sessions, etc.
"""

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User

def get_current_user(
    x_telegram_user_id: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current user based on a Telegram ID.

    This function retrieves the user corresponding to the Telegram ID provided
    in the `X-Telegram-User-Id` header. If the header is missing or invalid,
    it raises an HTTP exception. If the user does not exist in the database,
    it automatically creates and saves a new user.

    Args:
        x_telegram_user_id: The Telegram User ID, extracted from the request
                            header.
        db: The SQLAlchemy database session, injected by FastAPI.

    Raises:
        HTTPException: If the `X-Telegram-User-Id` header is missing or
                       the ID format is invalid.

    Returns:
        The authenticated `User` object.
    """
    if not x_telegram_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram User ID not provided",
        )

    try:
        telegram_user_id = int(x_telegram_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram User ID format",
        )

    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()

    if user is None:
        # Auto-register user if not found
        new_user = User(
            telegram_user_id=telegram_user_id,
            username=f"user_{telegram_user_id}" # Placeholder
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    return user
