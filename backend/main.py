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
from bot import run_bot
from pothole_detection import detect_potholes
from garbage_detection import detect_garbage
from hf_service import (
    detect_vandalism_clip,
    detect_flooding_clip,
    detect_infrastructure_clip,
    detect_stray_animal_clip,
    detect_fire_clip,
    detect_traffic_clip
)
from PIL import Image
from init_db import migrate_db
import logging
import asyncio

from backend.database import Base, engine
from backend.ai_factory import create_all_ai_services
from backend.ai_interfaces import initialize_ai_services
from backend.bot import start_bot_thread, stop_bot_thread
from backend.init_db import migrate_db
from backend.scheduler import start_scheduler
from backend.maharashtra_locator import load_maharashtra_pincode_data, load_maharashtra_mla_data
from backend.exceptions import EXCEPTION_HANDLERS
from backend.routers import issues, detection, grievances, utility, auth, admin, analysis, voice, field_officer
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
        await run_in_threadpool(migrate_db)
        logger.info("migrate_db completed. Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # We continue to allow health checks even if DB has issues (for debugging)

    # Startup: Initialize Grievance Service (needed for escalation engine)
    try:
        logger.info("Initializing grievance service...")
        grievance_service = GrievanceService()
        app.state.grievance_service = grievance_service
        logger.info("Grievance service initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing grievance service: {e}", exc_info=True)

    # Launch background tasks that are non-blocking for startup/health-check
    asyncio.create_task(background_initialization(app))
    
    # Start the daily civic intelligence refinement scheduler
    start_scheduler()

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

@app.get("/health")
def health():
    return {"status": "healthy"}

def save_file_blocking(file_obj, path):
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file_obj, buffer)

def save_issue_db(db: Session, issue: Issue):
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue

@app.post("/api/issues")
async def create_issue(
    description: str = Form(...),
    category: str = Form(...),
    user_email: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        # Save image if provided
        image_path = None
        if image:
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            # Generate unique filename
            filename = f"{uuid.uuid4()}_{image.filename}"
            image_path = os.path.join(upload_dir, filename)

            # Offload blocking file I/O to threadpool
            await run_in_threadpool(save_file_blocking, image.file, image_path)

        # Save to DB
        new_issue = Issue(
            description=description,
            category=category,
            image_path=image_path,
            source="web",
            user_email=user_email
        )

        # Offload blocking DB operations to threadpool
        await run_in_threadpool(save_issue_db, db, new_issue)

        # Generate Action Plan (AI)
        action_plan = await generate_action_plan(description, category, image_path)

        return {
            "id": new_issue.id,
            "message": "Issue reported successfully",
            "action_plan": action_plan
        }
    except Exception as e:
        logger.error(f"Error creating issue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/issues/{issue_id}/vote")
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

    return {"id": issue.id, "upvotes": issue.upvotes, "message": "Upvoted successfully"}

@lru_cache(maxsize=1)
def _load_responsibility_map():
    # Assuming the data folder is at the root level relative to where backend is run
    # Adjust path as necessary. If running from root, it is "data/responsibility_map.json"
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "responsibility_map.json")

    with open(file_path, "r") as f:
        return json.load(f)

@app.get("/api/responsibility-map")
def get_responsibility_map():
    # In a real app, this might read from the file or database
    # For MVP, we can return the structure directly or read the file
    try:
        return _load_responsibility_map()
    except FileNotFoundError:
        logger.error("Responsibility map file not found", exc_info=True)
        raise HTTPException(status_code=404, detail="Data file not found")
    except Exception as e:
        logger.error(f"Error loading responsibility map: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    response = await chat_with_civic_assistant(request.query)
    return {"response": response}

@app.get("/api/issues/recent")
def get_recent_issues(db: Session = Depends(get_db)):
    current_time = time.time()
    if RECENT_ISSUES_CACHE["data"] and (current_time - RECENT_ISSUES_CACHE["timestamp"] < RECENT_ISSUES_CACHE["ttl"]):
        return RECENT_ISSUES_CACHE["data"]

    # Fetch last 10 issues
    issues = db.query(Issue).order_by(Issue.created_at.desc()).limit(10).all()
    # Sanitize data (no emails)
    data = [
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

    RECENT_ISSUES_CACHE["data"] = data
    RECENT_ISSUES_CACHE["timestamp"] = current_time

    return data

@app.post("/api/detect-pothole")
async def detect_pothole_endpoint(image: UploadFile = File(...)):
    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
    except Exception as e:
        logger.error(f"Invalid image file for pothole detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (blocking, so run in threadpool)
    try:
        detections = await run_in_threadpool(detect_potholes, pil_image)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Pothole detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-infrastructure")
async def detect_infrastructure_endpoint(image: UploadFile = File(...)):
    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
    except Exception as e:
        logger.error(f"Invalid image file for infrastructure detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (async now, so no threadpool needed for the detection call itself)
    try:
        detections = await detect_infrastructure_clip(pil_image)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Infrastructure detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-flooding")
async def detect_flooding_endpoint(image: UploadFile = File(...)):
    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
    except Exception as e:
        logger.error(f"Invalid image file for flooding detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (async)
    try:
        detections = await detect_flooding_clip(pil_image)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Flooding detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-vandalism")
async def detect_vandalism_endpoint(image: UploadFile = File(...)):
    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
    except Exception as e:
        logger.error(f"Invalid image file for vandalism detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (async)
    try:
        detections = await detect_vandalism_clip(pil_image)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Vandalism detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-garbage")
async def detect_garbage_endpoint(image: UploadFile = File(...)):
    # Convert to PIL Image directly from file object to save memory
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
    except Exception as e:
        logger.error(f"Invalid image file for garbage detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (blocking, so run in threadpool)
    try:
        detections = await run_in_threadpool(detect_garbage, pil_image)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Garbage detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-stray-animal")
async def detect_stray_animal_endpoint(image: UploadFile = File(...)):
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
    except Exception as e:
        logger.error(f"Invalid image file for stray animal detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        detections = await detect_stray_animal_clip(pil_image)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Stray animal detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-fire")
async def detect_fire_endpoint(image: UploadFile = File(...)):
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
    except Exception as e:
        logger.error(f"Invalid image file for fire detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        detections = await detect_fire_clip(pil_image)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Fire detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/detect-traffic")
async def detect_traffic_endpoint(image: UploadFile = File(...)):
    try:
        pil_image = await run_in_threadpool(Image.open, image.file)
    except Exception as e:
        logger.error(f"Invalid image file for traffic detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        detections = await detect_traffic_clip(pil_image)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Traffic detection error: {e}", exc_info=True)
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
            description = await generate_mla_summary(
                district=constituency_info["district"],
                assembly_constituency=assembly_constituency,
                mla_name=mla_info["mla_name"]
            )
    except Exception as e:
        print(f"Error generating MLA summary: {e}")
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

# Note: Frontend serving code removed for separate deployment
# The frontend will be deployed on Netlify and make API calls to this backend
