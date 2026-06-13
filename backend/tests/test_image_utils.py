
import pytest
from unittest.mock import MagicMock
from backend.utils import process_uploaded_image_sync, save_file_blocking
from fastapi import UploadFile
from io import BytesIO
from PIL import Image, ExifTags
import os

def create_mock_upload_file(content, filename="test.jpg"):
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.file = BytesIO(content)
    # Mock read/seek/tell behavior
    file.file.seek(0)
    return file

def test_process_uploaded_image_sync_basic():
    # Create a simple image
    img = Image.new('RGB', (100, 100), color='red')
    buf = BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)

    file = create_mock_upload_file(buf.getvalue())

    processed_img, processed_bytes = process_uploaded_image_sync(file)

    assert isinstance(processed_img, Image.Image)
    assert isinstance(processed_bytes, bytes)
    assert processed_img.size == (100, 100)

    # Check if we can open the bytes
    img_from_bytes = Image.open(BytesIO(processed_bytes))
    assert img_from_bytes.size == (100, 100)

def test_process_uploaded_image_sync_resize():
    # Create a large image
    img = Image.new('RGB', (2000, 2000), color='blue')
    buf = BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)

    file = create_mock_upload_file(buf.getvalue())

    processed_img, processed_bytes = process_uploaded_image_sync(file)

    # Check resize logic (max 1024)
    assert processed_img.width <= 1024
    assert processed_img.height <= 1024
    assert processed_img.width == 1024 or processed_img.height == 1024

def test_save_file_blocking():
    # Create a simple image
    img = Image.new('RGB', (50, 50), color='green')
    buf = BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)

    test_path = "test_save.jpg"
    try:
        # Test with file object
        buf.seek(0)
        save_file_blocking(buf, test_path)
        assert os.path.exists(test_path)

        # Verify saved image
        saved_img = Image.open(test_path)
        assert saved_img.size == (50, 50)
        saved_img.close()

        # Test with image object
        os.remove(test_path)
        save_file_blocking(None, test_path, image=img)
        assert os.path.exists(test_path)

        saved_img = Image.open(test_path)
        assert saved_img.size == (50, 50)
        saved_img.close()

    finally:
        if os.path.exists(test_path):
            os.remove(test_path)
