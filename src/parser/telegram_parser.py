from telethon import TelegramClient, events
from telethon.tl.types import Message
import asyncio
from src.config import settings
from src.database import get_db
from src.models.property import Property
from .data_extractor import PropertyDataExtractor
from .media_handler import MediaHandler

class TelegramChannelParser:
    def __init__(self):
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

    def _load_last_message_id(self):
        last_property = self.db_session.query(Property).order_by(Property.posted_at.desc()).first()
        return last_property.telegram_message_id if last_property else 0

    def _save_last_message_id(self, msg_id):
        # In a real-world scenario, you might want a more robust way to track this.
        # For now, we rely on the DB query.
        pass

    async def start(self):
        """Initialize client and start listening."""
        print("Starting parser...")
        await self.client.start(phone=self.phone)
        print(f"Connected to Telegram as {await self.client.get_me()}")

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

    async def parse_history(self, limit=100):
        """Parse the last N messages from the channel."""
        async for message in self.client.iter_messages(self.channel, limit=limit):
            if message.id > self.last_message_id:
                await self.process_message(message)

    async def process_message(self, message: Message):
        """Extract, process, and save property data from a message."""
        if not message.text:
            return

        print(f"Processing message {message.id}...")

        # 1. Extract data
        extracted_data = self.extractor.extract(message.text)

        # 2. Download media
        media_paths = await self.media_handler.download_media(message, self.client)

        # 3. Generate embedding
        embedding = self.extractor.generate_embedding(extracted_data)

        has_embedding = embedding is not None

        # 4. Save to database
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
            description=extracted_data.get('description'),
            raw_text=extracted_data.get('raw_text'),
            embedding=embedding,
            has_embedding=has_embedding,
            search_enabled=has_embedding,
            embedding_generation_failed=not has_embedding,
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
    parser = TelegramChannelParser()
    asyncio.run(parser.start())
