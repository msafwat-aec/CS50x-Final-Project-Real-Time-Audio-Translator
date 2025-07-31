"""
AI Manager - Handles Whisper transcription and translation models
"""
import numpy as np
import threading
import time
from typing import Optional, Callable, Dict, Any, Tuple
from utils.constants import *

# Import AI libraries with fallback handling
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ faster-whisper not available")

try:
    from transformers import pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ transformers not available")

class AIManager:
    
    def __init__(self, config: dict, callback: Optional[Callable] = None):
        """Initialize AI manager with configuration and callback"""
        self.config = config
        self.callback = callback
        
        # AI Models
        self.whisper_model = None
        self.translator = None
        
        # Model loading status
        self.models_loaded = False
        self.loading_in_progress = False
        
        # Processing statistics
        self.stats = {
            'transcriptions_completed': 0,
            'translations_completed': 0,
            'total_processing_time': 0.0,
            'average_transcription_time': 0.0,
            'average_translation_time': 0.0,
            'errors': 0
        }
        
        # Threading for model operations
        self.processing_lock = threading.Lock()
    
    def load_models(self) -> bool:
        """Load Whisper and translation models"""
        if self.loading_in_progress:
            self._notify_callback('status', 'Models already loading...')
            return False
        
        if not WHISPER_AVAILABLE:
            self._notify_callback('error', 'Whisper not available. Install: pip install faster-whisper')
            return False
        
        self.loading_in_progress = True
        self._notify_callback('status', 'Loading AI models...')
        
        # Load in separate thread to prevent GUI blocking
        threading.Thread(target=self._load_models_thread, daemon=True).start()
        return True
    
    def _load_models_thread(self):
        """Load models in background thread"""
        try:
            # Load Whisper model
            self._notify_callback('status', 'Loading Whisper model...')
            self._load_whisper_model()
            
            # Load translation model
            if TRANSFORMERS_AVAILABLE:
                self._notify_callback('status', 'Loading translation model...')
                self._load_translation_model()
            
            self.models_loaded = True
            self._notify_callback('models_loaded', {
                'whisper': self.whisper_model is not None,
                'translator': self.translator is not None
            })
            
        except Exception as e:
            self._notify_callback('error', f'Failed to load models: {e}')
            self.stats['errors'] += 1
        finally:
            self.loading_in_progress = False
    
    def _load_whisper_model(self):
        """Load the Whisper speech recognition model"""
        model_size = self.config.get('whisper_model', 'tiny')
        
        # Determine device and compute type
        #device = "cuda" if TRANSFORMERS_AVAILABLE and torch.cuda.is_available() else "cpu"
        device = "cpu"
        compute_type = "int8" if device == "cuda" else "int8"
        
        self.whisper_model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=None  # Use default cache directory
        )
        
        self._notify_callback('status', f'Whisper {model_size} model loaded on {device}')
    
    def _load_translation_model(self):
        """Load the translation model based on language pair"""
        source_lang = self.config.get('source_language', 'en')
        target_lang = self.config.get('target_language', 'es')
        
        # Skip if auto-detect source (we'll determine language from Whisper)
        if source_lang == 'auto':
            source_lang = 'en'  # Default assumption
        
        # Get model name for language pair
        model_name = self._get_translation_model_name(source_lang, target_lang)
        
        if not model_name:
            self._notify_callback('status', f'No translation model for {source_lang}→{target_lang}')
            return
        
        try:
            #device = 0 if TRANSFORMERS_AVAILABLE and torch.cuda.is_available() else -1
            device = -1
            
            # FIXED: Remove deprecated return_all_scores parameter
            self.translator = pipeline(
                "translation",
                model=model_name,
                device=device
                # Removed: return_all_scores=False (deprecated)
            )
            
            self._notify_callback('status', f'Translation model loaded: {source_lang}→{target_lang}')
            
        except Exception as e:
            self._notify_callback('error', f'Translation model error: {e}')
            self.translator = None
    
    def _get_translation_model_name(self, source_lang: str, target_lang: str) -> Optional[str]:
        """Get the appropriate translation model name for language pair"""
        lang_pair = (source_lang, target_lang)
        
        # Check direct mapping
        if lang_pair in TRANSLATION_MODELS:
            return TRANSLATION_MODELS[lang_pair]
        
        # Fallback to multilingual model
        if source_lang == 'en':
            return "Helsinki-NLP/opus-mt-en-mul"
        
        return None
    
    def process_speech(self, audio_data: np.ndarray, sample_rate: int) -> bool:
        """Process speech audio through transcription and translation pipeline"""
        if not self.models_loaded or not self.whisper_model:
            self._notify_callback('error', 'Models not loaded')
            return False
        
        # Process in background thread to avoid blocking
        threading.Thread(
            target=self._process_speech_thread,
            args=(audio_data.copy(), sample_rate),
            daemon=True
        ).start()
        
        return True
    
    def _process_speech_thread(self, audio_data: np.ndarray, sample_rate: int):
        """Process speech in background thread"""
        with self.processing_lock:
            try:
                start_time = time.time()
                
                # Step 1: Transcription
                transcription_result = self._transcribe_audio(audio_data, sample_rate)
                transcription_time = time.time() - start_time
                
                if not transcription_result['text'].strip():
                    return  # No speech detected
                
                # Step 2: Translation
                translation_start = time.time()
                translation_result = self._translate_text(
                    transcription_result['text'],
                    transcription_result['detected_language']
                )
                translation_time = time.time() - translation_start
                
                # Update statistics
                total_time = time.time() - start_time
                self._update_stats(transcription_time, translation_time, total_time)
                
                # Send results
                self._notify_callback('translation_complete', {
                    'original_text': transcription_result['text'],
                    'translated_text': translation_result['text'],
                    'source_language': transcription_result['detected_language'],
                    'target_language': self.config.get('target_language', 'es'),
                    'confidence': transcription_result.get('confidence', 0.0),
                    'transcription_time': transcription_time,
                    'translation_time': translation_time,
                    'total_time': total_time
                })
                
            except Exception as e:
                self._notify_callback('error', f'Processing error: {e}')
                self.stats['errors'] += 1
    
    def _transcribe_audio(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Transcribe audio using Whisper"""
        try:
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Whisper expects audio in specific format
            if sample_rate != 16000:
                # This should already be 16kHz from AudioManager, but double-check
                audio_data = self._resample_audio(audio_data, sample_rate, 16000)
            
            # Configure transcription
            source_lang = self.config.get('source_language', 'auto')
            language = None if source_lang == 'auto' else source_lang
            
            # Transcribe
            segments, info = self.whisper_model.transcribe(
                audio_data,
                beam_size=1,  # Faster for real-time
                language=language,
                vad_filter=True,  # Voice activity detection
                word_timestamps=False  # We don't need word-level timing
            )
            
            # Extract text from segments
            text = " ".join(segment.text.strip() for segment in segments)
            
            result = {
                'text': text,
                'detected_language': info.language,
                'language_probability': info.language_probability
            }
            
            self.stats['transcriptions_completed'] += 1
            return result
            
        except Exception as e:
            raise Exception(f"Transcription failed: {e}")
    
    def _translate_text(self, text: str, detected_language: str) -> Dict[str, Any]:
        """Translate text using the translation model"""
        target_lang = self.config.get('target_language', 'es')
        
        # Skip translation if target language same as source
        if detected_language == target_lang:
            return {
                'text': text,
                'skipped': True,
                'reason': 'Same language'
            }
        
        # Skip if no translator available
        if not self.translator:
            return {
                'text': f"[Translation not available for {detected_language}→{target_lang}]",
                'skipped': True,
                'reason': 'No translator'
            }
        
        try:
            # Perform translation
            translation_result = self.translator(text)
            
            # Handle the result - it should be a list with translation_text key
            if isinstance(translation_result, list) and len(translation_result) > 0:
                translated_text = translation_result[0]['translation_text']
            else:
                translated_text = str(translation_result)
            
            self.stats['translations_completed'] += 1
            
            return {
                'text': translated_text,
                'skipped': False
            }
            
        except Exception as e:
            return {
                'text': f"[Translation error: {e}]",
                'skipped': True,
                'reason': str(e)
            }
    
    def _resample_audio(self, audio: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        """Simple audio resampling using linear interpolation"""
        if orig_rate == target_rate:
            return audio
        
        ratio = target_rate / orig_rate
        new_length = int(len(audio) * ratio)
        
        return np.interp(
            np.linspace(0, len(audio) - 1, new_length),
            np.arange(len(audio)),
            audio
        )
    
    def _update_stats(self, transcription_time: float, translation_time: float, total_time: float):
        """Update processing statistics"""
        self.stats['total_processing_time'] += total_time
        
        # Update rolling averages
        count = self.stats['transcriptions_completed']
        if count > 0:
            self.stats['average_transcription_time'] = (
                (self.stats['average_transcription_time'] * (count - 1) + transcription_time) / count
            )
        
        count = self.stats['translations_completed']
        if count > 0:
            self.stats['average_translation_time'] = (
                (self.stats['average_translation_time'] * (count - 1) + translation_time) / count
            )
    
    def update_config(self, new_config: dict):
        """Update configuration and reload models if needed"""
        old_whisper_model = self.config.get('whisper_model', 'tiny')
        old_source_lang = self.config.get('source_language', 'auto')
        old_target_lang = self.config.get('target_language', 'es')
        
        self.config.update(new_config)
        
        # Check if we need to reload models
        new_whisper_model = self.config.get('whisper_model', 'tiny')
        new_source_lang = self.config.get('source_language', 'auto')
        new_target_lang = self.config.get('target_language', 'es')
        
        if (new_whisper_model != old_whisper_model and self.models_loaded):
            self._notify_callback('status', 'Whisper model changed, reloading...')
            self.models_loaded = False
            self.load_models()
        
        elif ((new_source_lang != old_source_lang or new_target_lang != old_target_lang) 
              and self.models_loaded and TRANSFORMERS_AVAILABLE):
            self._notify_callback('status', 'Language changed, reloading translator...')
            self._load_translation_model()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.stats.copy()
    
    def is_ready(self) -> bool:
        """Check if AI models are loaded and ready"""
        return self.models_loaded and self.whisper_model is not None
    
    def _notify_callback(self, event_type: str, data: Any):
        """Send notification to callback function"""
        if self.callback:
            try:
                self.callback(event_type, data)
            except Exception as e:
                print(f"AI Manager callback error: {e}")