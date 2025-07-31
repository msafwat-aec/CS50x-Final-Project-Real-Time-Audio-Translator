"""
Event Handlers - All event handling logic for the Real-Time Audio Translator
Separated from main_window.py for better maintainability
Enhanced with streaming text effect and checkbox filtering
"""
import tkinter as tk
from tkinter import messagebox
import threading
from typing import Dict, Any, List
from datetime import datetime
import time
import queue

from core.device_scanner import DeviceScanner
from core.audio_manager import AudioManager

class EventHandlers:
    
    def __init__(self, main_window):
        """Initialize event handlers with reference to main window"""
        self.main_window = main_window
        # Create shortcuts for commonly used components
        self.root = main_window.root
        self.config_manager = main_window.config_manager
        self.colors = main_window.COLORS
        
        # Streaming effect queue and state
        self.streaming_queue = queue.Queue()
        self.is_streaming = False
        self.streaming_speed = 30  # milliseconds between characters
        
        # Start the streaming processor
        self.start_streaming_processor()
    
    # ======================== STREAMING EFFECT ========================
    
    def start_streaming_processor(self):
        """Start the background thread that processes streaming messages"""
        def process_stream():
            while True:
                try:
                    # Get next message from queue (blocks until available)
                    message_data = self.streaming_queue.get()
                    
                    if message_data is None:  # Shutdown signal
                        break
                    
                    # Extract message details
                    message = message_data['message']
                    tag = message_data['tag']
                    stream = message_data.get('stream', False)
                    
                    if stream and tag in ['original', 'translation']:
                        # Stream the message character by character
                        self._stream_message(message, tag)
                    else:
                        # Display immediately
                        self._display_message_immediate(message, tag)
                    
                except Exception as e:
                    print(f"Streaming processor error: {e}")
        
        # Start background thread
        self.streaming_thread = threading.Thread(target=process_stream, daemon=True)
        self.streaming_thread.start()
    
    def _stream_message(self, message: str, tag: str):
        """Stream a message in chunks with natural speech pauses like live transcription"""
        # Check if message should be displayed
        if not self._should_display_message(message, tag):
            return
            
        self.is_streaming = True
        
        # Show typing indicator (like someone is speaking)
        def show_typing():
            if self.root.winfo_exists():
                self.main_window.output_text.insert(tk.END, "... ", tag)
                self.main_window.output_text.see(tk.END)
        
        self.root.after(0, show_typing)
        time.sleep(0.4)  # Brief pause to show typing indicator
        
        # Clear typing indicator
        def clear_typing():
            if self.root.winfo_exists():
                # Remove the "... " (4 characters)
                current_pos = self.main_window.output_text.index(tk.END)
                self.main_window.output_text.delete("end-5c", "end-1c")
        
        self.root.after(0, clear_typing)
        
        # Split message into natural chunks (phrases)
        import re
        
        # Multiple patterns for more natural chunking
        # First try to split by punctuation and common conjunctions
        chunk_patterns = [
            # Split by punctuation but keep it with the chunk
            r'([^,;:.!?]+[,;:.!?])',
            # Split by conjunctions
            r'(.+?(?:\s+(?:and|or|but|so|then|because|while|when|if|that|which|who)\s+))',
            # Fallback: split by 3-5 word groups
            r'(\S+(?:\s+\S+){2,4})'
        ]
        
        chunks = []
        remaining_text = message
        
        # Try to split using punctuation first
        punctuation_chunks = re.findall(r'([^,;:.!?]+[,;:.!?]?\s*)', message)
        if punctuation_chunks and len(punctuation_chunks) > 1:
            chunks = punctuation_chunks
        else:
            # If no good punctuation splits, use word groups
            words = message.split()
            chunk_size = 4  # Average words per chunk
            chunks = []
            
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                chunks.append(chunk)
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            # Check if we should still display
            if not self._should_display_message(message, tag):
                break
            
            # Clean up the chunk
            chunk = chunk.strip()
            if not chunk:
                continue
            
            # Calculate dynamic pause based on chunk content
            chunk_length = len(chunk.split())
            base_pause = 0.2  # Base pause between chunks
            
            # Adjust pause based on punctuation and length
            if chunk.rstrip().endswith(('.', '!', '?')):
                pause_time = 0.8  # Longer pause after sentences
            elif chunk.rstrip().endswith(','):
                pause_time = 0.4  # Medium pause after commas
            elif chunk.rstrip().endswith(':'):
                pause_time = 0.5  # Medium-long pause after colons
            else:
                # Variable pause based on chunk length
                pause_time = base_pause + (chunk_length * 0.05)
                pause_time = min(pause_time, 0.6)  # Cap maximum pause
            
            # For more realism, add slight randomization to pauses
            import random
            pause_time *= random.uniform(0.8, 1.2)
            
            # Display the entire chunk at once (like speech recognition)
            def add_chunk(c=chunk, t=tag, is_last=(i == len(chunks) - 1)):
                if self.root.winfo_exists():
                    self.main_window.output_text.insert(tk.END, c, t)
                    # Add space after chunk if not last chunk and doesn't already end with space
                    if not is_last and not c.endswith(' '):
                        self.main_window.output_text.insert(tk.END, ' ', t)
                    self.main_window.output_text.see(tk.END)
                    
                    # Flash cursor to simulate active transcription
                    self.main_window.output_text.mark_set("insert", tk.END)
            
            self.root.after(0, add_chunk)
            
            # Pause between chunks (simulating speech gaps)
            if i < len(chunks) - 1:
                # Occasionally add a longer pause (like speaker thinking)
                if random.random() < 0.15:  # 15% chance of longer pause
                    time.sleep(pause_time * 1.5)
                else:
                    time.sleep(pause_time)
        
        # Add newline at the end with a small delay
        time.sleep(0.2)
        def add_newline():
            if self.root.winfo_exists():
                self.main_window.output_text.insert(tk.END, '\n')
                self.main_window.output_text.see(tk.END)
        
        self.root.after(0, add_newline)
        self.is_streaming = False
    
    def _display_message_immediate(self, message: str, tag: str):
        """Display a message immediately without streaming"""
        def update_gui():
            if self.root.winfo_exists() and self._should_display_message(message, tag):
                self.main_window.output_text.insert(tk.END, f"{message}\n", tag)
                self.main_window.output_text.see(tk.END)
        
        self.root.after(0, update_gui)
    
    def _should_display_tag(self, tag: str) -> bool:
        """Check if a message with the given tag should be displayed based on checkbox states"""
        # First check if logs are enabled at all
        if not self.main_window.var_show_logs.get() and tag in ['info', 'error']:
            # Only show error messages even if logs are disabled
            if tag == 'error':
                return True
            return False
        
        if tag == 'timestamp':
            return self.main_window.var_show_timestamp.get()
        elif tag == 'original':
            return self.main_window.var_show_original.get()
        elif tag == 'translation':
            return True  # Always show translations
        else:
            return True  # Show all other messages by default
    
    def _should_display_message(self, message: str, tag: str) -> bool:
        """Check if a specific message should be displayed based on content and checkbox states"""
        # Check process time messages
        if 'Processing time' in message and not self.main_window.var_show_process_time.get():
            return False
        
        # Use tag-based filtering
        return self._should_display_tag(tag)
    
    # ======================== CALLBACK HANDLERS ========================
    
    def handle_audio_events(self, event_type: str, data):
        """Handle events from the audio manager"""
        def update_gui():
            try:
                if event_type == 'audio_level':
                    # Update audio level meter
                    self.main_window.current_audio_level.set(min(data * 10, 1.0))
                    self.main_window.level_label.config(text=f"{data:.3f}")
                
                elif event_type == 'speech_detected':
                    # Send audio to AI for processing
                    if self.main_window.ai_manager and self.main_window.ai_manager.is_ready():
                        self.main_window.ai_manager.process_speech(data['audio_data'], data['sample_rate'])
                        
                        duration = data['duration']
                        self.add_output_message(f"🎯 Speech detected ({duration:.1f}s) - processing...", "info")
                
                elif event_type == 'status':
                    self.update_status(data)
                
                elif event_type == 'error':
                    self.add_output_message(f"❌ Audio error: {data}", "error")
            
            except Exception as e:
                print(f"Audio event handler error: {e}")
        
        # Schedule the GUI update on the main thread
        if self.root.winfo_exists():
            self.root.after(0, update_gui)
    
    def handle_ai_events(self, event_type: str, data):
        """Handle events from the AI manager"""
        def update_gui():
            try:
                if event_type == 'models_loaded':
                    self.main_window.models_loaded = True
                    self.main_window.load_models_btn.config(state=tk.NORMAL)
                    self.main_window.load_models_btn.config(text="✅ Models Loaded")
                    self.main_window.load_models_btn.config(style='Success.TButton')
                    self.main_window.start_stop_btn.config(state=tk.NORMAL)
                    
                    whisper_status = "✅" if data['whisper'] else "❌"
                    translator_status = "✅" if data['translator'] else "❌"
                    
                    self.add_output_message(f"🤖 AI Models loaded:", "info")
                    self.add_output_message(f"   Whisper: {whisper_status}", "info")
                    self.add_output_message(f"   Translator: {translator_status}", "info")
                    self.update_status("AI models ready!")
                    
                    messagebox.showinfo("Success", "🤖 AI models loaded successfully!\n\nYou can now start translation.")
                
                elif event_type == 'translation_complete':
                    # Display translation results with streaming effect
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    original = data['original_text']
                    translated = data['translated_text']
                    source_lang = data['source_language']
                    target_lang = data['target_language']
                    confidence = data.get('confidence', 0.0)
                    total_time = data['total_time']
                    
                    # Add messages to streaming queue
                    if self.main_window.var_show_timestamp.get():
                        self.add_output_message(f"\n[{timestamp}] 🎯 Translation #{self.main_window.ai_manager.stats['transcriptions_completed']}", "timestamp")
                    
                    if self.main_window.var_show_original.get():
                        self.add_output_message(f"🗣️...Original({source_lang}): {original}", "original", stream=True)
                    
                    # Always show translation with streaming effect
                    self.add_output_message(f"🌐Translation({target_lang}): {translated}", "translation", stream=True)
                    
                    if self.main_window.var_show_process_time.get():
                        self.add_output_message(f"⏱️  Processing time: {total_time:.2f}s", "info")
                    
                    if confidence > 0:
                        self.add_output_message(f"📊 Confidence: {confidence:.1%}", "info")
                
                elif event_type == 'status':
                    self.update_status(data)
                
                elif event_type == 'error':
                    self.add_output_message(f"❌ AI error: {data}", "error")
            
            except Exception as e:
                print(f"AI event handler error: {e}")
        
        # Schedule the GUI update on the main thread
        if self.root.winfo_exists():
            self.root.after(0, update_gui)
    
    # ======================== GUI EVENT HANDLERS ========================
    
    def on_device_selected(self, event=None):
        """Handle device selection from combo box"""
        selected_text = self.main_window.device_combo.get()
        self.main_window.selected_device.set(selected_text)
        
        # Extract device ID and update config
        if selected_text:
            try:
                device_id = int(selected_text.split(':')[0])
                self.config_manager.set('device_id', device_id, save_immediately=False)
                self.add_output_message(f"📱 Selected device: {selected_text}", "info")
            except ValueError:
                pass  # Invalid selection, ignore
    
    def on_source_language_change(self, event=None):
        """Handle source language combo change"""
        try:
            selected = self.main_window.source_combo.get()
            self.main_window.source_language.set(selected)
            # Auto-save configuration when language changes
            self.save_configuration()
        except Exception as e:
            print(f"ERROR: Source language change error: {e}")

    def on_target_language_change(self, event=None):
        """Handle target language combo change"""
        try:
            selected = self.main_window.target_combo.get()
            self.main_window.target_language.set(selected)
            # Auto-save configuration when language changes
            self.save_configuration()
        except Exception as e:
            print(f"ERROR: Target language change error: {e}")
    
    def on_threshold_change(self, value):
        """Handle threshold slider changes"""
        threshold = float(value)
        self.main_window.threshold_label.config(text=f"{threshold:.3f}")
        
        # Update audio manager if running
        if self.main_window.audio_manager:
            self.main_window.audio_manager.update_config({'energy_threshold': threshold})
    
    def on_gain_change(self, value):
        """Handle gain slider changes"""
        gain = float(value)
        self.main_window.gain_label.config(text=f"{gain:.1f}x")
        
        # Update audio manager if running
        if self.main_window.audio_manager:
            self.main_window.audio_manager.update_config({'audio_gain': gain})
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop streaming processor
            self.streaming_queue.put(None)  # Shutdown signal
            
            # Stop any running operations
            if self.main_window.is_running:
                self.stop_translation()
            
            # Save current configuration
            self.save_configuration()
            
            # Add a simple goodbye message BEFORE destroying
            try:
                self.add_output_message("👋 Application closing...", "info")
            except:
                pass  # Ignore if widgets are already destroyed
            
            # Actually close the application
            self.root.destroy()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
            # Force close even if there are errors
            try:
                self.root.destroy()
            except:
                pass
    
    # ======================== UTILITY METHODS ========================
    
    def add_output_message(self, message: str, tag: str = "info", stream: bool = False):
        """Add a message to the output display with optional streaming effect"""
        # Add to streaming queue
        self.streaming_queue.put({
            'message': message,
            'tag': tag,
            'stream': stream
        })
    
    def update_status(self, message: str):
        """Update the status bar message"""
        try:
            self.main_window.status_text.set(message)
            self.root.update_idletasks()
        except Exception as e:
            print(f"ERROR: Failed to update status: {e}")
    
    def refresh_output_visibility(self):
        """Refresh the output text based on checkbox states (called when checkboxes change)"""
        # Clear and rebuild the output based on stored messages
        # This would require storing all messages in a list, which is a more complex implementation
        # For now, new messages will respect the checkbox states
        pass
    
    def update_gui_from_config(self):
        """Update GUI controls to match current configuration"""
        try:
            # Set language selections
            source_lang = self.config_manager.get('source_language')
            target_lang = self.config_manager.get('target_language')
            whisper_model = self.config_manager.get('whisper_model')
            
            # Find and set combo box values
            for i, value in enumerate(self.main_window.source_combo['values']):
                if value.startswith(source_lang):
                    self.main_window.source_combo.current(i)
                    self.main_window.source_language.set(value)
                    break
            
            for i, value in enumerate(self.main_window.target_combo['values']):
                if value.startswith(target_lang):
                    self.main_window.target_combo.current(i)
                    self.main_window.target_language.set(value)
                    break
            
            for i, value in enumerate(self.main_window.model_combo['values']):
                if value.startswith(whisper_model):
                    self.main_window.model_combo.current(i)
                    self.main_window.whisper_model.set(value)
                    break
                    
        except Exception as e:
            print(f"ERROR: Failed to update GUI from config: {e}")
    
    # ======================== ACTION HANDLERS ========================
    
    def clear_output(self):
        """Clear the translation output display"""
        self.main_window.output_text.delete(1.0, tk.END)
        self.add_output_message("🗑️ Output cleared", "info")
        self.update_status("Output cleared")
    
    def show_statistics(self):
        """Display performance statistics"""
        if self.main_window.ai_manager:
            ai_stats = self.main_window.ai_manager.get_statistics()
            
            stats_text = "📊 AI Performance Statistics\n"
            stats_text += "=" * 35 + "\n"
            stats_text += f"Transcriptions completed: {ai_stats['transcriptions_completed']}\n"
            stats_text += f"Translations completed: {ai_stats['translations_completed']}\n"
            stats_text += f"Average transcription time: {ai_stats['average_transcription_time']:.2f}s\n"
            stats_text += f"Average translation time: {ai_stats['average_translation_time']:.2f}s\n"
            stats_text += f"Total processing time: {ai_stats['total_processing_time']:.2f}s\n"
            stats_text += f"Errors encountered: {ai_stats['errors']}\n"
            
            if self.main_window.audio_manager:
                audio_stats = self.main_window.audio_manager.get_statistics()
                stats_text += "\n🎤 Audio Statistics\n"
                stats_text += "=" * 20 + "\n"
                stats_text += f"Speech detections: {audio_stats['speech_detections']}\n"
                stats_text += f"Audio chunks processed: {audio_stats['total_chunks']}\n"
                stats_text += f"Average audio level: {audio_stats['average_level']:.4f}\n"
            
            messagebox.showinfo("Statistics", stats_text)
        else:
            messagebox.showinfo("Statistics", "No statistics available - AI models not loaded yet.")
    
    def refresh_devices(self):
        """Scan and refresh the list of available audio devices"""
        try:
            self.update_status("Scanning audio devices...")
            
            # Get input devices
            devices = DeviceScanner.get_input_devices()
            
            if not devices:
                self.add_output_message("❌ No audio input devices found!", "error")
                messagebox.showwarning("No Devices", "No audio input devices found!\n\nCheck your audio drivers and connections.")
                return
            
            # Update combo box
            device_names = [f"{device['id']}: {device['name']}" for device in devices]
            self.main_window.device_combo['values'] = device_names
            
            # Set current device from config
            current_device_id = self.config_manager.get('device_id', 0)
            for i, device in enumerate(devices):
                if device['id'] == current_device_id:
                    self.main_window.device_combo.current(i)
                    break
            else:
                # If configured device not found, select first available
                if devices:
                    self.main_window.device_combo.current(0)
                    self.config_manager.set('device_id', devices[0]['id'])
            
            self.add_output_message(f"✅ Found {len(devices)} audio input devices", "info")
            self.update_status(f"Found {len(devices)} input devices")
            
        except Exception as e:
            self.add_output_message(f"❌ Error scanning devices: {e}", "error")
            self.update_status("Error scanning devices")
    
    def test_device(self):
        """Test the selected audio device"""
        # Get the current selection directly from the combo box
        selected_text = self.main_window.device_combo.get()
        
        if not selected_text or selected_text.strip() == "":
            messagebox.showwarning("No Device", "Please select an audio device first")
            return
        
        try:
            # Extract device ID from selection
            device_id = int(selected_text.split(':')[0])
            
            self.add_output_message(f"🧪 Testing device {device_id}... Speak or play audio!", "info")
            self.update_status("Testing device - play some audio...")
            
            def level_callback(level, elapsed, total):
                """Update GUI during device test"""
                self.main_window.current_audio_level.set(min(level * 10, 1.0))  # Scale for visibility
                progress = (elapsed / total) * 100
                self.update_status(f"Testing device... {progress:.0f}% - Level: {level:.4f}")
                self.root.update_idletasks()
            
            # Run test in background thread
            def test_thread():
                result = DeviceScanner.test_device(device_id, duration=5.0, callback=level_callback)
                
                # Update GUI from main thread
                def show_results():
                    self.main_window.current_audio_level.set(0)
                    
                    if result['success']:
                        self.add_output_message(f"✅ Device test successful!", "info")
                        self.add_output_message(f"   Max volume: {result['max_amplitude']:.4f}", "info")
                        self.add_output_message(f"   RMS level: {result['rms']:.4f}", "info")
                        
                        # Suggest optimal threshold
                        suggested_threshold = min(result['rms'] * 1.5, 0.05)
                        self.main_window.audio_threshold.set(suggested_threshold)
                        self.main_window.threshold_label.config(text=f"{suggested_threshold:.3f}")
                        
                        messagebox.showinfo("Test Success", 
                                          f"✅ Device working properly!\n\n"
                                          f"Max amplitude: {result['max_amplitude']:.4f}\n"
                                          f"RMS level: {result['rms']:.4f}\n\n"
                                          f"Threshold adjusted to: {suggested_threshold:.3f}")
                    else:
                        error_msg = result.get('error', 'No audio detected')
                        self.add_output_message(f"❌ Device test failed: {error_msg}", "error")
                        messagebox.showerror("Test Failed", f"❌ Device test failed:\n{error_msg}")
                    
                    self.update_status("Device test completed")
                
                self.root.after(0, show_results)
            
            threading.Thread(target=test_thread, daemon=True).start()
            
        except ValueError as e:
            self.add_output_message(f"❌ Invalid device selection: {selected_text}", "error")
            messagebox.showerror("Selection Error", f"Invalid device selection:\n{selected_text}")
        except Exception as e:
            self.add_output_message(f"❌ Device test error: {e}", "error")
            messagebox.showerror("Test Error", f"Device test failed:\n{e}")
    
    def save_configuration(self):
        """Save current GUI settings to configuration"""
        try:
            # Extract values from GUI
            updates = {}
            
            # Device selection
            if self.main_window.selected_device.get():
                device_id = int(self.main_window.selected_device.get().split(':')[0])
                updates['device_id'] = device_id
            
            # Language settings - Extract language codes properly
            if self.main_window.source_language.get():
                source_lang = self.main_window.source_language.get().split(' - ')[0]
                updates['source_language'] = source_lang
            
            if self.main_window.target_language.get():
                target_lang = self.main_window.target_language.get().split(' - ')[0]
                updates['target_language'] = target_lang
            
            if self.main_window.whisper_model.get():
                model = self.main_window.whisper_model.get().split(' - ')[0]
                updates['whisper_model'] = model
            
            # Audio settings
            updates['energy_threshold'] = self.main_window.audio_threshold.get()
            updates['audio_gain'] = self.main_window.audio_gain.get()
            
            # Update configuration
            self.config_manager.update_multiple(updates)
            
            # Update AI manager if exists
            if self.main_window.ai_manager:
                self.main_window.ai_manager.update_config(updates)
            
            self.add_output_message("💾 Configuration saved", "info")
            self.update_status("Configuration saved")
            
        except Exception as e:
            self.add_output_message(f"❌ Error saving configuration: {e}", "error")
            messagebox.showerror("Save Error", f"Failed to save configuration:\n{e}")
    
    def load_models(self):
        """Load AI models (Whisper and translation)"""
        if self.main_window.ai_manager.loading_in_progress:
            messagebox.showinfo("Loading", "Models are already being loaded...")
            return
        
        # Save current configuration first
        self.save_configuration()
        
        # Disable load button during loading
        self.main_window.load_models_btn.config(state=tk.DISABLED)
        self.main_window.load_models_btn.config(text="🔄 Loading Models...")
        self.main_window.load_models_btn.config(style='Warning.TButton')
        
        # Start loading
        self.add_output_message("🤖 Loading AI models... This may take a few minutes on first run.", "info")
        success = self.main_window.ai_manager.load_models()
        
        if not success:
            self.main_window.load_models_btn.config(state=tk.NORMAL)
            self.main_window.load_models_btn.config(text="🤖 Load AI Models")
            self.main_window.load_models_btn.config(style='Accent.TButton')
    
    def toggle_translation(self):
        """Start or stop the translation process"""
        if not self.main_window.is_running:
            self.start_translation()
        else:
            self.stop_translation()
    
    def start_translation(self):
        """Start real-time translation"""
        if not self.main_window.ai_manager.is_ready():
            messagebox.showerror("Not Ready", "Please load AI models first!")
            return
        
        # Get current device selection directly from combo box
        selected_text = self.main_window.device_combo.get()
        if not selected_text or selected_text.strip() == "":
            messagebox.showwarning("No Device", "Please select an audio device first!")
            return
        
        try:
            # Save current settings
            self.save_configuration()
            
            # Create audio manager with current config
            self.main_window.audio_manager = AudioManager(
                self.config_manager.get_all(),
                callback=self.handle_audio_events
            )
            
            # Start audio capture
            if self.main_window.audio_manager.start_capture():
                self.main_window.is_running = True
                self.main_window.start_stop_btn.config(text="⏹️ Stop Translation")
                self.main_window.start_stop_btn.config(style='Warning.TButton')
                self.main_window.load_models_btn.config(state=tk.DISABLED)
                
                self.add_output_message("🎤 Translation started! Speak or play audio with speech...", "info")
                self.update_status("Translation active - listening for speech...")
            else:
                messagebox.showerror("Start Error", "Failed to start audio capture!")
        
        except Exception as e:
            self.add_output_message(f"❌ Failed to start translation: {e}", "error")
            messagebox.showerror("Start Error", f"Failed to start translation:\n{e}")
    
    def stop_translation(self):
        """Stop real-time translation"""
        if self.main_window.audio_manager:
            stats = self.main_window.audio_manager.stop_capture()
            self.main_window.audio_manager = None
            
            # Show session statistics
            if stats['speech_detections'] > 0:
                self.add_output_message(f"📊 Session complete:", "info")
                self.add_output_message(f"   Speech segments processed: {stats['speech_detections']}", "info")
                self.add_output_message(f"   Total audio chunks: {stats['total_chunks']}", "info")
                self.add_output_message(f"   Average audio level: {stats['average_level']:.4f}", "info")
        
        self.main_window.is_running = False
        self.main_window.start_stop_btn.config(text="▶️ Start Translation")
        self.main_window.start_stop_btn.config(style='Success.TButton')
        self.main_window.load_models_btn.config(state=tk.NORMAL)
        self.main_window.current_audio_level.set(0)