from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base, Issue
from ai_service import generate_action_plan, chat_with_civic_assistant
from maharashtra_locator import find_constituency_by_pincode, find_mla_by_constituency
from pydantic import BaseModel
from gemini_summary import generate_mla_summary
import json
import os
import io

# Add the project root to sys.path so we can import 'backend' modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Issue
from contextlib import asynccontextmanager
import shutil
import datetime
from sqlalchemy import text
from typing import Optional, List
import PIL.Image
import uuid

# Import specialized detection modules
from pothole_detection import detect_potholes
from garbage_detection import detect_garbage
from vandalism_detection import detect_vandalism
from flood_detection import detect_flooding

# Import AI and Logic services
from ai_service import analyze_issue_image, chat_with_civic_assistant, analyze_issue_with_ai, generate_action_plan
from maharashtra_locator import get_district_by_pincode_range, find_constituency_by_pincode, find_mla_by_constituency, load_maharashtra_pincode_data, load_maharashtra_mla_data
from responsibility_mapper import get_responsible_authority
from bot import application  # Import the Telegram Application
from gemini_summary import generate_mla_summary

# Create the database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("Starting up backend...")

    # Initialize the Telegram bot
    try:
        await application.initialize()
        await application.updater.start_polling()
        await application.start()
        print("Telegram bot started.")
    except Exception as e:
        print(f"Error starting Telegram bot: {e}")

    # Preload data
    try:
        load_maharashtra_pincode_data()
        load_maharashtra_mla_data()
        logger.info("Maharashtra data pre-loaded successfully.")
    except Exception as e:
        logger.error(f"Error pre-loading Maharashtra data: {e}")

    # Run database migrations
    try:
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE INDEX ix_issues_created_at ON issues (created_at)"))
            except Exception: pass
            try:
                conn.execute(text("CREATE INDEX ix_issues_status ON issues (status)"))
            except Exception: pass
            try:
                conn.execute(text("ALTER TABLE issues ADD COLUMN upvotes INTEGER DEFAULT 0"))
            except Exception: pass
            try:
                conn.execute(text("ALTER TABLE issues ADD COLUMN user_email VARCHAR"))
            except Exception: pass
            conn.commit()
    except Exception as e:
        print(f"Migration warning: {e}")

    yield
    # --- Shutdown ---
    print("Shutting down backend...")
    try:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        print("Telegram bot stopped.")
    except Exception as e:
        print(f"Error stopping Telegram bot: {e}")

app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PincodeRequest(BaseModel):
    pincode: str

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "VishwaGuru API",
        "version": "1.0.0"
    }

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

@app.post("/api/issues")
async def create_issue(
    description: str = Form(...),
    category: str = Form(...),
    source: str = Form("web"),
    user_email: Optional[str] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Save the uploaded image
        os.makedirs("data/uploads", exist_ok=True)
        filename = f"{uuid.uuid4()}_{image.filename}"
        file_location = f"data/uploads/{filename}"

        # Write to disk in a threadpool to avoid blocking event loop
        await run_in_threadpool(save_file_blocking, image.file, file_location)

        # Analyze with AI
        ai_analysis = await analyze_issue_image(file_location)

        # Generate Action Plan (AI)
        action_plan = await generate_action_plan(description, category, file_location)

        db_issue = Issue(
            description=description,
            category=category,
            image_path=file_location,
            source=source,
            user_email=user_email
        )
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)

    return {
        "id": new_issue.id,
        "message": "Issue reported successfully",
        "action_plan": action_plan
    }

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
        return {"error": "Data file not found"}

class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    response = await chat_with_civic_assistant(request.query)
    return {"response": response}

@app.get("/api/issues/recent")
def get_recent_issues(db: Session = Depends(get_db)):
    # Fetch last 10 issues
    issues = db.query(Issue).order_by(Issue.created_at.desc()).limit(10).all()
    # Sanitize data (no emails)
    return [
        {
            "id": i.id,
            "category": i.category,
            "description": i.description[:100] + "..." if len(i.description) > 100 else i.description,
            "created_at": i.created_at,
            "image_path": i.image_path,
            "status": i.status
        }
        for i in issues
    ]

@app.post("/api/detect-pothole")
async def detect_pothole_endpoint(image: UploadFile = File(...)):
    # Read image
    contents = await image.read()
    # Convert to PIL Image
    try:
        pil_image = Image.open(io.BytesIO(contents))
    except Exception:
         raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (blocking, so run in threadpool)
    try:
        detections = await run_in_threadpool(detect_potholes, pil_image)
    except Exception as e:
        print(f"Error creating issue: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/api/issues")
def get_issues(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Added pagination
    issues = db.query(Issue).offset(skip).limit(limit).all()
    return issues

@app.get("/api/issues/recent")
def get_recent_issues(db: Session = Depends(get_db)):
    # Fetch top 10 most recent issues
    issues = db.query(Issue).order_by(Issue.created_at.desc()).limit(10).all()
    return issues

@app.post("/api/mh/rep-contacts")
async def get_rep_contacts_post(request: PincodeRequest):
    return await get_maharashtra_rep_contacts_logic(request.pincode)

@app.get("/api/mh/rep-contacts")
async def get_rep_contacts_get(pincode: str = Query(..., min_length=6, max_length=6)):
    return await get_maharashtra_rep_contacts_logic(pincode)

async def get_maharashtra_rep_contacts_logic(pincode: str):
    # Logic extracted to support both GET and POST
    if not pincode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pincode")
    
    constituency_info = find_constituency_by_pincode(pincode)
    
    if not constituency_info:
        # Fallback to just district check
         raise HTTPException(status_code=404, detail="Unknown pincode")

    assembly_constituency = constituency_info.get("assembly_constituency")
    mla_info = None

    if assembly_constituency:
        mla_info = find_mla_by_constituency(assembly_constituency)
    
    if not mla_info:
        mla_info = {
            "mla_name": "MLA Info Unavailable",
            "party": "N/A",
            "phone": "N/A",
            "email": "N/A",
            "twitter": "Not Available"
        }
        if not assembly_constituency:
             constituency_info["assembly_constituency"] = "Unknown (District Found)"
    
    description = None
    try:
        if assembly_constituency and mla_info["mla_name"] != "MLA Info Unavailable":
            ai_services = get_ai_services()
            description = await ai_services.mla_summary_service.generate_mla_summary(
                district=constituency_info["district"],
                assembly_constituency=assembly_constituency,
                mla_name=mla_info["mla_name"]
            )
    except Exception:
        pass
    
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
    
    if description:
        response["description"] = description
    elif mla_info["mla_name"] == "MLA Info Unavailable":
        response["description"] = f"We found that {pincode} belongs to {constituency_info['district']} district."

    return response

@app.get("/api/mh/districts")
async def get_districts():
    return {"districts": [d[2] for d in DISTRICT_RANGES]} if 'DISTRICT_RANGES' in globals() else {"districts": []}

@app.post("/api/detect-pothole")
async def api_detect_pothole(file: UploadFile = File(...)):
    try:
        def process_image():
            img = PIL.Image.open(file.file)
            return detect_potholes(img)
        result = await run_in_threadpool(process_image)
        return {"detections": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/detect-garbage")
async def api_detect_garbage(file: UploadFile = File(...)):
    try:
        def process_image():
            img = PIL.Image.open(file.file)
            return detect_garbage(img)
        result = await run_in_threadpool(process_image)
        return {"detections": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/detect-vandalism")
async def api_detect_vandalism(file: UploadFile = File(...)):
    try:
        if not os.getenv("HF_TOKEN") and not os.getenv("HUGGINGFACE_HUB_TOKEN"):
             print("Warning: HF_TOKEN not set.")
        def process_image():
            img = PIL.Image.open(file.file)
            return detect_vandalism(img)
        result = await run_in_threadpool(process_image)
        return {"detections": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/detect-flooding")
async def api_detect_flooding(file: UploadFile = File(...)):
    try:
        def process_image():
            img = PIL.Image.open(file.file)
            return detect_flooding(img)
        result = await run_in_threadpool(process_image)
        return {"detections": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = await chat_with_civic_assistant(request.message, request.history)
        return {"response": response}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/responsibility-map")
async def get_responsibility_map_endpoint():
    try:
        data = await run_in_threadpool(get_responsible_authority)
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/analyze-issue")
async def analyze_issue_endpoint(
    description: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    try:
        image_path = None
        if image:
            os.makedirs("data/temp", exist_ok=True)
            image_path = f"data/temp/{uuid.uuid4()}_{image.filename}"
            # save blocking
            await run_in_threadpool(save_file_blocking, image.file, image_path)

        result = await analyze_issue_with_ai(description, image_path)

        # Cleanup
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        return result
    except Exception as e:
        print(f"Analysis error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/issues/{issue_id}/upvote")
def upvote_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.upvotes is None:
        issue.upvotes = 0
    issue.upvotes += 1
    db.commit()
    db.refresh(issue)
    return {"status": "success", "upvotes": issue.upvotes}
