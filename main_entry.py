#!/usr/bin/env python3
"""
Real-Time Audio Translator - Main Entry Point
Captures system audio, transcribes with AI, and translates in real-time
"""

import sys
import os
import warnings
import traceback

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing_deps = []
    
    # Core audio dependencies
    try:
        import numpy
        import sounddevice
        import soundfile
    except ImportError as e:
        missing_deps.append(f"Audio processing: {e}")
    
    # AI dependencies
    try:
        import faster_whisper
    except ImportError:
        missing_deps.append("Whisper (install: pip install faster-whisper)")
    
    try:
        import transformers
        import torch
    except ImportError:
        missing_deps.append("Transformers (install: pip install transformers torch)")
    
    return missing_deps

def show_dependency_error(missing_deps):
    """Show dependency installation instructions"""
    print("=" * 60)
    print("MISSING DEPENDENCIES")
    print("=" * 60)
    print("Please install the following packages:\n")
    
    for dep in missing_deps:
        print(f"• {dep}")
    
    print("\nQuick install command:")
    print("pip install numpy sounddevice soundfile faster-whisper transformers torch")
    print("\nFor GPU support (recommended):")
    print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print("=" * 60)

def create_project_directories():
    """Ensure all required project directories exist"""
    directories = ['core', 'gui', 'utils']
    
    for directory in directories:
        dir_path = os.path.join(project_root, directory)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                # Create __init__.py files for Python packages
                init_file = os.path.join(dir_path, '__init__.py')
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        f.write(f'"""Package: {directory}"""\n')
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {e}")

def show_startup_info():
    """Display startup information"""
    print("=" * 60)
    print("🎤 REAL-TIME AUDIO TRANSLATOR")
    print("=" * 60)
    print("🚀 Starting application...")
    print(f"📁 Project directory: {project_root}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    
    # Check system info
    import platform
    print(f"💻 System: {platform.system()} {platform.release()}")
    
    # Check for GPU
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_count = torch.cuda.device_count()
        print(f"🔥 GPU support: {'Yes' if gpu_available else 'CPU only'}")
        if gpu_available:
            print(f"   GPUs detected: {gpu_count}")
            print(f"   Primary GPU: {torch.cuda.get_device_name(0)}")
    except:
        print("🔥 GPU support: Not available")
    
    print("=" * 60)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler for better error reporting"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow Ctrl+C to work normally
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    print("=" * 60)
    print("CRITICAL ERROR")
    print("=" * 60)
    print(f"Error type: {exc_type.__name__}")
    print(f"Error message: {str(exc_value)}")
    print("\nDetailed traceback:")
    print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    print("=" * 60)

def main():
    """Main entry point for the application"""
    try:
        # Setup global exception handling
        sys.excepthook = handle_exception
        
        # Show startup information
        show_startup_info()
        
        # Create project structure
        create_project_directories()
        
        # Check dependencies
        print("🔍 Checking dependencies...")
        missing_deps = check_dependencies()
        
        if missing_deps:
            print("❌ Missing dependencies detected!")
            show_dependency_error(missing_deps)
            return 1
        
        print("✅ All dependencies available!")
        
        # Import and create main application
        print("🚀 Loading application...")
        
        try:
            from gui.main_window import MainWindow
        except ImportError as e:
            print(f"❌ Error importing main window: {e}")
            print("Make sure all project files are in the correct directories.")
            return 1
        
        print("✅ Starting Real-Time Audio Translator...")
        
        # Create and run the application
        app = MainWindow()
        app.run()
        
        print("👋 Application closed normally")
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
        return 0
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        traceback.print_exc()
        return 1

def run_dependency_check():
    """Standalone dependency checker"""
    print("🔍 Real-Time Audio Translator - Dependency Check")
    print("=" * 50)
    
    missing_deps = check_dependencies()
    
    if not missing_deps:
        print("✅ All dependencies are installed!")
        print("✅ Ready to run the application!")
        return True
    else:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\nInstallation command:")
        print("pip install numpy sounddevice soundfile faster-whisper transformers torch")
        return False

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--check-deps', '-c']:
            # Just run dependency check
            success = run_dependency_check()
            sys.exit(0 if success else 1)
        elif sys.argv[1] in ['--help', '-h']:
            print("Real-Time Audio Translator")
            print("Usage:")
            print("  python main_entry.py          - Run the application")
            print("  python main_entry.py --check-deps  - Check dependencies only")
            print("  python main_entry.py --help   - Show this help")
            sys.exit(0)
    
    # Run the main application
    exit_code = main()
    sys.exit(exit_code)