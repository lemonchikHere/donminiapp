"""
This module contains the main logic for parsing a Telegram channel.

It uses the Telethon library to connect to Telegram, listen for new messages
in a specified channel, process them to extract real estate data, and save
the structured information to the database.
"""

from telethon import TelegramClient, events
from telethon.tl.types import Message
import asyncio
from src.config import settings
from src.database import get_db
from src.models.property import Property
from .data_extractor import PropertyDataExtractor
from .media_handler import MediaHandler
from src.services.geocoding_service import geocoding_service

class TelegramChannelParser:
    """
    Parses a Telegram channel for real estate listings.

    This class connects to a Telegram channel, listens for new messages,
    and processes historical messages. For each relevant message, it extracts
    property data, downloads media, geocodes the address, and saves the
    information as a `Property` record in the database.
    """
    def __init__(self):
        """Initializes the TelegramChannelParser."""
        self.client = TelegramClient(
            'don_estate_session',
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )
        self.phone = settings.TELEGRAM_PHONE
        self.channel_username = settings.TELEGRAM_CHANNEL
        self.extractor = PropertyDataExtractor()
        self.media_handler = MediaHandler()
        self.db_session = next(get_db())
        self.last_message_id = self._load_last_message_id()

    def _load_last_message_id(self) -> int:
        """
        Loads the ID of the most recently processed message from the database.

        This is used to prevent reprocessing the entire channel history on
        every startup.

        Returns:
            The Telegram ID of the last processed message, or 0 if none exist.
        """
        last_property = self.db_session.query(Property).order_by(Property.posted_at.desc()).first()
        return last_property.telegram_message_id if last_property else 0

    def _save_last_message_id(self, msg_id: int):
        """
        Saves the ID of the last processed message.

        Note: This is currently a placeholder. State is determined by querying
              the database in `_load_last_message_id`.

        Args:
            msg_id: The Telegram ID of the message that was just processed.
        """
        pass

    async def start(self):
        """
        Starts the parser.

        This method connects the Telegram client, sets up an event handler for
        new messages, parses the channel history if it's the first run, and
        then runs indefinitely to listen for new messages.
        """
        print("Starting parser...")
        await self.client.start(phone=self.phone)
        me = await self.client.get_me()
        print(f"Connected to Telegram as {me.first_name}")

        self.channel = await self.client.get_entity(self.channel_username)

        @self.client.on(events.NewMessage(chats=self.channel))
        async def handler(event):
            print(f"New message received: {event.message.id}")
            await self.process_message(event.message)

        if self.last_message_id == 0:
            print("Parsing channel history for the first time...")
            await self.parse_history()

        print("Parser is running and listening for new messages...")
        await self.client.run_until_disconnected()

    async def parse_history(self, limit: int = 100):
        """
        Parses the most recent messages from the channel's history.

        Args:
            limit: The maximum number of recent messages to fetch and process.
        """
        async for message in self.client.iter_messages(self.channel, limit=limit):
            if message.id > self.last_message_id:
                await self.process_message(message)

    async def process_message(self, message: Message):
        """
        Processes a single Telegram message to extract and save property data.

        This involves:
        1. Extracting structured data from the message text.
        2. Downloading any associated photos or videos.
        3. Geocoding the property's address.
        4. Generating a vector embedding for semantic search.
        5. Saving the complete `Property` object to the database.

        Args:
            message: The Telethon `Message` object to process.
        """
        if not message.text:
            return

        print(f"Processing message {message.id}...")

        # 1. Extract data
        extracted_data = self.extractor.extract(message.text)

        # 2. Download media
        media_paths = await self.media_handler.download_media(message, self.client)

        # 3. Geocode address
        latitude, longitude = None, None
        if extracted_data.get('address'):
            coords = await geocoding_service.get_coordinates(extracted_data['address'])
            if coords:
                latitude, longitude = coords

        # 4. Generate embedding
        embedding = self.extractor.generate_embedding(extracted_data)

        # 5. Save to database
        new_property = Property(
            telegram_message_id=message.id,
            telegram_channel_id=self.channel.id,
            posted_at=message.date,
            transaction_type=extracted_data.get('transaction_type'),
            property_type=extracted_data.get('property_type'),
            rooms=extracted_data.get('rooms'),
            area_sqm=extracted_data.get('area_sqm'),
            floor=extracted_data.get('floor'),
            price_usd=extracted_data.get('price_usd'),
            address=extracted_data.get('address'),
            latitude=latitude,
            longitude=longitude,
            description=extracted_data.get('description'),
            raw_text=extracted_data.get('raw_text'),
            embedding=embedding,
            photos=media_paths,
            video_url=media_paths[0] if media_paths and media_paths[0].endswith(('.mp4', '.mov')) else None,
            views_count=message.views or 0,
        )

        try:
            self.db_session.add(new_property)
            self.db_session.commit()
            print(f"Successfully saved property from message {message.id}")
            self.last_message_id = message.id
            self._save_last_message_id(message.id)
        except Exception as e:
            self.db_session.rollback()
            print(f"Error saving property from message {message.id}: {e}")

if __name__ == '__main__':
    # This block allows the script to be run directly to start the parser.
    parser = TelegramChannelParser()
    asyncio.run(parser.start())
