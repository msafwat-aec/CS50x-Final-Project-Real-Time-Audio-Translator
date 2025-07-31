"""
Device Scanner - Discovers and tests audio input devices
"""
import sounddevice as sd
import numpy as np
import time
from typing import List, Dict, Any, Optional, Callable

class DeviceScanner:
    
    @staticmethod
    def get_all_devices() -> List[Dict[str, Any]]:
        """Get information about all audio devices on the system"""
        try:
            devices = sd.query_devices()
            device_list = []
            
            for i, device in enumerate(devices):
                device_info = {
                    'id': i,
                    'name': device['name'],
                    'max_input_channels': device['max_input_channels'],
                    'max_output_channels': device['max_output_channels'],
                    'default_samplerate': device['default_samplerate'],
                    'hostapi': device['hostapi']
                }
                device_list.append(device_info)
            
            return device_list
            
        except Exception as e:
            print(f"Error scanning devices: {e}")
            return []
    
    @staticmethod
    def get_input_devices() -> List[Dict[str, Any]]:
        """Get only devices that can capture audio (have input channels)"""
        all_devices = DeviceScanner.get_all_devices()
        return [device for device in all_devices if device['max_input_channels'] > 0]
    
    @staticmethod
    def get_default_input_device() -> Optional[Dict[str, Any]]:
        """Get the system's default input device"""
        try:
            default_device = sd.query_devices(kind='input')
            device_id = sd.default.device[0] if isinstance(sd.default.device, tuple) else sd.default.device
            
            return {
                'id': device_id,
                'name': default_device['name'],
                'max_input_channels': default_device['max_input_channels'],
                'default_samplerate': default_device['default_samplerate']
            }
        except Exception as e:
            print(f"Error getting default device: {e}")
            return None
    
    @staticmethod
    def test_device(device_id: int, duration: float = 3.0, 
                   callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Test an audio device by recording for a specified duration"""
        try:
            device_info = sd.query_devices(device_id)
            sample_rate = int(device_info['default_samplerate'])
            channels = min(2, device_info['max_input_channels'])
            
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=channels,
                device=device_id,
                dtype='float32'
            )
            
            start_time = time.time()
            max_level = 0
            
            while time.time() - start_time < duration:
                sd.wait()
                elapsed = time.time() - start_time
                
                if elapsed > 0.5:
                    current_samples = int(elapsed * sample_rate)
                    if current_samples < len(recording):
                        current_data = recording[:current_samples]
                        level = np.max(np.abs(current_data))
                        max_level = max(max_level, level)
                        
                        if callback:
                            callback(level, elapsed, duration)
                
                time.sleep(0.1)
            
            sd.wait()
            
            audio_data = recording.flatten()
            max_amplitude = np.max(np.abs(audio_data))
            mean_amplitude = np.mean(np.abs(audio_data))
            rms = np.sqrt(np.mean(audio_data**2))
            
            return {
                'success': max_amplitude > 0.001,
                'max_amplitude': float(max_amplitude),
                'mean_amplitude': float(mean_amplitude),
                'rms': float(rms),
                'sample_rate': sample_rate,
                'channels': channels,
                'device_name': device_info['name']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'max_amplitude': 0.0,
                'mean_amplitude': 0.0,
                'rms': 0.0
            }
    
    @staticmethod
    def is_device_available(device_id: int) -> bool:
        """Check if a specific device ID is available and working"""
        try:
            device_info = sd.query_devices(device_id)
            return device_info['max_input_channels'] > 0
        except:
            return False
    
    @staticmethod
    def get_recommended_settings(device_id: int) -> Dict[str, Any]:
        """Get recommended audio settings for a specific device"""
        try:
            device_info = sd.query_devices(device_id)
            
            return {
                'sample_rate': int(device_info['default_samplerate']),
                'channels': min(2, device_info['max_input_channels']),
                'suggested_threshold': 0.01,
                'suggested_gain': 1.0
            }
        except Exception as e:
            return {
                'sample_rate': 44100,
                'channels': 1, 
                'suggested_threshold': 0.01,
                'suggested_gain': 1.0
            }