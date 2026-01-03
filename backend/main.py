from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import engine, get_db
from models import Base, Issue
from ai_service import generate_action_plan, chat_with_civic_assistant
from maharashtra_locator import (
    find_constituency_by_pincode,
    find_mla_by_constituency,
    load_maharashtra_pincode_data,
    load_maharashtra_mla_data
)
from pydantic import BaseModel
from gemini_summary import generate_mla_summary
import json
import os
import shutil
from functools import lru_cache
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
import logging
import time

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Migrate DB
    migrate_db()

    # Startup: Load static data to avoid first-request latency
    try:
        # These functions use lru_cache, so calling them once loads the data into memory
        load_maharashtra_pincode_data()
        load_maharashtra_mla_data()
        print("Maharashtra data pre-loaded successfully.")
    except Exception as e:
        print(f"Error pre-loading Maharashtra data: {e}")

    # Startup: Start Telegram Bot in background (non-blocking)
    bot_task = None
    bot_app = None
    
    # Start bot initialization in background to avoid blocking port binding
    async def start_bot_background():
        nonlocal bot_app
        try:
            bot_app = await run_bot()
        except Exception as e:
            print(f"Error starting bot: {e}")
    
    # Create background task for bot initialization
    bot_task = asyncio.create_task(start_bot_background())
    
    yield
    
    # Shutdown: Stop Telegram Bot
    if bot_task and not bot_task.done():
        try:
            bot_task.cancel()
            await bot_task
        except asyncio.CancelledError:
            pass  # Expected when cancelling
        except Exception as e:
            print(f"Error cancelling bot task: {e}")
    
    if bot_app:
        try:
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
        except Exception as e:
            print(f"Error stopping bot: {e}")

app = FastAPI(title="VishwaGuru Backend", lifespan=lifespan)

# CORS Configuration
# For separate frontend/backend deployment (e.g., Netlify + Render)
# Set FRONTEND_URL environment variable to your Netlify URL
# Example: https://your-app.netlify.app
frontend_url = os.environ.get("FRONTEND_URL", "*")
allowed_origins = [frontend_url] if frontend_url != "*" else ["*"]

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=500)

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

        # Invalidate recent issues cache to ensure immediate feedback
        RECENT_ISSUES_CACHE["timestamp"] = 0

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

# Simple in-memory cache for recent issues
RECENT_ISSUES_CACHE = {"data": [], "timestamp": 0}
CACHE_TTL = 60  # seconds

@app.get("/api/issues/recent")
def get_recent_issues(db: Session = Depends(get_db)):
    now = time.time()

    # Check cache
    if now - RECENT_ISSUES_CACHE["timestamp"] < CACHE_TTL and RECENT_ISSUES_CACHE["data"]:
        return RECENT_ISSUES_CACHE["data"]

    # Fetch last 10 issues with optimized query (selecting only needed columns)
    issues = db.query(
        Issue.id,
        Issue.category,
        Issue.created_at,
        Issue.status,
        Issue.upvotes,
        Issue.image_path,
        func.substr(Issue.description, 1, 100).label('description')
    ).order_by(Issue.created_at.desc()).limit(10).all()

    # Sanitize data (no emails)
    result = [
        {
            "id": i.id,
            "category": i.category,
            "description": i.description + "..." if len(i.description) >= 100 else i.description,
            "created_at": i.created_at,
            "image_path": i.image_path,
            "status": i.status,
            "upvotes": i.upvotes if i.upvotes is not None else 0
        }
        for i in issues
    ]

    # Update cache
    RECENT_ISSUES_CACHE["data"] = result
    RECENT_ISSUES_CACHE["timestamp"] = now

    return result

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
