import pytest
import sys
from unittest.mock import MagicMock
from backend import utils
from backend.utils import _validate_uploaded_file_sync
from fastapi import UploadFile
from io import BytesIO
from PIL import Image

def create_mock_upload_file(content=b"test", filename="test.jpg"):
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.file = BytesIO(content)
    return file

def test_validate_uploaded_file_sync_no_magic(monkeypatch):
    """
    Test validation when python-magic is missing.
    Should fallback to PIL validation.
    """
    # Simulate missing magic
    monkeypatch.setattr("backend.utils.HAS_MAGIC", False)

    # Create valid image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    file = create_mock_upload_file(content=img_byte_arr.getvalue(), filename="test.jpg")

    # Run validation
    result = _validate_uploaded_file_sync(file)

    assert result is not None
    assert isinstance(result, Image.Image)
    assert result.format == 'JPEG'

def test_validate_uploaded_file_sync_invalid_format_no_magic(monkeypatch):
    """
    Test validation of invalid file when python-magic is missing.
    PIL should reject it.
    """
    monkeypatch.setattr("backend.utils.HAS_MAGIC", False)

    # Text file masquerading as image
    file = create_mock_upload_file(content=b"Not an image", filename="test.jpg")

    try:
        _validate_uploaded_file_sync(file)
        assert False, "Should have raised exception"
    except Exception as e:
        # Should be HTTPException(400)
        assert "Invalid image file" in str(e) or "Invalid image format" in str(e)

def test_validate_uploaded_file_sync_with_magic(monkeypatch):
    """
    Test validation when python-magic is present.
    """
    # Mock magic module
    mock_magic = MagicMock()
    mock_magic.from_buffer.return_value = 'image/jpeg'

    # Inject mock magic into backend.utils
    monkeypatch.setattr("backend.utils.magic", mock_magic, raising=False)
    monkeypatch.setattr("backend.utils.HAS_MAGIC", True)

    # Create valid image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    file = create_mock_upload_file(content=img_byte_arr.getvalue(), filename="test.jpg")

    # Run validation
    result = _validate_uploaded_file_sync(file)

    assert result is not None
    assert isinstance(result, Image.Image)
