"""
Defines the SQLAlchemy models for users and their favorites.

This module contains the `User` class, which maps to the `users` table,
and the `Favorite` class, which maps to the `favorites` table, representing
a user's saved properties.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, BIGINT
import uuid
from datetime import datetime
from .base import Base

class User(Base):
    """
    Represents a user of the application.

    Users are identified by their unique Telegram user ID.

    Attributes:
        id (UUID): The unique identifier for the user in the database.
        telegram_user_id (int): The user's unique Telegram ID.
        username (str): The user's Telegram username.
        phone (str): The user's contact phone number.
        created_at (DateTime): The timestamp when the user was first created.
    """
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_user_id = Column(BIGINT, unique=True, nullable=False)
    username = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Favorite(Base):
    """
    Represents a property that a user has marked as a favorite.

    This model creates a many-to-many relationship between users and properties.

    Attributes:
        id (UUID): The unique identifier for the favorite entry.
        user_id (UUID): The ID of the user who favorited the property.
        property_id (UUID): The ID of the favorited property.
        notes (str): Any personal notes the user has added about the favorite.
        created_at (DateTime): The timestamp when the property was favorited.
    """
    __tablename__ = 'favorites'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey('properties.id'), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
