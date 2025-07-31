"""
Configuration Manager - Handles saving and loading user settings
"""

import json
import os 
from typing import Dict, Any, Optional
from utils.constants import *

class ConfigManager:
    """
    Manages configuration settings for the Real-time Audio Translator.
    Loads settings from a JSON file and provides methods to access and update them.
    """
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Initializes the configManager with the specified configuration file.
        If the file does not exist, it creates a default configuration.
        """
        self.config_file = config_file 
        self.config = self._load_default_config()
        self.load_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """ 
        Create default configuration vales 
        Return a dictionary with default setting from constants file
        """

        return {
            # Audio Device Settings 
            "device_id": 0,
            "sample_rate": DEFAULT_SAMPLE_RATE,
            "channels": DEFAULT_CHANNELS,

            # Audio Processing Settings
            "energy_threshold": DEFAULT_ENERGY_THRESHOLD,
            "audio_gain": 1.0,
            "min_speech_duration": MIN_SPEECH_DURATION,
            "max_speech_duration": MAX_SPEECH_DURATION,
            "silence_timeout": SILENCE_TIMEOUT,

            # AI Model Settings
            "whisper_model": "tiny",
            "source_language": "auto",
            "target_language": "es",

            # GUI Settings
            "window_geometry": WINDOW_SIZE,
            "show_confidence": True,
            "auto_scroll": True,
        }
    
    def load_config(self) -> bool:
        """
        Load configurations from file
        Return boolan, True if loaded successfuly, False if using defaults"""

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)

                    # Merge saved config with defaults (handel new settings)
                    self.config.update(saved_config)
                    print(f"configuration loaded from {self.config_file}")
                    return True
            else:
                print(f"No configuration file found, using defaults")
                return False
        except Exception as e:
            print(f"Error loading config: {e}")
            print("using default congiguration")
            return False
        
    def save_config(self) -> bool:
        """
        Save current configuration to file
        Return True if saved successfuly, Fales otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                print(f"configuratoin saved to {self.config_file}")
                return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        return: configuration value or default    
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, save_immediately: bool = True) -> bool:
        """=This method is to set a configuration value"""

        self.config[key] = value

        if save_immediately:
            self.save_config()
        return True
    
    def update_multiple(self, updates: Dict[str, Any], save_immediately: bool = True) -> bool:
        """update multiple values at once by pass it dictionay"""

        self.config.update(updates)

        if save_immediately:
            self.save_config()
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """ get a copy of all configuration values as a dic"""

        return self.config.copy()
    
    def rest_to_defaults(self) -> bool:
        """Rest all configuration to default values"""

        self.config = self._load_default_config()
        return self.save_config()
    
    def validate_config(self) -> bool:
        """
        Validate the current configuration values
        retrun true if is Valid, if not , set it as default value
        """
        try:
            # Validate audio settings
            if not (8000 <= self.config["sample_rate"] <= 48000):
                print("⚠️ Invalid sample rate, using default")
                self.config["sample_rate"] = DEFAULT_SAMPLE_RATE
            
            if not (0.001 <= self.config["energy_threshold"] <= 1.0):
                print("⚠️ Invalid energy threshold, using default")
                self.config["energy_threshold"] = DEFAULT_ENERGY_THRESHOLD
            
            if not (0.1 <= self.config["audio_gain"] <= 10.0):
                print("⚠️ Invalid audio gain, using default")
                self.config["audio_gain"] = 1.0
            
            # Validate model selection
            if self.config["whisper_model"] not in WHISPER_MODELS:
                print("⚠️ Invalid Whisper model, using default")
                self.config["whisper_model"] = "tiny"
            
            # Validate languages
            if self.config["source_language"] not in LANGUAGES:
                print("⚠️ Invalid source language, using default")
                self.config["source_language"] = "auto"
            
            if self.config["target_language"] not in LANGUAGES:
                print("⚠️ Invalid target language, using default")
                self.config["target_language"] = "es"
            
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation error: {e}")
            return False

            

#Example usage for testing 

# Example usage (for testing)
if __name__ == "__main__":
    # Test the configuration manager
    config = ConfigManager()
    
    print("Current configuration:")
    for key, value in config.get_all().items():
        print(f"  {key}: {value}")
    
    # Test setting values
    config.set("device_id", 1)
    config.set("source_language", "it")
    
    print(f"\nDevice ID: {config.get('device_id')}")
    print(f"Source Language: {config.get('source_language')}")