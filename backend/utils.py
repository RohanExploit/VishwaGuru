from __future__ import annotations
from fastapi import UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from PIL import Image
import os
import shutil
import logging
import io
import magic
from typing import Optional

from backend.cache import user_upload_cache
from backend.models import Issue
from backend.schemas import DetectionResponse
from backend.pothole_detection import validate_image_for_processing
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# File upload validation constants
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    'image/tiff'
}

# User upload limits
UPLOAD_LIMIT_PER_USER = 5
UPLOAD_LIMIT_PER_IP = 10

def check_upload_limits(identifier: str, limit: int) -> None:
    """
    Check if the user/IP has exceeded upload limits using thread-safe cache.
    """
    current_uploads = user_upload_cache.get(identifier) or []
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)

    # Filter out old timestamps (older than 1 hour)
    recent_uploads = [ts for ts in current_uploads if ts > one_hour_ago]

    if len(recent_uploads) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Upload limit exceeded. Maximum {limit} uploads per hour allowed."
        )

    # Add current timestamp and update cache atomically
    recent_uploads.append(now)
    user_upload_cache.set(recent_uploads, identifier)

def _validate_uploaded_file_sync(file: UploadFile) -> Optional[Image.Image]:
    """
    Synchronous validation logic to be run in a threadpool.
    Returns the PIL Image if it was opened/processed, or None.
    """
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size allowed is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Check MIME type from content using python-magic
    try:
        # Read first 1024 bytes for MIME detection
        file_content = file.file.read(1024)
        file.file.seek(0)  # Reset file pointer

        detected_mime = magic.from_buffer(file_content, mime=True)

        if detected_mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only image files are allowed. Detected: {detected_mime}"
            )

        # Additional content validation: Try to open with PIL to ensure it's a valid image
        try:
            img = Image.open(file.file)
            # Optimization: Skip img.verify() to avoid full file read.
            # Corrupt files will fail during resize or subsequent processing.

            # Resize large images for better performance
            if img.width > 1024 or img.height > 1024:
                # Calculate new size maintaining aspect ratio
                ratio = min(1024 / img.width, 1024 / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)

                # Use BILINEAR for faster resizing (LANCZOS is too slow for upload path)
                img = img.resize((new_width, new_height), Image.Resampling.BILINEAR)

                # Save resized image back to file
                output = io.BytesIO()
                img.save(output, format=img.format or 'JPEG', quality=85)
                output.seek(0)

                # Replace file content
                file.file = output
                file.size = output.tell()
                output.seek(0)

            # Return the image object (resized or original)
            # Ensure file pointer is at start for any subsequent reads from file.file
            file.file.seek(0)

            return img

        except Exception as pil_error:
            logger.error(f"PIL validation failed for {file.filename}: {pil_error}")
            raise HTTPException(
                status_code=400,
                detail="Invalid image file. The file appears to be corrupted or not a valid image."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating file {file.filename}: {e}")
        raise HTTPException(
            status_code=400,
            detail="Unable to validate file content. Please ensure it's a valid image file."
        )

async def validate_uploaded_file(file: UploadFile) -> Optional[Image.Image]:
    """
    Validate uploaded file for security and safety (async wrapper).
    Returns the PIL Image if it was opened/processed, or None.
    """
    return await run_in_threadpool(_validate_uploaded_file_sync, file)

def process_uploaded_image_sync(file: UploadFile) -> tuple[Image.Image, bytes]:
    """
    Synchronously validate, resize, and strip EXIF from uploaded image.
    Returns a tuple of (PIL Image, image bytes).
    """
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size allowed is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Check MIME type
    try:
        file_content = file.file.read(1024)
        file.file.seek(0)
        detected_mime = magic.from_buffer(file_content, mime=True)

        if detected_mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only image files are allowed. Detected: {detected_mime}"
            )

        try:
            img = Image.open(file.file)
            original_format = img.format

            # Resize if needed
            if img.width > 1024 or img.height > 1024:
                ratio = min(1024 / img.width, 1024 / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.BILINEAR)

            # Strip EXIF
            img_no_exif = Image.new(img.mode, img.size)
            img_no_exif.paste(img)

            # Save to BytesIO
            output = io.BytesIO()
            # Preserve format or default to JPEG (handling mode compatibility)
            # JPEG doesn't support RGBA, so use PNG for RGBA if format not specified
            if original_format:
                fmt = original_format
            else:
                fmt = 'PNG' if img.mode == 'RGBA' else 'JPEG'

            img_no_exif.save(output, format=fmt, quality=85)
            img_bytes = output.getvalue()

            return img_no_exif, img_bytes

        except Exception as pil_error:
            logger.error(f"PIL processing failed: {pil_error}")
            raise HTTPException(
                status_code=400,
                detail="Invalid image file."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=400, detail="Unable to process file.")

async def process_uploaded_image(file: UploadFile) -> tuple[Image.Image, bytes]:
    return await run_in_threadpool(process_uploaded_image_sync, file)

def save_processed_image(image_bytes: bytes, path: str):
    """
    Save processed image bytes to disk.
    Optimized: Direct write instead of stream copy.
    """
    with open(path, "wb") as f:
        f.write(image_bytes)

async def process_and_detect(image: UploadFile, detection_func) -> DetectionResponse:
    """
    Helper to process uploaded image and run detection.
    Uses the optimized image processing pipeline.
    """
    # Validate uploaded file
    pil_image = await validate_uploaded_file(image)

    # Validate image for processing (check integrity)
    try:
        if pil_image is None:
            pil_image = await run_in_threadpool(Image.open, image.file)

        # Validate image for processing
        await run_in_threadpool(validate_image_for_processing, pil_image)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from validation
    except Exception as e:
        logger.error(f"Invalid image file during processing: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection
    try:
        detections = await detection_func(pil_image)
        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Detection service temporarily unavailable")

def save_file_blocking(file_obj, path, image: Optional[Image.Image] = None):
    """
    Save uploaded file with security measures.
    """
    try:
        # Try to open as image with PIL
        if image:
             img = image
        else:
             img = Image.open(file_obj)

        # Strip EXIF data by creating a new image without metadata
        # Use paste() instead of getdata() for O(1) performance (vs O(N) list creation)
        img_no_exif = Image.new(img.mode, img.size)
        img_no_exif.paste(img)
        # Save without EXIF
        # Use original format if available, otherwise default to JPEG if mode is RGB, PNG if RGBA
        fmt = img.format or ('PNG' if img.mode == 'RGBA' else 'JPEG')
        img_no_exif.save(path, format=fmt)
        logger.info(f"Saved image {path} with EXIF metadata stripped")
    except Exception:
        # If not an image or PIL fails, save as binary
        file_obj.seek(0)  # Reset in case PIL read some
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
        logger.info(f"Saved file {path} as binary (not an image or PIL failed)")

def save_issue_db(db: Session, issue: Issue):
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue

# --- Password Hashing Utils ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
