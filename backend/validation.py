"""
Input validation and sanitization utilities for VishwaGuru backend.
Provides protection against XSS, SQL injection, and path traversal attacks.
"""

import re
import html
import os
import uuid
from typing import Optional
from fastapi import HTTPException
import bleach

# Allowed HTML tags for description fields (very restrictive)
ALLOWED_TAGS = ['p', 'br', 'strong', 'em']
ALLOWED_ATTRIBUTES = {}

# Regex patterns for validation
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')  # International format
PINCODE_PATTERN = re.compile(r'^\d{6}$')
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

# SQL injection detection patterns
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
    r"(--|#|/\*|\*/)",
    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    r"(\bOR\s+\d+\s*=\s*\d+)",
    r"('|(\\x27)|(\\x2D)|(\\x23))"
]

def sanitize_html(text: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    Removes dangerous tags and attributes.
    """
    if not text:
        return ""
    
    # First escape HTML entities
    escaped = html.escape(text)
    
    # Then use bleach for additional sanitization
    cleaned = bleach.clean(
        escaped, 
        tags=ALLOWED_TAGS, 
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return cleaned.strip()

def detect_sql_injection(text: str) -> bool:
    """
    Detect potential SQL injection attempts in text input.
    Returns True if suspicious patterns are found.
    """
    if not text:
        return False
    
    text_upper = text.upper()
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text_upper, re.IGNORECASE):
            return True
    
    return False

def validate_and_sanitize_text(
    text: str, 
    field_name: str,
    min_length: int = 1,
    max_length: int = 1000,
    allow_html: bool = False
) -> str:
    """
    Comprehensive text validation and sanitization.
    """
    if not text or not text.strip():
        if min_length > 0:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} cannot be empty"
            )
        return ""
    
    text = text.strip()
    
    # Length validation
    if len(text) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be at least {min_length} characters long"
        )
    
    if len(text) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must not exceed {max_length} characters"
        )
    
    # SQL injection detection
    if detect_sql_injection(text):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid characters detected in {field_name}"
        )
    
    # XSS protection
    if allow_html:
        return sanitize_html(text)
    else:
        return html.escape(text)

def validate_email(email: str) -> str:
    """
    Validate and sanitize email address.
    """
    if not email:
        return ""
    
    email = email.strip().lower()
    
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email format"
        )
    
    # Additional length check
    if len(email) > 254:  # RFC 5321 limit
        raise HTTPException(
            status_code=400,
            detail="Email address too long"
        )
    
    return email

def validate_phone(phone: str) -> str:
    """
    Validate phone number format.
    """
    if not phone:
        return ""
    
    # Remove spaces and common separators
    phone = re.sub(r'[\s\-\(\)]', '', phone.strip())
    
    if not PHONE_PATTERN.match(phone):
        raise HTTPException(
            status_code=400,
            detail="Invalid phone number format"
        )
    
    return phone

def validate_pincode(pincode: str) -> str:
    """
    Validate Indian pincode format.
    """
    if not pincode:
        raise HTTPException(
            status_code=400,
            detail="Pincode is required"
        )
    
    pincode = pincode.strip()
    
    if not PINCODE_PATTERN.match(pincode):
        raise HTTPException(
            status_code=400,
            detail="Invalid pincode format. Must be 6 digits"
        )
    
    return pincode

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    """
    if not filename:
        return f"upload_{uuid.uuid4().hex[:8]}"
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Prevent hidden files and relative paths
    if filename.startswith('.') or filename.startswith('_'):
        filename = f"file_{filename}"
    
    # Ensure reasonable length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = f"{name[:90]}{ext}"
    
    # Add UUID prefix to prevent conflicts
    name, ext = os.path.splitext(filename)
    return f"{uuid.uuid4().hex[:8]}_{name}{ext}"

def validate_coordinates(latitude: Optional[float], longitude: Optional[float]) -> tuple:
    """
    Validate GPS coordinates.
    """
    if latitude is None and longitude is None:
        return None, None
    
    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=400,
            detail="Both latitude and longitude must be provided"
        )
    
    if not (-90 <= latitude <= 90):
        raise HTTPException(
            status_code=400,
            detail="Latitude must be between -90 and 90"
        )
    
    if not (-180 <= longitude <= 180):
        raise HTTPException(
            status_code=400,
            detail="Longitude must be between -180 and 180"
        )
    
    return latitude, longitude

def validate_category(category: str, allowed_categories: list) -> str:
    """
    Validate category against allowed values.
    """
    if not category:
        raise HTTPException(
            status_code=400,
            detail="Category is required"
        )
    
    category = category.strip()
    
    if category not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Allowed values: {', '.join(allowed_categories)}"
        )
    
    return category