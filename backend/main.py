import os
import sys
from pathlib import Path

# Add project root to sys.path to ensure 'backend.*' imports work
# This handles cases where PYTHONPATH is set to 'backend' (e.g. on Render)
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
repo_root = backend_dir.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
import httpx
import logging
import asyncio

from backend.database import Base, engine
from backend.ai_factory import create_all_ai_services
from backend.ai_interfaces import initialize_ai_services
from backend.bot import start_bot_thread, stop_bot_thread
from backend.init_db import migrate_db
from backend.maharashtra_locator import load_maharashtra_pincode_data, load_maharashtra_mla_data
from backend.exceptions import EXCEPTION_HANDLERS
from backend.routers import issues, detection, grievances, utility
from backend.grievance_service import GrievanceService
import backend.dependencies

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

        # 3. Start Telegram Bot in separate thread
        await run_in_threadpool(start_bot_thread)
        logger.info("Telegram bot started in separate thread.")
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
        await run_in_threadpool(Base.metadata.create_all, bind=engine)
        await run_in_threadpool(migrate_db)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # We continue to allow health checks even if DB has issues (for debugging)

    # Startup: Initialize Grievance Service (needed for escalation engine)
    try:
        grievance_service = GrievanceService()
        app.state.grievance_service = grievance_service
        logger.info("Grievance service initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing grievance service: {e}", exc_info=True)

    # Launch background tasks that are non-blocking for startup/health-check
    asyncio.create_task(background_initialization(app))
    
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
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]
    allowed_origins.extend(dev_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=500)

# Include Modular Routers
app.include_router(issues.router, tags=["Issues"])
app.include_router(detection.router, tags=["Detection"])
app.include_router(grievances.router, tags=["Grievances"])
app.include_router(utility.router, tags=["Utility"])

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
