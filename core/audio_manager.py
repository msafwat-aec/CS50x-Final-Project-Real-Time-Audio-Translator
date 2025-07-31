"""
Audio Manager - Handles real-time audio capture and processing
"""
import numpy as np
import sounddevice as sd
import threading
import queue
import time
from typing import Optional, Callable, List
from utils.constants import *

class AudioManager:
    
    def __init__(self, config: dict, callback: Optional[Callable] = None):
        """Initialize the audio manager with configuration and callback"""
        self.config = config
        self.callback = callback
        
        # Audio stream and processing
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
        # Speech detection buffers
        self.speech_buffer = []
        self.last_speech_time = 0
        self.current_audio_level = 0.0
        
        # Processing thread
        self.processing_thread = None
        self.stop_processing = False
        
        # Statistics
        self.stats = {
            'total_chunks': 0,
            'speech_detections': 0,
            'average_level': 0.0
        }
    
    def start_capture(self) -> bool:
        """Start real-time audio capture from the configured device"""
        try:
            device_id = self.config.get('device_id', 0)
            sample_rate = self.config.get('sample_rate', DEFAULT_SAMPLE_RATE)
            channels = self.config.get('channels', DEFAULT_CHANNELS)
            
            # Calculate chunk size for smooth processing
            chunk_size = int(sample_rate * AUDIO_CHUNK_DURATION)
            
            self.stream = sd.InputStream(
                device=device_id,
                channels=channels,
                samplerate=sample_rate,
                callback=self._audio_callback,
                blocksize=chunk_size,
                dtype='float32'
            )
            
            self.stream.start()
            self.is_recording = True
            
            # Start processing thread
            self.stop_processing = False
            self.processing_thread = threading.Thread(target=self._process_audio_loop)
            self.processing_thread.start()
            
            self._notify_callback('status', 'Audio capture started')
            return True
            
        except Exception as e:
            self._notify_callback('error', f'Failed to start audio capture: {e}')
            return False
    
    def stop_capture(self) -> dict:
        """Stop audio capture and return session statistics"""
        try:
            self.is_recording = False
            self.stop_processing = True
            
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            if self.processing_thread:
                self.processing_thread.join(timeout=2.0)
            
            self._notify_callback('status', 'Audio capture stopped')
            return self.stats.copy()
            
        except Exception as e:
            self._notify_callback('error', f'Error stopping capture: {e}')
            return self.stats.copy()
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio chunk"""
        if status:
            self._notify_callback('audio_status', str(status))
        
        # Convert to mono if stereo
        if len(indata.shape) > 1:
            audio_data = indata[:, 0]
        else:
            audio_data = indata.flatten()
        
        # Apply gain and clipping
        gain = self.config.get('audio_gain', 1.0)
        audio_data = audio_data * gain
        audio_data = np.clip(audio_data, -1.0, 1.0)
        
        # Add to processing queue
        self.audio_queue.put(audio_data.copy())
    
    def _process_audio_loop(self):
        """Main audio processing loop running in separate thread"""
        target_sample_rate = WHISPER_SAMPLE_RATE
        original_sample_rate = self.config.get('sample_rate', DEFAULT_SAMPLE_RATE)
        
        energy_threshold = self.config.get('energy_threshold', DEFAULT_ENERGY_THRESHOLD)
        min_speech_samples = int(target_sample_rate * MIN_SPEECH_DURATION)
        max_speech_samples = int(target_sample_rate * MAX_SPEECH_DURATION)
        silence_timeout = SILENCE_TIMEOUT
        
        while not self.stop_processing:
            try:
                # Get audio chunk with timeout
                audio_chunk = self.audio_queue.get(timeout=0.1)
                self.stats['total_chunks'] += 1
                
                # Downsample for Whisper if needed
                if original_sample_rate != target_sample_rate:
                    downsampled = self._downsample_audio(
                        audio_chunk, original_sample_rate, target_sample_rate
                    )
                else:
                    downsampled = audio_chunk
                
                # Calculate audio energy (RMS)
                rms_energy = np.sqrt(np.mean(downsampled ** 2))
                self.current_audio_level = rms_energy
                self.stats['average_level'] = (
                    self.stats['average_level'] * 0.95 + rms_energy * 0.05
                )
                
                # Notify GUI of audio level
                self._notify_callback('audio_level', rms_energy)
                
                current_time = time.time()
                
                # Speech detection logic
                if rms_energy > energy_threshold:
                    # Speech detected
                    self.last_speech_time = current_time
                    self.speech_buffer.extend(downsampled)
                    
                    # Force processing if buffer too long
                    if len(self.speech_buffer) > max_speech_samples:
                        self._process_speech_segment()
                        
                else:
                    # Silence detected
                    if (self.speech_buffer and 
                        current_time - self.last_speech_time > silence_timeout):
                        
                        # Process if we have enough speech
                        if len(self.speech_buffer) > min_speech_samples:
                            self._process_speech_segment()
                
            except queue.Empty:
                continue
            except Exception as e:
                self._notify_callback('error', f'Audio processing error: {e}')
    
    def _process_speech_segment(self):
        """Process accumulated speech segment"""
        if not self.speech_buffer:
            return
        
        try:
            # Convert to numpy array
            speech_array = np.array(self.speech_buffer, dtype=np.float32)
            
            # Normalize audio
            speech_array = self._normalize_audio(speech_array)
            
            # Send to AI processing
            self._notify_callback('speech_detected', {
                'audio_data': speech_array,
                'sample_rate': WHISPER_SAMPLE_RATE,
                'duration': len(speech_array) / WHISPER_SAMPLE_RATE
            })
            
            self.stats['speech_detections'] += 1
            
        except Exception as e:
            self._notify_callback('error', f'Speech processing error: {e}')
        finally:
            # Clear buffer
            self.speech_buffer.clear()
    
    def _downsample_audio(self, audio: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        """Downsample audio to target sample rate"""
        if orig_rate == target_rate:
            return audio
        
        # Simple linear interpolation downsampling
        ratio = target_rate / orig_rate
        new_length = int(len(audio) * ratio)
        
        return np.interp(
            np.linspace(0, len(audio) - 1, new_length),
            np.arange(len(audio)),
            audio
        )
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to prevent clipping and improve AI accuracy"""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val * 0.95
        return audio
    
    def get_current_level(self) -> float:
        """Get the current audio level (for GUI display)"""
        return self.current_audio_level
    
    def get_statistics(self) -> dict:
        """Get current session statistics"""
        return self.stats.copy()
    
    def update_config(self, new_config: dict):
        """Update configuration (requires restart for some settings)"""
        self.config.update(new_config)
    
    def _notify_callback(self, event_type: str, data):
        """Send notification to callback function if available"""
        if self.callback:
            try:
                self.callback(event_type, data)
            except Exception as e:
                print(f"Callback error: {e}")