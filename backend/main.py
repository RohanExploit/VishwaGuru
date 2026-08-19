"""VishwaGuru API - FastAPI application entrypoint.

Import policy: every intra-project import uses the fully qualified `backend.`
package path. Mixing bare (`from models import ...`) and packaged
(`from backend.models import ...`) forms loaded the same module twice under two
names, which registered every SQLAlchemy table twice on one MetaData and made
`backend.main` raise InvalidRequestError at import time -- the app could not
start at all.
"""

import asyncio
import io
import json
import logging
import os
import shutil
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from functools import lru_cache
from typing import List, Optional

import httpx
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.ai_factory import create_all_ai_services
from backend.ai_interfaces import get_ai_services, initialize_ai_services
from backend.ai_service import (
    analyze_issue_with_ai,
    chat_with_civic_assistant,
    generate_action_plan,
)
from backend.bot import application  # Telegram Application
from backend.cache import recent_issues_cache
from backend.hf_api_service import (
    analyze_urgency_text,
    detect_blocked_road_clip,
    detect_civic_eye_clip,
    detect_depth_map,
    detect_fire_clip,
    detect_illegal_parking_clip,
    detect_pest_clip,
    detect_severity_clip,
    detect_smart_scan_clip,
    detect_stray_animal_clip,
    detect_street_light_clip,
    detect_tree_hazard_clip,
    detect_waste_clip,
    generate_image_caption,
    transcribe_audio,
    verify_resolution_vqa,
)
from backend.image_validator import validate_image_file
from backend.local_ml_service import detect_infrastructure_local
from backend.database import Base, SessionLocal, engine
from backend.flood_detection import detect_flooding
from backend.garbage_detection import detect_garbage
from backend.maharashtra_locator import (
    DISTRICT_RANGES,
    find_constituency_by_pincode,
    find_mla_by_constituency,
    load_maharashtra_mla_data,
    load_maharashtra_pincode_data,
)
from backend.models import Issue
from backend.pothole_detection import detect_potholes
from backend.responsibility_mapper import get_responsible_authority
from backend.schemas import (
    HealthResponse,
    MLStatusResponse,
    StatsResponse,
    SuccessResponse,
)
from backend.unified_detection_service import get_detection_status
from backend.vandalism_detection import detect_vandalism

logger = logging.getLogger(__name__)

# Create the database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Starting up backend...")

    # One shared httpx client for all outbound model calls. Opening a client
    # per request exhausts sockets under load and loses connection reuse.
    app.state.http_client = httpx.AsyncClient(timeout=30.0)

    # Initialize the AI service container. get_ai_services() raises
    # RuntimeError until this runs, which made /api/mh/rep-contacts fail.
    try:
        action_plan_service, chat_service, mla_summary_service = create_all_ai_services()
        initialize_ai_services(
            action_plan_service=action_plan_service,
            chat_service=chat_service,
            mla_summary_service=mla_summary_service,
        )
        logger.info("AI services initialized.")
    except Exception:
        logger.exception("Failed to initialize AI services")

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
    try:
        await app.state.http_client.aclose()
    except Exception:
        logger.exception("Error closing HTTP client")

    print("Shutting down backend...")
    try:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        print("Telegram bot stopped.")
    except Exception as e:
        print(f"Error stopping Telegram bot: {e}")

app = FastAPI(lifespan=lifespan)

# CORS.
#
# The previous configuration paired allow_origins=["*"] with
# allow_credentials=True. That combination is invalid per the Fetch spec --
# browsers reject a wildcard Access-Control-Allow-Origin on a credentialed
# request -- and it also ignored the CORS_ORIGINS variable that render.yaml
# already declares. Origins are now read from the environment, with a
# localhost-only default so a misconfigured deploy fails closed rather than
# open.
def _allowed_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    if frontend_url:
        return [frontend_url]
    return ["http://localhost:5173", "http://localhost:4173", "http://127.0.0.1:5173"]


ALLOWED_ORIGINS = _allowed_origins()
logger.info("CORS allowed origins: %s", ALLOWED_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
        filename = f"{uuid.uuid4()}_{os.path.basename(image.filename)}"
        file_location = f"data/uploads/{filename}"

        # Offload blocking file I/O to a thread
        await run_in_threadpool(save_file_blocking, image.file, file_location)

        # Generate Action Plan (AI)
        action_plan = await generate_action_plan(description, category, file_location)

        # Offload blocking DB operations to a thread
        def save_to_db():
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
            return db_issue

        new_issue = await asyncio.to_thread(save_to_db)

        return {
            "id": new_issue.id,
            "message": "Issue reported successfully",
            "action_plan": action_plan
        }
    except Exception as e:
        logger.exception("Error creating issue")
        return JSONResponse(status_code=500, content={"message": "An internal error occurred"})

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

@app.get("/api/issues")
def get_issues(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Added pagination
    issues = db.query(Issue).offset(skip).limit(limit).all()
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
async def api_detect_pothole(image: UploadFile = File(...)):
    try:
        def process_image():
            img = Image.open(image.file)
            return detect_potholes(img)
        result = await run_in_threadpool(process_image)
        return {"detections": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/detect-garbage")
async def api_detect_garbage(image: UploadFile = File(...)):
    try:
        def process_image():
            img = Image.open(image.file)
            return detect_garbage(img)
        result = await run_in_threadpool(process_image)
        return {"detections": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/detect-vandalism")
async def api_detect_vandalism(image: UploadFile = File(...)):
    try:
        if not os.getenv("HF_TOKEN") and not os.getenv("HUGGINGFACE_HUB_TOKEN"):
             print("Warning: HF_TOKEN not set.")
        def process_image():
            img = Image.open(image.file)
            return detect_vandalism(img)
        result = await run_in_threadpool(process_image)
        return {"detections": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/detect-flooding")
async def api_detect_flooding(image: UploadFile = File(...)):
    try:
        img = Image.open(image.file)
        result = await detect_flooding(img)
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

@app.post("/api/analyze-issue")
async def analyze_issue_endpoint(
    description: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    try:
        image_path = None
        if image:
            os.makedirs("data/temp", exist_ok=True)
            image_path = f"data/temp/{uuid.uuid4()}_{os.path.basename(image.filename)}"
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


# =============================================================================
# Detector endpoints
# =============================================================================
#
# Every service function called below already existed in
# backend/hf_api_service.py and backend/local_ml_service.py. None of them was
# ever routed, so the frontend called 15 endpoints that returned 404 in
# production. tests/test_api_contract.py now fails if that gap reopens.
#
# The handlers are generated from a table instead of being copy-pasted. The
# copy-paste approach is what produced four handlers that declared their upload
# field as `file` while every caller posted `image`.
#
# `service` is stored as a NAME and resolved from this module at request time,
# so tests that monkeypatch backend.main.<name> take effect.

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024


class UrgencyRequest(BaseModel):
    text: str


def _service(name: str):
    """Resolve a service function from this module at call time."""
    return getattr(sys.modules[__name__], name)


async def _read_upload(upload: UploadFile) -> bytes:
    """Read an upload, enforcing the configured size ceiling.

    MAX_UPLOAD_SIZE_MB was declared in render.yaml and parsed in config.py but
    was never actually enforced on any request path.
    """
    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit.",
        )
    return contents


async def validate_uploaded_file(upload: UploadFile) -> bytes:
    """Read and validate an uploaded image, returning its bytes."""
    contents = await _read_upload(upload)
    try:
        validate_image_file(contents)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}") from exc
    return contents


def _http_client(request: Request):
    return getattr(request.app.state, "http_client", None)


# (route path, service function name, wrap result as {"detections": ...})
DETECTOR_ENDPOINTS = [
    ("/api/detect-fire", "detect_fire_clip", True),
    ("/api/detect-illegal-parking", "detect_illegal_parking_clip", True),
    ("/api/detect-street-light", "detect_street_light_clip", True),
    ("/api/detect-stray-animal", "detect_stray_animal_clip", True),
    ("/api/detect-blocked-road", "detect_blocked_road_clip", True),
    ("/api/detect-tree-hazard", "detect_tree_hazard_clip", True),
    ("/api/detect-pest", "detect_pest_clip", True),
    ("/api/detect-severity", "detect_severity_clip", False),
    ("/api/detect-smart-scan", "detect_smart_scan_clip", False),
    ("/api/detect-waste", "detect_waste_clip", False),
    ("/api/detect-civic-eye", "detect_civic_eye_clip", False),
    ("/api/analyze-depth", "detect_depth_map", False),
]


def _make_detector_route(service_name: str, wrap: bool):
    async def endpoint(request: Request, image: UploadFile = File(...)):
        contents = await _read_upload(image)
        try:
            result = await _service(service_name)(contents, client=_http_client(request))
        except HTTPException:
            raise
        except Exception:
            logger.exception("%s failed", service_name)
            raise HTTPException(status_code=502, detail="Detection service unavailable.")
        return {"detections": result} if wrap else result

    endpoint.__name__ = f"{service_name}_endpoint"
    return endpoint


for _path, _service_name, _wrap in DETECTOR_ENDPOINTS:
    app.post(_path)(_make_detector_route(_service_name, _wrap))


@app.post("/api/detect-infrastructure")
async def detect_infrastructure_endpoint(image: UploadFile = File(...)):
    """Infrastructure damage runs through the local YOLO model, not CLIP."""
    contents = await _read_upload(image)
    try:
        pil_image = await run_in_threadpool(Image.open, io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file.") from exc

    try:
        detections = await detect_infrastructure_local(pil_image)
    except Exception:
        logger.exception("Infrastructure detection failed")
        raise HTTPException(status_code=502, detail="Detection service unavailable.")
    return {"detections": detections}


@app.post("/api/transcribe-audio")
async def transcribe_audio_endpoint(request: Request, file: UploadFile = File(...)):
    """The upload field is `file` here, matching the audio caller; image
    endpoints use `image`. transcribe_audio() returns a bare string, so it is
    wrapped rather than returned directly."""
    contents = await _read_upload(file)
    try:
        text = await transcribe_audio(contents, client=_http_client(request))
    except Exception:
        logger.exception("Audio transcription failed")
        raise HTTPException(status_code=502, detail="Transcription service unavailable.")
    return {"text": text}


@app.post("/api/generate-description")
async def generate_description_endpoint(request: Request, image: UploadFile = File(...)):
    contents = await _read_upload(image)
    try:
        caption = await generate_image_caption(contents, client=_http_client(request))
    except Exception:
        logger.exception("Caption generation failed")
        raise HTTPException(status_code=502, detail="Captioning service unavailable.")
    return {"description": caption}


@app.post("/api/analyze-urgency")
async def analyze_urgency_endpoint(request: Request, payload: UrgencyRequest):
    try:
        return await analyze_urgency_text(payload.text, client=_http_client(request))
    except Exception:
        logger.exception("Urgency analysis failed")
        raise HTTPException(status_code=502, detail="Urgency service unavailable.")


@app.get("/api/leaderboard")
def get_leaderboard(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Top reporters by number of issues filed, with their total upvotes."""
    rows = (
        db.query(
            Issue.user_email.label("user_email"),
            func.count(Issue.id).label("reports_count"),
            func.coalesce(func.sum(Issue.upvotes), 0).label("upvotes"),
        )
        .filter(Issue.user_email.isnot(None))
        .group_by(Issue.user_email)
        .order_by(func.count(Issue.id).desc(), func.sum(Issue.upvotes).desc())
        .limit(limit)
        .all()
    )
    return {
        "leaderboard": [
            {
                "rank": index,
                "user_email": row.user_email,
                "reports_count": int(row.reports_count or 0),
                "upvotes": int(row.upvotes or 0),
            }
            for index, row in enumerate(rows, start=1)
        ]
    }


@app.post("/api/issues/{issue_id}/verify")
async def verify_issue_resolution(
    issue_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Citizen uploads a photo; a VQA model judges whether the issue is fixed."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found.")

    contents = await validate_uploaded_file(image)

    question = f"Is this {issue.category or 'civic issue'} still present in the image?"
    try:
        answer = await verify_resolution_vqa(contents, question)
    except Exception:
        logger.exception("Resolution verification failed")
        raise HTTPException(status_code=502, detail="Verification service unavailable.")

    raw_answer = answer.get("answer") if isinstance(answer, dict) else answer
    ai_answer = str(raw_answer).strip().lower()
    is_resolved = ai_answer == "no"

    issue.status = "verified" if is_resolved else "open"
    db.commit()

    return {"is_resolved": is_resolved, "ai_answer": ai_answer, "issue_id": issue_id}
