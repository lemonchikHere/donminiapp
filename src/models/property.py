"""
Defines the SQLAlchemy model for a property listing.

This module contains the `Property` class, which maps to the `properties` table
in the database. It stores detailed information about real estate properties
parsed from Telegram messages.
"""

from sqlalchemy import (Column, String, Integer, Float, DateTime, Boolean,
                      Enum, Text, ARRAY)
from sqlalchemy.dialects.postgresql import UUID, BIGINT
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from .base import Base

class Property(Base):
    """
    Represents a single real estate property listing.

    Attributes:
        id (UUID): The unique identifier for the property.
        telegram_message_id (int): The ID of the Telegram message this property
                                   was parsed from.
        telegram_channel_id (int): The ID of the Telegram channel where the
                                   message was posted.
        posted_at (DateTime): The timestamp when the original message was
                              posted in the channel.

        transaction_type (Enum): The type of transaction (e.g., 'sell', 'rent').
        property_type (Enum): The type of property (e.g., 'apartment', 'house').
        rooms (int): The number of rooms in the property.
        area_sqm (float): The total area of the property in square meters.
        floor (str): The floor information (e.g., "3/9").
        price_usd (float): The price of the property in USD.
        address (str): The physical address of the property.
        latitude (float): The geographic latitude of the property.
        longitude (float): The geographic longitude of the property.
        description (str): The detailed description of the property.
        raw_text (str): The original, unprocessed text from the Telegram message.

        embedding (Vector): The vector embedding of the property description,
                            used for semantic search.

        photos (list[str]): A list of URLs to photos of the property.
        video_url (str): A URL to a video of the property.
        views_count (int): The number of views the original Telegram message received.
        is_active (bool): A flag indicating if the property listing is currently
                          active.

        created_at (DateTime): The timestamp when the property was first added to
                               the database.
        updated_at (DateTime): The timestamp when the property was last updated.
    """
    __tablename__ = 'properties'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_message_id = Column(BIGINT, unique=True, nullable=False)
    telegram_channel_id = Column(BIGINT, nullable=False)
    posted_at = Column(DateTime, nullable=False)

    transaction_type = Column(Enum('sell', 'rent', name='transaction_types'))
    property_type = Column(Enum('apartment', 'house', 'commercial', name='property_types'))
    rooms = Column(Integer)
    area_sqm = Column(Float)
    floor = Column(String(20))
    price_usd = Column(Float)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(Text)
    raw_text = Column(Text)

    # Vector embedding for semantic search
    embedding = Column(Vector(1536))

    photos = Column(ARRAY(Text))
    video_url = Column(Text)
    views_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
