from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func
from sqlalchemy.orm import Session, defer, joinedload
from pydantic import BaseModel
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import List, Union, Any, Dict, Optional
from datetime import datetime, timedelta, timezone
from PIL import Image

import json
import os
import shutil
import uuid
import asyncio
from fastapi import Depends
from contextlib import asynccontextmanager
from bot import run_bot
from pothole_detection import detect_potholes
from garbage_detection import detect_garbage
from hf_service import detect_vandalism_clip, detect_flooding_clip, detect_infrastructure_clip
from PIL import Image
from init_db import migrate_db
from image_validator import validate_uploaded_image, ImageValidationError
import logging
import time

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Shared HTTP Client for cached functions
SHARED_HTTP_CLIENT: Optional[httpx.AsyncClient] = None

# File upload validation constants
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB (increased for better user experience)
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

# Image processing cache to avoid duplicate API calls
# Replaced custom cache with async_lru for better performance and memory management

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
            
            # Resize large images for better performance
            img = Image.open(file.file)
            if img.width > 1024 or img.height > 1024:
                # Calculate new size maintaining aspect ratio
                ratio = min(1024 / img.width, 1024 / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save resized image back to file
                output = io.BytesIO()
                img.save(output, format=img.format or 'JPEG', quality=85)
                output.seek(0)
                
                # Replace file content
                file.file = output
                file.size = output.tell()
                output.seek(0)
                
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

async def process_and_detect(image: UploadFile, detection_func) -> DetectionResponse:
    """
    Helper to process uploaded image and run detection.
    Handles validation, loading, and error handling.
    """
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
        logger.error(f"Invalid image file during processing: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection
    try:
        detections = await detection_func(pil_image)
        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Detection service temporarily unavailable")

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

async def create_grievance_from_issue_background(issue_id: int):
    """Background task to create a grievance from an issue for escalation management"""
    db = SessionLocal()
    try:
        # Get the issue
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            logger.error(f"Issue {issue_id} not found for grievance creation")
            return

        # Get grievance service
        grievance_service = GrievanceService()

        # Map issue category to grievance severity
        severity_mapping = {
            'pothole': 'high',
            'garbage': 'medium',
            'streetlight': 'medium',
            'flood': 'critical',
            'infrastructure': 'high',
            'parking': 'low',
            'fire': 'critical',
            'animal': 'medium',
            'blocked': 'high',
            'tree': 'medium',
            'pest': 'low',
            'vandalism': 'medium'
        }

        severity = severity_mapping.get(issue.category.lower(), 'medium')

        # Create grievance data
        grievance_data = {
            'category': issue.category,
            'severity': severity,
            'pincode': None,  # Will be determined by routing service
            'description': issue.description,
            'location': {
                'latitude': issue.latitude,
                'longitude': issue.longitude,
                'address': issue.location
            },
            'reporter_info': {
                'email': issue.user_email,
                'source': issue.source
            }
        }

        # Create grievance
        grievance = grievance_service.create_grievance(grievance_data, db)
        if grievance:
            logger.info(f"Created grievance {grievance.id} from issue {issue_id}")
        else:
            logger.error(f"Failed to create grievance from issue {issue_id}")

    except Exception as e:
        logger.error(f"Error creating grievance from issue {issue_id}: {e}", exc_info=True)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global SHARED_HTTP_CLIENT
    # Startup: Migrate DB
    migrate_db()

    # Startup: Initialize Shared HTTP Client for external APIs (Connection Pooling)
    app.state.http_client = httpx.AsyncClient()
    SHARED_HTTP_CLIENT = app.state.http_client
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

    # Startup: Initialize Grievance Service
    try:
        grievance_service = GrievanceService()
        app.state.grievance_service = grievance_service
        logger.info("Grievance service initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing grievance service: {e}", exc_info=True)
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
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        services={
            "database": "connected",
            "ai_services": "initialized"
        }
    )

@app.get("/api/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    cached_stats = recent_issues_cache.get("stats")
    if cached_stats:
        return JSONResponse(content=cached_stats)

    total = db.query(func.count(Issue.id)).scalar()
    resolved = db.query(func.count(Issue.id)).filter(Issue.status.in_(['resolved', 'verified'])).scalar()
    # Pending is everything else
    pending = total - resolved

    # By category
    cat_counts = db.query(Issue.category, func.count(Issue.id)).group_by(Issue.category).all()
    issues_by_category = {cat: count for cat, count in cat_counts}

    response = StatsResponse(
        total_issues=total,
        resolved_issues=resolved,
        pending_issues=pending,
        issues_by_category=issues_by_category
    )

    data = response.model_dump(mode='json')
    recent_issues_cache.set(data, "stats")

    return response

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

@app.post("/api/issues", response_model=IssueCreateWithDeduplicationResponse, status_code=201)
async def create_issue(
    request: Request,
    background_tasks: BackgroundTasks,
    description: str = Form(..., min_length=10, max_length=1000),
    category: str = Form(..., pattern=f"^({'|'.join([cat.value for cat in IssueCategory])})$"),
    language: str = Form('en'),
    user_email: str = Form(None),
    latitude: float = Form(None, ge=-90, le=90),
    longitude: float = Form(None, ge=-180, le=180),
    location: str = Form(None, max_length=200),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
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
        
        # Save image if provided
        if image:
            # Validate the image first
            try:
                pil_image, img_format = await validate_uploaded_image(image)
            except ImageValidationError as e:
                logger.error(f"Image validation failed for issue creation: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{uuid.uuid4()}_{image.filename}"
            image_path = os.path.join(upload_dir, filename)
            await run_in_threadpool(save_file_blocking, image.file, image_path)

        # Save to DB first to ensure we capture the user's report
        new_issue = Issue(
            description=description,
            category=category,
            image_path=image_path,
            source="web",
            user_email=user_email,
            latitude=latitude,
            longitude=longitude,
            location=location,
            action_plan=action_plan_json
        )

        # Offload blocking DB operations to threadpool
        await run_in_threadpool(save_issue_db, db, new_issue)

        # Generate Action Plan (AI)
        action_plan = None
        try:
            action_plan = await generate_action_plan(description, category, image_path)

            # Update the issue with the action plan
            new_issue.action_plan = json.dumps(action_plan)
            db.commit() # We are in the main thread (but db object might need care if reused from threadpool?
                        # Actually save_issue_db uses the session. The session is not thread-safe but we are back in async main thread.
                        # Wait, save_issue_db was run in threadpool. The 'new_issue' object is attached to 'db' session.
                        # We should be careful. It is safer to re-query or just update via session in threadpool if strictly needed.
                        # But since we are using 'run_in_threadpool', the 'db' session is technically used there.
                        # FastAPI dependency 'db' is created in the main thread (async).
                        # 'run_in_threadpool' runs in a separate thread.
                        # If we use 'db' here again, it might be fine if the threadpool task is finished.
                        # But to be safe and robust, let's wrap the update in a function run in threadpool again.
        except Exception as e:
            logger.error(f"Error generating action plan: {e}", exc_info=True)
            # We don't fail the request if AI fails, just return without plan

        if action_plan:
             # Update DB with action plan
             def update_issue_plan(db, issue_id, plan):
                 issue = db.query(Issue).filter(Issue.id == issue_id).first()
                 if issue:
                     issue.action_plan = plan
                     db.commit()

             await run_in_threadpool(update_issue_plan, db, new_issue.id, json.dumps(action_plan))

        # Invalidate recent issues cache
        global RECENT_ISSUES_CACHE
        RECENT_ISSUES_CACHE = None

        return {
            "id": new_issue.id,
            "message": "Issue reported successfully",
            "action_plan": action_plan_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    # Spatial deduplication check
    deduplication_info = None
    linked_issue_id = None

    if latitude is not None and longitude is not None:
        try:
            # Find existing open issues within 50 meters
            # Optimization: Use bounding box to filter candidates in SQL
            min_lat, max_lat, min_lon, max_lon = get_bounding_box(latitude, longitude, 50.0)

            open_issues = await run_in_threadpool(
                lambda: db.query(Issue).filter(
                    Issue.status == "open",
                    Issue.latitude >= min_lat,
                    Issue.latitude <= max_lat,
                    Issue.longitude >= min_lon,
                    Issue.longitude <= max_lon
                ).all()
            )

            nearby_issues_with_distance = find_nearby_issues(
                open_issues, latitude, longitude, radius_meters=50.0
            )

            if nearby_issues_with_distance:
                # Found nearby issues - prepare deduplication response
                nearby_responses = [
                    NearbyIssueResponse(
                        id=issue.id,
                        description=issue.description[:100] + "..." if len(issue.description) > 100 else issue.description,
                        category=issue.category,
                        latitude=issue.latitude,
                        longitude=issue.longitude,
                        distance_meters=distance,
                        upvotes=issue.upvotes or 0,
                        created_at=issue.created_at,
                        status=issue.status
                    )
                    for issue, distance in nearby_issues_with_distance[:3]  # Limit to top 3 closest
                ]

                deduplication_info = DeduplicationCheckResponse(
                    has_nearby_issues=True,
                    nearby_issues=nearby_responses,
                    recommended_action="upvote_existing"
                )

                # Automatically upvote the closest issue and link this report to it
                closest_issue, _ = nearby_issues_with_distance[0]
                closest_issue.upvotes = (closest_issue.upvotes or 0) + 1
                linked_issue_id = closest_issue.id

                # Update the database with the upvote
                await run_in_threadpool(db.commit)

                logger.info(f"Spatial deduplication: Linked new report to existing issue {closest_issue.id}, upvoted to {closest_issue.upvotes}")

        except Exception as e:
            logger.error(f"Error during spatial deduplication check: {e}", exc_info=True)
            # Continue with issue creation if deduplication fails

    try:
        # Save to DB only if no nearby issues found or deduplication failed
        if deduplication_info is None or not deduplication_info.has_nearby_issues:
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
        else:
            # Don't create new issue, just return deduplication info
            new_issue = None
    except Exception as e:
        # Clean up uploaded file if DB save failed
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass  # Ignore cleanup errors
        
        logger.error(f"Database error while creating issue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save issue to database")

    # Add background task for AI generation only if new issue was created
    if new_issue:
        background_tasks.add_task(process_action_plan_background, new_issue.id, description, category, language, image_path)
        
        # Create grievance for escalation management
        background_tasks.add_task(create_grievance_from_issue_background, new_issue.id)

        # Optimistic Cache Update with thread-safe operations
        try:
            current_cache = recent_issues_cache.get("recent_issues")
            if current_cache:
                # Create a dict representation of the new issue
                # Using IssueSummaryResponse to match the list view optimization
                new_issue_dict = IssueSummaryResponse(
                    id=new_issue.id,
                    category=new_issue.category,
                    description=new_issue.description[:100] + "..." if len(new_issue.description) > 100 else new_issue.description,
                    created_at=new_issue.created_at,
                    image_path=new_issue.image_path,
                    status=new_issue.status,
                    upvotes=new_issue.upvotes if new_issue.upvotes is not None else 0,
                    location=new_issue.location,
                    latitude=new_issue.latitude,
                    longitude=new_issue.longitude
                    # action_plan excluded
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

    # Prepare deduplication info if not already set
    if deduplication_info is None:
        deduplication_info = DeduplicationCheckResponse(
            has_nearby_issues=False,
            nearby_issues=[],
            recommended_action="create_new"
        )

    # Return response with deduplication information
    if new_issue:
        return IssueCreateWithDeduplicationResponse(
            id=new_issue.id,
            message="Issue reported successfully. Action plan will be generated shortly.",
            action_plan=None,
            deduplication_info=deduplication_info,
            linked_issue_id=linked_issue_id
        )
    else:
        return IssueCreateWithDeduplicationResponse(
            id=None,
            message="Similar issue found nearby. Your report has been linked to the existing issue to increase its priority.",
            action_plan=None,
            deduplication_info=deduplication_info,
            linked_issue_id=linked_issue_id
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

@app.get("/api/issues/nearby", response_model=List[NearbyIssueResponse])
def get_nearby_issues(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude of the location"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude of the location"),
    radius: float = Query(50.0, ge=10, le=500, description="Search radius in meters"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get issues near a specific location for deduplication purposes.
    Returns issues within the specified radius, sorted by distance.
    """
    try:
        # Query open issues with coordinates
        # Optimization: Use bounding box to filter candidates in SQL
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(latitude, longitude, radius)

        open_issues = db.query(Issue).filter(
            Issue.status == "open",
            Issue.latitude >= min_lat,
            Issue.latitude <= max_lat,
            Issue.longitude >= min_lon,
            Issue.longitude <= max_lon
        ).all()

        nearby_issues_with_distance = find_nearby_issues(
            open_issues, latitude, longitude, radius_meters=radius
        )

        # Convert to response format and limit results
        nearby_responses = [
            NearbyIssueResponse(
                id=issue.id,
                description=issue.description[:100] + "..." if len(issue.description) > 100 else issue.description,
                category=issue.category,
                latitude=issue.latitude,
                longitude=issue.longitude,
                distance_meters=distance,
                upvotes=issue.upvotes or 0,
                created_at=issue.created_at,
                status=issue.status
            )
            for issue, distance in nearby_issues_with_distance[:limit]
        ]

        return nearby_responses

    except Exception as e:
        logger.error(f"Error getting nearby issues: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve nearby issues")

@app.post("/api/issues/{issue_id}/verify", response_model=Union[VoteResponse, Dict[str, Any]])
async def verify_issue_endpoint(
    issue_id: int,
    request: Request,
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    issue = await run_in_threadpool(lambda: db.query(Issue).filter(Issue.id == issue_id).first())
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if image:
        # AI Verification Logic
        # Validate uploaded file
        await validate_uploaded_file(image)

        try:
            image_bytes = await image.read()
        except Exception as e:
            logger.error(f"Invalid image file: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Construct question
        category = issue.category.lower() if issue.category else "issue"
        question = f"Is there a {category} in this image?"

        # Custom questions for common categories
        if "pothole" in category:
            question = "Is there a pothole on the road?"
        elif "garbage" in category or "waste" in category:
            question = "Is there garbage or trash on the ground?"
        elif "light" in category:
            question = "Is the streetlight broken?"
        elif "water" in category or "flood" in category:
            question = "Is the street flooded?"
        elif "tree" in category:
            question = "Is there a fallen tree?"

        try:
            client = request.app.state.http_client
            result = await verify_resolution_vqa(image_bytes, question, client)

            answer = result.get('answer', 'unknown')
            confidence = result.get('confidence', 0)

            # If the answer is "no" (meaning the issue is NOT present), we consider it resolved.
            is_resolved = False
            if answer.lower() in ["no", "none", "nothing"] and confidence > 0.5:
                is_resolved = True
                # Update status if not already resolved
                if issue.status != "resolved":
                    issue.status = "verified" # Mark as verified (resolved usually implies closed)
                    issue.verified_at = datetime.now(timezone.utc)
                    await run_in_threadpool(db.commit)

            return {
                "is_resolved": is_resolved,
                "ai_answer": answer,
                "confidence": confidence,
                "question_asked": question
            }
        except Exception as e:
            logger.error(f"Resolution verification error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Verification service temporarily unavailable")
    else:
        # Manual Verification Logic (Vote)
        # Increment upvotes (verification counts as strong support)
        if issue.upvotes is None:
            issue.upvotes = 0
        issue.upvotes += 2  # Verification counts as 2 upvotes

        # If issue has enough verifications, consider upgrading status
        if issue.upvotes >= 5 and issue.status == "open":
            issue.status = "verified"
            logger.info(f"Issue {issue_id} automatically verified due to {issue.upvotes} upvotes")

        await run_in_threadpool(db.commit)
        await run_in_threadpool(db.refresh, issue)

        return VoteResponse(
            id=issue.id,
            upvotes=issue.upvotes,
            message="Issue verified successfully"
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

# Simple in-memory cache for recent issues
RECENT_ISSUES_CACHE = None
RECENT_ISSUES_TIMESTAMP = 0
CACHE_TTL = 60 # 60 seconds

@app.get("/api/issues/recent")
def get_recent_issues(db: Session = Depends(get_db)):
    global RECENT_ISSUES_CACHE, RECENT_ISSUES_TIMESTAMP

    current_time = time.time()
    if RECENT_ISSUES_CACHE and (current_time - RECENT_ISSUES_TIMESTAMP < CACHE_TTL):
        return RECENT_ISSUES_CACHE

    # Fetch last 10 issues
    issues = db.query(Issue).order_by(Issue.created_at.desc()).limit(10).all()
    # Sanitize data (no emails)
    result = [
        {
            "id": i.id,
            "category": i.category,
            "description": i.description[:100] + "..." if len(i.description) > 100 else i.description,
            "created_at": i.created_at,
            "image_path": i.image_path,
            "status": i.status,
            "upvotes": i.upvotes if i.upvotes is not None else 0
        }
        for i in issues
    ]

    RECENT_ISSUES_CACHE = result
    RECENT_ISSUES_TIMESTAMP = current_time

    return result

@app.post("/api/detect-pothole")
async def detect_pothole_endpoint(image: UploadFile = File(...)):
    # Validate and convert to PIL Image
    try:
        pil_image, img_format = await validate_uploaded_image(image)
    except ImageValidationError as e:
        logger.error(f"Image validation failed for pothole detection: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Invalid image file for pothole detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection
    try:
        if is_model_available():
            # Use local model if available (blocking)
            detections = await run_in_threadpool(detect_potholes, pil_image)
        else:
            # Fallback to Hugging Face API
            logger.info("Local pothole model unavailable, falling back to HF API")
            client = request.app.state.http_client
            detections = await detect_pothole_clip(pil_image, client=client)

        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Pothole detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Pothole detection service temporarily unavailable")

@app.post("/api/detect-infrastructure")
async def detect_infrastructure_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate and convert to PIL Image
    try:
        pil_image, img_format = await validate_uploaded_image(image)
    except ImageValidationError as e:
        logger.error(f"Image validation failed for infrastructure detection: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Invalid image file for infrastructure detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

@app.post("/api/detect-flooding", response_model=DetectionResponse)
async def detect_flooding_endpoint(image: UploadFile = File(...)):
    return await process_and_detect(image, detect_flooding_unified)

@app.post("/api/detect-flooding")
async def detect_flooding_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate and convert to PIL Image
    try:
        pil_image, img_format = await validate_uploaded_image(image)
    except ImageValidationError as e:
        logger.error(f"Image validation failed for flooding detection: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Invalid image file for flooding detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (async)
    try:
        # Use shared HTTP client from app state
        client = request.app.state.http_client
        detections = await detect_flooding_clip(pil_image, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Flooding detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-vandalism")
async def detect_vandalism_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate and convert to PIL Image
    try:
        pil_image, img_format = await validate_uploaded_image(image)
    except ImageValidationError as e:
        logger.error(f"Image validation failed for vandalism detection: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Invalid image file for vandalism detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (async)
    try:
        # Use shared HTTP client from app state
        client = request.app.state.http_client
        detections = await detect_vandalism_clip(pil_image, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Vandalism detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-garbage")
async def detect_garbage_endpoint(image: UploadFile = File(...)):
    # Validate and convert to PIL Image
    try:
        pil_image, img_format = await validate_uploaded_image(image)
    except ImageValidationError as e:
        logger.error(f"Image validation failed for garbage detection: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_tree_clip(pil_image, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Tree hazard detection error: {e}", exc_info=True)
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


@app.post("/api/detect-water-leak")
async def detect_water_leak_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_water_leak_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Water leak detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/detect-accessibility")
async def detect_accessibility_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_accessibility_issue_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Accessibility detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/detect-crowd")
async def detect_crowd_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        detections = await detect_crowd_density_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Crowd detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/detect-audio")
async def detect_audio_endpoint(request: Request, file: UploadFile = File(...)):
    # Basic audio validation
    # Allow webm (browser default), wav, mp3
    if file.content_type and not file.content_type.startswith("audio/"):
         # Some browsers might send application/octet-stream for blobs
         pass

    # Check simple extension just in case if name is available, but for blob it might be 'blob'

    # Just proceed to read and try
    # 10MB limit for audio
    if hasattr(file, 'size') and file.size and file.size > 10 * 1024 * 1024:
         raise HTTPException(status_code=413, detail="Audio file too large")

    try:
        audio_bytes = await file.read()
        if len(audio_bytes) > 10 * 1024 * 1024:
             raise HTTPException(status_code=413, detail="Audio file too large")
    except Exception as e:
        logger.error(f"Invalid audio file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid audio file")

    try:
        client = request.app.state.http_client
        detections = await detect_audio_event(audio_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Audio detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@alru_cache(maxsize=100)
async def _cached_detect_severity(image_bytes: bytes):
    from backend.hf_api_service import detect_severity_clip
    return await detect_severity_clip(image_bytes, client=SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_detect_smart_scan(image_bytes: bytes):
    from backend.hf_api_service import detect_smart_scan_clip
    return await detect_smart_scan_clip(image_bytes, client=SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_generate_caption(image_bytes: bytes):
    from backend.hf_api_service import generate_image_caption
    return await generate_image_caption(image_bytes, client=SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_detect_waste(image_bytes: bytes):
    from backend.hf_api_service import detect_waste_clip
    return await detect_waste_clip(image_bytes, client=SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_detect_civic_eye(image_bytes: bytes):
    from backend.hf_api_service import detect_civic_eye_clip
    return await detect_civic_eye_clip(image_bytes, client=SHARED_HTTP_CLIENT)


@app.post("/api/detect-severity")
async def detect_severity_endpoint(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        return await _cached_detect_severity(image_bytes)
    except Exception as e:
        logger.error(f"Severity detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/detect-smart-scan")
async def detect_smart_scan_endpoint(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        return await _cached_detect_smart_scan(image_bytes)
    except Exception as e:
        logger.error(f"Smart scan detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/generate-description")
async def generate_description_endpoint(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        description = await _cached_generate_caption(image_bytes)
        if not description:
            return {"description": "", "error": "Could not generate description"}
        return {"description": description}
    except Exception as e:
        logger.error(f"Description generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/analyze-depth")
async def analyze_depth_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        result = await detect_depth_map(image_bytes, client=client)
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Depth analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/mh/rep-contacts")
async def get_maharashtra_rep_contacts(pincode: str = Query(..., min_length=6, max_length=6)):
    """
    Get MLA and representative contact information for Maharashtra by pincode.
    
    Args:
        pincode: 6-digit pincode for Maharashtra
        
    Returns:
        JSON with MLA details, constituency info, and grievance portal links
    """
    # Validate pincode format
    if not pincode.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Invalid pincode format. Must be 6 digits."
        )
    
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

def send_status_notification(issue_id: int, old_status: str, new_status: str, notes: str = None):
    """Send push notification for issue status update"""
    db = SessionLocal()
    try:
        # Get issue details
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
    finally:
        db.close()

# Escalation API Endpoints
@app.get("/api/grievances", response_model=List[GrievanceSummaryResponse])
def get_grievances(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get list of grievances with escalation history"""
    try:
        query = db.query(Grievance).options(
            joinedload(Grievance.audit_logs),
            joinedload(Grievance.jurisdiction)
        )

        if status:
            query = query.filter(Grievance.status == status)
        if category:
            query = query.filter(Grievance.category == category)

        grievances = query.offset(offset).limit(limit).all()

        # Convert to response format
        result = []
        for grievance in grievances:
            escalation_history = [
                EscalationAuditResponse(
                    id=audit.id,
                    grievance_id=audit.grievance_id,
                    previous_authority=audit.previous_authority,
                    new_authority=audit.new_authority,
                    timestamp=audit.timestamp,
                    reason=audit.reason.value
                )
                for audit in grievance.audit_logs
            ]

            result.append(GrievanceSummaryResponse(
                id=grievance.id,
                unique_id=grievance.unique_id,
                category=grievance.category,
                severity=grievance.severity.value,
                pincode=grievance.pincode,
                city=grievance.city,
                district=grievance.district,
                state=grievance.state,
                current_jurisdiction_id=grievance.current_jurisdiction_id,
                assigned_authority=grievance.assigned_authority,
                sla_deadline=grievance.sla_deadline,
                status=grievance.status.value,
                created_at=grievance.created_at,
                updated_at=grievance.updated_at,
                resolved_at=grievance.resolved_at,
                escalation_history=escalation_history
            ))

        return result

    except Exception as e:
        logger.error(f"Error getting grievances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve grievances")

@app.get("/api/grievances/{grievance_id}", response_model=GrievanceSummaryResponse)
def get_grievance(grievance_id: int, db: Session = Depends(get_db)):
    """Get detailed grievance information with escalation history"""
    try:
        grievance = db.query(Grievance).options(
            joinedload(Grievance.audit_logs),
            joinedload(Grievance.jurisdiction)
        ).filter(Grievance.id == grievance_id).first()

        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")

        escalation_history = [
            EscalationAuditResponse(
                id=audit.id,
                grievance_id=audit.grievance_id,
                previous_authority=audit.previous_authority,
                new_authority=audit.new_authority,
                timestamp=audit.timestamp,
                reason=audit.reason.value
            )
            for audit in grievance.audit_logs
        ]

        return GrievanceSummaryResponse(
            id=grievance.id,
            unique_id=grievance.unique_id,
            category=grievance.category,
            severity=grievance.severity.value,
            pincode=grievance.pincode,
            city=grievance.city,
            district=grievance.district,
            state=grievance.state,
            current_jurisdiction_id=grievance.current_jurisdiction_id,
            assigned_authority=grievance.assigned_authority,
            sla_deadline=grievance.sla_deadline,
            status=grievance.status.value,
            created_at=grievance.created_at,
            updated_at=grievance.updated_at,
            resolved_at=grievance.resolved_at,
            escalation_history=escalation_history
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve grievance")

@app.get("/api/escalation-stats", response_model=EscalationStatsResponse)
def get_escalation_stats(db: Session = Depends(get_db)):
    """Get escalation statistics"""
    try:
        total_grievances = db.query(func.count(Grievance.id)).scalar()
        escalated_grievances = db.query(func.count(Grievance.id)).filter(Grievance.status == "escalated").scalar()
        active_grievances = db.query(func.count(Grievance.id)).filter(Grievance.status.in_(["open", "in_progress"])).scalar()
        resolved_grievances = db.query(func.count(Grievance.id)).filter(Grievance.status == "resolved").scalar()

        escalation_rate = (escalated_grievances / total_grievances * 100) if total_grievances > 0 else 0

        return EscalationStatsResponse(
            total_grievances=total_grievances,
            escalated_grievances=escalated_grievances,
            active_grievances=active_grievances,
            resolved_grievances=resolved_grievances,
            escalation_rate=escalation_rate
        )

    except Exception as e:
        logger.error(f"Error getting escalation stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve escalation statistics")

@app.post("/api/grievances/{grievance_id}/escalate")
def manual_escalate_grievance(
    grievance_id: int,
    request: Request,
    reason: str = Query(..., description="Reason for manual escalation"),
    db: Session = Depends(get_db)
):
    """Manually escalate a grievance"""
    try:
        grievance_service = getattr(request.app.state, 'grievance_service', None)
        if not grievance_service:
            raise HTTPException(status_code=500, detail="Grievance service not available")

        # Get the grievance
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")

        # Perform manual escalation
        success = grievance_service.escalation_engine.escalate_grievance_severity(
            grievance_id=grievance_id,
            new_severity=grievance.severity,  # Keep same severity, just escalate jurisdiction
            reason=reason,
            db=db
        )

        if success:
            return {"message": "Grievance escalated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to escalate grievance")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error escalating grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to escalate grievance")

@app.post("/api/transcribe-audio")
async def transcribe_audio_endpoint(request: Request, file: UploadFile = File(...)):
    # Basic audio validation
    if hasattr(file, 'size') and file.size and file.size > 25 * 1024 * 1024:
         raise HTTPException(status_code=413, detail="Audio file too large (max 25MB)")

    try:
        audio_bytes = await file.read()
    except Exception as e:
        logger.error(f"Invalid audio file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid audio file")

    try:
        client = request.app.state.http_client
        text = await transcribe_audio(audio_bytes, client=client)
        return {"text": text}
    except Exception as e:
        logger.error(f"Audio transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-waste")
async def detect_waste_endpoint(image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        return await _cached_detect_waste(image_bytes)
    except Exception as e:
        logger.error(f"Waste detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-civic-eye")
async def detect_civic_eye_endpoint(image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        return await _cached_detect_civic_eye(image_bytes)
    except Exception as e:
        logger.error(f"Civic Eye detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Note: Frontend serving code removed for separate deployment
# The frontend will be deployed on Netlify and make API calls to this backend
