"""
Field Officer Check-In Router
API endpoints for field officer location verification and visit tracking
Issue #288: Field Officer Check-In System With Location Verification
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Optional
import logging
import os
import json
import uuid
from datetime import datetime, timezone

from backend.database import get_db
from backend.models import FieldOfficerVisit, Issue, Grievance, User
from backend.dependencies import get_current_active_user
from backend.utils import process_uploaded_image, save_processed_image
from backend.schemas import (
    OfficerCheckInRequest,
    OfficerCheckOutRequest,
    FieldOfficerVisitResponse,
    PublicFieldOfficerVisitResponse,
    VisitHistoryResponse,
    VisitStatsResponse,
    VisitImageUploadResponse,
)
from backend.geofencing_service import (
    is_within_geofence,
    generate_visit_hash,
    verify_visit_integrity,
    calculate_visit_metrics,
    get_geofencing_service,
)
from backend.cache import visit_last_hash_cache, visit_stats_cache
from backend.schemas import BlockchainVerificationResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory for storing visit images
VISIT_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "visit_images")
os.makedirs(VISIT_IMAGES_DIR, exist_ok=True)

# File upload constraints
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB per image
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


@router.post("/field-officer/check-in", response_model=FieldOfficerVisitResponse)
def officer_check_in(request: OfficerCheckInRequest, db: Session = Depends(get_db)):
    """
    Field officer check-in at a grievance site with GPS verification

    - **issue_id**: ID of the issue being visited
    - **officer_email**: Officer's email
    - **officer_name**: Officer's name
    - **check_in_latitude**: GPS latitude of check-in location
    - **check_in_longitude**: GPS longitude of check-in location
    - **visit_notes**: Optional notes about the visit
    - **geofence_radius_meters**: Acceptable distance from site (default: 100m)

    **Geo-Fencing**: Automatically verifies if officer is within acceptable radius of issue location
    """
    try:
        # Validate issue exists
        issue = db.query(Issue).filter(Issue.id == request.issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=404, detail=f"Issue {request.issue_id} not found"
            )

        # Validate grievance if provided
        if request.grievance_id:
            grievance = (
                db.query(Grievance).filter(Grievance.id == request.grievance_id).first()
            )
            if not grievance:
                raise HTTPException(
                    status_code=404,
                    detail=f"Grievance {request.grievance_id} not found",
                )

        # Validate GPS coordinates
        geofencing = get_geofencing_service()
        if not geofencing.validate_coordinates(
            request.check_in_latitude, request.check_in_longitude
        ):
            raise HTTPException(status_code=400, detail="Invalid GPS coordinates")

        # Check if issue has location data (use 'is None' to allow 0.0 coordinates)
        if issue.latitude is None or issue.longitude is None:
            raise HTTPException(
                status_code=400,
                detail="Issue does not have location data. Cannot verify geo-fence.",
            )

        # Calculate distance and verify geo-fence
        within_fence, distance = is_within_geofence(
            check_in_lat=request.check_in_latitude,
            check_in_lon=request.check_in_longitude,
            site_lat=issue.latitude,
            site_lon=issue.longitude,
            radius_meters=request.geofence_radius_meters or 100.0,
        )

        # Create visit record
        # Normalize check_in_time: strip microseconds for deterministic hashing across DBs
        check_in_time = datetime.now(timezone.utc).replace(microsecond=0)

        # Blockchain feature: calculate integrity hash for the visit
        prev_hash = visit_last_hash_cache.get("last_hash")
        if prev_hash is None:
            # Cache miss: Fetch only the last hash from DB
            prev_visit = (
                db.query(FieldOfficerVisit.visit_hash)
                .order_by(FieldOfficerVisit.id.desc())
                .first()
            )
            prev_hash = prev_visit[0] if prev_visit and prev_visit[0] else ""
            visit_last_hash_cache.set(data=prev_hash, key="last_hash")

        visit_data = {
            "issue_id": request.issue_id,
            "officer_email": request.officer_email,
            "check_in_latitude": request.check_in_latitude,
            "check_in_longitude": request.check_in_longitude,
            "check_in_time": check_in_time,
            "visit_notes": request.visit_notes or "",
            "previous_visit_hash": prev_hash,
        }

        # Generate immutable hash
        visit_hash = generate_visit_hash(visit_data)

        new_visit = FieldOfficerVisit(
            issue_id=request.issue_id,
            grievance_id=request.grievance_id,
            officer_email=request.officer_email,
            officer_name=request.officer_name,
            officer_department=request.officer_department,
            officer_designation=request.officer_designation,
            check_in_latitude=request.check_in_latitude,
            check_in_longitude=request.check_in_longitude,
            check_in_time=check_in_time,
            distance_from_site=round(distance, 2),
            within_geofence=within_fence,
            geofence_radius_meters=request.geofence_radius_meters or 100.0,
            visit_notes=request.visit_notes,
            status="checked_in",
            visit_hash=visit_hash,
            previous_visit_hash=prev_hash,
            is_public=True,
        )

        db.add(new_visit)
        db.commit()
        db.refresh(new_visit)

        # Update cache for next visit AFTER successful DB commit
        visit_last_hash_cache.set(data=visit_hash, key="last_hash")

        # Invalidate visit stats cache
        visit_stats_cache.clear()

        logger.info(
            f"Officer {request.officer_name} checked in at issue {request.issue_id}. "
            f"Distance: {distance:.2f}m, Within fence: {within_fence}"
        )

        return FieldOfficerVisitResponse(
            id=new_visit.id,
            issue_id=new_visit.issue_id,
            grievance_id=new_visit.grievance_id,
            officer_email=new_visit.officer_email,
            officer_name=new_visit.officer_name,
            officer_department=new_visit.officer_department,
            officer_designation=new_visit.officer_designation,
            check_in_latitude=new_visit.check_in_latitude,
            check_in_longitude=new_visit.check_in_longitude,
            check_in_time=new_visit.check_in_time,
            check_out_time=new_visit.check_out_time,
            distance_from_site=new_visit.distance_from_site,
            within_geofence=new_visit.within_geofence,
            visit_notes=new_visit.visit_notes,
            visit_images=new_visit.visit_images,
            visit_duration_minutes=new_visit.visit_duration_minutes,
            status=new_visit.status,
            verified_by=new_visit.verified_by,
            verified_at=new_visit.verified_at,
            is_public=new_visit.is_public,
            created_at=new_visit.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during officer check-in: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Check-in failed. Please try again."
        )


@router.post("/field-officer/check-out", response_model=FieldOfficerVisitResponse)
def officer_check_out(request: OfficerCheckOutRequest, db: Session = Depends(get_db)):
    """
    Field officer check-out from a visit

    - **visit_id**: ID of the visit to check out from
    - **check_out_latitude**: GPS latitude at check-out
    - **check_out_longitude**: GPS longitude at check-out
    - **visit_duration_minutes**: Estimated visit duration
    - **additional_notes**: Any additional notes
    """
    try:
        visit = (
            db.query(FieldOfficerVisit)
            .filter(FieldOfficerVisit.id == request.visit_id)
            .first()
        )

        if not visit:
            raise HTTPException(
                status_code=404, detail=f"Visit {request.visit_id} not found"
            )

        if visit.status == "checked_out":
            raise HTTPException(
                status_code=400, detail="Already checked out from this visit"
            )

        # Validate GPS coordinates
        geofencing = get_geofencing_service()
        if not geofencing.validate_coordinates(
            request.check_out_latitude, request.check_out_longitude
        ):
            raise HTTPException(
                status_code=400, detail="Invalid check-out GPS coordinates"
            )

        # Update visit with check-out data
        visit.check_out_time = datetime.now(timezone.utc)
        visit.check_out_latitude = request.check_out_latitude
        visit.check_out_longitude = request.check_out_longitude
        visit.visit_duration_minutes = request.visit_duration_minutes

        # Append additional notes if provided
        if request.additional_notes:
            existing_notes = visit.visit_notes or ""
            visit.visit_notes = (
                f"{existing_notes}\n\n[Check-out notes]: {request.additional_notes}"
            )

        visit.status = "checked_out"
        visit.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(visit)

        # Invalidate visit stats cache
        visit_stats_cache.clear()

        logger.info(f"Officer checked out from visit {request.visit_id}")

        return FieldOfficerVisitResponse(
            id=visit.id,
            issue_id=visit.issue_id,
            grievance_id=visit.grievance_id,
            officer_email=visit.officer_email,
            officer_name=visit.officer_name,
            officer_department=visit.officer_department,
            officer_designation=visit.officer_designation,
            check_in_latitude=visit.check_in_latitude,
            check_in_longitude=visit.check_in_longitude,
            check_in_time=visit.check_in_time,
            check_out_time=visit.check_out_time,
            distance_from_site=visit.distance_from_site,
            within_geofence=visit.within_geofence,
            visit_notes=visit.visit_notes,
            visit_images=visit.visit_images,
            visit_duration_minutes=visit.visit_duration_minutes,
            status=visit.status,
            verified_by=visit.verified_by,
            verified_at=visit.verified_at,
            is_public=visit.is_public,
            created_at=visit.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during officer check-out: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Check-out failed. Please try again."
        )


@router.post(
    "/field-officer/visit/{visit_id}/upload-images",
    response_model=VisitImageUploadResponse,
)
async def upload_visit_images(
    visit_id: int,
    images: List[UploadFile] = File(..., description="Visit images"),
    db: Session = Depends(get_db),
):
    """
    Upload images for a field officer visit

    - **visit_id**: ID of the visit
    - **images**: List of image files

    Maximum 10 images per visit
    """
    try:
        visit = (
            db.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit_id).first()
        )

        if not visit:
            raise HTTPException(status_code=404, detail=f"Visit {visit_id} not found")

        if len(images) > 10:
            raise HTTPException(
                status_code=400, detail="Maximum 10 images allowed per visit"
            )

        # Check cumulative image count
        existing_images = visit.visit_images or []
        if not isinstance(existing_images, list):
            existing_images = []

        if len(existing_images) + len(images) > 10:
            raise HTTPException(
                status_code=400,
                detail=f"Total images would exceed limit. Current: {len(existing_images)}, attempting to add: {len(images)}",
            )

        image_paths = []

        for idx, image in enumerate(images):
            # Performance Boost: Check file size without reading full content into memory (O(1) seek)
            await image.seek(0, 2)  # Seek to end
            file_size = image.tell()
            await image.seek(0)  # Reset pointer

            if file_size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {image.filename} too large. Maximum allowed is {MAX_UPLOAD_SIZE // (1024*1024)}MB",
                )

            # Validate extension (Fast early-exit)
            extension = (
                image.filename.split(".")[-1].lower()
                if image.filename and "." in image.filename
                else ""
            )
            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"File extension '{extension}' not allowed. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
                )

            # Performance Boost: Unified pipeline for validation, resizing, and EXIF stripping
            # Reduces redundant Encode/Decode cycles and storage footprint.
            _, image_bytes = await process_uploaded_image(image)

            # Generate secure filename using UUID to prevent collisions and path traversal
            safe_filename = f"visit_{visit_id}_{uuid.uuid4().hex}.{extension}"
            file_path = os.path.join(VISIT_IMAGES_DIR, safe_filename)

            # Performance Boost: Wrap blocking synchronous File I/O in threadpool to keep event loop responsive
            await run_in_threadpool(save_processed_image, image_bytes, file_path)

            # Store relative path
            relative_path = os.path.join("data", "visit_images", safe_filename)
            image_paths.append(relative_path)

        # Update visit with image paths
        existing_images.extend(image_paths)
        visit.visit_images = existing_images
        visit.updated_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(f"Uploaded {len(images)} images for visit {visit_id}")

        return VisitImageUploadResponse(
            visit_id=visit_id,
            image_paths=image_paths,
            message=f"Successfully uploaded {len(images)} images",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading visit images: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Image upload failed. Please try again."
        )


@router.get(
    "/field-officer/issue/{issue_id}/visit-history", response_model=VisitHistoryResponse
)
def get_issue_visit_history(
    issue_id: int, public_only: bool = True, db: Session = Depends(get_db)
):
    """
    Get visit history for an issue (public read-only access for transparency)

    - **issue_id**: ID of the issue
    - **public_only**: Only return public visits (default: True)

    Returns chronological list of all officer visits to the site
    """
    try:
        query = db.query(FieldOfficerVisit).filter(
            FieldOfficerVisit.issue_id == issue_id
        )

        if public_only:
            query = query.filter(FieldOfficerVisit.is_public == True)

        visits = query.order_by(FieldOfficerVisit.check_in_time.desc()).all()

        visit_responses = [
            PublicFieldOfficerVisitResponse(
                id=v.id,
                issue_id=v.issue_id,
                grievance_id=v.grievance_id,
                officer_name=v.officer_name,
                officer_department=v.officer_department,
                officer_designation=v.officer_designation,
                check_in_latitude=v.check_in_latitude,
                check_in_longitude=v.check_in_longitude,
                check_in_time=v.check_in_time,
                check_out_time=v.check_out_time,
                distance_from_site=v.distance_from_site,
                within_geofence=v.within_geofence,
                visit_notes=v.visit_notes,
                visit_images=v.visit_images,
                visit_duration_minutes=v.visit_duration_minutes,
                status=v.status,
                verified_by=v.verified_by,
                verified_at=v.verified_at,
                is_public=v.is_public,
                created_at=v.created_at,
            )
            for v in visits
        ]

        return VisitHistoryResponse(
            issue_id=issue_id, total_visits=len(visits), visits=visit_responses
        )

    except Exception as e:
        logger.error(
            f"Error getting visit history for issue {issue_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve visit history")


@router.get("/field-officer/visit-stats", response_model=VisitStatsResponse)
def get_visit_statistics(db: Session = Depends(get_db)):
    """
    Get aggregate statistics for all field officer visits using optimized SQL queries.
    Optimized: Uses serialization caching to bypass Pydantic overhead.
    """
    try:
        cache_key = "global_visit_stats"
        cached_json = visit_stats_cache.get(cache_key)
        if cached_json:
            return Response(content=cached_json, media_type="application/json")

        # Optimized: Standard GROUP BY is measurably faster than multiple func.sum(case(...)) aggregations.
        groups = db.query(
            FieldOfficerVisit.verified_at.isnot(None).label('is_verified'),
            FieldOfficerVisit.within_geofence,
            func.count(FieldOfficerVisit.id)
        ).group_by(
            FieldOfficerVisit.verified_at.isnot(None),
            FieldOfficerVisit.within_geofence
        ).all()

        # Second query for global aggregates
        global_stats = db.query(
            func.count(func.distinct(FieldOfficerVisit.officer_email)).label('unique_officers'),
            func.avg(FieldOfficerVisit.distance_from_site).label('avg_distance')
        ).first()

        total_visits = 0
        verified_visits = 0
        within_geofence_count = 0
        outside_geofence_count = 0

        for is_ver, in_geo, count in groups:
            total_visits += count
            if is_ver:
                verified_visits += count
            if in_geo is True:
                within_geofence_count += count
            elif in_geo is False:
                outside_geofence_count += count

        unique_officers = global_stats.unique_officers or 0
        average_distance = global_stats.avg_distance
        
        # Round to 2 decimals if not None
        if average_distance is not None:
            average_distance = round(float(average_distance), 2)
        else:
            average_distance = 0.0

        result_data = {
            "total_visits": total_visits,
            "verified_visits": verified_visits,
            "within_geofence_count": within_geofence_count,
            "outside_geofence_count": outside_geofence_count,
            "unique_officers": unique_officers,
            "average_distance_from_site": average_distance,
        }

        # Cache serialized JSON
        json_data = json.dumps(result_data)
        visit_stats_cache.set(data=json_data, key=cache_key)

        return Response(content=json_data, media_type="application/json")

    except Exception as e:
        logger.error(f"Error calculating visit statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate statistics")


@router.post("/field-officer/visit/{visit_id}/verify")
def verify_visit(
    visit_id: int,
    verifier_email: str = Form(..., description="Email of verifying admin/supervisor"),
    db: Session = Depends(get_db),
):
    """
    Admin/supervisor verification of a field officer visit

    - **visit_id**: ID of the visit to verify
    - **verifier_email**: Email of the person verifying

    Marks visit as officially verified
    """
    try:
        visit = (
            db.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit_id).first()
        )

        if not visit:
            raise HTTPException(status_code=404, detail=f"Visit {visit_id} not found")

        if visit.verified_at:
            raise HTTPException(status_code=400, detail="Visit already verified")

        visit.verified_by = verifier_email
        visit.verified_at = datetime.now(timezone.utc)
        visit.status = "verified"
        visit.updated_at = datetime.now(timezone.utc)

        db.commit()

        # Invalidate visit stats cache
        visit_stats_cache.clear()

        logger.info(f"Visit {visit_id} verified by {verifier_email}")

        return {"message": "Visit verified successfully", "visit_id": visit_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying visit {visit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Verification failed")


@router.get(
    "/field-officer/{visit_id}/blockchain-verify",
    response_model=BlockchainVerificationResponse,
)
def verify_visit_blockchain(visit_id: int, db: Session = Depends(get_db)):
    """
    Verify the cryptographic integrity of a field officer visit using blockchain-style chaining.
    Optimized: Uses previous_visit_hash column for O(1) verification.
    """
    try:
        visit = (
            db.query(FieldOfficerVisit).filter(FieldOfficerVisit.id == visit_id).first()
        )

        if not visit:
            raise HTTPException(status_code=404, detail=f"Visit {visit_id} not found")

        # Determine previous hash (O(1) from stored column)
        prev_hash = visit.previous_visit_hash or ""

        # Chaining logic: rebuild the dictionary for verification
        visit_data = {
            "issue_id": visit.issue_id,
            "officer_email": visit.officer_email,
            "check_in_latitude": visit.check_in_latitude,
            "check_in_longitude": visit.check_in_longitude,
            "check_in_time": visit.check_in_time,
            "visit_notes": visit.visit_notes or "",
            "previous_visit_hash": prev_hash,
        }

        # Use helper for verification
        is_valid = verify_visit_integrity(visit_data, visit.visit_hash)

        # For the response, we need the computed hash
        computed_hash = generate_visit_hash(visit_data)

        if is_valid:
            message = "Integrity verified. This visit record is cryptographically sealed and part of a secure chain."
        else:
            message = "Integrity check failed! The visit data does not match its cryptographic seal."

        return BlockchainVerificationResponse(
            is_valid=is_valid,
            current_hash=visit.visit_hash,
            computed_hash=computed_hash,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error verifying visit blockchain for {visit_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to verify visit integrity")
