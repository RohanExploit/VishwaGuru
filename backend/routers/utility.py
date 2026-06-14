from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
import logging

from backend.database import get_db
from backend.models import Issue
from backend.schemas import (
    SuccessResponse, HealthResponse, StatsResponse, MLStatusResponse,
    ChatRequest, ChatResponse, LeaderboardResponse, LeaderboardEntry
)
from backend.cache import recent_issues_cache
from backend.unified_detection_service import get_detection_status
from backend.ai_service import chat_with_civic_assistant
from backend.gemini_services import get_ai_services
from backend.maharashtra_locator import (
    find_constituency_by_pincode,
    find_mla_by_constituency,
    find_mla_by_constituency
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=SuccessResponse)
def root():
    return SuccessResponse(
        message="VishwaGuru API is running",
        data={
            "service": "VishwaGuru API",
            "version": "1.0.0"
        }
    )

@router.get("/health", response_model=HealthResponse)
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

@router.get("/api/stats", response_model=StatsResponse)
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

@router.get("/api/ml-status", response_model=MLStatusResponse)
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

@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response = await chat_with_civic_assistant(request.query)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat service error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable")

@router.get("/api/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(db: Session = Depends(get_db)):
    """Get top reporters leaderboard (cached)"""
    cache_key = "leaderboard"
    cached_data = recent_issues_cache.get(cache_key)
    if cached_data:
        return JSONResponse(content=cached_data)

    # Group by user_email, count issues, sum upvotes
    # Optimization: Only select needed columns and use aggregation
    results = db.query(
        Issue.user_email,
        func.count(Issue.id).label('count'),
        func.sum(Issue.upvotes).label('total_upvotes')
    ).filter(
        Issue.user_email.isnot(None),
        Issue.user_email != ""
    ).group_by(Issue.user_email).order_by(func.count(Issue.id).desc()).limit(10).all()

    leaderboard_data = []
    for idx, (email, count, upvotes) in enumerate(results):
        # Mask email for privacy
        try:
            if '@' in email:
                name, domain = email.split('@')
                masked_email = f"{name[0]}***@{domain}"
            else:
                masked_email = email[:3] + "***"
        except Exception:
            masked_email = "User***"

        leaderboard_data.append(LeaderboardEntry(
            user_email=masked_email,
            reports_count=count,
            total_upvotes=upvotes or 0,
            rank=idx + 1
        ).model_dump(mode='json'))

    response_data = {"leaderboard": leaderboard_data}
    # Cache for 5 minutes to reduce DB load on frequent hits
    recent_issues_cache.set(response_data, cache_key)

    return response_data


@router.get("/api/mh/rep-contacts")
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
