from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from PIL import Image
from async_lru import alru_cache
import logging

from backend.utils import process_and_detect, validate_uploaded_file, process_uploaded_image
from backend.schemas import DetectionResponse, UrgencyAnalysisRequest, UrgencyAnalysisResponse
from backend.pothole_detection import detect_potholes, validate_image_for_processing
from backend.unified_detection_service import (
    detect_vandalism as detect_vandalism_unified,
    detect_infrastructure as detect_infrastructure_unified,
    detect_flooding as detect_flooding_unified,
    detect_garbage as detect_garbage_unified
)
from backend.hf_api_service import (
    detect_illegal_parking_clip,
    detect_street_light_clip,
    detect_fire_clip,
    detect_stray_animal_clip,
    detect_blocked_road_clip,
    detect_tree_hazard_clip,
    detect_pest_clip,
    detect_severity_clip,
    detect_smart_scan_clip,
    generate_image_caption,
    analyze_urgency_text,
    detect_depth_map,
    detect_water_leak_clip,
    detect_accessibility_issue_clip,
    detect_crowd_density_clip,
    detect_audio_event,
    transcribe_audio,
    detect_waste_clip,
    detect_civic_eye_clip,
    detect_graffiti_art_clip,
    detect_traffic_sign_clip,
    detect_abandoned_vehicle_clip,
    detect_public_transport_clip,
    detect_cleanliness_clip,
    detect_playground_clip
)
from backend.dependencies import get_http_client
import backend.dependencies

logger = logging.getLogger(__name__)

router = APIRouter()

# Cached Functions

@alru_cache(maxsize=100)
async def _cached_detect_severity(image_bytes: bytes):
    return await detect_severity_clip(image_bytes, client=backend.dependencies.SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_detect_smart_scan(image_bytes: bytes):
    return await detect_smart_scan_clip(image_bytes, client=backend.dependencies.SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_generate_caption(image_bytes: bytes):
    return await generate_image_caption(image_bytes, client=backend.dependencies.SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_detect_waste(image_bytes: bytes):
    return await detect_waste_clip(image_bytes, client=backend.dependencies.SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_detect_civic_eye(image_bytes: bytes):
    return await detect_civic_eye_clip(image_bytes, client=backend.dependencies.SHARED_HTTP_CLIENT)

@alru_cache(maxsize=100)
async def _cached_detect_graffiti(image_bytes: bytes):
    return await detect_graffiti_art_clip(image_bytes, client=backend.dependencies.SHARED_HTTP_CLIENT)

# Endpoints

@router.post("/api/detect-pothole", response_model=DetectionResponse)
async def detect_pothole_endpoint(image: UploadFile = File(...)):
    # Validate uploaded file
    pil_image = await validate_uploaded_file(image)

    # Validate image for processing
    try:
        if pil_image is None:
            pil_image = await run_in_threadpool(Image.open, image.file)

        # Validate image for processing
        await run_in_threadpool(validate_image_for_processing, pil_image)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from validation
    except Exception as e:
        logger.error(f"Invalid image file for pothole detection: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection (blocking, so run in threadpool)
    try:
        detections = await run_in_threadpool(detect_potholes, pil_image)
        return DetectionResponse(detections=detections)
    except Exception as e:
        logger.error(f"Pothole detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Pothole detection service temporarily unavailable")

@router.post("/api/detect-infrastructure", response_model=DetectionResponse)
async def detect_infrastructure_endpoint(image: UploadFile = File(...)):
    return await process_and_detect(image, detect_infrastructure_unified)

@router.post("/api/detect-flooding", response_model=DetectionResponse)
async def detect_flooding_endpoint(image: UploadFile = File(...)):
    return await process_and_detect(image, detect_flooding_unified)

@router.post("/api/detect-vandalism", response_model=DetectionResponse)
async def detect_vandalism_endpoint(image: UploadFile = File(...)):
    return await process_and_detect(image, detect_vandalism_unified)

@router.post("/api/detect-garbage", response_model=DetectionResponse)
async def detect_garbage_endpoint(image: UploadFile = File(...)):
    return await process_and_detect(image, detect_garbage_unified)

@router.post("/api/detect-illegal-parking")
async def detect_illegal_parking_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_illegal_parking_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Illegal parking detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/detect-street-light")
async def detect_street_light_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_street_light_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Street light detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/detect-fire")
async def detect_fire_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_fire_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Fire detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/detect-stray-animal")
async def detect_stray_animal_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_stray_animal_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Stray animal detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/detect-blocked-road")
async def detect_blocked_road_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_blocked_road_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Blocked road detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-tree-hazard")
async def detect_tree_hazard_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_tree_hazard_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Tree hazard detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-pest")
async def detect_pest_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_pest_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Pest detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-water-leak")
async def detect_water_leak_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_water_leak_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Water leak detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-accessibility")
async def detect_accessibility_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_accessibility_issue_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Accessibility detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-crowd")
async def detect_crowd_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        detections = await detect_crowd_density_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Crowd detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-audio")
async def detect_audio_endpoint(request: Request, file: UploadFile = File(...)):
    # Basic audio validation
    # Allow webm (browser default), wav, mp3
    if file.content_type and not file.content_type.startswith("audio/"):
         # Some browsers might send application/octet-stream for blobs
         pass

    # Check simple extension just in case if name is available, but for blob it might be 'blob'

    # Just proceed to read and try
    # 10MB limit for audio
    if hasattr(file, 'size') and file.size and file.size > 10 * 1024 * 1024:
         raise HTTPException(status_code=413, detail="Audio file too large")

    try:
        audio_bytes = await file.read()
        if len(audio_bytes) > 10 * 1024 * 1024:
             raise HTTPException(status_code=413, detail="Audio file too large")
    except Exception as e:
        logger.error(f"Invalid audio file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid audio file")

    try:
        client = get_http_client(request)
        detections = await detect_audio_event(audio_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Audio detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-severity")
async def detect_severity_endpoint(image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)
    try:
        return await _cached_detect_severity(image_bytes)
    except Exception as e:
        logger.error(f"Severity detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-smart-scan")
async def detect_smart_scan_endpoint(image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)
    try:
        return await _cached_detect_smart_scan(image_bytes)
    except Exception as e:
        logger.error(f"Smart scan detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/generate-description")
async def generate_description_endpoint(image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)
    try:
        description = await _cached_generate_caption(image_bytes)
        if not description:
            return {"description": "", "error": "Could not generate description"}
        return {"description": description}
    except Exception as e:
        logger.error(f"Description generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/analyze-depth")
async def analyze_depth_endpoint(request: Request, image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        client = get_http_client(request)
        result = await detect_depth_map(image_bytes, client=client)
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Depth analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/analyze-urgency", response_model=UrgencyAnalysisResponse)
async def analyze_urgency_endpoint(request: Request, urgency_req: UrgencyAnalysisRequest):
    try:
        client = get_http_client(request)
        result = await analyze_urgency_text(urgency_req.description, client=client)
        return UrgencyAnalysisResponse(
            urgency_level=result.get("urgency_level", "medium"),
            reasoning=result.get("reasoning", "Analysis completed"),
            recommended_actions=result.get("recommended_actions", [])
        )
    except Exception as e:
        logger.error(f"Urgency analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Urgency analysis service temporarily unavailable")

@router.post("/api/transcribe-audio")
async def transcribe_audio_endpoint(request: Request, file: UploadFile = File(...)):
    # Basic audio validation
    if hasattr(file, 'size') and file.size and file.size > 25 * 1024 * 1024:
         raise HTTPException(status_code=413, detail="Audio file too large (max 25MB)")

    try:
        audio_bytes = await file.read()
    except Exception as e:
        logger.error(f"Invalid audio file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid audio file")

    try:
        client = get_http_client(request)
        text = await transcribe_audio(audio_bytes, client=client)
        return {"text": text}
    except Exception as e:
        logger.error(f"Audio transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/detect-waste")
async def detect_waste_endpoint(image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        return await _cached_detect_waste(image_bytes)
    except Exception as e:
        logger.error(f"Waste detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/detect-civic-eye")
async def detect_civic_eye_endpoint(image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        return await _cached_detect_civic_eye(image_bytes)
    except Exception as e:
        logger.error(f"Civic Eye detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/detect-graffiti")
async def detect_graffiti_endpoint(image: UploadFile = File(...)):
    # Optimized Image Processing: Validation + Optimization
    _, image_bytes = await process_uploaded_image(image)

    try:
        return {"detections": await _cached_detect_graffiti(image_bytes)}
    except Exception as e:
        logger.error(f"Graffiti detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-traffic-sign")
async def detect_traffic_sign_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = get_http_client(request)
        detections = await detect_traffic_sign_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Traffic sign detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-abandoned-vehicle")
async def detect_abandoned_vehicle_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = get_http_client(request)
        detections = await detect_abandoned_vehicle_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Abandoned vehicle detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api/detect-public-transport")
async def detect_public_transport_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = get_http_client(request)
        detections = await detect_public_transport_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Public transport detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-cleanliness")
async def detect_cleanliness_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = get_http_client(request)
        detections = await detect_cleanliness_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Cleanliness detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/detect-playground")
async def detect_playground_endpoint(request: Request, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")

    try:
        client = get_http_client(request)
        detections = await detect_playground_clip(image_bytes, client=client)
        return {"detections": detections}
    except Exception as e:
        logger.error(f"Playground detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
