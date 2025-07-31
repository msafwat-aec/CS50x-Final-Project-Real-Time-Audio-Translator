"""
Constants and configuration values for the Real-Time Audio Translator
"""

# Audio Configuration
DEFAULT_SAMPLE_RATE = 44100  # Standard audio quality (CD quality)
WHISPER_SAMPLE_RATE = 16000  # Whisper expects 16kHz audio
DEFAULT_CHANNELS = 1         # Mono audio (easier to process)
AUDIO_CHUNK_DURATION = 0.05  # Process audio in 50ms chunks (smooth real-time)

# Voice Activity Detection
DEFAULT_ENERGY_THRESHOLD = 0.01  # Minimum audio level to consider as speech
MIN_SPEECH_DURATION = 0.3        # Minimum seconds of speech to process
MAX_SPEECH_DURATION = 5.0        # Maximum seconds before forcing processing
SILENCE_TIMEOUT = 0.8            # Seconds of silence before processing speech

# Whisper Models (trade-off between speed and accuracy)
WHISPER_MODELS = {
    "tiny": "Fastest, least accurate",
    "base": "Good balance",
    "small": "Better accuracy",
    "medium": "High accuracy",
    "large": "Best accuracy, slowest"
}

# Supported Languages
LANGUAGES = {
    "auto": "Auto-detect",
    "en": "English",
    "es": "Spanish", 
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ar": "Arabic",
    "hi": "Hindi"
}

# Translation Model Mapping (Helsinki NLP models)
TRANSLATION_MODELS = {
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr", 
    ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
    ("en", "it"): "Helsinki-NLP/opus-mt-en-it",
    ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("it", "en"): "Helsinki-NLP/opus-mt-it-en",
    ("en", "ar"): "Helsinki-NLP/opus-mt-en-ar",
    # Add more as needed
}

# GUI Configuration
WINDOW_SIZE = "900x930"
WINDOW_TITLE = "Real-Time Audio Translator"

# File Paths
CONFIG_FILE = "config.json"