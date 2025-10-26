# src/models/__init__.py
# This file imports all models, ensuring that Base knows about them.
from .base import Base
from .user import User, Favorite
from .property import Property
from .appointment import Appointment

__all__ = [
    'Base',
    'User',
    'Favorite',
    'Property',
    'Appointment',
]
