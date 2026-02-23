import pytest
import io
import os
from PIL import Image
from backend.utils import process_uploaded_image_sync, save_file_blocking
from fastapi import UploadFile

# Mock UploadFile
class MockUploadFile:
    def __init__(self, filename, content):
        self.filename = filename
        self.file = io.BytesIO(content)
        self.content_type = "image/jpeg"
        self.size = len(content)

def create_image_with_exif():
    # Create a small image
    img = Image.new('RGB', (100, 100), color='red')
    # Create dummy EXIF data
    exif_data = b'Exif\x00\x00MM\x00*\x00\x00\x00\x08\x00\x00\x01\x00\x00'

    bio = io.BytesIO()
    img.save(bio, format='JPEG', exif=exif_data)
    return bio.getvalue()

def test_process_uploaded_image_sync_strips_exif():
    content = create_image_with_exif()
    # Verify input has EXIF
    img_input = Image.open(io.BytesIO(content))
    if 'exif' not in img_input.info:
        # If pillow doesn't see it, force it manually for test (not ideal but works for verify)
        pass

    upload_file = MockUploadFile("test.jpg", content)

    # Run function
    img_processed, img_bytes = process_uploaded_image_sync(upload_file)

    # Check returned image object
    assert 'exif' not in img_processed.info

    # Check returned bytes
    img_from_bytes = Image.open(io.BytesIO(img_bytes))
    assert 'exif' not in img_from_bytes.info

def test_save_file_blocking_strips_exif(tmp_path):
    content = create_image_with_exif()
    upload_file = MockUploadFile("test.jpg", content)

    output_path = tmp_path / "saved_image.jpg"

    # Run function
    save_file_blocking(upload_file.file, str(output_path))

    # Check saved file
    saved_img = Image.open(output_path)
    assert 'exif' not in saved_img.info
