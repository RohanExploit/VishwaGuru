import io
import os
import pytest
from PIL import Image
from fastapi import UploadFile
from backend.utils import process_uploaded_image_sync, save_file_blocking

# Helper to create an UploadFile
def create_upload_file(content=b"test", filename="test.jpg"):
    return UploadFile(filename=filename, file=io.BytesIO(content))

def test_process_uploaded_image_strips_exif():
    # Create an image with EXIF
    img = Image.new('RGB', (100, 100), color='red')
    exif = img.getexif()
    exif[0x010E] = "Test Image Description" # ImageDescription

    # Save to buffer with EXIF
    buf = io.BytesIO()
    img.save(buf, format='JPEG', exif=exif)
    buf.seek(0)

    # Verify EXIF is present in the buffer
    img_check = Image.open(buf)
    # Check if 0x010E is in the keys of the dict-like Exif object
    assert 0x010E in img_check.getexif()
    buf.seek(0)

    # Create UploadFile
    upload_file = create_upload_file(content=buf.getvalue())

    # Process
    processed_img, processed_bytes = process_uploaded_image_sync(upload_file)

    # Verify EXIF is stripped from processed_bytes
    img_from_bytes = Image.open(io.BytesIO(processed_bytes))
    assert not img_from_bytes.getexif()
    assert 'exif' not in img_from_bytes.info

    # Verify processed_img (PIL object) produces clean output if saved
    # We don't check processed_img.getexif() directly as it might still hold a reference
    # to the original file data or parsed tags, but what matters is if it saves cleanly.
    out_buf = io.BytesIO()
    processed_img.save(out_buf, format='JPEG')
    out_buf.seek(0)
    img_from_obj = Image.open(out_buf)
    assert not img_from_obj.getexif()
    assert 'exif' not in img_from_obj.info

def test_save_file_blocking_strips_exif(tmp_path):
    # Create an image with EXIF
    img = Image.new('RGB', (100, 100), color='blue')
    exif = img.getexif()
    exif[0x010E] = "Test Image Description"

    # Save to buffer with EXIF
    buf = io.BytesIO()
    img.save(buf, format='JPEG', exif=exif)
    buf.seek(0)

    # Output path
    out_path = tmp_path / "saved_image.jpg"

    # Call save_file_blocking with file object
    # It reads from file_obj
    save_file_blocking(buf, str(out_path))

    # Verify saved file has no EXIF
    saved_img = Image.open(out_path)
    assert not saved_img.getexif()
    assert 'exif' not in saved_img.info

def test_save_file_blocking_with_image_object_strips_exif(tmp_path):
    # Create an image with EXIF
    img = Image.new('RGB', (100, 100), color='green')
    exif = img.getexif()
    exif[0x010E] = "Test Image Description"

    # Let's simulate loading from file to get info['exif'] populated
    buf = io.BytesIO()
    img.save(buf, format='JPEG', exif=exif)
    buf.seek(0)
    loaded_img = Image.open(buf)

    # Output path
    out_path = tmp_path / "saved_image_obj.jpg"

    # Call save_file_blocking with image object
    save_file_blocking(None, str(out_path), image=loaded_img)

    # Verify saved file has no EXIF
    saved_img = Image.open(out_path)
    assert not saved_img.getexif()
    assert 'exif' not in saved_img.info
