#!/usr/bin/env python3
"""
Database initialization script for Don Estate application.
Creates all necessary tables and extensions.
"""
import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import engine
from src.models.base import Base
# Import all models to ensure they are registered with Base
from src.models.property import Property
from src.models.user import User, Favorite
from src.models.saved_search import SavedSearch

def init_database():
    """Initialize the database by creating all tables and extensions."""
    print("Initializing database...")

    with engine.connect() as conn:
        print("Attempting to create vector extension...")
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            print("Vector extension created or already exists.")
        except ProgrammingError as e:
            # This might happen in environments where the user doesn't have superuser privileges.
            # We log it but continue, as it might have been created manually.
            print(f"Warning: Could not create vector extension: {e}", file=sys.stderr)
            print("Please ensure the 'vector' extension is enabled in your PostgreSQL database.", file=sys.stderr)
        conn.commit()


    print("Creating database tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("Database initialized successfully!")
    print("Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    init_database()
