import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram API
    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
    TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")

    # Database
    DB_HOST = os.getenv("DB_HOST", "postgres")
    DB_PORT = os.getenv("DB_PORT", 5432)
    DB_NAME = os.getenv("DB_NAME", "don_estate")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    @property
    def database_url(self):
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

    # API
    API_SECRET_KEY = os.getenv("API_SECRET_KEY")

settings = Settings()
