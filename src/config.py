"""
Manages application configuration settings.

This module loads environment variables from a .env file and makes them
available through a centralized `Settings` class. This approach allows for
easy management of configuration parameters for different environments
(development, testing, production).
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Encapsulates all application configuration settings.

    Attributes are loaded from environment variables. Provides a single source
    of truth for configuration values throughout the application.
    """

    # Telegram API configuration for the parser client.
    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
    """The Telegram API ID for the client session."""
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
    """The Telegram API hash for the client session."""
    TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
    """The phone number associated with the Telegram account."""
    TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
    """The target Telegram channel to parse messages from."""

    # Database connection settings.
    DB_HOST = os.getenv("DB_HOST", "postgres")
    """The hostname of the database server."""
    DB_PORT = os.getenv("DB_PORT", 5432)
    """The port number of the database server."""
    DB_NAME = os.getenv("DB_NAME", "don_estate")
    """The name of the database."""
    DB_USER = os.getenv("DB_USER", "postgres")
    """The username for connecting to the database."""
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    """The password for the database user."""

    @property
    def database_url(self):
        """
        Constructs the full database connection URL.

        Returns:
            The database connection string in SQLAlchemy format.
        """
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # OpenAI API settings for embedding generation.
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    """The API key for accessing OpenAI services."""

    # Telegram Bot settings.
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    """The authentication token for the Telegram Bot."""
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    """The Telegram chat ID of the administrator for notifications."""

    # API security settings.
    API_SECRET_KEY = os.getenv("API_SECRET_KEY")
    """A secret key for API-related operations (e.g., JWT signing)."""

    # Yandex Maps API settings for geocoding.
    YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
    """The API key for the Yandex Maps Geocoding service."""

settings = Settings()
"""A global instance of the Settings class to be used throughout the application."""
