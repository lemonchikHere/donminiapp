"""
Handles database connection and session management.

This module sets up the SQLAlchemy engine and provides a dependency
for FastAPI routes to obtain a database session. It ensures that
database connections are properly managed and closed after each request.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings

engine = create_engine(settings.database_url)
"""The global SQLAlchemy engine, configured from the application settings."""

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""A factory for creating new database sessions."""

def get_db():
    """
    FastAPI dependency to get a database session.

    This is a generator function that yields a new database session for each
    request. It ensures that the session is always closed, even if errors
    occur during the request processing.

    Yields:
        Session: A new SQLAlchemy Session object.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
