import pytest
from backend import utils
from io import BytesIO
from PIL import Image
import io

class MockUploadFile:
    def __init__(self, content, filename="test.jpg"):
        self.filename = filename
        self.file = BytesIO(content)
        self.size = len(content)

def test_process_uploaded_image_sync_strips_exif(monkeypatch):
    """
    Test that process_uploaded_image_sync correctly strips metadata.
    """
    # Mock magic to avoid dependency issues in test environment if missing
    monkeypatch.setattr("backend.utils.HAS_MAGIC", False)

    # Create an image with metadata
    img = Image.new('RGB', (100, 100), color='red')
    img.info['test_key'] = 'test_value'
    img.info['exif'] = b'fake_exif_data'

    # Save to buffer
    buf = io.BytesIO()
    # Use PNG as it supports metadata chunks
    img.save(buf, format='PNG')
    buf.seek(0)

    # Create mock file
    file = MockUploadFile(content=buf.getvalue(), filename="test.png")

    # Process
    processed_img, processed_bytes = utils.process_uploaded_image_sync(file)

    # Verify processed image object has cleared info
    # Note: process_uploaded_image_sync returns 'img_no_exif' which is the alias to 'img'
    # And we called img.info.clear() on it.
    assert not processed_img.info, f"Image info should be empty, got {processed_img.info}"

    # Verify bytes also result in clean image
    final_img = Image.open(io.BytesIO(processed_bytes))
    # 'exif' key should definitely be gone
    assert 'exif' not in final_img.info
    # 'test_key' should be gone
    assert 'test_key' not in final_img.info

def test_save_file_blocking_strips_exif(tmp_path):
    """
    Test that save_file_blocking correctly strips metadata.
    """
    # Create an image with metadata
    img = Image.new('RGB', (100, 100), color='blue')
    img.info['secret'] = 'data'

    file_path = tmp_path / "test_safe.png"

    # Mock file obj
    file_obj = BytesIO(b"dummy")

    # Call save_file_blocking with the image object
    utils.save_file_blocking(file_obj, str(file_path), image=img)

    # Check saved file
    saved_img = Image.open(file_path)
    assert 'secret' not in saved_img.info, "Metadata should be stripped in saved file"
