"""
Main Window - Primary GUI interface for the Real-Time Audio Translator
Modern Windows 11 Light Theme with clean, flat design
Enhanced with checkbox controls for output filtering
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
from datetime import datetime

# Import our core components
from core.config_manager import ConfigManager
from core.ai_manager import AIManager
from utils.constants import *
from gui.event_handlers import EventHandlers

class MainWindow:
    
    # Modern Windows 11 Light Theme Colors
    COLORS = {
        'bg_primary': '#fafafa',        # Main window background
        'bg_secondary': '#ffffff',      # Frame backgrounds
        'bg_tertiary': '#f5f5f5',       # Input/text backgrounds
        'border': '#e0e0e0',            # Border color
        'text_primary': '#1f1f1f',      # Main text
        'text_secondary': '#6d6d6d',    # Secondary text
        'accent_blue': '#0078d4',       # Primary accent
        'accent_green': '#107c10',      # Success color
        'accent_orange': '#ff8c00',     # Warning color
        'accent_red': '#d83b01',        # Error color
        'hover': '#f0f0f0',             # Hover state
    }
    
    def __init__(self):
        """Initialize the main application window"""
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        # Apply modern Windows 11 styling FIRST (before creating widgets)
        self.setup_modern_styling()
        
        # Core components
        self.config_manager = ConfigManager()
        self.audio_manager = None
        self.ai_manager = None
        
        # Application state
        self.is_running = False
        self.models_loaded = False
        
        # Setup event handlers
        self.event_handlers = EventHandlers(self)
        
        # GUI variables for data binding
        self.setup_gui_variables()
        
        # Build the interface (after styling is ready)
        self.setup_gui()
        
        # Initialize components
        self.initialize_components()
        
        # Setup window closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.event_handlers.on_closing)
    
    def setup_modern_styling(self):
        """Setup modern Windows 11 light theme styling"""
        # Set main window background
        self.root.configure(bg=self.COLORS['bg_primary'])
        
        # Configure modern flat styles
        style = ttk.Style()
        
        # Use clean theme
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'winnative' in available_themes:
            style.theme_use('winnative')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # ======================== BUTTON STYLES ========================
        
        # Modern default button
        style.configure('Modern.TButton',
                       background=self.COLORS['bg_secondary'],
                       foreground=self.COLORS['text_primary'],
                       borderwidth=1,
                       focuscolor='none',
                       font=('Segoe UI', 9),
                       relief='flat')
        
        style.map('Modern.TButton',
                 background=[('active', self.COLORS['hover']),
                           ('pressed', self.COLORS['border'])])
        
        # Primary accent button
        style.configure('Accent.TButton',
                       background=self.COLORS['accent_blue'],
                       foreground='blue',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9, 'bold'),
                       relief='flat')
        
        style.map('Accent.TButton',
                 background=[('active', '#106ebe'),
                           ('pressed', '#005ba1')])
        
        # Success button
        style.configure('Success.TButton',
                       background=self.COLORS['accent_green'],
                       foreground='green',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9, 'bold'),
                       relief='flat')
        
        style.map('Success.TButton',
                 background=[('active', '#0e6e0e'),
                           ('pressed', '#0c5d0c')])
        
        # Warning button
        style.configure('Warning.TButton',
                       background=self.COLORS['accent_orange'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9, 'bold'),
                       relief='flat')
        
        style.map('Warning.TButton',
                 background=[('active', '#e67e00'),
                           ('pressed', '#cc7000')])
        
        # ======================== FRAME STYLES ========================
        
        # Modern frame
        style.configure('Modern.TFrame',
                       background=self.COLORS['bg_secondary'],
                       borderwidth=0,
                       relief='flat')
        
        # Configure default TLabelframe to match our modern style
        style.configure('TLabelframe',
                       background=self.COLORS['bg_secondary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.COLORS['border'])
        
        style.configure('TLabelframe.Label',
                       background=self.COLORS['bg_secondary'],
                       foreground=self.COLORS['text_primary'],
                       font=('Segoe UI', 10, 'bold'))
        
        # ======================== INPUT WIDGET STYLES ========================
        
        # Modern combobox
        style.configure('Modern.TCombobox',
                       fieldbackground=self.COLORS['bg_tertiary'],
                       background=self.COLORS['bg_secondary'],
                       foreground=self.COLORS['text_primary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.COLORS['border'],
                       font=('Segoe UI', 9),
                       arrowcolor=self.COLORS['text_secondary'])
        
        style.map('Modern.TCombobox',
                 fieldbackground=[('readonly', self.COLORS['bg_tertiary']),
                                ('focus', 'white')],
                 bordercolor=[('focus', self.COLORS['accent_blue'])])
        
        # Modern scale (slider)
        style.configure('Modern.Horizontal.TScale',
                       background=self.COLORS['bg_secondary'],
                       troughcolor=self.COLORS['bg_tertiary'],
                       borderwidth=0,
                       sliderthickness=20,
                       gripcount=0)
        
        style.map('Modern.Horizontal.TScale',
                 background=[('active', self.COLORS['accent_blue'])])
        
        # ======================== PROGRESS BAR STYLES ========================
        
        # Modern progressbar
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.COLORS['accent_blue'],
                       troughcolor=self.COLORS['bg_tertiary'],
                       borderwidth=0,
                       lightcolor=self.COLORS['accent_blue'],
                       darkcolor=self.COLORS['accent_blue'],
                       relief='flat')
        
        # ======================== LABEL STYLES ========================
        
        # Modern label
        style.configure('Modern.TLabel',
                       background=self.COLORS['bg_secondary'],
                       foreground=self.COLORS['text_primary'],
                       font=('Segoe UI', 9))
    
    def setup_gui_variables(self):
        """Setup tkinter variables for data binding"""
        # Device selection
        self.selected_device = tk.StringVar()
        
        # Language settings
        self.source_language = tk.StringVar(value=self.config_manager.get('source_language'))
        self.target_language = tk.StringVar(value=self.config_manager.get('target_language'))
        self.whisper_model = tk.StringVar(value=self.config_manager.get('whisper_model'))
        
        # Audio settings
        self.audio_threshold = tk.DoubleVar(value=self.config_manager.get('energy_threshold'))
        self.audio_gain = tk.DoubleVar(value=self.config_manager.get('audio_gain'))
        self.current_audio_level = tk.DoubleVar(value=0.0)
        
        # Status
        self.status_text = tk.StringVar(value="Ready")
    
    def setup_gui(self):
        """Build the main GUI layout"""
        # Configure main grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Main container with modern spacing
        main_frame = ttk.Frame(self.root, padding="20", style='Modern.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Create sections with modern spacing
        self.create_title_section(main_frame, row=0)
        self.create_device_section(main_frame, row=1)
        self.create_language_section(main_frame, row=1)
        self.create_control_section(main_frame, row=2)
        self.create_output_section(main_frame, row=3)
        self.create_status_section(main_frame, row=5)
    
    def create_title_section(self, parent, row):
        """Create the application title section"""
        title_frame = ttk.Frame(parent, style='Modern.TFrame')
        title_frame.grid(row=row, column=0,columnspan=2, sticky=(tk.W, tk.E), pady=(0, 25))
        
        # Main title with modern typography
        title_label = tk.Label(
            title_frame, 
            text="🎤 Real-Time Audio Translator", 
            font=('Segoe UI', 20, 'bold'),
            foreground=self.COLORS['text_primary'],
            background=self.COLORS['bg_secondary'],
            border=0
        )
        title_label.pack()
        
        # Subtitle with modern secondary text
        subtitle_label = tk.Label(
            title_frame,
            text="Capture system audio • AI transcription • Instant translation",
            font=('Segoe UI', 11),
            foreground=self.COLORS['text_secondary'],
            background=self.COLORS['bg_secondary'],
            border=0
        )
        subtitle_label.pack(pady=(8, 0))
    
    def create_device_section(self, parent, row):
        """Create the audio device configuration section"""
        # Use default TLabelFrame (no custom style)
        device_frame = ttk.LabelFrame(
            parent, 
            text="🎧 Audio Device Configuration", 
            padding="20"
        )
        device_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 20),padx=(0,10))
        device_frame.columnconfigure(1, weight=1)
        
        # Device selection with modern spacing
        tk.Label(
            device_frame, 
            text="Audio Device:",
            font=('Segoe UI', 9),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['text_primary'],
            border=0
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        
        self.device_combo = ttk.Combobox(
            device_frame, 
            textvariable=self.selected_device,
            state="readonly",
            width=45,
            style='Modern.TCombobox'
        )
        self.device_combo.grid(row=0, column=1,columnspan=2, sticky=(tk.W, tk.E), padx=(0, 15))
        self.device_combo.bind('<<ComboboxSelected>>', self.event_handlers.on_device_selected)
        
        # Modern flat buttons
        ttk.Button(
            device_frame, 
            text="🔄   Refresh", 
            command=self.event_handlers.refresh_devices,
            style='Modern.TButton'
        ).grid(row=0, column=3, padx=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(
            device_frame, 
            text="🧪 Test Device", 
            command=self.event_handlers.test_device,
            style='Modern.TButton'
        ).grid(row=1, column=3, padx=(0, 10), sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Audio level visualization with modern design
        tk.Label(
            device_frame, 
            text="Audio Level:",
            font=('Segoe UI', 9),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['text_primary'],
            border=0
        ).grid(row=1, column=0, sticky=tk.W, pady=(20, 0))
        
        self.level_progress = ttk.Progressbar(
            device_frame,
            variable=self.current_audio_level,
            maximum=1.0,
            length=100,
            mode='determinate',
            style='Modern.Horizontal.TProgressbar'
        )
        self.level_progress.grid(row=1, column=1,  sticky=(tk.W, tk.E),  pady=(20, 0), padx=(0,25))
        
        self.level_label = tk.Label(
            device_frame, 
            text="0.000",
            font=('Segoe UI', 9, 'bold'),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['accent_blue'],
            border=0
        )
        self.level_label.grid(row=1, column=2 , sticky=(tk.W, tk.E), pady=(20, 0), padx=(0,10))
        
        # Audio settings
        self.create_audio_settings(device_frame, start_row=2)
    
    def create_audio_settings(self, parent, start_row):
        """Create audio threshold and gain controls"""
        # Threshold setting with modern design
        tk.Label(
            parent, 
            text="Speech Threshold:",
            font=('Segoe UI', 9),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['text_primary'],
            border=0
        ).grid(row=start_row, column=0, sticky=tk.W, pady=(20, 0))
        
        threshold_frame = ttk.Frame(parent, style='Modern.TFrame')
        threshold_frame.grid(row=start_row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0), padx=(0, 15))
        threshold_frame.columnconfigure(0, weight=1)
        
        self.threshold_scale = ttk.Scale(
            threshold_frame,
            from_=0.001,
            to=0.1,
            variable=self.audio_threshold,
            orient=tk.HORIZONTAL,
            command=self.event_handlers.on_threshold_change,
            style='Modern.Horizontal.TScale'
        )
        self.threshold_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.threshold_label = tk.Label(
            threshold_frame, 
            text=f"{self.audio_threshold.get():.3f}",
            font=('Segoe UI', 9, 'bold'),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['accent_blue'],
            border=0
        )
        self.threshold_label.grid(row=0, column=1, padx=(15, 0))
        
        # Gain setting
        tk.Label(
            parent, 
            text="Audio Gain:",
            font=('Segoe UI', 9),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['text_primary'],
            border=0
        ).grid(row=start_row + 1, column=0, sticky=tk.W, pady=(15, 0))
        
        gain_frame = ttk.Frame(parent, style='Modern.TFrame')
        gain_frame.grid(row=start_row + 1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0), padx=(0, 15))
        gain_frame.columnconfigure(0, weight=1)
        
        self.gain_scale = ttk.Scale(
            gain_frame,
            from_=0.1,
            to=5.0,
            variable=self.audio_gain,
            orient=tk.HORIZONTAL,
            command=self.event_handlers.on_gain_change,
            style='Modern.Horizontal.TScale'
        )
        self.gain_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.gain_label = tk.Label(
            gain_frame, 
            text=f"{self.audio_gain.get():.1f}x",
            font=('Segoe UI', 9, 'bold'),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['accent_blue'],
            border=0
        )
        self.gain_label.grid(row=0, column=1, padx=(15, 0))
    
    def create_language_section(self, parent, row):
        """Create the language configuration section"""
        # Use default TLabelFrame (no custom style)
        lang_frame = ttk.LabelFrame(
            parent, 
            text="🌍 Language Configuration", 
            padding="20"
        )
        lang_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 20),padx=(0,10))
        lang_frame.columnconfigure(1, weight=1)
        #lang_frame.columnconfigure(3, weight=1)
        
        # Create language dropdown options
        source_language_options = [f"{code} - {name}" for code, name in LANGUAGES.items()]
        target_language_options = [f"{code} - {name}" for code, name in LANGUAGES.items() if code != "auto"]
        model_options = [f"{size} - {desc}" for size, desc in WHISPER_MODELS.items()]
        
        # Source language
        tk.Label(
            lang_frame, 
            text="Source Language:",
            font=('Segoe UI', 9),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['text_primary'],
            border=0
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        
        self.source_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.source_language,
            values=source_language_options,
            state="readonly",
            width=20,
            style='Modern.TCombobox'
        )
        self.source_combo.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.source_combo.bind('<<ComboboxSelected>>', self.event_handlers.on_source_language_change)
        
        # Target language
        tk.Label(
            lang_frame, 
            text="Target Language:",
            font=('Segoe UI', 9),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['text_primary'],
            border=0
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 15), pady=(20, 0))
        
        self.target_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.target_language,
            values=target_language_options,
            state="readonly",
            width=20,
            style='Modern.TCombobox'
        )
        self.target_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(20, 0))
        self.target_combo.bind('<<ComboboxSelected>>', self.event_handlers.on_target_language_change)
        
        # Whisper model selection
        tk.Label(
            lang_frame, 
            text="AI Model:",
            font=('Segoe UI', 9),
            background=self.COLORS['bg_secondary'],
            foreground=self.COLORS['text_primary'],
            border=0
        ).grid(row=2, column=0, sticky=tk.W, pady=(20, 0), padx=(0, 15))
        
        self.model_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.whisper_model,
            values=model_options,
            state="readonly",
            width=20,
            style='Modern.TCombobox'
        )
        self.model_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Save configuration button
        ttk.Button(
            lang_frame,
            text="💾 Save Configuration",
            command=self.event_handlers.save_configuration,
            style='Modern.TButton'
        ).grid(row=3, column=1, pady=(30, 0),sticky=(tk.W, tk.E))
    
    def create_control_section(self, parent, row):
        """Create the main control buttons section"""
        # Use default TLabelFrame (no custom style)
        control_frame = ttk.LabelFrame(
            parent, 
            text="🎮 Controls", 
            padding="20"
        )
        control_frame.grid(row=row, column=0,columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Load models button
        self.load_models_btn = ttk.Button(
            control_frame,
            text="🤖 Load AI Models",
            command=self.event_handlers.load_models,
            style='Accent.TButton'
        )
        self.load_models_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Start/Stop button
        self.start_stop_btn = ttk.Button(
            control_frame,
            text="▶️ Start Translation",
            command=self.event_handlers.toggle_translation,
            state=tk.DISABLED,
            style='Success.TButton'
        )
        self.start_stop_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Clear output button
        ttk.Button(
            control_frame,
            text="🗑️ Clear Output",
            command=self.event_handlers.clear_output,
            style='Modern.TButton'
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        # Statistics button
        ttk.Button(
            control_frame,
            text="📊 Statistics",
            command=self.event_handlers.show_statistics,
            style='Modern.TButton'
        ).pack(side=tk.LEFT)

    
    def create_output_section(self, parent, row):
        """Create the translation output display section with checkbox controls."""

        # Frame container
        output_frame = ttk.LabelFrame(parent, text="📝 Translation Output", padding="15")
        output_frame.grid(row=row, column=0,columnspan=2, rowspan=2, sticky="nsew", pady=(0, 20))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)  # Make text area expandable

        # ========== CHECKBOX SECTION ==========
        checkbox_frame = ttk.Frame(output_frame)
        checkbox_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Control variables
        self.var_show_logs = tk.BooleanVar(value=True)
        self.var_show_timestamp = tk.BooleanVar(value=True)
        self.var_show_process_time = tk.BooleanVar(value=True)
        self.var_show_original = tk.BooleanVar(value=True)

        # Checkbuttons with callbacks to refresh output
        ttk.Checkbutton(
            checkbox_frame, 
            text="Show Logs", 
            variable=self.var_show_logs,
            command=self.event_handlers.refresh_output_visibility
        ).grid(row=0, column=0, padx=5)
        
        ttk.Checkbutton(
            checkbox_frame, 
            text="Show Timestamp", 
            variable=self.var_show_timestamp,
            command=self.event_handlers.refresh_output_visibility
        ).grid(row=0, column=1, padx=5)
        
        ttk.Checkbutton(
            checkbox_frame, 
            text="Show Process Time", 
            variable=self.var_show_process_time,
            command=self.event_handlers.refresh_output_visibility
        ).grid(row=0, column=2, padx=5)
        
        ttk.Checkbutton(
            checkbox_frame, 
            text="Show Original", 
            variable=self.var_show_original,
            command=self.event_handlers.refresh_output_visibility
        ).grid(row=0, column=3, padx=5)

        # ========== TEXT + SCROLLBAR ==========
        text_frame = ttk.Frame(output_frame)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.output_text = tk.Text(
            text_frame,
            height=12,
            width=80,
            font=('Segoe UI', 10),
            wrap=tk.WORD,
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['text_primary'],
            selectbackground=self.COLORS['accent_blue'],
            selectforeground='white',
            insertbackground=self.COLORS['text_primary'],
            relief='flat',
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=self.COLORS['accent_blue'],
            highlightbackground=self.COLORS['border']
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.configure(yscrollcommand=scrollbar.set)

        # Tag configurations with enhanced styling for streaming effect
        self.output_text.tag_configure("timestamp", foreground=self.COLORS['text_secondary'], font=('Segoe UI', 9))
        self.output_text.tag_configure("original", foreground=self.COLORS['accent_blue'], font=('Segoe UI', 10, 'bold'))
        self.output_text.tag_configure("translation", foreground=self.COLORS['accent_green'], font=('Segoe UI', 10, 'bold'))
        self.output_text.tag_configure("info", foreground=self.COLORS['text_secondary'], font=('Segoe UI', 9))
        self.output_text.tag_configure("error", foreground=self.COLORS['accent_red'], font=('Segoe UI', 10, 'bold'))

    
    def create_status_section(self, parent, row):
        """Create the status bar section"""
        status_frame = ttk.Frame(parent, style='Modern.TFrame')
        status_frame.grid(row=row, column=0,columnspan=2, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        # Modern status bar
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_text,
            relief='flat',
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['text_secondary'],
            font=('Segoe UI', 9),
            anchor='w',
            padx=15,
            pady=8,
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=self.COLORS['border'],
            highlightbackground=self.COLORS['border']
        )
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def initialize_components(self):
        """Initialize core components"""
        # Create AI manager
        self.ai_manager = AIManager(
            self.config_manager.get_all(),
            callback=self.event_handlers.handle_ai_events
        )
        
        # Refresh device list
        self.event_handlers.refresh_devices()
        
        # Set initial GUI values
        self.event_handlers.update_gui_from_config()
        
        self.event_handlers.add_output_message("👋 Welcome to Real-Time Audio Translator!", "info")
        self.event_handlers.update_status("Ready - Load AI models to begin")
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()