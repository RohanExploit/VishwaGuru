"""VishwaGuru API - FastAPI application entrypoint.

Import policy: every intra-project import uses the fully qualified `backend.`
package path. Mixing bare (`from models import ...`) and packaged
(`from backend.models import ...`) forms loaded the same module twice under two
names, which registered every SQLAlchemy table twice on one MetaData and made
`backend.main` raise InvalidRequestError at import time -- the app could not
start at all.
"""

import inspect
import io
import json
import logging
import os
import shutil
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from functools import lru_cache

import httpx
from fastapi import (
    BackgroundTasks,
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
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.ai_factory import create_all_ai_services
from backend.ai_interfaces import get_ai_services, initialize_ai_services
from backend.ai_service import (
    analyze_issue_with_ai,
    chat_with_civic_assistant,
    generate_action_plan,
)
from backend.auth import require_api_key
from backend.bot import (
    application,  # noqa: F401 - re-exported for callers
    start_bot_thread,
    stop_bot_thread,
)
from backend.cache import recent_issues_cache
from backend.database import Base, SessionLocal, engine
from backend.flood_detection import detect_flooding
from backend.garbage_detection import detect_garbage
from backend.hf_api_service import (
    analyze_urgency_text,
    detect_accessibility_issue_clip,
    detect_audio_event,
    detect_blocked_road_clip,
    detect_civic_eye_clip,
    detect_crowd_density_clip,
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
    detect_water_leak_clip,
    generate_image_caption,
    transcribe_audio,
    verify_resolution_vqa,
)
from backend.image_validator import (
    MAX_IMAGE_HEIGHT,
    MAX_IMAGE_WIDTH,
    validate_image_file,
)
from backend.local_ml_service import detect_infrastructure_local
from backend.maharashtra_locator import (
    DISTRICT_RANGES,
    find_constituency_by_pincode,
    find_mla_by_constituency,
    load_maharashtra_mla_data,
    load_maharashtra_pincode_data,
)
from backend.models import Issue
from backend.pothole_detection import detect_potholes
from backend.schemas import (
    HealthResponse,
    MLStatusResponse,
    StatsResponse,
    SuccessResponse,
)
from backend.spatial_utils import find_nearby_issues
from backend.unified_detection_service import (
    detect_infrastructure as detect_infrastructure_unified,
)
from backend.unified_detection_service import (
    detect_vandalism as detect_vandalism_unified,
)
from backend.unified_detection_service import (
    get_detection_status,
)
from backend.vandalism_detection import detect_vandalism

logger = logging.getLogger(__name__)

# Only the process with this set runs the Telegram poller; see the lifespan.
RUN_TELEGRAM_BOT = os.getenv("RUN_TELEGRAM_BOT", "").lower() in {"1", "true", "yes"}

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

    # Telegram bot.
    #
    # Polling used to run inside this lifespan, which meant every uvicorn worker
    # opened its own long-poll against Telegram. Telegram rejects the extras
    # with HTTP 409, so the API could never be scaled past a single worker.
    #
    # The poller now runs on its own thread and only in the process that opts in
    # via RUN_TELEGRAM_BOT. Run the web service with it unset and one dedicated
    # worker with it set, and the API scales horizontally.
    if RUN_TELEGRAM_BOT:
        if start_bot_thread() is None:
            logger.warning(
                "RUN_TELEGRAM_BOT is set but the bot did not start; "
                "TELEGRAM_BOT_TOKEN is probably missing."
            )
    else:
        logger.info("RUN_TELEGRAM_BOT is not set; this process serves the API only.")

    # Preload data
    try:
        load_maharashtra_pincode_data()
        load_maharashtra_mla_data()
        logger.info("Maharashtra data pre-loaded successfully.")
    except Exception as e:
        logger.error(f"Error pre-loading Maharashtra data: {e}")

    # Schema migrations are NOT run here.
    #
    # This block used to execute raw ALTER/CREATE INDEX statements on every
    # startup, tolerating each failure individually because the column or index
    # usually already existed. That has no ordering, no down path, and no record
    # of which revision a database is on, and with more than one worker every
    # process raced to apply it.
    #
    # Alembic owns the schema now. Migrations run once per deploy, before the
    # service starts -- see preDeployCommand in render.yaml -- so a worker that
    # boots can assume the schema is already correct:
    #
    #     alembic upgrade head

    yield

    # --- Shutdown ---
    try:
        await app.state.http_client.aclose()
    except Exception:
        logger.exception("Error closing HTTP client")

    logger.info("Shutting down backend...")
    if RUN_TELEGRAM_BOT:
        try:
            await run_in_threadpool(stop_bot_thread)
        except Exception:
            logger.exception("Error stopping the Telegram bot thread")


# Rate limiting.
#
# RATE_LIMIT_ENABLED and MAX_REQUESTS_PER_MINUTE were declared in render.yaml
# and parsed in config.py, but nothing ever enforced them, so every endpoint was
# unmetered. That matters here beyond the usual denial-of-service concern: the
# detector and chat endpoints call paid inference APIs on every request, so an
# unmetered endpoint is a billing exposure as much as an availability one.
#
# AI-backed routes get a tighter bucket than plain reads. Storage is in-process,
# which is correct for a single service instance; a multi-instance deployment
# needs a shared backend (RATE_LIMIT_STORAGE_URI, e.g. redis://...).
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
AI_REQUESTS_PER_MINUTE = int(os.getenv("AI_REQUESTS_PER_MINUTE", "12"))
RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")

DEFAULT_RATE_LIMIT = f"{MAX_REQUESTS_PER_MINUTE}/minute"
AI_RATE_LIMIT = f"{AI_REQUESTS_PER_MINUTE}/minute"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_RATE_LIMIT] if RATE_LIMIT_ENABLED else [],
    storage_uri=RATE_LIMIT_STORAGE_URI,
    enabled=RATE_LIMIT_ENABLED,
)

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
logger.info(
    "Rate limiting %s (default %s, AI %s)",
    "enabled" if RATE_LIMIT_ENABLED else "disabled",
    DEFAULT_RATE_LIMIT,
    AI_RATE_LIMIT,
)

# CORS.
#
# The previous configuration paired allow_origins=["*"] with
# allow_credentials=True. That combination is invalid per the Fetch spec --
# browsers reject a wildcard Access-Control-Allow-Origin on a credentialed
# request -- and it also ignored the CORS_ORIGINS variable that render.yaml
# already declares. Origins are now read from the environment, with a
# localhost-only default so a misconfigured deploy fails closed rather than
# open.
# A Capacitor WebView does not serve the app from the site's domain: on Android
# it is https://localhost, on iOS capacitor://localhost. Those origins will
# never appear in a CORS_ORIGINS value written for the web deployment, so
# without them every request from the packaged app is blocked by the WebView's
# CORS check even when the URL is correct. They are appended to whatever the
# environment configures rather than replacing it.
MOBILE_APP_ORIGINS = [
    "https://localhost",
    "capacitor://localhost",
    "ionic://localhost",
]

LOCAL_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
]


def _allowed_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        configured = [o.strip() for o in raw.split(",") if o.strip()]
    else:
        frontend_url = os.getenv("FRONTEND_URL", "").strip()
        configured = [frontend_url] if frontend_url else list(LOCAL_DEV_ORIGINS)

    seen: set[str] = set()
    origins: list[str] = []
    for origin in [*configured, *MOBILE_APP_ORIGINS]:
        if origin not in seen:
            seen.add(origin)
            origins.append(origin)
    return origins


ALLOWED_ORIGINS = _allowed_origins()
logger.info("CORS allowed origins: %s", ALLOWED_ORIGINS)

# The grievance/escalation service layer existed but was never mounted, so
# every path frontend/src/api/grievances.js calls returned 404.
from backend.grievance_routes import router as grievance_router  # noqa: E402

app.include_router(grievance_router)

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
    history: list[dict] = []


@app.get("/", response_model=SuccessResponse)
def root():
    return SuccessResponse(
        message="VishwaGuru API is running", data={"service": "VishwaGuru API", "version": "1.0.0"}
    )


@app.get("/health", response_model=HealthResponse)
@limiter.exempt
def health():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
        version="1.0.0",
        services={"database": "connected", "ai_services": "initialized"},
    )


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    cached_stats = recent_issues_cache.get("stats")
    if cached_stats:
        return JSONResponse(content=cached_stats)

    total = db.query(func.count(Issue.id)).scalar()
    resolved = (
        db.query(func.count(Issue.id)).filter(Issue.status.in_(["resolved", "verified"])).scalar()
    )
    # Pending is everything else
    pending = total - resolved

    # By category
    cat_counts = db.query(Issue.category, func.count(Issue.id)).group_by(Issue.category).all()
    issues_by_category = dict(cat_counts)

    response = StatsResponse(
        total_issues=total,
        resolved_issues=resolved,
        pending_issues=pending,
        issues_by_category=issues_by_category,
    )

    data = response.model_dump(mode="json")
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
        memory_usage=status.get("memory_usage"),
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


def save_issue_db(db: Session, issue: Issue) -> Issue:
    """Persist an issue. Named at module level so it can be run in a threadpool
    and identified by callers that need to distinguish the two blocking steps."""
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


def _coerce_action_plan(value):
    """Action plans are stored as JSON text but handled as dicts in memory."""
    if value is None or isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _serialise_issue_for_cache(issue: Issue) -> dict:
    return {
        "id": issue.id,
        "category": issue.category,
        "description": issue.description,
        "created_at": issue.created_at,
        "image_path": issue.image_path,
        "status": issue.status,
        "upvotes": issue.upvotes,
        "location": issue.location,
        "latitude": issue.latitude,
        "longitude": issue.longitude,
        "action_plan": _coerce_action_plan(issue.action_plan),
    }


def _update_recent_cache(issue: Issue) -> None:
    """Prepend the new issue to the cached recent list instead of dropping it.

    Invalidating forced the next reader to re-query, which is wasteful when the
    only change is one row at the head of a list already in memory. The cache is
    only invalidated when there is nothing to update.
    """
    try:
        cached = recent_issues_cache.get(RECENT_ISSUES_CACHE_KEY)
        if not cached:
            recent_issues_cache.invalidate(RECENT_ISSUES_CACHE_KEY)
            return
        updated = [_serialise_issue_for_cache(issue), *cached][:RECENT_ISSUES_LIMIT]
        recent_issues_cache.set(updated, RECENT_ISSUES_CACHE_KEY)
    except Exception:
        logger.exception("Failed to update the recent-issues cache")
        recent_issues_cache.invalidate(RECENT_ISSUES_CACHE_KEY)


async def _generate_action_plan_task(issue_id: int, description: str, category: str) -> None:
    """Produce the action plan after the response has been sent.

    Generating it inline held the request open for the full duration of the
    model call, so submitting a report appeared to hang. The client polls
    /api/issues/recent, which now carries action_plan, until it is populated.
    """
    try:
        plan = await generate_action_plan(description, category)
    except Exception:
        logger.exception("Background action plan generation failed for issue %s", issue_id)
        return

    session = SessionLocal()
    try:
        issue = session.query(Issue).filter(Issue.id == issue_id).first()
        if issue is None:
            logger.warning("Issue %s vanished before its action plan was stored", issue_id)
            return
        issue.action_plan = plan
        session.commit()
        logger.info("Stored action plan for issue %s", issue_id)
    except Exception:
        logger.exception("Failed to store action plan for issue %s", issue_id)
        session.rollback()
    finally:
        session.close()


def _find_nearby(db: Session, latitude: float, longitude: float, radius_meters: float):
    """Candidate issues near a point, nearest first."""
    candidates = (
        db.query(Issue).filter(Issue.latitude.isnot(None), Issue.longitude.isnot(None)).all()
    )
    matches = find_nearby_issues(candidates, latitude, longitude, radius_meters)
    return sorted(matches, key=lambda pair: pair[1])


@app.get("/api/issues/nearby")
def get_nearby_issues(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(50.0, gt=0, le=50000, description="Search radius in metres"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Issues within `radius` metres of a point, sorted by distance.

    The frontend's duplicate check called this and got a 404: backend/spatial_utils.py
    implemented the geometry but nothing ever exposed it.
    """
    matches = _find_nearby(db, latitude, longitude, radius)[:limit]
    return [
        {
            "id": issue.id,
            "category": issue.category,
            "description": issue.description,
            "status": issue.status,
            "upvotes": issue.upvotes,
            "latitude": issue.latitude,
            "longitude": issue.longitude,
            "created_at": issue.created_at,
            "distance_meters": round(distance, 2),
        }
        for issue, distance in matches
    ]


@app.post("/api/issues", status_code=201)
async def create_issue(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    category: str = Form(...),
    source: str = Form("web"),
    user_email: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    location: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Record a civic issue.

    Returns 201 with `action_plan` null. The plan is generated in the
    background and collected by polling /api/issues/recent, because the model
    call took long enough that submitting a report looked like a hang.
    """
    file_location = None
    if image is not None and image.filename:
        await validate_uploaded_file(image)
        await image.seek(0)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid.uuid4()}_{os.path.basename(image.filename)}"
        file_location = os.path.join(UPLOAD_DIR, filename)
        await run_in_threadpool(save_file_blocking, image.file, file_location)

    deduplication_info = {"has_nearby_issues": False, "nearby_issues": []}
    linked_issue_id = None

    if latitude is not None and longitude is not None:
        try:
            nearby = _find_nearby(db, latitude, longitude, DEDUPLICATION_RADIUS_METERS)
        except Exception:
            logger.exception("Nearby-issue lookup failed during issue creation")
            nearby = []

        if nearby:
            deduplication_info = {
                "has_nearby_issues": True,
                "nearby_issues": [
                    {
                        "id": existing.id,
                        "category": existing.category,
                        "description": existing.description,
                        "distance_meters": round(distance, 2),
                    }
                    for existing, distance in nearby[:5]
                ],
            }
            linked_issue_id = nearby[0][0].id

    new_issue = Issue(
        description=description,
        category=category,
        image_path=file_location,
        source=source,
        user_email=user_email,
        latitude=latitude,
        longitude=longitude,
        location=location,
    )

    try:
        saved = await run_in_threadpool(save_issue_db, db, new_issue)
    except Exception as exc:
        logger.exception("Error creating issue")
        raise HTTPException(status_code=500, detail="Could not record the issue.") from exc

    if saved is None:
        saved = new_issue

    _update_recent_cache(saved)

    background_tasks.add_task(_generate_action_plan_task, saved.id, description, category)

    return {
        "id": saved.id,
        "message": "Issue reported successfully",
        "action_plan": None,
        "deduplication_info": deduplication_info,
        "linked_issue_id": linked_issue_id,
    }


@lru_cache(maxsize=1)
def _load_responsibility_map():
    # Assuming the data folder is at the root level relative to where backend is run
    # Adjust path as necessary. If running from root, it is "data/responsibility_map.json"
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "responsibility_map.json"
    )

    with open(file_path) as f:
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
            "description": i.description[:100] + "..."
            if len(i.description) > 100
            else i.description,
            "created_at": i.created_at,
            "image_path": i.image_path,
            "status": i.status,
            "upvotes": i.upvotes,
            # ActionView.jsx polls this endpoint for the backgrounded action
            # plan; without this field the poll could never terminate.
            "action_plan": _coerce_action_plan(i.action_plan),
        }
        for i in issues
    ]


@app.get("/api/issues")
def get_issues(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
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
            "twitter": "Not Available",
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
                mla_name=mla_info["mla_name"],
            )
    except Exception:
        # The AI-written summary is optional garnish on the representative
        # lookup; the contact details below are the answer. A failure here was
        # silently discarded, so an outage in the summary service looked like
        # the feature simply not having a description.
        logger.warning("MLA summary generation failed", exc_info=True)

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
            "twitter": mla_info.get("twitter"),
        },
        "grievance_links": {
            "central_cpgrams": "https://pgportal.gov.in/",
            "maharashtra_portal": "https://aaplesarkar.mahaonline.gov.in/en",
            "note": "This is an MVP; data may not be fully accurate.",
        },
    }

    if description:
        response["description"] = description
    elif mla_info["mla_name"] == "MLA Info Unavailable":
        response["description"] = (
            f"We found that {pincode} belongs to {constituency_info['district']} district."
        )

    return response


@app.get("/api/mh/districts")
async def get_districts():
    return (
        {"districts": [d[2] for d in DISTRICT_RANGES]}
        if "DISTRICT_RANGES" in globals()
        else {"districts": []}
    )


# The four original detector handlers, rewritten to share one code path.
#
# They had three defects between them. detect_vandalism and detect_flooding are
# coroutine functions, but the vandalism handler called detect_vandalism inside
# a sync function handed to run_in_threadpool, so it produced an un-awaited
# coroutine that failed serialisation with a 500 on every request. The flooding
# handler awaited correctly but opened the image on the event loop. And none of
# the four enforced MAX_UPLOAD_SIZE_MB, so a phone photo above the limit was
# accepted here while the generated endpoints correctly rejected it.
#
# Detector callables are resolved through _service() so monkeypatching
# backend.main.<name> in tests still works, and both sync and async
# implementations are supported.


async def _run_image_detector(service_name: str, upload: UploadFile) -> dict:
    contents = await _read_upload(upload)
    try:
        pil_image = await run_in_threadpool(Image.open, io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file.") from exc

    validate_image_for_processing(pil_image)

    detector = _service(service_name)
    try:
        result = detector(pil_image)
        if inspect.isawaitable(result):
            result = await result
        elif callable(getattr(result, "__await__", None)):  # pragma: no cover
            result = await result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("%s failed", service_name)
        raise HTTPException(status_code=502, detail="Detection service unavailable.") from exc
    return {"detections": result}


@app.post("/api/detect-pothole")
@limiter.limit(AI_RATE_LIMIT)
async def api_detect_pothole(request: Request, image: UploadFile = File(...)):
    return await _run_image_detector("detect_potholes", image)


@app.post("/api/detect-garbage")
@limiter.limit(AI_RATE_LIMIT)
async def api_detect_garbage(request: Request, image: UploadFile = File(...)):
    return await _run_image_detector("detect_garbage", image)


@app.post("/api/detect-vandalism")
@limiter.limit(AI_RATE_LIMIT)
async def api_detect_vandalism(request: Request, image: UploadFile = File(...)):
    return await _run_image_detector("detect_vandalism_unified", image)


@app.post("/api/detect-flooding")
@limiter.limit(AI_RATE_LIMIT)
async def api_detect_flooding(request: Request, image: UploadFile = File(...)):
    return await _run_image_detector("detect_flooding", image)


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = await chat_with_civic_assistant(request.message, request.history)
        return {"response": response}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/analyze-issue")
async def analyze_issue_endpoint(
    description: str = Form(...), image: UploadFile | None = File(None)
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
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join("data", "uploads"))
RECENT_ISSUES_CACHE_KEY = "recent"
RECENT_ISSUES_LIMIT = 10
# Reports closer than this to an existing one are flagged as possible duplicates.
DEDUPLICATION_RADIUS_METERS = 50.0


class UrgencyRequest(BaseModel):
    """frontend/src/views/ReportForm.jsx posts {"description": ...}.

    This model originally declared a single required `text` field, so every
    request from the report form was rejected with 422 and the urgency panel
    silently never populated -- ReportForm's catch only console.errors.
    `text` is kept as an accepted alias.
    """

    description: str | None = None
    text: str | None = None

    @property
    def content(self) -> str:
        value = self.description or self.text
        if not value or not value.strip():
            raise HTTPException(
                status_code=422,
                detail="Provide a non-empty 'description' (or 'text').",
            )
        return value


# Detector implementations are dispatched by name through _service() so that
# tests can monkeypatch backend.main.<name>. Listing them here makes that
# indirection explicit: without it the imports read as dead to both linters and
# reviewers, and deleting one would break a route with nothing to catch it.
DETECTOR_IMPLEMENTATIONS = (
    detect_potholes,
    detect_garbage,
    detect_vandalism,
    detect_vandalism_unified,
    detect_flooding,
    detect_infrastructure_local,
    detect_infrastructure_unified,
    detect_accessibility_issue_clip,
    detect_audio_event,
    detect_blocked_road_clip,
    detect_civic_eye_clip,
    detect_crowd_density_clip,
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
    detect_water_leak_clip,
    generate_image_caption,
    transcribe_audio,
    verify_resolution_vqa,
    analyze_urgency_text,
)


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


def validate_image_for_processing(image: "Image.Image") -> None:
    """Validate a decoded image before it is handed to a detector.

    validate_uploaded_file() checks the bytes; this checks the decoded result,
    where a small payload can still expand to dimensions large enough to
    exhaust memory during inference.
    """
    width, height = image.size
    if width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Image has no pixels.")
    if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
        raise HTTPException(
            status_code=413,
            detail=f"Image dimensions {width}x{height} exceed the "
            f"{MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT} limit.",
        )


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
    ("/api/detect-accessibility", "detect_accessibility_issue_clip", True),
    ("/api/detect-crowd", "detect_crowd_density_clip", True),
    ("/api/detect-water-leak", "detect_water_leak_clip", True),
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
        except Exception as exc:
            logger.exception("%s failed", service_name)
            raise HTTPException(status_code=502, detail="Detection service unavailable.") from exc
        return {"detections": result} if wrap else result

    endpoint.__name__ = f"{service_name}_endpoint"
    return endpoint


for _path, _service_name, _wrap in DETECTOR_ENDPOINTS:
    # Each of these calls a paid inference API, so they use the tighter bucket.
    app.post(_path)(limiter.limit(AI_RATE_LIMIT)(_make_detector_route(_service_name, _wrap)))


@app.post("/api/detect-infrastructure")
@limiter.limit(AI_RATE_LIMIT)
async def detect_infrastructure_endpoint(request: Request, image: UploadFile = File(...)):
    """Infrastructure damage goes through the unified service.

    This used to call detect_infrastructure_local directly, so a deployment
    without the local model had no path to the hosted API at all.
    """
    return await _run_image_detector("detect_infrastructure_unified", image)


@app.post("/api/transcribe-audio")
@limiter.limit(AI_RATE_LIMIT)
async def transcribe_audio_endpoint(request: Request, file: UploadFile = File(...)):
    """The upload field is `file` here, matching the audio caller; image
    endpoints use `image`. transcribe_audio() returns a bare string, so it is
    wrapped rather than returned directly."""
    contents = await _read_upload(file)
    try:
        text = await transcribe_audio(contents, client=_http_client(request))
    except Exception as exc:
        logger.exception("Audio transcription failed")
        raise HTTPException(status_code=502, detail="Transcription service unavailable.") from exc
    return {"text": text}


@app.post("/api/detect-audio")
@limiter.limit(AI_RATE_LIMIT)
async def detect_audio_endpoint(request: Request, file: UploadFile = File(...)):
    """Noise classification. NoiseDetector.jsx posts the recording as `file`
    and reads `data.detections`."""
    contents = await _read_upload(file)
    try:
        detections = await detect_audio_event(contents, client=_http_client(request))
    except Exception as exc:
        logger.exception("Audio event detection failed")
        raise HTTPException(status_code=502, detail="Audio detection service unavailable.") from exc
    return {"detections": detections}


@app.post("/api/generate-description")
@limiter.limit(AI_RATE_LIMIT)
async def generate_description_endpoint(request: Request, image: UploadFile = File(...)):
    contents = await _read_upload(image)
    try:
        caption = await generate_image_caption(contents, client=_http_client(request))
    except Exception as exc:
        logger.exception("Caption generation failed")
        raise HTTPException(status_code=502, detail="Captioning service unavailable.") from exc
    return {"description": caption}


@app.post("/api/analyze-urgency")
@limiter.limit(AI_RATE_LIMIT)
async def analyze_urgency_endpoint(request: Request, payload: UrgencyRequest):
    try:
        return await analyze_urgency_text(payload.content, client=_http_client(request))
    except Exception as exc:
        logger.exception("Urgency analysis failed")
        raise HTTPException(status_code=502, detail="Urgency service unavailable.") from exc


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
@limiter.limit(AI_RATE_LIMIT)
async def verify_issue_resolution(
    request: Request,
    issue_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _api_key: str = Depends(require_api_key),
):
    """Citizen uploads a photo; a VQA model judges whether the issue is fixed.

    Requires X-API-Key: this writes issue.status, which is what officials and
    the public dashboard treat as the record of whether a problem was fixed.

    The response carries `confidence` and `question_asked` because
    frontend/src/views/VerifyView.jsx renders both directly -- it computes
    `(result.confidence * 100).toFixed(1)`, which shows "NaN%" if the field is
    absent, and interpolates `result.question_asked` into its summary line.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found.")

    contents = await validate_uploaded_file(image)

    question = f"Is this {issue.category or 'civic issue'} still present in the image?"
    try:
        answer = await verify_resolution_vqa(contents, question, client=_http_client(request))
    except Exception as exc:
        logger.exception("Resolution verification failed")
        raise HTTPException(status_code=502, detail="Verification service unavailable.") from exc

    if isinstance(answer, dict):
        raw_answer = answer.get("answer")
        confidence = answer.get("confidence", 0)
    else:
        raw_answer = answer
        confidence = 0

    ai_answer = str(raw_answer).strip().lower()
    is_resolved = ai_answer == "no"

    issue.status = "verified" if is_resolved else "open"
    db.commit()

    return {
        "issue_id": issue_id,
        "is_resolved": is_resolved,
        "ai_answer": ai_answer,
        "confidence": float(confidence or 0),
        "question_asked": question,
    }
