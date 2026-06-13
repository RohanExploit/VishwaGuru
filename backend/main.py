from fastapi import FastAPI, Form, UploadFile, File, Depends, BackgroundTasks, Request, Query
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
import sys
from pathlib import Path
import httpx
import logging
import time
import magic
import httpx
from backend.grievance_classifier import get_grievance_classifier
from backend.schemas import GrievanceRequest, ChatRequest, IssueResponse
from backend.grievance_service import GrievanceService
from backend.database import Base, engine, get_db, SessionLocal
from sqlalchemy.orm import Session
import backend.dependencies
from backend.models import Issue
from backend.ai_factory import create_all_ai_services
from backend.ai_interfaces import initialize_ai_services, get_ai_services
from backend.ai_service import chat_with_civic_assistant, generate_action_plan
from backend.bot import run_bot, start_bot_thread, stop_bot_thread
from backend.exceptions import EXCEPTION_HANDLERS
from backend.init_db import migrate_db
from backend.maharashtra_locator import load_maharashtra_pincode_data, load_maharashtra_mla_data, find_constituency_by_pincode, find_mla_by_constituency
from backend.cache import recent_issues_cache
from backend.pothole_detection import detect_potholes
from backend.garbage_detection import detect_garbage
from backend.local_ml_service import (
    detect_infrastructure_local,
    detect_flooding_local,
    get_detection_status
)
from backend.gemini_services import get_ai_services, initialize_ai_services
from backend.spatial_utils import find_nearby_issues, get_bounding_box
from backend.hf_api_service import (
    detect_vandalism_clip,
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
    analyze_urgency_text,
    verify_resolution_vqa,
    detect_depth_map,
    detect_water_leak_clip,
    detect_accessibility_issue_clip,
    detect_crowd_density_clip,
    detect_audio_event,
    transcribe_audio
)

def validate_image_for_processing(image):
    if not image:
        pass

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def background_initialization(app: FastAPI):
    """Perform non-critical startup tasks in background to speed up app availability"""
    try:
        # 1. AI Services initialization
        # These can take a few seconds due to imports and configuration
        action_plan_service, chat_service, mla_summary_service = await run_in_threadpool(create_all_ai_services)

        initialize_ai_services(
            action_plan_service=action_plan_service,
            chat_service=chat_service,
            mla_summary_service=mla_summary_service
        )
        logger.info("AI services initialized successfully.")

        # 2. Static data pre-loading (loads large JSONs into memory)
        await run_in_threadpool(load_maharashtra_pincode_data)
        await run_in_threadpool(load_maharashtra_mla_data)
        logger.info("Maharashtra data pre-loaded successfully.")

        # Ensure uploads directory exists
        os.makedirs("data/uploads", exist_ok=True)

        # 3. Start Telegram Bot in separate thread
        # Temporarily disabled for local testing
        # await run_in_threadpool(start_bot_thread)
        logger.info("Telegram bot initialization skipped for local testing.")
    except Exception as e:
        logger.error(f"Error during background initialization: {e}", exc_info=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Shared HTTP Client for external APIs (Connection Pooling)
    app.state.http_client = httpx.AsyncClient()
    # Set global shared client in dependencies for cached functions
    backend.dependencies.SHARED_HTTP_CLIENT = app.state.http_client
    logger.info("Shared HTTP Client initialized.")

    # Startup: Database setup (Blocking but necessary for app consistency)
    try:
        logger.info("Starting database initialization...")
        await run_in_threadpool(Base.metadata.create_all, bind=engine)
        logger.info("Base.metadata.create_all completed.")
        # Enabled database migrations for production deployment
        await run_in_threadpool(migrate_db)
        logger.info("Database initialized successfully with migrations.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # We continue to allow health checks even if DB has issues (for debugging)

    # Startup: Initialize Grievance Service (needed for escalation engine)
    try:
        logger.info("Initializing grievance service...")
        # Enabled grievance service for escalation logic
        grievance_service = GrievanceService()
        app.state.grievance_service = grievance_service
        logger.info("Grievance service initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing grievance service: {e}", exc_info=True)

    # Launch background tasks that are non-blocking for startup/health-check
    asyncio.create_task(background_initialization(app))

    # Start the daily civic intelligence refinement scheduler (temporarily disabled for local dev)
    # start_scheduler()
    logger.info("Scheduler skipped for local development")

    yield
    
    # Shutdown: Close Shared HTTP Client
    if app.state.http_client:
        await app.state.http_client.aclose()
    logger.info("Shared HTTP Client closed.")

    # Shutdown: Stop Telegram Bot thread
    try:
        await run_in_threadpool(stop_bot_thread)
        logger.info("Telegram bot thread stopped.")
    except Exception as e:
        logger.error(f"Error stopping bot thread: {e}")

app = FastAPI(
    title="VishwaGuru Backend",
    description="AI-powered civic issue reporting and resolution platform",
    version="1.0.0",
    # Enable lifespan context manager for resource management and startup tasks
    lifespan=lifespan
)

# Add centralized exception handlers
for exception_type, handler in EXCEPTION_HANDLERS.items():
    app.add_exception_handler(exception_type, handler)

# CORS Configuration - Security Enhanced
frontend_url = os.environ.get("FRONTEND_URL")
is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"

if not frontend_url:
    if is_production:
        raise ValueError(
            "FRONTEND_URL environment variable is required for security in production. "
            "Set it to your frontend URL (e.g., https://your-app.netlify.app)."
        )
    else:
        logger.warning("FRONTEND_URL not set. Defaulting to http://localhost:5173 for development.")
        frontend_url = "http://localhost:5173"

if not (frontend_url.startswith("http://") or frontend_url.startswith("https://")):
    raise ValueError(
        f"FRONTEND_URL must be a valid HTTP/HTTPS URL. Got: {frontend_url}"
    )

allowed_origins = [frontend_url]

if not is_production:
    dev_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:8080",
    ]
    allowed_origins.extend(dev_origins)
    # Also add the one from .env if it's different
    if frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=500)

# Mount static files for uploads
# check if directory exists, if not create it (redundant but safe)
os.makedirs("data/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

# Include Modular Routers
app.include_router(issues.router, tags=["Issues"])
app.include_router(detection.router, tags=["Detection"])
app.include_router(grievances.router, tags=["Grievances"])
app.include_router(utility.router, tags=["Utility"])
app.include_router(auth.router, tags=["Authentication"])
app.include_router(admin.router)
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(voice.router, tags=["Voice & Language"])
app.include_router(field_officer.router, tags=["Field Officer Check-In"])
app.include_router(hf.router, tags=["Hugging Face"])
app.include_router(resolution_proof.router, tags=["Resolution Proof"])

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "VishwaGuru API",
        "version": "1.0.0"
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

@app.get("/api/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(db: Session = Depends(get_db)):
    # Group by user_email, count issues, sum upvotes
    results = db.query(
        Issue.user_email,
        func.count(Issue.id).label('count'),
        func.sum(Issue.upvotes).label('total_upvotes')
    ).filter(
        Issue.user_email.isnot(None),
        Issue.user_email != ""
    ).group_by(Issue.user_email).order_by(func.count(Issue.id).desc()).limit(10).all()

    leaderboard = []
    for idx, (email, count, upvotes) in enumerate(results):
        # Mask email
        try:
            if '@' in email:
                name, domain = email.split('@')
                masked_email = f"{name[0]}***@{domain}"
            else:
                masked_email = email[:3] + "***"
        except:
            masked_email = "User***"

        leaderboard.append(LeaderboardEntry(
            user_email=masked_email,
            reports_count=count,
            total_upvotes=upvotes or 0,
            rank=idx + 1
        ))

    return LeaderboardResponse(leaderboard=leaderboard)


@app.get("/api/issues/recent", response_model=List[IssueSummaryResponse])
def get_recent_issues(db: Session = Depends(get_db)):
    cached_data = recent_issues_cache.get("recent_issues")
    if cached_data:
        return JSONResponse(content=cached_data)

    # Fetch last 10 issues, deferring action_plan for performance
    issues = db.query(Issue).options(defer(Issue.action_plan)).order_by(Issue.created_at.desc()).limit(10).all()

    # Convert to Pydantic models for validation and serialization
    data = []
    for i in issues:
        data.append(IssueSummaryResponse(
            id=i.id,
            category=i.category,
            description=i.description[:100] + "..." if len(i.description) > 100 else i.description,
            created_at=i.created_at,
            image_path=i.image_path,
            status=i.status,
            upvotes=i.upvotes if i.upvotes is not None else 0,
            location=i.location,
            latitude=i.latitude,
            longitude=i.longitude
            # action_plan is deferred and excluded
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

    # Run detection using HF API (Lightweight)
    try:
        # Use shared HTTP client from app state
        client = request.app.state.http_client
        detections = await detect_vandalism_clip(pil_image, client=client)
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
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_cached_or_compute(cache_key: str, compute_func, *args, **kwargs):
    """Get cached result or compute and cache it."""
    global _cache_cleanup_counter
    now = datetime.now(timezone.utc).timestamp()
    
    # Clean expired entries periodically
    _cache_cleanup_counter += 1
    if _cache_cleanup_counter > 100 or len(image_processing_cache) > 1000:
        _cache_cleanup_counter = 0
        expired_keys = [k for k, v in image_processing_cache.items() if now - v['timestamp'] > CACHE_EXPIRY]
        for k in expired_keys:
            del image_processing_cache[k]
    
    if cache_key in image_processing_cache:
        return image_processing_cache[cache_key]['result']
    
    # Compute and cache
    result = await compute_func(*args, **kwargs)
    image_processing_cache[cache_key] = {
        'result': result,
        'timestamp': now
    }
    return result


@app.post("/api/detect-severity")
async def detect_severity_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        # Create cache key from image hash
        import hashlib
        image_hash = hashlib.md5(image_bytes).hexdigest()
        cache_key = f"severity_{image_hash}"
        
        client = request.app.state.http_client
        result = get_cached_or_compute(cache_key, detect_severity_clip, image_bytes, client)
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
        # Create cache key from image hash
        image_hash = hashlib.md5(image_bytes).hexdigest()
        cache_key = f"smart_scan_{image_hash}"
        
        client = request.app.state.http_client
        result = await get_cached_or_compute(cache_key, detect_smart_scan_clip, image_bytes, client)
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
        # Create cache key from image hash
        image_hash = hashlib.md5(image_bytes).hexdigest()
        cache_key = f"description_{image_hash}"
        
        client = request.app.state.http_client
        description = await get_cached_or_compute(cache_key, generate_image_caption, image_bytes, client)
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
    reason: str = Query(..., description="Reason for manual escalation"),
    db: Session = Depends(get_db)
):
    """Manually escalate a grievance"""
    try:
        grievance_service = getattr(db.get_bind()._app.state, 'grievance_service', None)
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
async def detect_waste_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        # Cache key
        image_hash = hashlib.md5(image_bytes).hexdigest()
        cache_key = f"waste_{image_hash}"

        result = await get_cached_or_compute(cache_key, detect_waste_clip, image_bytes, client)
        return result
    except Exception as e:
        logger.error(f"Waste detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-civic-eye")
async def detect_civic_eye_endpoint(request: Request, image: UploadFile = File(...)):
    # Validate uploaded file
    await validate_uploaded_file(image)

    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = request.app.state.http_client
        # Cache key
        image_hash = hashlib.md5(image_bytes).hexdigest()
        cache_key = f"civic_eye_{image_hash}"

        result = await get_cached_or_compute(cache_key, detect_civic_eye_clip, image_bytes, client)
        return result
    except Exception as e:
        logger.error(f"Civic Eye detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# Note: Frontend serving code removed for separate deployment
# The frontend will be deployed on Netlify and make API calls to this backend
