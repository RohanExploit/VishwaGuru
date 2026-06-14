"""
Voice and Language Router
API endpoints for voice-based grievance submission and multi-language support
Issue #291: Local Language and Voice-Based Grievance Submission
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import Optional
import logging
import os
import uuid
from datetime import datetime, timezone

from backend.database import get_db
from backend.models import Issue
from backend.schemas import (
    VoiceTranscriptionResponse,
    TextTranslationRequest,
    TextTranslationResponse,
    VoiceIssueCreateRequest,
    IssueCreateResponse,
    SupportedLanguagesResponse,
    IssueCategory
)
from backend.voice_service import get_voice_service
from backend.utils import generate_reference_id

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory for storing audio files
AUDIO_STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "audio_recordings")
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)

# Maximum audio file size (10 MB)
MAX_AUDIO_SIZE = 10 * 1024 * 1024


@router.post("/api/voice/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_voice(
    audio_file: UploadFile = File(..., description="Audio file (WAV, MP3, FLAC, etc.)"),
    preferred_language: str = Form('auto', description="Preferred language code")
):
    """
    Transcribe voice audio to text with support for Indian regional languages
    
    - **audio_file**: Audio file to transcribe
    - **preferred_language**: Preferred language code ('auto', 'hi', 'mr', 'en', etc.)
    
    Returns transcribed text, translated text (English), and confidence score
    """
    try:
        # Read audio file
        audio_content = await audio_file.read()
        
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio file provided")
        
        # Validate file size
        if len(audio_content) > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"Audio file too large. Maximum size is {MAX_AUDIO_SIZE / 1024 / 1024:.0f} MB."
            )
        
        # Get voice service
        voice_service = get_voice_service()
        
        # Process voice grievance (transcribe + translate) in threadpool to avoid blocking
        result = await run_in_threadpool(
            voice_service.process_voice_grievance,
            audio_file=audio_content,
            preferred_language=preferred_language
        )
        
        if result['error']:
            logger.warning(f"Voice transcription failed: {result['error']}")
            return VoiceTranscriptionResponse(
                original_text=None,
                translated_text=None,
                source_language=None,
                source_language_name=None,
                confidence=0.0,
                manual_correction_needed=True,
                error=result['error']
            )
        
        return VoiceTranscriptionResponse(
            original_text=result['original_text'],
            translated_text=result['translated_text'],
            source_language=result['source_language'],
            source_language_name=result['source_language_name'],
            confidence=result['confidence'],
            manual_correction_needed=result['manual_correction_needed'],
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in voice transcription endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice transcription failed: {str(e)}")


@router.post("/api/voice/translate", response_model=TextTranslationResponse)
def translate_text(request: TextTranslationRequest):
    """
    Translate text from one language to another
    
    - **text**: Text to translate
    - **source_language**: Source language code ('auto' for auto-detection)
    - **target_language**: Target language code (default: 'en')
    
    Supports Indian regional languages: Hindi, Marathi, Bengali, Tamil, Telugu, etc.
    """
    try:
        voice_service = get_voice_service()
        
        result = voice_service.translate_text(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language
        )
        
        if result['error']:
            logger.warning(f"Text translation failed: {result['error']}")
            return TextTranslationResponse(
                translated_text=None,
                source_language=None,
                source_language_name=None,
                target_language=None,
                target_language_name=None,
                original_text=request.text,
                error=result['error']
            )
        
        return TextTranslationResponse(
            translated_text=result['translated_text'],
            source_language=result['source_language'],
            source_language_name=result['source_language_name'],
            target_language=result['target_language'],
            target_language_name=result['target_language_name'],
            original_text=result['original_text'],
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error in text translation endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Text translation failed: {str(e)}")


@router.post("/api/voice/submit-issue", response_model=IssueCreateResponse)
async def submit_voice_issue(
    audio_file: UploadFile = File(..., description="Audio file with grievance description"),
    category: str = Form(..., description="Issue category"),
    user_email: Optional[str] = Form(None, description="User email"),
    latitude: Optional[float] = Form(None, description="Latitude"),
    longitude: Optional[float] = Form(None, description="Longitude"),
    location: Optional[str] = Form(None, description="Location description"),
    preferred_language: str = Form('auto', description="Preferred language code"),
    manual_description: Optional[str] = Form(None, description="Manual correction of description"),
    db: Session = Depends(get_db)
):
    """
    Submit an issue via voice recording
    
    - **audio_file**: Voice recording describing the issue
    - **category**: Issue category (Road, Water, Garbage, etc.)
    - **user_email**: User's email (optional)
    - **latitude/longitude**: GPS coordinates (optional)
    - **location**: Location description (optional)
    - **preferred_language**: Preferred language for transcription
    - **manual_description**: Manual correction if transcription needs fixing
    
    The system will:
    1. Transcribe the audio to text
    2. Translate to English if needed
    3. Create the issue in the system
    4. Store the original audio and language metadata
    """
    try:
        # Validate category
        try:
            issue_category = IssueCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        # Read audio file
        audio_content = await audio_file.read()
        
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio file provided")
        
        # Validate file size
        if len(audio_content) > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Audio file too large. Maximum size is {MAX_AUDIO_SIZE / 1024 / 1024:.0f} MB."
            )
        
        # Get voice service
        voice_service = get_voice_service()
        
        # Process voice (transcribe + translate) in threadpool to avoid blocking
        voice_result = await run_in_threadpool(
            voice_service.process_voice_grievance,
            audio_file=audio_content,
            preferred_language=preferred_language
        )
        
        if voice_result['error'] and not manual_description:
            raise HTTPException(
                status_code=400,
                detail=f"Voice transcription failed: {voice_result['error']}. Please provide manual description."
            )
        
        # Determine final description
        if manual_description:
            # User provided manual correction
            final_description = manual_description
            manual_correction_applied = True
            original_text = voice_result.get('original_text', '')
        else:
            # Use transcribed and translated text
            final_description = voice_result['translated_text']
            manual_correction_applied = False
            original_text = voice_result['original_text']
        
        # Validate description
        if not final_description or len(final_description.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Description too short. Please provide at least 10 characters."
            )
        
        # Save audio file with secure filename (prevent path traversal)
        # Use UUID to avoid any user-controlled filename issues
        file_extension = '.wav'  # Default extension
        if audio_file.filename:
            # Try to extract extension safely
            parts = audio_file.filename.rsplit('.', 1)
            if len(parts) == 2 and parts[1].lower() in ['wav', 'mp3', 'flac', 'ogg', 'm4a']:
                file_extension = '.' + parts[1].lower()
        
        audio_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}{file_extension}"
        audio_file_path = os.path.join(AUDIO_STORAGE_DIR, audio_filename)
        
        with open(audio_file_path, 'wb') as f:
            f.write(audio_content)
        
        # Store relative path for portability
        relative_audio_path = os.path.join("data", "audio_recordings", audio_filename)
        
        # Create issue in database
        reference_id = generate_reference_id()
        
        new_issue = Issue(
            reference_id=reference_id,
            description=final_description,
            category=issue_category.value,
            user_email=user_email,
            latitude=latitude,
            longitude=longitude,
            location=location,
            source='voice',
            status='open',
            # Voice-specific fields
            submission_type='voice',
            original_language=voice_result.get('source_language'),
            original_text=original_text,
            transcription_confidence=voice_result.get('confidence', 0.0),
            manual_correction_applied=manual_correction_applied,
            audio_file_path=relative_audio_path  # Store relative path
        )
        
        db.add(new_issue)
        db.commit()
        db.refresh(new_issue)
        
        logger.info(f"Voice issue created: ID={new_issue.id}, Language={voice_result.get('source_language')}, Confidence={voice_result.get('confidence')}")
        
        return IssueCreateResponse(
            id=new_issue.id,
            message=f"Voice issue submitted successfully. Transcription confidence: {voice_result.get('confidence', 0.0):.2%}",
            action_plan=None  # Action plan can be generated separately
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting voice issue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit voice issue: {str(e)}")


@router.get("/api/voice/supported-languages", response_model=SupportedLanguagesResponse)
def get_supported_languages():
    """
    Get list of supported languages for voice transcription and translation
    
    Returns dictionary of language codes and their names
    """
    try:
        voice_service = get_voice_service()
        supported_langs = voice_service.get_supported_languages()
        
        return SupportedLanguagesResponse(
            languages=supported_langs,
            total_count=len(supported_langs)
        )
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve supported languages")


@router.get("/api/voice/issue/{issue_id}/audio")
def get_issue_audio(issue_id: int, db: Session = Depends(get_db)):
    """
    Get the original audio file for a voice-submitted issue
    
    - **issue_id**: ID of the issue
    
    Returns the audio file if available
    """
    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        if issue.submission_type != 'voice' or not issue.audio_file_path:
            raise HTTPException(status_code=404, detail="No audio file available for this issue")
        
        # Resolve path (handle both absolute and relative paths)
        if os.path.isabs(issue.audio_file_path):
            audio_path = issue.audio_file_path
        else:
            # Relative path - resolve from backend directory
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            audio_path = os.path.join(backend_dir, issue.audio_file_path)
        
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found on server")
        
        # Detect media type from file extension
        extension = os.path.splitext(audio_path)[1].lower()
        media_type_map = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4'
        }
        media_type = media_type_map.get(extension, 'audio/wav')
        
        from fastapi.responses import FileResponse
        return FileResponse(
            audio_path,
            media_type=media_type,
            filename=os.path.basename(audio_path)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audio file for issue {issue_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve audio file")
