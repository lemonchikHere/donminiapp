from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from .base import Base

class SavedSearch(Base):
    __tablename__ = 'saved_searches'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # We can store the flexible search criteria as a JSON object
    criteria = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
