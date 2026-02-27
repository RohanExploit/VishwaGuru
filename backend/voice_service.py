"""
Voice Transcription and Language Translation Service
Handles voice-based grievance submissions with support for Indian regional languages.
Issue #291: Local Language and Voice-Based Grievance Submission
"""

import logging
import os
import tempfile
import asyncio
from typing import Dict, Optional, Tuple
from pathlib import Path
import speech_recognition as sr
from googletrans import Translator
from langdetect import detect, LangDetectException
from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Supported Indian regional languages
SUPPORTED_LANGUAGES = {
    'hi': 'Hindi',
    'bn': 'Bengali',
    'te': 'Telugu',
    'mr': 'Marathi',
    'ta': 'Tamil',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'or': 'Odia',
    'as': 'Assamese',
    'en': 'English'
}

class VoiceService:
    """Service for handling voice transcription and language translation"""
    
    def __init__(self):
        # Don't create recognizer or translator as instance variables
        # Create fresh instances per call for thread-safety
        pass
        
    def transcribe_audio(
        self, 
        audio_file: bytes, 
        language: str = 'auto'
    ) -> Dict[str, any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_file: Audio file bytes (WAV, MP3, FLAC, etc.)
            language: Language code ('auto' for auto-detection or specific code like 'hi', 'en')
            
        Returns:
            Dict containing:
                - text: Transcribed text
                - language: Detected/specified language code
                - confidence: Confidence score (0-1)
                - error: Error message if transcription failed
        """
        try:
            # Create fresh recognizer instance for thread-safety
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 4000
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8
            
            # Create temporary file for audio processing
            # Detect file format and convert to WAV if needed
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_input:
                temp_input.write(audio_file)
                temp_input_path = temp_input.name
            
            # Convert to WAV format using pydub (supports MP3, FLAC, etc.)
            try:
                audio = AudioSegment.from_file(temp_input_path)
                temp_wav_path = temp_input_path + '.wav'
                audio.export(temp_wav_path, format='wav')
            except Exception as conv_error:
                logger.warning(f"Audio conversion failed, trying direct load: {conv_error}")
                # Try renaming to .wav and loading directly
                temp_wav_path = temp_input_path + '.wav'
                os.rename(temp_input_path, temp_wav_path)
                temp_input_path = None  # Mark as renamed
            
            try:
                # Load audio file
                with sr.AudioFile(temp_wav_path) as source:
                    # Adjust for ambient noise
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Record audio
                    audio_data = recognizer.record(source)
                
                # Determine language for recognition
                # If auto mode, try common Indian languages in order of likely usage
                if language == 'auto':
                    # Attempt recognition with multiple languages and pick best result
                    candidate_languages = ['hi', 'mr', 'en', 'ta', 'te', 'bn']
                    best_result = None
                    best_confidence = 0
                    
                    for lang_code in candidate_languages:
                        try:
                            result = recognizer.recognize_google(
                                audio_data,
                                language=lang_code,
                                show_all=True
                            )
                            if result and 'alternative' in result:
                                # Get top alternative with confidence
                                top_alt = result['alternative'][0]
                                confidence = top_alt.get('confidence', 0.5)
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                    best_result = {
                                        'text': top_alt['transcript'],
                                        'language': lang_code,
                                        'confidence': confidence
                                    }
                        except (sr.UnknownValueError, sr.RequestError):
                            continue
                    
                    if not best_result:
                        # Fall back to English if no result
                        transcribed_text = recognizer.recognize_google(audio_data, language='en')
                        detected_language = 'en'
                        confidence = 0.6
                    else:
                        transcribed_text = best_result['text']
                        detected_language = best_result['language']
                        confidence = best_result['confidence']
                else:
                    # Use specified language
                    recognition_language = language
                    transcribed_text = recognizer.recognize_google(
                        audio_data,
                        language=recognition_language,
                        show_all=False
                    )
                    detected_language = language
                    confidence = self._estimate_confidence(transcribed_text)
                
                logger.info(f"Successfully transcribed audio: language={detected_language}, confidence={confidence}")
                
                return {
                    'text': transcribed_text,
                    'language': detected_language,
                    'language_name': SUPPORTED_LANGUAGES.get(detected_language, 'Unknown'),
                    'confidence': confidence,
                    'error': None
                }
                
            finally:
                # Clean up temporary files
                if temp_input_path and os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                    
        except sr.UnknownValueError:
            logger.warning("Speech recognition could not understand audio")
            return {
                'text': None,
                'language': None,
                'language_name': None,
                'confidence': 0.0,
                'error': 'Could not understand audio. Please speak clearly.'
            }
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return {
                'text': None,
                'language': None,
                'language_name': None,
                'confidence': 0.0,
                'error': 'Speech recognition service unavailable. Please try again later.'
            }
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
            return {
                'text': None,
                'language': None,
                'language_name': None,
                'confidence': 0.0,
                'error': f'Transcription error: {str(e)}'
            }
    
    def translate_text(
        self, 
        text: str, 
        source_language: str = 'auto', 
        target_language: str = 'en'
    ) -> Dict[str, any]:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_language: Source language code ('auto' for auto-detection)
            target_language: Target language code (default: 'en')
            
        Returns:
            Dict containing:
                - translated_text: Translated text
                - source_language: Detected source language
                - target_language: Target language
                - original_text: Original text
                - error: Error message if translation failed
        """
        try:
            if not text or not text.strip():
                return {
                    'translated_text': None,
                    'source_language': None,
                    'source_language_name': None,
                    'target_language': None,
                    'target_language_name': None,
                    'original_text': text,
                    'error': 'Empty text provided'
                }
            
            # Perform translation (create new Translator instance for thread-safety)
            # googletrans 4.0.2 is async-only, so use asyncio.run() for synchronous context
            translator = Translator()
            
            # Wrap async translate call in asyncio.run for synchronous execution
            async def _do_translation():
                return await translator.translate(
                    text,
                    src=source_language,
                    dest=target_language
                )
            
            translation = asyncio.run(_do_translation())
            
            logger.info(f"Successfully translated text: {translation.src} -> {translation.dest}")
            
            return {
                'translated_text': translation.text,
                'source_language': translation.src,
                'source_language_name': SUPPORTED_LANGUAGES.get(translation.src, 'Unknown'),
                'target_language': translation.dest,
                'target_language_name': SUPPORTED_LANGUAGES.get(translation.dest, 'Unknown'),
                'original_text': text,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error translating text: {e}", exc_info=True)
            return {
                'translated_text': None,
                'source_language': None,
                'source_language_name': None,
                'target_language': None,
                'target_language_name': None,
                'original_text': text,
                'error': f'Translation error: {str(e)}'
            }
    
    def process_voice_grievance(
        self, 
        audio_file: bytes,
        preferred_language: str = 'auto'
    ) -> Dict[str, any]:
        """
        Complete pipeline: Transcribe audio and translate to English
        
        Args:
            audio_file: Audio file bytes
            preferred_language: Preferred language for transcription
            
        Returns:
            Dict containing:
                - original_text: Transcribed text in original language
                - translated_text: Translated text (English)
                - source_language: Detected/specified language
                - confidence: Transcription confidence score
                - manual_correction_needed: Boolean flag for low confidence
                - error: Error message if processing failed
        """
        try:
            # Step 1: Transcribe audio
            transcription_result = self.transcribe_audio(audio_file, preferred_language)
            
            if transcription_result['error']:
                return {
                    'original_text': None,
                    'translated_text': None,
                    'source_language': None,
                    'source_language_name': None,
                    'confidence': 0.0,
                    'manual_correction_needed': True,
                    'error': transcription_result['error']
                }
            
            original_text = transcription_result['text']
            source_language = transcription_result['language']
            confidence = transcription_result['confidence']
            
            # Step 2: Translate to English if not already in English
            translated_text = original_text
            if source_language != 'en':
                translation_result = self.translate_text(
                    original_text,
                    source_language=source_language,
                    target_language='en'
                )
                
                if translation_result['error']:
                    logger.warning(f"Translation failed, using original text: {translation_result['error']}")
                else:
                    translated_text = translation_result['translated_text']
            
            # Determine if manual correction is needed (low confidence)
            manual_correction_needed = confidence < 0.7
            
            return {
                'original_text': original_text,
                'translated_text': translated_text,
                'source_language': source_language,
                'source_language_name': transcription_result['language_name'],
                'confidence': confidence,
                'manual_correction_needed': manual_correction_needed,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error processing voice grievance: {e}", exc_info=True)
            return {
                'original_text': None,
                'translated_text': None,
                'source_language': None,
                'source_language_name': None,
                'confidence': 0.0,
                'manual_correction_needed': True,
                'error': f'Processing error: {str(e)}'
            }
    
    def _estimate_confidence(self, text: str) -> float:
        """
        Estimate confidence score based on transcribed text quality
        
        Args:
            text: Transcribed text
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not text or not text.strip():
            return 0.0
        
        # Heuristic-based confidence estimation
        confidence = 0.8  # Base confidence
        
        # Adjust based on text length (very short might be incomplete)
        if len(text.split()) < 3:
            confidence -= 0.2
        
        # Adjust based on special characters (too many might indicate poor transcription)
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    @staticmethod
    def get_supported_languages() -> Dict[str, str]:
        """Get dictionary of supported languages"""
        return SUPPORTED_LANGUAGES.copy()
    
    @staticmethod
    def is_language_supported(language_code: str) -> bool:
        """Check if a language is supported"""
        return language_code in SUPPORTED_LANGUAGES


# Singleton instance
_voice_service_instance = None

def get_voice_service() -> VoiceService:
    """Get or create VoiceService singleton instance"""
    global _voice_service_instance
    if _voice_service_instance is None:
        _voice_service_instance = VoiceService()
    return _voice_service_instance
