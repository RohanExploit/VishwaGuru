import sys
import os
import shutil
from functools import lru_cache
from async_lru import alru_cache
import uuid
import asyncio
from fastapi import Depends
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
            "status": "success",
            "issue_id": db_issue.id,
            "message": "Issue reported successfully",
            "ai_analysis": ai_analysis,
            "action_plan": action_plan
        }
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

@alru_cache(maxsize=100)
async def _get_maharashtra_rep_contacts_cached(pincode: str):
    """
    Cached logic for getting MLA contacts.
    Separated from the endpoint to allow caching.
    """
    # Find constituency by pincode
    constituency_info = find_constituency_by_pincode(pincode)
    
    if not constituency_info:
        return None
    
    # Find MLA by constituency
    # If constituency_info exists but assembly_constituency is None, it means we only found District info via fallback
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

    result = await _get_maharashtra_rep_contacts_cached(pincode)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Unknown pincode for Maharashtra MVP. Currently only supporting limited pincodes."
        )

    return result

# Note: Frontend serving code removed for separate deployment
# The frontend will be deployed on Netlify and make API calls to this backend
