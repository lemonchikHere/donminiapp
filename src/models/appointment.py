"""
Defines the SQLAlchemy model for an appointment.

This module contains the `Appointment` class, which maps to the `appointments`
table in the database. It stores information about user requests to view a
property.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from .base import Base

class Appointment(Base):
    """
    Represents a user's request to view a property.

    Attributes:
        id (UUID): The unique identifier for the appointment.
        user_id (UUID): The ID of the user who requested the appointment.
        property_id (UUID): The ID of the property to be viewed.
        requested_datetime (DateTime): The date and time the user wishes to
                                       view the property.
        status (Enum): The current status of the appointment (e.g., pending,
                       confirmed).
        user_phone (str): The contact phone number provided by the user.
        user_name (str): The name provided by the user.
        notes (str): Any additional notes or comments from the user.
        created_at (DateTime): The timestamp when the appointment was created.
    """
    __tablename__ = 'appointments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey('properties.id'), nullable=False)
    requested_datetime = Column(DateTime, nullable=False)
    status = Column(Enum('pending', 'confirmed', 'cancelled', 'completed', name='appointment_status'), default='pending')
    user_phone = Column(String)
    user_name = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
