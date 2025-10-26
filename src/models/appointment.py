from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from src.database import Base

class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey('properties.id', ondelete="CASCADE"), nullable=False)
    requested_datetime = Column(DateTime, nullable=False)
    status = Column(Enum('pending', 'confirmed', 'cancelled', 'completed', name='appointment_status'), default='pending')
    user_phone = Column(String)
    user_name = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
