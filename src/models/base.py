"""
Defines the base class for all SQLAlchemy models.

This module provides a declarative base that all other models in the
application should inherit from. This allows SQLAlchemy's declarative
extension to discover and manage all the models.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
"""The declarative base for SQLAlchemy models."""
