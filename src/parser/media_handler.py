"""
Handles downloading and processing of media from Telegram messages.

This module provides the `MediaHandler` class, which is responsible for
downloading photos and videos associated with a Telegram message, and
performing basic processing like image compression.
"""

import os
from telethon.tl.types import Message
from telethon import TelegramClient
from PIL import Image
from typing import List

class MediaHandler:
    """
    Manages the downloading and processing of media files from Telegram.
    """
    def __init__(self, media_dir: str = "media"):
        """
        Initializes the MediaHandler.

        Args:
            media_dir: The directory where media files will be saved.
                       It will be created if it doesn't exist.
        """
        self.media_dir = media_dir
        if not os.path.exists(self.media_dir):
            os.makedirs(self.media_dir)

    async def download_media(self, message: Message, client: TelegramClient) -> List[str]:
        """
        Downloads all photos and videos from a given Telegram message.

        This method handles both single media messages and grouped media (albums).

        Args:
            message: The Telethon `Message` object.
            client: The active Telethon `TelegramClient` instance.

        Returns:
            A list of local file paths for the downloaded media.
        """
        media_paths = []

        # Handle single photo or video
        if message.photo or message.video:
            file_path = await message.download_media(file=self.media_dir)
            processed_path = self._process_image(file_path) if message.photo else file_path
            media_paths.append(processed_path)

        # Handle media group (album)
        if message.grouped_id:
            # This is a simplified approach. A robust solution would handle potential duplicates
            # and ensure all items in the group are fetched.
            # In Telethon, getting a message by ID that is part of a group
            # often returns all messages in that group.
            group_messages = await client.get_messages(message.chat_id, ids=[message.id])
            for msg in group_messages:
                 if msg and (msg.photo or msg.video):
                    file_path = await msg.download_media(file=self.media_dir)
                    processed_path = self._process_image(file_path) if msg.photo else file_path
                    if processed_path not in media_paths:
                        media_paths.append(processed_path)

        return media_paths

    def _process_image(self, file_path: str, max_size_mb: int = 2) -> str:
        """
        Compresses an image if it exceeds a specified file size.

        Args:
            file_path: The local path to the image file.
            max_size_mb: The maximum allowed file size in megabytes.

        Returns:
            The file path of the processed (or original) image.
        """
        if not file_path or not os.path.exists(file_path):
            return file_path

        if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
            try:
                img = Image.open(file_path)
                img.save(file_path, "JPEG", optimize=True, quality=85)
            except Exception as e:
                print(f"Could not compress image {file_path}: {e}")

        return file_path
