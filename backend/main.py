from fastapi import FastAPI, Form, UploadFile, File, Depends, BackgroundTasks, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import List
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
from backend.local_ml_service import detect_infrastructure_local, detect_flooding_local, detect_vandalism_local
from backend.unified_detection_service import get_detection_status
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
    generate_image_caption
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
