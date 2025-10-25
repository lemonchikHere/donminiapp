from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User
import uuid

def get_current_user(
    x_telegram_user_id: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
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
