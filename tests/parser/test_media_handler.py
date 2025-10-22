"""
Unit tests for the MediaHandler class.

This module tests the `MediaHandler`'s ability to download and process
media files from mocked Telegram messages. It covers single media,
grouped media, and image compression logic.
"""

import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch
from src.parser.media_handler import MediaHandler

@pytest.fixture
def media_handler():
    """
    A pytest fixture that provides a `MediaHandler` instance configured to use
    a temporary `test_media` directory.
    """
    return MediaHandler(media_dir="test_media")

@pytest.fixture(autouse=True)
def cleanup_media_dir():
    """
    An auto-used pytest fixture that ensures the `test_media` directory is
    created fresh for each test and completely removed after each test runs.
    This prevents test side-effects.
    """
    media_dir = "test_media"
    if os.path.exists(media_dir):
        for f in os.listdir(media_dir):
            os.remove(os.path.join(media_dir, f))
    yield
    if os.path.exists(media_dir):
        for f in os.listdir(media_dir):
            os.remove(os.path.join(media_dir, f))
        os.rmdir(media_dir)

@pytest.mark.asyncio
async def test_download_single_photo(media_handler):
    """
    Tests the `download_media` method for a message containing a single photo.
    Verifies that the message's `download_media` method is called and that
    the result is passed to the image processor.
    """
    # Arrange
    mock_message = AsyncMock()
    mock_message.photo = True
    mock_message.video = False
    mock_message.grouped_id = None
    mock_message.download_media.return_value = "test_media/photo.jpg"

    mock_client = MagicMock()

    # Create a dummy file to simulate the downloaded media
    os.makedirs("test_media", exist_ok=True)
    with open("test_media/photo.jpg", "w") as f:
        f.write("dummy image data")

    # Act & Assert
    with patch.object(media_handler, '_process_image', return_value="test_media/processed_photo.jpg") as mock_process:
        paths = await media_handler.download_media(mock_message, mock_client)

        mock_message.download_media.assert_called_once_with(file="test_media")
        mock_process.assert_called_once_with("test_media/photo.jpg")
        assert paths == ["test_media/processed_photo.jpg"]

@pytest.mark.asyncio
async def test_download_media_group(media_handler):
    """
    Tests the `download_media` method for a message that is part of a group
    (an album). It verifies that the client's `get_messages` method is called
    to fetch all items in the group.
    """
    # Arrange
    mock_msg1 = AsyncMock()
    mock_msg1.photo = True
    mock_msg1.video = False
    mock_msg1.download_media.return_value = "test_media/photo1.jpg"

    mock_client = AsyncMock()
    mock_client.get_messages.return_value = [mock_msg1]

    os.makedirs("test_media", exist_ok=True)
    with open("test_media/photo1.jpg", "w") as f:
        f.write("dummy data")

    trigger_message = AsyncMock()
    trigger_message.grouped_id = 12345
    trigger_message.chat_id = -100
    trigger_message.id = 1
    trigger_message.photo = None  # Ensure it doesn't get processed twice
    trigger_message.video = None

    # Act & Assert
    with patch.object(media_handler, '_process_image', side_effect=lambda x: x) as mock_process:
        paths = await media_handler.download_media(trigger_message, mock_client)

        mock_client.get_messages.assert_called_once_with(-100, ids=[1])
        assert "test_media/photo1.jpg" in paths

def test_process_image_no_compression(media_handler):
    """
    Tests that the `_process_image` method does not attempt to compress an
    image that is smaller than the specified maximum size.
    """
    # Arrange
    os.makedirs("test_media", exist_ok=True)
    file_path = "test_media/small.jpg"
    with open(file_path, "wb") as f:
        f.write(b'\0' * (1 * 1024 * 1024)) # 1 MB file

    # Act & Assert
    with patch('PIL.Image.open') as mock_image_open:
        result_path = media_handler._process_image(file_path, max_size_mb=2)
        mock_image_open.assert_not_called()
        assert result_path == file_path

def test_process_image_with_compression(media_handler):
    """
    Tests that the `_process_image` method correctly identifies a large image
    and calls the PIL library to compress it.
    """
    # Arrange
    os.makedirs("test_media", exist_ok=True)
    file_path = "test_media/large.jpg"
    with open(file_path, "wb") as f:
        f.write(b'\0' * (3 * 1024 * 1024)) # 3 MB file

    mock_img = MagicMock()
    # Act & Assert
    with patch('PIL.Image.open', return_value=mock_img) as mock_image_open:
        result_path = media_handler._process_image(file_path, max_size_mb=2)

        mock_image_open.assert_called_once_with(file_path)
        mock_img.save.assert_called_once_with(file_path, "JPEG", optimize=True, quality=85)
        assert result_path == file_path
