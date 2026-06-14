from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session, defer
from sqlalchemy import func
from typing import List, Union, Dict, Any
import uuid
import os
import logging
import hashlib
from datetime import datetime, timezone

from backend.database import get_db
from backend.models import Issue, PushSubscription
from backend.schemas import (
    IssueCreateWithDeduplicationResponse, IssueCategory, NearbyIssueResponse,
    DeduplicationCheckResponse, IssueSummaryResponse, VoteResponse,
    IssueStatusUpdateRequest, IssueStatusUpdateResponse, PushSubscriptionRequest,
    PushSubscriptionResponse, BlockchainVerificationResponse
)
from backend.utils import (
    check_upload_limits, validate_uploaded_file, save_file_blocking, save_issue_db,
    process_uploaded_image, save_processed_image,
    UPLOAD_LIMIT_PER_USER, UPLOAD_LIMIT_PER_IP
)
from backend.tasks import (
    process_action_plan_background, create_grievance_from_issue_background,
    send_status_notification
)
from backend.spatial_utils import get_bounding_box, find_nearby_issues
from backend.cache import recent_issues_cache, nearby_issues_cache
from backend.hf_api_service import verify_resolution_vqa
from backend.dependencies import get_http_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/issues", response_model=IssueCreateWithDeduplicationResponse, status_code=201)
async def create_issue(
    request: Request,
    background_tasks: BackgroundTasks,
    description: str = Form(..., min_length=10, max_length=1000),
    category: str = Form(..., pattern=f"^({'|'.join([cat.value for cat in IssueCategory])})$"),
    language: str = Form('en'),
    user_email: str = Form(None),
    latitude: float = Form(None, ge=-90, le=90),
    longitude: float = Form(None, ge=-180, le=180),
    location: str = Form(None, max_length=200),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_path = None

    # Check upload limits if image is being uploaded
    if image:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        # Use user_email if provided, otherwise IP
        identifier = user_email if user_email else client_ip
        limit = UPLOAD_LIMIT_PER_USER if user_email else UPLOAD_LIMIT_PER_IP
        check_upload_limits(identifier, limit)

    try:
        # Save image if provided (optimized single pass)
        if image:
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{uuid.uuid4()}_{image.filename}"
            image_path = os.path.join(upload_dir, filename)

            # Process image (validate, resize, strip EXIF)
            # Unpack the tuple: (PIL.Image, image_bytes)
            _, image_bytes = await process_uploaded_image(image)

            # Save processed image to disk
            await run_in_threadpool(save_processed_image, image_bytes, image_path)
    except HTTPException:
        # Re-raise HTTP exceptions (from validation)
        raise
    except OSError as e:
        logger.error(f"File I/O error while saving image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    except Exception as e:
        logger.error(f"Unexpected error during file processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    # Spatial deduplication check
    deduplication_info = None
    linked_issue_id = None

    if latitude is not None and longitude is not None:
        try:
            # Find existing open issues within 50 meters
            # Optimization: Use bounding box to filter candidates in SQL
            min_lat, max_lat, min_lon, max_lon = get_bounding_box(latitude, longitude, 50.0)

            # Performance Boost: Use column projection to avoid loading full model instances
            open_issues = await run_in_threadpool(
                lambda: db.query(
                    Issue.id,
                    Issue.description,
                    Issue.category,
                    Issue.latitude,
                    Issue.longitude,
                    Issue.upvotes,
                    Issue.created_at,
                    Issue.status
                ).filter(
                    Issue.status == "open",
                    Issue.latitude >= min_lat,
                    Issue.latitude <= max_lat,
                    Issue.longitude >= min_lon,
                    Issue.longitude <= max_lon
                ).all()
            )

            nearby_issues_with_distance = find_nearby_issues(
                open_issues, latitude, longitude, radius_meters=50.0
            )

            if nearby_issues_with_distance:
                # Found nearby issues - prepare deduplication response
                nearby_responses = [
                    NearbyIssueResponse(
                        id=issue.id,
                        description=issue.description[:100] + "..." if len(issue.description) > 100 else issue.description,
                        category=issue.category,
                        latitude=issue.latitude,
                        longitude=issue.longitude,
                        distance_meters=distance,
                        upvotes=issue.upvotes or 0,
                        created_at=issue.created_at,
                        status=issue.status
                    )
                    for issue, distance in nearby_issues_with_distance[:3]  # Limit to top 3 closest
                ]

                deduplication_info = DeduplicationCheckResponse(
                    has_nearby_issues=True,
                    nearby_issues=nearby_responses,
                    recommended_action="upvote_existing"
                )

                # Automatically upvote the closest issue and link this report to it
                closest_issue_row, _ = nearby_issues_with_distance[0]
                linked_issue_id = closest_issue_row.id

                # Atomic update for upvotes to prevent race conditions
                # Use query update to avoid fetching the full model instance
                await run_in_threadpool(
                    lambda: db.query(Issue).filter(Issue.id == linked_issue_id).update({
                        Issue.upvotes: func.coalesce(Issue.upvotes, 0) + 1
                    }, synchronize_session=False)
                )

                # Commit the upvote
                await run_in_threadpool(db.commit)

                logger.info(f"Spatial deduplication: Linked new report to existing issue {linked_issue_id}")

        except Exception as e:
            logger.error(f"Error during spatial deduplication check: {e}", exc_info=True)
            # Continue with issue creation if deduplication fails

    try:
        # Save to DB only if no nearby issues found or deduplication failed
        if deduplication_info is None or not deduplication_info.has_nearby_issues:
            # Blockchain feature: calculate integrity hash for the report
            # Optimization: Fetch only the last hash to maintain the chain with minimal overhead
            prev_issue = await run_in_threadpool(
                lambda: db.query(Issue.integrity_hash).order_by(Issue.id.desc()).first()
            )
            prev_hash = prev_issue[0] if prev_issue and prev_issue[0] else ""

            # Simple but effective SHA-256 chaining
            hash_content = f"{description}|{category}|{prev_hash}"
            integrity_hash = hashlib.sha256(hash_content.encode()).hexdigest()

            new_issue = Issue(
                reference_id=str(uuid.uuid4()),
                description=description,
                category=category,
                image_path=image_path,
                source="web",
                user_email=user_email,
                latitude=latitude,
                longitude=longitude,
                location=location,
                action_plan=None,
                integrity_hash=integrity_hash
            )

            # Offload blocking DB operations to threadpool
            await run_in_threadpool(save_issue_db, db, new_issue)
        else:
            # Don't create new issue, just return deduplication info
            new_issue = None
    except Exception as e:
        # Clean up uploaded file if DB save failed
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass  # Ignore cleanup errors

        logger.error(f"Database error while creating issue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save issue to database")

    # Add background task for AI generation only if new issue was created
    if new_issue:
        background_tasks.add_task(process_action_plan_background, new_issue.id, description, category, language, image_path)

        # Create grievance for escalation management
        background_tasks.add_task(create_grievance_from_issue_background, new_issue.id)

        # Invalidate cache so new issue appears
        try:
            recent_issues_cache.clear()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    # Prepare deduplication info if not already set
    if deduplication_info is None:
        deduplication_info = DeduplicationCheckResponse(
            has_nearby_issues=False,
            nearby_issues=[],
            recommended_action="create_new"
        )

    # Return response with deduplication information
    if new_issue:
        return IssueCreateWithDeduplicationResponse(
            id=new_issue.id,
            message="Issue reported successfully. Action plan will be generated shortly.",
            action_plan=None,
            deduplication_info=deduplication_info,
            linked_issue_id=linked_issue_id
        )
    else:
        return IssueCreateWithDeduplicationResponse(
            id=None,
            message="Similar issue found nearby. Your report has been linked to the existing issue to increase its priority.",
            action_plan=None,
            deduplication_info=deduplication_info,
            linked_issue_id=linked_issue_id
        )

@router.post("/api/issues/{issue_id}/vote", response_model=VoteResponse)
async def upvote_issue(issue_id: int, db: Session = Depends(get_db)):
    """
    Upvote an issue.
    Optimized: Performs atomic update without loading full model instance.
    """
    # Use update() for atomic increment and to avoid full model overhead
    updated_count = await run_in_threadpool(
        lambda: db.query(Issue).filter(Issue.id == issue_id).update({
            Issue.upvotes: func.coalesce(Issue.upvotes, 0) + 1
        }, synchronize_session=False)
    )

    if not updated_count:
        raise HTTPException(status_code=404, detail="Issue not found")

    await run_in_threadpool(db.commit)

    # Fetch only the updated upvote count using column projection
    new_upvotes = await run_in_threadpool(
        lambda: db.query(Issue.upvotes).filter(Issue.id == issue_id).scalar()
    )

    return VoteResponse(
        id=issue_id,
        upvotes=new_upvotes or 0,
        message="Issue upvoted successfully"
    )

@router.get("/api/issues/nearby", response_model=List[NearbyIssueResponse])
def get_nearby_issues(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude of the location"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude of the location"),
    radius: float = Query(50.0, ge=10, le=500, description="Search radius in meters"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get issues near a specific location for deduplication purposes.
    Returns issues within the specified radius, sorted by distance.
    """
    try:
        # Check cache first
        cache_key = f"{latitude:.5f}_{longitude:.5f}_{radius}_{limit}"
        cached_data = nearby_issues_cache.get(cache_key)
        if cached_data:
            return cached_data

        # Query open issues with coordinates
        # Optimization: Use bounding box to filter candidates in SQL
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(latitude, longitude, radius)

        # Performance Boost: Use column projection to avoid loading full model instances
        open_issues = db.query(
            Issue.id,
            Issue.description,
            Issue.category,
            Issue.latitude,
            Issue.longitude,
            Issue.upvotes,
            Issue.created_at,
            Issue.status
        ).filter(
            Issue.status == "open",
            Issue.latitude >= min_lat,
            Issue.latitude <= max_lat,
            Issue.longitude >= min_lon,
            Issue.longitude <= max_lon
        ).all()

        nearby_issues_with_distance = find_nearby_issues(
            open_issues, latitude, longitude, radius_meters=radius
        )

        # Convert to response format and limit results
        nearby_responses = [
            NearbyIssueResponse(
                id=issue.id,
                description=issue.description[:100] + "..." if len(issue.description) > 100 else issue.description,
                category=issue.category,
                latitude=issue.latitude,
                longitude=issue.longitude,
                distance_meters=distance,
                upvotes=issue.upvotes or 0,
                created_at=issue.created_at,
                status=issue.status
            )
            for issue, distance in nearby_issues_with_distance[:limit]
        ]

        # Update cache
        nearby_issues_cache.set(nearby_responses, cache_key)

        return nearby_responses

    except Exception as e:
        logger.error(f"Error getting nearby issues: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve nearby issues")

@router.post("/api/issues/{issue_id}/verify", response_model=Union[VoteResponse, Dict[str, Any]])
async def verify_issue_endpoint(
    issue_id: int,
    request: Request,
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Verify an issue manually or via AI.
    Optimized: Uses column projection for initial check and atomic updates.
    """
    # Performance Boost: Fetch only necessary columns
    issue_data = await run_in_threadpool(
        lambda: db.query(
            Issue.id, Issue.category, Issue.status, Issue.upvotes
        ).filter(Issue.id == issue_id).first()
    )

    if not issue_data:
        raise HTTPException(status_code=404, detail="Issue not found")

    if image:
        # AI Verification Logic
        await validate_uploaded_file(image)

        try:
            image_bytes = await image.read()
        except Exception as e:
            logger.error(f"Invalid image file: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Construct question
        category = issue_data.category.lower() if issue_data.category else "issue"
        question = f"Is there a {category} in this image?"

        # Custom questions for common categories
        if "pothole" in category:
            question = "Is there a pothole on the road?"
        elif "garbage" in category or "waste" in category:
            question = "Is there garbage or trash on the ground?"
        elif "light" in category:
            question = "Is the streetlight broken?"
        elif "water" in category or "flood" in category:
            question = "Is the street flooded?"
        elif "tree" in category:
            question = "Is there a fallen tree?"

        try:
            client = request.app.state.http_client
            result = await verify_resolution_vqa(image_bytes, question, client)

            answer = result.get('answer', 'unknown')
            confidence = result.get('confidence', 0)

            is_resolved = False
            if answer.lower() in ["no", "none", "nothing"] and confidence > 0.5:
                is_resolved = True
                if issue_data.status != "resolved":
                    # Perform update using primary key
                    await run_in_threadpool(
                        lambda: db.query(Issue).filter(Issue.id == issue_id).update({
                            Issue.status: "verified",
                            Issue.verified_at: datetime.now(timezone.utc)
                        }, synchronize_session=False)
                    )
                    await run_in_threadpool(db.commit)

            return {
                "is_resolved": is_resolved,
                "ai_answer": answer,
                "confidence": confidence,
                "question_asked": question
            }
        except Exception as e:
            logger.error(f"Resolution verification error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Verification service temporarily unavailable")
    else:
        # Manual Verification Logic (Vote)
        # Atomic increment by 2 for verification
        # Optimized: Use a single transaction for all updates
        await run_in_threadpool(
            lambda: db.query(Issue).filter(Issue.id == issue_id).update({
                Issue.upvotes: func.coalesce(Issue.upvotes, 0) + 2
            }, synchronize_session=False)
        )

        # Flush to DB so we can query the updated value within the same transaction
        await run_in_threadpool(db.flush)

        # Performance Boost: Fetch only needed fields to check auto-verification threshold
        # This query is performed within the same transaction after flush
        updated_issue = await run_in_threadpool(
            lambda: db.query(Issue.upvotes, Issue.status).filter(Issue.id == issue_id).first()
        )

        final_status = updated_issue.status if updated_issue else "open"
        final_upvotes = updated_issue.upvotes if updated_issue else 0

        if updated_issue and updated_issue.upvotes >= 5 and updated_issue.status == "open":
            await run_in_threadpool(
                lambda: db.query(Issue).filter(Issue.id == issue_id).update({
                    Issue.status: "verified"
                }, synchronize_session=False)
            )
            logger.info(f"Issue {issue_id} automatically verified due to {updated_issue.upvotes} upvotes")
            final_status = "verified"

        # Final commit for all changes in the transaction
        await run_in_threadpool(db.commit)

        return VoteResponse(
            id=issue_id,
            upvotes=final_upvotes,
            message="Issue verified successfully"
        )

@router.put("/api/issues/status", response_model=IssueStatusUpdateResponse)
def update_issue_status(
    request: IssueStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update issue status via secure reference ID (for government portals)"""
    issue = db.query(Issue).filter(Issue.reference_id == request.reference_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Validate status transition (simple state machine)
    valid_transitions = {
        "open": ["verified"],
        "verified": ["assigned", "open"],
        "assigned": ["in_progress", "verified"],
        "in_progress": ["resolved", "assigned"],
        "resolved": []  # Terminal state
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
    now = datetime.now(timezone.utc)
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

@router.post("/api/push-subscription", response_model=PushSubscriptionResponse)
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

@router.get("/api/issues/user", response_model=List[IssueSummaryResponse])
def get_user_issues(
    user_email: str = Query(..., description="Email of the user"),
    limit: int = Query(10, ge=1, le=50, description="Number of issues to return"),
    offset: int = Query(0, ge=0, description="Number of issues to skip"),
    db: Session = Depends(get_db)
):
    """
    Get issues reported by a specific user (identified by email).
    Optimized: Uses column projection to avoid loading full model instances and large fields.
    """
    results = db.query(
        Issue.id,
        Issue.category,
        Issue.description,
        Issue.created_at,
        Issue.image_path,
        Issue.status,
        Issue.upvotes,
        Issue.location,
        Issue.latitude,
        Issue.longitude
    ).filter(Issue.user_email == user_email)\
        .order_by(Issue.created_at.desc())\
        .offset(offset).limit(limit).all()

    # Convert results to dictionaries for faster serialization and schema compliance
    data = []
    for row in results:
        desc = row.description or ""
        short_desc = desc[:100] + "..." if len(desc) > 100 else desc

        data.append({
            "id": row.id,
            "category": row.category,
            "description": short_desc,
            "created_at": row.created_at,
            "image_path": row.image_path,
            "status": row.status,
            "upvotes": row.upvotes if row.upvotes is not None else 0,
            "location": row.location,
            "latitude": row.latitude,
            "longitude": row.longitude
        })

    return data

@router.get("/api/issues/{issue_id}/blockchain-verify", response_model=BlockchainVerificationResponse)
async def verify_blockchain_integrity(issue_id: int, db: Session = Depends(get_db)):
    """
    Verify the cryptographic integrity of a report using the blockchain-style chaining.
    Optimized: Uses column projection to fetch only needed data.
    """
    # Fetch current issue data
    current_issue = await run_in_threadpool(
        lambda: db.query(
            Issue.id, Issue.description, Issue.category, Issue.integrity_hash
        ).filter(Issue.id == issue_id).first()
    )

    if not current_issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Fetch previous issue's integrity hash to verify the chain
    prev_issue_hash = await run_in_threadpool(
        lambda: db.query(Issue.integrity_hash).filter(Issue.id < issue_id).order_by(Issue.id.desc()).first()
    )

    prev_hash = prev_issue_hash[0] if prev_issue_hash and prev_issue_hash[0] else ""

    # Recompute hash based on current data and previous hash
    # Chaining logic: hash(description|category|prev_hash)
    hash_content = f"{current_issue.description}|{current_issue.category}|{prev_hash}"
    computed_hash = hashlib.sha256(hash_content.encode()).hexdigest()

    is_valid = (computed_hash == current_issue.integrity_hash)

    if is_valid:
        message = "Integrity verified. This report is cryptographically sealed and has not been tampered with."
    else:
        message = "Integrity check failed! The report data does not match its cryptographic seal."

    return BlockchainVerificationResponse(
        is_valid=is_valid,
        current_hash=current_issue.integrity_hash,
        computed_hash=computed_hash,
        message=message
    )

@router.get("/api/issues/recent", response_model=List[IssueSummaryResponse])
def get_recent_issues(
    limit: int = Query(10, ge=1, le=50, description="Number of issues to return"),
    offset: int = Query(0, ge=0, description="Number of issues to skip"),
    db: Session = Depends(get_db)
):
    cache_key = f"recent_issues_{limit}_{offset}"
    cached_data = recent_issues_cache.get(cache_key)
    if cached_data:
        return JSONResponse(content=cached_data)

    # Fetch issues with pagination
    # Optimized: Use column projection to fetch only needed fields
    results = db.query(
        Issue.id,
        Issue.category,
        Issue.description,
        Issue.created_at,
        Issue.image_path,
        Issue.status,
        Issue.upvotes,
        Issue.location,
        Issue.latitude,
        Issue.longitude
    ).order_by(Issue.created_at.desc()).offset(offset).limit(limit).all()

    # Convert to Pydantic models for validation and serialization
    data = []
    for row in results:
        # Manually construct dict from named tuple row to avoid full object overhead
        desc = row.description or ""
        short_desc = desc[:100] + "..." if len(desc) > 100 else desc

        data.append({
            "id": row.id,
            "category": row.category,
            "description": short_desc,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "image_path": row.image_path,
            "status": row.status,
            "upvotes": row.upvotes if row.upvotes is not None else 0,
            "location": row.location,
            "latitude": row.latitude,
            "longitude": row.longitude
        })

    # Thread-safe cache update
    recent_issues_cache.set(data, cache_key)
    return data
