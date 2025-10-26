#!/usr/bin/env python3
"""
Database initialization script for Don Estate application.
Creates all necessary tables and extensions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import engine
from src.models.base import Base
from src.models.property import Property
from src.models.user import User
from src.models.appointment import Appointment

def init_database():
    """Initialize the database by creating all tables."""
    print("Creating database tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("Database initialized successfully!")
    print("Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    init_database()
