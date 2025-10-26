from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
    Enum,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, BIGINT
import uuid
from datetime import datetime

Base = declarative_base()


class TestProperty(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_message_id = Column(BIGINT, unique=True, nullable=False)
    telegram_channel_id = Column(BIGINT, nullable=False)
    posted_at = Column(DateTime, nullable=False)

    transaction_type = Column(Enum("sell", "rent", name="transaction_types"))
    property_type = Column(
        Enum("apartment", "house", "commercial", name="property_types")
    )
    rooms = Column(Integer)
    area_sqm = Column(Float)
    floor = Column(String(20))
    price_usd = Column(Float)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(Text)
    raw_text = Column(Text)

    embedding = Column(Text)
    photos = Column(Text)
    video_url = Column(Text)
    views_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
