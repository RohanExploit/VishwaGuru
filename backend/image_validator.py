"""
Image validation utility to prevent crashes and resource exhaustion from
corrupted, unsupported, or extremely large images.
"""

import io
from typing import Tuple, Optional
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Configuration constants
SUPPORTED_FORMATS = {'JPEG', 'PNG', 'WEBP', 'BMP', 'GIF'}
MAX_IMAGE_WIDTH = 8000  # pixels
MAX_IMAGE_HEIGHT = 8000  # pixels
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MIN_IMAGE_WIDTH = 10  # pixels
MIN_IMAGE_HEIGHT = 10  # pixels


class ImageValidationError(Exception):
    """Custom exception for image validation failures."""
    pass


def validate_image_file(file_bytes: bytes) -> Tuple[Image.Image, str]:
    """
    Validate an image file for corruption, format support, and size constraints.
    
    Args:
        file_bytes: Raw bytes of the image file
        
    Returns:
        Tuple of (PIL Image object, format string)
        
    Raises:
        ImageValidationError: If validation fails with descriptive message
    """
    # Check file size
    file_size = len(file_bytes)
    if file_size == 0:
        raise ImageValidationError("Image file is empty")
    
    if file_size > MAX_FILE_SIZE:
        raise ImageValidationError(
            f"Image file size ({file_size / (1024*1024):.2f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE / (1024*1024):.0f}MB)"
        )
    
    # Try to open the image
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        raise ImageValidationError(f"Invalid or corrupted image file: {str(e)}")
    
    # Verify image integrity using PIL's verify method
    try:
        # Create a copy for verification since verify() can consume the file
        verify_image = Image.open(io.BytesIO(file_bytes))
        verify_image.verify()
    except Exception as e:
        logger.error(f"Image verification failed: {e}")
        raise ImageValidationError(f"Image file is corrupted or invalid: {str(e)}")
    
    # Re-open the image after verify (verify consumes the image data)
    image = Image.open(io.BytesIO(file_bytes))
    
    # Check format support
    if image.format not in SUPPORTED_FORMATS:
        raise ImageValidationError(
            f"Unsupported image format: {image.format}. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    # Check image dimensions
    width, height = image.size
    
    if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
        raise ImageValidationError(
            f"Image dimensions ({width}x{height}) are too small. Minimum size: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}"
        )
    
    if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
        raise ImageValidationError(
            f"Image dimensions ({width}x{height}) exceed maximum allowed size ({MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT})"
        )
    
    logger.info(f"Image validated successfully: format={image.format}, size={width}x{height}, file_size={file_size/1024:.2f}KB")
    
    return image, image.format


async def validate_uploaded_image(file_obj) -> Tuple[Image.Image, str]:
    """
    Validate an uploaded image file (FastAPI UploadFile).
    
    Args:
        file_obj: FastAPI UploadFile object
        
    Returns:
        Tuple of (PIL Image object, format string)
        
    Raises:
        ImageValidationError: If validation fails
    """
    try:
        # Read file contents
        file_bytes = await file_obj.read()
        # Reset file pointer for potential re-reading
        await file_obj.seek(0)
        
        return validate_image_file(file_bytes)
    except ImageValidationError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during image upload validation: {e}")
        raise ImageValidationError(f"Failed to process uploaded image: {str(e)}")
