from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from pydantic import BaseModel
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import List
from datetime import datetime, timedelta
from PIL import Image

import json
import os
import shutil
import uuid
import asyncio
import logging
import time
from pywebpush import webpush, WebPushException
import magic
import httpx

from backend.cache import recent_issues_cache, user_upload_cache
from backend.database import engine, Base, SessionLocal, get_db
from backend.models import Issue
from backend.schemas import (
    IssueResponse, IssueCreateRequest, IssueCreateResponse, ChatRequest, ChatResponse,
    VoteRequest, VoteResponse, DetectionResponse, UrgencyAnalysisRequest,
    UrgencyAnalysisResponse, HealthResponse, MLStatusResponse, ResponsibilityMapResponse,
    ErrorResponse, SuccessResponse, IssueCategory, IssueStatus
)
from backend.exceptions import EXCEPTION_HANDLERS
from backend.bot import run_bot, start_bot_thread, stop_bot_thread
from backend.ai_factory import create_all_ai_services
from backend.ai_service import generate_action_plan, chat_with_civic_assistant
from backend.maharashtra_locator import (
    load_maharashtra_pincode_data,
    load_maharashtra_mla_data,
    find_constituency_by_pincode,
    find_mla_by_constituency
)
from backend.init_db import migrate_db
from backend.pothole_detection import detect_potholes, validate_image_for_processing
from backend.garbage_detection import detect_garbage
from backend.local_ml_service import (
    detect_infrastructure_local,
    detect_flooding_local,
    detect_vandalism_local,
    get_detection_status
)
from backend.gemini_services import get_ai_services, initialize_ai_services
from backend.hf_api_service import (
    detect_illegal_parking_clip,
    detect_street_light_clip,
    detect_fire_clip,
    detect_stray_animal_clip,
    detect_blocked_road_clip,
    detect_tree_hazard_clip,
    detect_pest_clip,
    detect_severity_clip,
    detect_smart_scan_clip,
    generate_image_caption,
    analyze_urgency_text
)
from backend.validation import (
    validate_and_sanitize_text,
    validate_email,
    validate_coordinates,
    validate_category,
    sanitize_filename
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File upload validation constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    'image/tiff'
}

# User upload limits
UPLOAD_LIMIT_PER_USER = 5  # max uploads per user per hour
UPLOAD_LIMIT_PER_IP = 10  # max uploads per IP per hour

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

def _validate_uploaded_file_sync(file: UploadFile) -> None:
    """
    Synchronous validation logic to be run in a threadpool.
    
    Security measures:
    - File size limits
    - MIME type validation using content detection
    - Image content validation using PIL
    - TODO: Add virus/malware scanning (consider integrating ClamAV or similar)
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
            img.verify()  # Verify the image is not corrupted
            file.file.seek(0)  # Reset after PIL operations
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

async def validate_uploaded_file(file: UploadFile) -> None:
    """
    Validate uploaded file for security and safety (async wrapper).

    Args:
        file: The uploaded file to validate

    Raises:
        HTTPException: If validation fails
    """
    await run_in_threadpool(_validate_uploaded_file_sync, file)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

async def process_action_plan_background(issue_id: int, description: str, category: str, language: str, image_path: str):
    db = SessionLocal()
    try:
        # Generate Action Plan (AI)
        action_plan = await generate_action_plan(description, category, language, image_path)

        # Update issue in DB
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if issue:
            issue.action_plan = action_plan
            db.commit()

            # Invalidate cache to ensure users get the updated action plan
            recent_issues_cache.invalidate("recent_issues")
    except Exception as e:
        logger.error(f"Background action plan generation failed for issue {issue_id}: {e}", exc_info=True)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Migrate DB
    migrate_db()

    # Startup: Initialize Shared HTTP Client for external APIs (Connection Pooling)
    app.state.http_client = httpx.AsyncClient()
    logger.info("Shared HTTP Client initialized.")

    # Startup: Initialize AI services
    try:
        action_plan_service, chat_service, mla_summary_service = create_all_ai_services()

        initialize_ai_services(
            action_plan_service=action_plan_service,
            chat_service=chat_service,
            mla_summary_service=mla_summary_service
        )
        logger.info("AI services initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing AI services: {e}", exc_info=True)
        raise

    # Startup: Load static data to avoid first-request latency
    try:
        # These functions use lru_cache, so calling them once loads the data into memory
        load_maharashtra_pincode_data()
        load_maharashtra_mla_data()
        logger.info("Maharashtra data pre-loaded successfully.")
    except Exception as e:
        logger.error(f"Error pre-loading Maharashtra data: {e}")

    # Startup: Start Telegram Bot in separate thread (non-blocking for FastAPI)
    try:
        start_bot_thread()
        logger.info("Telegram bot started in separate thread.")
    except Exception as e:
        logger.error(f"Error starting bot thread: {e}")
    
    yield
    
    # Shutdown: Close Shared HTTP Client
    await app.state.http_client.aclose()
    logger.info("Shared HTTP Client closed.")

    # Shutdown: Stop Telegram Bot thread
    try:
        stop_bot_thread()
        logger.info("Telegram bot thread stopped.")
    except Exception as e:
        logger.error(f"Error stopping bot thread: {e}")

app = FastAPI(
    title="VishwaGuru Backend",
    description="AI-powered civic issue reporting and resolution platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add centralized exception handlers
for exception_type, handler in EXCEPTION_HANDLERS.items():
    app.add_exception_handler(exception_type, handler)

# CORS Configuration - Security Enhanced
# For separate frontend/backend deployment (e.g., Netlify + Render)
# FRONTEND_URL environment variable is REQUIRED for security
# Example: https://your-app.netlify.app

frontend_url = os.environ.get("FRONTEND_URL")
if not frontend_url:
    raise ValueError(
        "FRONTEND_URL environment variable is required for security. "
        "Set it to your frontend URL (e.g., https://your-app.netlify.app). "
        "For development, use http://localhost:5173 or similar."
    )

# Validate URL format (basic check)
if not (frontend_url.startswith("http://") or frontend_url.startswith("https://")):
    raise ValueError(
        f"FRONTEND_URL must be a valid HTTP/HTTPS URL. Got: {frontend_url}"
    )

# Build allowed origins list
allowed_origins = [frontend_url]

# Allow localhost origins for development
if os.environ.get("ENVIRONMENT", "").lower() != "production":
    # Add common development origins
    dev_origins = [
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",  # Alternative dev port
    ]
    allowed_origins.extend(dev_origins)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Enable Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=500)

@app.get("/", response_model=SuccessResponse)
def root():
    return SuccessResponse(
        message="VishwaGuru API is running",
        data={
            "service": "VishwaGuru API",
            "version": "1.0.0"
        }
    )

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={
            "database": "connected",
            "ai_services": "initialized"
        }
    )

@app.get("/api/ml-status", response_model=MLStatusResponse)
async def ml_status():
    """
    Get the status of the ML detection service.
    Returns information about which backend is being used (local or HF API).
    """
    status = await get_detection_status()
    return MLStatusResponse(
        status="ok",
        models_loaded=status.get("models_loaded", []),
        memory_usage=status.get("memory_usage")
    )

def save_file_blocking(file_obj, path):
    """
    Save uploaded file with security measures:
    - Strip EXIF metadata from images to protect privacy
    - For non-images, save as-is
    """
    try:
        # Try to open as image with PIL
        img = Image.open(file_obj)
        # Strip EXIF data by creating a new image without metadata
        img_no_exif = Image.new(img.mode, img.size)
        img_no_exif.putdata(list(img.getdata()))
        # Save without EXIF
        img_no_exif.save(path, format=img.format)
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

@app.post("/api/issues", response_model=IssueCreateResponse, status_code=201)
async def create_issue(
    request: Request,
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    category: str = Form(...),
    user_email: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    location: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Input validation and sanitization
    try:
        # Validate and sanitize description
        description = validate_and_sanitize_text(
            description, 
            "Description", 
            min_length=10, 
            max_length=1000,
            allow_html=False
        )
        
        # Validate category
        allowed_categories = [cat.value for cat in IssueCategory]
        category = validate_category(category, allowed_categories)
        
        # Validate email if provided
        if user_email:
            user_email = validate_email(user_email)
        
        # Validate coordinates
        latitude, longitude = validate_coordinates(latitude, longitude)
        
        # Validate and sanitize location
        if location:
            location = validate_and_sanitize_text(
                location,
                "Location",
                min_length=0,
                max_length=200,
                allow_html=False
            )
        
    except HTTPException:
        raise  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid input data")
    image_path = None
    
    # Check upload limits if image is being uploaded
    if image:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        # Use user_email if provided, otherwise IP
        identifier = user_email if user_email else client_ip
        limit = UPLOAD_LIMIT_PER_USER if user_email else UPLOAD_LIMIT_PER_IP
        check_upload_limits(identifier, limit)
    
    try:
        # Validate uploaded image if provided
        if image:
            await validate_uploaded_file(image)
        
        # Save image if provided with secure filename
        if image:
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            # Use secure filename to prevent path traversal
            secure_filename = sanitize_filename(image.filename)
            image_path = os.path.join(upload_dir, secure_filename)
            await run_in_threadpool(save_file_blocking, image.file, image_path)
    except HTTPException:
        # Re-raise HTTP exceptions (from validation)
        raise
    except OSError as e:
        logger.error(f"File I/O error while saving image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    except Exception as e:
        logger.error(f"Unexpected error during file processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    try:
        # Save to DB
        new_issue = Issue(
            reference_id=str(uuid.uuid4()),
            description=description,
            category=category,
            image_path=image_path,
            source="web",
            user_email=user_email,
            latitude=latitude,
            longitude=longitude,
            location=location,
            action_plan=None
        )

        # Offload blocking DB operations to threadpool
        await run_in_threadpool(save_issue_db, db, new_issue)
    except Exception as e:
        # Clean up uploaded file if DB save failed
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass  # Ignore cleanup errors
        
        logger.error(f"Database error while creating issue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save issue to database")

    # Add background task for AI generation
    background_tasks.add_task(process_action_plan_background, new_issue.id, description, category, language, image_path)

    # Optimistic Cache Update with thread-safe operations
    try:
        current_cache = recent_issues_cache.get("recent_issues")
        if current_cache:
            # Create a dict representation of the new issue
            new_issue_dict = IssueResponse(
                id=new_issue.id,
                category=new_issue.category,
                description=new_issue.description[:100] + "..." if len(new_issue.description) > 100 else new_issue.description,
                created_at=new_issue.created_at,
                image_path=new_issue.image_path,
                status=new_issue.status,
                upvotes=new_issue.upvotes if new_issue.upvotes is not None else 0,
                location=new_issue.location,
                latitude=new_issue.latitude,
                longitude=new_issue.longitude,
                action_plan=new_issue.action_plan
            ).model_dump(mode='json')

            # Prepend new issue to the list (atomic operation)
            current_cache.insert(0, new_issue_dict)

            # Keep only last 10 entries
            if len(current_cache) > 10:
                current_cache.pop()

            # Atomic cache update
            recent_issues_cache.set(current_cache, "recent_issues")
    except Exception as e:
        logger.error(f"Error updating cache optimistically: {e}")
        # Failure to update cache is not critical, don't fail the request

    return IssueCreateResponse(
        id=new_issue.id,
        message="Issue reported successfully. Action plan will be generated shortly.",
        action_plan=None
    )

@app.post("/api/issues/{issue_id}/vote", response_model=VoteResponse)
def upvote_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Increment upvotes
    if issue.upvotes is None:
        issue.upvotes = 0
    issue.upvotes += 1

    db.commit()
    db.refresh(issue)

    return VoteResponse(
        id=issue.id,
        upvotes=issue.upvotes,
        message="Issue upvoted successfully"
    )

@app.put("/api/issues/status", response_model=IssueStatusUpdateResponse)
def update_issue_status(
    request: IssueStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update issue status via secure reference ID (for government portals)"""
    issue = db.query(Issue).filter(Issue.reference_id == request.reference_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Validate status transition (simple state machine)
    valid_transitions = {
        "open": ["verified"],
        "verified": ["assigned", "open"],
        "assigned": ["in_progress", "verified"],
        "in_progress": ["resolved", "assigned"],
        "resolved": []  # Terminal state
    }

    if request.status.value not in valid_transitions.get(issue.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {issue.status} to {request.status.value}"
        )

    # Update issue
    old_status = issue.status
    issue.status = request.status.value
    if request.assigned_to:
        issue.assigned_to = request.assigned_to

    # Set timestamps
    now = datetime.datetime.now(datetime.timezone.utc)
    if request.status.value == "verified":
        issue.verified_at = now
    elif request.status.value == "assigned":
        issue.assigned_at = now
    elif request.status.value == "resolved":
        issue.resolved_at = now

    db.commit()
    db.refresh(issue)

    # Send notification to citizen
    background_tasks.add_task(send_status_notification, issue.id, old_status, request.status.value, request.notes)

    return IssueStatusUpdateResponse(
        id=issue.id,
        reference_id=issue.reference_id,
        status=request.status,
        message=f"Issue status updated to {request.status.value}"
    )

@app.post("/api/push-subscription", response_model=PushSubscriptionResponse)
def subscribe_push_notifications(
    request: PushSubscriptionRequest,
    db: Session = Depends(get_db)
):
    """Subscribe to push notifications for issue updates"""
    # Check if subscription already exists
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == request.endpoint
    ).first()

    if existing:
        # Update existing subscription
        existing.user_email = request.user_email
        existing.p256dh = request.p256dh
        existing.auth = request.auth
        existing.issue_id = request.issue_id
        db.commit()
        return PushSubscriptionResponse(
            id=existing.id,
            message="Push subscription updated"
        )

    # Create new subscription
    subscription = PushSubscription(
        user_email=request.user_email,
        endpoint=request.endpoint,
        p256dh=request.p256dh,
        auth=request.auth,
        issue_id=request.issue_id
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return PushSubscriptionResponse(
        id=subscription.id,
        message="Push subscription created"
    )

@lru_cache(maxsize=1)
def _load_responsibility_map():
    # Assuming the data folder is at the root level relative to where backend is run
    # Adjust path as necessary. If running from root, it is "data/responsibility_map.json"
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "responsibility_map.json")

    with open(file_path, "r") as f:
        return json.load(f)

@app.get("/api/responsibility-map", response_model=ResponsibilityMapResponse)
def get_responsibility_map():
    """Get responsibility mapping data for civic authorities"""
    try:
        data = _load_responsibility_map()
        return ResponsibilityMapResponse(data=data)
    except FileNotFoundError:
        logger.error("Responsibility map file not found", exc_info=True)
        raise HTTPException(status_code=404, detail="Responsibility map data not found")
    except Exception as e:
        logger.error(f"Error loading responsibility map: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load responsibility map")

@app.post("/api/analyze-urgency", response_model=UrgencyAnalysisResponse)
async def analyze_urgency_endpoint(request: Request, urgency_req: UrgencyAnalysisRequest):
    try:
        client = request.app.state.http_client
        result = await analyze_urgency_text(urgency_req.description, client=client)
        return UrgencyAnalysisResponse(
            urgency_level=result.get("urgency_level", "medium"),
            reasoning=result.get("reasoning", "Analysis completed"),
            recommended_actions=result.get("recommended_actions", [])
        )
    except Exception as e:
        logger.error(f"Urgency analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Urgency analysis service temporarily unavailable")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response = await chat_with_civic_assistant(request.query)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat service error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable")

@app.get("/api/issues/recent", response_model=List[IssueResponse])
def get_recent_issues(db: Session = Depends(get_db)):
    cached_data = recent_issues_cache.get("recent_issues")
    if cached_data:
        return JSONResponse(content=cached_data)

    # Fetch last 10 issues
    issues = db.query(Issue).order_by(Issue.created_at.desc()).limit(10).all()

    # Convert to Pydantic models for validation and serialization
    data = []
    for i in issues:
        data.append(IssueResponse(
            id=i.id,
            category=i.category,
            description=i.description[:100] + "..." if len(i.description) > 100 else i.description,
            created_at=i.created_at,
            image_path=i.image_path,
            status=i.status,
            upvotes=i.upvotes if i.upvotes is not None else 0,
            location=i.location,
            latitude=i.latitude,
            longitude=i.longitude,
            action_plan=i.action_plan
        ).model_dump(mode='json'))

    # Thread-safe cache update
    recent_issues_cache.set(data, "recent_issues")
    return data

@app.post("/api/detect-pothole", response_model=DetectionResponse)
async def detect_pothole_endpoint(image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
        # Validate image for processing
        await run_in_threadpool(validate_image_for_processing, pil_image)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from validation
    except Exception as e:
        logger.error(f"Invalid image file for pothole detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (blocking, so run in threadpool)
    try:
        detections = await run_in_threadpool(detect_potholes, pil_image)
        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Pothole detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Pothole detection service temporarily unavailable")

@app.post("/api/detect-infrastructure", response_model=DetectionResponse)
async def detect_infrastructure_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
        # Validate image for processing
        await run_in_threadpool(validate_image_for_processing, pil_image)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from validation
    except Exception as e:
        logger.error(f"Invalid image file for infrastructure detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection using unified service (local ML by default)
    try:
        # Use shared HTTP client from app state
        client = request.app.state.http_client
        detections = await detect_infrastructure_local(pil_image, client=client)
        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Infrastructure detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Infrastructure detection service temporarily unavailable")

@app.post("/api/detect-flooding", response_model=DetectionResponse)
async def detect_flooding_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)
    
    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
        # Validate image for processing
        await run_in_threadpool(validate_image_for_processing, pil_image)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from validation
    except Exception as e:
        logger.error(f"Invalid image file for flooding detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection using unified service (local ML by default)
    try:
        # Use shared HTTP client from app state
        client = request.app.state.http_client
        detections = await detect_flooding_local(pil_image, client=client)
        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Flooding detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Flooding detection service temporarily unavailable")

# FIXED: Standardized Detection Endpoints with Consistent Validation
@app.post("/api/detect-vandalism", response_model=DetectionResponse)
async def detect_vandalism_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)
    
    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
        # Validate image for processing
        await run_in_threadpool(validate_image_for_processing, pil_image)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from validation
    except Exception as e:
        logger.error(f"Invalid image file for vandalism detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection using unified service (local ML by default)
    try:
        # Use shared HTTP client from app state
        client = request.app.state.http_client
        detections = await detect_vandalism_local(pil_image, client=client)
        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Vandalism detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Detection service temporarily unavailable")

@app.post("/api/detect-garbage", response_model=DetectionResponse)
async def detect_garbage_endpoint(image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)
    
    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
        # Validate image for processing
        await run_in_threadpool(validate_image_for_processing, pil_image)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from validation
    except Exception as e:
        logger.error(f"Invalid image file for garbage detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (blocking, so run in threadpool)
    try:
        detections = await run_in_threadpool(detect_garbage, pil_image)
        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Garbage detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Detection service temporarily unavailable")

@app.post("/api/detect-illegal-parking")
async def detect_illegal_parking_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_illegal_parking_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Illegal parking detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-street-light")
async def detect_street_light_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_street_light_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Street light detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-fire")
async def detect_fire_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_fire_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Fire detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-stray-animal")
async def detect_stray_animal_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_stray_animal_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Stray animal detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-blocked-road")
async def detect_blocked_road_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_blocked_road_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Blocked road detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/detect-tree-hazard")
async def detect_tree_hazard_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_tree_hazard_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Tree hazard detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/detect-pest")
async def detect_pest_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_pest_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Pest detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/detect-severity")
async def detect_severity_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        result = await detect_severity_clip(image_bytes, client=client)
        return result
    except Exception as e:
        logger.error(f"Severity detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/detect-smart-scan")
async def detect_smart_scan_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        result = await detect_smart_scan_clip(image_bytes, client=client)
        return result
    except Exception as e:
        logger.error(f"Smart scan detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/generate-description")
async def generate_description_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        description = await generate_image_caption(image_bytes, client=client)
        if not description:
            return {"description": "", "error": "Could not generate description"}
        return {"description": description}
    except Exception as e:
        logger.error(f"Description generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/mh/rep-contacts")
async def get_maharashtra_rep_contacts(pincode: str = Query(...)):
    """
    Get MLA and representative contact information for Maharashtra by pincode.
    """
    # Validate and sanitize pincode
    try:
        from backend.validation import validate_pincode
        pincode = validate_pincode(pincode)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pincode validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid pincode format")
    
    # Find constituency by pincode
    constituency_info = find_constituency_by_pincode(pincode)
    
    if not constituency_info:
        raise HTTPException(
            status_code=404,
            detail="Unknown pincode for Maharashtra MVP. Currently only supporting limited pincodes."
        )
    
    # Find MLA by constituency
    # If constituency_info exists but assembly_constituency is None, it means we only found District info via fallback
    assembly_constituency = constituency_info.get("assembly_constituency")
    mla_info = None

    if assembly_constituency:
        mla_info = find_mla_by_constituency(assembly_constituency)
    
    # If explicit MLA lookup failed or wasn't possible, create a generic placeholder
    if not mla_info:
        mla_info = {
            "mla_name": "MLA Info Unavailable",
            "party": "N/A",
            "phone": "N/A",
            "email": "N/A",
            "twitter": "Not Available"
        }
        # If we have a district but no constituency, explain it
        if not assembly_constituency:
             constituency_info["assembly_constituency"] = "Unknown (District Found)"
    
    # Generate AI summary (optional)
    description = None
    try:
        # Only generate summary if we have a valid constituency and MLA
        if assembly_constituency and mla_info["mla_name"] != "MLA Info Unavailable":
            ai_services = get_ai_services()
            description = await ai_services.mla_summary_service.generate_mla_summary(
                district=constituency_info["district"],
                assembly_constituency=assembly_constituency,
                mla_name=mla_info["mla_name"]
            )
    except Exception as e:
        logger.error(f"Error generating MLA summary: {e}")
        # Continue without description
    
    # Build response
    response = {
        "pincode": pincode,
        "state": constituency_info["state"],
        "district": constituency_info["district"],
        "assembly_constituency": constituency_info["assembly_constituency"],
        "mla": {
            "name": mla_info["mla_name"],
            "party": mla_info["party"],
            "phone": mla_info["phone"],
            "email": mla_info["email"],
            "twitter": mla_info.get("twitter")
        },
        "grievance_links": {
            "central_cpgrams": "https://pgportal.gov.in/",
            "maharashtra_portal": "https://aaplesarkar.mahaonline.gov.in/en",
            "note": "This is an MVP; data may not be fully accurate."
        }
    }
    
    # Add description if generated
    if description:
        response["description"] = description
    elif mla_info["mla_name"] == "MLA Info Unavailable":
        response["description"] = f"We found that {pincode} belongs to {constituency_info['district']} district, but we don't have the specific MLA details for this exact pincode yet."

    return response

async def send_status_notification(issue_id: int, old_status: str, new_status: str, notes: str = None):
    """Send push notification for issue status update"""
    try:
        # Get issue details
        db = next(get_db())
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return

        # Get subscriptions for this issue or general subscriptions
        subscriptions = db.query(PushSubscription).filter(
            (PushSubscription.issue_id == issue_id) | (PushSubscription.issue_id.is_(None))
        ).all()

        # VAPID keys (in production, these should be environment variables)
        vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "dev_private_key")
        vapid_public_key = os.getenv("VAPID_PUBLIC_KEY", "dev_public_key")
        vapid_email = os.getenv("VAPID_EMAIL", "mailto:test@example.com")

        status_messages = {
            "verified": "Your issue has been verified by authorities",
            "assigned": f"Your issue has been assigned to {issue.assigned_to or 'authorities'}",
            "in_progress": "Work on your issue has begun",
            "resolved": "Your issue has been resolved!"
        }

        message = status_messages.get(new_status, f"Your issue status changed to {new_status}")

        payload = {
            "title": "Issue Update",
            "body": message,
            "icon": "/icon-192.png",
            "badge": "/icon-192.png",
            "data": {
                "issue_id": issue_id,
                "status": new_status,
                "url": f"/issue/{issue_id}"
            }
        }

        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth
                        }
                    },
                    data=json.dumps(payload),
                    vapid_private_key=vapid_private_key,
                    vapid_claims={
                        "sub": vapid_email
                    }
                )
            except WebPushException as e:
                logger.error(f"Failed to send push notification: {e}")
                # Remove invalid subscriptions
                if e.response.status_code in [400, 404, 410]:
                    db.delete(subscription)

        db.commit()

    except Exception as e:
        logger.error(f"Error sending status notification: {e}")

# Note: Frontend serving code removed for separate deployment
# The frontend will be deployed on Netlify and make API calls to this backend
