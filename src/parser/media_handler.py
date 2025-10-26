import os
from telethon.tl.types import Message
from PIL import Image


class MediaHandler:
    def __init__(self, media_dir="media"):
        self.media_dir = media_dir
        if not os.path.exists(self.media_dir):
            os.makedirs(self.media_dir)

    async def download_media(self, message: Message, client):
        """Downloads all photos and videos from a message."""
        media_paths = []

        # Handle single photo or video
        if message.photo or message.video:
            file_path = await message.download_media(file=self.media_dir)
            processed_path = (
                self._process_image(file_path) if message.photo else file_path
            )
            media_paths.append(processed_path)

        # Handle media group (album)
        if message.grouped_id:
            # This is a simplified approach. A robust solution would handle potential duplicates
            # and ensure all items in the group are fetched.
            group_messages = await client.get_messages(
                message.chat_id, ids=[message.id]
            )
            for msg in group_messages:
                if msg and (msg.photo or msg.video):
                    file_path = await msg.download_media(file=self.media_dir)
                    processed_path = (
                        self._process_image(file_path) if msg.photo else file_path
                    )
                    if processed_path not in media_paths:
                        media_paths.append(processed_path)

        return media_paths

    def _process_image(self, file_path: str, max_size_mb: int = 2) -> str:
        """Compresses an image if it's too large."""
        if not file_path or not os.path.exists(file_path):
            return file_path

        if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
            try:
                img = Image.open(file_path)
                img.save(file_path, "JPEG", optimize=True, quality=85)
            except Exception as e:
                print(f"Could not compress image {file_path}: {e}")

        return file_path
